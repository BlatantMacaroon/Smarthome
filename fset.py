from collections import defaultdict

def parse_data(data):
    def add_sensor(buffer, line):
        # verify behaviour is valid (related to motion or ) and then add sensor to all current behaviours
        if line[2][0] == 'M' and line[3] == 'ON':
            for key in buffer: buffer[key].add(line[2])
        if line[2][0] == 'D':
            for key in buffer: buffer[key].add(line[2]+('O' if line[3] == 'OPEN' else 'C'))
    activities = defaultdict(Activity)
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
            activity = line[4]
            if line[5] == 'begin':
                if activity in buffer:
                    print('error! Starting behaviour that is already started')
                else:
                    buffer[activity] = set() # start building a set of triggered sensors for this observed behaviour
                    add_sensor(buffer, line)
            if line[5] == 'end':
                if activity not in buffer:
                    print('error! Ending behaviour that has not started yet')
                else:
                    add_sensor(buffer, line)
                    for s in buffer[activity]:
                        if s[0] == 'D' and s[:-1]+('O' if s[-1] == 'C' else 'C') not in buffer[activity]: doormismatch +=1
                    if any(s[0] == 'D' for s in buffer[activity]): hasdoor +=1
                    total +=1
                    activities[activity].add(buffer[activity])
                    del buffer[activity]
                    # max_parsed -=1
                    # if max_parsed == 0: break
                    #print(len(buffer))
        else: add_sensor(buffer, line)
    print(total, doormismatch, doormismatch/total)
    print(hasdoor, doormismatch, doormismatch/hasdoor)
    return activities

# class Activities:
#     def __init__(self, data):
#         behaviours= {}
#         self.data = defaultdict(Activity)
#         f = open(data)
#         max_parsed = 15
#         total = 0
#         hasdoor = 0
#         doormismatch = 0
#         for reading in f:
#             # whenever starting point is found, start adding lines to a new behaviour
#             # whenever end point is found, finish that behaviour, remove it from list of behaviours being added and 
#             reading = reading.split()
#             if len(reading) > 4: # if this row is a start/end of an activity, it will have two extra values at the end
#                 if reading[5] == 'begin':
#                     if reading[4] in behaviours:
#                         print('error! Starting behaviour that is already started')
#                     else:
#                         behaviours[reading[4]] = set() # start building a set of triggered sensors for this observed behaviour
#                         self.add_sensor(behaviours, reading)
#                 if reading[5] == 'end':
#                     if reading[4] not in behaviours:
#                         print('error! Ending behaviour that has not started yet')
#                     else:
#                         self.add_sensor(behaviours, reading)
#                         for s in behaviours[reading[4]]:
#                             if s[0] == 'D' and s[:-1]+('O' if s[-1] == 'C' else 'C') not in behaviours[reading[4]]: doormismatch +=1
#                         if any(s[0] == 'D' for s in behaviours[reading[4]]): hasdoor +=1
#                         total +=1
#                         self.data[reading[4]].add(behaviours[reading[4]])
#                         del behaviours[reading[4]] #
#                         # max_parsed -=1
#                         # if max_parsed == 0: break
#                         #print(len(behaviours))
#             else: self.add_sensor(behaviours, reading)
#         print(total, doormismatch, doormismatch/total)
#         print(hasdoor, doormismatch, doormismatch/hasdoor)
#     def add_sensor(self, behaviours, reading):
#         # verify behaviour is valid (related to motion or ) and then add sensor to all current behaviours
#         if reading[2][0] == 'M' and reading[3] == 'ON':
#             for key in behaviours: behaviours[key].add(reading[2])
#         if reading[2][0] == 'D':
#             for key in behaviours: behaviours[key].add(reading[2]+('O' if reading[3] == 'OPEN' else 'C'))

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

activities= parse_data('data/data_aruba')
print(activities['Meal_Preparation'].get_fuzzy_set())
print(len(activities['Meal_Preparation'].get_fuzzy_set()))
print(activities['Meal_Preparation'].get_a_level(.8))
