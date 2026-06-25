"""Remove sysmonitor-widget from Windows startup and optionally delete installed files."""

import os
import sys
import winreg


def remove(delete_files: bool = True):
    app_name = "SysMonitorWidget"
    exe_name = "sysmonitor-widget.exe"
    install_dir = os.path.join(os.environ["APPDATA"], "SysMonitor")
    target_exe = os.path.join(install_dir, exe_name)

    reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, app_name)
        print(f"Removed '{app_name}' from startup.")
    except FileNotFoundError:
        print(f"'{app_name}' was not found in startup registry.")

    if delete_files:
        try:
            if os.path.exists(target_exe):
                os.remove(target_exe)
                print(f"Deleted: {target_exe}")
            if os.path.exists(install_dir) and not os.listdir(install_dir):
                os.rmdir(install_dir)
                print(f"Removed empty directory: {install_dir}")
        except OSError as e:
            print(f"Warning: could not delete files: {e}")


if __name__ == "__main__":
    if sys.platform != "win32":
        print("This script is for Windows only.")
        sys.exit(1)
    remove()
