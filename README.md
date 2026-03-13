# Artnet2Tuya

### [DESCRIPTION]
This is a Python Bridge between any ArtNet device like QLC+ / Xlights / GrandMA / etc. and your Tuya-Smart Lights (currently only working for Lights but im working on implementing it with smart plugs too)
It works with all White / RGB Smart bulbs from any brand that uses the Tuya System.

It uses Python to create a bridge, that will listen to Artnet Signals inside your Network and convert that into local Tuya commands.
To make usage as simple as possible, i created a Webinterface with Flask on top of it, so that you dont need to mess inside the code for any changes or new lights.

You can host it either on your Windows or Linux PC or you can even host it on a RaspberryPi (Even on a Pi Zero 1.1 like i did)

Once you have your script set up and running you can just connect to http://127.0.0.1:5000 (from local) or http://yourlocalip:5000 (if you're hosting it on a pi or a different machine)
and you will get an easy webinterface, where you can scan your network for your lights, check which lights you want to use for the artnet bridge, and change the order and (artnet) starting channel for each device. 
The interface will adjust the channel offset automatically and also auto-adjust the channels live as you order them. You can also delete devices or upload a new devices.json file if you have new lights (i will explain what this is for later)
Below that you will get an automatically generated patching table that shows you which channel or fader is for what function as well as the DMX / Artnet Address. Live Changes are possible and the Script will auto-adjust to your changes.

You can also change your desired Universe from that webinterface live.
With this there should never be the need to handle any code or whatever. It can all be managed from within the webinterface.


### [DISCLAIMER]
While this does integrate flawlessly and works quite nice, you should be aware, that this system has its limits given by the smart-light nature of the bulbs you are using. 
So first of all: I will not be responsible for any stability issues, or if that breaks your smart lights. These devices are not really built to handle these kinds of requests and i can't guarantee you that it wont affect their lifetime. 
With that said - There is another very obvious limitation: While it can be used with DMX Systems & Programs - these lights (even addressed locally) are not made for stage lighting purposes. 
So please don't expect them to do any fast Chasers or Response times like on Wired (or Wireless) DMX as you would with proper PAR-Fixtures.


### [USECASES]
So what CAN you use it for?

- You can use it as a mobile DJ for Weddings for example to adjust the lighting (DIY Uplights or your Stage Lights) like change them to different color scenes or turn off / on / white during dinner / speak.
- You can use it for specific (slower) fade-patterns for home partys with your already installed smart lights.
- You can use it as Blinders for smaller stages (especially cool with bright bulbs)
- You can use it for Theatre scenery (To change ambient lighting or create small effects)
- You can use it as Floodlights and whatever doesnt have very fast pace changes.
- Personally i'm using this System in my Christmas Lightshow for Floodlights and to turn off my smart christmas lights before the show without the need of additional timers in the Tuya app. 

All that with lights that are far more cheaper than any stage-lighting Equipment with WirelessDMX.

Im currently working on also implementing Smart-Plugs that will react to the "Power" Channel (0-127 = ON / 128-255 OFF) but havent implemented it yet.
This will give you the ability to turn on and off 230V (or whatever your mains voltage is) Devices from within your DMX console without the need of an expensive DMX-SWITCH or DMX-RELAY
Could be useful for Theatre groups that dont want to spend a fortune just to remotely switch some devices on stage. 
Ofc this yould also be used as kind of a "Main Switch" for Venues for their DMX Lights .. just make Channel 1 your "Master Switch" and it will remotely turn off the power for all Devices from
your DMX-Console. 


# [1 INSTALLTION ON WINDOWS]
You will just need Python 3 to be installed (i tested it on Version 3.10, so thats what i can recommend - you have to test it with other versions if you want to use it)
if you dont have Python installed you can download it at:
https://www.python.org/downloads/

after you installed it just use pip to install the needed libraries:

### :scroll:

> pip install tinytuya, stupidArtnet, flask

The libraries used are: time, json, threading, os, colorsys, datetime, flask, stupidArtnet, tinytuya

Create any directory where you put your files in. The script will need the following files to run:
```
- artnet2tuya.py
- devices.json (see devices.json to see what that is about and how you can get it)
- config.json (will be created automatically for you once you save your first configuration)
``` 

Then you just run the Python script and open the IP-Address shown in the console (it should work with either your localhost address on port 5000 - 127.0.0.1:5000 or your local ip from within
your network like 192.168.178.XX:5000 in your Browser. 

Done :)


# [1 INSTALLTION ON RASPBERRY PI or LINUX]

*optional for using a Raspberry Pi*
To make this into a stadalone System, i would recommend using a RaspberryPi - this doesnt need to be a beefy expensive one - it runs perfectly fine even on a 25$ Raspberry Pi Zero W (1.1)

For this i would recommend installing dietpi on your raspberry this will run just fine with even a 2GB SD-Card and will be very lightweight.
For that just follow this guide:
https://dietpi.com/docs/install/
or use "Pi Installer" - select your board - choose dietpi - install it. make sure to activate SSH.
*optional for using a Raspberry Pi*

Once installed, you go to the Software-Installer and install Python3, Pip3 and an SFTP Server.

after you installed it just use pip to install the needed libraries:

### :scroll:

> pip install tinytuya, stupidArtnet, flask

The libraries used are: time, json, threading, os, colorsys, datetime, flask, stupidArtnet, tinytuya

Open your favorite SFTP software like FileZilla or WINSCP and upload your files to your home directoy.
The script will need the following files to run:

```
- artnet2tuya.py
- devices.json (see devices.json to see what that is about and how you can get it)
- config.json (will be created automatically for you once you save your first configuration)
``` 

Then you just run the Python script and open the IP-Address shown in the console
(it should be something like 192.168.178.XX:5000) in your Browser. 

Done :)


# [2 devices.json]
So in order for you Smart-Devices to work locally you need to get your "Local Keys" for your Devices. (It would be a pain in the bum to use it via the cloud)
So to get these there are 2 Ways:

## 1 (the official way):

You need to get an API Key from the Tuya IoT Cloud (this is completely free at the time of writing this)
and i will save myself the work to describe this here in detail, as there is already a great guide on this you can follow on the TinyTuya github documentation:
https://github.com/jasonacox/tinytuya
just follow this guide and then run 
python -m tinytuya wizard
in your console. this will create the devices.json file for you in your User directory (C:/Users/Admin/)


just copy it next to your scripts directory if you are on windows or upload it via sftp if you're on a raspberry.
If your script is already running you can also upload the file via the webinterface (this will save it next to the script for you).

## 2 (the hacky way):

You can also follow this Video to get your keys. You will either need a rooted Android device for this of the BlueStacks emulator.
There is a great video from Mark Watt Tech, so i will just link this here if you want to do it that way (which is also more future-proof):
https://www.youtube.com/watch?v=YKvGYXw-_cE

either way you will end up with your devices.json file which contains your Local Keys.


# [3 CONFIGURATION]
Once you have your devices.json in the same directory you are basically done. Just run the script and connect to the Webinterface.

From there you just click the "Scan Network" button and all your available Smart-Devices should appear in the list (They have to be online for the Scan, so flip your lightswitch on and plug the stuff you want to use in)

Then:

- Use the 3 Stripes on the left to Drag&Drop your devices into the desired order (this will auto-adjust the channels for you but you can also manually set your channels)
- tick the checkbox for the lights in your network that you want to use. They will automatically have the Name you chose in your Tuya App on setup. you will also see the IP-Address and Local Key as well as the version if you need it.
- then you select which devices are able to RGB and which dont (this shouldnt be needed in the current version, but to be safe just set this correctly)
- and hit "Save & Apply Changes"...

this will create a config.json file with your settings in the same directory as the script, so it will be remembered for the next time (even after restart)...
If a config file exists it will always load from that - to clear it just upload your devices.json again. this will backup and replace your old devices.json and config.json files. 
You can also delete devices from that list, that you dont need. 

Nice! You're Done! Now you should be able to control your lights via Artnet from your Software (like QLC) - make sure that you're actually sending on the correct interface to your local network. 
At the bottom there will also be a Patching Guide, so you can setup your Software easily and see which channel is for which function. 
Each Bulb / Device will use 6 DMX-Addresses.


## Happy controlling your lights and have fun :)


_coded with :purple_heart: by_ **Fabian Rehme**
