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


user_path = os.path.join(get_isotropix_user_path(), '.csk')
if user_path:
    sys.path.append(os.path.normpath(user_path))
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    init_path = os.path.join(user_path, '__init__.py')
    if not os.path.isfile(init_path):
        init_file = open(init_path, 'w+')
        init_file.close()

    log_level = logging.ERROR
    settings_path = os.path.join(user_path, settings_filename)
    if not os.path.isfile(settings_path):
        settings_file = open(settings_path, 'w+')
        settings_file.close()
    else:
        try:
            from user_settings import LOG_LEVEL
            log_level = LOG_LEVEL
        except ImportError:
            pass

    log_path = os.path.join(user_path, logging_filename)
    if os.path.isfile(log_path):
        with open(log_path, "w") as log_file:
            log_file.truncate()
    try:
        from user_settings import PACKAGE_PATH
        os.environ["CSK_PACKAGE_PATH"] = PACKAGE_PATH
    except ImportError:
        sitepackages_folders = site.getsitepackages() + [site.getusersitepackages()]
        for sitepackages_folder in sitepackages_folders:
            if os.path.isdir(sitepackages_folder):
                sub_folders = os.listdir(sitepackages_folder)
                for sub_folder in sub_folders:
                    folder_path = os.path.normpath(os.path.join(sitepackages_folder, sub_folder))
                    if os.path.isdir(folder_path):
                        if sub_folder == 'clarisse_survival_kit':
                            print("Found CSK package location on disk")
                            settings_file = open(settings_path, 'a')
                            settings_file.write('\nPACKAGE_PATH = "%s"' % folder_path)
                            os.environ["CSK_PACKAGE_PATH"] = folder_path
                            settings_file.close()

    logging.basicConfig(filename=log_path, level=log_level, format='%(message)s')
    log_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.debug("--------------------------------------")
    logging.debug("Log start: " + log_start)
else:
    print("Could not generate log or user settings!!!")
