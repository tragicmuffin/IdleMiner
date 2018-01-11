# Module     : SysTrayIcon.py
# Synopsis   : Windows System tray icon.
# Programmer : Simon Brunning - simon@brunningonline.net
# Date       : 11 April 2005 (20 December 2017)
# Notes      : Based on (i.e. ripped off from) Mark Hammond's
#              win32gui_taskbar.py and win32gui_menu.py demos from PyWin32
# --- modified and converted to Python3 by Jesse Williams ---

# Info on win32con and win32gui messages: https://msdn.microsoft.com/en-us/library/windows/desktop/ms644927(v=vs.85).aspx#system_defined

import os
import sys
import win32api
import win32con
import win32gui_struct
import win32ui
import time

try:
	import winxpgui as win32gui
except ImportError:
	import win32gui

class SysTrayIcon(object):
	QUIT = 'QUIT'
	SPECIAL_ACTIONS = [QUIT]
	
	FIRST_ID = 1024  	# Starting ID of user-definable block. Actions associated with menu options will be registered to IDs starting here.
	OFFSET = 20  		# Offset (from FIRST_ID) to begin custom actions not triggered by menu options.
	
	def __init__(self,
				 icon,
				 hover_text,
				 menu_options,
				 on_quit=None,
				 default_menu_index=None,
				 window_class_name=None,
				 data_feedback=None,
				 extra_icon_paths=None):
		
		self.icon = icon
		self.hover_text = hover_text
		self.on_quit = on_quit
		self.extra_icon_paths = extra_icon_paths
		
		menu_options = menu_options + (('Quit', None, self.QUIT),)
		self._next_action_id = self.FIRST_ID
		self.menu_actions_by_id = set()
		self.menu_options = self._add_ids_to_menu_options(list(menu_options))
		self.menu_actions_by_id = dict(self.menu_actions_by_id)
		del self._next_action_id
		
		
		self.default_menu_index = (default_menu_index or 0)
		self.window_class_name = window_class_name or "SysTrayIconPy"
		
		# This dict sets up a coorespondance from received win32gui messages (in the form of standard integer constants as defined in win32con)
		#   and the desired action to take upon receiving the message.
		#   WM_USER is the beginning of a reserved block of user-definable messages.
		message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
					   win32con.WM_DESTROY: self.destroy,
					   win32con.WM_COMMAND: self.command,
					   win32con.WM_USER+self.OFFSET : self.notify,
					   win32con.WM_USER+self.OFFSET+1 : self.change_icon,}
		# Register the Window class.
		window_class = win32gui.WNDCLASS()
		hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
		window_class.lpszClassName = self.window_class_name
		window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
		window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
		window_class.hbrBackground = win32con.COLOR_WINDOW
		window_class.lpfnWndProc = message_map # could also specify a wndproc.
		classAtom = win32gui.RegisterClass(window_class)
		# Create the Window.
		style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
		self.hwnd = win32gui.CreateWindow(classAtom,
										  self.window_class_name,
										  style,
										  0,
										  0,
										  win32con.CW_USEDEFAULT,
										  win32con.CW_USEDEFAULT,
										  0,
										  0,
										  hinst,
										  None)
		win32gui.UpdateWindow(self.hwnd)
		self.notify_id = None
		self.refresh_icon()
		
		# Send data to calling script. Used to retrieve hwnd in order to send messages.
		if(data_feedback): data_feedback(self)
		
		# Runs the main loop that waits for messages in this thread
		win32gui.PumpMessages()
		
	def _add_ids_to_menu_options(self, menu_options):
		result = []
		for menu_option in menu_options:
			option_text, option_icon, option_action = menu_option
			if callable(option_action) or option_action in self.SPECIAL_ACTIONS: # This will be called if a function is given
				self.menu_actions_by_id.add((self._next_action_id, option_action))
				result.append(menu_option + (self._next_action_id,))
			elif non_string_iterable(option_action): # This will be called when function is replaced by submenu
				result.append((option_text,
							   option_icon,
							   self._add_ids_to_menu_options(option_action), # recursion
							   self._next_action_id))
			else:
				print ('Unknown item', option_text, option_icon, option_action)
			self._next_action_id += 1
		return result
	
	
	def find_menu_option(self, menu_options, id):
		# A function to recursively parse through all submenus in menu_options looking for a matching 'id'
		for menu_option in menu_options:
			_, _, option_action, option_id = menu_option
			if callable(option_action) or option_action in self.SPECIAL_ACTIONS: # This will be called if a function is given
				if option_id == id:
					return menu_option[0]
			elif non_string_iterable(option_action): # This will be called when function is replaced by submenu
				return self.find_menu_option(option_action, id) # Search the "action" which is a list of submenu options
		print("find_menu_option: ID not found.")
		
		
	def refresh_icon(self):
		# Try and find a custom icon
		hinst = win32gui.GetModuleHandle(None)
		if os.path.isfile(self.icon):
			icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
			hicon = win32gui.LoadImage(hinst,
									   self.icon,
									   win32con.IMAGE_ICON,
									   0,
									   0,
									   icon_flags)
		else:
			print ("Can't find icon file - using default.")
			hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

		if self.notify_id: message = win32gui.NIM_MODIFY  # NIM_MODIFY sends a message to modify an icon in the taskbar.
		else: message = win32gui.NIM_ADD  # NIM_ADD sends a message to add an icon in the taskbar.
		
		# This is a NOTIFYICONDATA structure as defined here: https://msdn.microsoft.com/en-us/library/windows/desktop/bb773352(v=vs.85).aspx
		#   The fourth argument sets uCallbackMessage = 'win32con.WM_USER+self.OFFSET'
		#   uCallbackMessage: "The system uses this identifier to send notification messages to the window identified in hWnd."
		self.notify_id = (self.hwnd,
						  0,
						  win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
						  win32con.WM_USER+self.OFFSET,
						  hicon,
						  self.hover_text)
		win32gui.Shell_NotifyIcon(message, self.notify_id)  # Registers the message 'win32con.WM_USER+self.OFFSET' to trigger the 'notify' function on mouse-event
	
	def restart(self, hwnd, msg, wparam, lparam):
		self.refresh_icon()
	
	def change_icon(self, hwnd, msg, wparam, lparam):
		try:
			self.icon = self.extra_icon_paths[wparam]
			self.refresh_icon()
		except IndexError:
			print("change_icon: Icon paths missing.")
	
	def destroy(self, hwnd, msg, wparam, lparam):
		if self.on_quit: self.on_quit(self)
		nid = (self.hwnd, 0)
		win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
		win32gui.PostQuitMessage(0) # Terminate the app.

	def notify(self, hwnd, msg, wparam, lparam):
		# Run on any interaction with taskbar icon (mouseover, click, etc)
		if lparam==win32con.WM_LBUTTONDBLCLK:  # Double left-click handler
			if (self.default_menu_index == -1):
				# If default_menu_index is set to -1, double left-click on icon is ignored
				pass
			else:
				# If default_menu_index >= 0, that menu item will be activated on double left-click
				self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
		elif lparam==win32con.WM_RBUTTONUP:  # Right-click handler
			self.show_menu()
		elif lparam==win32con.WM_LBUTTONUP:  # Left-click handler
			#self.show_menu()
			pass
		return True
		
	def show_menu(self):
		menu = win32gui.CreatePopupMenu()
		self.create_menu(menu, self.menu_options)
		#win32gui.SetMenuDefaultItem(menu, 1000, 0)
		
		pos = win32gui.GetCursorPos()
		# See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
		win32gui.SetForegroundWindow(self.hwnd)
		win32gui.TrackPopupMenu(menu,
								win32con.TPM_LEFTALIGN,
								pos[0],
								pos[1],
								0,
								self.hwnd,
								None)
		win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
	
	def create_menu(self, menu, menu_options):
		for option_text, option_icon, option_action, option_id in menu_options[::-1]:
			if option_icon:
				option_icon = self.prep_menu_icon(option_icon)
			
			if option_id in self.menu_actions_by_id:                
				item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
																hbmpItem=option_icon,
																wID=option_id)
				win32gui.InsertMenuItem(menu, 0, 1, item)
			else:
				submenu = win32gui.CreatePopupMenu()
				self.create_menu(submenu, option_action)
				item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
																hbmpItem=option_icon,
																hSubMenu=submenu)
				win32gui.InsertMenuItem(menu, 0, 1, item)

				
	def update_menu_options(self, menu_options):
		# Refreshes menu options to update any changes in icons, text, or handler functions
		self.menu_options = menu_options + (('Quit', None, self.QUIT),)
		self._next_action_id = self.FIRST_ID
		self.menu_actions_by_id = set()
		self.menu_options = self._add_ids_to_menu_options(list(self.menu_options))
		self.menu_actions_by_id = dict(self.menu_actions_by_id)
		del self._next_action_id
		
	def prep_menu_icon(self, icon):
		# Version of prep_menu_icon using win32ui package
		# Source: https://stackoverflow.com/questions/45716730/add-image-in-window-tray-menu/45890829
		
		# First load the icon.
		ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
		ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
		hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

		hwndDC = win32gui.GetWindowDC(self.hwnd)
		dc = win32ui.CreateDCFromHandle(hwndDC)
		memDC = dc.CreateCompatibleDC()
		iconBitmap = win32ui.CreateBitmap()
		iconBitmap.CreateCompatibleBitmap(dc, ico_x, ico_y)
		oldBmp = memDC.SelectObject(iconBitmap)
		brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)

		win32gui.FillRect(memDC.GetSafeHdc(), (0, 0, ico_x, ico_y), brush)
		win32gui.DrawIconEx(memDC.GetSafeHdc(), 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)

		memDC.SelectObject(oldBmp)
		memDC.DeleteDC()
		win32gui.ReleaseDC(self.hwnd, hwndDC)

		return iconBitmap.GetHandle()
	
	def prep_menu_icon_OriginalVersion(self, icon):
		# Original version of prep_menu_icon function. Deprecated.
		
		# First load the icon.
		ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
		ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
		hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

		hdcBitmap = win32gui.CreateCompatibleDC(0)
		hdcScreen = win32gui.GetDC(0)
		hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
		hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
		# Fill the background.
		brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
		win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
		# unclear if brush needs to be feed.  Best clue I can find is:
		# "GetSysColorBrush returns a cached brush instead of allocating a new
		# one." - implies no DeleteObject
		# draw the icon
		win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
		win32gui.SelectObject(hdcBitmap, hbmOld)
		win32gui.DeleteDC(hdcBitmap)
		
		return hbm

	def command(self, hwnd, msg, wparam, lparam):
		id = win32gui.LOWORD(wparam)
		self.execute_menu_option(id)
		
	def execute_menu_option(self, id):
		menu_action = self.menu_actions_by_id[id]
		
		if menu_action == self.QUIT:
			win32gui.DestroyWindow(self.hwnd)  # hwnd = Window Handle (window id?)
		else:
			# Call function associated with menu option. 
			# Argument 1: passes SysTrayIcon object for updating icons, etc.
			# Argument 2: passes id of menu action that was activated.
			menu_action(self, id)
			
def non_string_iterable(obj):
	try:
		iter(obj)
	except TypeError:
		return False
	else:
		return not isinstance(obj, str)

		
		
# Minimal self test. You'll need a bunch of ICO files in the current working
# directory in order for this to work...
if __name__ == '__main__':
	import itertools, glob
	
	icons = itertools.cycle(glob.glob('*.ico'))
	hover_text = "SysTrayIcon.py Demo"
	def hello(sysTrayIcon): print ("Hello World.")
	def simon(sysTrayIcon): print ("Hello Simon.")
	def switch_icon(sysTrayIcon):
		sysTrayIcon.icon = next(icons)
		sysTrayIcon.refresh_icon()
	try:
		menu_options = (('Say Hello', next(icons), hello),
						('Switch Icon', None, switch_icon),
						('A sub-menu', next(icons), (('Say Hello to Simon', next(icons), simon),
													  ('Switch Icon', next(icons), switch_icon),
													 ))
					   )
	except StopIteration:
		print('No icons found')
		
	def bye(sysTrayIcon): print ("Bye, then.")
	
	try:
		SysTrayIcon(next(icons), hover_text, menu_options, on_quit=bye, default_menu_index=1)
	except StopIteration:
		print('No icons found')