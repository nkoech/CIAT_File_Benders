__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import gzip
import os


def extract_data(dest_dir, file_path, file_name, fname_endswith):
    """ Extract file """
    if file_name.endswith(fname_endswith):
        dest_file = os.path.join(dest_dir, file_name[:-3]).replace('\\', '/')
        with gzip.open(file_path, 'rb') as in_file:
            with open(dest_file, 'wb') as out_file:
                out_file.write(in_file.read())
        out_file.close()
        in_file.close()
