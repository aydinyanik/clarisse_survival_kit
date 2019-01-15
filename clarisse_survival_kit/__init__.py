import sys
import os
import logging
import datetime
import site
import platform

sys.dont_write_bytecode = True

logging_filename = 'clarisse_survival_kit.log'
settings_filename = 'user_settings.py'
settings_path = ''


def get_isotropix_user_path():
    clarisse_dir = None
    if platform.system().lower() == "windows":
        clarisse_dir = os.path.join(os.getenv('APPDATA'), "Isotropix\\")
    elif platform.system().lower().startswith("linux"):
        clarisse_dir = os.path.join(os.path.expanduser("~"), ".isotropix/")
    elif platform.system().lower() == "darwin":
        homedir = os.path.expanduser('~')
        clarisse_dir = homedir + '/Library/Preferences/Isotropix/'
    return clarisse_dir


sitepackages_folders = site.getsitepackages()
for sitepackages_folder in sitepackages_folders:
    user_path = os.path.join(get_isotropix_user_path(), '.csk')
    if user_path:
        sys.path.append(os.path.normpath(user_path))
        if not os.path.exists(user_path):
            os.makedirs(user_path)
        init_path = os.path.join(user_path, '__init__.py')
        if not os.path.isfile(init_path):
            init_file = open(init_path, 'w+')
            init_file.close()
        settings_path = os.path.join(user_path, settings_filename)
        if not os.path.isfile(settings_path):
            settings_file = open(settings_path, 'w+')
            settings_file.close()

        log_path = os.path.join(user_path, logging_filename)
        if os.path.isfile(log_path):
            with open(log_path, "w") as log_file:
                log_file.truncate()

        logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(message)s')
        log_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.debug("--------------------------------------")
        logging.debug("Log start: " + log_start)
    else:
        print "Could not generate log or user settings!!!"
