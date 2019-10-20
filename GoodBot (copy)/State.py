import time
import copy
from threading import RLock

class State:

    def __init__(self):
        # id : object_dict
        self.objects = {}
        self.last_clear = time.time()
        self.kills = {}
        self.pickups = {}
        self.snitch_id = -1
        self.snitch = False
        self.lock = RLock()
        self.oldObjs = {}

    def update(self, obj):
        obj['time'] = time.time()
        if obj['Id'] in self.objects:
            self.oldObjs[obj['Id']] = self.objects[obj['Id']]
        self.objects[ obj['Id'] ] = obj
        self.lock.acquire()
        try:
            if time.time() - self.last_clear > 0.5:
                self.last_clear = time.time()
                outdated = []
                for key in self.objects:
                    if time.time() - self.objects[key]['time'] > 5:
                        outdated.append(key)
                for trash in outdated:
                    self.objects.pop(trash)
        finally:
            self.lock.release()

    def getAttr(self, Id, Attr):
        if Id not in self.objects:
            return None
        return self.objects[Id][Attr]

    def enemies(self, teamname):
        res = {}
        self.lock.acquire()
        try:
            for Id in self.objects:
                if teamname not in self.objects[Id]['Name'] and self.objects[Id]['Type'] == 'Tank':
                    res[Id] = copy.deepcopy(self.objects[Id])
        finally:
            self.lock.release()
        return res

    def allies(self, teamname):
        res = {}
        self.lock.acquire()
        try:
            for Id in self.objects:
                if teamname in self.objects[Id]['Name'] and self.objects[Id]['Type'] == 'Tank':
                    res[Id] = copy.deepcopy(self.objects[Id])
        finally:
            self.lock.release()
        return res

    def ammo(self):
        res = {}
        self.lock.acquire()
        try:
            for Id in self.objects:
                if self.objects[Id]['Type'] == 'AmmoPickup':
                    res[Id] = copy.deepcopy(self.objects[Id])
        finally:
            self.lock.release()
        return res