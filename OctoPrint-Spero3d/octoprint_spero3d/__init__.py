# coding=utf-8
from __future__ import absolute_import

from threading import Timer
from flask.globals import request
from tinydb.database import TinyDB
from tinydb.queries import Query
import copy
from octoprint.filemanager.storage import StorageInterface as storage
from .SheildControl import SheildControl
import os
import flask
import json
import uuid
import datetime

from flask import jsonify
import json


from octoprint.server.util.flask import (
    restricted_access,
)

import octoprint.plugin


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = None
class Spero3dPlugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.BlueprintPlugin,
                    octoprint.plugin.AssetPlugin,               
                    octoprint.plugin.EventHandlerPlugin,
                    octoprint.plugin.ProgressPlugin,  
                        ):




    def __init__(self):
        self.esp = dict()
        self.queues = []
        self.queue_state = "IDLE"
    
        self.print_bed_state="Idle"
        self.motor_state="Idle"
        self.ejecting = False
        self.eject_fail = False
        self.connection = "False"
        self.heat=60.00
        self.tempeartures_temp=60.00
        self.current_index=0
        self.temp=None
        self.queue_finish="None"
        self.index=None
        self.eject_fail_continuous=False
        self.pointer_click=True
        self.control_eject=False
        self.the_last_queue=None
        self.last_queuee=None
        self.sheild_control=SheildControl(buttonForward,6,3,23,18,4,8)
        self.sheild_control.on_state_change = self.get_states
     
   
        
        
        
        
        self.current_queue = None
        self.last_queue = None
        self.current_item = 'IDLE'
        self.currentFiles = []
        self.sheiled_state="sa"

        self.totalEstimatedTime = -1


        self.isQueueStarted = False
        self.isQueuePrinting = False
   

     
       
        self.kontrol=False





    def on_startup(self, host, port):
   
        
        db = TinyDB('db.json')
        
    
        fileDir = ROOT_DIR + "\\queues.json"
        fileExist = os.path.exists(fileDir)
        if not fileExist:
            open(fileDir, 'w+')
        
        



        

        if self.current_queue != None and len(self.queues) > 0:
            if self.current_queue["items"] != None:
                for item in self.current_queue["items"]:
                    item["state"] = "Await"
        else:
            self.current_queue = dict(
                id=str(uuid.uuid4()),
                name="New Queue",
                items= [],
            )
        return super().on_startup(host, port)

   
            
    def on_after_startup(self):
            
    
        self.sheild_control=SheildControl(forward_button,backworld_button,button_Sequence,motor_Pin1,motor_Pin2,switch_Front,switch_back)
        self.sheild_control.on_state_change = self.get_states
    
        
        db = TinyDB('db.json')
        db = TinyDB(ROOT_DIR+"/queues.json")
        end=Query()
        result=(db.search(end.last=="last"))
        print(result)
        
        print("//////////////////////////////////////////////////")
        print("**********---------------------////////")
        print("//////////////////////////////////////////////////")
        print(result[0]["name"])
        print("**********---------------------////////")
        
        print("//////////////////////////////////////////////////")
        print(result[0]["items"])
        print("**********---------------------////////")
        print(self.current_queue)
        print("111111111111111111111111")
        print(self.current_queue["name"])
        
        name=self.current_queue["name"]=result[0]["name"]
        print(name)
        print("22222222222222222222222222222222222")
        self.last_queuee=name
        
     
        
    
        
        print(self.sheild_control.connection())
        print("sasoısudhsdjuoashdaosdjı")
        self.connection=self.sheild_control.connection()
        
        
        self._logger.info("KİNG İS HEREEE (more: %s)" % self._settings.get(["url"]))
        self.sheild_control.button_init()
        self.message_to_js(index_current=0)
        db = TinyDB('db.json')
        db.search(self.the_last_queue)
        print(self.the_last_queue)
        self.last_queuee="none"
        
        print(db.all)
        
        
        
        
    
         
                      
    def on_event(self, event, payload):
        state = self._printer.get_state_id()
        if self.isQueueStarted == True and self.isQueuePrinting == True:
            if state == "CANCELLING":
                self.current_item["state"] = "Cancelling"

            if state == "FINISHING":
                self.current_item["state"] = "Ejecting"

            if state == "PAUSING":
                self.queue_state = "PAUSING"
                self.message_to_js(terminate=True)

            # if state == "PAUSED":

            if event == "Disconnected" or event == "Error":
                if self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"
                    self.current_item["state"] = "Failed"
                    self.message_to_js(sendItemIndex=True)

            if event == "PrintStarted" or event == "PrintResumed":  
                if(self.queue_state != "CANCELED" and self.queue_state != "FINISHED"and self.queue_state != "PAUSED"):
                    self.queue_state = "RUNNING"
                self.current_item["state"] = "Printing"
                self.message_to_js(
                    sendItemIndex=True)

            if event == "PrintPaused":
                # self.current_item["state"] = "Paused"
                self.queue_state = "PAUSED"
                self.message_to_js(
                    sendItemIndex=True, terminate=False)

            if event == "DisplayLayerProgress_progressChanged":

                if self.current_item["state"] != "Ejecting" and self.current_item["state"] != "Cancelling":

                    self.current_item["state"] = "Printing"

                self.message_to_js(
                    sendItemIndex=True)

            if event == "PrintCancelling":
                if self.queue_state != "CANCELED" and self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"

                self.message_to_js(terminate=True)

            if event == "PrintFailed" or event == "PrintCanceled":
                if self.queue_state != "CANCEL" and self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"

                # if event != "PrintCanceled":
                #     if self.isQueuePrinting == False:
                #         self.current_item["state"] = "Canceled"
                #     else:
                #         self.current_item["state"] = "Cancelling"
                # else:
                #     if self.current_item["state"] != "Cancelling":
                #         self.current_item["state"] = "Failed"

                self.queue_state="CANCEL"
                
                self.message_to_js(
                    sendItemIndex=True, terminate=True,itemResult="Canceled") 
             

            if event == "PrinterStateChanged" and self.queue_state != "PAUSED":
                state = self._printer.get_state_id()

            if event == "PrintDone":
                self.message_to_js(
                sendItemIndex=True, itemResult="Ejecting")
                self.waitting_tem() 
                
     
      
    def get_states(self,bed,motor,eject_faill):
        if eject_faill==True:
            self.current_item["state"] = "PAUSED"
        self.print_bed_state=bed
        self.motor_state=motor
        self.eject_fail=eject_faill
        self.message_to_js(print_bed_state=bed,motor_state=motor,eject_fail=eject_faill)
          
         
    def waitting_tem(self):
        self.heat=self.tempeartures_temp
        if self.heat<=45:
            self.Ejecting()
        else:
  
            waitTimer = Timer(1,self.temperatures,args=None,kwargs=None)
            waitTimer.start()           
          
                
    def Ejecting(self):
        self.sheild_control.start_sequence()
        self.WaittingEject()
          
        
    def WaittingEject(self):
        
        if self.eject_fail ==False:
            self.control_eject=self.sheild_control.sequence_finish
            if(self.control_eject==True):
                    
                    
                self.message_to_js(
                        sendItemIndex=True, itemResult="Finished")
                self.eject_fail_continuous=False 
                print("///////////////////////")
                print(self.queue_state )
                print("/////////////////////////")
                self.current_item["state"] = "Finished"
                self.itemResult="Finished"  
                self.current_index=self.current_index+1
                self.message_to_js(
                    index_current=self.current_index)
                        
                    
                if self.current_index==self.current_queue["items"].__len__():
                    self.queue_state="FINISHED"
                    self.current_index=0
                    self.message_to_js(index_current=-1)
                    self.do_item_state_await()
                    
            
            
        
                if self.queue_state=="CANCELED" or self.queue_state=="FINISHED":
                        self.message_to_js(
                        sendItemIndex=True, itemResult="Await",cansel_queue="yes",index_current=-1) 
                        self.queue_state="IDLE"
                        self.do_item_state_await()
                        
                self.Next_item() 
            else:
                waitTimer2 = Timer(1,self.WaittingEject,args=None,kwargs=None)
                waitTimer2.start()
        else:
            self.Next_item()          
          
    def Next_item(self):
        print(self.queue_state )
        if self.queue_state == "RUNNING":
            print(self.control_eject)
            if(self.queue_state == "RUNNING" and self.control_eject==True):
            
                self.eject_fail=True
                self.message_to_js(index_current=self.current_index)
                self.start_print()   
            else:
                print("print and queue finish") 
         
        else:
            print("queue and print finisheeed")
      
            
    def do_item_state_await(self) :
        for i in range(self.current_queue["items"].__len__()):
            self.current_queue["items"][i]["state"] = "Await"
       
            
            

    def get_from_database(self):
        db = TinyDB(ROOT_DIR+"/queues.json")
        queues = db.all()
        self.queues = []
        if len(queues) > 0:
            param = 0
            for queue in queues:
                self.queues.append(queue)
                param += 1
        
        

    def start_print(self, canceledIndex=None):
        if self.queue_state == "RUNNING"or self.queue_state=="STARTED":
            queue = self.current_queue["items"]
            self.print_file = None
            
            if (self.queue_state == "RUNNING" or self.queue_state == "STARTED" or canceledIndex != None):
                self.print_file = None

                if canceledIndex != None:
        
                    self.current_queue["items"][canceledIndex]["state"] = "Await"
                    self.print_file = self.current_queue["items"][canceledIndex]
                else:
                    for item in queue:
                            self.print_file = item
                            break
            if self.print_file != None:
                is_from_sd = None
                if self.print_file["sd"] == "true":
                    is_from_sd = True
                else:
                    is_from_sd = False
                    
            if self.index !=None:
                self.current_index=self.index    
                self.message_to_js(index_current=self.current_index)
                self.index=None    
                
            if self.current_index!=self.current_queue["items"].__len__():
                self.current_item=self.current_queue["items"][self.current_index]
                self.message_to_js(index_current=self.current_index)
            
                self.print_file=self.current_item    
                self._printer.select_file(self.print_file["path"], is_from_sd)
                self.print_startted()
                self.current_item["state"]
                self.message_to_js(
                    sendItemIndex=True, itemResult= self.current_item["state"])
            else :
                self.current_index=0
                self.message_to_js(finis_queue="yes")
                self.message_to_js(index_current=self.current_index)
                 
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
                 
                 
    
    def print_startted(self):
        self.message_to_js(index_current=self.current_index)
        self.itemResult="print"    
        self._printer.start_print()
        self.isQueuePrinting = True
    
  


    
    def get_settings_defaults(self):
        
        
        return dict(
            motor_Pin1=23,
            motor_Pin2=18,
            switch_Front=4,
            switch_Back=8,
            button_Forward=2,
            button_Backword=6,
            button_Sequence=3,
            minTask_Temp=40,
            max_queues=10,
            delaySeconds=10,
            target_bed_temp=40,
            servo_allowed=False,
            spero_current_queue=None,
            spero3d_current_queue=None
            
        )
        self.sheild_control=SheildControl(button_Forward,backworld_button,button_Sequence,motor_Pin1,motor_Pin2,switch_Front,switch_back)
        self.sheild_control.on_state_change = self.get_states



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

    def message_to_js(self,last_queuee="none",queue_finish="Nonee",temp=None,eject_fail=None,print_bed_state="bbbb",motor_state="aaaaa",targetTemp=None,motorPin1=None, motorPin2=None ,switchFront= None,buttonForward=None,switchBack=None,buttonBackword=None, buttonSequence=None,
                      minTaskTemp=None ,maxQueues= None,delaySeconds=None,sendItemIndex=False, stop=False, terminate=None, itemResult=None,cansel_queue="asd",index_current=0,finis_queue="aaaa",connection="none"):

        message = {}
        if(eject_fail != None):
            message["eject_fail"] = self.eject_fail  
        if(last_queuee != None):
                message["last_queuee"] = self.last_queuee           
        if(print_bed_state != None):
            message["print_bed_state"] = self.print_bed_state              
        if(motor_state != None):
            message["motor_state"] = self.motor_state        
        if(queue_finish != None):
            message["queue_finish"] = queue_finish     
        if(connection != None):
            message["connection"] = self.connection             
            
                   
        if(index_current != None):
            message["index_current"] = index_current
            
        if(finis_queue != None):
            message["finis_queue"] = finis_queue      
            
        if(temp != None):
            message["temp"] = temp
        if(targetTemp != None):
            message["targetTemp"] = targetTemp
        if(cansel_queue != None):
            message["cansel_queue"] = cansel_queue      
        if(motorPin1 != None):
            message["motorPin1"] = motorPin1  
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
        if(self.esp != None):
            message["esp"] = self.esp
        if(self.isQueuePrinting != None):
            message["isQueuePrinting"] = self.isQueuePrinting
        if(sendItemIndex) and self.current_queue["items"] != None and self.current_queue["items"].__len__() > 0 and self.current_item != None:
            message["index"] = self.current_item["index"]
        if(stop):
            message["stop"] = stop
        if(terminate != None):
            message["terminate"] = terminate
        if(itemResult != None) and (self.current_queue["items"] != None or self.current_queue["items"].__len__() > 0):
            message["itemResult"] = itemResult
        if(targetTemp != None):
            message["targetTemp"] = targetTemp

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




        # ~~ Softwareupdate hook

    @ octoprint.plugin.BlueprintPlugin.route("/queue_item_restart", methods=["GET"])
    @ restricted_access
    def queue_item_restart(self):
        index = int(flask.request.args.get("index", 0))

        self.start_print(canceledIndex=index)

        self.queue_state = "RUNNING"

        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/save_to_database", methods=["POST"])
    @ restricted_access
    def save_to_database(self):
        
        data = flask.request.get_json()
        directory = (ROOT_DIR + '/queues.json')

        Exist = Query()
        db = TinyDB(directory)
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

        self._settings.set(["spero3d_current_queue"], json.dumps(self.current_queue))
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
    
    @ octoprint.plugin.BlueprintPlugin.route("/device_controll", methods=["POST"])
    @ restricted_access
    def device_controll(self):
        data = flask.request.get_json()  
        if (data["request"]):
            self.sheild_control.send_actions(data["request"])

            
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

        self._settings.remove(["spero3d_current_queue"])

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
    
    
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/pause_resume_queue", methods=["GET"])
    @ restricted_access
    def pause_resume_queue(self):
        if self.queue_state=="FINISHED":
            self.current_index=-1
    
        if self.queue_state=="CANCELED":
            self.Next_item()
     
        if self.eject_fail==True:
            print("eject fail")
            self.control_eject=True
            self.eject_fail=False
            self.queue_state="RUNNING"
            self.Next_item()
          
        else:
            self.queue_state="RUNNING"
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
    @ octoprint.plugin.BlueprintPlugin.route("/cancel_queue", methods=["GET"])
    @ restricted_access
    def cancel_queue(self):

        self.queue_state="CANCELED"
        self.current_index=-1  
     

        
        self.Next_item()
        
        
        
        # state = self._printer.get_state_id()

        # if state == "OPERATIONAL":
        #     self.stop_queue()

        # if state == "PRINTING" or "PAUSED":
        #     self._printer.cancel_print()

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/pause_stop_queue", methods=["GET"])
    @ restricted_access
    def pause_stop_queue(self):
        self.queue_state= "PAUSED"
        self.Next_item()
        

        res = jsonify(success=True)
        res.status_code = 200
        return res
    

    
    @ octoprint.plugin.BlueprintPlugin.route("/start_queue", methods=["GET"])
    @ restricted_access
    def start_queue(self):
        self.queue_state = "STARTED"
        self.isQueueStarted = True

        totalTime = flask.request.args.get("totalEstimatedTime", 0)
        self.totalEstimatedTime = totalTime

        if len(self.current_queue["items"]) > 0:
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

        target_temp = self._settings.get(["target_bed_temp"])

        queue = json.dumps(dict(queue=self.current_queue,
                                isQueueStarted=self.isQueueStarted,
                                isQueuePrinting=self.isQueuePrinting,
                                totalEstimatedTime=self.totalEstimatedTime,
                                queues=self.queues,
                                queue_state=self.queue_state,
                                current_index=self.current_index,
                                current_files=self.currentFiles,
                                esp=self.esp,
                                print_bed_state=self.print_bed_state,
                                eject_fail=self.eject_fail,
                                motor_state=self.motor_state,
                                queue_finish=self.queue_finish,
                                temp=self.temp,
                                ejecting=self.ejecting,
                                target_temp=target_temp,
                                connection=self.connection,
                                
                                ))
        return queue
    
   
   
    @ octoprint.plugin.BlueprintPlugin.route("/get_datas", methods=["GET"])
    @ restricted_access
    def get_datas(self):
     

        self.queues.append(self.current_queue)

        self.current_item = None
        self.currentTime = 0
        self.totalEstimatedTime = 0

        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/create_queue", methods=["GET"])
    @ restricted_access
    def create_queue(self):
        self.last_queuee="New Queue"
        self.current_queue = dict(
            id=str(uuid.uuid4()),
            name="New Queue",
            items= [],
        )
        self.last_queuee="none"
        
        
        # self.the_last_queue=self.current_queue
        # db = TinyDB('db.json')
        # db.insert(self.the_last_queue) 
        



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
        res = jsonify(success=True, data="asdadasdas")
        res.status_code = 200
        return res





       
    @octoprint.plugin.BlueprintPlugin.route("/pointer", methods=["GET"])
    @ restricted_access
    def pointer(self):
        self.index = int(flask.request.args.get("index", 0))
        print(self.index)
        
        res = jsonify(success=True)
        res.status_code = 200
        return res

     
    
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/queue_remove_item", methods=["DELETE"])
    @ restricted_access
    def queue_remove_item(self):
        index = int(flask.request.args.get("index", 0))
        queue = self.current_queue["items"]
        queue.pop(index)

        for i in queue:
            if i["index"] > index:
                i["index"] -= 1

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



    def get_assets(self):
        return {
            "js": ["js/spero3d.js"],
            "css": ["css/spero3d.css"],
            "less": ["less/spero3d.less"]
        }







    def get_update_information(self):
      
        return {
            "spero3d": {
                "displayName": "Spero3d Plugin",
                "displayVersion": self._plugin_version,

           
                "type": "github_release",
                "user": "you",
                "repo": "OctoPrint-Spero3d",
                "current": self._plugin_version,

           
                "pip": "https://github.com/you/OctoPrint-Spero3d/archive/{target_version}.zip",
            }
        }

    def sanitize_temperatures(self,comm_instance, parsed_temperatures, *args, **kwargs):
        x = parsed_temperatures.get('B')
        if x:
            self.tempeartures_temp=x[0]
            self.message_to_js(temp=self.tempeartures_temp)
        return parsed_temperatures
    
    def temperatures(self):
        self.heat=self.tempeartures_temp
        if(self.heat<=45):
            self.Ejecting()
        else:
            self.waitting_tem()
            
 




__plugin_name__ = "Spero3d Plugin"

__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Spero3dPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.temperatures.received": (__plugin_implementation__.sanitize_temperatures,1)
    }