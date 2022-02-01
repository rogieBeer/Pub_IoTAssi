import RPi.GPIO as GPIO


def is_pressed():
    count = 0
    while True:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(21,GPIO.IN)
        inputval = GPIO.input(21)
        if inputval == 0:
            return 0
        if count == 10:
            return 1
        count += 1


