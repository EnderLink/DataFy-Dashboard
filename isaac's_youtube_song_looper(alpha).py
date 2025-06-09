import time
import webbrowser
import pygetwindow as gw
import pyautogui
import psutil
import subprocess
import os

# URL to loop
URL_user = input("Welcome to Isaac's Youtube Song Looper. \nPlease paste your Youtube link here:")
SKIP_TIME = input("How many seconds would you like to skip into the song? ")
URL = URL_user + f"&t={SKIP_TIME}s"
WAIT_TIME = int(input("How long would you like to wait until the song restarts? "))  # 2 minutes 30 seconds
BROWSER_PROCESS_NAME = "chrome.exe"  # Browser process name
WINDOW_TITLE_MATCH = "YouTube"


def close_youtube_tab():
    try:
        for window in gw.getWindowsWithTitle(WINDOW_TITLE_MATCH):
            if "YouTube" in window.title:
                try:
                    window.activate()
                    time.sleep(0.5)
                    pyautogui.hotkey('ctrl', 'w')  # Close current tab
                    time.sleep(0.5)
                    return True
                except Exception as e:
                    print(f"Could not activate or close tab: {e}")
        print("No matching YouTube tab found.")
    except Exception as e:
        print(f"Error while searching for windows: {e}")
    return False


def open_youtube_tab():
    webbrowser.open(URL)


def browser_is_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == BROWSER_PROCESS_NAME.lower():
            return True
    return False


def ensure_browser():
    if not browser_is_running():
        opera_path = os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Programs\Opera GX\launcher.exe")
        subprocess.Popen([opera_path])
        time.sleep(3)


if __name__ == "__main__":
    while True:
        ensure_browser()
        open_youtube_tab()
        time.sleep(WAIT_TIME)
        close_youtube_tab()
