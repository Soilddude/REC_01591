import RPi.GPIO as GPIO
import re
import serial  # for GPS module
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import threading
import logging
from threading import Lock

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Water level sensors setup (assuming GPIO17 and GPIO27)
water_level_sensors = [17, 27]
for sensor in water_level_sensors:
    GPIO.setup(sensor, GPIO.IN)

# Buzzer setup (assuming GPIO22)
buzzer = 22
GPIO.setup(buzzer, GPIO.OUT)
GPIO.output(buzzer, GPIO.LOW)

geolocator = Nominatim(user_agent="geoapiExercises")

def get_location_name(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True, language='en')
        return location.address if location else "Unknown location"
    except GeocoderTimedOut:
        logger.error("GeocoderTimedOut: retrying...")
        return get_location_name(lat, lon)

def sound_buzzer():
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(1)  # Buzzer on for 1 second
    GPIO.output(buzzer, GPIO.LOW)

gps = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=0.5)

# GPS reading and location name updating
location_name = "Unknown location"
location_lock = Lock()

def update_location(lat, lon):
    global location_name
    try:
        location_name_temp = get_location_name(lat, lon)
        with location_lock:  # Ensure thread-safe update of the global variable
            location_name = location_name_temp
    except Exception as e:
        logger.error(f"Failed to update location: {e}")

def gps_thread_function():
    while True:
        gps_data = gps.readline().decode('utf-8', errors='ignore')
        if "$GPGGA" in gps_data:
            lat, lon = parse_gps(gps_data)
            if lat != "0" and lon != "0":
                update_location(lat, lon)
        time.sleep(1)

def parse_gps(data):
    if "$GPGGA" in data:  # Check if it's a GPGGA sentence
        parts = data.split(',')
        if len(parts) > 5:  # Ensure it has enough parts
            # Extract and format latitude
            latitude = float(parts[2][:2]) + float(parts[2][2:]) / 60
            if parts[3] == 'S':
                latitude *= -1
            # Extract and format longitude
            longitude = float(parts[4][:3]) + float(parts[4][3:]) / 60
            if parts[5] == 'W':
                longitude *= -1
            return str(latitude), str(longitude)
    return "0", "0"  # This line must be aligned with the starting if of the block

gps_thread = threading.Thread(target=gps_thread_function)
gps_thread.daemon = True  # Daemonize thread
gps_thread.start()

myMQTTClient = AWSIoTMQTTClient("uniqueID0120")
# Configure the MQTT Client as previously
# Assuming your credential files are in the same directory as your script.
# Update the paths if your files are located elsewhere.
rootCAPath = "AMAZONROOTCA PATH"
certificatePath = "CERTIFICATE PATH"
privateKeyPath = "PRIVATEKEY PATH"

myMQTTClient = AWSIoTMQTTClient("YOUR CLIENT ID")
myMQTTClient.configureEndpoint("AWS IoT URL", 8883)
myMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# The rest of the configuration...
myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myMQTTClient.connect()


try:
    while True:
        message = {
            'sensor_data': [],
            'location': None
        }
        water_detected = False

        for index, sensor in enumerate(water_level_sensors):
            sensor_status = GPIO.input(sensor)
            message['sensor_data'].append({'sensor_id': index + 1, 'status': sensor_status})
            if sensor_status == GPIO.HIGH:
                water_detected = True

        if water_detected:
            sound_buzzer()

        with location_lock:  # Ensure thread-safe read of the location name
            message['location'] = location_name

        print(f"Publishing message: {json.dumps(message)}")    

        myMQTTClient.publish("topic/flood_alert", json.dumps(message), 0)

        time.sleep(60)  # Delay before the next send

except KeyboardInterrupt:
    GPIO.cleanup()
    gps.close()

except Exception as e:
    logger.error(f"An error occurred: {e}")
    GPIO.cleanup()
    gps.close()
