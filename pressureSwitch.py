def return_press():
    import RPi.GPIO as GPIO
    import time
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.IN)
    # initialise a previous input variable to 0 (Assume no pressure applied)
    prev_input = 0
    try:
        # take a reading
        input = GPIO.input(22)
        # if the last reading was low and this one high, alert us
        if ((not prev_input) and input):
            return "pressed"
        # update previous input
        prev_input = input
    except KeyboardInterrupt:
        pass

