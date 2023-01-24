

from enum import Enum



class UsbState(str,Enum):
    Searching='Searching'
    Connected='Connected'


class ItemState(str,Enum):
    
    AWAIT="Await"
    PRINTING="Printing"
    EJECTING="Ejecting"
    EJECT_FAIL="eject fail"
    CANCELLED="Cancelled"
    CANCELLING="Cancelling"
    PAUSED="Paused"
    PAUSING="Pausing"
    FINISHED="Finished"
    FAILED="Failed"
  
   

class QueueState(Enum):
    
    IDLE="Idle"
    STARTED="Started"
    RUNNING="Running"
    CANCELLED="Cancelled"
    PAUSED="Paused"
    FAILED="Failed"

    def __str__(self):
        return str(self.value)




class BedPosition(Enum):
    MIDDLE="Middle"
    FRONT="Front"
    BACK="Back"
    
    def __str__(self):
         return str(self.value)



class MotorState(Enum):
    IDLE="Idle"
    FORWARD="Forward"
    BACKWARD="Backward"
    STOP="Stop"

    
    
class EjectState(Enum):
    IDLE="Idle"
    WAIT_FOR_TEMP="WaitForTemp"
    EJECTING="Ejecting"
    EJECTING_FINISHED="EjectingFinished"
    EJECT_FAIL="EjectFail"
    
    
class ShieldState(Enum):
    IDLE="Idle"
    ISINSEQUENACE="isInSequence"
    
    def __str__(self):
     return str(self.value)
     
     


