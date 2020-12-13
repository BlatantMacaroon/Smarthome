def linear(first, second, start, finish):
    def func(time, side):
        return (first, (time-start)/(finish-start)) if side == 'start' else (second, (time-finish)/(start-finish))
    return func

membership = {
    4: ('Night', 1.0),
    6: linear('Night', 'Morning', 4, 6),
    10: ('Morning', 1.0),
    12: linear('Morning', 'Noon', 10, 12),
    14: linear('Noon', 'Afternoon', 12, 14),
    16: ('Afternoon', 1.0),
    18: linear('Afternoon', 'Evening', 16, 18),
    22: linear('Evening', 'Night', 18, 22),
    24: ('Night', 1.0)    
}

times = ['Night', 'Morning', 'Noon', 'Afternoon', 'Evening']

def parse_time(line, side):
    hours = int(line[1][:2])+int(line[1][3:5])/60 #number of hours since midnight, rounded down to the closest minute (1/60th of an hour)
    return next(v if isinstance(v, tuple) else v(hours, side) for t, v in membership.items() if t >= hours)

class Behaviour:
    
    def __init__(self, activity_name, sensors, start, finish):
        self.activity_name = activity_name
        self.sensors = sensors
        self.start = start
        self.finish = finish
        start_index = times.index(self.start[0])
        finish_index = times.index(self.finish[0])
        inside_range = start_index > finish_index
        self.time = {}
        for i, t in enumerate(times):
            self.time[t] = inside_range*1.0
            if i is start_index:
                self.time[t] = self.start[1]
                inside_range = True
            if i is finish_index:
                self.time[t] = self.finish[1]
                inside_range = False
    def membership(self, domain, element):
        if domain == 'x': return (element[0] in self.sensors) * self.time[element[1]]
        domain_set = getattr(self, domain)
        return (element in domain_set) * 1 if isinstance(domain_set, set) else domain_set[element]

    def __str__(self):
        return 'Behaviour(' + self.activity_name + ', ' + str(self.sensors) + ', ' + str(self.time) + ')'