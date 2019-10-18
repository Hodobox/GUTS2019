from serverComms import *
import sys

class Bot:

    def __init__(self,name,server,port,state):
        self.i = 0
        self.teamname = name.split(':')[0]
        self.fullname = name
        self.server = server
        self.port = port
        self.state = state

    def receiveMessage(self, message):
        messageType = message['messageType']
        response = []
        logging.info(message)

        if messageType == ServerMessageTypes.OBJECTUPDATE:
            pass
            #self.state.update(message)

        if self.i == 5:
            if random.randint(0, 10) > 5:
                logging.info("Firing")
                response.append([ServerMessageTypes.FIRE])
        elif self.i == 10:
            #logging.info("Turning randomly")
            response.append((ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0, 359)}))
        elif self.i == 15:
            #logging.info("Moving randomly")
            response.append((ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': random.randint(0, 10)}))
        self.i = self.i + 1
        if self.i > 20:
            self.i = 0
        return response

    def activate(self):
        self.server.sendMessage(ServerMessageTypes.CREATETANK, {'Name' : self.fullname})
        logging.info(self.fullname + ' activated!')
        while True:
            message = self.server.readMessage()
            commands = self.receiveMessage(message)
            for command in commands:
                self.server.sendMessage(command[0],command[1] if len(command)>1 else None)