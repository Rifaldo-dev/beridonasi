
#!/usr/bin/env python3
import os
import signal
import psutil
import sys

def kill_existing_bots():
    """Kill all existing Python processes running main.py"""
    current_pid = os.getpid()
    killed_count = 0
    
    print("🔍 Searching for existing bot processes...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue
                
            # Check if it's a Python process running main.py
            if (proc.info['name'] and 'python' in proc.info['name'].lower() and 
                proc.info['cmdline'] and any('main.py' in arg for arg in proc.info['cmdline'])):
                
                print(f"🔪 Killing process {proc.info['pid']}: {' '.join(proc.info['cmdline'])}")
                proc.terminate()
                killed_count += 1
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed_count > 0:
        print(f"✅ Killed {killed_count} existing bot process(es)")
        print("⏳ Waiting 3 seconds for cleanup...")
        import time
        time.sleep(3)
    else:
        print("ℹ️  No existing bot processes found")

if __name__ == "__main__":
    kill_existing_bots()
    print("✅ Cleanup complete. You can now start the bot.")
