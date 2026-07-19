import glob, subprocess

def touchscreen_devices():
    found=[]
    for path in glob.glob('/sys/class/input/event*/device/name'):
        try:
            name=open(path).read().strip()
            if 'ads7846' in name.lower() or 'touchscreen' in name.lower(): found.append((path, name))
        except OSError: pass
    return found

def rtl_test():
    try:
        result = subprocess.run(['rtl_test','-t'],text=True,capture_output=True,timeout=15)
        return result.stdout + result.stderr
    except (OSError, subprocess.TimeoutExpired) as exc: return f'Falha ao testar RTL-SDR: {exc}'
