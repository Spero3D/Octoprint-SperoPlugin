

from enum import Enum
from lib2to3.pgen2.token import AWAIT



class ItemState(Enum):
    
    AWAIT="AWAIT"
    PRINTING="PRINTING"
    EJECTING="EJECTING"
    EJECT_FAİL="EJECT_FAİL"
    CANCELLED="CANCELLED"
    PAUSED="PAUSED"
    PAUSING="PAUSING"
    FINISHED="FINISHED"

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
    WAIT_FOR_TEMP="WAIT_FOR_TEMP"
    EJECTING="EJECTING"
    EJECT_FAİL="EJECT_FAİL"



