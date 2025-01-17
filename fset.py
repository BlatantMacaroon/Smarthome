from collections import defaultdict
from random import random, shuffle
import math
from activities import Activities
from behaviour import Behaviour, parse_time, times
import numpy as np
import pylab as pl

def parse_data(data, test_proportion):
    #parses the data from a file, producing a trained Activities object, a set of test Behaviour objects, and a universe dict (with a set of elements for each domain)
    def add_sensor(buffer, line):
        # verify sensor information is valid (related to motion detector or door) and then add sensor to all current behaviours in buffer
        if line[2][0] == 'M' and line[3] == 'ON': # motion sensor present in Behaviour if there is at least one occurrence of that sensor being turned on
            for key in buffer: buffer[key]['sensors'].add(line[2])
        if line[2][0] == 'D': # door sensor is present in Behaviour if there is at least one occurrence of that door being opened or closed
            for key in buffer: buffer[key]['sensors'].add(line[2])
    buffer = {} # data that will be used to build Behaviour objects once all lines relating to that object have been read (multiple different activities can be built in buffer at once)
    behaviours = [] # Behaviour items that will be split into training and test data.
    universe = defaultdict(set) # sets containing all elements in each domain
    universe['time'] = times
    predecessor = None # the first behaviour has no predecessor
    f = open(data)
    for line in f:
        # build a list of all behaviours and a universe of sensors
        line = line.split()
        if len(line) > 4: # if this row is a start/end of an activity, it will have two extra values at the end
            activity_name = line[4]
            if activity_name == 'Novel': print('error! Activity cannot be defined as Novel')
            if line[5] == 'begin':
                if activity_name in buffer:
                    print('error! Starting behaviour that is already started')
                else:
                    buffer[activity_name] = {'activity_name': activity_name, 'sensors': set(), 'start': parse_time(line, 'start'), 'predecessor': predecessor} # start building kwargs to contruct this behaviour
                    add_sensor(buffer, line)
            if line[5] == 'end':
                if activity_name not in buffer:
                    print('error! Ending behaviour that has not started yet')
                else:
                    add_sensor(buffer, line)
                    buffer[activity_name]['finish'] = parse_time(line, 'finish')
                    behaviours.append(Behaviour(**buffer[activity_name])) # build a behaviour object using buffered data and add to list
                    universe['sensors'] = universe['sensors'].union(buffer[activity_name]['sensors'])
                    predecessor = activity_name
                    del buffer[activity_name]
        else: add_sensor(buffer, line)
    #shuffle behaviours but keep first item at start as it has no predecessor (only suitable as a training item if successor domain is being used)
    front = behaviours.pop(0)
    shuffle(behaviours)
    behaviours = [front] + behaviours
    training_n = int(len(behaviours)*(1-test_proportion))
    activities = Activities(behaviours[:training_n]) # train the activities model using the training data
    test = behaviours[training_n:]
    print(len(test))
    print(training_n)
    return activities, test, universe

def fuzzy_error(behaviour, activity, universe, domain):
    # this will calculate how well a given Activity fits a given behaviour by returning the standardized error
    return 1-math.sqrt(sum(((behaviour.membership(domain, element) - activity.membership(domain, element)))**2 for element in universe[domain])/len(universe[domain]))

def best_activity(behaviour, activities, universe, domains, novelty_criterion, t):
    #returns a list of activity names, from best fitting to worst fitting
    def error_list(behaviour, activities, universe, domains, t):
        if len(domains) > 1:
            return t(error_list(behaviour, activities, universe, set(list(domains)[:len(domains)//2]), t), error_list(behaviour, activities, universe, set(list(domains)[len(domains)//2:]), t))
        else:
            domain = list(domains)[0]
            #if domain is 'predecessor' then look up fuzzy set for the predecessor (this could be boosted later on to make predecessor a fuzzy set rather than a string)
            if domain == 'predecessor':
                return [(activities[behaviour.predecessor].membership('successor', act), act) for act in activities]
            return [(fuzzy_error(behaviour, activities[act], universe, domain), act) for act in activities]
    return sorted(error_list(behaviour, activities, universe, domains, t)+([(novelty_criterion**len(domains), 'Novel')]), reverse=True)

def grade_vs_accuracy(test_data, activities, universe, domains, novelty_criterion, t):
    result = []
    # produce a box plot of membership grade of correct guess vs incorrect guesses
    for behaviour in test_data:
        guess = best_activity(behaviour, activities, universe, domains, novelty_criterion, t)[0]
        result.append([behaviour.activity_name, guess[0], guess[1] == behaviour.activity_name])
    result = np.array(result)
    pl.boxplot([result[result[:,2] == 'True', 1].astype(np.float), result[result[:,2] == 'False', 1].astype(np.float)])
    pl.show()

class Crosstab:
    # provides a crosstabulation of best guesses: the frequency with which each activity in the test data was categorized as being each activity class
    # also provides row/col totals to speed up calculation
    def __init__(self, test_data, activities, universe, domains, novelty_criterion, t):
        self.test_data = test_data
        self.activities = activities
        self.universe = universe
        self.domains = domains
        self.novelty_criterion = novelty_criterion
        self.t = t
        self.xtab = defaultdict(lambda: defaultdict(int))
        self.truths = defaultdict(int)
        self.predictions = defaultdict(int)
        for observation in test_data:
            truth = observation.activity_name
            guess = best_activity(observation, activities, universe, domains, novelty_criterion, t)[0][1]
            self.xtab[truth][guess] +=1
            self.predictions[guess] +=1
        for truth in self.xtab:
            self.truths[truth] = sum(self.xtab[truth].values())
        self.total = sum(self.truths.values())
        print(sum(self.truths.values()), sum(self.predictions.values()), self.total)
    def f_string(self, truth, pred):
        s =  str(self.xtab[truth][pred])
        return (s if truth != pred else f"\u001b[32m{s}\u001b[37m")+' '*(4-len(s))

def confusion_matrix(test_data, activities, universe, domains, novelty_criterion=0, t=None):
    #prints a confusion matrix to the console for given results
    result = Crosstab(test_data, activities, universe, domains, novelty_criterion, t)
    act_names = sorted([act for act in activities]) #categories that the algorithm can actually categorise behaviours as (but not including 'Novel')
    test_names_in_act = sorted([t for t in result.truths if t in act_names]) #categories that were present in test cases and were also in act_names
    test_names_not_in_act = sorted([t for t in result.truths if t not in act_names]) #categories that were present in test cases but were not also in act_names
    test_names = test_names_in_act + test_names_not_in_act #all categories present in test cases, alphabetized but with those actually not actually present in act_names listed last
    key_names = act_names + test_names_not_in_act + ['Novel']
    act_names.append('Novel')
    print('\nKEY')
    for index, name in enumerate(key_names): print(index, ': '+name)
    print ('\nTRUTH\t\t\tPREDICTION')
    print ('\t',*(str(key_names.index(act))+'   ' for act in act_names), 'n')
    for truth in test_names:
        print(str(key_names.index(truth))+'\t',*((result.f_string(truth, act) 
            if act in result.xtab[truth] else '.   ') for act in act_names), result.truths[truth])
    print('n\t', *((str(result.predictions[act])+' '*(4-len(str(result.predictions[act]))) if act in result.predictions else '.   ') for act in act_names), result.total)


def idx_of_truth(behaviour, activities, universe, domains, novelty_criterion, t=None):
    #returns the index of the activity that was actually the corresponding ground truth (0 means first guess was correct, 1 means second guess, etc)
    #if activity is actually novel (ie not in the list of activities) will return the index of 'Novel'
    target = behaviour.activity_name if behaviour.activity_name in activities else 'Novel'
    return  next((idx for idx, v in enumerate(best_activity(behaviour, activities, universe, domains, novelty_criterion, t)) if v[1] == target), None)

def nth_guess_table(test_data, activities, universe, domains, novelty_criterion=0, t=None):
    #prints for each activity class, a frequency distribution for the index in the best_activity list for behaviours
    #eg for Wash_Dishes, [23, 34, 0, 1] would mean that across all the cases of Wash_Dishes, the algorithm ranked Wash_Dishes as the best option, 23 times,
    #the second best option 34 times, and the fourth best option one time.
    result = defaultdict(list)
    for observation in test_data:
        truth = observation.activity_name
        idx = idx_of_truth(observation, activities, universe, domains, novelty_criterion, t)
        if idx == None: 
            print('error: None found')
            continue 
        # if idx>3: print(t, best_activity(t, activities ,universe))
        current_len = len(result[truth])
        if current_len <= idx:
            result[truth].extend([0 for i in range(idx-current_len+1)])
        result[truth][idx]+=1
    print('\nCORRECT PREDICTION ON NTH GUESS')
    for truth in result:
        print(truth, result[truth])

def hit_rate(crosstab, truth, activities):
    #activity and target should normally be the same (exception would be where you expect a particular activity to be recognized as 'novel')
    target = truth if truth in activities else 'Novel'
    return crosstab.xtab[truth][target]/crosstab.truths[truth]

def fa_rate(crosstab, target, activities):
    #returns the false alarm rate for a given target activity FA / (FA+CR)
    others = {a for a in crosstab.xtab if a in activities} if target == 'Novel' else {a for a in crosstab.xtab if a != target}
    return sum(crosstab.xtab[a][target] for a in others)/sum(crosstab.truths[a] for a in others)

def overall_accuracy(crosstab, activities):
    #returns (hits + CR) / (hits + misses + FA + CR) for all activities combined
    return sum(crosstab.xtab[truth][truth if truth in activities else 'Novel'] for truth in crosstab.truths)/crosstab.total

def error_rates(test_data, activities, universe, domains, novelty_criterion, t=None):
    #prints out the hit and false alarm rates for each activity class
    result = Crosstab(test_data, activities, universe, domains, novelty_criterion, t)
    print ('\nHITS AND FALSE ALARMS')
    for truth in result.truths:
        hit_string = str(round(hit_rate(result, truth, activities), 3))
        print(truth+' '*(18-len(truth)), 
            hit_string+' '*(8-len(hit_string)),
            round(fa_rate(result, truth, activities), 3) if truth in activities else '.'
        )
    print('Novel'+' '*22, round(fa_rate(result, 'Novel', activities), 3))
    print('Overall Accuracy:', round(overall_accuracy(result, activities), 3))

def t_prod(a, b):
    # calculates combined membership for a list of (membership, element_name) tuples
    # uses product as t-norm
    if len(a) is not len(b):
        print('error: a and b are not same length')
        return None
    return [(a[i][0]*b[i][0], a[i][1]) for i in range(len(a))]



activities, test_data, universe= parse_data('data/data_aruba', 0.5)
domains = {'sensors', 'time', 'predecessor'}
criterion = 0 #Note, novelty detection here is based upon a cutoff and is not documented in article. 0 = no behaviour is classed as Novel
t = t_prod
args = (test_data, activities, universe, domains, criterion, t)

confusion_matrix(*args)
nth_guess_table(*args)
error_rates(*args)
