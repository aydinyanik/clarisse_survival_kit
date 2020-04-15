#!/usr/bin/env python2
import os
import json
import platform
import re
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
import site
import datetime
from shutil import copyfile
import logging
import codecs


def setup_shelf(shelf_path, slot=0):
    """Sets up the shelf"""
    print os.path.dirname(os.path.join(shelf_path, 'shelf_installation.log'))
    logging.basicConfig(filename=os.path.join(os.path.dirname(shelf_path), 'shelf_installation.log'),
                        level=logging.DEBUG, format='%(message)s')
    log_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.debug("--------------------------------------")
    logging.debug("Log start: " + log_start)

    with open(os.path.join(script_dir, package_name, 'shelf.json')) as json_file:
        json_data = json.load(json_file)
    shelf_title = json_data.get('category')
    logging.debug("Setting up shelf: " + shelf_title)
    required_shelf_items = json_data.get('shelf_items')
    category_search = None
    with codecs.open(shelf_path, "r", encoding="utf-8") as f:
        shelf_file = f.read()

    # Make a backup
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    shelf_backup = re.sub('\.cfg$', "." + timestamp + ".bak", shelf_path)
    copyfile(shelf_path, shelf_backup)

    write_index = 0
    generated_string = ''

    # Search for view mode #:
    logging.debug("Searching for view mode string")
    view_mode_search = re.search(ur"view_mode [0-9]", shelf_file, re.MULTILINE | re.DOTALL)
    if view_mode_search:
        write_index = view_mode_search.end()
        logging.debug("Found view mode:")
        logging.debug(view_mode_search.group(0))
    # Search for slot #:
    logging.debug("Searching for slot string")
    slot_search = re.search(ur"slot [0-9] {", shelf_file,
                            re.MULTILINE | re.DOTALL)
    if not slot_search:
        generated_string += "\n\tslot " + str(slot) + " {\n"
    else:
        write_index = slot_search.end() + 1
        # Search for category:
        logging.debug("Found slot block:")
        logging.debug(slot_search.group(0))
        logging.debug("Searching for category string")
        category_search = re.search(r'category "' + shelf_title + '" {(.*?)(?<! ) {8}(?! )}', shelf_file,
                                    re.MULTILINE | re.DOTALL | re.IGNORECASE)

    existing_items = []
    if not category_search:
        generated_string += "\t\tcategory \"" + shelf_title + "\" {\n"
    else:
        logging.debug("Found category block:")
        logging.debug(unicode(shelf_file[category_search.start():category_search.end()]))
        write_index = category_search.end()
        shelf_item_search = re.finditer(r"\s{12}shelf_item {(.*?)(?<! ) {12}(?! )}",
                                        shelf_file[category_search.start():category_search.end()],
                                        re.MULTILINE | re.DOTALL)
        for shelf_item in shelf_item_search:
            logging.debug("Found shelf item block:")
            logging.debug(unicode(shelf_file[category_search.start():category_search.end()][
                                  shelf_item.start():shelf_item.end()]))
            shelf_attributes_search = re.search(r"\s{16}title \"(?P<title>.*?)\".*"
                                                r"\s{16}description \"(?P<description>.*?)\".*"
                                                r"\s{16}script_filename \"(?P<script_filename>.*?)\".*"
                                                r"\s{16}icon_filename \"(?P<icon_filename>.*?)\".*",
                                                shelf_file[category_search.start():category_search.end()][
                                                shelf_item.start():shelf_item.end()],
                                                re.MULTILINE | re.DOTALL)
            if shelf_attributes_search:
                for required_shelf_item in required_shelf_items:
                    if required_shelf_item.get("title") == shelf_attributes_search.group('title'):
                        logging.debug("Shelf item \"%s\" already exists. Item is ignored." % \
                                      required_shelf_item.get('title'))
                        existing_items.append(shelf_attributes_search.group('title'))
            write_index = category_search.start() + shelf_item.end()
    if len(existing_items) < len(required_shelf_items):
        generated_string += "\n"
    for required_shelf_item in required_shelf_items:
        if not required_shelf_item.get('title') in existing_items:
            logging.debug("Adding shelf item: " + required_shelf_item.get('title'))
            sitepackages_folders = site.getsitepackages()
            script_filename = ''
            icon_filename = ''
            for sitepackages_folder in sitepackages_folders:
                logging.debug("Testing folder for script availability: " + sitepackages_folder)
                test_script_filename = os.path.join(sitepackages_folder, package_name,
                                                    required_shelf_item.get('script_filename'))
                test_icon_filename = os.path.join(sitepackages_folder, package_name,
                                                  required_shelf_item.get('icon_filename'))
                logging.debug(test_script_filename)
                if os.path.isfile(test_script_filename):
                    script_filename = test_script_filename
                if os.path.isfile(test_icon_filename):
                    icon_filename = test_icon_filename
            if platform.system() == "Windows":
                script_filename = script_filename.replace("\\", "/")
                icon_filename = icon_filename.replace("\\", "/")
            generated_string += str("\t" * 3 + "shelf_item {\n")
            generated_string += str("\t" * 4 + "title \"" + required_shelf_item.get('title') + "\"\n")
            if required_shelf_item.get('description'):
                generated_string += str("\t" * 4 + "description \"" +
                                        required_shelf_item.get('description') + "\"\n")
            generated_string += str("\t" * 4 + "script_filename \"" +
                                    script_filename + "\"\n")
            if required_shelf_item.get('icon_filename'):
                generated_string += str("\t" * 4 + "icon_filename \"" +
                                        icon_filename + "\"\n")
            generated_string += str("\t" * 3 + "}\n")

    if not category_search:
        generated_string += "\t\t}\n"
    if not slot_search:
        generated_string += "\t}\n"
    if not view_mode_search:
        generated_string = '\n' + generated_string

    new_cfg = shelf_file[:write_index] + generated_string + shelf_file[write_index:]
    new_cfg = new_cfg.replace("\t", "    ")
    cleaned_whitespace = "\n".join([line for line in new_cfg.split('\n') if line.strip() != ''])
    new_cfg = cleaned_whitespace

    new_cfg = re.sub("category_selected \"[\w\s]+\"", "category_selected \"" + shelf_title + "\"", new_cfg)

    cfg_file = codecs.open(shelf_path, "w", encoding="utf-8")
    cfg_file.write(new_cfg)
    cfg_file.close()
    logging.debug("...Shelf installed!")
    log_end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.debug("Log end: " + log_end)


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        develop.run(self)
        print "Post develop command running..."


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        print "Post installation command running..."
        if platform.system().lower() == "windows":
            clarisse_dir = os.path.join(os.getenv('APPDATA'), "Isotropix\Clarisse\\")
            for version_dir in os.listdir(clarisse_dir):
                if os.path.isdir(os.path.join(clarisse_dir, version_dir)):
                    if version_dir in versions:
                        print "Looking for shelf file in." + os.path.join(clarisse_dir, version_dir)
                        shelf_path = os.path.join(clarisse_dir, version_dir, "shelf.cfg")
                        print os.path.join(clarisse_dir, version_dir, "shelf.cfg")
                        if os.path.isfile(shelf_path):
                            print "Found shelf config file."
                            setup_shelf(shelf_path)

        elif platform.system().lower().startswith("linux"):
            clarisse_dir = os.path.join(os.path.expanduser("~"), ".isotropix/clarisse/")
            for version_dir in os.listdir(clarisse_dir):
                if os.path.isdir(os.path.join(clarisse_dir, version_dir)):
                    if version_dir in versions:
                        shelf_path = os.path.join(clarisse_dir, version_dir, "shelf.cfg")
                        if os.path.isfile(shelf_path):
                            setup_shelf(shelf_path)
        elif platform.system().lower() == "darwin":
            homedir = os.path.expanduser('~')
            clarisse_dir = homedir + '/Library/Preferences/Isotropix/Clarisse/'
            for version_dir in os.listdir(clarisse_dir):
                if os.path.isdir(os.path.join(clarisse_dir, version_dir)):
                    version_match = re.search(r"(\d[.\d]*)$", version_dir)
                    if version_match and version_match.group(1) in versions:
                        shelf_path = os.path.join(clarisse_dir, version_dir, "shelf.cfg")
                        if os.path.isfile(shelf_path):
                            setup_shelf(shelf_path)
                            print "sp: ", shelf_path


long_description = ''
script_dir = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(script_dir, "README.md"), "r") as fh:
    long_description = fh.read()

package_name = "clarisse_survival_kit"
versions = ['3.5', '3.6', '4.0']

setup(
    name=package_name,
    version="1.0.0",
    author="Aydin Yanik",
    author_email="aydinyanik@gmail.com",
    description="Provides utility functions to import common assets such as Megascans assets and Substance textures.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aydinyanik/clarisse_survival_kit",
    packages=find_packages(),
    package_data={'': ['*.png', '*.json']},
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: GPLv3",
        "Operating System :: OS Independent",
    ]
)
