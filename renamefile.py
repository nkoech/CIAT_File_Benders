__author__ = 'nkoech'

import os


class RenameFile(object):
    """ Rename file according to user requirements """

    def __init__(self, s_dir):
        self.s_dir = s_dir

    def get_dir_paths(self):
        """Get file directory path"""
        tiff_dirs = []
        for root_path, dir_names, files in os.walk(self.s_dir):  # walk through root directory
            for dir_name in dir_names:
                for dir_Output in dir_name.split("_"):  # Split sub-directory names
                    if dir_Output == "SRTMCombined":
                        dir_join = os.path.join(root_path, dir_name).replace("\\","/")  # Join rooth to sub-directory
                        tiff_dirs.append(dir_join)
        return tiff_dirs

    def del_file(self):
        """Delete files with less than the indicated size"""

        for source_path in self.get_dir_paths():
            status = "FALSE"
            for file in os.listdir(source_path):
                if file.endswith(".tif"):
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    if os.path.getsize(file_path) < 25964800:
                        status = "TRUE"
                        print("Deleting...... " + file_path)
                        os.remove(file_path)
            if status == "TRUE":
                print("ALL FILES DELETED SUCCESSFULLY IN " + source_path)
            else:
                print("NO FILE TO BE DELETED IN " + source_path)
        print("DELETION OF FILES COMPLETE SUCCESSFULLY!!!!!")

    def rename_file(self):
        """Rename all files in the input folder"""

        for source_path in self.get_dir_paths():
            status = "FALSE"
            for file in os.listdir(source_path):
                if ").tif" in file:
                    old_filename = os.path.join(source_path, file).replace("\\","/") #construct file full path
                    new_filename = os.path.join(source_path, file[:-8] + ".tif").replace("\\","/") #construct file full path
                    try:
                        if os.path.exists(old_filename):
                            status = "TRUE"
                            print("Renaming.... " + old_filename)
                            os.rename(old_filename, new_filename)
                        else:
                            status = "FALSE"
                    except Exception, e:
                        print(e)
            if status == "TRUE":
                print("ALL FILES RENAMED SUCCESSFULLY IN " + source_path)
            else:
                print("NO FILE TO BE RENAMED IN " + source_path)
        print("RENAMING OF FILES COMPLETE SUCCESSFULLY!!!!!")

def main():
    """ Main program """
    f_rename = RenameFile("C:/CCAFS_DATA/")
    f_rename.del_file()
    f_rename.rename_file()

if __name__ == "__main__":
    main()