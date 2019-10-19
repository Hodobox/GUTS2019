from serverComms import *
from mathfuncs import *
import sys

class Bot:

    def __init__(self,name,server,port,state):
        self.i = 0
        self.teamname = name.split(':')[0]
        self.fullname = name
        self.server = server
        self.port = port
        self.state = state
        self.id = None
        self.lock = False

    def receiveMessage(self, message):
        messageType = message['messageType']
        response = []
        #logging.info(message)

        if messageType == ServerMessageTypes.OBJECTUPDATE:
            self.state.update(message)
            #logging.info(message)
            if self.id is None and message['Name'] == self.fullname:
                self.id = message['Id']
        elif messageType == ServerMessageTypes.KILL:
            x,y,X,Y = self.state.objects[self.id]['X'],self.state.objects[self.id]['Y'],0,-100
            goalheading = getHeading(x,y,X,Y)
            response.append([ServerMessageTypes.TURNTOHEADING,{'Amount' : goalheading}])
            response.append([ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount':20}])
            self.lock = True
            return response
        elif messageType == ServerMessageTypes.ENTEREDGOAL:
            response.append([ServerMessageTypes.TURNTOHEADING,{'Amount' : 270}])
            response.append([ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount':100}])
            self.lock = False
            return response
        elif messageType == ServerMessageTypes.DESTROYED:
            self.lock = False

        if self.id is None:
            return []

        if self.lock:
            x,y,X,Y = self.state.objects[self.id]['X'],self.state.objects[self.id]['Y'],0,-100
            goalheading = getHeading(x,y,X,Y)
            response.append([ServerMessageTypes.TURNTOHEADING,{'Amount' : goalheading}])
            response.append([ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount':20}])
            return response

        enemies = self.state.enemies(self.teamname)

        if len(enemies) > 0:
            target = list(enemies.items())[0][1]
            x,y,X,Y = self.state.objects[self.id]['X'],self.state.objects[self.id]['Y'],target['X'],target['Y']
            #print('I am at',x,y,'target is at',X,Y)
            heading = getHeading(x,y,X,Y)
            if abs(heading - self.state.objects[self.id]['TurretHeading']) < 1:
                print('firing')
                response.append([ServerMessageTypes.FIRE])
            else:
                print('turning',heading)
                response.append([ServerMessageTypes.TURNTOHEADING,{'Amount' : heading}])

        return response

    def activate(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name' : self.fullname})
        logging.info(self.fullname + ' activated!')
        while True:
            message = self.server.readMessage()
            commands = self.receiveMessage(message)
            for command in commands:
                self.server.sendMessage(command[0],command[1] if len(command)>1 else None)