from math import *
PI = 3.1415926535897932384626
def RadToDeg(angle):
    return angle * (180.0 / PI)

def DegToRad(angle):
    return (angle / 180) * PI

def getHeading(x,y,X,Y):
    heading = atan2(Y-y,X-x)
    heading = RadToDeg(heading)
    heading = (360 - heading) % 360
    return abs(heading)

def dist(x1,y1,x2,y2):
	return sqrt((x1 - x2)**2 + (y1 - y2)**2)

def preaim(x, y, target):
	#velocity = 25
	X = target['X']
	Y = target['Y']
	distance = dist(X, Y, x, y)
	if 'dx' in target.keys() and 'dy' in target.keys():
		return (X + distance/25*target['dx'], Y + distance/25*target['dy'])
	else: 
		return (X + cos(DegToRad(target['Heading']))*distance/25*10, Y + sin(DegToRad(target['Heading']))*distance/25*10)
