from collections import defaultdict
from random import random
import math

def parse_data(data, test_proportion, test_novel=set()):
    #test_novel is a set of activity names to keep to one side to use as 'novel' activities
    def add_sensor(buffer, line):
        # verify behaviour is valid (related to motion or ) and then add sensor to all current behaviours
        if line[2][0] == 'M' and line[3] == 'ON':
            for key in buffer: buffer[key].add(line[2])
        if line[2][0] == 'D':
            for key in buffer: buffer[key].add(line[2])
    activities = defaultdict(Activity)
    test = []
    buffer = {}
    universe = set()
    f = open(data)
    for line in f:
        # whenever starting point is found, start adding lines to a new behaviour
        # whenever end point is found, finish that behaviour, remove it from list of behaviours being added and 
        line = line.split()
        if len(line) > 4: # if this row is a start/end of an activity, it will have two extra values at the end
            activity_name = line[4]
            if line[5] == 'begin':
                if activity_name in buffer:
                    print('error! Starting behaviour that is already started')
                else:
                    buffer[activity_name] = set() # start building a set of triggered sensors for this observed behaviour
                    add_sensor(buffer, line)
            if line[5] == 'end':
                if activity_name not in buffer:
                    print('error! Ending behaviour that has not started yet')
                else:
                    add_sensor(buffer, line)
                    if random() < test_proportion or activity_name in test_novel:
                        test.append(Behaviour(activity_name, buffer[activity_name]))
                    else: 
                        activities[activity_name].add(buffer[activity_name])
                    universe = universe.union(buffer[activity_name])
                    del buffer[activity_name]
        else: add_sensor(buffer, line)
    return activities, test, universe

class Activity:
    def __init__(self):
        self.behaviours = []
        self.sensor_count = defaultdict(int)
    def add(self, behaviour):
        self.behaviours.append(behaviour)
        for sensor in self.behaviours[-1]: self.sensor_count[sensor]+=1
    def get_fuzzy_set(self):
        n = len(self.behaviours)
        return {key: value/n for key, value in self.sensor_count.items()}
    def get_a_level(self, alpha):
        n = len(self.behaviours)
        return {key: value/n for key, value in self.sensor_count.items() if value/n >= alpha}

class Behaviour:
    def __init__(self, activity_name, sensors):
        self.activity_name = activity_name
        self.sensors = sensors
    def __str__(self):
        return 'Behaviour(' + self.activity_name + ', ' + str(self.sensors) + ')'

def fuzzy_error(behaviour, activity, universe):
    # this will calculate how well a given Activity fits a given behaviour by returning the standardized error
    return math.sqrt(sum(((sensor in behaviour.sensors) - (activity[sensor] if sensor in activity else 0))**2 for sensor in universe)/len(universe))

def best_activity(behaviour, activities, universe):
    #returns a list of activity names, from best fitting to worst fitting
    return sorted([(fuzzy_error(behaviour, activities[act].get_fuzzy_set(), universe), act) for act in activities])
    
def idx_of_truth(behaviour, activities, universe):
    #returns the index of the activity that was actually the corresponding ground truth (0 means first guess was correct, 1 means second guess, etc)
    return  next((idx for idx, v in enumerate(best_activity(behaviour, activities, universe)) if v[1] == behaviour.activity_name), None)

def confusion_matrix(activities, test_data, universe, novelty_criterion=1):
    #prints a confusion matrix to the console for given results
    result = defaultdict(lambda: defaultdict(int))
    for t in test_data:
        truth = t.activity_name
        guess = best_activity(t, activities, universe)[0]
        guess = 'Novel' if guess[0]>novelty_criterion else guess[1]
        result[truth][guess] +=1
    act_names = sorted([act for act in activities])
    test_names = act_names+sorted([t for t in result if t not in act_names])
    need_novel = novelty_criterion < 1 and 'Novel' not in test_names
    key_names = test_names+(['Novel'] if need_novel else [])
    if need_novel: act_names.append('Novel')
    print(test_names)
    print(act_names)
    print('\nKEY')
    for index, name in enumerate(key_names): print(index, ': '+name)
    print ('\nTRUTH\t\t\tPREDICTION')
    print ('\t',*(str(key_names.index(act))+'   ' for act in act_names))
    for truth in test_names:
        print(str(key_names.index(truth))+'\t',*((str(result[truth][act])+' '*(4-len(str(result[truth][act]))) 
            if act in result[truth] else '.   ') for act in act_names))

def nth_guess_table(activities, test_data, universe):
    result = defaultdict(list)
    for t in test_data:
        truth = t.activity_name
        idx = idx_of_truth(t, activities, universe)
        if idx == None: continue 
        # if idx>3: print(t, best_activity(t, activities ,universe))
        current_len = len(result[truth])
        if current_len <= idx:
            result[truth].extend([0 for i in range(idx-current_len+1)])
        result[truth][idx]+=1
    print('\nCORRECT PREDICTION ON NTH GUESS')
    for truth in result:
        print(truth, result[truth])



activities, test_data, universe= parse_data('data/data_aruba', 0.2, test_novel={'Eating'})
print(activities['Meal_Preparation'].get_fuzzy_set())
print(len(activities['Meal_Preparation'].get_fuzzy_set()))
print(activities['Meal_Preparation'].get_a_level(.8))
print(len(test_data))
print(len(universe))
print(test_data[0])
# for act in activities:
#     print(act, fuzzy_error(test_data[0], activities[act].get_fuzzy_set(), universe))
print(best_activity(test_data[0], activities, universe))
print(idx_of_truth(test_data[0], activities, universe))

# result = {t.activity_name: best_activity for t in test_data}

confusion_matrix(activities, test_data, universe, novelty_criterion=.25)
nth_guess_table(activities, test_data, universe)
