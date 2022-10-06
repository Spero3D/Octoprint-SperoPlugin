

from enum import Enum


class QueueState(Enum):
    IDLE="IDLE"
    STARTED="STARTED"
    RUNNING="RUNNING"
    CANCELLED="CANCELLED"
    PAUSED="PAUSED"
    FINISHED="FINISHED"

