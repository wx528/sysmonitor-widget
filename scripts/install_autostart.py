"""Install sysmonitor-widget to APPDATA and register it to run on Windows startup."""

import os
import shutil
import sys
import winreg


def install():
    app_name = "SysMonitorWidget"
    exe_name = "sysmonitor-widget.exe"

    source_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", exe_name)
    if not os.path.exists(source_exe):
        print(f"Error: {source_exe} not found. Please run PyInstaller first.")
        sys.exit(1)

    install_dir = os.path.join(os.environ["APPDATA"], "SysMonitor")
    target_exe = os.path.join(install_dir, exe_name)

    os.makedirs(install_dir, exist_ok=True)
    shutil.copy2(source_exe, target_exe)
    print(f"Copied to: {target_exe}")

    reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, target_exe)

    print(f"Registered '{app_name}' to start on login.")
    print("You can verify in Task Manager > Startup.")


if __name__ == "__main__":
    if sys.platform != "win32":
        print("This script is for Windows only.")
        sys.exit(1)
    install()
