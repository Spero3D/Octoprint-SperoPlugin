import sys
import glob
import serial
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
        self.readthread=None
        self.connection=False
        self.listThread =None
        self.serialConnection=None
       
        pass


  
    def getSummary(self):
        
        self.serialConnection.write("[CMD] Summary|123\n".encode())   
        
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
        self.callOnStateChange()
       
        
  



    def selectedPortId(self,p): 
        self.serialId = p
        self.portList()
        

    def portList(self):
            self.connection=False
            self.callOnStateChange()
            while self.connection==False:
                self.ports=self.serialPorts()
                self.callOnStateChange()
                try:
                    if len(self.ports)>0:
                        if self.ports[0]["serial"] == self.serialId:
                            self.serialConnect(self.ports[0]["device"])
                            self.serialConnection.write("[CMD] Summary|123\n".encode())   
                            self.connection=True
                            self.readFromPort()
                            break
                        else:
                            time.sleep(0.5)
                            if self.connection==True:
                                break
                            self.ports=self.serialPorts()   
                            self.portList()
                            self.callOnStateChange()  
      
                    
            
                except  serial.serialutil.SerialException:
                    print("connect lose")
                    
            self.listThread = threading.Thread(target=self.portList)
            self.listThread.start()
  


    def handle_data(self,data):
        data=data.replace("[INFO]"," ")    #trim spaces
        data=data.split(":")  
        self.state=ShieldState.ISINSEQUENACE   
        self.callOnStateChange()
        if len(data)>1:   
            if data[0]=="  M":
                self.motorState=data[1]
                self.callOnStateChange()
            if data[0]=="  B":
                self.bedState=data[1]
                self.callOnStateChange()
            if data[0]=="  C":
                if data[1]=="Idle\n":
                    self.state=ShieldState.IDLE
                    self.callOnStateChange()
                if data[1]=="SequenceError\n":
                    self.state=ShieldState.EJECTFAIL    
                    self.callOnStateChange()                
                    

                
    def readFromPort(self):
        print(self.serialConnection)
        while self.serialConnection.isOpen():
            try:
                reading = self.serialConnection.readline().decode()
                self.handle_data(reading)
            except  serial.serialutil.SerialException:
                self.serialConnection.close()
                self.portList()
                
                break

        self.readthread = threading.Thread(target=self.readFromPort)
        self.readthread.start()
            

        

        

    def callOnStateChange(self):
        self.connection=self.connection
        self.bedPosition=self.bedState
        self.motorPosition=self.motorState
        if self.onStateChange:
            self.onStateChange(self.connection,self.bedPosition,self.motorPosition,self.ports,self.state)


    def sendActions(self,a):
        if a=="backward":
           self.serialConnection.write("[CMD] MotorBackward|123\n".encode())
        if a=="stop":
            self.serialConnection.write("[CMD] MotorStop|123\n".encode())
        if a=="forward":
           self.serialConnection.write("[CMD] MotorForward|123\n".encode())
        if a=="eject":
            self.state=ShieldState.ISINSEQUENACE
          
            self.serialConnection.write("[CMD] SequenceStart|123\n".encode())      
      

    



SerialPorts()   