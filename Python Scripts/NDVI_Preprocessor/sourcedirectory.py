import os


def get_directory(src, dir_startswith):
    """ Get file root directory """
    file_dir = []
    try:
        if src:
            for root_path, dirs, files in os.walk(src):
                if dirs:
                    for dir_name in dirs:
                        if dir_name.startswith(dir_startswith):
                            src_dir = os.path.join(root_path, dir_name).replace('\\', '/')
                            file_dir.append(src_dir)
                else:
                    if root_path == src:
                        file_dir.append(root_path)
            return file_dir
        else:
            raise ValueError('Source directory for the files is not set')
    except ValueError as e:
        print(e)