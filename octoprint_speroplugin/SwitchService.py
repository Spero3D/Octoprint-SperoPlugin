from time import time
import RPi.GPIO as GPIO 
import gpiozero
import time
from signal import pause
from datetime import datetime, timedelta
from timeit import default_timer
import time
from unicodedata import name
import RPi.GPIO as GPIO 
from enum import Enum




GPIO.setmode(GPIO.BCM)

class SwitchService():

   def __initSwitch(self):
      if self._pin1 and self._pin2:
         GPIO.setup(self._pin1,GPIO.OUT)
         GPIO.setup(self._pin2,GPIO.OUT)


   def __init__(self,pin1,pin2):
      self._pin1 = pin1
      self._pin2 = pin2
      self.__initSwitch()
   