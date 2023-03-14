import sys
import glob
import serial
import json
import serial.tools
import serial.tools.list_ports
import time
import threading
from octoprint_speroplugin.PluginEnums import ShieldState,BedPosition,MotorState

class SerialPorts(object):
    onStateChange = None 
    serialId=None
    ports=[]
    
    def __init__(self):
        self.state = ShieldState.IDLE
        self.bedState=BedPosition.MIDDLE
        self.motorState=MotorState.IDLE
        self.readThread=None
        self.connection=False
        self.listThread =None
        self.readLive = False
        self.serialConnection=None
        self.state=ShieldState.ISINSEQUENACE
        
       
        pass


  
    def getSummary(self):
        self.write("Summary") 
        
    def serialPorts(self):
    
        """ Lists serial port names
            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        ports = serial.tools.list_ports.comports()
        self.ports = []
        for port in ports:
            try:
                if (port.manufacturer=="Spero3D"):
                    self.ports.append({"device":port.device,"serial":port.serial_number})
            except (OSError, serial.SerialException):
                pass
        return self.ports


    def serialConnect(self,p):

        
        self.serialConnection=serial.Serial(port=p)
        self.connection=True
        self.write("Summary")
        self.startRead()
        self.callOnStateChange()
       
        
  



    def selectedPortId(self,p): 
        if p is not None:
            self.serialId = p
        self.startListThread()
        
    def startListThread(self):
   
        if self.listThread is None:
            self.listThread = threading.Thread(target=self.portList)
            self.listThread.start()

    def portList(self):
        while True:
            if self.connection==False:
                self.ports=self.serialPorts()
                self.callOnStateChange()
                for port in self.ports:
                    if port["serial"] == self.serialId:
               
                        self.serialConnect(port["device"])
            time.sleep(0.5)
                    
            
   
                
                    
  


    def handle_data(self,data):
        data=data.replace("[INFO] ",":")    #trim spaces
        data=data.strip(":")
        data=data.split(":")
     
        
        self.state=ShieldState.ISINSEQUENACE   
        if len(data)>1:   
            if data[0]=="M":
                self.motorState=data[1]
            if data[0]=="B":
                self.bedState=data[1]
            if data[0]=="C":
                if data[1].rstrip()=="Idle":
                    self.state=ShieldState.IDLE
                if data[1].rstrip()=="SequenceError":
                    self.state=ShieldState.EJECTFAIL    
            self.callOnStateChange()                      
                    

    def startRead(self):
        self.readLive = True
        if self.readThread is None:
            self.readThread = threading.Thread(target=self.readFromPort)
            self.readThread.start()
            
    def stopRead(self):
        self.readLive = False
        self.connection=False
        if self.serialConnection:
            self.serialConnection.close()
        self.callOnStateChange()
        
                
    def readFromPort(self):
        if self.readLive is False:
            self.readThread = None
            sys.exit()
        while True:
            if self.serialConnection.isOpen():
                try:
                    reading = self.serialConnection.readline().decode()
                    self.handle_data(reading)
                except  serial.serialutil.SerialException:
               
                    self.stopRead()
                

       
            

        

        

    def callOnStateChange(self):
        self.bedPosition=self.bedState
        self.motorPosition=self.motorState
        if self.onStateChange:
            self.onStateChange(self.connection,self.bedPosition,self.motorPosition,self.ports,self.state)


    def sendActions(self,a):
        if a=="backward":
           self.write("MotorBackward")
        if a=="stop":
            self.write("MotorStop")
        if a=="forward":
           self.write("MotorForward")
        if a=="eject":
            self.state=ShieldState.ISINSEQUENACE
            self.write("SequenceStart")      
      

    def write(self,a:str):
        if self.serialConnection and self.serialConnection.isOpen():
            msg = "[CMD] "+a+"|123\n"
            self.serialConnection.write(msg.encode())
        else:
            print("USB not exist")

 