

from enum import Enum



class isShieldConnected(str,Enum):
    DISCONNECTED='Disconnected'
    CONNECTED='Connected'


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
  
   

class QueueState(str,Enum):
    
    IDLE="Idle"
    STARTED="Started"
    RUNNING="Running"
    CANCELLED="Cancelled"
    PAUSED="Paused"
    FAILED="Failed"
    FINISHED="Finished"

   




class BedPosition(str,Enum):
    MIDDLE="Middle"
    FRONT="Front"
    BACK="Back"
    
  



class MotorState(str,Enum):
    IDLE="Idle"
    FORWARD="Forward"
    BACKWARD="Backward"
    STOP="Stop"

    
    
class EjectState(str,Enum):
    IDLE="Idle"
    WAIT_FOR_TEMP="WaitForTemp"
    EJECTING="Ejecting"
    EJECTING_FINISHED="EjectingFinished"
    EJECT_FAIL="EjectFail"
    
    
class ShieldState(str,Enum):
    IDLE="Idle"
    ISINSEQUENACE="isInSequence"
    EJECTFAIL="ejectFaild"
    
 
     


