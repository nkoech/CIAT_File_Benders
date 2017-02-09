__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import os


def get_file_location(root_dir, file_startswith=None, file_endswith=None):
    """
    Get file location
    :param root_dir: File root directory
    :param file_startswith: File name starting characters
    :param file_endswith: File name ending characters
    :return root_dir: File root directory
    :return file_path: Full file path
    :return file_name: File name
    :rtype root_dir: String
    :rtype file_path: String
    :rtype file_name: String
    """
    try:
        for file_name in os.listdir(root_dir):
            if file_startswith and file_endswith:
                if file_name.startswith(file_startswith) & file_name.endswith(file_endswith):
                    file_path = os.path.join(root_dir, file_name).replace('\\', '/')
                    yield root_dir, file_path, file_name
            elif file_startswith:
                if file_name.startswith(file_startswith):
                    file_path = os.path.join(root_dir, file_name).replace('\\', '/')
                    yield root_dir, file_path, file_name
            elif file_endswith:
                if file_name.endswith(file_endswith):
                    file_path = os.path.join(root_dir, file_name).replace('\\', '/')
                    yield root_dir, file_path, file_name
            else:
                raise IOError('Input raster file could not be found')
    except IOError as e:
        print (e)


