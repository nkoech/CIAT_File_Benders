__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import os


def get_directory(src, dir_startswith=None):
    """ Get file root directory """
    try:
        if src:
            for root_path, dirs, files in os.walk(src):
                if dirs:
                    for dir_name in dirs:
                        if dir_startswith:
                            if dir_name.startswith(dir_startswith):
                                src_dir = os.path.join(root_path, dir_name).replace('\\', '/')
                                yield src_dir
                        else:
                            src_dir = os.path.join(root_path, dir_name).replace('\\', '/')
                            yield src_dir
                else:
                    if root_path == src:
                        yield root_path
        else:
            raise ValueError('Source directory for the files is not set')
    except ValueError as e:
        print(e)