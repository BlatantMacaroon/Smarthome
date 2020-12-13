from collections import defaultdict
from random import random
import math
from activity import Activity
from behaviour import Behaviour, parse_time, times

def parse_data(data, test_proportion, test_novel=set()):
    #test_novel is a set of activity names to keep to one side to use as 'novel' activities
    def add_sensor(buffer, line):
        # verify behaviour is valid (related to motion or ) and then add sensor to all current behaviours
        if line[2][0] == 'M' and line[3] == 'ON':
            for key in buffer: buffer[key]['sensors'].add(line[2])
        if line[2][0] == 'D':
            for key in buffer: buffer[key]['sensors'].add(line[2])
    activities = defaultdict(Activity)
    test = []
    buffer = {}
    universe = defaultdict(set)
    max_lines = 150
    max_behaviours = 20
    f = open(data)
    for line in f:
        # whenever starting point is found, start adding lines to a new behaviour
        # whenever end point is found, finish that behaviour, remove it from list of behaviours being added and 
        line = line.split()
        # if max_lines>0:
        #     max_lines-=1
        #     # print(line, parse_time(line, 'start'), parse_time(line, 'finish'))
        # else: break
        if len(line) > 4: # if this row is a start/end of an activity, it will have two extra values at the end
            activity_name = line[4]
            if activity_name == 'Novel': print('error! Activity cannot be defined as Novel')
            if line[5] == 'begin':
                if activity_name in buffer:
                    print('error! Starting behaviour that is already started')
                else:
                    buffer[activity_name] = {'activity_name': activity_name, 'sensors': set(), 'start': parse_time(line, 'start')} # start building kwargs to contruct this behaviour
                    add_sensor(buffer, line)
            if line[5] == 'end':
                if activity_name not in buffer:
                    print('error! Ending behaviour that has not started yet')
                else:
                    add_sensor(buffer, line)
                    buffer[activity_name]['finish'] = parse_time(line, 'finish')
                    behaviour = Behaviour(**buffer[activity_name])
                    if random() < test_proportion or activity_name in test_novel:
                        test.append(behaviour)
                    else: 
                        # print('\n',activity_name)
                        activities[activity_name].add(behaviour)
                        # print(max_behaviours)
                        # if max_behaviours == 0: break
                        # else: max_behaviours -=1
                    universe['sensors'] = universe['sensors'].union(buffer[activity_name]['sensors'])
                    del buffer[activity_name]
        else: add_sensor(buffer, line)
        universe['time'] = times
    return activities, test, universe

def fuzzy_error(behaviour, activity, universe, domain):
    # this will calculate how well a given Activity fits a given behaviour by returning the standardized error
    return math.sqrt(sum(((behaviour.membership(domain, element) - activity.membership(domain, element)))**2 for element in universe[domain])/len(universe[domain]))

def best_activity(behaviour, activities, universe, domain, novelty_criterion):
    #returns a list of activity names, from best fitting to worst fitting
    return sorted([(fuzzy_error(behaviour, activities[act], universe, domain), act) for act in activities]+([(novelty_criterion, 'Novel')]))

class Crosstab:
    # provides a crosstabulation of best guesses: the frequency with which each activity in the test data was categorized as being each activity class
    # also provides row/col totals to speed up calculation
    def __init__(self, test_data, activities, universe, domain, novelty_criterion):
        self.test_data = test_data
        self.activities = activities
        self.universe = universe
        self.domain = domain
        self.novelty_criterion = novelty_criterion
        self.xtab = defaultdict(lambda: defaultdict(int))
        self.truths = defaultdict(int)
        self.predictions = defaultdict(int)
        for t in test_data:
            truth = t.activity_name
            guess = best_activity(t, activities, universe, domain, novelty_criterion)[0][1]
            self.xtab[truth][guess] +=1
            self.predictions[guess] +=1
        for truth in self.xtab:
            self.truths[truth] = sum(self.xtab[truth].values())
        self.total = sum(self.truths.values())
    def f_string(self, truth, pred):
        s =  str(self.xtab[truth][pred])
        return (s if truth != pred else f"\u001b[32m{s}\u001b[37m")+' '*(4-len(s))

def confusion_matrix(test_data, activities, universe, domain, novelty_criterion=1):
    #prints a confusion matrix to the console for given results
    result = Crosstab(test_data, activities, universe, domain, novelty_criterion)
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

def idx_of_truth(behaviour, activities, universe, domain, novelty_criterion):
    #returns the index of the activity that was actually the corresponding ground truth (0 means first guess was correct, 1 means second guess, etc)
    #if activity is actually novel (ie not in the list of activities) will return the index of 'Novel'
    target = behaviour.activity_name if behaviour.activity_name in activities else 'Novel'
    return  next((idx for idx, v in enumerate(best_activity(behaviour, activities, universe, domain, novelty_criterion)) if v[1] == target), None)

def nth_guess_table(test_data, activities, universe, domain, novelty_criterion=1):
    result = defaultdict(list)
    for t in test_data:
        truth = t.activity_name
        idx = idx_of_truth(t, activities, universe, domain, novelty_criterion)
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
    #TODO: update to use totals to make calc faster
    others = {a for a in crosstab.xtab if a in activities} if target == 'Novel' else {a for a in crosstab.xtab if a != target}
    return sum(crosstab.xtab[a][target] for a in others)/sum(sum(crosstab.xtab[a].values()) for a in others)

def error_rates(test_data, activities, universe, domain, novelty_criterion):
    result = Crosstab(test_data, activities, universe, domain, novelty_criterion)
    print ('\nHITS AND FALSE ALARMS')
    for truth in result.truths:
        hit_string = str(round(hit_rate(result, truth, activities), 3))
        print(truth+' '*(18-len(truth)), 
            hit_string+' '*(8-len(hit_string)),
            round(fa_rate(result, truth if truth in activities else 'Novel', activities), 3)
        )

activities, test_data, universe= parse_data('data/data_aruba', 0.4, {'Sleeping', 'Meal_Preparation'})
domain = 'sensors'
criterion = .3
args = (test_data, activities, universe, domain, criterion)
# print(crosstab(test_data, activities, universe, domain, 0.5))
confusion_matrix(*args)
nth_guess_table(*args)
error_rates(*args)

