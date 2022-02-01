#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import getTemp
import pressureSwitch
import logging
import time
import argparse
import json
import datetime
import readRFID
import switch
import RPi.GPIO as GPIO
import tempAdjustment

# This area of code is for testing without sending to amazon for easy fault finding.

avg_temp = []

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
   

# Publish to the same topic in a loop forever
loopCount = 0
default = "Coffee Station"
argument = 'both'
topic = "sdk/Coffee/Python"
rfid = "on"
count = 0

while True:
    
    if argument == 'both' or argument == 'publish':

        # This area below will need to be refactored into Main.py to commit changes.
        # CUT AND PASTE BETWEEN HERE.

        message = {}
        dt = datetime.datetime.now()
        temp = getTemp.retun_temp()
        message['PK'] = str(dt)
        message['message'] = default
        message['date'] = dt.strftime("%x")
        rfid = readRFID.read()
        if switch.is_pressed() == 0:
            message['cupID'] = rfid
            message['name'] = "Rogan Tong"        
        if pressureSwitch.return_press() == "pressed":
            on()
            if count >= 20:
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

        # AND HERE

        print(messageJson)
        if argument == 'publish':
            print('Published topic %s: %s\n' % (topic, messageJson))
        loopCount += 1
    time.sleep(.5)
