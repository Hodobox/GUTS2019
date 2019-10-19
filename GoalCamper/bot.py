from serverComms import *
from mathfuncs import *
import sys

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
         
    def fire(self):
        return [ServerMessageTypes.FIRE]

    def moveForward(self, dist):
        return [ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount' : dist}]

    def getToGoal(self):
        response = []
        targetY = -101 if self.getAttr('Y') < 0 else 101
        targetX = 12 - 8*self.number
        response.append(self.turnToHeading(self.getAttr('X'), self.getAttr('Y'), targetX, targetY ) )
        response.append(self.moveForward(abs(self.getAttr('Y')-targetY)+1))
        return response

    def getAmmo(self):
        return []

    def camp(self):
        return []
        #target = list(enemies.items())[0][1]
        #x,y,X,Y = self.state.objects[self.id]['X'],self.state.objects[self.id]['Y'],target['X'],target['Y']  

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

        Ypos = self.state.getAttr(self.id, 'Y')
        if abs(Ypos) > 100 and self.state.getAttr(self.id, 'Ammo') > 0: # we are in goal with ammo, camp
            return self.camp()
        elif self.state.getAttr(self.id, 'Ammo') == 0:
            return self.getAmmo()
        else:
            return self.getToGoal()

        enemies = self.state.enemies(self.teamname)
        return response

    def activate(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name' : self.fullname})
        logging.info(self.fullname + ' activated!')
        while True:
            message = self.server.readMessage()
            commands = self.receiveMessage(message)
            for command in commands:
                self.server.sendMessage(command[0],command[1] if len(command)>1 else None)