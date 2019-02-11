import os
from clarisse_survival_kit.settings import *
import threading
import time

host, port = '127.0.0.1', 24981

if not ix.application.is_command_port_active():
    ix.application.enable_command_port()

if ix.application.get_command_port() != 55000:
    ix.application.set_command_port(55000)

package_path = os.environ.get("CSK_PACKAGE_PATH")

if not package_path:
    try:
        package_path = PACKAGE_PATH
    except (NameError, ImportError):
        message = 'PACKAGE_PATH could not be loaded from user_settings.py.\n' \
                  'If this is your first run the variable should have been setup during this session, but it requires the kit to be reloaded.\n\n' \
                  'Please restart Clarisse and see if it works.'
        mb = ix.application.message_box(message, "Please restart", ix.api.AppDialog.cancel(),
                                        ix.api.AppDialog.STYLE_OK)
        ix.log_warning(message)


def run_script():
    if package_path:
        os.system('python %s' % os.path.join(package_path, 'ms_bridge_importer.py'))


t = threading.Thread(target=run_script)
t.start()
time.sleep(2)
