import time
import win32gui
import subprocess
import os
import sys
import SysTrayIcon as tray
import IdleMiner_Helpers as helpers
import _thread
import yaml

# -- Requirements --
# Python 3
# Non-Standard Dependencies: uptime, pypiwin32, pyyaml

## TODO ##
## ✓ Add a tray icon with options for running out of idle mode and changing/removing idle timer
## ✓ Open mining window(s) in background or not at all (remove printing of sdout?)
## ✓ Automatically close window opened by batch file on startup
## ✓ Add config file that stores user-changed settings (YAML?)
## ✓ Change tray double-click functionality to start/stop mining
## ✓ Update icon when mining auto-starts from idle timer
## - Generalize command in Miner class to accomodate different mining programs
## - Prevent multiple instances from running (https://raspberrypi.stackexchange.com/questions/22005/how-to-prevent-python-script-from-running-more-than-once)
## - Add logging
## - Add readout in tray menu showing current hashrate
## - Implement error checking to stop program if miner file not found or mining can't start
## - Fix miner shutdown. Not shutting down sometimes.

## Behavior ##
## Miner will begin on Windows startup and run in tray. On startup, idle timer will be active.
## If mining is manually started from tray, timer will be suspended until mining is manually stopped from tray.
## Mining is manually started from tray on double left-click. Menu opens on right-click. Left-click is disabled.

# ####################### #
# #### CONFIGURATION #### #

# Default options
IDLE_TIMER = 1*60  # Run after this many seconds idle

# Load config file
try:
	with open("IdleMiner_Config.yaml", 'r') as ymlfile:
		config = yaml.load(ymlfile)
		ymlfile.close()
	
	POOL_SERVER = config['POOL_SERVER']
	USER_ADDRESS = config['USER_ADDRESS']
	EXTRA_OPTIONS = []
	for opt in config['EXTRA_OPTIONS']:
		EXTRA_OPTIONS.append( '--' + opt )
		EXTRA_OPTIONS.append( str(config['EXTRA_OPTIONS'][opt]) )
	
	MINER_PATH = config['MINER_PATH']
	
	IDLE_TIMER = config['IDLE_TIMER']
	
	
except FileNotFoundError:
	print("Config file not found.")
except KeyError:
	print("Config file not formatted properly.")

	
def updateConfig_IDLE_TIMER(n):
	with open(os.path.abspath("IdleMiner_Config.yaml"), 'r') as ymlfile:
		config = yaml.load(ymlfile)
		ymlfile.close()
	
	if (5 <= round(n) <= 60*60):
		config["IDLE_TIMER"] = round(n)
		
		with open(os.path.abspath("IdleMiner_Config.yaml"), "w") as ymlfile:
			yaml.dump(config, ymlfile)
			ymlfile.close()
	
# ####################### #
# ####################### #

# Timer options
timer_options = [1, 5, 10, 15, 30]

# Save main script working directory
dir_Script = os.getcwd()

class Miner():
	def __init__(self, path_to_miner):
		self.isMining = False
		self.timerOverride = False
		self.timerActive = True
		self.path_to_miner = path_to_miner
		
	def startMining(self):
		cmd = [self.path_to_miner, '--server', POOL_SERVER, '--user', USER_ADDRESS] + EXTRA_OPTIONS
		
		# Prepare options for window hiding. See: https://docs.python.org/3/library/subprocess.html#subprocess.STARTUPINFO
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		
		self.miner_process = subprocess.Popen(cmd, startupinfo=startupinfo)
		self.isMining = True
		
	def stopMining(self):
		self.isMining = False
		self.miner_process.terminate()
		print("\n-- System no longer idle. Mining suspended. --\n")

# Instantiate Miner object
miner = Miner(MINER_PATH)

# Setup system tray icon
icon_on = os.path.join(dir_Script, "IdleMiner_iconOn.ico")
icon_off = os.path.join(dir_Script, "IdleMiner_iconOff.ico")
icon_check = os.path.join(dir_Script, "IdleMiner_iconCheck.ico")
hover_text = "IdleMiner"
toggleMiner_text = 'Start Mining'
toggleTimer_text = 'Disable Timer'
T_hwnd = 0
T_msgindex = 0

# Menu handler functions
def changeTimer(sysTrayIcon, id):
	opt_text = sysTrayIcon.find_menu_option(sysTrayIcon.menu_options, id)  # Get text of selected menu option
	opt_time = [int(opt_text) for opt_text in str.split(opt_text) if opt_text.isdigit()][0]  # Extract number from option text

	# Update icons
	global menu_changeTimer
	menu_changeTimer_list = helpers.tupleToList(menu_changeTimer)  # Convert to list for editing
	
	for idx, opt in enumerate(menu_changeTimer_list[2]):
		if opt[0] == opt_text:
			menu_changeTimer_list[2][idx][1] = icon_check
		else:
			menu_changeTimer_list[2][idx][1] = None
	
	menu_changeTimer = helpers.listToTuple(menu_changeTimer_list)  # Convert back to tuple
	
	
	menu_options = (menu_toggleMiner, menu_toggleTimer, menu_changeTimer)
	# Refresh menu items
	sysTrayIcon.update_menu_options(menu_options)
	
	# Change timer
	global IDLE_TIMER
	IDLE_TIMER = opt_time*60
	updateConfig_IDLE_TIMER(IDLE_TIMER)
	
def toggleMiner(sysTrayIcon, id):
	if miner.isMining:
		toggleMiner_text = 'Start Mining'
		sysTrayIcon.icon = icon_off
		miner.timerOverride = False
		miner.stopMining()
	else:
		toggleMiner_text = 'Stop Mining'
		sysTrayIcon.icon = icon_on
		miner.timerOverride = True
		miner.startMining()
	
	# Update icon
	sysTrayIcon.refresh_icon()
		
	# Update menu item text
	menu_toggleMiner = (toggleMiner_text, None, toggleMiner)
	menu_options = (menu_toggleMiner, menu_toggleTimer, menu_changeTimer)
	
	# Refresh menu items
	sysTrayIcon.update_menu_options(menu_options)
	

def toggleTimer(sysTrayIcon, id):
	if miner.timerActive:
		toggleTimer_text = 'Enable Timer'
		miner.timerActive = False
	else:
		toggleTimer_text = 'Disable Timer'
		miner.timerActive = True
	
	# Update menu item text
	menu_toggleTimer = (toggleTimer_text, None, toggleTimer)
	menu_options = (menu_toggleMiner, menu_toggleTimer, menu_changeTimer)
	
	# Refresh menu items
	sysTrayIcon.update_menu_options(menu_options)
	
def bye(sysTrayIcon): 
	print ("Quitting...")

	
# Menu options
menu_toggleMiner = (toggleMiner_text, None, toggleMiner)
menu_toggleTimer = (toggleTimer_text, None, toggleTimer)

menu_changeTimer = ['Change Timer', None, []]
for t in timer_options:
	icon_or_none = None
	if(t*60==IDLE_TIMER):
		icon_or_none = icon_check
	if(t==1): 
		menu_changeTimer[2].append([str(t) + ' minute', icon_or_none, changeTimer])
	else: 
		menu_changeTimer[2].append([str(t) + ' minutes', icon_or_none, changeTimer])
menu_changeTimer = helpers.listToTuple(menu_changeTimer)

menu_options = (menu_toggleMiner, menu_toggleTimer, menu_changeTimer)

def get_tray_data(sysTrayIcon):
	# Used to get (initial) information from SysTrayIcon object, i.e. hwnd window ID for sending messages.
	global T_hwnd
	global T_msgindex
	T_hwnd = sysTrayIcon.hwnd  # Window ID (to send messages)
	T_msgindex = sysTrayIcon.FIRST_ID + sysTrayIcon.OFFSET + 1  # ID of custom message trigger
	
	
# Create a separate thread to handle tray icon
def trayThread():
	# Create tray icon (this object will block the thread it runs in)
	tray.SysTrayIcon(icon_off, hover_text, menu_options, on_quit=bye, default_menu_index=0, 
					 window_class_name="IdleMiner", data_feedback=get_tray_data, extra_icon_paths=[icon_on, icon_off])

try:
	_thread.start_new_thread( trayThread, () )
except:
	print("Error: unable to start thread")
	
if __name__ == "__main__":
	
	while True:
	
		if (miner.timerActive == True and miner.timerOverride == False):
		
			if (helpers.getIdleTime() >= IDLE_TIMER and miner.isMining == False):
				miner.startMining()
				
				# Post custom message to icon window, triggering icon update function in SysTrayIcon.
				# The third argument is the index of the icon in the provided extra_icon_paths list.
				win32gui.PostMessage(T_hwnd, T_msgindex, 0)
				
			if (helpers.getIdleTime() < (IDLE_TIMER/2) and miner.isMining == True):
				miner.stopMining()
				
				# Post custom message to icon window, triggering icon update function in SysTrayIcon.
				# The third argument is the index of the icon in the provided extra_icon_paths list.
				win32gui.PostMessage(T_hwnd, T_msgindex, 1)
				
		time.sleep(1)
		