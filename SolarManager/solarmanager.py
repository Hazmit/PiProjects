import logging
import time
import RPi.GPIO as GPIO
from influxdb import InfluxDBClient

logging.basicConfig(format='%(asctime)s %(message)s', filename='/home/jonj/solarmanager.log', encoding='utf-8', level=logging.INFO)

#Setup pin for turning on relay
relay_pin = 37
relay_state = 0
full_soc = 0

# Set up the GPIO pin
GPIO.setmode(GPIO.BOARD)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.setwarnings(False)

client = InfluxDBClient(host='localhost', port=8086)
client.switch_database('mqtt_solar')

def check_soc():
    global relay_state
    print("Checking State of Charge..", end='')
    
    # Query the measurement
    result = client.query('SELECT "SOC" FROM "mqtt_consumer" ORDER BY time DESC LIMIT 1')
    SOC = result.raw['series'][0]['values'][0][1]
    
    result = client.query('SELECT "Aux1" FROM "mqtt_consumer" ORDER BY time DESC Limit 1')
    Aux = result.raw['series'][0]['values'][0][1]
    
    print('SOC: ', end='')
    print(SOC, end='')
    print('% ', end='')
    print('Aux: ', end='')
    print(Aux)
    
    logging.info("Checking State of Charge.. SOC: " + str(SOC) + "% Aux: " + str(Aux))

    # Check if the value is 0 and turn on the GPIO pin
    if SOC >= 80 and Aux == 1:
        if relay_state == 1:
            return
        GPIO.output(relay_pin, GPIO.LOW)
        relay_state = 1
        print('State of charge is over 80% and Aux is on')
        print('Switching to Solar Power')
        logging.info("State of charge is over 80% and Aux is on, switching to solar power")
    else:
        if relay_state == 0:
            return
        GPIO.output(relay_pin, GPIO.HIGH)
        print('State of charge is less than 80%');
        print('Switching to Grid Power')
        relay_state = 0
        logging.info("State of charge is less than 80% or Aux is off, switching to grid power")

while True:
    try:
        check_soc()
        time.sleep(60)
    except KeyboardInterrupt:
        GPIO.cleanup()
        break

GPIO.cleanup()
