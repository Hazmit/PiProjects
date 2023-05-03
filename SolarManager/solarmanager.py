import requests
import logging
import time
import RPi.GPIO as GPIO
from influxdb import InfluxDBClient

logging.basicConfig(format='%(asctime)s %(message)s', filename='/home/jonj/solarmanager.log', encoding='utf-8', level=logging.INFO)

last_push = 0

#Setup pin for turning on relay
relay_pin = 7
relay_state = 0

# Set up the GPIO pin
GPIO.setmode(GPIO.BOARD)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.setwarnings(False)

client = InfluxDBClient(host='localhost', port=8086)
client.switch_database('mqtt_solar')

def send_push(message):
    global last_push
    pushover_url = 'https://api.pushover.net/1/messages.json'
    pushover_token = 'akhnkrwuo2z4faymw24oimt7zdp9v8'
    pushover_user = 'uMVcEZGPGQ37gbyCsRyChW96HBEw5A'
    
    payload = {'token': pushover_token, 'user': pushover_user, 'message': message, 'priority': 1}
    time_since_push = int(time.time())-last_push
    if time_since_push > 60:
        print('time since last push ' + str(time_since_push))
        response = requests.post(pushover_url, data=payload)
    last_push = int(time.time())

def switch_to_grid(reason):
    global relay_state
    GPIO.output(relay_pin, GPIO.LOW)
    if relay_state == 0:
        return
    relay_state = 0
    send_push('Switching to grid power, ' + reason)
    logging.info('Switching to grid power, ' + reason)
    return

def switch_to_solar(reason):
    global relay_state
    GPIO.output(relay_pin, GPIO.HIGH)
    if relay_state == 1:
        return
    relay_state = 1
    send_push('Switching to Solar Power, ' + reason)
    logging.info('Switching to Solar Power, ' + reason)
    return

def get_metric(metric):
    result = client.query('SELECT "' + metric + '" FROM "mqtt_consumer" ORDER BY time DESC LIMIT 1')
    metric_result = result.raw['series'][0]['values'][0][1]
    return metric_result

def check_soc():
    global relay_state

    SOC = get_metric('SOC')
    Aux = get_metric('Aux1')
    bvolts = get_metric('BatVoltage')

    logging.info("Check State of Charge.. SOC: " + str(SOC) + "% Aux: " + str(Aux) + " BatVoltage: " + str(bvolts))

    # Check if the value is 0 and turn on the GPIO pin
    if SOC >= 80 and Aux == 'True' and bvolts > 12.3:
        message = 'State of charge is ' + str(SOC) + '% and Aux is ' + str(Aux) +', Bat Voltage is ' + str(bvolts)
        switch_to_solar(message)
    elif bvolts < 12.3:
        bvolts = get_metric('BatVoltage')
        message = 'Battery Voltage is too low! Bvolts: ' + str(bvolts)
        switch_to_grid(message)
    elif Aux == 'False':
        switch_to_grid('Aux is off')
    elif SOC < 80:
        switch_to_grid('State of Charge is less than 80%, currently ' + str(SOC) + '%')
    else:
        switch_to_grid('Can not determine state of system. SOC: ' + str(SOC) + ' Aux: ' + str(Aux) + ' Bat Voltage: ' + str(bvolts))

logging.info('Starting up Solar Manager')
send_push('Starting up Solar Manager... Sleeping 60 seconds')
switch_to_grid('Startup Grid Default')

while True:
    try:
        time.sleep(60)
        check_soc()
    except KeyboardInterrupt:
        GPIO.cleanup()
        send_push('Shutting down Solar Manager')
        logging.info('Shutting down Solar Manager')
        break

GPIO.cleanup()
