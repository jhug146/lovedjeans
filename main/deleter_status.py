import os

def is_deleter_running():
    try:
        result = os.system("pgrep -f \"^bash ./deleter.sh$\" > /dev/null 2>&1")
        return result == 0
    except subprocess.CalledProcessError as error:
        return False
