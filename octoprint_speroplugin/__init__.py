# coding=utf-8
from __future__ import absolute_import
from email import message
from pickle import TRUE

from flask.globals import request
from tinydb.database import TinyDB
from tinydb.queries import Query
import copy
from octoprint.filemanager.storage import StorageInterface as storage
import RPi.GPIO as GPIO 
from gpiozero import Button
from octoprint.server import printer
import time
import os
import flask
import uuid
import datetime
import threading
from flask import jsonify,render_template
import json
from .SheildControl import SheildControl
from threading import Timer



ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = None

from octoprint.server.util.flask import (
    restricted_access,
)


import octoprint.plugin

class Speroplugin(     octoprint.plugin.StartupPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.BlueprintPlugin,
                       octoprint.plugin.AssetPlugin,               
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.ProgressPlugin,  
                       
                        ):
    KOntrol=True
    motor=None

    def __init__(self):
        self.sheild = dict()
        self.sheild_control=SheildControl(2,6,3,23,18,4,8)
        print('-----------------------------Plugin INIT------------------------------')
   
        self.esp = dict()
        self.queue_state="saaaa"
        self.print_bed_state="saaaa"
        self.currentİndex=0
        self.queues = []
        self.queue_state = "IDLE"
        self.ahmet="asdasd"
        self.current_item=None
        self.canselQuee=False
        self.canselQueueIndex=0
        self.current_queue = None
        self.state="as"
        self.currentFiles = []
        self.pins=[]
        self.itemResult=None
        self.totalEstimatedTime = 0
        self.stateCanselled=None
        self.isQueueStarted = False
        self.isQueuePrinting = False
        self.isManualEject = False
        self.printdonee=False
        self.connection = False
        self.ejecting = False
        self.eject_fail = False
        self.kontrol=False
        self.tempeartures="sıcaklık"
        self.tempeartures_temp=0
        self.c=12.00
        self.queue_numberofmembers=0
        self.printed_item=0
        self.stopQueueRememberNumber=0
        self.queue_mumberr=0
        self.Pauseclick=None
        self.cansel_start_queue="as"
        self.cansel_queue=False
        self.print_file=None
        self.queue=None
        self.queueee=0
        self.queueActive=False
        self.ejecting_finish=False
        self.printStart=False
        self.ejectStart=False
        self.Continue=None
        
    
    def get_from_database(self):
        
        db = TinyDB(ROOT_DIR+"/queues.json")
        queues = db.all()
        self.queues = []
        if len(queues) > 0:
            param = 0
            for queue in queues:
                self.queues.append(queue)
                param += 1
        
        fileDir = ROOT_DIR + "\\queues.json"
    
        print(self.queue)
        
        self.sendPrinterState()
        self._logger.info("KİNG İS HERE (more: %s)" % self._settings.get(["url"]))
        fileExist = os.path.exists(fileDir)
        if not fileExist:
            open(fileDir, 'w+')

        self.current_queue = self._settings.get(["speroplugin_current_queue"])
        c=self.current_queue
        # if c!=None and len(self.queues) > 0:
        #     if self.current_queue["items"] != None:
        #         for item in self.current_queue["items"]:
        #             item["state"] = "Await"
        # else:
        #     self.current_queue = dict(
        #         id=str(uuid.uuid4()),
        #         name="New Queue",
        #         items= [],
        #     )
        print('-----------get_from_database----------')
     
    
    def on_startup(self, host, port):
        print('-------------------ON STARTUP------------------------')



     
        if self.isManualEject == True:
            self._printer.cancel_print()
    
        self.esp["motor"] = 'IDLE'
        SheildControl.buttonService(self)
        fileDir = ROOT_DIR + "\\queues.json"
        fileExist = os.path.exists(fileDir)
        self.ejecting=SheildControl.Sequence_Finish()
        if self.ejecting==False:
          print("-----------------ejecting falseeeeeeee--------")

     
        
        if not fileExist:
            open(fileDir, 'w+')
       
        self.get_from_database()

        self.current_queue = self._settings.get(["speroplugin_current_queue"])

        if self.current_queue != None and len(self.queues) > 0:
           print(self.current_queue)
        else:
            self.current_queue = dict(
                id=str(uuid.uuid4()),
                name="New Queue",
                items= [],
            )
        print('-----------on_startup----------')  
        return super().on_startup(host, port)
       
       
    def motorRun(self):
        pin3=Button(3)
        pin2=Button(2)
        pin22=Button(6)
        switch1=Button(0)
        switch2=Button(5)
        while True:
            pin2.when_pressed=SheildControl.startSequence
            pin3.when_pressed=SheildControl.backward
            pin3.when_released=SheildControl.callStop
            pin22.when_pressed=SheildControl.forward
            pin22.when_released=SheildControl.callStop
            switch1.when_pressed=SheildControl.switch1Press
            switch2.when_pressed=SheildControl.switch2Press
               
               
                             
                    
            
    def on_after_startup(self):
        self._logger.info("KİNG İS HERE (more: %s)" % self._settings.get(["url"]))
        self.sendPrinterState()
       
  

    
    
    def pinKontrol(self):
        t=0
        while t<11:
            for x in range(10):
                if self.pin[t]==self.pin[x]:
                    self.kontrol=True
            t=t+1            
                
                
    def on_event(self, event, payload):
        self.print_bed_state=SheildControl.tabla_State()
        self.message_to_js(motorPin1=12)
        motor=SheildControl.motor_State()
        self.esp["motor"] =motor
        self.espState=SheildControl.motor_State()
        if motor:
            motorState = motor
            self.esp["motor"] = motor
            self.espState=SheildControl.motor_State()
            if motorState == "eject_start":
                self.ejecting = True
                self.eject_fail = False
                self.check_queue_busy()
        state = self._printer.get_state_id()
        if self.isQueueStarted == True and self.isQueuePrinting == True:
            if state == "CANCELLING":
                self.current_item["state"] = "Cancelling"

            if state == "FINISHING":
                self.current_item["state"] = "Finishing"

            if state == "PAUSED":
                self.queue_state = "PAUSED"
                self.message_to_js(terminate=True)

            # if state == "PAUSED":

        
        if self.isQueueStarted == True and self.isQueuePrinting == True:
            if state == "CANCELLING":
                self.current_item["state"] = "Cancelling"

            if state == "FINISHING":
                self.current_item["state"] = "Printing"

            if state == "PAUSED":
                self.queue_state = "PAUSED"
                self.message_to_js(terminate=True)

            # if state == "PAUSED":

            if event == "Disconnected" or event == "Error":
                if self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"
                    self.current_item["state"] = "Failed"
                    self.message_to_js(sendItemIndex=True)

            if event == "PrintStarted" or event == "PrintResumed":
                if(self.queue_state != "CANCELLED" and self.queue_state != "FINISHED" and self.queue_state != "PAUSED" ):
                    print("**************************************************************************")
                    print(self.queue_state)
                    if self.Pauseclick==True:
                        self.queue_state = "PAUSED"
                    else:
                        self.queue_state="RUNNING"    
                else :
                    self.queue_state="PAUSED"    
                self.current_item["state"] = "Printing"
           
            if event == "PrintPaused":
                if self.isManualEject == False:
                    self.current_item["state"] = "Paused"
                self.queue_state = "PAUSED"
                self.message_to_js(
                    sendItemIndex=True, terminate=False)

            if event == "DisplayLayerProgress_progressChanged":

                if self.current_item["state"] != "Printing" and self.current_item["state"] != "Cancelling":

                    self.current_item["state"] = "Printing"

                self.message_to_js(
                    sendItemIndex=True)

            if event == "PrintCancelling":
                if self.queue_state != "CANCELED" and self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"

                self.message_to_js(terminate=True)

            if event == "PrintFailed" or event == "PrintCanceled":
                
                if self.queue_state != "CANCELED" and self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"

                if event != "PrintCanceled":
                    if self.isQueuePrinting == False:
                        self.current_item["state"] = "Canceled"
                    else:
                        self.current_item["state"] = "Cancelling"
                else:
                    if self.current_item["state"] != "Cancelling":
                        self.current_item["state"] = "Failed"

                self.message_to_js(
                    sendItemIndex=True, terminate=True)

            if event == "PrinterStateChanged" and self.queue_state != "PAUSED":
                state = self._printer.get_state_id()

            if event == "PrintDone":
                self.current_item["state"] = "Finishing"
                print("prinnt donee")
                self.message_to_js(
                sendItemIndex=True, itemResult="Finishing")
                self.WaittingTem() 
                
                
                
    def WaittingTem(self):
        self.c=self.tempeartures_temp
        if self.c<=45:
            print("ideal tem eject starting")
            self.Ejecting()
        else:
            print(self.c)
            waitTimer = Timer(1,self.temperatures,args=None,kwargs=None)
            waitTimer.start()   
           
            
    def Ejecting(self):
        print("ejectstart")
        SheildControl.startSequence()
        self.WaittingEject()
        
   
    def WaittingEject(self):
        print("ejectwating")
        print(SheildControl.Sequence_Finish())
        if(SheildControl.Sequence_Finish()==False):
            print("ejectFinish")
          
            self.message_to_js(
                sendItemIndex=True, itemResult="Finished")
            
      
            
            if self.cansel_queue==True:
                print(self.cansel_queue)
                self.message_to_js(canselQuee="yes")
                print("---------------------------------------------------------------------------------------")
            
         
             
            self.current_item["state"] = "Finished"
            self.itemResult="Finished"  
            self.Next_item() 
        else:
            waitTimer2 = Timer(1,self.WaittingEject,args=None,kwargs=None)
            waitTimer2.start()
         
                
           
    def Next_item(self):
        print(self.stateCanselled)
        if self.stateCanselled!=True and self.Pauseclick!=True:
            print("NEXT İTEM")
            self.message_to_js(canselQuee="no"
                )
            self.state="Finishing"
            self.state="asdasd"
            if(self.Pauseclick!=True and SheildControl.Sequence_Finish()==False):
                self.currentİndex=self.currentİndex+1
                self.start_print()   
            else:
                self.queue_state == "FINISH"
                self.current_item["state"] = "Finished"
                print("print and queue finish")  
        else:
            print("queue and print finish")
            self.current_item["state"] = "Finished"        
    
    
    
    
    
    

    def check_queue_busy(self):
        if self.current_item != None:
            state = self.current_item["state"]
            if state == "Pausing" or state == "Paused" or state == "Printing":
                self.isManualEject = True
                SheildControl.startSequence()
            else:
                self.isManualEject = False
    
    def start_print(self, canceledIndex=None):
        print("start print")
        if self.cansel_queue==False:
            queue = self.current_queue["items"]
            print(queue)
            if (self.queue_state == "RUNNING" or self.queue_state == "STARTED" or canceledIndex != None):
                self.print_file = None

                if canceledIndex != None:
        
                    self.current_queue["items"][canceledIndex]["state"] = "Await"
                    self.print_file = self.current_queue["items"][canceledIndex]
                else:
                    for item in queue:
                            self.print_file = item
                            print("nexttt")
                            break

        if self.print_file != None:
            is_from_sd = None
            if self.print_file["sd"] == "true":
                is_from_sd = True
            else:
                is_from_sd = False
            
      
                 
                 
            # if self.Continue==True and self.stateCanselled !=True:
            #     if self.printed_item==0 and self.cansel_queue==False:
            #         self.printed_item=1     
            #     self.current_item=self.current_queue["items"][self.printed_item]
            #     self.Continue=False
            #     print(self.current_item)
            # # y = json.loads( self.tempeartures)
            # #  x=y['B'] 
            # # 
            # # self.current_item = self.print_file
            # #  if x:
            # else:
            #     self.current_item = self.print_file
                
            #     print(self.current_item)
            # if self.cansel_queue==True:
            #     self.printed_item=0
            #     self.current_queue["items"][0]["state"] = "Await"
            #     self.current_item=self.current_queue["items"][0]
            #     self.current_item = self.print_file
            #     self.cansel_queue=False
                 
                 
            if  self.printStart==True:
                self.current_item=self.current_queue["items"][self.currentİndex]
                print(self.current_item)
                print("qqqqqqqqqqqqqqqqqqqqqq")
   
            

            
            
            
            self.print_file=self.current_item    
            self._printer.select_file(self.print_file["path"], is_from_sd)
            self.print_startted()
            self.current_item["state"]
            self.message_to_js(
                sendItemIndex=True, itemResult= self.current_item["state"])
            
                
            
    
    def print_startted(self):
    
        self.itemResult="print"    
        self._printer.start_print()
        self.isQueuePrinting = True
    
  
    
    
    def stop_queue(self):
        self.queue_state = "IDLE"
        self.isQueueStarted = False
        

        for item in self.current_queue["items"]:
            item["state"] = "Await"

        self.message_to_js(
            stop=True)
    
   
    
    
                            
    
    
    def sendPrinterState(self):
        try:
            index = int(flask.request.args.get("index", 0))
            self.ejecting=SheildControl.Sequence_Finish()
            threading.Timer(5.0, self.sendPrinterState).start()
            self.connection==True
            self.ejecting=SheildControl.Sequence_Finish()
            if self.connection == True:
                print("-----------------------------------------------------------------------------------+"+state+"-----------------------")
                state = self._printer.get_state_id()
                
                jsonData = json.dumps(dict(
                    disableEject= 1 if state == "OPERATIONAL" else 0
                ))

            else:
                self.ejecting=SheildControl.Sequence_Finish()
                print(self.ejecting)
                print(self.ejecting)
                if self.isQueuePrinting == True and self.isQueueStarted == True and self.ejecting==True and self.printdonee==True:
                    while True:
                        print("*******************************")
                        self._logger.info("queue is wating ejecting")
                        print(self.ejecting)
                        time.sleep(0.4)
                        if self.ejecting == False:
                            print(self.queue_numberofmembers)
                            break
                    if(self.queue_numberofmembers>1):
                        
                        self.message_to_js
                        print("next queue item")
                        print(self.queue_state)
                        self.eject_fail = True
                        self.isQueuePrinting = False
                        self.isManualEject = False
                    else:
                        print("print and queue finishhhhhh")
                                


        except Exception as e:
            print(type(e))

    
    def get_settings_defaults(self):
        return dict(
           
            esp_address="",
            motor_Pin1=15,
            motor_Pin2=18,
            switch_Front=27,
            switch_Back=22,
            button_Forward=2,
            button_Backword=3,
            button_Sequence=4,
            minTask_Temp=40,
            max_queues=10,
            delaySeconds=10,
            target_bed_temp=40,
            servo_allowed=False,
            spero_current_queue=None,
            speroplugin_current_queue=None
          
        )

   

    def on_settings_save(self, data):
        target_temp = self._settings.get(["target_bed_temp"])
        motor_1=self._settings.get(["motor_Pin1"])
        motor_2=self._settings.get(["motor_Pin2"])
        front_switch=self._settings.get(["switch_Front"]) 
        switch_back=self._settings.get(["switch_Back"])
        forward_button=self._settings.get(["button_Forward"])
        backworld_button=self._settings.get(["button_Backword"])
        Sequence_button=self._settings.get(["button_Sequence"])
        min_Task=self._settings.get(["minTask_Temp"])
        queues_max=self._settings.get(["max_queues"])
        seconds_delay=self._settings.get(["delaySeconds"])
            
        
    
        self.pins=[motor_1,motor_2,front_switch,switch_back,forward_button,backworld_button,Sequence_button,min_Task,queues_max,seconds_delay]
        self.message_to_js(targetTemp=target_temp)
        self.message_to_js(motorPin1=motor_1)
        self.message_to_js(motorPin2=motor_2)
        self.message_to_js(switchFront=front_switch)
        self.message_to_js(switchBack=switch_back)
        self.message_to_js(buttonForward=forward_button)
        self.message_to_js(buttonBackword=backworld_button)
        self.message_to_js(buttonSequence=Sequence_button)
        self.message_to_js(minTaskTemp=min_Task)
        self.message_to_js(maxQueues=queues_max)
        self.message_to_js(delaySeconds=seconds_delay)
   
        
        
        return super().on_settings_save(data)

    def message_to_js(self,canselQuee="as", state ="asdpkasşd",print_bed_state="bbbb",espState="aaaaa",ahmet="asdoahsdnjashndklj",targetTemp=None,motorPin1=None, motorPin2=None ,switchFront= None,buttonForward=None,switchBack=None,buttonBackword=None, buttonSequence=None,
                      minTaskTemp=None ,maxQueues= None,delaySeconds=None,sendItemIndex=False, stop=False, terminate=None, itemResult=None,ejecting_finish=None,printStart=None):



   
        message = {}
        if(canselQuee != None):
            message["canselQuee"] = canselQuee
        if(state != None):
            message["state"] = self.state
        if(print_bed_state != None):
            message["print_bed_state"] = self.print_bed_state  
        if(espState != None):
            message["espState"] = self.espState                               
        if(self.esp != None):
            message["esp"] = self.esp
        if(ahmet != None):
            message["ahmet"] = self.ahmet
        if(targetTemp != None):
            message["targetTemp"] = targetTemp
        if(motorPin1 != None):
            message["motorPin1"] = motorPin1  
        if(itemResult != None) and (self.current_queue["items"] != None or self.current_queue["items"].__len__() > 0):
            message["itemResult"] = self.itemResult
        if(motorPin2 != None):
            message["motorPin2"] = motorPin2    
        if(switchFront != None):
            message["switchFront"] = switchFront 
        if(switchBack != None):
            message["switchBack"] = switchBack 
        if(buttonBackword != None):
            message["buttonBackword"] = buttonBackword    
        if(buttonBackword != None):
            message["buttonBackword"] = buttonBackword   
        if(buttonSequence!= None):
            message["buttonSequence"] = buttonSequence    
        if(minTaskTemp != None):
            message["minTaskTemp"] = minTaskTemp    
        if(maxQueues != None):
            message["maxQueues"] = maxQueues                                                  
        if(delaySeconds != None):
            message["delaySeconds"] = delaySeconds    
        if(self.sheild != None):
            message["esp"] = self.sheild
        if(self.isQueuePrinting != None):
            message["isQueuePrinting"] = self.isQueuePrinting
        if(self.isManualEject != None):
            message["isManualEject"] = self.isManualEject
        if(sendItemIndex) and self.current_queue["items"] != None and self.current_queue["items"].__len__() > 0 and self.current_item != None:
            message["index"] = self.current_item["index"]
        if(stop):
            message["stop"] = stop
        if(terminate != None):
            message["terminate"] = terminate
        if(itemResult != None) :
            message["itemResult"] = itemResult
        if(targetTemp != None):
            message["targetTemp"] = targetTemp
        if(ejecting_finish != None):
            message["ejecting_finish"] = self.ejecting_finish
        if(printStart != None):
            message["printStart"] = self.printStart       
        if(self.ejectStart != None):
             message["ejectStart"] = self.ejectStart   
        if(self.esp != None):
            message["esp"] = self.esp   
    
        self._plugin_manager.send_plugin_message(self._identifier, message)  
                                                                                                                                                                 
               
  
    def sendPin(self):
        motor_1=self._settings.get(["motor_Pin1"])
        motor_2=self._settings.get(["motor_Pin2"])
        front_switch=self._settings.get(["switch_Front"]) 
        switch_back=self._settings.get(["switch_Back"])
        forward_button=self._settings.get(["button_Forward"])
        backworld_button=self._settings.get(["button_Backword"])
        Sequence_button=self._settings.get(["button_Sequence"])
        min_Task=self._settings.get(["minTask_Temp"])
        queues_max=self._settings.get(["max_queues"])
        seconds_delay=self._settings.get(["delaySeconds"])
        self.pins=[motor_1,motor_2,front_switch,switch_back,forward_button,backworld_button,Sequence_button,min_Task,queues_max,seconds_delay]
       
        
  
    

    def get_template_configs(self): 
        return [
            dict(type="settings", custom_bindings=False),
            dict(type="tab", custom_bindings=False)
        ]

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/speroplugin.js"],
            "css": ["css/speroplugin.css"],
            "less": ["less/speroplugin.less"],
        }
      # ~~ Softwareupdate hookpauseindexet("index", 0))
      
        self.start_print(canceledIndex=index)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/save_to_database", methods=["POST"])
    @ restricted_access
    def save_to_database(self):
        data = flask.request.get_json()
        directory = (ROOT_DIR + '/queues.json')
        Exist = Query()
        db = TinyDB(directory)
        # queues = db.all()

        self.current_queue["name"] = data["queue_name"]
        queue_id = data["id"]
        name = data["queue_name"]  if data["queue_name"]  != "" or data["queue_name"]  != None else "New Queue"
        items = self.current_queue["items"] if self.current_queue["items"] !=None else []

        inDb = db.search(Exist.id == queue_id)

        if(len(inDb) > 0 and inDb != None):
            db.update({
                'items': items,
                'name':name,
                'updateTime':str(datetime.datetime.now()),
            },Exist.id==queue_id)
        else:
            db.insert({
                    'items': items,
                    'id': queue_id,
                    'updateTime':str(datetime.datetime.now()),
                    'createTime':str(datetime.datetime.now()),
                    'name': name
                })

        self._settings.set(["speroplugin_current_queue"], json.dumps(self.current_queue))
        self._settings.save()

        self.get_from_database()
        db.close()
        

        res = jsonify(success=True)
        res.status_code = 200
        return res

    def get_template_vars(self):
        return dict(url=self._settings.get(["url"]))
    
    @ octoprint.plugin.BlueprintPlugin.route("/sendTimeData", methods=["POST"])
    @ restricted_access
    def sendTimeData(self):
        data = flask.request.get_json()

        if data["timeLeft"]!=None and data["index"]!=None:
            self.current_queue["items"][data["index"]]["timeLeft"] = data["timeLeft"]

        if self.totalEstimatedTime != None:
            self.totalEstimatedTime = data["totalEstimatedTime"]
        else:
            self.totalEstimatedTime = 0

        res = jsonify(success=True, data="time done")
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/sendTerminateMessage", methods=["GET"])
    @ restricted_access
    def sendTerminateMessage(self):
        if self.ejecting != True:
            self.ejecting = True

        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/delete_from_database", methods=["DELETE"])
    @ restricted_access
    
    def delete_from_database(self):
        
        queue_id = flask.request.args.get("id")
        
        self.current_queue = None

        Exist = Query()
        db = TinyDB(ROOT_DIR+"/queues.json")
        db.remove(Exist.id == queue_id)
        db.close()

        self._settings.remove(["speroplugin_current_queue"])

        self.get_from_database()

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    octoprint.plugin.BlueprintPlugin.route("/queue_item_up", methods=["GET"])
    @ restricted_access
  
    def queue_item_up(self):
        index = int(flask.request.args.get("index", 0))

        if len(self.current_queue["items"]) > 1:

            itemCurr = self.current_queue["items"][index]
            itemCurr["index"] = index - 1
            itemNext = self.current_queue["items"][index - 1]
            itemNext["index"] = index

            self.current_queue["items"][index] = itemNext
            self.current_queue["items"][index - 1] = itemCurr


        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    octoprint.plugin.BlueprintPlugin.route("/pointer", methods=["GET"])
    @ restricted_access
    def pointer(self):
        index = int(flask.request.args.get("index", 0))
        self.pauseindex=index
        isim="ahmet"
        sayi=1
        print(index)
        res = jsonify(success=True)
        res.status_code = 200
        return render_template("speroplugin_tab.jinja2",isim=isim,sayi=sayi)
    
    
    

    @octoprint.plugin.BlueprintPlugin.route("/api/printer/bed?history=true&limit=2 HTTP/1.1", methods=["GET"])
    @restricted_access
    def set_enclosure_temp_humidity(self, identifier):
        data = request.json ;
        self.A = data["bed"];
        print(self.A)
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/pause_resume_queue", methods=["GET"])
    @ restricted_access
    def pause_resume_queue(self):
    
        if self.stateCanselled==True:
            self.stateCanselled=False
            
        if self.Pauseclick==True:
            self.Pauseclick=False

        self.Next_item()
        # printer_state = self._printer.get_state_id()
        # queue_state = self.queue_state

        # if queue_state == "PAUSED":
        #     self.queue_state = "RUNNING"
        #     if printer_state == "OPERATIONAL":
        #         if self.current_item["index"] == len(self.current_queue["items"]) - 1:
        #             self.queue_state = "FINISHED"
        #             self.stop_queue()
        #         else:
        #             self.start_print()
        #     elif printer_state == "PAUSED":
        #         self._printer.resume_print()
        # elif queue_state == "RUNNING" or queue_state == "STARTED":
        #     self.queue_state = "PAUSED"

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    @ octoprint.plugin.BlueprintPlugin.route("/pause_stop_queue", methods=["GET"])
    @ restricted_access
    def pause_stop_queue(self):
        self.queue_state == "PAUSED"
        self.Pauseclick=True  
      
        
        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    @ octoprint.plugin.BlueprintPlugin.route("/cancel_queue", methods=["GET"])
    @ restricted_access
    def cancel_queue(self):
        print("queuq canselelled")
        self.stateCanselled=True
        self.currentİndex=-1
        queue = self.current_queue["items"]
        for item in queue:
            item["state"] = "Await"
            
        self.Next_item()
    


    
        # self.sheild_motor = "IDLE"
        # self.queue_state = "IDLE"
        # state = self._printer.get_state_id()
        # if state == "OPERATIONAL":
        #     self.stop_queue()

        # if state == "PRINTING" or "PAUSED":
        #     self._printer.cancel_print()

        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/start_queue", methods=["GET"])
    @ restricted_access
    def start_queue(self):
        print("start quequ")
        self.message_to_js(motorPin1=12)
        self.esp["motor"] = 'IDLE'
        self.queue_state = "STARTED"
        self.printStart=True
        self.isQueueStarted = True 
        self.isQueuePrinting = True
   
        self.isQueueStarted = True
        totalTime = flask.request.args.get("totalEstimatedTime", 0)
        self.totalEstimatedTime = totalTime

        if len(self.current_queue["items"]) > 0:
            print(len(self.current_queue["items"]))
            self.queue_numberofmembers=len(self.current_queue["items"])
            self.start_print()

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/get_current_states", methods=["GET"])
    @ restricted_access
    def get_current_states(self):
        index = None
        if self.current_item != None:
            index = self.current_item["index"]

        if self.stateCanselled==True:
            self.queue_state="CANCELLED"
            
        if self.stateCanselled==False:
            self.queue_state="RUNNING"
               
        if(self.Pauseclick==True):
            self.queue_state="PAUSED"
            
        if(self.Pauseclick==False):
                self.queue_state="RUNNING"

        self.espState=SheildControl.motor_State()
        self.print_bed_state="IDLEE"


        target_temp = self._settings.get(["target_bed_temp"])
        motor_1=self._settings.get(["motor_Pin1"])

        queue = json.dumps(dict(queue=self.current_queue,
                                isQueueStarted=self.isQueueStarted,
                                isQueuePrinting=self.isQueuePrinting,
                                isManualEject=self.isManualEject,
                                totalEstimatedTime=self.totalEstimatedTime,
                                queues=self.queues,
                                queue_state=self.queue_state,
                                current_index=index,
                                current_files=self.currentFiles,
                                esp=self.esp,
                                espState=self.espState,
                                print_bed_state=self.print_bed_state,
                                ejecting=self.ejecting,
                                eject_fail=self.eject_fail,
                                target_temp=target_temp,
                                motor_1=motor_1,
                               
                                ))
        return queue
  
    
    @ octoprint.plugin.BlueprintPlugin.route("/device_controll", methods=["POST"])
    @ restricted_access
    def device_controll(self):
        data = flask.request.get_json()  
        if (data["request"] =="backward"):
            SheildControl.getMessage("backword")
            self.espState="MOTOR GOING TO BACKWARD"
        if (data["request"] =="forward"):
            SheildControl.getMessage("forward")
            self.espState="MOTOR GOING TO FORWARD"
        if (data["request"] =="stop"):
            SheildControl.getMessage("stop")
            self.espState="MOTOR STOP"
        if (data["request"] =="eject"):
            SheildControl.startSequence()
            
        


        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/create_queue", methods=["GET"])
    @ restricted_access
    def create_queue(self):
        self.current_queue = dict(
            id=str(uuid.uuid4()),
            name="New Queue",
            items= [],
        )

        self.queues.append(self.current_queue)

        self.current_item = None
        self.currentTime = 0
        self.totalEstimatedTime = 0

        res = jsonify(success=True)
        res.status_code = 200
        return res

    
    @ octoprint.plugin.BlueprintPlugin.route("/queue_item_down", methods=["GET"])
    @ restricted_access
    def queue_item_down(self):
        index = int(flask.request.args.get("index", 0))

        if len(self.current_queue["items"]) > 1:
            itemCurr = self.current_queue["items"][index]
            itemCurr["index"] = index + 1

            itemNext = self.current_queue["items"][index+1]
            itemNext["index"] = index

            self.current_queue["items"][index] = itemNext
            self.current_queue["items"][index + 1] = itemCurr


        res = jsonify(success=True)
        res.status_code = 200
        return res

    # QUEUE UP-DOWN END



    @ octoprint.plugin.BlueprintPlugin.route("/queue_add_item", methods=["POST"])
    @ restricted_access
    def queue_add_item(self):
        self.queueee=self.queueee+1
        queue = self.current_queue["items"]

        data = flask.request.get_json()
        queue.append(
            dict(
                index=data["index"],
                name=data["item"]["name"],
                path=data["item"]["path"],
                sd=data["item"]["sd"],
                state="Await",
                timeLeft=data["item"]["timeLeft"]
            )
        )
        print("---------------------------------------------------------------------------------------")
        print(self.current_queue["items"])
        print("---------------------------------------------------------------------------------------")
        res = jsonify(success=True, data="")
        res.status_code = 200
        return res

   
    @ octoprint.plugin.BlueprintPlugin.route("/queue_remove_item", methods=["DELETE"])
    @ restricted_access
    def queue_remove_item(self):
        self.queueee=self.queueee-1
        index = int(flask.request.args.get("index", 0))
        queue = self.current_queue["items"]
        queue.pop(index)

        for i in queue:
            if i["index"] > index:
                i["index"] -= 1

        print("---------------------------------------------------------------------------------------")
        print(self.current_queue["items"])
        print("---------------------------------------------------------------------------------------")
        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/queue_duplicate_item", methods=["GET"])
    @ restricted_access
    def queue_duplicate_item(self):
        index = int(flask.request.args.get("index", 0))
        queue = copy.deepcopy(self.current_queue["items"])

        item = queue[index]
        item["index"] += 1

        for i in self.current_queue["items"]:
            if i["index"] > index:
                i["index"] += 1

        self.current_queue["items"].insert(item["index"], item)

        res = jsonify(success=True)
        res.status_code = 200
        return res

   
    @ octoprint.plugin.BlueprintPlugin.route("/get_queue", methods=["GET"])
    @ restricted_access
    def get_queue(self):
        queue_id = flask.request.args.get("id")

        for queue in self.queues:
            if queue["id"] == queue_id:
                self.current_queue = queue
                break

        res = jsonify(success=True)
        res.status_code = 200
        return res    
 
    def get_update_information(self):
            # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
          return {
            "speroplugin": {
                "displayName": "Spero plugin",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "AHMET_SARIOĞLU",
                "repo": "octoprint_spero",
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/ahmet-sa/projeOctoprint/archive/{target_version}.zip",
            }
        }
    def sanitize_temperatures(self,comm_instance, parsed_temperatures, *args, **kwargs):
        x = parsed_temperatures.get('B')
        if x:
            self.tempeartures_temp=x[0]
        return parsed_temperatures
    
    def temperatures(self):
        self.c=self.tempeartures_temp
        if(self.c<=45):
            self.Ejecting()
        else:
            print("waiting idealll temp")
            time.sleep(0.6)
            self.WaittingTem()
            

__plugin_name__ = "Spero Plugin"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = Speroplugin()

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Speroplugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.temperatures.received": (__plugin_implementation__.sanitize_temperatures,1)
        
    }