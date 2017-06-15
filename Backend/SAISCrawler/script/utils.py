###############################################################
# Utility functions
###############################################################

import os
import json
import datetime

def get_project_full_path():
    """ Return the full path of the project, for navigating directories."""

    projectDirectory = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))

    return projectDirectory


def check_date_string(date):
    """ Return True if the input string is a valid YYYY-MM-DD date, False
        otherwise. """

    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False

    return True


def check_direction(direction):
    """ Return True if the input string is a valid direction of forecast (N, NE,
        E, SE, S, SW, W, NW). Return False otherwise. """

    if direction in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
        return True
    else:
        return False


def read_config(requestedKey):
    """ Return the configuration value of requestedKey. """

    configFile = get_project_full_path() + "/script/config.json"

    if not os.path.isfile(configFile):
        raise ValueError("The configuration file config.json does not exist!")

    with open(configFile) as SettingsFile:
        SettingsData = json.load(SettingsFile)
        return SettingsData[requestedKey]
