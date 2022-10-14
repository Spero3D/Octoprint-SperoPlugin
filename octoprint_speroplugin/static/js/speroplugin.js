/*ted
 * View model for OctoPrint-speroplugin
 *
 * Author: AHMET SARIOĞLU
 * License: AGPLv3
 */
$(function() {
    function SperoViewModel(parameters) {
        

        var self = this;
        self.temp=ko.observable(0)
        self.currentIndex=ko.observable(0)
        self.bedPosition=ko.observable(0)
        self.motorState=ko.observable(0)
        self.isShieldConnected=ko.observable(0)
        self.queueState=ko.observable("IDLE");
        self.queueName = ko.observable(null);
        self.queuesIndex=ko.observable(null);
        self.currentQueue=ko.observable(null);
        self.selectedQueue = ko.observable();
        self.itemState=ko.observable();
        


        self.printerState = parameters[0];
        self.connectionState = parameters[1];
        self.loginState = parameters[2];
        self.files = parameters[3];
        self.settings = parameters[4];
        self.temperature = parameters[5];
   
        self.settings = ko.observable({}); 
        self.queues = ko.observableArray([]);
        self.currentItems = ko.observableArray([]);
        self.queueId = ko.observable(null);
        
     

    
        self.stateMotorr = ko.observable();
        
        self.isQueuePrinting = ko.observable(false);
        self.isManualEject = ko.observable(false);

        self.connection = ko.observable(false);
        self.client_address = ko.observable(null);
        self.client_state = ko.observable(null);
        self.client_motor = ko.observable(null);
        self.sheild_motor = ko.observable(null);
        self.client_position = ko.observable(null);
        self.queueState = ko.observable("IDLE");

        self.item_info = ko.observable();
        self.info_message = ko.observable();
      
        self.info_color = ko.observable();

        self.terminating = ko.observable(false);
        self.ejecting = ko.observable(false);
        self.eject_fail = ko.observable(false);

        self.item_count = 0;
        self.target_temp = 40;
        self.currentIndex = ko.observable();

        self.totalEstimatedTime = ko.observable(0);
       

        self.pins=[23,18,4,8,2,6,3,10,40]

        self.target_temp=ko.observable();
        self.motor_1=ko.observable();
        self.motor_2=ko.observable();
        self.front_switch=ko.observable();
        self.switch_back=ko.observable();
        self.button_forward=ko.observable();
        self.button_backward=ko.observable();
        self.button_sequence=ko.observable();


        
        self.settings.saveData = function (data, successCallback, setAsSending) {
            var options;
            var validated=true;
            if (_.isPlainObject(successCallback)) {
                options = successCallback;
            } else {
                options = {
                    success: successCallback,
                    sending: setAsSending === true
                };
            }
            self.settings.settingsDialog.trigger("beforeSave");

            self.settings.sawUpdateEventWhileSending = false;
            self.settings.sending(data === undefined || options.sending || false);

            if (data === undefined) {
                // we also only send data that actually changed when no data is specified
                var localData = self.settings.getLocalData();
                console.log('localData',self.printerState)

                self.button_backward(),self.button_sequence()
                data = getOnlyChangedData(localData, self.settings.lastReceivedSettings);
                if(_.has(data,'plugins.speroplugin')){
                    const changedSettings =  {...self.settings,..._.get(data,'plugins.speroplugin')??{}} 
     
                
                    console.log(self.pins)
                    
                    if(data.plugins.speroplugin.motorPin1!=undefined)
                        self.pins[0]=parseInt(data.plugins.speroplugin.motorPin1);

                    if(data.plugins.speroplugin.motorPin2!=undefined)
                        self.pins[1]=parseInt(data.plugins.speroplugin.motorPin2);


                    if(data.plugins.speroplugin.switchFront!=undefined)
                        self.pins[2]=parseInt(data.plugins.speroplugin.switchFront);

                    if(data.plugins.speroplugin.switchBack!=undefined)
                        self.pins[3]=parseInt(data.plugins.speroplugin.switchBack);

                    if(data.plugins.speroplugin.buttonForward!=undefined)
                        self.pins[4]=parseInt(data.plugins.speroplugin.buttonForward);
                    if(data.plugins.speroplugin.buttonBackword!=undefined)
                        self.pins[5]=parseInt(data.plugins.speroplugin.buttonBackword);
                    if(data.plugins.speroplugin.buttonSequence!=undefined){
                        self.pins[6]=parseInt(data.plugins.speroplugin.buttonSequence);
                    
                    }

                    console.log(data.plugins.speroplugin)
                    
                    let map = {};
                    let result = false;
                    for(let i = 0; i < self.pins.length; i++) {
                        if(map[self.pins[i]]) {
                            result = true;
                            break;
                        }
                        map[self.pins[i]] = true;
                    }
                    if(result) {
                      
                        console.log('Array contains duplicate elements');
                        validated = false;
                        console.log("send info")
                  
                    } else {
                     
                   
                        console.log('Array does not contain duplicate elements'); 
                        validated = true;
                    
                    }







                    //TODO: check there is any validation issue
                    // sorun varsa -> validated=false
                    // sorun yoksa -> validated=true
                    data.plugins.speroplugin.error =!validated;
                    
                    // console.log('data',data);

                    console.log(data.plugins.speroplugin)
                    console.log(self.pins);
                    
         

                }

            }

            // final validation
            if (self.settings.testFoldersDuplicate()) {
                // duplicate folders configured, we refuse to send any folder config
                // to the server
                delete data.folder;
            }

            self.settings.active = true;
            return OctoPrint.settings
                .save(data)
                .done(function (data, status, xhr) {
                    self.settings.ignoreNextUpdateEvent = !self.settings.sawUpdateEventWhileSending;
                    self.settings.active = false;
                    self.settings.receiving(true);
                    self.settings.sending(false);

                    try {
                        self.settings.fromResponse(data);
                        if(validated){
                            if (options.success) options.success(data, status, xhr);

                        }else{
                            if (options.error) options.error(xhr, status, "Validation Error");
                        }

                    } finally {
                        self.settings.receiving(false);
                    }
                })
                .fail(function (xhr, status, error) {
                    self.settings.sending(false);
                    self.settings.active = false;
                    if (options.error) options.error(xhr, status, error);
                })
                .always(function (xhr, status) {
                    if (options.complete) options.complete(xhr, status);
                });
        };

        // self.onSettingsBeforeSave=function(ali){
        //     console.log('ali',self.settings)
        // }
        
 
        self.onBeforeBinding = function () {
            try {
                
            
                self.reload_plugin();
                self.fileDatas();
            } catch (error) {
                console.log("onBeforeBinding => ", error);

            }
        };
        self.startQueue = function () {
            try {
                console.log("start_queue")                           
                self.fileDatas();
          
                self.reload_plugin();
               

                $.ajax({
                    url:
                        "plugin/speroplugin/startQueue?totalEstimatedTime=" +
                        self.totalEstimatedTime(),
                    method: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: {},
                    success() {
                      console.log("printStarted")
                    },
                });
                  
           
               
               
            } catch (error) {
                console.log("start_queue => ", error);
            }
        };




        // self.sendTerminateMessage = function () {
        //     try {
        //         if (self.isQueueStarted() && self.isQueuePrinting()) {
        //             if (self.queueState != "IDLE") {
        //                 self.ejecting(true);
        //                 $.ajax({
        //                     url: "plugin/speroplugin/sendTerminateMessage",
        //                     method: "GET",
        //                     dataType: "json",
        //                     headers: {
        //                         "X-Api-Key": UI_API_KEY,
        //                     },
        //                     success(r) {},
        //                 });
        //             }
        //         }
        //     } catch (error) {
        //         console.log("sendTerminateMessage error => ", error);
        //     }
        // };

        // self.prev_check = function (index) {
        //     try {
        //         if (self.currentItems().length > 1) {
        //             let state = self.currentItems()[index - 1]().state();
        //             if (state == "Await") {
        //                 return false;
        //             } else return true;
        //         } else return true;
        //     } catch (error) {
        //         console.log("prev_check => ", error);
        //     }
        // };

        // self.check_connection = function () {
        //     try {
        //         $.ajax({
        //             url: "/api/connection",
        //             method: "GET",
        //             dataType: "json",
        //             headers: {
        //                 "X-Api-Key": UI_API_KEY,
        //             },
        //             success(r) {
        //              self.connection(true);
        //             },
        //         });
        //     } catch (error) {
        //         console.log("connection check error => ", error);
        //     }
        //     b=5;
        //     if(b==5);
        //     self.Connection(true);
        // };


        // self.check_is_busy = ko.computed(function () {
        //     if (
        //         self.isQueuePrinting() == false &&
        //         self.printerState.isBusy() == true
        //     ) {
        //         return false;
        //     } else {
        //         return true;
        //     }
        // }, self);
        

        self.pointer = function (index) {
            try {
              
                
                self.index2=index
                console.log("pointer")
                console.log(self.index2)
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
                    console.log('temp',self.temp())
                    console.log('currentIndex',self.currentIndex());
                    console.log('bedPosition',self.bedPosition());
                    console.log('motorState',self.motorState());
                    console.log('isShieldConnected',self.isShieldConnected());
                    console.log('queueState',self.queueState());
                    console.log('queues',self.queues());
                    console.log('currentQueue',self.currentQueue());
                    console.log('itemState',self.itemState());

                    self.selectedQueue(self.currentQueue())
                    
                    // console.log(self.currentItems(self.currentQueue()["items"]));
                    // console.log(self.currentItems())
               

                // if(data["eject_fail"] !=undefined) {
                //     console.log(data["eject_fail"])
                   
                //     if (data["eject_fail"]==true){
                //         var item = self.currentItems()[self.currentIndex()];
                //         item().state("Eject Failed");
                //         item().color("#F9F9F9");
                        
                //         self.queueState('PAUSED');
                //         self.queueState=='PAUSED';
                //     }

                // }      

                // if(data["motorPin1"] !=undefined) {
                //     console.log(data["motorPin1"]);
                //     self.motor_1(data["motorPin1"]);
                // }
                // if(data["print_bed_state"] !=undefined) {
                //     var tabla = data["print_bed_state"];
                //     self.client_position(tabla);
            
                // }


                // if(data["print_bed_state"] !=undefined) {
                //     var tabla = data["print_bed_state"];
                //     self.client_position(tabla);
            
                // }

           
             
                
                // if(data["queue_finish"] !=undefined) {
                //     if (data["queue_finish"]=="yes"){
                //         console.log(data["queue_finish"]);
                //         console.log("asdpokj");
                //         self.queueState('FINISHED');
                //         self.queueState=='FINISHED';
                //     }

                // }
                // if(data["cansel_queue"] !=undefined) {
                //     self.deneme2 = data["cansel_queue"];
                //     if (data["cansel_queue"] =="yes"){
                //         self.queueState("IDLE");
                //         self.currentItems().forEach((element) => {
                //             element().state("Await");
                //             element().color("white");
                //         });
                //     }


                // }


                // if(data["motor_state"] !=undefined) {
                //     var motor = data["motor_state"];
                //     self.client_motor(motor) ;
                // }


                // if(data["connection"] !=undefined) {
               
                //     self.Connection(data["connection"]) ;
                // }
                // if(data["temp"] !=undefined) {
                //     var motor = data["temp"];
         
                //     var message =
                //         data["temp"].toString() +
                //         " / " +
                //         self.target_temp.toString() +
                //         " C";
                //     self.item_info(message);


                    
                // }

                                          
                // if (data["isQueuePrinting"] != undefined) {
                //     self.isQueuePrinting(data["isQueuePrinting"]);
                // }
                // if (data["isManualEject"] != undefined) {
                //     self.isManualEject(data["isManualEject"]);
                // }


                // if (data["index_current"]) {

                //     self.currentIndex(data["index_current"]);

                // }
                // if (data["itemResult"]) {
                //     console.log(data["itemResult"])
                //     self.Finished=data["itemResult"];
                //     var item = self.currentItems()[self.currentIndex()];
                //     item().state(data["itemResult"]);
                //     item().previous_state(data["itemResult"]);

                //     if (data["itemResult"] == "Finished")
                //         item().color("#F9F9F9");
                //     if (data["itemResult"] == "Canceled")
                //         item().color("#F9F9F9");

                //     item().timeLeft(0);
                // }
                // if (data["targetTemp"])
                //     self.target_temp = data["targetTemp"];

                // if (data["terminate"]) {
                //     self.terminating(data["terminate"]);
                // }
                // if (data["stop"]) {
                //     if (self.queueState() == "CANCELED") {
                //         self.send_info("Queue canceled.", "danger");
                //     } else {
                //         self.send_info("Queue finished!", "success");
                //     }
                //     self.terminating(false);
                //     self.isQueueStarted(false);
                //     self.ejecting(false);

                //     self.currentItems().forEach((element) => {
                //         element().state("Await");
                //         element().color("white");
                //     });

                //     self.currentIndex(0);
                //     self.queueState("IDLE");
                // }

                        
              }catch (error) {
                console.log("onDataUpdaterPluginMessage => ", error);
            }
            }
        
        };
        

        self.temperature_bed=function(){
            var message =
                data.toString() +
                " / " +
                self.target_temp.toString() +
                " C";
            self.item_info(message);

        }


        // self.onEventStart = function (payload) {
        //     try {

        //         if (self.isQueueStarted() && self.isQueuePrinting()) {
        //             self.terminating(false);
        //             self.queueState("RUNNING");
        //             self.send_info(this.sheild_motor)
                    
               
        //         }
        //     } catch (error) {
        //         console.log("resume print event error => ", error);
        //     }
        // };
        // self.onEvent = function (payload) {
        //     try {
        //         console.log("hello")
        //     } catch (error) {
        //         console.log("resume print event error => ", error);
        //     }
        // };






        self.pauseStopQueue = function (index) {
            try {
         
                console.log(self.pauseclickQueueNumber);
                
            

                ;

          
                console.log("pause ye basıldı");
                self.queueState('PAUSED');
                self.queueState=='PAUSED';

                    $.ajax({
                        url: "plugin/speroplugin/pauseStopQueue",
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

                console.log("Cansel la basıldı")
                self.queueState('CANCELLED');
                self.queueState=='CANCELLED';
                

                $.ajax({
                    url: "plugin/speroplugin/cancelQueue",
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


                console.log("play press")
                self.queueState('RUNNING');
                self.queueState=='RUNNING';
           

                





                // if (self.isQueueStarted()) {
                //     if (self.connection()) {
                //         if (self.queueState() == "RUNNING") {
                //             self.queueState("PAUSED");
                //             self.send_info("Queue paused.", "info");
                //         } else if (self.queueState() == "PAUSED") {
                //             self.send_info("Queue resumed", "info");
                //             self.queueState("RUNNING");
                //         }

                        $.ajax({
                            url: "plugin/speroplugin/pause_resume_queue",
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

        self.getQueue = function (id) {
            console.log("asdişlamsdkş")
            try {
                console.log("Our queue id is =>=> ", id);
                $.ajax({
                    url: "plugin/speroplugin/getQueue?id=" + id,
                    method: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    success() {
                        ko.utils.arrayFirst(self.queues(), function (item) {
                            var reload =
                                self.queueState() == "IDLE"
                            if (item.id == id) {
                                console.log(item);
                                self.queueId(item.id);
                                self.queueName(item.name);

                                var queue = self.reload_items(
                                    item.items,
                                    (reload = reload)
                                );
                                console.log("Array get successfull!");
                                return queue;
                            }
                        });
                    },
                });
            } catch (error) {
                console.log("getQueue => ", error);
            }
        };
        self.selectedQueue.subscribe(function (q) {
            if (q != undefined || q != null) {
            
                self.getQueue(q.id);
                self.queueName(q.name)
                self.queuesIndex(q.index)
                
            
           
                
            }
        });
        // self.stateMotorr.subscribe(function (q) {
        //     if (q != undefined || q != null) {
        //         self.client_motor(item.esp["motor"]);
        //     }
        // });
        self.deviceControl = function (data) {
            try {
                if (self.eject_fail() == true) {
                    self.eject_fail(false);
                    if (data == "cancel") {
                        self.ejecting(false);
                        self.terminating(false);
                    } else if (data == "eject") {
                        self.ejecting(true);
                        self.terminating(true);
                        
                    }
                }
                json = JSON.stringify({ request: data });
                $.ajax({
                    url: "plugin/speroplugin/deviceControl",
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


        // self.check_button = function (data) {
            
        //         console.log("saaaaaaaaaa")
        //         json = JSON.stringify({ request: data });
        //         $.ajax({
        //             url: "plugin/speroplugin/check_button",
        //             method: "POST",
        //             contentType: "application/json",
        //             dataType: "json",
        //             headers: {
        //                 "X-Api-Key": UI_API_KEY,
        //             },
        //             data: json,
        //         });
     
        // };



        $(document).ready(function () {
            try {
                let regex =
                    /<div class="btn-group action-buttons">([\s\S]*)<.div>/im;
                let template =
                    '<div class="btn btn-mini bold" data-bind="click: function() { $root.file_ad_item($data) }," title="Add To Queue" ><i></i>P</div>';

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

        // self.check_empty = function (type) {
        //     try {
        //         var list = [];

        //         if (type == "queues") list = self.queues();
        //         if (type == "current_queue") list = self.currentItems();

        //         if (list != null && list != undefined) {
        //             if (list.length > 0) return false;
        //             else return true;
        //         } else return true;
        //     } catch (e) {
        //         console.log("check_empty => ", e);
        //     }
        // };

        self.checkPrinting = function () {
            try {
                var have_print = false;

                self.currentItems().forEach((element) => {
                    if (
                        element().state() == "Printing" ||
                        element().state() == "Paused"
                    ) {
                        have_print = true;
                        return have_print;
                    }
                });
                return have_print;
            } catch (error) {
                console.log("check_printing => ", error);
            }
        };


        self.printerState.printTime.subscribe(function (data) {
            try {
              
                   {
                        if (data != null || data != undefined) {
                            self.currentItems()
                                [self.currentIndex()]()
                                .timeLeft(self.printerState.printTimeLeft());
                            self.currentItems()
                                [self.currentIndex()]()
                                .progress(
                                    self.printerState.progressString() ?? 0
                                );

                            self.totalPrintTime();
                            self.sendTimeData();
                        }
                    }
                
            } catch (error) {
                console.log("print time subscription => ", error);
            }
        });

        // self.onEventError = function (payload) {
        //     try {
        //         if (self.isQueueStarted() && self.isQueuePrinting()) {
        //             if (self.queueState() != "IDLE") {
        //                 var item = self.currentItems()[self.currentIndex()];

        //                 if (item().state() != "Cancelling") {
        //                     self.terminating(false);
        //                     item().state("Failed");
        //                     item().color("#F9F9F9");
        //                     self.queueState("PAUSED");

        //                     self.send_info(
        //                         "Error occurs while printing!",
        //                         "Danger"
        //                     );
        //                 }
        //             }
        //         }
        //     } catch (error) {
        //         console.log("onEventError error => ", error);
        //     }
        // };

        // self.onEventDisconnected = function (payload) {
        //     try {
        //         if (self.isQueueStarted() && self.isQueuePrinting()) {
        //             if (self.queueState() != "IDLE") {
        //                 var item = self.currentItems()[self.currentIndex()];

        //                 if (
        //                     item().state() != "Cancelled" ||
        //                     item().state() != "Cancelling"
        //                 ) {
        //                     self.terminating(false);
        //                     self.isQueuePrinting(false);

        //                     item().state("Failed");
        //                     item().color("#F9F9F9");
        //                     self.queueState("PAUSED");

        //                     self.send_info("Printer disconnected!", "danger");
        //                 }
        //             } else self.connection(false);
        //         }
        //     } catch (error) {
        //         console.log("disconnect event error => ", error);
        //     }
        // };

        // self.onEventPrintResumed = function (payload) {

        //     console.log("resume press")

        //     self.queueState('RUNNING');
        //     self.queueState=='RUNNING';
     
        // };

        // self.onEventPrintDone = function (payload) {
        //     try {
        //         console.log("print done");
     

        //         if (self.isQueueStarted() && self.isQueuePrinting()) {
        //             var item = self.currentItems()[self.currentIndex()];
        //             self.terminating(true);
        //             item().state("Ejecting");
        //             item().color("#F9F9F9");
                    
        //         }
        //     } catch (error) {
        //         console.log("print done event error => ", error);
        //     }
        // };

        // self.onEventPrintCancelled = function (payload) {
        //     try {
        //         var item = self.currentItems()[self.currentIndex()];
        //         item().state("Cancelled");
        //         console.log("Cansel la basıldı")
        //         self.queueState('CANCELLED');
        //         self.state="Cancelled"
        //         self.queueState=='CANCELLED';
                

        //         if (self.isQueueStarted() && self.isQueuePrinting()) {onEventPrintDone
        //             item().color("#F9F9F9");

        //             if (self.queueState() != "CANCELED")
        //                 self.queueState("PAUSED");
        //         }
        //     } catch (error) {
        //         console.log("print cancel event error => ", error);
        //     }
        // };


        // self.onEventPrintPaused = function (payload) {
        //     var item = self.currentItems()[self.currentIndex()];
        
        //     item().state("Cancelled");
        //     console.log("paused")
       
        // };


        // self.onEventConnected = function (payload) {
        //     try {
        //         self.terminating(false);
        //         self.connection(true);
        //     } catch (error) {
        //         console.log("connect event error => ", error);
        //     }
        // };

        // self.printerState.printTime.subscribe(function (data) {
        //     try {
        //         if (self.isQueueStarted() && self.isQueuePrinting()) {
        //             if (
        //                 self.currentIndex() != null &&
        //                 self.queueState() != "IDLE"
        //             ) {
        //                 if (data != null || data != undefined) {
        //                     self.currentItems()
        //                         [self.currentIndex()]()
        //                         .timeLeft(self.printerState.
        //                             self.onEventConnected = function (payload) {
        //                                 try {
        //                                     self.terminating(false);
        //                                     self.connection(true);
        //                                 } catch (error) {
        //                                     console.log("connect event error => ", error);
        //                                 }
        //                             };
                            
        //                         [self.currentIndex()]()
        //                         .progress(
        //                             self.printerState.progressString() ?? 0
        //                         );

        //                     self.totalPrintTime();

        //                     self.sendTimeData();
        //                 }
        //             }
        //         }
        //     } catch (error) {
        //         console.log("print time subscription => ", error);
        //     }
        // });
      
        self.printerState.stateString.subscribe(function (state) {
            try {   
            
            
                if (self.queueState != "IDLE") {
                    var item = self.currentItems()[self.currentIndex()];
                    if (
                        state != "Operational" &&
                        state != "Finished" &&
                        state != "Cancelled"
                    ) {
                        switch (state) {
                            case "Printing":
                                self.terminating(false);
                                item().color("#F9F9F9");
                                item().state(state);
                                if (self.queueState() != "PAUSED")
                                    self.queueState("RUNNING");
                                break;
                            case "Pausing":
                                self.terminating(true);
                                item().color("#F9F9F9");
                                item().state(state);
                                self.queueState("PAUSING");
                                break;
                            case "Paused":
                                self.terminating(false);
                                item().color("#F9F9F9");
                                item().state(state);
                                self.queueState("PAUSED");
                                break;
                                
                            case "Eject Faild":
                                self.terminating(false);
                                item().color("red");
                                item().state(state);
                                self.queueState("EJECT FAILD");
                                break;


                            case "Cancelled":
                                self.terminating(false);
                                item().color("red");
                                item().state(state);
                                self.queueState("CANCELLED");
                                break;
                            default:
                                break;
                        }
                    }
                }
                
                
            } catch (error) {
                console.log("printerState => ", error);
            }
        });




        self.totalPrintTime = function () {
            try {
                var totalTime = 0;
                self.currentItems().forEach((element) => {
                    totalTime += parseInt(element().timeLeft());
                });
                self.totalEstimatedTime(totalTime);
            } catch (error) {
                console.log("totalPrintTime error => ", error);
            }
        };

        // self.check_removed = function () {
        //     try {
        //         if (
        //             (self.queueId() == undefined || self.queueId() == null) &&
        //             (self.queueName() == null ||
        //                 self.queueName() == undefined)
        //         ) {
        //             return true;
        //         } else {
        //             return false;
        //         }
        //     } catch (e) {
        //         console.log("check_empty => ", e);
        //     }
        // };




     
    
        self.queue_item_add = function (data) {
            try {
                self.check_add_remove("add", data.item);

                var jsonData = JSON.stringify({
                    index: self.item_count - 1,
                    item: data.item,
                });

                $.ajax({
                    url: "plugin/speroplugin/queue_add_item",
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
        self.files.file_ad_item = function (data) {
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

                self.queue_item_add({
                    item,
                });
                
            } catch (e) {
                console.log("File add item error => ", e);
            }
        };
        self.saveToDataBase = function (val,e) {

          
           
            const newName = e.target.value??'';
            console.log(newName)
         
            try {
                $.ajax({
                    url: "plugin/speroplugin/saveToDataBase",
                    method: "POST",
                    contentType: "application/json",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: JSON.stringify({
                        queueName: newName,
                        id: self.selectedQueue().id,
                        index:self.queuesIndex(),
                    }),
                    success() {
                  
                        self.queueName(newName)
                        self.send_info(
                            "Queue saved in to saveToDatabase.",
                            "success"
                        );
                        console.log("----------reload----------")
                        self.reload_plugin();
                    },
                });
            } catch (error) {
                console.log("save_to_database => ", error);
            }
        };

  
        
     


        
        self.reload_items = function (items = [], reload = false) {
            try {
                self.item_count = items.length;
                var templist = [];

                items.forEach((e) => {
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
                console.log("reload_items => ", error);
            }
        };


    //     self.change_position=function(){
    //     cansol.log("motor poz change")
    //     if (item.esp["motor"] != undefined);
   
    //    }


        
        self.reload_plugin = function () {
            try {
                $.ajax({
                    url: "plugin/speroplugin/sendStartDatas",
                    type: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    success: function (item) {
                       
                        // self.queueState("IDLE");
                        // self.item_count = 0;
                        // self.currentIndex(0);
                        // if (item.totalEstimatedTime != undefined)
                        //     self.totalEstimatedTime(item.totalEstimatedTime);


                        // self.sheild_motor=='idle';

                        // if (item.queues) {
                        //     self.queues([]);
                        //     item.queues.forEach((element) => {
                        //         self.queues.push(element);
                        //     });
                        // }
                        
                        // if (item.motor_1) {
                        //     self.motor_1=item.motor_1
                        // }
                        // if (item.motor_state) {
                        //     self.motor_state=item.motor_state;
                        //     self.client_motor(item.motor_state);
                        // }

                        // if (item.print_bed_state) {
                        //     self.client_position(item.print_bed_state);
                        // }
                        // if (item.isQueueStarted) {
                        //     self.isQueueStarted(item.isQueueStarted);
                        // }

                        // if (item.isQueuePrinting) {
                        //     self.isQueuePrinting(item.isQueuePrinting);
                        // }

                        // if (item.isManualEject) {
                        //     self.isManualEject(item.isManualEject);
                        // }

                        // if (item.esp) {
                    
                        //     self.client_address(item.esp["address"]);
                        //     self.client_state(item.esp["connection"]);
                        //     if (item.esp["motor"] != undefined)
      
                        //     if (item.esp["position"] != undefined)
                        //         self.client_position(item.esp["position"]);
                        // }
                        // if(item.motor_state){
                        //     self.client_motor(item.motor_state);

                        // }
                        // if (item.queueState != undefined)
                        //     self.queueState(item.queueState);
                        // if (item.current_index != undefined) {
                        //     self.currentIndex(item.current_index);
                        // }

                        // if (item.terminating != undefined) {
                        //     self.terminating(item.terminating);
                        // }
                        // if (item.ejecting != undefined)
                        //     self.ejecting(item.ejecting);
                        // if (item.eject_fail != undefined) {
                        //     self.eject_fail(item.eject_fail);
                        //     console.log(item.eject_fail);
                          
                        // }

                        // if (item.queue != undefined) {
                        //     self.selectedQueue(item.queue);    
                        //     self.currentItems([]);

                        //     console.log(
                        //         item.queue["id"],
                        //         item.queue["name"],
                        //         item.queue["items"]
                        //     );

                        //     if (item.queue != undefined && item.queue != null) {
                        //         self.queueName(item.queue["name"]);
                        //         self.queueId(item.queue["id"]);

                        //         if (item.queue["items"] != undefined) {
                        //             if (item.queue["items"].length > 0) {
                        //                 self.reload_items(item.queue["items"]);
                        //             }
                        //         }
                        //     } else {
                        //         self.queueName(null);
                        //         self.queueId(null);
                        //         self.currentItems(null);
                        //     }
                        // }
                        // if (item.target_temp)
                        //     self.target_temp = item.target_temp;
                    },
                });
            } catch (error) {
                console.log("reload_plugin => ", error);
            }
        };

        self.send_info = function (message, type) {
            try {
                self.info_message(message);
                switch (type) {
                    case "info":
                        self.info_color("powderblue");
                        break;
                    case "warning":
                        self.info_color("gold");
                        break;
                    case "danger":
                        self.info_color("lightcoral");
                        break;
                    case "success":
                        self.info_color("darkseagreen");
                        break;
                    default:
                        break;
                }

                setTimeout(function () {
                    self.info_message(null);
                }, 3000);
            } catch (error) {
                console.log("send info error => ", error);
            }
        };
        self.createQueue = function () {
            try {
                // self.queueState('IDLE');
                // self.queueState=='IDLE';
                $.ajax({
                    url: "/plugin/speroplugin/createQueue",
                    type: "GET",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    success: function (r) {
                    
                        self.reload_plugin();
                        self.send_info("Queue created.", "success");
                    },
                    error: function (e) {
                        console.log(e);
                    },
                });
            } catch (error) {
                console.log("create queue error => ", error);
            }
        };
        self.check_add_remove = function (type, data) {
            try {
                if (type == "add") {
                    var index = self.item_count;
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
                    self.item_count += 1;
                }
                if (type == "remove") {
                    self.currentItems.remove(self.currentItems()[data]);
                    self.currentItems().forEach((element) => {
                        if (element().index() > data) {
                            element().index(element().index() - 1);
                        }
                    });
                    self.item_count -= 1;
                }
            } catch (error) {
                console.log("check_add_remove => ", error);
            }
        };

        self.queue_item_remove = function (data) {
            try {
                self.check_add_remove("remove", data);
                $.ajax({
                    url: "plugin/speroplugin/queue_remove_item?index=" + data,
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
        self.sendTimeData = function (
            customIndex = null,
            sendTotalTime = true
        ) {
            try {
                customIndex =
                    customIndex != null ? customIndex : self.currentIndex();

                var time = JSON.stringify({
                    index: customIndex,
                    timeLeft:
                        self.currentItems()[customIndex]().timeLeft() ?? 0,
                    totalEstimatedTime: sendTotalTime
                        ? self.totalEstimatedTime()
                        : null,
                });

                $.ajax({
                    url: "plugin/speroplugin/sendTimeData",
                    method: "POST",
                    dataType: "json",
                    contentType: "application/json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: time,
                    success() {},
                });
            } catch (error) {
                console.log("sendTimeData => ", error);
            }
        };
    
        self.totalPrintTime = function () {
            try {
                var totalTime = 0;
                self.currentItems().forEach((element) => {
                    totalTime += parseInt(element().timeLeft());
                });
                self.totalEstimatedTime(totalTime);
            } catch (error) {
                console.log("totalPrintTime error => ", error);
            }
        };

        self.toHHMMSS = function (sec_num) {
            try {
                if (!isNaN(sec_num) && sec_num > 0 && !self.terminating()) {
                    var secs = parseInt(sec_num, 10);
                    var hours = Math.floor(secs / 3600);
                    var minutes = Math.floor((secs - hours * 3600) / 60);
                    var seconds = secs - hours * 3600 - minutes * 60;

                    if (hours < 10) {
                        hours = "0" + hours;
                    }
                    if (minutes < 10) {
                        minutes = "0" + minutes;
                    }
                    if (seconds < 10) {
                        seconds = "0" + seconds;
                    }

                    return hours + ":" + minutes + ":" + seconds;
                } else return "-";
            } catch (error) {
                console.log("toHHMMSS error ==> ", error);
            }
        };
        self.queue_item_down = function (index) {
            try {
                if (index < self.currentItems().length - 1) {
                    self.row_change_items("down", index);

                    $.ajax({
                        url: "plugin/speroplugin/queue_item_down?index=" + index,
                        type: "GET",
                        dataType: "json",
                        headers: { "X-Api-Key": UI_API_KEY },
                        success: function (c) {},
                        error: function () {},
                    });
                }
            } catch (error) {
                console.log("queue_item_down error => ", error);
            }
        };
        self.row_change_items = function (type, index) {
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
        self.queue_item_up = function (index) {
            try {
                if (index > 0) {
                    self.row_change_items("up", index);
                    $.ajax({
                        url: "plugin/speroplugin/queue_item_up?index=" + index,
                        type: "GET",
                        dataType: "json",
                        headers: { "X-Api-Key": UI_API_KEY },
                        success: function (c) {},
                        error: function () {},
                    });
                }
            } catch (error) {
                console.log("queue_item_up error => ", error);
            }
        };





        // self.sayhello2= function () {

        //     $('#sayhello2').modal('show');
        //     console.log("ougasdkjasgbdıkasgd")
           

        // };





        self.sayhello = function () {
         
            console.log("Hello!");

        };



        
        self.queueItemDuplicate = function (data) {
            try {
                console.log("asjhkdlbsad")
                $.ajax({
                    url: "plugin/speroplugin/queue_duplicate_item?index=" + data,
                    type: "GET",
                    dataType: "text",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    success: function () {
                        self.reload_plugin();
                    },
                });
            } catch (error) {
                console.log("duplicate item error => ", error);
            }
        };
        self.delete_from_database = function () {
            try {
                if (self.queueId() != undefined || self.queueId() != null);
                $.ajax({
                    url:
                        "plugin/speroplugin/deleteFromDatabase?id=" +
                        self.queueId(),
                    method: "DELETE",
                    dataType: "json",
                    headers: {
                        "X-Api-Key": UI_API_KEY,
                    },
                    data: {},
                    success() {
                        self.send_info("Queue successfully removed.", "info");

                        self.queueName(null);
                        self.queueId(null);
                        self.currentItems(null);

                        self.reload_plugin();
                        setTimeout(function () {
                            self.info_message(null);
                        }, 3000);
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
    
        self.toHHMMSS = function (sec_num) {
            try {
                if (!isNaN(sec_num) && sec_num > 0 && !self.terminating()) {
                    var secs = parseInt(sec_num, 10);
                    var hours = Math.floor(secs / 3600);
                    var minutes = Math.floor((secs - hours * 3600) / 60);
                    var seconds = secs - hours * 3600 - minutes * 60;

                    if (hours < 10) {
                        hours = "0" + hours;
                    }
                    if (minutes < 10) {
                        minutes = "0" + minutes;
                    }
                    if (seconds < 10) {
                        seconds = "0" + seconds;
                    }

                    return hours + ":" + minutes + ":" + seconds;
                } else return "-";
            } catch (error) {
                console.log("toHHMMSS error ==> ", error);
            }
        };
        };
        


    }


    // ko.applyBindings(new SperoViewModel(),document.querySelector("#hay"))



    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
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
        elements: ["#tab_plugin_speroplugin","#settings_plugin_speroplugin"],
    });
});