import os, re
import errno, shutil


class FileCopier(object):
    """search for tiff file with the word 'dem' and copy to a new folder"""

    def __init__(self, source_dir, dest_dir):
        self.source_dir = source_dir
        self.dest_dir = dest_dir

    def get_file_paths(self):
        """Get files and copy"""
        for root_path, dir_name, files in os.walk(self.source_dir):
            for f in files:
                file_path = os.path.join(root_path, f).replace("\\","/")
                if file_path.endswith(".tif"):
                    if re.search(r'lc030', file_path) != None:
                        try:
                            shutil.copy2(file_path, self.dest_dir)
                            print('File ' + f + ' copied')
                        except IOError:
                            print('File ' + f + ' already exists')
        print "DONE coping ALL files"

def main():
    """Main program"""
    fcopier = FileCopier("D:/Junk/GCL30_Extracts/", "C:/CCAFS_DATA/LULC_30m_TIF/")
    fcopier.get_file_paths()

if __name__ == "__main__":
    main()
        
    
