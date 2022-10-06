# coding=utf-8
from __future__ import absolute_import
from threading import Timer

from flask.globals import request
from octoprint.plugin.types import SettingsPlugin
from octoprint.settings import settings
from octoprint_speroplugin.PluginEnums import QueueState
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

    settingsParams = ["targetBedTemp","motorPin1","motorPin2","switchFront","switchBack","buttonForward","buttonBackword","buttonSequence","delaySeconds"]
    
    requiredDatas = ["queues","currentQueue","settings"]

    def __init__(self):
        self.queues = []
        self.queue_state = QueueState.IDLE  # queueState
        self.print_bed_state="Idle"         # bedPosition -> middle front back
        self.motor_state="Idle"             # motorState -> idle forward backward
        # self.ejecting= False
        # self.eject_fail = False
        self.connection = "False"           #isShieldConnected
       
        self.current_index=0                #selectedItemIndex
        # self.eject_fail_continuous=False
        self.control_eject=False
        self.last_queue=None
        self.current_item = None
        self.sheiled_state="sa"
        self.total_estimated_time = -1
        self.queues_max=0


   



    def on_startup(self, host, port):
        fileDir = os.path.join(self.ROOT_DIR,"queues.json")
        fileExist = os.path.exists(fileDir)
        if not fileExist:
            open(fileDir, 'w+')
        self.db = TinyDB(fileDir)
        return super().on_startup(host, port)

    
    def on_after_startup(self):
        self.settings = {}
        for val in self.settingsParams:
            self.settings[val] = self._settings.get([val])
        print("--------settings--------")
        print(self.settings)
    
        # self.sheild_control=SheildControl(self.buttonForward,self.buttonBackword,self.buttonSequence,self.motorPin1,self.motorPin2,self.switchBack,self.switchFront)
        # self.sheild_control.on_state_change = self.get_states
        
  
        search=Query()
        result = self.db.get(search.last=="last_queue")
        self.current_queue=result
        self._logger.info("KİNG İS HEREEE (more: %s)" % self._settings.get(["url"]))
        self.message_to_js({'settings':self.settings,'index_current':0})
        

    def on_event(self, event, payload):
        state = self._printer.get_state_id()
        if self.queue_state == "STARTED" or self.queue_state == "RUNNING":
            if state == "CANCELLING":
                self.current_item["state"] = "Cancelling"

            if state == "FINISHING":
                self.current_item["state"] = "ejecting"

            if state == "PAUSING":
                self.queue_state = "PAUSING"
                self.message_to_js({'terminate':True})

    
            if event == "Disconnected" or event == "Error":
                if self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"
                    self.current_item["state"] = "Failed"

            if event == "PrintStarted" or event == "PrintResumed":  
                if(self.queue_state != "CANCELED" and self.queue_state != "FINISHED"and self.queue_state != "PAUSED"):
                    self.queue_state = "RUNNING"
                self.current_item["state"] = "Printing"

            if event == "PrintPaused":
                self.queue_state = "PAUSED"
                self.message_to_js({'terminate':False})

            if event == "DisplayLayerProgress_progressChanged":
                if self.current_item["state"] != "ejecting" and self.current_item["state"] != "Cancelling":

                    self.current_item["state"] = "Printing"


            if event == "PrintCancelling":
                if self.queue_state != "CANCELED" and self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"

                self.message_to_js({'terminate':True})

            if event == "PrintFailed" or event == "PrintCanceled":
                if self.queue_state != "CANCEL" and self.queue_state != "IDLE":
                    self.queue_state = "PAUSED"
                self.queue_state="CANCEL"
                
                self.message_to_js({ 'terminate':True,'itemResult':"Canceled"}) 
             

            if event == "PrinterStateChanged" and self.queue_state != "PAUSED":
                state = self._printer.get_state_id()

            if event == "PrintDone":
                self.message_to_js({'sendItemIndex':True,'itemResult':"ejecting"})
                self.tryEject();
                
     
      
    def get_states(self,bed,motor,eject_faill):
        if eject_faill==True:
            self.current_item["state"] = "PAUSED"
        self.print_bed_state=bed
        self.motor_state=motor
        self.eject_fail=eject_faill
        self.message_to_js(dict(print_bed_state=bed,motor_state=motor,eject_fail=eject_faill))
          
         
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
         
                print(self.queue_state )
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
                wait_timer2 = Timer(1,self.waitting_eject,args=None,kwargs=None)
                wait_timer2.start()
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
     
        queues = self.db.all()
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
                 
           
                 
                 
    
    def print_startted(self):
        self.message_to_js(index_current=self.current_index)
        self.itemResult="print"    
        self._printer.start_print()
    
    
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

    @ octoprint.plugin.BlueprintPlugin.route("/queue_item_restart", methods=["GET"])
    @ restricted_access
    def queue_item_restart(self):
        index = int(flask.request.args.get("index", 0))

        self.start_print(canceledIndex=index)

        self.queue_state = "RUNNING"

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/check_pin", methods=["GET"])
    @ restricted_access
    def check_pin(self):
        print("saasa")

        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/save_to_database", methods=["POST"])
    @ restricted_access
    def save_to_database(self):
        
        data = flask.request.get_json()
        Exist = Query()


        queue_id = data["id"]
        name = data["queue_name"]  if data["queue_name"]  != "" or data["queue_name"]  != None else "New Queue"
        items = self.current_queue["items"] if self.current_queue["items"] !=None else []
            
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
            
            
              
  
            

        self._settings.set(["speroplugin_current_queue"], json.dumps(self.current_queue))
        self._settings.save()

        self.get_from_database()

        self.db.close()

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
            self.current_queue["items"][data["index"]]["timeLeft"] = data["timeLeft"]

        if self.total_estimated_time != None:
            self.total_estimated_time = data["total_estimated_time"]
        else:
            self.total_estimated_time = 0

        res = jsonify(success=True, data="time done")
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/device_controll")
    @ restricted_access
    def device_controll(self):
        data = flask.request.get_json()  
        # if (data["request"]):
            # self.sheild_control.send_actions(data["request"])

            
        res = jsonify(success=True)
        res.status_code = 200
        return res    
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/check_button")
    @ restricted_access
    def check_button(self):
            print("jaaaa")

            
            res = jsonify(success=True)
            res.status_code = 200
            return res    
                
    
    @ octoprint.plugin.BlueprintPlugin.route("/delete_from_database", methods=["DELETE"])
    @ restricted_access
    
    def delete_from_database(self):
        
        queue_id = flask.request.args.get("id")
        
        self.current_queue = None

        Exist = Query()

        self.db.remove(Exist.id == queue_id)
        self.db.close()

        self._settings.remove(["speroplugin_current_queue"])

        self.get_from_database()

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    
    @ octoprint.plugin.BlueprintPlugin.route("/sayhello",)
    @ restricted_access
    
    def sayhello(self):
        print("saas")

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
        

        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/cancel_queue", methods=["GET"])
    @ restricted_access
    def cancel_queue(self):

        self.queue_state="CANCELED"
        self.current_index=-1  
     

        
        self.Next_item()
        
        


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

        totalTime = flask.request.args.get("total_estimated_time", 0)
        self.total_estimated_time = totalTime

        if len(self.current_queue["items"]) > 0:
            self.start_print()

        res = jsonify(success=True)
        res.status_code = 200
        return res
    
    # get data for js
    @ octoprint.plugin.BlueprintPlugin.route("/get_current_states", methods=["GET"])
    @ restricted_access
    def get_current_states(self):
        message ={}
        for val in self.requiredDatas:
            message[val]=getattr(self,val)
        self.message_to_js(message)
            
        # targetBedTemp = self._settings.get(["targetBedTemp"])
        # print(self.current_queue)
        # print("------------------------------------queqe------------------------")
        # self.message_to_js()
        # queue = json.dumps(dict(queue=self.current_queue,
        #                         total_estimated_time=self.total_estimated_time,
        #                         queues=self.queues,
        #                         queue_state=self.queue_state,
        #                         current_index=self.current_index,
        #                         current_files=self.currentFiles,
        #                         esp=self.esp,
        #                         print_bed_state=self.print_bed_state,
        #                         eject_fail=self.eject_fail,
        #                         motor_state=self.motor_state,
        #                         ejecting=self.ejecting,
        #                         connection=self.connection,
                                
        #                         ))
        return 
    
   
   
    @ octoprint.plugin.BlueprintPlugin.route("/get_datas", methods=["GET"])
    @ restricted_access
    def get_datas(self):
     

        self.queues.append(self.current_queue)

        self.current_item = None
        self.currentTime = 0
        self.total_estimated_time = 0

        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/create_queue", methods=["GET"])
    @ restricted_access
    def create_queue(self):
        self.last_queue="New Queue"
        self.current_queue = dict(
            id=str(uuid.uuid4()),
            name="New Queue",
            items= [],
        )
        self.last_queue="none"
        
    
        self.queues.append(self.current_queue)

        self.current_item = None
        self.currentTime = 0
        self.total_estimated_time = 0

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