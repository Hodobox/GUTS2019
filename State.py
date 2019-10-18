import time

class State:

    def __init__(self):
        # id : object_dict
        self.objects = {}

    def update(self, obj):
        obj['time'] = time.time()
        self.objects[ obj['Id'] ] = obj