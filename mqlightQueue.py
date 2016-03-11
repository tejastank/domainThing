import threading
import mqlight
import configparser 
import os
import logging as logger

class mqlightQueue():

    def __init__(self, config, clientName):

        self.options = {
            'qos': mqlight.QOS_AT_LEAST_ONCE,
            'ttl': 999999
        }
        self.ready = False
        mqService = "amqps://hdaa7cZMddEc:ke=6.YeW(6sh@mqlightprod-ag-00002a.services.dal.bluemix.net:2906"
        mqClient = clientName
        self.client = mqlight.Client(
            service=mqService,
            client_id=mqClient,
            on_state_changed=self.stateChanged,
            on_started=self.started

        )
        self.lock = threading.RLock()
        self.thread = threading.Event()

    def __exit__(self):
        logger.info("Shutting mq down")
        self.close()

    def started(self, client):
        logger.info("Ready to go!")
        self.ready=True


    def sendMessage(self, message, topic):
        with self.lock:
            self.thread.clear()
            logger.info("%s - %s" % (topic,message[0:45]))

            if self.client.send(topic=topic,data=message,options=self.options,on_sent=self.on_sent):
                return True
            else:
                self.thread.wait()

    def close(self):
        logger.info("Closing the connection")
        self.client.stop()
        # self.thread.exit()

    def stateChanged(self, client, state, message='None'):
        if state == mqlight.ERROR:
            logger.info("Hit an error %s" % message)
            self.close()

        elif state == mqlight.DRAIN:
            self.thread.set()
        else:
            logger.info("State changed to %s" % state)


    def on_sent(self, error, topic, data, options):
        if error:
            logger.info("ERROR: %s" % error)
            return False
        else:
            logger.info("Sent to %s successfully" % topic)
            return True


    def subscribe(self,topic, callback):
        myOptions = self.options
        myOptions['auto_confirm'] = False
        myOptions['credit'] = 1
        self.client.subscribe(
            topic_pattern = topic,
            share = None,
            options = self.options,
            on_message=callback
        )
        logger.info("Subscribed to %s" % topic)


