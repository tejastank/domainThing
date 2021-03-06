#!/usr/bin/env python
import re
import socket
import os.path
import os
import sys
from pprint import pprint as pp

import json
from datetime import datetime, timedelta
import logging as logger
import time
import configparser 
from multiprocessing import Process, current_process, active_children
from mqlightQueue import mqlightQueue

class domainReader():


    def __init__(self, domainType, doStats=0):
        self.start = datetime.now()
        configFile = './config.cfg'
        config = configparser.ConfigParser()
        config.read(configFile)

        self.packetSize = config.getint('domainParser','packetSize')
        logger.info("domainReader Starting up")

        # clientName = 'parser_' + str(os.getpid())
        clientName = 'parser_0000' 
        self.q = mqlightQueue(config,clientName)


        self.regex = re.compile(config.get(domainType,'regex'))
        self.path = config.get(domainType,'path')
        self.doStats = doStats
        self.stats = {
            'domains' : 0,
            'startTime': 0,
            'endTime' : 0,
            'runningSeconds': 0,
            'avg': []
        }



    def __exit__(self):
        logger.info("domainReader Shutting down")
        self.q.close()

    def getZoneFiles(self, startLine=0):
        logger.info("Looing in %s" % (self.path))
        for root, dirs, files in os.walk(self.path, topdown=True):
            pp(files)
            for name in files:
                logger.info("Found FILE %s" % name)
                self.queueDomains(self.regex,os.path.join(root, name), startLine)
        # self.q.close()
        if self.doStats:
            self.printStats()
            self.q.close()



    def queueDomains(self,regex, filename, startLine):
        lastZone = ''
        lineNumber = 0
        workQueue = []
        queueLength = 0
        domainCount = 0
        f = open(filename,'r')
        # Verisign zones don't end with the TLD
        # we can figure this out from the filename though
        start = datetime.now()
        self.stats['startTime'] = start
        tld = re.search("\S+\/(\S+)\.zone$", filename)
        # of course .org zone has to be difficult
        orgzone = './zones/org/org.zone'
        if filename == orgzone:
            tld = None
        for line in f:
            lineNumber = lineNumber + 1
            if lineNumber < startLine:
                continue
            zone = regex.match(line)
            if zone:
                thisZone = zone.group(1)
                if tld:
                    thisZone = thisZone + "." + tld.group(1)

                # Most zones have multiple entries, we only care abotu the first
                if thisZone == lastZone:
                    continue
                
                lastZone = thisZone
                nownow = datetime.now()

                zoneObject = {
                    'created': nownow.isoformat(),
                    'domain' : lastZone,
                    'domainFullZone': zone.group(0)
                }
                workQueue.append(zoneObject)
                queueLength = queueLength + 1
                domainCount = domainCount + 1

            if  queueLength >= self.packetSize:
                self.uploadQueue(workQueue)
                logger.info("%s - %s" % (lineNumber, thisZone))
                queueLength = 0
                workQueue = []
                # Sleeping to not overload queue
                # need to replace with something more aware


        self.uploadQueue(workQueue)
        nownow = datetime.now()

        if self.doStats:
            elapsed = nownow - start
            if (elapsed.total_seconds() > 0):
                ds = round(domainCount / elapsed.total_seconds())
            else:
                ds = 0
            self.stats['domains'] = self.stats['domains'] + domainCount
            self.stats['runningSeconds'] =self.stats['runningSeconds'] + elapsed.total_seconds()
            self.stats['avg'].append(ds)
            self.stats['endTime'] = nownow.isoformat()
        logger.info("%s - Finished with %s" % (nownow.isoformat(),filename))


    def uploadQueue(self, workQueue):
        nownow = datetime.now()
        message = json.dumps(workQueue)
        self.q.sendMessage(message,'domain-queue')

    def printStats(self):
        logger.info("Start: %s" % (self.stats['startTime']))
        logger.info("Domains: %s" % (self.stats['domains']))
        logger.info("runningSeconds: %s" % (self.stats['runningSeconds']))
        logger.info("Average domains/s %s" % (self.stats['avg']))
        logger.info("End: %s" % (self.stats['endTime']))


if __name__ == "__main__":
    logger.basicConfig(filename="parser.log", format='%(asctime)s, %(message)s' ,level=logger.INFO)


    configFile = './config.cfg'
    config = configparser.ConfigParser()
    config.read(configFile)
    ready = config.getint('domainParser','ready')
    while not ready:
        logger.info("Not ready, sleeping for 60")
        time.sleep(60)
        config.read(configFile)
        ready = config.getint('domainParser','ready')

    try:

        # This gives each process its own connection to rabbit
        # so that they don't clobber each other. Not doing this causes
        # rabbit to disconnect the thread.
        domainReadera = domainReader('verisign')
        domainReaderb = domainReader('icaan')
        domainReaderc = domainReader('org')

        regexIcaan = domainReadera.regexIcaan
        regexVerisign = domainReadera.regexVerisign
        regexORG = domainReadera.regexORG
        a = Process(target=domainReadera.getZoneFiles).start()
        b = Process(target=domainReaderb.getZoneFiles).start()
        c = Process(target=domainReaderc.getZoneFiles).start()
        active_children()

    except BaseException as e:
        logger.error("Exiting due to exception")
        logger.exception(str(e))



