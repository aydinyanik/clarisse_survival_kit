import os
from clarisse_survival_kit.settings import *
import threading

host, port = '127.0.0.1', 24981


def run_script():
    os.system('python %s' % os.path.join(PACKAGE_PATH, 'ms_bridge_importer.py'))


t = threading.Thread(target=run_script)
t.start()
