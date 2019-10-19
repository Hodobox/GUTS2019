from serverComms import *
from mathfuncs import *
import sys
import random
import time
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
        self.lastSeen = None
        self.points = 0

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

    def sumTeamDist(self, x, y):
        res = 0
        for objId in self.state.objects:
            if self.state.getAttr(objId, 'Type') == 'Tank' and self.teamname in self.state.getAttr(objId, 'Name'):
                res += dist(self.state.getAttr(objId,'X'),self.state.getAttr(objId,'Y'),x,y)
        return res

    def violence(self):
         
        response = []
        enemies = self.state.enemies(self.teamname)
        
        bestDist = 1000000
        target = None
        for enemy in enemies.items():
            D = dist(self.getAttr('X'),self.getAttr('Y'), enemy[1]['X'],enemy[1]['Y'])
            if D < bestDist:
                bestDist = D
                target = enemy[1]

        if (bestDist < 80) or (bestDist < 100 and len(self.state.suicides) > 1 + (1 if self.id in self.state.suicides else 0) ):
            #preaim enemy
            #print('I hunt')
            prex, prey = preaim(self.getAttr('X'), self.getAttr('Y'), target)
            TurretHeadingMsg = self.turnTurretToHeading(prex, prey)
            TurretHeadingAmount = TurretHeadingMsg[1]['Amount']
            response += [TurretHeadingMsg, self.fire()]
        else: # try assisted suicide
            bestDist = 1000000
            target = None
            for suicidal in self.state.suicides:
                if suicidal == self.id:
                    continue
                X,Y = self.state.getAttr(suicidal,'X'),self.state.getAttr(suicidal,'Y')
                D = dist(self.getAttr('X'),self.getAttr('Y'),X,Y)
                if D < bestDist:
                    target = suicidal
                    bestDist = D

            if bestDist < 30:
                print('Suicide hotline is here')
                prex, prey = preaim(self.getAttr('X'), self.getAttr('Y'), self.state.objects[target])
                TurretHeadingMsg = self.turnTurretToHeading(prex, prey)
                response += [ TurretHeadingMsg, self.fire() ]

        return response

    def getToGoal(self):
        response = self.violence()

        sumLeft = self.sumTeamDist(0,-100)
        sumRight = self.sumTeamDist(0,100)

        #get to goal
        targetY = -103 if sumLeft < sumRight else 103
        targetX = 12 - 8*self.number
        response.append(self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), targetX, targetY ) )
        response.append(self.moveForward(abs(self.getAttr('Y')-targetY)+1))
        return response

    def switchGoals(self):
        response = self.violence()

        #get to goal
        targetY = 103 if self.getAttr('Y') < 0 else -103
        targetX = 12 - 8*self.number
        response.append(self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), targetX, targetY ) )
        response.append(self.moveForward(dist(self.getAttr('X'), self.getAttr('Y'), targetX, targetY)))
        return response

    def getAmmo(self):

        response = self.violence()

        #find ammo pickup
        ammo = self.state.ammo()
        closest = None
        mindist = 1000000
        for pickup in ammo.items():
            distance = dist(self.getAttr('X'), self.getAttr('Y'),pickup[1]['X'], pickup[1]['Y'])
            if distance < mindist:
                closest = pickup[1]
                mindist = distance
        if closest == None:
            response.append(self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), 0, 0) )
            response.append(self.moveForward(dist(self.getAttr('X'), self.getAttr('Y'), 0, 0)))
            if random.choice([False,True]):
                response.append(self.turnTurretToHeading(-100,-100))
            else:
                response.append(self.turnTurretToHeading(100,100))
            return response
        # move to ammo
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
        
        return self.violence()

    def receiveMessage(self, message):
        messageType = message['messageType']
        response = []
        #logging.info(message)

        if messageType == ServerMessageTypes.OBJECTUPDATE:
            self.state.update(message)
            #logging.info(message)
            if self.id is None and message['Name'] == self.fullname:
                self.id = message['Id']

        if messageType == ServerMessageTypes.HITDETECTED:
            print(self.id,'has been hit. Health:',self.getAttr('Health'))
            if self.getAttr('Health') == 2 and self.points == 0:
                print(self.id,': I am suiciding')
                self.state.suicides.add(self.id)

        if messageType == ServerMessageTypes.DESTROYED:
            self.points = 0
            if self.id in self.state.suicides:
                print(self.id,': I want to live')
                self.state.suicides.remove(self.id)


        if messageType == ServerMessageTypes.KILL:
            self.points += 1
            if self.id in self.state.suicides:
                self.state.suicides.remove(self.id)

        if messageType == ServerMessageTypes.ENTEREDGOAL:
            self.points = 0

        if self.id is None:
            return []
        
        if self.points > 0:
            if abs(self.getAttr('Y')) > 99:
                response.append(self.turnToHeading(self.getAttr('X'),self.getAttr('Y'),0,0))
                response.append(self.moveForward( abs(self.getAttr('Y')-99) + 5 ))
                response += self.violence()
                return response
            else:
                return self.getToGoal()

        bestDist = 1000000
        for enemy in self.state.enemies(self.teamname).items():
            D = dist(self.getAttr('X'),self.getAttr('Y'), enemy[1]['X'],enemy[1]['Y'])
            if D < bestDist:
                bestDist = D


        if bestDist < 100 or self.lastSeen == None:
            self.lastSeen = time.time()
        elif time.time() - self.lastSeen > 5:
            print("Switching goals. ")
            return self.switchGoals()


        Ypos = self.state.getAttr(self.id, 'Y')
        if abs(Ypos) > 100 and self.state.getAttr(self.id, 'Ammo') > 2: # we are in goal with ammo, camp
            return self.camp()
        elif self.state.getAttr(self.id, 'Ammo') < 3:
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