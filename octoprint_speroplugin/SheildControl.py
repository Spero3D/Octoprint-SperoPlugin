# coding=utf-8
import RPi.GPIO as GPIO 
import gpiozero
from .ButtonService import ButtonService
from .MotorService import MotorService
from .MotorService import MotorState
from .SwitchService import SwitchService
from threading import Timer
import string
from signal import pause

class SheildControl:   
    
    onSequenceFinish:None
  
    def __initControl(self):
        if self._pin1 and self._pin2:
            print('-----------------------------CONTROL ----------------------------------------')

    def __init__(self,pin1,pin2,pin3,pin4,pin5,pin6,pin7):
      self._pin1 = pin1
      self._pin2 = pin2
      self._pin3 = pin3
      self._pin4 = pin4
      self._pin5 = pin5
      self._pin6 = pin6
      self._pin7 = pin7
      self.curr_index=0
      self.is_in_sequence=False
      self.wait_timer= None
      self.control=False
      self.motor_state='IDLE'
      self.tabla_state='IDLE'
      self.sequence = ['W','F','W','B','W','C','S']
      self.actions ={"W":self.wait,"F":self.forward,"B":self.backward,"C":self.correct}
      self.__initControl()
      self.button_service=ButtonService(self._pin1,self._pin2,self._pin3)
      self.motor_service=MotorService(self._pin4,self._pin5)
      self.switch_service=SwitchService(self._pin6,self._pin7)    
      print('-----------------------------CONTROL    INIT------------------------------')
      
      
    def connection(self):
        
        self.connection_sheild=MotorState.getConnection()
        return MotorState.getConnection()

   
    def forward(self):
        self.motor_state='MOTOR GOING TO FORWARD'
        self.motor_service.goForward()

    def backward(self):
        self.motor_state='MOTOR GOING TO BACKWARD'
        self.motor_service.goBackward()
        
    def stop(self):
        self.motor_state='MOTOR STOP'
        self.motor_service.stop()    
  
    def call_stop(self):
        self.motor_state='MOTOR STOP'
        if self.control==False:
            self.stop()
            self.curr_index=0
            self.is_in_sequence=False
        else:
            self.control=False
            
    def get_message(self,a:string):
        if a=="backword":
            self.backward()
        if a=="stop":
            self.call_stop()
        if a=="forward":
            self.forward()
        if a=="eject":
            self.start_sequence()        
            
    def start_sequence(self):
        if self.is_in_sequence==False and self.curr_index==0:
            self.trigger_nextJob()
        else :
            self.curr_index=0
            self.is_in_sequence=False
            self.stop()
            
    def trigger_nextJob(self):
        if self.is_in_sequence==True:
            self.curr_index=self.curr_index+1
            self.run_job()
        else:
            self.is_in_sequence=True
            self.run_job()        
    
    def run_job(self):
        self.currentSeq = self.sequence[self.curr_index]
        self.action = self.actions.get(self.currentSeq,self.job_finish)
        if self.action :
            self.action()

        
    def job_finish(self):
        print(self.curr_index)
        if self.curr_index==6:
            self.call_stop()
            self.control=False
            self.curr_index=0
            self.isInSequence=False
        else :
            self.trigger_nextJob()
    
    def wait(self):
        self.stop()
        waitTimer = Timer(2,self.job_finish,args=None,kwargs=None)
        waitTimer.start()
 
    def correct(self):
        print("correct")
        self.stop()
        waitTimer = Timer(2,self.job_finish,args=None,kwargs=None)
        waitTimer.start()
        print("forward")
        self.motor_service.goForward()
        waitTimer = Timer(1,self.stop,args=None,kwargs=None)
        waitTimer.start()
        if self.onSequenceFinish:
            self.onSequenceFinish()
        self.tablaState="IDLE"
 
 
    def switch1_press(self):
        self.tabla_state="FORWARD"
        if self.is_in_sequence==True and self.sequence[self.curr_index]=='F':
            self.job_finish()

        
    def switch2_press(self):
        self.tabla_state="BACKWARD"
        if self.is_in_sequence==True and self.sequence[self.curr_index]=='B':
            self.job_finish()

    def button_init(self):
        self.button_service.onShortPressed = self.start_sequence
        self.button_service.onForwardPressed=self.forward
        self.button_service.onBackwardPressed=self.backward
        self.switch_service.onswitch1Pressed=self.switch1_press
        self.switch_service.onSwitch2Pressed=self.switch2_press
        
        pause()

