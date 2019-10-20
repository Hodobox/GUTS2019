import time
import copy
from math import *

class State:

    def __init__(self):
        # id : object_dict
        self.objects = {}
        self.last_clear = time.time()
        self.suicides = set()
        self.snitch = None
        self.snitchObj = None
        self.Last_point_scored = time.time()
        self.RAMBO_SWITCHING = False

    def update(self, obj):
        
        if obj['Type'] == 'Snitch':
            #print('yay snitch found')
            obj['time'] = time.time()
            self.snitchObj = obj
            return
        elif self.snitchObj != None and time.time() - self.snitchObj['time'] > 10:
            self.snitchObj = None

        if obj['Id'] in self.objects and obj['Type'] == 'Tank':
            timediff = time.time() - self.objects[obj['Id']]['time']
            if timediff != 0:
                dx = obj['X'] - self.objects[ obj['Id'] ]['X']
                dy = obj['Y'] - self.objects[ obj['Id'] ]['Y']
                # velocity = sqrt(dx**2 + dy**2)
                # obj['velocity'] = velocity
                obj['dy'] = dy/timediff
                obj['dx'] = dx/timediff

        obj['time'] = time.time()

        self.objects[ obj['Id'] ] = obj

        if time.time() - self.last_clear > 4:
            self.last_clear = time.time()
            #print(time.time())
            outdated = []
            for key in self.objects:
                if time.time() - self.objects[key]['time'] > 5:
                    outdated.append(key)
            for trash in outdated:
                #print('throwing out',self.objects[trash])
                self.objects.pop(trash)

    def getAttr(self, Id, Attr):
        if Id not in self.objects:
            return None
        return self.objects[Id][Attr]

    def enemies(self, teamname):
        res = {}
        for Id in self.objects:
            if teamname not in self.objects[Id]['Name'] and self.objects[Id]['Type'] == 'Tank' and self.objects[Id]['Health'] > 0:
                res[Id] = copy.deepcopy(self.objects[Id])
        return res

    def getSnitch(self):
        return self.snitchObj

    def ammo(self):
        res = {}
        for Id in self.objects:
            if self.objects[Id]['Type'] == 'AmmoPickup':
                res[Id] = copy.deepcopy(self.objects[Id])
        return res

    def health(self):
        res = {}
        for Id in self.objects:
            if self.objects[Id]['Type'] == 'HealthPickup':
                res[Id] = copy.deepcopy(self.objects[Id])
        return res