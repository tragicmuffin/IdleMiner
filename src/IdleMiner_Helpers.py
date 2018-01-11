import uptime
import win32api

def tupleToList(t):
	# Converts a nested tuple to a nested list
    return list(map(tupleToList, t)) if isinstance(t, (list, tuple)) else t
def listToTuple(l):
	# Converts a nested list to a nested tuple
    return tuple(map(listToTuple, l)) if isinstance(l, (tuple, list)) else l
def getIdleTime():
	# The Windows API function GetLastInputInfo returns the number of milliseconds since last user input
	# The python uptime library function uptime returns the number of seconds since system start
	# Reference:
	#	https://msdn.microsoft.com/en-us/library/windows/desktop/ms646302(v=vs.85).aspx
	#	https://msdn.microsoft.com/en-us/library/system.environment.tickcount(v=vs.110).aspx
	up_seconds = uptime.uptime()
	up_milliseconds = up_seconds * 1000
	
	idleTime_milliseconds = up_milliseconds - win32api.GetLastInputInfo()
	idleTime_seconds = idleTime_milliseconds / 1000
	
	return (round(idleTime_seconds, 1))