import json
import urllib2
import base64
import sys
import RPi.GPIO as GPIO
import time
import os
import json
from pprint import pprint

config = {}

def readConf(filename):
	file = open(filename, 'r')
	config = json.load(file)
	file.close()
	return config

def getJsonRemote(host,port,username,password,method,parameters):
    # First we build the URL we're going to talk to
    url = 'http://%s:%s/jsonrpc' %(host, port)
    # Next we'll build out the Data to be sent
    values ={}
    values["jsonrpc"] = "2.0"
    values["method"] = method
    # This fork handles instances where no parameters are specified
    if parameters:
        values["params"] = parameters
    values["id"] = "1"
    headers = {"Content-Type":"application/json",}
    # Format the data
    data = json.dumps(values)
    # Now we're just about ready to actually initiate the connection
    req = urllib2.Request(url, data, headers)
    # This fork kicks in only if both a username & password are provided
    if username and password:
        # This properly formats the provided username & password and adds them to the request header
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)
    # Now we're ready to talk to Kody
    # I wrapped this up in a try: statement to allow for graceful error handling
    try:
        response = urllib2.urlopen(req)
        response = response.read()
        response = json.loads(response)
        # A lot of the Kodi responses include the value "result", which lets you know how your call went
        # This logic fork grabs the value of "result" if one is present, and then returns that.
        # Note, if no "result" is included in the response from Kodi, the JSON response is returned instead.
        # You can then print out the whole thing, or pull info you want for further processing or additional calls.
        if 'result' in response:
            response = response['result']
    # This error handling is specifically to catch HTTP errors and connection errors
    except urllib2.URLError as e:
        # In the event of an error, I am making the output begin with "ERROR " first, to allow for easy scripting.
        # You will get a couple different kinds of error messages in here, so I needed a consistent error condition to check for.
        response = 'ERROR '+str(e.reason)
    return response

def kodiRemoteControl(action):
	print getJsonRemote(config["kodi"]["ip"], config["kodi"]["port"], config["kodi"]["username"], config["kodi"]["password"], action["method"], action["parameters"])

def kodiInit():
	for action in config["kodi"]["init"]:
		kodiRemoteControl(action) 

# Our function on what to do when the button is pressed
def onClick(channel):
	index = config["gpio"].index(channel)
	kodiRemoteControl(config["kodi"]["actions"][index])

config = readConf(sys.argv[1])

GPIO.setmode(GPIO.BOARD)
for pin in config["gpio"]:
	GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	# Add our function to execute when the button pressed event happens
	GPIO.add_event_detect(pin, GPIO.FALLING, callback = onClick, bouncetime = 2000)

kodiInit()
# Now wait!
while 1:
	time.sleep(1)
