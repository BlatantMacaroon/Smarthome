from collections import defaultdict

class Activities:
    def __init__(self, data):
        behaviours= {}
        self.data = defaultdict(Activity)
        f = open(data)
        max_parsed = 15
        for reading in f:
            # whenever starting point is found, start adding lines to a new behaviour
            # whenever end point is found, finish that behaviour, remove it from list of behaviours being added and 
            reading = reading.split()
            if len(reading) > 4: # if this row is a start/end of an activity, it will have two extra values at the end
                if reading[5] == 'begin':
                    if reading[4] in behaviours:
                        print('error! Starting behaviour that is already started')
                    else:
                        behaviours[reading[4]] = set() # start building a set of triggered sensors for this observed behaviour
                        self.add_sensor(behaviours, reading)
                if reading[5] == 'end':
                    if reading[4] not in behaviours:
                        print('error! Ending behaviour that has not started yet')
                    else:
                        self.add_sensor(behaviours, reading)
                        self.data[reading[4]].add(behaviours[reading[4]])
                        # print(reading[4], behaviours[reading[4]])
                        del behaviours[reading[4]] #
                        # max_parsed -=1
                        # if max_parsed == 0: break
                        #print(len(behaviours))
            else: self.add_sensor(behaviours, reading)
    def add_sensor(self, behaviours, reading):
        # verify behaviour is valid (related to motion or ) and then add sensor to all current behaviours
        if reading[2][0] in ['M', 'D']:
            for key in behaviours: behaviours[key].add(reading[2])

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

activities= Activities('data/data_aruba')
print(activities.data['Meal_Preparation'].get_fuzzy_set())
print(activities.data['Meal_Preparation'].get_a_level(.8))
