from math import *
PI = 3.1415926535897932384626
def RadToDeg(angle):
    return angle * (180.0 / PI)

def getHeading(x,y,X,Y):
    heading = atan2(Y-y,X-x)
    heading = RadToDeg(heading)
    heading = (360 - heading) % 360
    return abs(heading)

def dist(x1,y1,x2,y2):
	return sqrt((x1 + x2)**2 + (y1 + y2)**2)