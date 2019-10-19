from serverComms import *
from mathfuncs import *
import sys
import random

class Bot:

    def __init__(self,name,server,port,state):
        self.i = 0
        self.teamname = name.split(':')[0]
        self.fullname = name
        self.number = int(name.split(':')[1])
        self.server = server
        self.port = port
        self.state = state
        self.id = None

    def getAttr(self,Attr):
        return self.state.getAttr(self.id,Attr)

    def turnToHeading(self,x,y,X,Y):
        return [ServerMessageTypes.TURNTOHEADING, {'Amount' : getHeading(x,y,X,Y)}]

    def turnTurretToHeading(self,X,Y):
        return [ServerMessageTypes.TURNTURRETTOHEADING, {'Amount' : getHeading(self.getAttr('X'), self.getAttr('Y'), X, Y) }]
         
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
            else:
                return [ self.turnTurretToHeading(100,100) ]
        # find closest enemy
        bestDist = 1000000
        target = None
        for enemy in enemies.items():
            D = dist(self.getAttr('X'),self.getAttr('Y'), enemy[1]['X'],enemy[1]['Y'])
            if D < bestDist:
                bestDist = D
                target = enemy[1]

        if bestDist > 100:
            return []
        #preaim enemy
        prex, prey = preaim(self.getAttr('X'), self.getAttr('Y'), target)
        TurretHeadingMsg = self.turnTurretToHeading(prex, prey)
        TurretHeadingAmount = TurretHeadingMsg[1]['Amount']
        return [ TurretHeadingMsg, self.fire() ]

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
            response.append(self.turnToHeading(self.getAttr('X'),self.getAttr('Y'),0,0))
            response.append(self.moveForward(25))
            return response

        Ypos = self.state.getAttr(self.id, 'Y')
        if abs(Ypos) > 100 and self.state.getAttr(self.id, 'Ammo') > 0: # we are in goal with ammo, camp
            return self.camp()
        elif self.state.getAttr(self.id, 'Ammo') == 0:
            return self.getAmmo()
        else:
            return self.getToGoal()

        return response

    def activate(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name' : self.fullname})
        logging.info(self.fullname + ' activated!')
        while True:
            message = self.server.readMessage()
            commands = self.receiveMessage(message)
            for command in commands:
                self.server.sendMessage(command[0],command[1] if len(command)>1 else None)