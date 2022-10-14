import RPi.GPIO as GPIO 
from gpiozero import Button

class SwitchService():


   onswitch1Pressed = None
   onSwitch2Pressed = None

   def __onPressedswitch1(self):
      if self.onswitch1Pressed:
         self.onswitch1Pressed()

   def __onPressedswitch2(self):
      if self.onSwitch2Pressed:
       self.onSwitch2Pressed()


   def __init__(self,_pin1,_pin2):
      GPIO.setup(_pin1,GPIO.OUT)
      GPIO.setup(_pin2,GPIO.OUT)
  
      print("Switch Service init")
      if _pin1:
         self.pinswitch1 = _pin1
         GPIO.setup(self.pinswitch1,GPIO.OUT)
         self.__switch1 = Button(_pin1,pull_up=True)
         self.__switch1.when_pressed = self.__onPressedswitch1
      if _pin2:
         self.pinswitch2 = _pin2
         GPIO.setup(self.pinswitch2,GPIO.OUT)
         self.__switch2 = Button(_pin2,pull_up=True)
         self.__switch2.when_pressed = self.__onPressedswitch2