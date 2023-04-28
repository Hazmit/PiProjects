import RPi.GPIO as GPIO
import requests
import time

# Set up GPIO pin
sensor_pin = 37
GPIO.setmode(GPIO.BOARD)
GPIO.setup(sensor_pin, GPIO.IN)

tank_state = 'Startup'

def send_push(message):
    # Set up Pushover API details
    pushover_url = 'https://api.pushover.net/1/messages.json'
    pushover_token = 'ab7uubduu3s6944s2vm7nte8op92m2'
    pushover_user = 'uMVcEZGPGQ37gbyCsRyChW96HBEw5A'

    payload = {'token': pushover_token, 'user': pushover_user, 'message': message}
    response = requests.post(pushover_url, data=payload)

# Infinite loop to monitor the sensor
try:
    while True:
        current_state = GPIO.input(sensor_pin)

        if tank_state != current_state:
            if current_state == GPIO.HIGH:
                message = 'Water Tank is low!'

            if current_state == GPIO.LOW:
                message = 'Water Tank is no longer low!'
            print(message)
            send_push(message)
            
        tank_state = current_state
        time.sleep(10)
except KeyboardInterrupt:
    print('Interupted')
