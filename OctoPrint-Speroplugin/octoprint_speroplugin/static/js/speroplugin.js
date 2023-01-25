/*ted
 * View model for OctoPrint-speroplugin
 *
 * Author: AHMET SARIOĞLU
 * License: AGPLv3
 */
$(function() {
    function SperoViewModel(parameters) {


        var self = this;
        self.selectedQueue = ko.observable();
        self.selectedPort = ko.observable();
        self.portName = ko.observable(0);
        self.temp=ko.observable(0)
        self.currentIndex=ko.observable(0)
        self.bedPosition=ko.observable(0)
        self.motorState=ko.observable(0)
        self.isShieldConnected=ko.observable(0)
        self.device=ko.observable(0)
        self.queueState=ko.observable("Idle");
        self.queueName = ko.observable(0);
        self.queuesIndex=ko.observable(0);
        self.currentQueue=ko.observable(0);
        self.createQueueEnable=ko.observable(0);
        self.repeatQueue=ko.observable("off");
        self.queueFinished=ko.observable(0)
        self.itemState=ko.observable();
        self.targetBedTemp=ko.observable(0);
        self.firstQueue=true;
        self.printerState = parameters[0];
        self.connectionState = parameters[1];
        self.loginState = parameters[2];
        self.files = parameters[3];
        self.settings = parameters[4];
        self.temperature = parameters[5];
        self.queues = ko.observableArray([]);
        self.ports= ko.observableArray([]);
        self.currentItems = ko.observableArray([]);
        self.queueId = ko.observable(null);
        self.itemInfo = ko.observable();               //sıcaklık verisini jinjaya gönderme
        self.itemCount = 0;                            //item sayısı





        self.onBeforeBinding = function () {
            try {
                self.reloadPlugin();
                self.fileDatas();
            } catch (error) {
                console.log("onBeforeBinding => ", error);

            }
        };

        self.startQueue = function () {
            try {
                self.fileDatas();
                $.ajax({
                    url:
                        "plugin/speroplugin/start-queue",
                    method: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: {},
                    success() {
                    },
                });
            } catch (error) {
                console.log("start_queue => ", error);
            }
        };




        self.pointer = function (index) {             // tıkladıgım pointerın indexsini döndürür
            try {
                if (index > 0) {
                    $.ajax({
                        url: "plugin/speroplugin/pointer?index=" + index,
                        type: "GET",
                        dataType: "json",
                        headers: { "X-Api-Key": UI_API_KEY },
                        success: function (c) {},
                        error: function () {},
                    });
                }
            } catch (error) {
                console.log("pointer error => ", error);
            }
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin == "speroplugin" && !_.isEmpty(data)) {
                try {
                   Object.entries(data).forEach((v)=>{
                        self[v[0]](v[1])
                    })
                    var message =
                        self.temp().toString() + " / " +self.targetBedTemp().toString() +
                        " C";
                    self.itemInfo(message);
                    if(self.firstQueue==true && self.currentQueue()!="0"){
                    self.firstQueue=false
                    self.selectedQueue(self.currentQueue())
                    }

                    if(self.queueFinished()==true){
                        self.queueFinished("false")
                        self.reloadPlugin()

                         }
                  
          
         
               

                


              }catch (error) {
            }
            }

        };






        self.pauseStopQueue = function (index) {
            try {
                    $.ajax({
                        url: "plugin/speroplugin/pause-stop-queue",
                        method: "GET",
                        dataType: "json",
                        headers: {
                            "X-Api-Key": UI_API_KEY,
                        },
                        data: {},
                        success: function () {},
                    });


            } catch (error) {
                console.log("pause resume queue error => ", error);
            }
        };

        self.cancelQueue = function () {
            try {
                $.ajax({
                    url: "plugin/speroplugin/cancel-queue",
                    method: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: {},
                });
            } catch (error) {
                console.log("cancel queue error => ", error);
            }
        };
        self.pauseResumeQueue = function () {
            try {
                 $.ajax({
                    url: "plugin/speroplugin/pause-resume-queue",
                    method: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: {},
                    success: function () {},
                });
            }catch (error) {
            console.log("pause resume queue error => ", error);
        }
    };

        self.getQueue = function (id) {              // queue itemleri atıyor
            if(self.queueState()=='Idle'){
                 try {
                    $.ajax({
                        url: "plugin/speroplugin/get-queue?id=" + id,
                        method: "GET",
                        dataType: "json",
                        headers: {
                            "X-Api-Key": UI_API_KEY,
                        },
                        success() {
                            ko.utils.arrayFirst(self.queues(), function (item) {
                                var reload =self.queueState() == "Idle"
                                if (item.id == id) {
                                    self.queueId(item.id);
                                    self.queueName(item.name);
                                    self.reloadItems(self.currentQueue())
                                    var queue = self.reloadItems(
                                        items=self.currentQueue()["items"],
                                        (reload = reload)
                                    );
                                    return queue;
                                }
                            });
                        },
                    });
                } catch (error) {
                }
        }};

      
        self.selectedQueue.subscribe(function (q) {
            if (q != undefined || q != null) {
                self.queueName(q.name)
                self.queuesIndex(q.index)
                self.queueId(q.id)
                
                if (q.items==[] || q.items==undefined) {
                  self.queueName(q.name)
                }
                else{
                    self.getQueue(q.id)
                    self.queueName(q.name)
                    self.queuesIndex(q.index)
                }
            }
        });

        self.selectedPort.subscribe(function (r) {
            if (r != undefined || r != null) {
                self.portName(r)
                self.sendPort(r)
                data=self.selectedPort()
                $.ajax({
                    url: "plugin/speroplugin/selected-port",
                    method: "POST",
                    contentType: "application/json",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: json,
                });
            }
        });


        // self.repeatOnOff = function (data) {
        //     // if (self.repeatQueue() == "off") {
        //     //     self.repeatQueue("on")
        //     //     document.getElementById("repeatButton").style.backgroundColor = "#3CAFEA";
        //     //     data="on"
        //     //     }
        //     // else{
        //     //     document.getElementById("repeatButton").style.backgroundColor = "rgb(249, 249, 249)";
        //     //     self.repeatQueue("off")
        //     //     data="off"
                
        //     // }
        //     console.log(self.repeatQueue())




        //     try {
        //         json = JSON.stringify({ request: data });
        //         $.ajax({
        //             url: "plugin/speroplugin/repeatOnOff",
        //             method: "POST",
        //             contentType: "application/json",
        //             dataType: "json",
        //             headers: {
        //                 "X-Api-Key": UI_API_KEY,
        //             },
        //             data: json,
        //         });
        //     } catch (error) {
           
        //     }
        // };

  



        self.deviceControl = function (data) {
            try {
                json = JSON.stringify({ request: data });
                $.ajax({
                    url: "plugin/speroplugin/device-control",
                    method: "POST",
                    contentType: "application/json",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: json,
                });
            } catch (error) {
                console.log("deviceControl => ", error);
            }
        };


        $(document).ready(function () {
            try {
                let regex =
                    /<div class="btn-group action-buttons">([\s\S]*)<.div>/im;
                let template =
                    '<div class="btn btn-mini bold" data-bind="click: function() { $root.fileAdItem($data) }," title="Add To Queue" ><i></i>P</div>';

                $("#files_template_machinecode").text(function () {
                    var return_value = $(this).text();
                    return_value = return_value.replace(
                        regex,
                        '<div class="btn-group action-buttons">$1	' +
                            template +
                            "></div>"
                    );
                    return return_value;
                });
            } catch (error) {
                console.log("document ready error => ", error);
            }
        });


        self.checkPrinting = function () {
            try {
                var have_print = false;
                return have_print;
            } catch (error) {
                console.log("check_printing => ", error);
            }
        };


        self.itemState.subscribe(function (state) {
                if (self.queueState != "Idle") {
                    var item = self.currentItems()[self.currentIndex()];
                  
                        switch (state) {
                            case "Printing":
                                item().state(state);
                         
                                break;
                            case "Ejecting":
                                item().state(state);
                                break;  
                            case "Await":
                                item().state(state);
                                break;
                            case "Cancelling":
                                item().state(state);
                                    break;
                            case "Cancelled":
                                item().state(state);
                                    break
                            case "Failed":
                                item().state(state);
                                    break
                            case "Finished":
                                item().state(state);
                                break;
                            case "Pausing":
                                item().state(state);
                                break;
                            case "Paused":
                                item().state(state);
                                break;

                            case "EjectFaild":
                                item().state(state);
                                break;
                            case "Resummed":
                                    item().state(state);
                                    break;
                            case "Cancelled":
                                item().state(state);
                                break;
                            default:
                                break;
                        }
                
                }
        });



      

        self.queueAddItem = function (data) {
            try {
                self.checkAddRemove("add", data.item);
                var jsonData = JSON.stringify({
                    index: self.itemCount - 1,
                    item: data.item,
                });

                $.ajax({
                    url: "plugin/speroplugin/queue-add-item",
                    type: "POST",
                    contentType: "application/json",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: jsonData,
                    success: function (data) {},
                    error: function (err) {
                        return console.log("Error occured", err);
                    },
                });
            } catch (error) {
                console.log("item add error ==> ", error);
            }
        };

        self.files.fileAdItem = function (data) {
            try {
                var sd = "true";
                if (data.origin == "local") {
                    sd = "false";
                }
                var item = {
                    name: data.name,
                    path: data.path,
                    timeLeft: data.gcodeAnalysis.estimatedPrintTime,
                    sd: sd,
                };

                self.queueAddItem({
                    item,
                });

            } catch (e) {
                console.log("File add item error => ", e);
            }
        };
        self.saveToDataBase = function (val,e) {
            const newName = e.target.value??'';
            if (self.selectedQueue()==undefined){
                self.currentId=self.currentQueue().id
            }
            else{
                self.currentId =self.selectedQueue().id
            }
            try {
                $.ajax({
                    url: "plugin/speroplugin/save-to-database",
                    method: "POST",
                    contentType: "application/json",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },

                    data: JSON.stringify({
                        queueName: newName,
                        id:  self.currentId,
                        index:(self.queuesIndex())

                    }),
                    success() {
                        self.queueName(newName)
                    },
                });
            } catch (error) {
                console.log("save_to_database => ", error);
            }
        };


        self.reloadItems = function (items = [], reload = false) {

            try {
                if (items!=undefined){
                    self.itemCount = items.length;
                }
                var templist = [];
                items.forEach((e) => {
                    items=self.currentQueue()["items"]
                    var temp = ko.observable({
                        index: ko.observable(e.index),
                        name: ko.observable(e.name),
                        progress: ko.observable(0),
                        timeLeft: ko.observable(e.timeLeft),
                        state: ko.observable(!reload ? e.state : "Await"),
                        
                        previous_state: ko.observable(""),
                        color: ko.observable(
                            !reload
                                ? e.state == "Printing"
                                    ? "#F9F9F9"
                                    : e.state == "Ejecting"
                                    ? "#F9F9F9"
                                    : e.state == "Finished"
                                    ? "#F9F9F9"
                                    : e.state == "Cancelling"
                                    ? "#F9F9F9"
                                    : e.state == "Await"
                                    ? "#F9F9F9"
                                    : e.state == "Canceled" ||
                                      e.state == "Failed"
                                    ? "#F9F9F9"
                                    : e.state == "Paused"
                                    ? "#F9F9F9"
                                    : "#F9F9F9"
                                : "#F9F9F9"
                        ),
                    });
                    templist.push(temp);
                });
                self.currentItems(templist);
                return templist;
            } catch (error) {
                
            }
        };

        self.reloadPlugin = function () {
            try {
                $.ajax({
                    url: "plugin/speroplugin/send-start-datas",
                    type: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    success: function (item) {
                        self.currentQueue(item["currentQueue"]["items"])
                        self.getQueue(item["currentQueue"]["id"])
                        // self.itemState("Finished");
                        for(let i=0;i<self.currentItems().length;i++){
                            var item = self.currentItems()[i];
                            item().state(self.itemState());

                         }
                    

                    },
                });
            } catch (error) {
                console.log("reloadPlugin => ", error);
            }
        };
        self.createQueue = function () {
            try {
             
                $.ajax({
                    url: "/plugin/speroplugin/create-queue",
                    type: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    success: function (r) {  
                    self.selectedQueue((self.currentQueue()))
                    self.currentItems(self.currentQueue().items)
                    self.itemCount=0
                    },
                    error: function (e) {
                        console.log(e);
                    },
                });
            } catch (error) {
                console.log("create queue error => ", error);
            }
        };
        self.checkAddRemove = function (type, data) {
            try {
                if (type == "add") {
                    var index = self.itemCount;
                    var temp = ko.observable({
                        index: ko.observable(index),
                        name: ko.observable(data.name),
                        progress: ko.observable("-"),
                        timeLeft: ko.observable(data.timeLeft),
                        state: ko.observable("Await"),
                        previous_state: ko.observable(""),
                        color: ko.observable("#F9F9F9"),
                    });
                    self.currentItems.push(temp);
                    self.itemCount += 1;
                }
                if (type == "remove") {
                    self.currentItems.remove(self.currentItems()[data]);
                    self.currentItems().forEach((element) => {
                        if (element().index() > data) {
                            element().index(element().index() - 1);
                        }
                    });
                    self.itemCount -= 1;
                }
            } catch (error) {
                console.log("checkAddRemove => ", error);
            }
        };

        self.queueRemoveItem = function (data) {
            try {
                self.checkAddRemove("remove", data);
                $.ajax({
                    url: "plugin/speroplugin/queue-remove-item?index=" + data,
                    type: "DELETE",
                    dataType: "text",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                });
            } catch (error) {
                console.log("item remove error => ", error);
            }
        };
        self.fileDatas = function (index = null) {
            try {
                $.ajax({
                    url: "/api/files?recursive=true",
                    type: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: {},
                    success(data) {
                        self.currentItems().forEach((item) => {
                            var isNotCancel =
                                item().state() != "Canceled" &&
                                item().state() != "Cancelling";
                            var isNotFinish =
                                item().state() != "Ejecting" &&
                                item().state() != "Finished";

                            data.files.forEach((file) => {
                                if (index == null || item().index() == index) {
                                    if (file.children) {
                                        file.children.forEach((child) => {
                                            if (item().name() == child.name) {
                                                if (
                                                    isNotCancel &&
                                                    isNotFinish
                                                ) {
                                                    item().timeLeft(
                                                        child.gcodeAnalysis
                                                            .estimatedPrintTime
                                                    );
                                                } else {
                                                    item().timeLeft(0);
                                                }
                                                return;
                                            }
                                        });
                                    } else {
                                        if (item().name() == file.name) {
                                            if (isNotCancel && isNotFinish) {
                                                item().timeLeft(
                                                    file.gcodeAnalysis
                                                        .estimatedPrintTime
                                                );
                                            } else {
                                                item().timeLeft(0);
                                            }
                                            return;
                                        }
                                    }
                                }
                            });
                            if (index != null && index == item().index()) {
                                return;
                            }
                        });
                    },
                });
            } catch (error) {
                console.log("fileDatas => ", error);
            }
        };
        self.queueItemDown = function (index) {
            try {
                if (index < self.currentItems().length - 1) {
                    self.rowChangeItems("down", index);

                    $.ajax({
                        url: "plugin/speroplugin/queue-item-down?index=" + index,
                        type: "GET",
                        dataType: "json",
                        headers: { "X-Api-Key": UI_API_KEY },
                        success: function (c) {},
                        error: function () {},
                    });
                }
            } catch (error) {
                console.log("queueItemDown error => ", error);
            }
        };

        self.rowChangeItems = function (type, index) {
            try {
                var newIndex;

                if (type == "up") newIndex = index - 1;
                if (type == "down") newIndex = index + 1;

                var itemCurrent = new self.currentItems()[index]();
                var itemNext = new self.currentItems()[newIndex]();

                itemCurrent.index(newIndex);
                itemNext.index(index);

                self.currentItems()[index](itemNext);
                self.currentItems()[newIndex](itemCurrent);
            } catch (error) {
                console.log("row change items error => ", error);
            }
        };

        self.queueItemUp = function (index) {
            try {
                if (index > 0) {
                    self.rowChangeItems("up", index);
                    $.ajax({
                        url: "plugin/speroplugin/queue-item-up?index=" + index,
                        type: "GET",
                        dataType: "json",
                        headers: { "X-Api-Key": UI_API_KEY },
                        success: function (c) {},
                        error: function () {},
                    });
                }
            } catch (error) {
                console.log("queueItemUp error => ", error);
            }
        };

        self.checkCreateQueueEnable = function () {
            if(self.selectedQueue()==undefined){
                self.createQueueEnable("idle")
                }
            else{
                self.createQueueEnable("false")

            }    
        };
        self.queueItemDuplicate = function (data) {
            try {
                $.ajax({
                    url: "plugin/speroplugin/queue-item-duplicate?index=" + data,
                    type: "GET",
                    dataType: "text",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    success: function () {
                        self.reloadPlugin()
                    },
                });
            } catch (error) {
                console.log("duplicate item error => ", error);
            }
        };
        self.deleteFromDatabase = function () {
            try {
                $.ajax({
                    url:
                        "plugin/speroplugin/delete-from-database?id=" +
                        self.queueId(),
                    method: "DELETE",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: {},
                    success() {

                        self.queueName(null);
                        self.queueId(null);
                        self.currentItems(null);
                    },
                });
            } catch (error) {
                console.log("deleteFromDatabase => ", error);
            }

        self.recursiveGetFiles = function (files) {
                try {
                    var filelist = [];
                    for (var i = 0; i < files.length; i++) {
                        var file = files[i];
                        if (
                            file.name.toLowerCase().indexOf(".gco") > -1 ||
                            file.name.toLowerCase().indexOf(".gcode") > -1
                        ) {
                            filelist.push(file);
                        } else if (file.children != undefined) {
                            filelist = filelist.concat(
                                self.recursiveGetFiles(file.children)
                            );
                        }
                    }
                    return filelist;
                } catch (error) {
                    console.log("recursiveGetFiles error => ", error);
                }
            };

        };
    }


    OCTOPRINT_VIEWMODELS.push({
        construct: SperoViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["printerStateViewModel",
            "connectionViewModel",
            "loginStateViewModel",
            "filesViewModel",
            "settingsViewModel",
            "temperatureViewModel", ],
        // Elements to bind to, e.g. #settings_plugin_speroplugin, #tab_plugin_speroplugin, ...
        elements: ["#tab_plugin_speroplugin"],
    });
});