from argparse import Action
from ast import Global, Return
from pickle import FALSE, TRUE

import string
import RPi.GPIO as GPIO 
from signal import pause
from .ButtonService import ButtonService
from .MotorService import MotorService
from .MotorService import MotorState
from threading import Timer
import time

sequence = ['W','F','W','B','W','C','S']
currIndex=0
isInSequence=False
waitTimer= None
konrol=False
motorr=None
sequenceFinish=False
sequenceStart=False
motorState='IDLE'
tablaState='IDLE'

class Control:
  
    
  
    motorr= MotorService(23,18)
    
    def __initKontrol(self):
        if self._pin1 and self._pin2:
            print('-----------------------------CONTROL ----------------------------------------')

    def __init__(self,pin1,pin2,pin3):
      self._pin1 = pin1
      self._pin2 = pin2
      self._pin3 = pin3
      print('-----------------------------CONTROL    INIT------------------------------')
      self.__initKontrol()


    def Sequence_Finish():
        global sequenceFinish
        return sequenceFinish

    def startSequence():
        global sequenceFinish
        sequenceFinish=True
        global konrol 
        konrol=True
        global currIndex
        global isInSequence
        print(isInSequence) 
        print(currIndex)   
        if isInSequence==False and currIndex==0:
            triggerNextJob()
        else :
            print(currIndex)
            currIndex=0
            isInSequence=False
            print(currIndex)
            print(isInSequence)
            callStopp()

    def getMessage(a:string):
        global motorState
       
        print(a)  
        b= MotorService(23,18)
        if a=="backword":
            b.goBackward()
        if a=="stop":
            b.stop()
        if a=="forward":
            b.goForward()
        if a=="eject":
            startSequencee()
            
    def callStop():
        global motorState
        motorState='MOTOR STOP'
        motorr= MotorService(23,18)
        global konrol
        if konrol==False:
            global  currIndex
            global isInSequence
            a=MotorState.getState()
            motorr.stop()
            currIndex=0
            isInSequence=False
        else:
            konrol=False


    def motor_State():
        global motorState
        return motorState

    def tabla_State():
        global tablaState
        return tablaState


    def stopp():
        global motorState
        motorState='MOTOR STOP'
        motorr= MotorService(23,18)
        print("Control Stop")
        motorr.stop()
       
    def forward():
        global motorState
        motorState='MOTOR GOING TO FORWARD'
        rr= MotorService(23,18)
        print("control FORWARD")
        rr.goForward()

    def backward():
        global motorState
        motorState='MOTOR GOING TO BACKWARD'
        motorr= MotorService(23,18)
        print("Control backword")
        motorr.goBackward()


    def switch1Press():
        global tablaState
        tablaState="FORWARD"
        global currIndex
        global isInSequence
        if isInSequence==True and sequence[currIndex]=='F':
            jobFinish()

        
    def switch2Press(self):
        global tablaState
        tablaState="BACKWARD"
        global isInSequence
        if isInSequence==True and sequence[currIndex]=='B':
           jobFinish()
    
    def buttonService(self):
        print("--------------------------------------------------------------------------------------------buttonservice-----------------------------------------------------------------------------")
        GPIO.setup(2,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(3,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(6,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(17,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(5,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)   
        GPIO.setup(0,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)     
        GPIO.setup(0,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)              
    def yaz():
       print("yazdııı")
    def yazz():
        print("olmadı")

        
def triggerNextJob():
    global currIndex
    global isInSequence
    if isInSequence==True:
        currIndex=currIndex+1
        RunJOB()
    else:
        isInSequence=True
        RunJOB()
def RunJOB():
    global currIndex
    global isInSequence
    global sequence
    currentSeq = sequence[currIndex]
    print(currIndex)
    print(sequence[currIndex])
    action = actions.get(currentSeq,jobFinish)
    if action :
        action()

def jobFinish():
    global currIndex
    global isInSequence
    global konrol
    if currIndex==6:
        callStopp()
        konrol=False
        currIndex=0
        isInSequence=False
    else :
        triggerNextJob()
def waittt():
    rr= MotorService(23,18)
    global waitTimer 
    rr.stop()
    print("wait start")
    waitTimer = Timer(2,jobFinish,args=None,kwargs=None)
    waitTimer.start()
        
def forwardd():
    global motorState
    motorState='MOTOR GOING TO FORWARD'
    rr= MotorService(23,18)
    print("control FORWARD")
    rr.goForward()

def backwardd():
    global motorState
    motorState='MOTOR GOING TO BACKWARD'
    motorr= MotorService(23,18)
    print("Control backword")
    motorr.goBackward()

    
def callStopp():
    global motorState
    motorState='MOTOR STOP'
    motorr= MotorService(23,18)
    global konrol
    if konrol==False:
        global  currIndex
        global isInSequence
        a=MotorState.getState()
        motorr.stop()
        currIndex=0
        isInSequence=False
    else:
        konrol=False

def startSequencee():
    global sequenceFinish
    sequenceFinish=True
    global konrol 
    konrol=True
    global currIndex
    global isInSequence
    print(currIndex)
    print(currIndex)
    if isInSequence==False and currIndex==0:
        triggerNextJob()
    else :
        print(currIndex)
        currIndex=0
        isInSequence=False
        print(currIndex)
        print(isInSequence)
        callStopp()

def correctt():
    global sequenceFinish
    global tablaState
    rr= MotorService(23,18)
    global currIndex
    global isInSequence
    rr.stop()
    waitTimer = Timer(2,jobFinish,args=None,kwargs=None)
    waitTimer.start()
    print("motor ileri")
    rr.goForward()
    time.sleep(1)
    rr.stop()
    print(isInSequence)
    sequenceFinish=False
    print(sequenceFinish)
    print("***********************************************************************")
    print("self.ejekting=false")
    tablaState="IDLE"
    
    

actions ={"W":waittt,"F":forwardd,"B":backwardd,"C":correctt}

def Sequence_Finish():
    global sequenceFinish
    return sequenceFinish

    
    