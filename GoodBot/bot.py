from serverComms import *
from mathfuncs import *
import sys
import random
import math

ENEMY = 0
HEALTH = 1
AMMO = 2
GOAL = 3

class Bot:

    def __init__(self,i,name,server,port,state):
        self.i = i
        self.teamname = name.split(':')[0]
        self.fullname = name
        self.number = int(name.split(':')[1])
        self.server = server
        self.port = port
        self.state = state
        self.id = None
        self.minDist = 15
        self.minTurn = 4

    def getAttr(self,Attr):
        return self.state.getAttr(self.id,Attr)

    def turnToHeading(self,x,y,X,Y):
        return [ServerMessageTypes.TURNTOHEADING, {'Amount' : int(math.floor(getHeading(x,y,X,Y)) + 0.5) }]

    def turnTurretToHeading(self,X,Y):
        return [ServerMessageTypes.TURNTURRETTOHEADING, {'Amount' : int(math.floor(getHeading(self.getAttr('X'), self.getAttr('Y'), X, Y)) + 0.5) }]
         
    def fire(self):
        return [ServerMessageTypes.FIRE]

    def moveForward(self, dist):
        return [ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount' : dist}]

    def move(self):
        gx, gy = None, None
        flag = False
        if self.state.kills[self.id] != 0 or self.state.snitch_id == self.id:
            neg, pos = 0, 0
            enemies = self.state.enemies(self.teamname)
            for id, enemy in enemies.items():
                if enemy['Y'] < self.getAttr('Y'):
                    neg += 1
                if enemy['Y'] > self.getAttr('Y'):
                    pos += 1
            gx = 0
            if pos > 2:
                gy = -105
            elif neg > 2:
                gy = 105
            else:
                gy = -105 if self.getAttr('Y') < 0 else 105
            print(self.i, gy, "objective")
        elif self.getAttr('Health') <= 1 or (self.getAttr('Health') <= 1 and not self.state.snitch):
            chosen = None
            self.state.lock.acquire()
            try:
                for _, obj in self.state.objects.items():
                    if obj['Type'] == 'HealthPickup' and (obj['Id'] not in self.state.pickups or self.state.pickups[obj['Id']] == self.id or self.state.objects[self.state.pickups[obj['Id']]]['Health'] <= 0) and (chosen is None or dist(self.getAttr('X'), self.getAttr('Y'), obj['X'], obj['Y']) < dist(self.getAttr('X'), self.getAttr('Y'), chosen['X'], chosen['Y'])):
                        chosen = obj
            finally:
                self.state.lock.release()
            if chosen is not None and dist(self.getAttr('X'), self.getAttr('Y'), chosen['X'], chosen['Y']) < 100:
                self.state.pickups[chosen['Id']] = self.id
                gx = chosen['X']
                gy = chosen['Y']
        elif self.getAttr('Ammo') <= 0 or (self.getAttr('Ammo') <= 2 and not self.state.snitch):
            chosen = None
            self.state.lock.acquire()
            try:
                for _, obj in self.state.objects.items():
                    if obj['Type'] == 'AmmoPickup' and (obj['Id'] not in self.state.pickups or self.state.pickups[obj['Id']] == self.id or self.state.objects[self.state.pickups[obj['Id']]]['Health'] <= 0) and (chosen is None or dist(self.getAttr('X'), self.getAttr('Y'), obj['X'], obj['Y']) < dist(self.getAttr('X'), self.getAttr('Y'), chosen['X'], chosen['Y'])):
                        chosen = obj
            finally:
                self.state.lock.release()
            if chosen is not None and dist(self.getAttr('X'), self.getAttr('Y'), chosen['X'], chosen['Y']) < 100:    
                self.state.pickups[chosen['Id']] = self.id
                gx = chosen['X']
                gy = chosen['Y']
        if gx is None:
            neg, pos = 0, 0
            '''enemies = self.state.enemies(self.teamname)
            for id, enemy in enemies.items():
                if enemy['Y'] < self.getAttr('Y'):
                    neg += 1
                if enemy['Y'] > self.getAttr('Y'):
                    pos += 1'''
            allies = self.state.allies(self.teamname)
            for id, ally in allies.items():
                if ally['Y'] < 0:
                    neg += 1
                else:
                    pos += 1
            gx = 5 + 10 * (self.i-2)
            gy = 85 if pos >= 2 else -85
            for id, obj in self.state.objects.items():
                if obj['Type'] == 'Snitch' and self.state.snitch:
                    gx, gy = self.predict(obj)
                    flag = True
        if abs(getHeading(self.getAttr('X'), self.getAttr('Y'), gx, gy) - self.getAttr('Heading')) < self.minTurn:
            MoveForwardMsg = self.moveForward(10)
            return [ MoveForwardMsg ]
        else:
            HeadingMsg = self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), gx, gy)
            if flag:
                MoveForwardMsg = self.moveForward(10)
                return [ HeadingMsg, MoveForwardMsg ]
            else:
                return [ HeadingMsg ]

    def safeShot(self, enemy, sx, sy):
        allies = self.state.allies(self.teamname)
        for _, ally in allies.items():
            if min(self.getAttr('X'), sx) <= ally['X'] and ally['X'] <= max(self.getAttr('X'), sx) and ally['Id'] != self.getAttr('Id') and ally['Id'] != enemy['Id'] and abs((sy - self.getAttr('Y')) * ally['X'] - (sx - self.getAttr('X')) * ally['Y'] + sx * self.getAttr('Y') - sy * self.getAttr('X'))/sqrt((sy - self.getAttr('Y')) ** 2 + (sx - self.getAttr('X')) ** 2) < 10.0:
                return False
        return True

    def predict(self, obj):
        sx, sy = obj['X'], obj['Y']
        return sx, sy
        if obj['Id'] in self.state.oldObjs:
            dx, dy = obj['X'] - self.state.oldObjs[obj['Id']]['X'], obj['Y'] - self.state.oldObjs[obj['Id']]['Y']
            length = math.hypot(dx, dy)
            if length > 0:
                dx, dy = dx / length, dy / length
                d = dist(self.getAttr('X'), self.getAttr('Y'), obj['X'], obj['Y'])
                if d > 0:
                    sx, sy = sx + 1.5 * dx * d, sy + 1.5 * dy * d
        return sx, sy

    def shoot(self):
        target = -1
        tx, ty = 0, 0
        allies = self.state.allies(self.teamname)
        flag = False
        if target == -1:
            enemies = self.state.enemies(self.teamname)
            for id, enemy in enemies.items():
                #sx, sy = self.predict(enemy)
                sx, sy = enemy['X'], enemy['Y']
                if dist(self.getAttr('X'), self.getAttr('Y'), sx, sy) < 100 and enemy['Health'] >= 1 and (target == -1 or target['Id'] != self.state.snitch_id) and (target == -1 or enemy['Health'] < target['Health'] or (enemy['Health'] == target['Health'] and dist(self.getAttr('X'), self.getAttr('Y'), sx, sy) < dist(self.getAttr('X'), self.getAttr('Y'), tx, ty))) and self.safeShot(enemy, sx, sy):
                    target = enemy
                    tx, ty = sx, sy
        if target == -1:
            for id, ally in allies.items():
                #sx, sy = self.predict(ally)
                sx, sy = ally['X'], ally['Y']
                if id != self.id and ally['Health'] == 1 and self.state.kills[id] == 0 and self.state.snitch_id != id and self.safeShot(ally, sx, sy):
                    target = ally
                    tx, ty = sx, sy
                    break
                    
        self.state.lock.acquire()
        try:
            for id, obj in self.state.objects.items():
                sx, sy = obj['X'], obj['Y']
                if self.state.snitch and obj['Type'] == 'Snitch' and dist(self.getAttr('X'), self.getAttr('Y'), sx, sy) < 45:
                    target = obj
                    tx, ty = sx, sy
                    flag = True
        finally:
            self.state.lock.release()
        if target == -1:
            return [ [ ServerMessageTypes.TURNTURRETTOHEADING, { 'Amount' : ((self.getAttr('TurretHeading') + 60) % 360) } ] ]
        if not flag and abs(getHeading(self.getAttr('X'), self.getAttr('Y'), tx, ty) - self.getAttr('TurretHeading')) < self.minTurn:
            FireMsg = self.fire()
            return [ FireMsg ]
        else:
            TurretHeadingMsg = self.turnTurretToHeading(tx, ty)
            return [ TurretHeadingMsg ]

    def receiveMessage(self, message):
        messageType = message['messageType']
        response = []
        #logging.info(message)

        if messageType == ServerMessageTypes.OBJECTUPDATE:
            self.state.update(message)
            #logging.info(message)
            if self.id is None and message['Name'] == self.fullname:
                self.id = message['Id']
                self.state.kills[self.id] = 0

        if self.id is None:
            return []
        if messageType == ServerMessageTypes.KILL:
            self.state.kills[self.id] += 1
        if messageType == ServerMessageTypes.ENTEREDGOAL:
            self.state.kills[self.id] = 0
        if messageType == ServerMessageTypes.SNITCHPICKUP:
            self.state.snitch = False
            self.state.snitch_id = message['Id']
        if messageType == ServerMessageTypes.SNITCHAPPEARED:
            self.state.snitch = True
        return self.move() + self.shoot()

    def activate(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name' : self.fullname})
        logging.info(self.fullname + ' activated!')
        while True:
            message = self.server.readMessage()
            commands = self.receiveMessage(message)
            for command in commands:
                self.server.sendMessage(command[0],command[1] if len(command)>1 else None)