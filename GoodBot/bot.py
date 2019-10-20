from serverComms import *
from mathfuncs import *
import sys
import random

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
        self.minDist = 5
        self.minTurn = 2

    def getAttr(self,Attr):
        return self.state.getAttr(self.id,Attr)

    def turnToHeading(self,x,y,X,Y):
        return [ServerMessageTypes.TURNTOHEADING, {'Amount' : int(getHeading(x,y,X,Y))}]

    def turnTurretToHeading(self,X,Y):
        return [ServerMessageTypes.TURNTURRETTOHEADING, {'Amount' : int(getHeading(self.getAttr('X'), self.getAttr('Y'), X, Y)) }]
         
    def fire(self):
        return [ServerMessageTypes.FIRE]

    def moveForward(self, dist):
        return [ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount' : dist}]

    def move(self):
        gx, gy = 0, 0
        flag = False
        if self.state.kills[self.id] != 0 or self.state.snitch_id == self.id:
            neg, pos = 0, 0
            enemies = self.state.enemies(self.teamname)
            for id, enemy in enemies.items():
                if enemy['X'] < self.getAttr('X'):
                    neg += 1
                if enemy['X'] > self.getAttr('X'):
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
            for _, obj in self.state.objects.items():
                if obj['Type'] == 'HealthPickup' and (obj['Id'] not in self.state.pickups or self.state.pickups[obj['Id']] == self.id or self.state.objects[self.state.pickups[obj['Id']]]['Health'] <= 0) and (chosen is None or dist(self.getAttr('X'), self.getAttr('Y'), obj['X'], obj['Y']) < dist(self.getAttr('X'), self.getAttr('Y'), chosen['X'], chosen['Y'])):
                    chosen = obj
            if chosen is not None:
                self.state.pickups[chosen['Id']] = self.id
                gx = chosen['X']
                gy = chosen['Y']
        elif self.getAttr('Ammo') <= 0 or (self.getAttr('Ammo') <= 2 and not self.state.snitch):
            chosen = None
            for _, obj in self.state.objects.items():
                if obj['Type'] == 'AmmoPickup' and (obj['Id'] not in self.state.pickups or self.state.pickups[obj['Id']] == self.id or self.state.objects[self.state.pickups[obj['Id']]]['Health'] <= 0) and (chosen is None or dist(self.getAttr('X'), self.getAttr('Y'), obj['X'], obj['Y']) < dist(self.getAttr('X'), self.getAttr('Y'), chosen['X'], chosen['Y'])):
                    chosen = obj
            if chosen is not None:    
                self.state.pickups[chosen['Id']] = self.id
                gx = chosen['X']
                gy = chosen['Y']
        else:
            neg, pos = 0, 0
            enemies = self.state.enemies(self.teamname)
            for id, enemy in enemies.items():
                if enemy['X'] < self.getAttr('X'):
                    neg += 1
                if enemy['X'] > self.getAttr('X'):
                    pos += 1
            gx = 7.5 + 15 * (self.i-2)
            if pos > 2:
                gy = -85
            elif neg > 2:
                gy = 85
            else:
                gy = -85 if self.getAttr('Y') < 0 else 85
            for id, obj in self.state.objects.items():
                if obj['Type'] == 'Snitch':
                    gx = obj['X']
                    gy = obj['Y']
                    flag = True
            print(self.i, gy, "bored")
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

    def shoot(self):
        target = -1
        allies = self.state.allies(self.teamname)
        flag = False
        for id, ally in allies.items():
            if id != self.id and ally['Health'] == 1 and self.state.kills[id] == 0 and self.state.snitch_id != id:
                target = ally
                break
        if target == -1:
            enemies = self.state.enemies(self.teamname)
            for id, enemy in enemies.items():
                if dist(self.getAttr('X'), self.getAttr('Y'), enemy['X'], enemy['Y']) < 100 and enemy['Health'] >= 1 and (target == 1 or target['Id'] != self.state.snitch_id) and (target == -1 or enemy['Health'] < target['Health'] or (enemy['Health'] == target['Health'] and dist(self.getAttr('X'), self.getAttr('Y'), enemy['X'], enemy['Y']) < dist(self.getAttr('X'), self.getAttr('Y'), target['X'], target['Y']))):
                    target = enemy
        for id, obj in self.state.objects.items():
            if obj['Type'] == 'Snitch' and dist(self.getAttr('X'), self.getAttr('Y'), obj['X'], obj['Y']) < 25:
                target = obj
                flag = True
        if target == -1:
            print("spinning")
            return [ [ ServerMessageTypes.TURNTURRETTOHEADING, { 'Amount' : ((self.getAttr('TurretHeading') + 30) % 360) } ] ]
        if not flag and abs(getHeading(self.getAttr('X'), self.getAttr('Y'), target['X'], target['Y']) - self.getAttr('TurretHeading')) < self.minTurn:
            FireMsg = self.fire()
            return [ FireMsg ]
        else:
            TurretHeadingMsg = self.turnTurretToHeading(target['X'], target['Y'])
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