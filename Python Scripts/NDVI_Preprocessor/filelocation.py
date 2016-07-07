import os


def get_file_location(root_dir, file_startswith=None, file_endswith=None):
    """ Get file location """
    for source_dir in root_dir:
        try:
            for file_name in os.listdir(source_dir):
                if file_startswith and file_endswith:
                    if file_name.startswith(file_startswith) & file_name.endswith(file_endswith):
                        file_path = os.path.join(source_dir, file_name).replace('\\', '/')
                        yield file_path, file_name
                elif file_startswith:
                    if file_name.startswith(file_startswith):
                        file_path = os.path.join(source_dir, file_name).replace('\\', '/')
                        yield file_path, file_name
                elif file_endswith:
                    if file_name.endswith(file_endswith):
                        file_path = os.path.join(source_dir, file_name).replace('\\', '/')
                        yield file_path, file_name
                else:
                    raise IOError('Input raster file could not be found')
        except IOError as e:
            print (e)


