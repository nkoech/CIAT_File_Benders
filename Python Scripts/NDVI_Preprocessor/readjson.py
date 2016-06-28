import os
import json


def get_file_path(file_startswith, file_endswith):
    """Get the current directory and search for a json file"""
    cwd = os.getcwd()
    try:
        for file_name in os.listdir(cwd):
            if file_name.startswith(file_startswith) & file_name.endswith(file_endswith):
                file_path = os.path.join(cwd, file_name).replace('\\', '/')
                return file_path
            else:
                raise ValueError('Settings in JSON file are missing')
    except ValueError as e:
        print(e)


def get_json_data(file_startswith, file_endswith):
    """Reads json file and return data"""
    file_path = get_file_path(file_startswith, file_endswith)
    if file_path:
        with open(file_path) as json_file:
            return json.load(json_file)