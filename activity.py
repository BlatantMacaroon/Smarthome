from collections import defaultdict

class Activity:
    def __init__(self):
        self.behaviours = []
        self.sets = {
            'sensors': defaultdict(int), 
            'time': defaultdict(float),
            'successor': defaultdict(int)
            # 'x': defaultdict(float)
        }
        # self.sensor_set = defaultdict(int)
        # self.time_set = defaultdict(float)
    def add(self, behaviour):
        self.behaviours.append(behaviour)
        for sensor in behaviour.sensors: self.sets['sensors'][sensor]+=1
        for key in behaviour.time:
            self.sets['time'][key] += behaviour.time[key]
        # for sensor in behaviour.sensors:
        #     for time in behaviour.time:
        #         self.sets['x'][(sensor, time)] += behaviour.time[time]
        #TODO I HAVE TO TALLY IN THE ACTIVITY FOR THE PREVIOUS ACTIVITY - NOT THIS ONE
    def add_successor(self, activity_name):
        self.sets['successor'][activity_name] +=1

    def get_fuzzy_set(self, domain):
        n = sum(self.sets['successor'].values()) if domain == 'successor' else len(self.behaviours)
        print(n)
        return {key: value/n for key, value in self.sets[domain].items()}
    def get_a_level(self, domain, alpha):
        n = len(self.behaviours)
        return {key: value/n for key, value in self.sets[domain].items() if value/n >= alpha}
    def membership(self, **kwargs):
        #TODO do not need to allow multiple domains as this isn't a very good measure (observation could equally match activity with low, high as high, low)
        if len(kwargs) == 1:
            domain, element = list(kwargs.items())[0]
            n = sum(self.sets['successor'].values()) if domain == 'successor' else len(self.behaviours)
            return self.sets[domain][element]/n if element in self.sets[domain] else 0.0
        else:
            return self.membership(**dict(list(kwargs.items())[:len(kwargs)//2])) * self.membership(**dict(list(kwargs.items())[len(kwargs)//2:]))


        # if isinstance(domain, set):
        #     if len(domain) is 1: domain = list(domain)[0]
        #     else:
        #         return self.membership(set(list(domain)[len(domain)//2:]), element)*self.membership(set(list(domain)[:len(domain)//2]), element)
        # n = len(self.behaviours)
        # return self.sets[domain][element]/n if element in self.sets[domain] else 0.0
    def __str__(self):
        return('Activity: %s %s' %(self.get_fuzzy_set('sensors'), self.get_fuzzy_set('time')))
