from serverComms import *
from mathfuncs import *
import sys
import random

ENEMY = 0
HEALTH = 1
AMMO = 2
GOAL = 3

class Bot:

    def __init__(self,name,server,port,state,w,ws):
        self.i = 0
        self.teamname = name.split(':')[0]
        self.fullname = name
        self.number = int(name.split(':')[1])
        self.server = server
        self.port = port
        self.state = state
        self.id = None
        self.kills = 0
        self.w = w
        self.ws = ws
        self.minDist = 5
        self.minTurn = 5

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

    def getToGoal(self):
        response = []
        targetY = -103 if self.getAttr('Y') < 0 else 103
        targetX = 12 - 8*self.number
        response.append(self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), targetX, targetY ) )
        response.append(self.moveForward(abs(self.getAttr('Y')-targetY)+1))
        return response

    def getAmmo(self):
        response = []
        ammo = self.state.ammo()
        closest = None
        mindist = 1000000
        for pickup in ammo.items():
            distance = dist(self.getAttr('X'), self.getAttr('Y'),pickup[1]['X'], pickup[1]['Y'])
            if distance < mindist:
                closest = pickup[1]
                mindist = distance
        if closest == None:
            return []

        response.append(self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), closest['X'], closest['Y']) )
        response.append(self.moveForward(mindist))
        return response


    def camp(self):
        enemies = self.state.enemies(self.teamname)
        if len(enemies) == 0:
            if random.choice([False,True]):
                return [ self.turnTurretToHeading(0,0) ]
            # else:
            #     return [ self.turnTurretToHeading(100,100) ]
        # find closest enemy
        bestDist = 1000000
        target = None
        for enemy in enemies.items():
            D = dist(self.getAttr('X'),self.getAttr('Y'), enemy[1]['X'],enemy[1]['Y'])
            if D < bestDist:
                bestDist = D
                target = enemy[1]

        print('camping target dist',bestDist)

        if bestDist > 100:
            return []

        TurretHeadingMsg = self.turnTurretToHeading(target['X'],target['Y'])
        TurretHeadingAmount = TurretHeadingMsg[1]['Amount']
        return [ TurretHeadingMsg, self.fire() ]
    
    def calcScore(self, typ, x, y):
        D = dist(self.getAttr('X'), self.getAttr('Y'), x, y)
        score = self.w[typ][0] * D/245 + self.w[typ][1] * self.getAttr('Health')/3 + self.w[typ][2] * self.getAttr('Ammo')/10 + self.w[typ][3] * self.kills + self.w[typ][4]
        return score
    
    def calcShootScore(self, enemy):
        D = dist(self.getAttr('X'), self.getAttr('Y'), enemy['X'], enemy['Y'])
        score = self.ws[0] * D/245 + self.ws[1] * enemy['Health']/3 + self.ws[2] * enemy['Ammo']/10
        return score

    def move(self):
        enemies = self.state.enemies(self.teamname)
        bestPos, bestScore = ( -1 ), 0
        for _, enemy in enemies.items():
            score = self.calcScore(ENEMY, enemy['X'], enemy['Y'])
            if bestPos == ( -1 ) or bestScore < score:
                bestScore = score
                bestPos = ( enemy['X'], enemy['Y'] )
        for _, obj in self.state.objects.items():
            if obj['Type'] == 'HealthPickup':
                score = self.calcScore(HEALTH, obj['X'], obj['Y'])
                if bestPos == ( -1 ) or bestScore < score:
                    bestScore = score
                    bestPos = ( obj['X'], obj['Y'] )
            if obj['Type'] == 'AmmoPickup':
                score = self.calcScore(AMMO, obj['X'], obj['Y'])
                if bestPos == ( -1 ) or bestScore < score:
                    bestScore = score
                    bestPos = ( obj['X'], obj['Y'] )
        score = self.calcScore(GOAL, 0, 100)
        if bestPos == ( -1 ) or bestScore < score:
            bestScore = score
            bestPos = ( 0, 100 )
        score = self.calcScore(GOAL, 0, -100)
        if bestPos == ( -1 ) or bestScore < score:
            bestScore = score
            bestPos = ( 0, -100 )
        if dist(self.getAttr('X'), self.getAttr('Y'), bestPos[0], bestPos[1]) < self.minDist:
            return []
        if abs(getHeading(self.getAttr('X'), self.getAttr('Y'), bestPos[0], bestPos[1]) - self.getAttr('Heading')) < self.minTurn:
            MoveForwardMsg = self.moveForward(10)
            return [ MoveForwardMsg ]
        else:
            HeadingMsg = self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), bestPos[0], bestPos[1])
            return [ HeadingMsg ]

    def shoot(self):
        enemies = self.state.enemies(self.teamname)
        bestName, bestScore = '', 0
        for name, enemy in enemies.items():
            score = self.calcShootScore(enemy)
            if bestName == '' or bestScore < score:
                bestScore = score
                bestName = name
        if bestName == '':
            return []
        if abs(getHeading(self.getAttr('X'), self.getAttr('Y'), enemies[bestName]['X'], enemies[bestName]['Y']) - self.getAttr('TurretHeading')) < self.minTurn:
            FireMsg = self.fire()
            return [ FireMsg ]
        else:
            TurretHeadingMsg = self.turnTurretToHeading(enemies[bestName]['X'], enemies[bestName]['Y'])
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

        if self.id is None:
            return []
        if messageType == ServerMessageTypes.KILL:
            self.kills += 1
            response.append(self.turnToHeading(self.getAttr('X'),self.getAttr('Y'),0,0))
            response.append(self.moveForward(25))
            return response
        if messageType == ServerMessageTypes.ENTEREDGOAL:
            self.kills = 0
        return self.move() + self.shoot()
        '''Ypos = self.state.getAttr(self.id, 'Y')
        if abs(Ypos) > 100 and self.state.getAttr(self.id, 'Ammo') > 0: # we are in goal with ammo, camp
            return self.camp()
        elif self.state.getAttr(self.id, 'Ammo') == 0:
            return self.getAmmo()
        else:
            return self.getToGoal()'''

    def activate(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name' : self.fullname})
        logging.info(self.fullname + ' activated!')
        while True:
            message = self.server.readMessage()
            commands = self.receiveMessage(message)
            for command in commands:
                self.server.sendMessage(command[0],command[1] if len(command)>1 else None)