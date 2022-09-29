from time import time
import RPi.GPIO as GPIO 
from unicodedata import name
from enum import Enum
import time

durum="MotorState.IDLE"
connection="IDLEE"
GPIO.setmode(GPIO.BCM)

on_state_change_motor = None 
class MotorService():

   __timerUtility = 0
   def __initMotor(self):
      if self._pin1 and self._pin2:
         GPIO.setup(self._pin1,GPIO.OUT)
         GPIO.setup(self._pin2,GPIO.OUT)


   def __init__(self,pin1,pin2):
      self._pin1 = pin1
      self._pin2 = pin2
      self.__initMotor()
   
   def connection(self):
      global connection
      if self._pin1 and self._pin2:
         print("connecteddd")
         connection="Connected"
      

   def stop(self):
      global durum
      if self._pin1 and self._pin2:
         GPIO.output(self._pin1,False)
         GPIO.output(self._pin2,False)
         durum = "MotorState.IDLE"

   def goForward(self):

      global durum
      if self._pin1 and self._pin2:
         GPIO.output(self._pin1,True)
         GPIO.output(self._pin2,False)
         durum = "MotorState.FORWARD"
         
    
         
         
    


   def goBackward(self):
      start = time.time()     
      global durum
      if self._pin1 and self._pin2:
         GPIO.output(self._pin1,False)
         GPIO.output(self._pin2,True)

         durum = "MotorState.BACKWARD"
         now=time.time()

         
         
      if now-self.__timerUtility < 10:
            print(now-self.__timerUtility)
            print("motor durdu")
            self.stop()     
   

         
class MotorState(Enum):
  IDLE = 0
  FORWARD =1
  BACKWARD =2
  
  def getState():
     return durum
  def getConnection():
      return connection