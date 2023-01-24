# coding=utf-8
from __future__ import absolute_import
import asyncio
from threading import Timer
from octoprint.plugin.types import SettingsPlugin
from octoprint.settings import settings
from octoprint_speroplugin.PluginEnums import BedPosition, EjectState, ItemState, MotorState, QueueState
from tinydb.database import TinyDB
from tinydb.queries import Query
import copy
from octoprint.filemanager.storage import StorageInterface as storage

from .SerialPorts import SerialPorts
import os
import flask
import uuid
import datetime
import requests
from flask import jsonify




from octoprint.server.util.flask import (
    restricted_access,
)

import octoprint.plugin
import asyncio







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


    settingsParams = ["motorPin1","motorPin2","switchFront","switchBack","buttonForward","buttonBackword","buttonSequence","targetBedTemp","delaySeconds"]
    # sheildControl=None

    requiredDatas = ["settings2","currentIndex","bedPosition",'motorState','isShieldConnected','queueState','currentQueue',
                    'itemState',"queuesIndex"    ]



    def __init__(self):
        self.q = asyncio.Queue()
        self.queues = []
        self.ports=[]
        self.portsIsChanged=[]
        print("/////////////////////////")
        
        self.queueState = QueueState.IDLE.value  # queueState
        print(self.queueState)
        self.bedPosition=BedPosition.MIDDLE.value   # bedPosition -> middle front back
        self.motorState=MotorState.IDLE.value            # motorState -> idle forward backward
        self.ejectState=EjectState.IDLE.value               #eject durumları
        self.itemState=ItemState.AWAIT               #item durumları
        self.currentIndex=0                           #queuenin o anki indexsi
        self.isShieldConnected = "Disconnet"           #isShieldConnected
        self.currentQueue=None                          #su anki queue
        self.currentQueueItem = None                    #secilen veya en son kalan queue nin item dizisi
        self.totalEstimatedTime = 0                     #priniting olan itemin basım zamanı
        print(self.itemState)
        self.queuesIndex=0   #queueların index numarası queuelara index numarası verdim başlangıcta
                            #en son kalanı ekrana vermek için

        self.change=None    #cancelling yaparken state değişikliğini tetikletmek için
        self.settings2=[]
        self.selectedPortName=None
        self.dbQueue=None
        self.savedPort=None
        self.firstPorts=None
        self.serialConnection=None
        self.results=None
        self.queueName="New Queue"
        self.targetBedTemp=None
        self.repeat="off"



    def on_startup(self, host, port):


        fileDir = os.path.join(self.ROOT_DIR,"queues.json")
        fileExist = os.path.exists(fileDir)
        if not fileExist:
            open(fileDir, 'w+')

        self.dbQueue = TinyDB(fileDir)

        fileDir2 = os.path.join(self.ROOT_DIR,"ports.json")
        fileExist = os.path.exists(fileDir2)
        self.dbPorts = TinyDB(fileDir2)
        if not fileExist:
            open(fileDir, 'w+')






        return super().on_startup(host, port)






    def on_after_startup(self):



        self.targetBedTemp=self._settings.get(["targetBedTemp"])
        self.messageToJs({'targetBedTemp':self.targetBedTemp})
        self.queues=self.dbQueue.all()



        self.setSettings()
        self.queueSettings()
        self.messageToJs({'queueState':self.queueState})
        print("****************")


        self.messageToJs({'settings':self.settings2,'currentIndex':self.currentIndex,'bedPosition':self.bedPosition,
                            'motorState':self.motorState,
                            'queueState':self.queueState,'currentQueue':self.currentQueue,'itemState':self.itemState,})



        self.selectedListId()



    def selectedListId(self):

        self.serial = SerialPorts()
        self.ports = self.serial.serialPorts()
        self.serial.onStateChange = self.getStates

        searchPort=Query()

        self.results=self.dbPorts.get(searchPort.findId=="find")

        if self.results!=None:
            self.serial.selectedPortId(self.results["serialId"])
        else:
            self.serial.portList()




    def setSettings(self):                         #settings jinjadan verileri çeken fonks
        self.settings2 = {}
        for val in self.settingsParams:
            self.settings2[val] = self._settings.get([val])




    def queueSettings(self):
        if len(self.dbQueue.all())==0:
            self.currentQueue = dict(
                id=str(uuid.uuid4()),
                name="New Queue",
                items= [],
                index=self.queuesIndex,
                last="last_queue"
        )

            self.dbQueue.insert(self.currentQueue)
            self.currentItems=self.currentQueue["items"]
            self.messageToJs({'queuesIndex':self.queuesIndex})


            self.queues.append(self.currentQueue)

            self.currentTime = 0
            self.totalEstimatedTime = 0


            self.messageToJs({'currentQueue':self.currentQueue})
            self.messageToJs({'currentItems':self.currentItems})



        else:

            self.queuesIndex=len(self.dbQueue.all())-1

            search=Query()
            self.currentQueue=self.dbQueue.get(search.last=="last_queue")

            if self.currentQueue!=None:
                self.messageToJs({'currentQueue':self.currentQueue})



    def on_event(self, event, payload):



        self.messageToJs({'ports':self.ports})

        state = self._printer.get_state_id()


        if state == "CANCELLING":
            self.itemState=ItemState.CANCELLING.value
            self.messageToJs({'itemState':self.itemState})


        if event == "Disconnected" or event == "Error":
            self.queueState = QueueState.PAUSED.value
            self.itemState=ItemState.FAILED.value

        if event == "PrintStarted" or event == "PrintResumed":
            self.queueState = QueueState.RUNNING.value
            self.itemState=ItemState.PRINTING.value
            self.messageToJs({'itemState':self.itemState})
            self.serial.state="printing"
            self.currentQueue["items"][self.currentIndex]["state"]=self.itemState
            self.updateItemState(self.currentQueue["id"],self.itemState)


        if event == "PrintPaused":
            self.queueState = QueueState.PAUSED.value
            self.itemState=ItemState.PAUSED.value

        if event == "DisplayLayerProgress_progressChanged":
            if self.itemState != "Ejecting" and self.itemState != "Cancelled":
                self.itemState=ItemState.PRINTING.value


        if event == "PrintFailed" or event == "PrintCanceled":
            self.change="yes" #anlık kontrol ettiği için kullanıcı state değişmeden tetikleyebilir bu yüzden kontrol
            #amaçlı yazdım.



        if event == "PrinterStateChanged" and self.queueState != "Paused":
            if self.change=="yes":

                self.itemState=ItemState.FAILED.value
                self.queueState = QueueState.CANCELLED.value
                self.messageToJs({'itemState':self.itemState,"QueueState":self.queueState})
                self.change="no"

            state = self._printer.get_state_id()

        if event == "PrintDone":
            self.ejectState=EjectState.WAIT_FOR_TEMP.value
            if self._printer:
                self._printer.jog({"z":60})
                self._printer.jog({"y":235},relative=False)
     

            # if self.device=="Reloder":
            #     if self._printer:
            #         self._printer.jog({"z":60})
            #         self._printer.jog({"y":235},relative=False)
            # elif self.device=="Reloder Pro":
            #     if self._printer:
            #         self._printer.jog({"z":60})
            #         self._printer.jog({"y":0},relative=False)
            self.itemState=ItemState.EJECTING.value
            self.currentQueue["items"][self.currentIndex]["state"]=self.itemState
            self.updateItemState(self.currentQueue["id"],self.itemState)
            self.tryEject()

        self.messageToJs({'itemState': self.itemState,'queueState':self.queueState})



    def getStates(self,connetion,bed,motor,ports):           #raspi baglı durumlar için bu yüzden şuan yorum satırında
        if connetion==True:
            self.isShieldConnected="Connected"
        if connetion==False:
            self.isShieldConnected="Disconnected"

        self.bedPosition=bed
        self.motorState=motor
        self.ports=ports

        self.messageToJs({"isShieldConnected":self.isShieldConnected,'bedPosition':self.bedPosition,'motorState':self.motorState,'ports':self.ports})



    def tryEject(self):                                 #eject için uygun sıcaklıgı saplamak için
        self.ejectState = EjectState.WAIT_FOR_TEMP.value

    def startEject(self):
        self.serial.sendActions("eject")
        self.ejectState=EjectState.EJECTING.value
        self.waitingEject()



    def waitingEject(self):
        if self.ejectState =="EjectingFinished":

            self.itemState=ItemState.FINISHED.value
            self.currentQueue["items"][self.currentIndex]["state"]=self.itemState
            self.updateItemState(self.currentQueue["id"],self.itemState)
            if self.queueState=='Running':
                self.currentIndex=self.currentIndex+1

            self.messageToJs({'itemState':self.itemState,'currentIndex':self.currentIndex})


            if(self.queueState=="Cancelled"):
                self.currentIndex=0
                self.messageToJs({'currentIndex':self.currentIndex} )
                self.doItemsStateAwait()

            if self.currentIndex==self.currentQueue["items"].__len__():
                self.queueState="FINISHED"

                self.currentIndex=0
                self.messageToJs({'itemState':self.itemState,'currentIndex':self.currentIndex})
                self.doItemsStateAwait()


            self.nextItem()
        else:

            if self.serial.state=="Idle":
                self.itemState=ItemState.FINISHED.value
                self.currentQueue["items"][self.currentIndex]["state"]=self.itemState
                self.updateItemState(self.currentQueue["id"],self.itemState)
                self.ejectState=EjectState.EJECTING_FINISHED.value
                self.messageToJs({'itemState':self.itemState})

            if self.serial.state=="EjectFail":
                self.itemState="EjectFaild"

                self.queueState=QueueState.PAUSED.value
                self.messageToJs({'itemState':self.itemState,"queueState":self.queueState})


            waitTimer2 = Timer(1,self.waitingEject,args=None,kwargs=None)
            waitTimer2.start()

    def nextItem(self):            #eject biitikten sonra queuenin statine göre bir sonraki işlem
        if self.queueState == "Running":

            if(self.queueState == "Running" and self.ejectState!="EjectFail"):
                self.messageToJs({'currentIndex':self.currentIndex})
                self.startPrint()
            else:
                print("print andd queue finish")
        else:
            print("queue and print finisheeed")


    def doItemsStateAwait(self) :   #queuenin bittigi ya da cancel olduğu durumlarda queuenin butun itemlerini Awaitte cekmek için

            for x in range(len(self.currentQueue["items"])):
               self.currentQueue["items"][x]["state"]="Await"
            self.updateItemState(self.currentQueue["id"],self.itemState)
            self.updateLastQueue(self.currentQueue["id"])




            self.queueState=QueueState.IDLE.value
            self.messageToJs({'queueState':self.queueState})


    def startPrint(self, canceledIndex=None):



        if self.queueState == "Running"or self.queueState=="Started":
            queue = self.currentQueue["items"]
            self.print_file = None

            if (self.queueState == "Running" or self.queueState == "Started" or canceledIndex != None):
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

            self.print_file=queue[self.currentIndex]
            self._printer.select_file(self.print_file["path"], is_from_sd)
            self._printer.start_print()


    def get_settings_defaults(self):
        return dict(
            status=6,
            targetBedTemp=40,
            device="Reloder"

      )



    def on_settings_save(self, data):

        if "targetBedTemp" in data and data["targetBedTemp"]!=None:
            self.targetBedTemp=data["targetBedTemp"]

        self.messageToJs({'targetBedTemp':self.targetBedTemp})


        return super().on_settings_save(data)


    def messageToJs(self,message):
        self._plugin_manager.send_plugin_message(self._identifier, message)



    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False),
            dict(type="tab", custom_bindings=False)
        ]

        # ~~ Softwareupdate hook

    @ octoprint.plugin.BlueprintPlugin.route("/saveToDataBase", methods=["POST"])
    @ restricted_access
    def saveToDataBase(self):
        data = flask.request.get_json()
        Exist = Query()
        queueId = data["id"]
        name = data["queueName"]  if data["queueName"]  != "" or data["queueName"]  != None else "New Queue"
        items = self.currentQueue["items"] if self.currentQueue["items"] !=None else []
  
        index=(data["index"])
        self.queues[index]["name"]=name
                                                        #queueyi yaratırken bir index numarasu atadım burdada last queue kelimesini atıyorum sadece
                                                        #birine digerlerinde none on startup tada last_queue yazısının indexsini bulup selected queue yapıyp

        inDb = self.dbQueue.search(Exist.id == queueId)
        item = Query()
        last_db=self.dbQueue.search(item.last == "last_queue")


        # if(len(last_db) > 1 and last_db != None):
        #     self.dbQueue.update({
        #         'last':"none"
        #     },item.last == "last_queue")


        if(len(inDb) > 0 and inDb != None):
            self.dbQueue.update({
                'items': items,
                'name':name,
                'updateTime':str(datetime.datetime.now()),
                'last':"none"
            },Exist.id==queueId)
        else:
            self.dbQueue.insert({
                    'items': items,
                    'id': queueId,
                    'updateTime':str(datetime.datetime.now()),
                    'createTime':str(datetime.datetime.now()),
                    'name': name,
                    'index':index,
                    'last':"none",
                })




        self.messageToJs({'queues':self.queues})
        self.messageToJs({'queues':self.queues})



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
            self.updateItemState(self.currentQueue["id"],self.itemState)

        if self.totalEstimatedTime != None:
            self.totalEstimatedTime = data["totalEstimatedTime"]
        else:
            self.totalEstimatedTime = 0

        res = jsonify(success=True, data="time done")
        res.status_code = 200
        return res




    @ octoprint.plugin.BlueprintPlugin.route("/selectedPort", methods=["POST"])
    @ restricted_access
    def selectedPort(self):

        data = flask.request.get_json()
        searchPort=Query()
        last_db=self.dbQueue.search(searchPort.items == "find")


        if(len(last_db) > 1 and last_db != None):
            self.dbQueue.update({
                'find':"none"
            },searchPort.items == "last_queue")


        data2=data["request"]["serial"]
        self.dbPorts.insert({
            'serialId': data2,
            'findId': "find",
        })

        self.serial.selectedPortId(data["request"]["serial"])
        self.selectedListId()
        self.deviceControl()





        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/repeatOnOff", methods=["POST"])
    @ restricted_access
    def repeatOnOff(self):
        
        data = flask.request.get_json()
  
        self.repeat=data["request"]
        print( self.repeat)
          

        res = jsonify(success=True)
        res.status_code = 200
        return res









    @ octoprint.plugin.BlueprintPlugin.route("/deviceControl", methods=["POST"])
    @ restricted_access
    def deviceControl(self):
        data = flask.request.get_json()
        if (data["request"]):
            self.serial.sendActions(data["request"])

        res = jsonify(success=True)
        res.status_code = 200
        return res







    @ octoprint.plugin.BlueprintPlugin.route("/deleteFromDatabase", methods=["DELETE"])
    @ restricted_access

    def deleteFromDatabase(self):

        queueId = flask.request.args.get("id")

        self.currentQueue = None
        self.currentQueueItem=None


        Exist = Query()
        result = self.dbQueue.get(Exist.id==queueId)
        if result!=None:
            self.queues = list(filter(lambda x: x['id'] != queueId, self.queues))

            self.dbQueue.remove(Exist.id == queueId)
        if self.queues==0:
            self.queuesIndex=0
        else :
         self.queuesIndex=len(self.queues)-1


        self.messageToJs({'queues':self.queues})
        res = jsonify(success=True)
        res.status_code = 200
        return res



    octoprint.plugin.BlueprintPlugin.route("/queueItemUp", methods=["GET"])
    @ restricted_access
    def queueItemUp(self):
        index = int(flask.request.args.get("index", 0))

        if len(self.currentQueue["items"]) > 1:

            itemCurr = self.currentQueue["items"][index]
            itemCurr["index"] = index - 1
            itemNext = self.currentQueue["items"][index - 1]
            itemNext["index"] = index
            self.updateItemState(self.currentQueue["id"],self.itemState)
            self.currentQueue["items"][index] = itemNext
            self.currentQueue["items"][index - 1] = itemCurr


        res = jsonify(success=True)
        res.status_code = 200
        return res


    @ octoprint.plugin.BlueprintPlugin.route("/pauseResumeQueue", methods=["GET"])
    @ restricted_access
    def pauseResumeQueue(self):
        self.setSettings()


        if self.queueState=="FINISHED":
            self.currentIndex=-1

        if self.queueState=="Cancelled" and self.itemState!="Failed":


            self.currentIndex=-1
            self.messageToJs({'currentIndex':self.currentIndex})
            self.nextItem()

        if self.itemState=="EjectFaild":

            self.currentIndex=self.currentIndex+1
            self.queueState=QueueState.RUNNING.value
            self.itemState=ItemState.PRINTING.value
            self.currentQueue["items"][self.currentIndex]["state"]=self.itemState
            self.updateItemState(self.currentQueue["id"],self.itemState)
            self.messageToJs({'ejectState':self.ejectState,'queueState':self.queueState,'currentIndex':self.currentIndex})
            self.nextItem()

        else:
            if self.itemState!='Failed':
                self.currentIndex=self.currentIndex+1
            self.ejectState=EjectState.IDLE.value
            self.queueState=QueueState.RUNNING.value

            self.messageToJs({'ejectState':self.ejectState,'queueState':self.queueState,'currentIndex':self.currentIndex})

            self.nextItem()


        res = jsonify(success=True)
        res.status_code = 200
        return res
    @ octoprint.plugin.BlueprintPlugin.route("/cancelQueue", methods=["GET"])
    @ restricted_access
    def cancelQueue(self):

        self.queueState=QueueState.CANCELLED.value

        self.messageToJs({'queueState':self.queueState})
        self.nextItem()

        res = jsonify(success=True)
        res.status_code = 200
        return res



    @ octoprint.plugin.BlueprintPlugin.route("/pauseStopQueue", methods=["GET"])
    @ restricted_access
    def pauseStopQueue(self):
        self.queueState=QueueState.PAUSED.value
        self.messageToJs({'queueState':self.queueState})
        self.nextItem()
        res = jsonify(success=True)
        res.status_code = 200
        return res



    @ octoprint.plugin.BlueprintPlugin.route("/startQueue", methods=["GET"])
    @ restricted_access
    def startQueue(self):
            self.setSettings()
            self.queueState = "Started"
            totalTime = flask.request.args.get("totalEstimatedTime", 0)
            self.itemState=ItemState.PRINTING.value
            self.currentQueue["items"][self.currentIndex]["state"]=self.itemState
            self.updateItemState(self.currentQueue["id"],self.itemState)
            self.messageToJs({'itemState':self.itemState})

            self.totalEstimatedTime = totalTime
            if self.currentQueue!=None:
                if len(self.currentQueue["items"]) > 0:
                    self.itemState=ItemState.PRINTING.value
                    self.messageToJs({'itemState':self.itemState})
                    self.startPrint()
           


            res = jsonify(success=True)
            res.status_code = 200
            return res


    def updateLastQueue(self,queueId):
        Exist = Query()
        inDb = self.dbQueue.search(Exist.id == queueId)
        
        lastQueue = Query()
        last = self.dbQueue.search(lastQueue.last == "last_queue")

        if(len(last) > 0 and last != None):
            self.dbQueue.update({
                'last': "none",

            })


        
        


        if(len(inDb) > 0 and inDb != None):
            self.dbQueue.update({
                'last':"last_queue"
            },Exist.id==queueId)


    def updateItemState(self,queueId,itemState):

        Exist = Query()
        inDb = self.dbQueue.search(Exist.id == queueId)

        if(len(inDb) > 0 and inDb != None):
            self.dbQueue.update({
                'items': self.currentQueue["items"],

            },Exist.id==queueId)








    @ octoprint.plugin.BlueprintPlugin.route("/sendStartDatas", methods=["GET"])
    @ restricted_access
    def sendStartDatas(self):

        message ={}
        for val in self.requiredDatas:
            message[val]=getattr(self,val)

        self.messageToJs(message)
        self.messageToJs({'queues':self.queues})
        self.messageToJs({'ports':self.ports})



        return message


    @ octoprint.plugin.BlueprintPlugin.route("/createQueue", methods=["GET"])
    @ restricted_access
    def createQueue(self):
        self.queuesIndex=self.queuesIndex+1
        self.messageToJs({'queuesIndex':self.queuesIndex})
        self.currentQueue = dict(
            id=str(uuid.uuid4()),
            name="New Queue",
            items= [],
            index=self.queuesIndex
        )
        self.updateItemState(self.currentQueue["id"],self.itemState)
        self.messageToJs({'currentQueue':self.currentQueue})

        self.dbQueue.insert(self.currentQueue)

        self.queues.append(self.currentQueue)

        self.currentTime = 0
        self.totalEstimatedTime = 0
        self.messageToJs({'queueName':self.queueName})
        self.messageToJs({'queues':self.queues})
        self.messageToJs({'queuesIndex':self.queuesIndex})
        self.messageToJs({'currentQueue':self.currentQueue})


        self.currentItems=self.currentQueue["items"]
        self.messageToJs({'currentItems':self.currentItems})


        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/queueItemDown", methods=["GET"])
    @ restricted_access
    def queueItemDown(self):
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

    @ octoprint.plugin.BlueprintPlugin.route("/queueAddItem", methods=["POST"])
    @ restricted_access
    def queueAddItem(self):
        if self.currentQueue!=None:
            queue = self.currentQueue["items"]
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
        self.currentQueue["items"]=queue
        self.messageToJs({'currentQueue':self.currentQueue})
        self.updateItemState(self.currentQueue["id"],self.itemState)
        res = jsonify(success=True, data="")
        res.status_code = 200
        return res

    @octoprint.plugin.BlueprintPlugin.route("/pointer", methods=["GET"])
    @ restricted_access
    def pointer(self):
        self.currentIndex = (int(flask.request.args.get("index", 0))-1)
        self.itemState=ItemState.PRINTING.value                #resumede ejcet fail tetiklenmesin diye
        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/queueRemoveItem", methods=["DELETE"])
    @ restricted_access
    def queueRemoveItem(self):
        index = int(flask.request.args.get("index", 0))
        queue = self.currentQueue["items"]
        queue.pop(index)

        for i in queue:
            if i["index"] > index:
                i["index"] -= 1


        self.currentQueue["items"]=queue
        self.messageToJs({'currentQueue':self.currentQueue})
        self.updateItemState(self.currentQueue["id"],self.itemState)
        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/queueItemDuplicate", methods=["GET"])
    @ restricted_access
    def queueItemDuplicate(self):
        index = int(flask.request.args.get("index", 0))
        queue = copy.deepcopy(self.currentQueue["items"])

        item = queue[index]
        item["index"] += 1

        for i in self.currentQueue["items"]:
            if i["index"] > index:
                i["index"] += 1

        self.currentQueue["items"].insert(item["index"], item)
        self.messageToJs({'currentQueue':self.currentQueue})
        self.updateItemState(self.currentQueue["id"],self.itemState)

        res = jsonify(success=True)
        res.status_code = 200
        return res

    @ octoprint.plugin.BlueprintPlugin.route("/getQueue", methods=["GET"])
    @ restricted_access
    def getQueue(self):

        queueId = flask.request.args.get("id")
        search=Query()

        self.currentQueue=self.dbQueue.get(search.id==queueId)
     

        self.messageToJs({'currentQueue':self.currentQueue})

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
            if self.ejectState == "WaitForTemp":

                self.checkBedTemp(currentBedTemp)

        return parsed_temperatures

    def checkBedTemp(self,currentBedTemp):
        self.messageToJs({'temp':currentBedTemp,'targetBedTemp':self.settings2["targetBedTemp"]})

        if(currentBedTemp<=float(self.settings2["targetBedTemp"])):
            self.startEject() # state -> Ejecting,






__plugin_name__ = "speroplugin Plugin"
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():

    global __plugin_implementation__
    __plugin_implementation__ = Speroplugin()
    # register_custom_hooks()
    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.sanitize_temperatures,

    }