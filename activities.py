from collections import defaultdict

class Activities:
    def __init__(self, training_data):
        self.data = defaultdict(Activity)
        for behaviour in training_data:
            self.data[behaviour.activity_name].add(behaviour)
            if behaviour.predecessor is not None:
                self.data[behaviour.predecessor].add_successor(behaviour.activity_name)
    def __iter__(self):
        return (x for x in self.data)
    def __getitem__(self, val):
        if val in self.data:
            return self.data[val]
        else: raise KeyError('no such key present in Activities object')

class Activity:
    def __init__(self):
        self.behaviours = []
        self.sets = {
            'sensors': defaultdict(int), 
            'time': defaultdict(float),
            'successor': defaultdict(int)
            # 'x': defaultdict(float)
        }
        self.most_successors = 0
        # self.sensor_set = defaultdict(int)
        # self.time_set = defaultdict(float)
    def add(self, behaviour):
        self.behaviours.append(behaviour)
        for sensor in behaviour.sensors: self.sets['sensors'][sensor]+=1
        for key in behaviour.time:
            self.sets['time'][key] += behaviour.time[key]
    def add_successor(self, activity_name):
        self.sets['successor'][activity_name] +=1
        self.most_successors = max(self.sets['successor'].values())

    def get_fuzzy_set(self, domain):
        n = self.n_for_domain(domain)
        return {key: value/n for key, value in self.sets[domain].items()}
    def get_a_level(self, domain, alpha):
        n = self.n_for_domain(domain)
        return {key: value/n for key, value in self.sets[domain].items() if value/n >= alpha}
    def membership(self, domain, element):
        n = self.n_for_domain(domain)
        return self.sets[domain][element]/n if element in self.sets[domain] else 0.0
    def n_for_domain(self, domain):
        return self.most_successors if domain == 'successor' else len(self.behaviours)



        # if isinstance(domain, set):
        #     if len(domain) is 1: domain = list(domain)[0]
        #     else:
        #         return self.membership(set(list(domain)[len(domain)//2:]), element)*self.membership(set(list(domain)[:len(domain)//2]), element)
        # n = len(self.behaviours)
        # return self.sets[domain][element]/n if element in self.sets[domain] else 0.0
    def __str__(self):
        return('Activity: %s %s' %(self.get_fuzzy_set('sensors'), self.get_fuzzy_set('time')))
