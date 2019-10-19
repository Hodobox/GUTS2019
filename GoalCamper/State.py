import time
import copy

class State:

    def __init__(self):
        # id : object_dict
        self.objects = {}

    def update(self, obj):
        obj['time'] = time.time()
        self.objects[ obj['Id'] ] = obj

    def getAttr(self, Id, Attr):
        if Id not in self.objects:
            return None
        return self.objects[Id][Attr]

    def enemies(self, teamname):
        res = {}
        for Id in self.objects:
            if teamname not in self.objects[Id]['Name'] and self.objects[Id]['Type'] == 'Tank':
                res[Id] = copy.deepcopy(self.objects[Id])
        return res