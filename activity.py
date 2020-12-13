from collections import defaultdict

class Activity:
    def __init__(self):
        self.behaviours = []
        self.sets = {
            'sensors': defaultdict(int), 
            'time': defaultdict(float)
        }
        # self.sensor_set = defaultdict(int)
        # self.time_set = defaultdict(float)
    def add(self, behaviour):
        self.behaviours.append(behaviour)
        for sensor in behaviour.sensors: self.sets['sensors'][sensor]+=1
        for key in behaviour.time:
            self.sets['time'][key] += behaviour.time[key]
    def get_fuzzy_set(self, domain):
        n = len(self.behaviours)
        return {key: value/n for key, value in self.sets[domain].items()}
    def get_a_level(self, domain, alpha):
        n = len(self.behaviours)
        return {key: value/n for key, value in self.sets[domain].items() if value/n >= alpha}
    def membership(self, domain, element):
        n = len(self.behaviours)
        return self.sets[domain][element]/n if element in self.sets[domain] else 0.0
    def __str__(self):
        return('Activity: %s %s' %(self.get_fuzzy_set('sensors'), self.get_fuzzy_set('time')))