
# coding=utf-8
from .ButtonService import ButtonService
from .MotorService import MotorService,MotorState
from .SwitchService import SwitchService
from threading import Timer
from signal import pause

class SheildControl:  
   
    on_state_change = None 
  
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
      self.timer_out=None
      self.t=None
      self.connection_sheild="Idle"
      self.sheild_control=False
      self.curr_index=0
      self.is_in_sequence=False
      self.wait_timer= None
      self.control=False
      self.sequence_finish=True
      self.sequence_start=False
      self.eject_fail=False
      self.motor_state='Idle'
      self.print_bed_state='Middle'
      self.sequence = ['W','F','W','B','W','C','S']
      self.actions ={"W":self.wait,"F":self.forward,"B":self.backward,"C":self.correct}
      self.__initControl()
      self.button_service=ButtonService(self._pin1,self._pin2,self._pin3)
      self.motor_service=MotorService(self._pin4,self._pin5)
      self.switch_service=SwitchService(self._pin6,self._pin7)    
      self.motor_service.connection()
   
   
      
    def connection(self):
        
        self.connection_sheild=MotorState.getConnection()
        return MotorState.getConnection()

    
    def forward(self):
        self.motor_state='Forward'
        self.send_states()
        
        self.motor_service.goForward()

    def backward(self):
        self.motor_state='Backward'
        self.send_states()
        
        self.motor_service.goBackward()
        
    def stop(self):
        self.motor_state='Stop'
        self.send_states()
        
        self.motor_service.stop()    
  
    def call_stop(self):
        self.motor_state='Stop'
        self.send_states()
        
        if self.control==False:
            self.stop()
            self.curr_index=0
            self.is_in_sequence=False
        else:
            self.control=False
            
    def send_actions(self,a):
        if a=="backward":
            self.backward()
        if a=="stop":
            self.stop()
        if a=="forward":
            self.forward()
        if a=="eject":
            self.start_sequence()        
            
    def start_sequence(self):
        self.eject_fail=False
        self.sequence_finish=False
        if self.is_in_sequence==False and self.curr_index==0:
            self.trigger_nextJob()
        else :
            self.curr_index=0
            self.is_in_sequence=False
            self.stop()
            
    def trigger_nextJob(self):
        if self.timer_out!=None:
            self.timer_out.cancel()
            self.timer_out=None
        if self.is_in_sequence==True:
            self.curr_index=self.curr_index+1
            if self.curr_index %2 == 1:
                self.start_timer()
            self.run_job()
        else:
            self.is_in_sequence=True
            self.run_job()        
    
    
    def start_timer(self):
        if self.timer_out==None:
            self.timer_out = Timer(6.0,self.kill_time_out)
            self.timer_out.start()        
         


    def kill_time_out(self):
        self.timer_out=None
        self.eject_fail=True
        self.call_stop()

        

    def run_job(self):

        self.currentSeq = self.sequence[self.curr_index]
        self.action = self.actions.get(self.currentSeq,self.job_finish)
        if self.action :
            self.action()

        
    def job_finish(self):

        if self.curr_index==6:
            self.call_stop()
            self.control=False
            self.curr_index=0
            self.is_in_sequence=False
        else :
            self.trigger_nextJob()
    
    

        
    def wait(self):
        self.stop()
        waitTimer = Timer(2,self.job_finish,args=None,kwargs=None)
        waitTimer.start()
 
    def correct(self):
        self.stop()
        waitTimer = Timer(2,self.job_finish,args=None,kwargs=None)
        waitTimer.start()
        self.motor_service.goForward()
        self.send_states()
        waitTimer = Timer(1,self.stop,args=None,kwargs=None)
        waitTimer.start()
        self.tablaState="Idle"
        self.sequence_finish=True
        
        
        
 

        
        
    def send_states(self):
        if self.on_state_change:
            self.on_state_change(self.print_bed_state,self.motor_state,self.eject_fail)
 
 
    def switch1_press(self):
        self.motor_service.stop()
        self.print_bed_state="Forward"
        self.send_states()
        
        if self.is_in_sequence==True and self.sequence[self.curr_index]=='F':
            self.job_finish()

        
    def switch2_press(self):
        self.motor_service.stop()
        self.print_bed_state="Backward"
        self.send_states()
        if self.is_in_sequence==True and self.sequence[self.curr_index]=='F':
            self.job_finish()

            
    def switch1_released(self):
        self.print_bed_state="Middle"
        self.send_states()
    
    def switch2_released(self):
        self.print_bed_state="Middle"
        self.send_states()
        if self.is_in_sequence==True and self.sequence[self.curr_index]=='B':
 
            self.job_finish()

   


    def button_init(self):
        self.button_service.onShortPressed = self.start_sequence
        self.button_service.onForwardPressed=self.forward
        self.button_service.onBackwardPressed=self.backward
        self.switch_service.onswitch1Pressed=self.switch1_press
        self.switch_service.onSwitch2Pressed=self.switch2_press
        self.switch_service.onswitch1Released=self.switch1_released
        self.switch_service.onswitch2Realesed=self.switch2_released
        
        
        pause()


            
        
         

  

  
