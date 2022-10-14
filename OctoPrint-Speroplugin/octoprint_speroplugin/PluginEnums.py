

from enum import Enum
from lib2to3.pgen2.token import AWAIT



class ItemState(Enum):
    
    AWAIT="Await"
    PRINTING="Printing"
    EJECTING="Ejecting"
    EJECT_FAIL="Eject_fail"
    CANCELLED="Cancelled"
    CANCELLING="Cancelling"
    FAILLED="Failed"
    PAUSED="Paused"
    PAUSING="Pausing"
    FINISHED="Finished"

class QueueState(Enum):
    
    IDLE="IDLE"
    STARTED="STARTED"
    RUNNING="RUNNING"
    CANCELLED="CANCELLED"
    PAUSED="PAUSED"
    FINISHED="FINISHED"

    # def __str__(self):
    #     return str(self.value)



class BedPosition(Enum):
    MIDDLE="MIDDLE"
    FRONT="FRONT"
    BACK="BACK"
    
    # def __str__(self):
    #     return str(self.value)



class MotorState(Enum):
    IDLE="IDLE"
    FORWARD="FORWARD"
    BACKWORD="BACKWORD"
    
class EjectState(Enum):
    IDLE="IDLE"
    WAIT_FOR_TEMP="WAIT_FOR_TEMP"
    EJECTING="EJECTING"
    EJECTING_FINISHED="EJECTING_FINISHED"
    EJECT_FAİL="EJECT_FAIL"



