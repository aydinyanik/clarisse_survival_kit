import sys
import os
import logging
import datetime
import site

sys.dont_write_bytecode = True

logging_filename = 'clarisse_survival_kit.log'
settings_filename = 'user_settings.py'

sitepackages_folders = site.getsitepackages()
for sitepackages_folder in sitepackages_folders:
	package_path = os.path.join(sitepackages_folder, 'clarisse_survival_kit')
	if os.path.isdir(package_path):
		user_path = os.path.join(package_path, "user")
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
			os.remove(log_path)

		logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(message)s')
		log_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		logging.debug("--------------------------------------")
		logging.debug("Log start: " + log_start)
