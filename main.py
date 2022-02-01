#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os, sys
import getTemp
import pressureSwitch
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json
import datetime
import readRFID
import switch
import RPi.GPIO as GPIO
import tempAdjustment

avg_temp = []
loopCount = 0
count = 0
incri = 0
cupPlaced = 0
cupCount = 0
currentDay = datetime.datetime.now().strftime("%x")

def on():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(19, GPIO.OUT)
    GPIO.output(19, GPIO.HIGH)


def off():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(19, GPIO.OUT)
    GPIO.output(19, GPIO.LOW)


def average(tmp):
    
    if len(avg_temp) >= 100:
        avg_temp.pop(0)
    avg_temp.append(tmp)
    avg = sum(avg_temp)/len(avg_temp)
    return round(avg, 2)


# Running AWS go to command line.
# cd to connect_device_package
# chmod +x start.sh
# ./start.sh

AllowedActions = ['both', 'publish', 'subscribe']

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="Coffee Station",
                    help="Message to publish")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
port = args.port
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Port defaults
if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
    port = 443
if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
    port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
# message['message'] = args.message

try:
    while True:
        if args.mode == 'both' or args.mode == 'publish':
            dt = datetime.datetime.now()
            temp = getTemp.retun_temp()
            average(temp)
            if switch.is_pressed() == 0:
                cupPlaced = 1
            if incri >= 200:
                message = {}
                message['PK'] = str(dt)
                message['message'] = args.message
                message['date'] = dt.strftime("%x")
                rfid = readRFID.read()
                if cupPlaced == 1:
                    message['cupID'] = rfid
                    message['name'] = "Rogan Tong" 
                    cupPlaced = 0
                    if currentDay == dt.strftime("%x"):
                        cupCount += 1
                        message['totalCups'] = cupCount 
                    else:
                        currentDay = dt.strftime("%x")
                        cupCount += 1
                        message['totalCups'] = cupCount
                    if int(time.strftime('%H')) >= 14:
                        message['toLate'] = "True"     
                if pressureSwitch.return_press() == "pressed":
                    on()
                    if count >= 2:
                        message['temp'] = tempAdjustment.adjusted(ambient, temp)
                    else:
                        message['temp'] = 50
                        count += 1
                    message['button'] = pressureSwitch.return_press()
                else:
                    off()
                    count = 0
                    ambient = average(temp)
                    message['ambient'] = ambient
                message['sequence'] = loopCount
                messageJson = json.dumps(message)
                myAWSIoTMQTTClient.publish(topic, messageJson, 1)
                if args.mode == 'publish':
                    print('Published topic %s: %s\n' % (topic, messageJson))
                loopCount += 1
                incri = 0
            else:
                incri += 1
        time.sleep(0.1) 
finally:
    GPIO.cleanup()
       