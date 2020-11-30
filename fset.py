from collections import defaultdict
from random import random

def parse_data(data):
    def add_sensor(buffer, line):
        # verify behaviour is valid (related to motion or ) and then add sensor to all current behaviours
        if line[2][0] == 'M' and line[3] == 'ON':
            for key in buffer: buffer[key].add(line[2])
        if line[2][0] == 'D':
            for key in buffer: buffer[key].add(line[2]+('O' if line[3] == 'OPEN' else 'C'))
    activities = defaultdict(Activity)
    test = []
    test_proportion = 0.2
    buffer = {}
    f = open(data)
    max_parsed = 15
    total = 0
    hasdoor = 0
    doormismatch = 0
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
                    for s in buffer[activity_name]:
                        if s[0] == 'D' and s[:-1]+('O' if s[-1] == 'C' else 'C') not in buffer[activity_name]: doormismatch +=1
                    if any(s[0] == 'D' for s in buffer[activity_name]): hasdoor +=1
                    total +=1
                    if random() < test_proportion:
                        test.append(Behaviour(activity_name, buffer[activity_name]))
                    else: 
                        activities[activity_name].add(buffer[activity_name])
                    del buffer[activity_name]
                    # max_parsed -=1
                    # if max_parsed == 0: break
                    #print(len(buffer))
        else: add_sensor(buffer, line)
    print(total, doormismatch, doormismatch/total)
    print(hasdoor, doormismatch, doormismatch/hasdoor)
    return activities, test

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

activities, test= parse_data('data/data_aruba')
print(activities['Meal_Preparation'].get_fuzzy_set())
print(len(activities['Meal_Preparation'].get_fuzzy_set()))
print(activities['Meal_Preparation'].get_a_level(.8))
print(len(test))
