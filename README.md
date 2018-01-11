# IdleMiner

IdleMiner is a Windows program written in Python 3 for launching cryptocurrency mining programs automatically when the system is idle.

The primary goal of IdleMiner was to create a Windows program that had some of the functionality of the [NiceHash Miner](https://github.com/nicehash/NiceHashMinerLegacy) clients, without actually using the NiceHash service. Specifically, a program that runs in the tray and begins mining automatically when the PC has been idle for a specified amount of time.

Automatically starting a mining program on idle using Windows Task Scheduler is not feasible due to the specific and arbitrary way that Windows 8+ defines an idle condition. Thus, IdleMiner uses the Windows API function [GetLastInputInfo](https://msdn.microsoft.com/en-us/library/windows/desktop/ms646302(v=vs.85).aspx), which is the same method used by the NiceHash miner for idle checking.

## Current features
- Accurate idle checking (idle is defined as no keyboard/mouse input)
- Customizable idle timer
- Hidden program and mining windows
- Currently only works with EWBF (Zcash) miner

## How to use
Right-clicking on tray icon will bring up menu, with options to manually start/stop mining, disable/enable idle timer, or change the length of the timer.
Double-clicking on tray icon will manually toggle mining on/off. When manual mining is on, timer is disabled.

## Source Files
### IdleMiner.py
Checks for idle condition. Manages setting changes. Initiates Windows tray icon. Loads saved program settings from .yaml file.

### SysTrayIcon.py
Adapted from [SysTrayIcon.py](http://www.brunningonline.net/simon/blog/archives/SysTrayIcon.py.html) by Simon Brunning. Handles drawing and interaction for tray icon.

### IdleMiner_Helpers.py
Various helper functions.
