# coding=utf-8
from __future__ import absolute_import
from asyncio import queues
from threading import Timer

from flask.globals import request
from octoprint.plugin.types import SettingsPlugin
from octoprint.settings import settings
from octoprint_speroplugin.PluginEnums import BedPosition, EjectState, ItemState, MotorState, QueueState
from tinydb.database import TinyDB
from tinydb.queries import Query
import copy
from octoprint.filemanager.storage import StorageInterface as storage
# from .SheildControl import SheildControl
import os
import flask
import json
import uuid
import datetime
""
from flask import jsonify
import json


from octoprint.server.util.flask import (
    restricted_access,
)

import octoprint.plugin


class Speroplugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.BlueprintPlugin,
                    octoprint.plugin.AssetPlugin,               
                    octoprint.plugin.EventHandlerPlugin,
                    octoprint.plugin.ProgressPlugin,  
                        ):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    FILE_DIR = None

    settingsParams = ["targetBedTemp","motorPin1","motorPin2","switchFront","switchBack","buttonForward","buttonBackword","buttonSequence","delaySeconds","currentIndex"]
    
    requiredDatas = ["settings","currentIndex","bedPosition",'motorState','isShieldConnected','queueState','currentQueue',
                    'itemState',    ]

    def __init__(self):
        self.queues = []
        self.queueState = QueueState.IDLE.value  # queueState
        self.bedPosition=BedPosition.MIDDLE.value   # bedPosition -> middle front back
        self.motorState=MotorState.IDLE.value            # motorState -> idle forward backward
        self.ejectState=EjectState.WAIT_FOR_TEMP
        self.itemState=ItemState.AWAIT.value
        

        self.currentIndex=0
        # self.ejecting= False
        # self.eject_fail = False
        self.isShieldConnected = "DISCONNECT"           #isShieldConnected
       
        self.selectedItemIndex=0                #selectedItemIndex
        # self.eject_fail_continuous=False
        self.currentBedTemp=0
        
        self.current_item = None
        self.totalEstimatedTime = 0
        self.currentQueue=None
        self.queuesIndex=0


 
    def on_startup(self, host, port):
          
        fileDir = os.path.join(self.ROOT_DIR,"queues.json")
        fileExist = os.path.exists(fileDir)
        if not fileExist:
            open(fileDir, 'w+')
        self.db = TinyDB(fileDir)
        return super().on_startup(host, port)

    
    def on_after_startup(self):  
     
        self.queues=self.db.all()
        self.settings = {}
        for val in self.settingsParams:
            self.settings[val] = self._settings.get([val])
            
            
  

        # self.sheild_control=SheildControl(self.buttonForward,self.buttonBackword,self.buttonSequence,self.motorPin1,self.motorPin2,self.switchBack,self.switchFront)
        # self.sheild_control.on_state_change = self.get_states
        
  
        search=Query()
        result = self.db.get(search.last=="last_queue")
        self.currentQueue=result
        print(self.currentQueue)
        self._logger.info("KİNG İS HEREEE (more: %s)" % self._settings.get(["url"]))
        self.message_to_js({'settings':self.settings,'currentIndex':self.currentIndex,'bedPosition':self.bedPosition,
                            'motorState':self.motorState,'isShieldConnected':self.isShieldConnected,
                            'queueState':self.queueState,'currentQueue':self.currentQueue,'itemState':self.itemState,})
     
        
        

    def on_event(self, event, payload):
        state = self._printer.get_state_id()
        if self.queueState == "STARTED" or self.queueState == "RUNNING":
            if state == "CANCELLING":
                self.current_item["state"] = "Cancelling"

            if state == "FINISHING":
                self.current_item["state"] = "ejecting"

            if state == "PAUSING":
                self.queueState = "PAUSING"
                self.message_to_js({'terminate':True})

    
            if event == "Disconnected" or event == "Error":
                if self.queueState != "IDLE":
                    self.queueState = "PAUSED"
                    self.current_item["state"] = "Failed"

            if event == "PrintStarted" or event == "PrintResumed":  
                if(self.queueState != "CANCELED" and self.queueState != "FINISHED"and self.queueState != "PAUSED"):
                    self.queueState = "RUNNING"
                self.current_item["state"] = "Printing"

            if event == "PrintPaused":
                self.queueState = "PAUSED"
                self.message_to_js({'terminate':False})

            if event == "DisplayLayerProgress_progressChanged":
                if self.current_item["state"] != "ejecting" and self.current_item["state"] != "Cancelling":

                    self.current_item["state"] = "Printing"


            if event == "PrintCancelling":
                if self.queueState != "CANCELED" and self.queueState != "IDLE":
                    self.queueState = "PAUSED"

                self.message_to_js({'terminate':True})

            if event == "PrintFailed" or event == "PrintCanceled":
                if self.queueState != "CANCEL" and self.queueState != "IDLE":
                    self.queueState = "PAUSED"
                self.queueState="CANCEL"
                
                self.message_to_js({ 'terminate':True,'itemResult':"Canceled"}) 
             

            if event == "PrinterStateChanged" and self.queueState != "PAUSED":
                state = self._printer.get_state_id()

            if event == "PrintDone":
                self.message_to_js({'sendItemIndex':True,'itemResult':"ejecting"})
                self.tryEject();
                
     
      
    def get_states(self,bed,motor,eject_faill):
        print("ahmet")
        
        # if eject_faill==True:
        #     self.current_item["state"] = "PAUSED"
        # self.bedPosition=bed
        # self.motorState=motor
        # self.eject_fail=eject_faill
        # self.message_to_js(dict(bedPosition=bed,motorState=motor,eject_fail=eject_faill))
          
         
    def tryEject(self):
        self.ejectState = "WAIT_FOR_Temp"
        
        self.heat=self.bedTemp
        if self.bedTemp<=45:
            self.Ejecting()
        else:
  
            wait_timer = Timer(1,self.checkBedTemp,args=None,kwargs=None)
            wait_timer.start()           
          
                
    def Ejecting(self):

        self.waitting_eject()
          
        
    def waitting_eject(self):
        
        if self.eject_fail ==False:
            self.control_eject=self.sheild_control.sequence_finish
            if(self.control_eject==True):
                    
                    
                self.message_to_js(
                        sendItemIndex=True, itemResult="Finished")
                self.eject_fail_continuous=False 
         
                print(self.queueState )
                self.current_item["state"] = "Finished"
                self.itemResult="Finished"  
                self.selectedItemIndex=self.selectedItemIndex+1
                self.message_to_js(
                    currentIndex=self.selectedItemIndex)
                        
                    
                if self.selectedItemIndex==self.currentQueue["items"].__len__():
                    self.queueState="FINISHED"
                    self.selectedItemIndex=0
                    self.message_to_js(currentIndex=-1)
                    self.do_item_state_await()
                    
            
            
        
                if self.queueState=="CANCELED" or self.queueState=="FINISHED":
                        self.message_to_js(
                        sendItemIndex=True, itemResult="Await",cansel_queue="yes",currentIndex=-1) 
                        self.queueState="IDLE"
                        self.do_item_state_await()
                        
                self.Next_item() 
            else:
                wait_timer2 = Timer(1,self.waitting_eject,args=None,kwargs=None)
                wait_timer2.start()
        else:
            self.Next_item()          
          
    def Next_item(self):
        print(self.queueState )
        if self.queueState == "RUNNING":
            print(self.control_eject)
            if(self.queueState == "RUNNING" and self.control_eject==True):
            
                self.eject_fail=True
                self.message_to_js(currentIndex=self.selectedItemIndex)
                self.startPrint()   
            else:
                print("print and queue finish") 
         
        else:
            print("queue and print finisheeed")
      
            
    def do_item_state_await(self) :
        for i in range(self.currentQueue["items"].__len__()):
            self.currentQueue["items"][i]["state"] = "Await"
        


    def startPrint(self, canceledIndex=None):
        if self.queueState == "RUNNING"or self.queueState=="STARTED":
            queue = self.currentQueue["items"]
            print(queue)
            print("ququueueueu")
            self.print_file = None
            
            if (self.queueState == "RUNNING" or self.queueState == "STARTED" or canceledIndex != None):
                self.print_file = None

                if canceledIndex != None:
        
                    self.currentQueue["items"][canceledIndex]["state"] = "Await"
                    self.print_file = self.currentQueue["items"][canceledIndex]
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
            print(self.currentIndex)
            print(queue[self.currentIndex])
            self.current_item=queue[self.currentIndex]  
            # if self.index !=None:
            #     self.selectedItemIndex=self.index    
            #     self.message_to_js(currentIndex=self.selectedItemIndex)
            #     self.index=None    
                
            # if self.selectedItemIndex!=self.currentQueue["items"].__len__():
            #     self.current_item=self.currentQueue["items"][self.selectedItemIndex]
            #     self.message_to_js(currentIndex=self.selectedItemIndex)
            
               
             
            #     self.current_item["state"]
            #     self.message_to_js(
            #         sendItemIndex=True, itemResult= self.current_item["state"])
            # else :
            #     self.selectedItemIndex=0
            #     self.message_to_js(finis_queue="yes")
            #     self.message_to_js(currentIndex=self.selectedItemIndex)
                 
                 
            self.print_file=self.current_item    
            self._printer.select_file(self.print_file["path"], is_from_sd)  
            self._printer.start_print()     
                 
    
    # def print_startted(self):
        # self.message_to_js(currentIndex=self.selectedItemIndex)
        # self.itemResult="print"    
      
    
    
    def get_settings_defaults(self):
        return dict(
            motorPin1=23,
            motorPin2=18,
            switchFront=4,
            switchBack=8,
            buttonForward=2,
            buttonBackword=6,
            buttonSequence=3,
            delaySeconds=10,
            targetBedTemp=40,
            error=False,
        )
    def on_settings_migrate(self, target, current):
        print("------settings ------ migrate -----")
        print(current)
        print(target)
        return
        return super().on_settings_migrate(target, current) 

    def on_settings_save(self, data):
        
        print("*************************")
        hasError = data.get('error',False)
        error=hasError
        if hasError is True:
            print("sıkıntı var")
        print(data.get('error',False))
        
        
        # data.remove('error')
        # Data içinden error'u sildir öyle gönder süpere
        return super().on_settings_save(data)
        return
        pins=[self._settings.get(["motorPin1"]),self._settings.get(["motorPin2"]),self._settings.get(["switchFront"]),self._settings.get(["switchBack"]),
              self._settings.get(["buttonForward"]),self._settings.get(["buttonBackword"]),self._settings.get(["buttonSequence"])]
        pins1=[]
        pins2=[]

        for deger in pins:
            if deger not in pins1:
                pins1.append(deger)
            else:
                pins2.append(deger)
        
        print(pins)
        print(pins2)      
        
        if len(pins2)!=0:
            self._settings.set(["check"],"true")
            check="true"
            print("degerler aynı")
        else:
             self._settings.set(["check"],"false")
        
        
        
        self.targetBedTemp = self._settings.get(["targetBedTemp"])
        self.motorPin1=self._settings.get(["motorPin1"])
        self.motorPin2=self._settings.get(["motorPin2"])
        self.switchFront=self._settings.get(["switchFront"]) 
        self.switchBack=self._settings.get(["switchBack"])
        self.buttonForward=self._settings.get(["buttonForward"])
        self.buttonBackword=self._settings.get(["buttonBackword"])
        self.buttonSequence=self._settings.get(["buttonSequence"])
        self.min_Task=self._settings.get(["minTaskTemp"])
        self.delaySeconds=self._settings.get(["delaySeconds"])
        
        

        
    
    
        self.message_to_js(targetTemp=self.targetBedTemp)
        self.message_to_js(motorPin1=self.motorPin1)
        self.message_to_js(motorPin2=self.motorPin2)
        self.message_to_js(switchFront=self.switchFront)
        self.message_to_js(switchBack=self.switchBack)
        self.message_to_js(buttonForward=self.buttonForward)
        self.message_to_js(buttonBackword=self.buttonBackword)
        self.message_to_js(buttonSequence=self.buttonSequence)
        self.message_to_js(minTaskTemp=self.min_Task)
        self.message_to_js(maxQueues=self.queues_max)
        self.message_to_js(delaySeconds=self.delaySeconds)
        
        
        return super().on_settings_save(data)

    def message_to_js(self,message):
        self._plugin_manager.send_plugin_message(self._identifier, message)          
       
    
            
            
                                                                                                                    

        
    

    def get_template_configs(self): 
        return [
            dict(type="settings", custom_bindings=False),
            dict(type="tab", custom_bindings=False)
        ]




        # ~~ Softwareupdate hook

    
    
    @ octoprint.plugin.BlueprintPlugin.route("/check_pin", methods=["GET"])
    @ restricted_access
    def check_pin(self):

        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/saveToDataBase", methods=["POST"])
    @ restricted_access
    def saveToDataBase(self):
   
        data = flask.request.get_json()
        Exist = Query()
        print(data["index"])
        print("------------------------------------------------------index---------------")
       
        queue_id = data["id"]
        name = data["queueName"]  if data["queueName"]  != "" or data["queueName"]  != None else "New Queue"
        items = self.currentQueue["items"] if self.currentQueue["items"] !=None else []
        selectedQueue=data["index"]
        self.queues[selectedQueue]["name"]=name
    
    
        inDb = self.db.search(Exist.id == queue_id)
        item = Query()
        last_db=self.db.search(item.last == "last_queue")
        
        
        if(len(last_db) > 1 and last_db != None):
            self.db.update({
                'last':"none"
            },item.last == "last_queue")   
  
            
        if(len(inDb) > 0 and inDb != None):
            self.db.update({
                'items': items,
                'name':name,
                'updateTime':str(datetime.datetime.now()),
                'last':"last_queue"
            },Exist.id==queue_id)
        else:
            self.db.insert({
                    'items': items,
                    'id': queue_id,
                    'updateTime':str(datetime.datetime.now()),
                    'createTime':str(datetime.datetime.now()),
                    'name': name,
                    'last':"last_queue",
                })
            
            
              

   
            

        # self._settings.set(["speroplugin_currentQueue"], json.dumps(self.currentQueue))
        # self._settings.save()

        
        res = jsonify(success=True)
        res.status_code = 200
        return res



    def get_template_vars(self):
        return dict(url=self._settings.get(["url"]))
    
    @ octoprint.plugin.BlueprintPlugin.route("/send_time_data", methods=["POST"])
    @ restricted_access
    def send_time_data(self):
        data = flask.request.get_json()

        if data["timeLeft"]!=None and data["index"]!=None:
            self.currentQueue["items"][data["index"]]["timeLeft"] = data["timeLeft"]

        if self.totalEstimatedTime != None:
            self.totalEstimatedTime = data["totalEstimatedTime"]
        else:
            self.totalEstimatedTime = 0

        res = jsonify(success=True, data="time done")
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/deviceControl")
    @ restricted_access
    def deviceControl(self):
        data = flask.request.get_json()  
        # if (data["request"]):
            # self.sheild_control.send_actions(data["request"])

            
        res = jsonify(success=True)
        res.status_code = 200
        return res    

                
    
    @ octoprint.plugin.BlueprintPlugin.route("/deleteFromDatabase", methods=["DELETE"])
    @ restricted_access
    
    def delete_from_database(self):
        
        queue_id = flask.request.args.get("id")
        
        self.currentQueue = None

        Exist = Query()

        self.db.remove(Exist.id == queue_id)
        self.db.close()

        self._settings.remove(["speroplugin_currentQueue"])

 

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/sayhello",)
    @ restricted_access
    
    def sayhello(self):



        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    octoprint.plugin.BlueprintPlugin.route("/queue_item_up", methods=["GET"])
    @ restricted_access
    def queue_item_up(self):
        index = int(flask.request.args.get("index", 0))

        if len(self.currentQueue["items"]) > 1:

            itemCurr = self.currentQueue["items"][index]
            itemCurr["index"] = index - 1
            itemNext = self.currentQueue["items"][index - 1]
            itemNext["index"] = index

            self.currentQueue["items"][index] = itemNext
            self.currentQueue["items"][index - 1] = itemCurr


        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/pauseResumeQueue", methods=["GET"])
    @ restricted_access
    def pauseResumeQueue(self):
        if self.queueState=="FINISHED":
            self.selectedItemIndex=-1
    
        if self.queueState=="CANCELED":
            self.Next_item()
     
        if self.eject_fail==True:
            print("eject fail")
            self.control_eject=True
            self.eject_fail=False
            self.queueState="RUNNING"
            self.Next_item()
          
        else:
            self.queueState="RUNNING"
            self.Next_item()
        

        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/cancelQueue", methods=["GET"])
    @ restricted_access
    def cancel_queue(self):

        self.queueState="CANCELED"
        self.selectedItemIndex=-1  
     

        
        self.Next_item()
        
        


        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/pauseStopQueue", methods=["GET"])
    @ restricted_access
    def pauseStopQueue(self):
        self.queueState= "PAUSED"
        self.Next_item()
        

        res = jsonify(success=True)
        res.status_code = 200
        return res
    

    
    @ octoprint.plugin.BlueprintPlugin.route("/startQueue", methods=["GET"])
    @ restricted_access
    def startQueue(self):
        print("startttttttttttttt")
        self.queueState = "STARTED"
        totalTime = flask.request.args.get("totalEstimatedTime", 0)
        self.totalEstimatedTime = totalTime

        if len(self.currentQueue["items"]) > 0:
            print("start")
            self.startPrint()

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    # get data for js
    @ octoprint.plugin.BlueprintPlugin.route("/sendStartDatas", methods=["GET"])
    @ restricted_access
    def sendStartDatas(self):
        message ={}
        for val in self.requiredDatas:
            message[val]=getattr(self,val)
        self.message_to_js(message)
        self.message_to_js({'queues':self.queues})
        print(self.queues)
            
        # targetBedTemp = self._settings.get(["targetBedTemp"])
        # print(self.currentQueue)
        # print("------------------------------------queqe------------------------")
        # self.message_to_js()
        # queue = json.dumps(dict(queue=self.currentQueue,
        #                         totalEstimatedTime=self.totalEstimatedTime,
        #                         queues=self.queues,
        #                         queueState=self.queueState,
        #                         selectedItemIndex=self.selectedItemIndex,
        #                         current_files=self.currentFiles,
        #                         esp=self.esp,
        #                         bedPosition=self.bedPosition,
        #                         eject_fail=self.eject_fail,
        #                         motorState=self.motorState,
        #                         ejecting=self.ejecting,
        #                         connection=self.connection,
                                
        #                         ))
        return message
    
   
   
    @ octoprint.plugin.BlueprintPlugin.route("/get_datas", methods=["GET"])
    @ restricted_access
    def get_datas(self):

        self.queues.append(self.currentQueue)

        self.current_item = None
        self.currentTime = 0
        self.totalEstimatedTime = 0

        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/createQueue", methods=["GET"])
    @ restricted_access
    def createQueue(self):
        print("queue created")
        self.currentQueue = dict(
            id=str(uuid.uuid4()),
            name="New Queue",
            items= [],
            index=self.queuesIndex
        )
        
        self.queuesIndex=self.queuesIndex+1
        print(self.currentQueue["name"])
        print(self.currentQueue["id"])
        self.queuesIndex
        
    
        self.queues.append(self.currentQueue)
    

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

        if len(self.currentQueue["items"]) > 1:
            itemCurr = self.currentQueue["items"][index]
            itemCurr["index"] = index + 1

            itemNext = self.currentQueue["items"][index+1]
            itemNext["index"] = index

            self.currentQueue["items"][index] = itemNext
            self.currentQueue["items"][index + 1] = itemCurr


        res = jsonify(success=True)
        res.status_code = 200
        return res

    # QUEUE UP-DOWN END

    @ octoprint.plugin.BlueprintPlugin.route("/queue_add_item", methods=["POST"])
    @ restricted_access
    def queue_add_item(self):
   
        queue = self.currentQueue["items"]

        
        data = flask.request.get_json()
        print(data)
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
        res = jsonify(success=True, data="")
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
        queue = self.currentQueue["items"]
        queue.pop(index)

        for i in queue:
            if i["index"] > index:
                i["index"] -= 1

        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/queueItemDuplicate", methods=["GET"])
    @ restricted_access
    def queueItemDuplicate(self):
        print("aojuhsdhaıuosgpaıosubd")
        index = int(flask.request.args.get("index", 0))
        queue = copy.deepcopy(self.currentQueue["items"])

        item = queue[index]
        item["index"] += 1

        for i in self.currentQueue["items"]:
            if i["index"] > index:
                i["index"] += 1

        self.currentQueue["items"].insert(item["index"], item)

        res = jsonify(success=True)
        res.status_code = 200
        return res

   
    @ octoprint.plugin.BlueprintPlugin.route("/getQueue", methods=["GET"])
    @ restricted_access
    def getQueue(self):
        queue_id = flask.request.args.get("id")

        for queue in self.queues:
            if queue["id"] == queue_id:
                self.currentQueue = queue
                break
  
        
        res = jsonify(success=True)
        res.status_code = 200
        return res

        


    def get_assets(self):
        return {
            "js": ["js/speroplugin.js"],
            "css": ["css/speroplugin.css"],
            "less": ["less/speroplugin.less"]
        }







    def get_update_information(self):
      
        return {
            "speroplugin": {
                "displayName": "speroplugin Plugin",
                "displayVersion": self._plugin_version,

           
                "type": "github_release",
                "user": "you",
                "repo": "OctoPrint-speroplugin",
                "current": self._plugin_version,

           
                "pip": "https://github.com/you/OctoPrint-speroplugin/archive/{target_version}.zip",
            }
        }


    def sanitize_temperatures(self,comm_instance, parsed_temperatures, *args, **kwargs):
        x = parsed_temperatures.get('B')
        if x:
            currentBedTemp = x[0]
            if self.ejectState == "WAIT_FOR_TEMP":
                self.checkBedTemp(currentBedTemp)
            
        return parsed_temperatures
    
    def checkBedTemp(self,currentBedTemp):
        
        if(currentBedTemp<=self.settings.get(["targetBedTemp"])):
            self.startEject() # state -> Ejecting, 
            self.message_to_js({'temp':currentBedTemp})
       
            
 




__plugin_name__ = "speroplugin Plugin"

__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Speroplugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.temperatures.received": (__plugin_implementation__.sanitize_temperatures,1)
    }