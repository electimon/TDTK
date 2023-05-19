import adbutils, time

def switch_wifi(device, status: bool) -> adbutils.ShellReturn:
    arglast = 'enable' if status else 'disable'
    cmdargs = ['svc', 'wifi', arglast]
    return device.shell2(cmdargs)

def enable_wifi(caller) -> adbutils.ShellReturn:
    caller.logger.log(f"Enter: wifi.enable_wifi", type="debug")
    return switch_wifi(caller.device, True)

def connect(caller, parameters) -> int:
    caller.logger.log(f"Enter: wifi.connect", type="debug")
    cmd = f'cmd wifi connect-network {parameters["ssid"]} {parameters["encryption"]} {parameters["password"]}'
    ret = caller.device.shell2(cmd)
    caller.logger.log(f"Command: {cmd}", type="debug")
    caller.logger.log(f"Command Output: {ret}", type="debug")
    return ret.returncode

def is_enabled(caller) -> bool:
    caller.logger.log(f"Enter: wifi.is_enabled", type="debug")
    timeout = time.time() + 3  # Set the timeout to 3 seconds from now
    cmd = "cmd wifi status | head -n1"
    while time.time() < timeout:
        ret = caller.device.shell(cmd).strip().lower()
        caller.logger.log(f"Command: {cmd}", type="debug")
        caller.logger.log(f"Command Output: {ret}", type="debug")  
        if ret == "wifi is enabled":
            return True
        time.sleep(0.2)  # Wait for a short duration before checking again

    return False

def is_connected(caller) -> bool:
    caller.logger.log(f"Enter: wifi.is_connected", type="debug")
    timeout = time.time() + 3  # Set the timeout to 3 seconds from now
    cmd = "cmd wifi status | sed '4q;d'"
    while time.time() < timeout:
        ret = caller.device.shell().strip().lower()
        caller.logger.log(f"Command: {cmd}", type="debug")
        caller.logger.log(f"Command Output: {ret}", type="debug")  
        if cmd == "wifi is connected to":
            return True
        time.sleep(0.2)  # Wait for a short duration before checking again

    return False