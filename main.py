#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  11 15:30:20 2019

@author: ayoubfoussoul
"""


"""
This will be the main program implementing the mouvement and path finding algorithm

"""
import numpy as np
import time
import path_finding_algorithm as pfa
import connect_robot as cr
import connect_camera as cc
import matplotlib.pyplot as plt
import sys
import itertools
import copy as cp


#################################################### Global variables ####################################################


# TODO : SET VALUES

ratio = 100 #means 1m = ratio points in the matrix
atomDiameter = 0.08 #in meters
ourRobotDiameter = 0.2 #in meters
opponentFirstRobotDiameter = 0.2
opponentSecondRobotDiameter = 0.1
ourRobotInitialPosition = (0.225, 0.75)
opponentFirstRobotInitialPosition = (2.75, 0.5)
opponentSecondRobotInitialPosition = (2.75, 1)
numberOfOpponentRobots = 1 #to be set at the begining of the game
margin = 0 # margin added to the inaccessible area of an element to the robot
space = 0.01 # space between atoms in the periodic table >= 0 (better to set it to more than the precision of the robot mouvement)
displayMessages = True # display print in the program of not
activateDraw = True # activate the function draw(path, table) [deactivate to get an idea on the time needed for calculations only]

# Classes 

class element:
    def __init__(self, x, y, diameter, label):
        self._x = x
        self._y = y
        self._diameter = diameter
        self._label = label # use "theirs1" for opponenet's first robot and "theirs2" for their second one if there is one    
    def __str__(self):
        return str(self._label) + "(x = " + str(round(self._x,3)) + ", y = " + str(round(self._y,3)) + ")"
    def getX(self):
        return self._x
    def getY(self):
        return self._y
    def getDiameter(self):
        return self._diameter
    def getLabel(self):
        return self._label;
    def setX(self, x):
        self._x = x
    def setY(self, y):
        self._y = y
    def setLabel(self, label):
        self._label = label

class robot (element):
    def __init__(self, x, y, diameter, v, theta, label): # for label use "theirs1" for opponenet's first robot and "theirs2" for their second one if there is one
        element.__init__(self, x, y, diameter, label)
        self._v = v
        self._theta = theta
    def getDir(self):
        return self._theta
    def setDir(self, theta):
        self._theta = theta
    def setDiameter(self, diameter):
        self._diameter = diameter
    def __str__(self):
        return "Robot : " + str(self._label) + " (x = " + str(round(self._x,3)) + ", y = " + str(round(self._y,3)) + ", theta = " + str(round(self._theta,3)) + ")"

idIncrement = 0 #to automaticlly set atoms ids

class atom (element):
    def __init__(self, x, y, label, diameter = atomDiameter):
        global Atoms
        global idIncrement
        element.__init__(self, x, y, diameter, label)
        self._id = idIncrement
        idIncrement += 1
        Atoms.append(self)
    def getId(self):
        return self._id
    def setId(self, Id):
        self._id = Id
    def setDiameter(self, diameter):
        self._diameter = diameter
    def __str__(self):
        return "Atom " + str(self._id) + " (x = " + str(round(self._x,3)) + ", y = " + str(round(self._y,3)) + ")"
        
class target (element):
    def __init__(self, x , y, finalRobotOrientation):
        element.__init__(self, x, y, 0.0, "target")
        self._finalRobotOrientation = finalRobotOrientation
    def getFinalRobotOrientation(self):
        return self._finalRobotOrientation
    
        
class colors:
    BLACK   = '\033[1;30m'
    RED     = '\033[1;31m'
    GREEN   = '\033[3;2;32m'
    YELLOW  = '\033[1;33m'
    BLUE    = '\033[1;34m'
    MAGENTA = '\033[1;35m'
    CYAN    = '\033[1;36m'
    WHITE   = '\033[1;37m'
    RESET   = '\033[39m'
    

# more Global Variables : not to be changed
currentMission = 0  
ourRobot = robot(ourRobotInitialPosition[0], ourRobotInitialPosition[1], ourRobotDiameter, 0, 0, "ours")
padding = ourRobot.getDiameter()/2 + margin
opponentFirstRobot = robot(opponentFirstRobotInitialPosition[0], opponentFirstRobotInitialPosition[1], opponentFirstRobotDiameter, 0, 0,"theirs1")
opponentSecondRobot = robot(opponentSecondRobotInitialPosition[0], opponentSecondRobotInitialPosition[1], opponentSecondRobotDiameter, 0, 0,"theirs2")
if numberOfOpponentRobots == 1 : opponentSecondRobot = None
Atoms = []

atomsDisposition = np.array( #red (1) green (2) bleu(3) ourGoldonium(-1) thierGoldonium(-2) START FROM ATOMS WE WILL NOT USE TO ATOMS OF OPPONENET
        [
                
        ##### primary atoms #####
        
         #near table of elements : ours
        atom(0.5, 0.45, 1),
        atom(0.5, 0.75, 1),
        atom(0.5, 1.05, 2),
        
         #in the central cercles : ours
        atom(1, 1.05 + atomDiameter*1.5, 1), #right
        atom(1, 1.05 - atomDiameter*1.5, 3), #left
        atom(1 - atomDiameter*1.5 , 1.05, 2), #down
        atom(1 + atomDiameter*1.5 , 1.05, 1), #up
        
         #in the central cercles : theirs
        atom(2 - atomDiameter/2 , 1.05 - atomDiameter*1.5, 1), #left
        atom(2 - atomDiameter/2 , 1.05, 2), #down
        atom(2 + atomDiameter/2 , 1.05, 3), #up
        atom(2 , 1.05 + atomDiameter, 1), #right
        
         #near table of elements : theirs
        atom(2.5 , 0.45, 1),
        atom(2.5, 0.75, 1),
        atom(2.5, 1.05, 2),
        
         #in the balance
        atom(0.834, 1.8, 2), # to 0.83??
        atom(2.166 , 1.8, 2),
        
        
        ##### secondary atoms #####
        
         #in the two distributors
        atom(0.45+ atomDiameter/2, 0, 1, 0.),
        atom(0.45+ atomDiameter*(3/2), 0, 2, 0.),
        atom(0.45+ atomDiameter*(5/2), 0, 1, 0.),
        atom(0.45+ atomDiameter*(7/2), 0, 3, 0.),
        atom(0.45+ atomDiameter*(9/2), 0, 1, 0.),
        atom(0.45+ atomDiameter*(11/2), 0, 2, 0.),
        
        atom(2.55- atomDiameter/2, 0, 1, 0.),
        atom(2.55- atomDiameter*(3/2), 0, 2, 0.),
        atom(2.55- atomDiameter*(5/2), 0, 1, 0.),
        atom(2.55- atomDiameter*(7/2), 0, 3, 0.),
        atom(2.55- atomDiameter*(9/2), 0, 1, 0.),
        atom(2.55- atomDiameter*(11/2), 0, 2, 0.),
        
         #in the wall
        atom(0.075+ atomDiameter/2, 2, 3, 0.),
        atom(0.075+ atomDiameter*(3/2), 2, 2, 0.),
        atom(0.075+ atomDiameter*(5/2), 2, 1, 0.),
        
        atom(2.925- atomDiameter/2, 2, 1, 0.),
        atom(2.925- atomDiameter*(3/2), 2, 2, 0.),
        atom(2.925- atomDiameter*(5/2), 2, 3, 0.),
        
         #the two near the experiance
        atom(1.3, 0, 3, 0.),
        atom(1.7, 0, 3, 0.), 
        
        ##### Goldonium #####
        atom(0.75, 0, -1, 0.),
        atom(2.25, 0, -2, 0.)
        
        ]
        )

# TODO : ADD SCORES / UPDATE POSITIONS / START WITH ATOMS THAT WE USE FIRST
missions = np.array([ 
        #[atom, target , step, score]
        # step? : 1 is for the first part of the mission (robot->atom) and 2 for the second (robot+atom -> target) than 3 for done
        
        [Atoms[0], target(atomDiameter + space + padding, 0.45, np.pi), 1, 6], 
        [Atoms[1], target(2*(atomDiameter + space) + padding, 0.45, np.pi), 1 , 6],
        [Atoms[2], target(atomDiameter + space + padding, 0.75, np.pi), 1 , 6],
        
        [Atoms[3], target(3*(atomDiameter + space)  + padding, 0.45, np.pi), 1, 6],
        [Atoms[4], target(atomDiameter + space  + padding, 1.05, np.pi), 1, 6],
        [Atoms[5], target(2*(atomDiameter + space)  + padding, 0.75, np.pi), 1, 6],
        [Atoms[6], target(4*(atomDiameter + space)  + padding, 0.45, np.pi), 1, 6],
        
#        [Atoms[7], target(5*(atomDiameter + space), 0.45), 1, 6],
#        [Atoms[8], target(3*(atomDiameter + space), 0.75), 1, 6],
#        [Atoms[9], target(2*(atomDiameter + space), 1.05), 1, 6],
#        [Atoms[10], target(6*(atomDiameter + space), 0.45), 1, 6],
        
#        [Atoms[12], target(2*(atomDiameter + space), 0.45, np.pi), 1],
#        [Atoms[13], target(atomDiameter + spcae, 0.75), 1],
        
        
        [Atoms[7], target(5*(atomDiameter + space) + padding, 0.45, np.pi), 1, 6],
        [Atoms[8], target(3*(atomDiameter + space) + padding, 0.75, np.pi), 1, 6],
        [Atoms[9], target(2*(atomDiameter + space) + padding, 1.05, np.pi), 1, 6],
        [Atoms[10], target(6*(atomDiameter + space) + padding, 0.45, np.pi), 1, 6],
        
        [Atoms[11], target(0,0,0), 1, 6],
        [Atoms[12], target(0,0,0), 1, 6],
        [Atoms[13], target(0,0,0), 1, 6],
        
        
        [Atoms[14], target(1.4 - padding - atomDiameter, 1.8, 0), 1, 8],
        [Atoms[15], target(1.6 + padding + atomDiameter, 1.8, np.pi), 1, 8],
        
        [Atoms[16], target(0,0,0), 1, 6], # dummy mission of dummy atoms: target(x = 0, y = 0) : keep them in the list because these dummy atoms are used by the sensors
        [Atoms[17], target(0,0,0), 1, 6],
        [Atoms[18], target(0,0,0), 1, 6],
        [Atoms[19], target(0,0,0), 1, 6],
        [Atoms[20], target(0,0,0), 1, 6],
        [Atoms[21], target(0,0,0), 1, 6],
        [Atoms[22], target(0,0,0), 1, 6],
        [Atoms[23], target(0,0,0), 1, 6],
        [Atoms[24], target(0,0,0), 1, 6],
        [Atoms[25], target(0,0,0), 1, 6],
        [Atoms[26], target(0,0,0), 1, 6],
        [Atoms[27], target(0,0,0), 1, 6],
        [Atoms[28], target(0,0,0), 1, 6],
        [Atoms[29], target(0,0,0), 1, 6],
        [Atoms[30], target(0,0,0), 1, 6],
        [Atoms[31], target(0,0,0), 1, 6],
        [Atoms[32], target(0,0,0), 1, 6],
        [Atoms[33], target(0,0,0), 1, 6],
        [Atoms[34], target(0,0,0), 1, 6],
        [Atoms[35], target(0,0,0), 1, 6],
        
        [Atoms[36], target(1.4 - padding - 2 * atomDiameter, 1.8, 0), 1, 30],
        [Atoms[37], target(0,0,0), 1, 0],
        ])


# empty table
emptyTable = np.zeros((3 * ratio, 2 * ratio))

#adding static obstacles:
 #adding central balance obstacle
for x in range(int((1.48 - padding)*ratio), int((1.52 + padding)*ratio)):
    for y in range(int((1.4 - padding)*ratio), 2*ratio):
        emptyTable[x][y] = 1

 #adding distributors
for x in range(int((0.45 - padding)*ratio), int((2.55 + padding)*ratio)):
    for y in range(int((1.54 - padding)*ratio), int((1.6 + padding)*ratio)):
        emptyTable[x][y] = 1
        
 #adding table paddings
for x in range(0, 3*ratio):
    for y in range(0, int(padding*ratio)):
        emptyTable[x][y] = 1
    for y in range(2*ratio - int(padding*ratio), 2*ratio):
        emptyTable[x][y] = 1  
for y in range(0, 2*ratio):
    for x in range(0, int(padding*ratio)):
        emptyTable[x][y] = 1
    for x in range(3*ratio - int(padding*ratio), 3*ratio):
        emptyTable[x][y] = 1  
        


#################################################### methods ####################################################
        

def message(message, color):
    if displayMessages: 
        sys.stdout.write(color)
        print(message)
        sys.stdout.write(colors.RESET)
        
      
def getBorders(element): #gets borders of an element in the matrix given a padding and given the dimensions of the robot
    
    global padding
    Xstart = int((element.getX() - element.getDiameter()/2)*ratio)
    Xend = int((element.getX() + element.getDiameter()/2)*ratio)
    Ystart = int((element.getY() - element.getDiameter()/2)*ratio)
    Yend = int((element.getY() + element.getDiameter()/2)*ratio)
     #first test if possible to add the robot if not return -1
    if Xstart < 0 or Xend >= (3 * ratio) and Ystart < 0 and Yend >= 2 * ratio:
        return -1, -1, -1, -1
    else:
        #if possible add check which paddings can fit in
        if int((element.getX() - element.getDiameter()/2)*ratio - padding*ratio) >= 0 : Xstart = int((element.getX() - element.getDiameter()/2)*ratio - padding*ratio)
        else : Xstart = 0
        if int((element.getX() + element.getDiameter()/2)*ratio + padding*ratio) < 3 * ratio : Xend = int((element.getX() + element.getDiameter()/2)*ratio + padding*ratio)
        else : Xend = (3 * ratio) -1
        if int((element.getY() - element.getDiameter()/2)*ratio - padding*ratio) >= 0 : Ystart = int((element.getY() - element.getDiameter()/2)*ratio - padding*ratio)
        else : Ystart = 0
        if int((element.getY() + element.getDiameter()/2)*ratio + padding*ratio) < 2 * ratio : Yend = int((element.getY() + element.getDiameter()/2)*ratio + padding*ratio)
        else : Yend = (2 * ratio) -1
    
    return Xstart, Xend, Ystart, Yend



def addElement(element, table): #returns 1 if successful and -1 if not
    Xstart, Xend, Ystart, Yend = getBorders(element)
    if Xstart == -1 : return -1
    
    for x,y in itertools.product(range(Xstart, Xend+1), range(Ystart, Yend+1)):
        if np.sqrt(np.power(x - element.getX()*ratio,2) + np.power(y - element.getY()*ratio,2)) <= (element.getDiameter() / 2. + padding) * ratio:
            table[x][y] += 1
        
    return 1      



def deleteElement(element, table): #returns 1 if successful and -1 if not
        
    #todo : consider near elements to not delete all !
    
    Xstart, Xend, Ystart, Yend = getBorders(element)
    
    if Xstart == -1 : return -1
    for x,y in itertools.product(range(Xstart, Xend+1), range(Ystart, Yend+1)):
        if np.sqrt(np.power(x - element.getX()*ratio,2) + np.power(y - element.getY()*ratio,2)) <= (element.getDiameter() / 2. + padding) * ratio:
            table[x][y] -= 1
    return 1



def updateElement(oldElement, newElement, table): #returns 1 if successful and -1 if not
    if deleteElement(oldElement, table) == -1 : return -1
    if addElement(newElement, table) == -1 : return -1
    return 1

        
    
def addAtoms(atoms, table): #returns 1 if successful and -1 if not
        
    oldCopy = table.copy()
    for atom in atoms:
        if addElement(atom, table) == -1:
            table = oldCopy
            return -1
    message("Ok! Atoms successfuly added", colors.GREEN)
    return 1



def getThetaFromSourceToTarget(source, target): # in ]-pi,pi]
    
    dx = target[0] - source[0]
    dy = target[1] - source[1]
    
    if dx == 0 and dy == 0: return 0
    
    sin = dy/np.sqrt(dx**2 + dy**2)
    tetaFromSource = np.arcsin(sin)
    if(dy >= 0 and dx < 0) : tetaFromSource = np.pi - tetaFromSource
    if(dy < 0 and dx < 0) : tetaFromSource = - np.pi - tetaFromSource
    return tetaFromSource



def initializeTable(atomsDisposition, ourRobot, opponentFirstRobot, opponentSecondRobot):
    
    table = emptyTable.copy()
    
    #if addElement(ourRobot, table) == -1 : message("ERROR WHILE ADDING OUR ROBOT TO THE TABLE")
    
    if addElement(opponentFirstRobot, table) == -1 : message("ERROR WHILE ADDING THEIR FIRST ROBOT TO THE TABLE", colors.RED)
    if opponentSecondRobot != None:
        if addElement(opponentSecondRobot, table) == -1 : message("ERROR WHILE ADDING THEIR SECOND ROBOT TO THE TABLE", colors.RED)
    if addAtoms(atomsDisposition, table)  == -1 : message("ERROR WHILE ADDING ATOMS TO THE TABLE", colors.RED)
        
    message("Ok! Table successfuly initialized", colors.GREEN)    
    
    return table


def getCamRobotPosition(response):
    return int(response[:3]) / 100., int(response[3:6]) / 100., int(response[240:243]) / 100.

def getCamOpponentsFirstRobotPosition(response):
    return int(response[6:9]) / 100., int(response[9:12]) / 100.

def getCamOpponentsSecondRobotPosition(response):
    return int(response[12:15]) / 100., int(response[15:18]) / 100.

def getCamAtomPosition(Id, response):
    return int(response[18 + 3*Id :21 + 3*Id]) / 100., int(response[21 + 3*Id:24 + 3*Id]) / 100.


def updateTable(table, ourRobot, opponentFirstRobot, opponentSecondRobot, atomsDisposition, response): # Updates is done if element is at least 7cm near the robot

    """
    
    to get the current disposition of atoms what we will do is the following:
        If the camera is trustfull update all elements in the table otherwise do the following:
            1 - adjust our robot's position/orientation using data from response
            2 - gess what the robot is looking at than update the element position
        
    """
    
    if cc.checkState():
        camResponse = cc.getCamResponse()
        x,y = getCamOpponentsFirstRobotPosition(camResponse)
        old = cp.copy(opponentFirstRobot)
        opponentFirstRobot.setX(x)
        opponentFirstRobot.setY(y)
        updateElement(old, opponentFirstRobot, table)
        
        if numberOfOpponentRobots == 2:
            x,y = getCamOpponentsSecondRobotPosition(response)
            old = cp.copy(opponentSecondRobot)
            opponentSecondRobot.setX(x)
            opponentSecondRobot.setY(y)
            updateElement(old, opponentSecondRobot, table)
        x,y, theta = getCamRobotPosition(camResponse)
        ourRobot.setX(x)
        ourRobot.setY(y)
        ourRobot.setDir(theta)
        for i in range(len(Atoms)):
            x,y = getCamAtomPosition(i, camResponse)
            old = cp.copy(Atoms[i])
            Atoms[i].setX(x)
            Atoms[i].setY(y)
            updateElement(old, Atoms[i], table)
    else:

        updateOurRobotPosition(getTraveledDistance(response), getRotationAngle(response), ourRobot)
        elements = theRobotIsLookingAt(getSensorsData(response))
             
        for elementData in elements:
            updatePosition(elementData, ourRobot, table)

    message("Table state updated...", colors.RESET)


def theRobotIsLookingAt(sensorsData, R = ourRobot.getDiameter() / 2):
    
    validSensors = []
    if sensorsData[0] <= atomDiameter and sensorsData[0] != 0.0 and sensorsData[1] == 0.0:
        validSensors.append((0,0))
    if sensorsData[5] <= atomDiameter and sensorsData[5] != 0.0 and sensorsData[4] == 0.0:
        validSensors.append((5,5))
    for i in range(5):
        if sensorsData[i] != 0.0 and sensorsData[i+1] != 0.0 and func(sensorsData[i], sensorsData[i+1], R):
            validSensors.append((i,i+1))
            
    # ignore if looking at the atom of the mission
    xm = missions[currentMission][0].getX()
    ym = missions[currentMission][0].getY()
    if missions[currentMission][2] == 1 and np.sqrt((xm - ourRobot.getX())**2 + (ym - ourRobot.getY())**2) <= R + atomDiameter + 0.07 and ourRobot.getDir() - getThetaFromSourceToTarget((int(ourRobot.getX()*ratio),int(ourRobot.getY()*ratio)), (int(xm*ratio),int(ym*ratio))) <= 0.23 and (2,3) in validSensors:
        validSensors.remove((2,3))
        
    if len(validSensors) != 0:
        elements = []
        tmpListOfAtoms = [i for i in range(len(missions)) if missions[i][1].getX() == 0 and missions[i][1].getY() == 0]
        tmpListOfAtoms.sort(key = lambda t : -missions[t][2])
        for i,j in validSensors:
            if len(tmpListOfAtoms) > 0: 
                indexMission = tmpListOfAtoms.pop()
                element = missions[indexMission][0]
                missions[indexMission][2] += 1
                if i != j:
                    elements.append([element, i, j, sensorsData[i], sensorsData[j]])
                else:
                    elements.append([element, i, j, sensorsData[i], sensorsData[j] + element.getDiameter()])
        return elements
    else:
        return []    
        
    

def updatePosition(elementData, ourRobot, table):
    
    tmpElement = cp.copy(elementData[0])
    
    if tmpElement.getDiameter() == 0.0 and isinstance(tmpElement.getLabel() , int): # means an atom
          elementData[0].setDiameter(atomDiameter)
    
    X, Y = getExpXY(elementData, ourRobot)
    
    elementData[0].setX(X) #do not forget to update on the table too
    elementData[0].setY(Y)
    updateElement(tmpElement, elementData[0], table)



def func(x, y, R):
    rad27 = 0.471238898
    return (y * np.sin(rad27) + R * np.sin(rad27))**2 + (x + R - y * np.cos(rad27) - R * np.cos(rad27))**2 <= atomDiameter**2



def getExpXY(elementData, ourRobot, pltShow = False, R = ourRobot.getDiameter() / 2):
    # look at the drawing
    r = elementData[0].getDiameter() / 2
    thetas = np.array([-1.178, -0.707, -0.236, 0.236, 0.707, 1.178]) + ourRobot.getDir()
    xA, yA = (R + elementData[3]) * np.cos(thetas[elementData[1]]) + ourRobot.getX(), (R + elementData[3]) * np.sin(thetas[elementData[1]]) + ourRobot.getY()
    xB, yB = (R + elementData[4]) * np.cos(thetas[elementData[2]]) + ourRobot.getX(), (R + elementData[4]) * np.sin(thetas[elementData[2]]) + ourRobot.getY()
    
    if pltShow:
        plt.gca().set_aspect('equal', adjustable='box')
        plt.plot([ourRobot.getX(), ourRobot.getX() + R, xA , xB ],[ourRobot.getY(), ourRobot.getY(), yA, yB], 'ro')
    
    d = np.sqrt((xA-xB)**2 + (yA-yB)**2)
    h = np.sqrt(r**2 - (d/2)**2)
    if xA == xB:
        dx, dy = h, 0
    elif yA == yB:
        dx, dy = 0, h
    else:
        dx, dy = h / np.sqrt(1 + ((xA-xB)/(yA-yB))**2), h / np.sqrt(1 + ((yA-yB)/(xA-xB))**2)
        
    signe = 1
    if (yA-yB) > 0 and (xA-xB) > 0 or (yA-yB) < 0 and (xA-xB) < 0: 
        signe = -1
    x1, y1 = (xA + xB) / 2 + signe * dx, (yA + yB) / 2 + dy
    x2, y2 = (xA + xB) / 2 - signe * dx, (yA + yB) / 2 - dy
    if np.sqrt((x1-ourRobot.getX())**2 + (y1-ourRobot.getY())**2) < np.sqrt((x2-ourRobot.getX())**2 + (y2-ourRobot.getY())**2):
        return x2, y2
    else:
        return x1, y1



def updateOurRobotPosition(traveledDistance, rotationAngle, ourRobot):
    theta = rotationAngle + ourRobot.getDir()
    if theta < - np.pi:
        theta = 2 * np.pi + theta
    elif theta > np.pi:
        theta = - 2 * np.pi + theta
    X = ourRobot.getX() + traveledDistance * np.cos(theta)
    Y = ourRobot.getY() + traveledDistance * np.sin(theta)
    
    ourRobot.setX(X)
    ourRobot.setY(Y)
    ourRobot.setDir(theta)



def sendNextActions(table, startTime):

    """
    given tableDisposition and currMission we do:
        1 - if currentMission is feasible do:
            1-1 - if the next step leads to the goal (we are one step away from the target = final target or atom):
                1-1-1 - if target is the final target : increment score, set the mission step to 3, update the robot position than put the atom
                1-1-2 - if target is an atom : set the mission step to 2 in case the target is the atom than update robot position and finaly grab the atom
            1-2 - else
                1-1-1 - set score to zero
            1-3 - send next actions to arduino
                1-3-1 - if the action is not complete update the robot position than put the atom and continue
            1-4 - store arduino's response in response and finish
        2- look for a feasable mission:
            2-1 - if found:
                change currentMission and go to 1

    """
    
    global currentMission
    
    path = False
    tmpMission = currentMission - 1
    while isinstance(path, bool):
        tmpMission += 1 # raise error if no mission is possible.. of wait 2-2
        #rewind when finished
        if tmpMission == len(missions):
            tmpMission, currentMission = 0, 0 
        
        #stop if time over
        if time.time() - startTime > 100.:
            return 0, 0
            
        #message("In pregress : " + str(missions[tmpMission][0]), colors.RESET)
        # preceed tests
        if missions[tmpMission][1].getX() != 0 or missions[tmpMission][1].getY() != 0: # skip dummy missions
            if missions[tmpMission][2] == 1:
                #message("In the way to the element ..." , colors.RESET)
                path = findPath(table, missions[tmpMission][0])
            elif missions[tmpMission][2] == 2:
                #message("In the way to the final target ..." , colors.RESET)
                path = pfa.algorithm(table, (int(ourRobot.getX()*ratio), int(ourRobot.getY()*ratio)), (int(missions[tmpMission][1].getX()*ratio), int(missions[tmpMission][1].getY()*ratio)))
                if isinstance(path, bool):
                    putDown(missions[tmpMission][0], table)
    
    currentMission = tmpMission
        
    if len(path) == 0:
        path.append((int(ourRobot.getX()*ratio), int(ourRobot.getY()*ratio)))
    
    path.reverse()
    
    #sending actions
    
    #proceed with the first part of the path
    theEnd = False
    if len(path) == 1: 
        theEnd = True
    firstPart = [(int(ourRobot.getX()*ratio),int(ourRobot.getY()*ratio)), path[0]]
    for i in range(1,len(path)):
        if (path[i][0] - firstPart[i][0] != firstPart[i][0] - firstPart[i-1][0]) or (path[i][1] - firstPart[i][1] != firstPart[i][1] - firstPart[i-1][1]): break
        firstPart.append(path[i])
        if i == len(path) - 1:
            theEnd = True

    draw(np.array(path), table)
    undraw(np.array(path), table)
    
        #rotation
    theta = getThetaFromSourceToTarget((int(ourRobot.getX()*ratio),int(ourRobot.getY()*ratio)), path[0])
    
    
    response = ""
    if ourRobot.getDir() > theta:
        response = cr.turnRight(ourRobot.getDir() - theta)
    elif ourRobot.getDir() < theta:
        response = cr.turnLeft(theta - ourRobot.getDir())
    else:
        response += "0000"
    
        #translation
    response = cr.moveForward(np.sqrt((firstPart[-1][0] - int(ourRobot.getX()*ratio))**2 + (firstPart[-1][1] - int(ourRobot.getY()*ratio))**2) / float(ratio)) + response
    
    score = 0
    if theEnd and missions[currentMission][2] == 2 and actionComplete(response):
        theta = missions[currentMission][1].getFinalRobotOrientation()
        if ourRobot.getDir() > theta:
            cr.turnRight(ourRobot.getDir() - theta)
        elif ourRobot.getDir() < theta:
            cr.turnLeft(theta - ourRobot.getDir())
        
        updateOurRobotPosition(getTraveledDistance(response), getRotationAngle(response), ourRobot)
        ourRobot.setDir(theta)
        response = response[:13] + "00000000"
        
        putDown(missions[currentMission][0], table)
        
        missions[currentMission][2] = 3
        score = missions[currentMission][3]
        
    if theEnd and missions[currentMission][2] == 1 and actionComplete(response):
        updateOurRobotPosition(getTraveledDistance(response), getRotationAngle(response), ourRobot)
        ourRobot.setDir(getThetaFromSourceToTarget((int(ourRobot.getX()*ratio),int(ourRobot.getY()*ratio)), (int(missions[currentMission][0].getX()*ratio), int(missions[currentMission][0].getY()*ratio))))
        response = response[:13] + "00000000"
        
        grab(missions[currentMission][0], table)
        
        missions[currentMission][2] = 2
        
    if not actionComplete(response) and missions[currentMission][2] == 2:
        updateOurRobotPosition(getTraveledDistance(response), getRotationAngle(response), ourRobot)
        ang = ourRobot.getDir()+np.pi/2
        if ourRobot.getDir() > np.pi/2: ang += - 2*np.pi
        ourRobot.setDir(ourRobot.getDir()+ang)
        response = response[:13] + "00000000"
        putDown(missions[currentMission][0], table)
        missions[currentMission][2] = 1
        ourRobot.setDir(ourRobot.getDir()-ang)
    
    return score, response # score != 0 only if the next action is the final action of an operation and response is the string sent by arduino



def grab(element, table):
    deleteElement(element, table)
    if element.getDiameter() == 0.0 and isinstance(element.getLabel() , int): # means an atom
         element.setDiameter(atomDiameter)
    cr.grab()
    


def putDown(element, table):
    
    element.setX(ourRobot.getX() + (padding + element.getDiameter()/2. + 1./ratio) * np.cos(ourRobot.getDir()))
    element.setY(ourRobot.getY() + (padding + element.getDiameter()/2. + 1./ratio) * np.sin(ourRobot.getDir()))
    addElement(element, table)
    cr.putDown()



def actionComplete(response): # returns a boolean saying if response indicates that the action was interupted (false) or not (true)
    return int(response[0]) == 1

def getSensorsData(response): # 0 if element is out of [0,15]
    return int(response[1:3]) / 100. , int(response[3:5]) / 100. , int(response[5:7]) / 100. , int(response[7:9]) / 100. , int(response[9:11]) / 100. , int(response[11:13]) / 100.  

def getTraveledDistance(response):
    return int(response[13:17]) / 1000.

def getRotationAngle(response):
    if int(response[17:21]) / 1000. <= np.pi: 
        return int(response[17:21]) / 1000.
    else:
        return - round((2*np.pi - int(response[17:21]) / 1000.),3)



def findPath(table, target):
        
    border = []
    x = target.getX()*ratio
    y = target.getY()*ratio
    mrg = (target.getDiameter()/2. + padding)*ratio
    
    #ordring borders to begin with the neighrest to the robot
    tmp = [(int(x + mrg) + 1, int(y)), (int(x - mrg) - 1, int(y)), (int(x), int(y + mrg) + 1), (int(x), int(y - mrg) -1)]
    tmp.sort(key = lambda t : np.power(int(ourRobot.getX()*ratio) - t[0], 2) + np.power(int(ourRobot.getY()*ratio) - t[1], 2))
    
    for i,j in tmp:
        if i < len(table) - 1 and i > 0 and j < len(table[0]) - 1 and j > 0:
            if table[i][j] == 0.:
                border.append((i,j))
        
    for borderElement in border:
        path = pfa.algorithm(table, (int(ourRobot.getX()*ratio), int(ourRobot.getY()*ratio)), (int(borderElement[0]), int(borderElement[1])))
        if not isinstance(path, bool):
            return path
    return False



def initialRespose(): # returns initial default response (needed ???)
    return "000000000000000000000" # 1st digit for action complete or not => 6 x 2 digits for sensors => 4 digits traveled distance => 4 digits angle


#################################################### Main loop #################################################### 
    

tableDisposition = initializeTable(atomsDisposition, ourRobot, opponentFirstRobot, opponentSecondRobot)

def action():
        
    startTime = time.time()
    actionResponse = initialRespose() #string sent by arduino
    score = 0
    
#    bol = True
    
    while time.time() - startTime < 100:

#        if time.time() - startTime > 5 and bol:
#            actionResponse = actionResponse[:1] + "0104" + actionResponse[5:]
#            bol = False
                
        updateTable(tableDisposition, ourRobot, opponentFirstRobot, opponentSecondRobot, atomsDisposition, actionResponse)
        draw(np.array([]), tableDisposition)
        actionScore, actionResponse = sendNextActions(tableDisposition, startTime)
        score += actionScore
        message("Current score is " + str(score) + " pts", colors.GREEN)
    
    message("Time Over! ", colors.BLUE)
                        
            

#################################################### for tests #################################################### 
   
def draw(path, table):
    if activateDraw:
        for i,j in path:
            table[i,j] += 7
            
        for i, j in itertools.product(range(- int(ourRobot.getDiameter()*ratio) // 2, int(ourRobot.getDiameter()*ratio) // 2), range(-int(ourRobot.getDiameter()*ratio) // 2, int(ourRobot.getDiameter()*ratio) // 2)):
            if ellipse(i, j , ourRobot.getDir(), int(ourRobot.getDiameter()*ratio) // 2):
                table[i + int(ourRobot.getX()*ratio) ,j + int(ourRobot.getY()*ratio)] += 3
    
        plt.figure(figsize=(8,9))
        plt.imshow(table)
        plt.show()
        
        for i, j in itertools.product(range(- int(ourRobot.getDiameter()*ratio) // 2, int(ourRobot.getDiameter()*ratio) // 2), range(-int(ourRobot.getDiameter()*ratio) // 2, int(ourRobot.getDiameter()*ratio) // 2)):
            if ellipse(i, j , ourRobot.getDir(), int(ourRobot.getDiameter()*ratio) // 2):
                table[i + int(ourRobot.getX()*ratio) ,j + int(ourRobot.getY()*ratio)] -= 3
    
    
def undraw(path, table):
    if activateDraw:
        for i,j in path:
            table[i,j] -= 7
  
    
def ellipse(i, j , t, R):
    if t == 0:
        cond = i >= 0
    elif t == -np.pi or t == np.pi:
        cond = i <= 0
    elif t > 0:
        cond = j >= (-1./np.tan(t)) *i
    else:
        cond = j <= (-1./np.tan(t)) *i
    return ((i*np.cos(t) + j*np.sin(t))/3)**2 + ((j*np.cos(t) - i*np.sin(t))/1)**2 <= R and cond