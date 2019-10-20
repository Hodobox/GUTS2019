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
        self.switchGoal = None

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

    def moveBackward(self, dist):
        return [ ServerMessageTypes.MOVEBACKWARSDISTANCE,{'Amount' : dist} ]

    def turnToHeadingBackwards(self,x,y,X,Y):
        return [ServerMessageTypes.TURNTOHEADING, {'Amount' : oppositeDegree(getHeading(x,y,X,Y)) }]

    def moveToPointFixedDist(self, x,y, DIST):
        response = []

        turnForwardTime = ForwardTurnTime(self.getAttr('Heading'), self.getAttr('X'),self.getAttr('Y'),x,y)
        turnBackwardTime = BackwardTurnTime(self.getAttr('Heading'),self.getAttr('X'),self.getAttr('Y'),x,y)

        if turnForwardTime > turnBackwardTime:
            response.append(self.turnToHeadingBackwards(self.getAttr('X'),self.getAttr('Y'),x,y))
            response.append(self.moveBackward(DIST))
        else:
            response.append(self.turnToHeading(self.getAttr('X'),self.getAttr('Y'),x,y))
            response.append(self.moveForward(DIST))

        return response

    def moveToPoint(self,x,y,overhead=0):
        response = []

        turnForwardTime = ForwardTurnTime(self.getAttr('Heading'),self.getAttr('X'),self.getAttr('Y'),x,y)
        turnBackwardTime = BackwardTurnTime(self.getAttr('Heading'),self.getAttr('X'),self.getAttr('Y'),x,y)

        if turnForwardTime > turnBackwardTime:
            response.append(self.turnToHeadingBackwards(self.getAttr('X'),self.getAttr('Y'),x,y))
            response.append(self.moveBackward(dist(self.getAttr('X'),self.getAttr('Y'),x,y)+overhead))
        else:
            response.append(self.turnToHeading(self.getAttr('X'),self.getAttr('Y'),x,y))
            response.append(self.moveForward(dist(self.getAttr('X'),self.getAttr('Y'),x,y)+overhead))

        return response

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
        snitch = False
        
        #if self.state.snitch:
           #print('maybe snitch violence',self.state.snitch)

        for enemy in enemies.items():
            D = dist(self.getAttr('X'),self.getAttr('Y'), enemy[1]['X'],enemy[1]['Y'])
            #if self.state.snitch == enemy[1]['Id']:
                #print('oooh ',enemy[1]['Id'],D)
            if (D < bestDist and snitch == False) or (D < 100 and self.state.snitch != None and enemy[1]['Id'] == self.state.snitch):
                bestDist = D
                target = enemy[1]
                if(D < 100 and self.state.snitch != None and enemy[1]['Id'] == self.state.snitch):
                    #print('REEE SNITCH')
                    snitch = True

        if (bestDist < 80) or (bestDist < 100 and len(self.state.suicides) > 1 + (1 if self.id in self.state.suicides else 0) ):
            #preaim enemy
            #print('I hunt')
            prex, prey = preaim(self.getAttr('X'), self.getAttr('Y'), target)
            TurretHeadingMsg = self.turnTurretToHeading(prex, prey)
            TurretHeadingAmount = TurretHeadingMsg[1]['Amount']
            response += [TurretHeadingMsg, self.fire()]
            if snitch and self.getAttr('Ammo') > 0:
                #also chase that MF
                response += self.moveToPoint(target['X'],target['Y'],2)
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
        response += self.moveToPoint(targetX,targetY,1)
        return response

    def switchGoals(self):
        response = self.violence()

        if self.switchGoal == None:
            #get to goal
            targetY = 103 if self.getAttr('Y') < 0 else -103
            targetX = 12 - 8*self.number
            response += self.moveToPoint(targetX, targetY)
            self.switchGoal = targetY
        else:
            if abs(self.switchGoal - self.getAttr('Y')) < 5:
                self.switchGoal = None
                print('Rambo can rest')
            else:
                targetX = 12 - 8*self.number
                response += self.moveToPoint(targetX, self.switchGoal)
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
            response += self.moveToPoint(0,0)
            if random.choice([False,True]):
                response.append(self.turnTurretToHeading(-100,-100))
            else:
                response.append(self.turnTurretToHeading(100,100))
            return response
        # move to ammo
        response += self.moveToPoint(closest['X'],closest['Y'])
        return response

    # returns True if we want to go get health
    def getHealth(self, response):
        health = self.state.health()
        for objId in health:
            D = dist(self.getAttr('X'),self.getAttr('Y'),health[objId]['X'],health[objId]['Y'])
            if D < 50:
                response += self.moveToPoint(health[objId]['X'],health[objId]['Y'],1)
                print(self.id, 'I NEED HEALING')
                return True
        return False

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
            print(self.id,': died and lost',self.points)
            self.points = 0
            if self.id in self.state.suicides:
                print(self.id,': I want to live')
                self.state.suicides.remove(self.id)

        if messageType == ServerMessageTypes.KILL:
            self.points += 1
            print(self.id,' has a kill!')
            if self.id in self.state.suicides:
                print(self.id,': I want to live')
                self.state.suicides.remove(self.id)

        if messageType == ServerMessageTypes.ENTEREDGOAL:
            self.points = 0

        if messageType == ServerMessageTypes.HEALTHPICKUP:
            if self.id in self.state.suicides:
                print(self.id,': I want to live')
                self.state.suicides.remove(self.id)

        if messageType == ServerMessageTypes.SNITCHPICKUP:
            Id = message['Id']
            print('SNITCHER',Id)
            self.state.snitch = Id
            if Id == self.id:
                print('lol I has snitch')
                self.points += 5

        if self.id is None:
            return []

        # Do not touch unless you need to unleash more than 5% of your power
        #if self.getAttr('Health') == 1:
        #    print(self.id,'is being banished to the shadow realm!!!')
        #    self.id = None
        #    return [ [ServerMessageTypes.DESPAWNTANK] , [ServerMessageTypes.CREATETANK, {'Name' : self.fullname} ] ]

        
        if self.points > 0:
            if abs(self.getAttr('Y')) > 99:
                response += self.moveToPointFixedDist(0,0,abs(self.getAttr('Y')-99) + 3)
                response += self.violence()
                return response
            else:
                return self.getToGoal()

        if self.state.snitchObj != None:
            #print(self.id,'afaik',dist(self.getAttr('X'),self.getAttr('Y'),self.state.getSnitch()['X'],self.state.getSnitch()['Y']),'from being harry')
            if dist(self.getAttr('X'),self.getAttr('Y'),self.state.getSnitch()['X'],self.state.getSnitch()['Y']) < 25:
                print(self.id,'I am harry potter!!!')
                response = self.violence()
                if time.time() - self.state.getSnitch()['time'] > 3:
                    #print(self.id,'Fix your glasses harry!!!')
                    response = [ self.turnTurretToHeading(self.state.getSnitch()['X'],self.state.getSnitch()['Y']) ]
                
                response += self.moveToPoint(self.state.getSnitch()['X'],self.state.getSnitch()['Y'],5)
                return response

        bestDist = 1000000
        for enemy in self.state.enemies(self.teamname).items():
            D = dist(self.getAttr('X'),self.getAttr('Y'), enemy[1]['X'],enemy[1]['Y'])
            if D < bestDist:
                bestDist = D

        if bestDist < 100 or self.lastSeen == None:
            self.lastSeen = time.time()
        elif time.time() - self.lastSeen > 5:
            print("Switching goals.")
            return self.switchGoals()

        if  self.switchGoal != None:
            print('Rambo switch')
            return self.switchGoals()

        response = self.violence()
        if self.getAttr('Health') < 3:
            if self.getHealth(response):
                return response


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