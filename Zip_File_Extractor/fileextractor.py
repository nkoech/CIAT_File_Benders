__author__ = 'nkoech'

import os, re, io, json
import zipfile, errno

class  FileExtractor(object):
    """
    Search for zip files in the source directory and its sub-directories
    and decompress them to the destination directory
    
    Author: Koech Nicholas
    Year: 2014
    """

    def get_json_file(self):
        """Get the current directory and search for a json file"""
        cwd = os.getcwd()
        for file in os.listdir(cwd):
            if file.endswith(".json"):
                file_path = os.path.join(cwd, file).replace("\\","/")
                return file_path            

    def get_dir_paths(self):
        """Reads json file and return paths"""
        dirs = json.loads(open(self.get_json_file()).read()) #read and load a json file
        source_dir = self.loop_json(dirs, "source", "source_dir")
        dest_dir = self.loop_json(dirs, "destination", "dest_dir")        
        return (source_dir, dest_dir)

    def loop_json(self, dirs, dir_type, dir_path):
        """Get contents from a Json file"""
        for dir in dirs[dir_type]: #loop through json keys
            directory = dir[dir_path] #get directory location
        return directory

    def get_file_paths(self):
        """Returns zip file paths"""
        file_paths = []
        for root_path, dir_name, files in os.walk(self.get_dir_paths()[0]):
            for file in files:
                file_path = os.path.join(root_path, file).replace("\\","/") #replace double backslash with single backslash
                if file_path.endswith(".zip"):
                    file_paths.append(file_path)
        return file_paths
    
    def makedir(self):
        """Check if directory exist if not make one"""
        try:
            os.makedirs(self.get_dir_paths()[1])
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        
    def extract_zip(self, file_paths):
        """Extract zip files to destination folders"""
        self.makedir()
        for file_path in file_paths:
            root_path = os.path.split(file_path)[0] #get root path of each file
            zfile1 = zipfile.ZipFile(file_path)
            print(file_path)
            for fname1 in zfile1.namelist(): #iterate through the zip file names
                if re.search(r'\.zip$', fname1) != None: #check if file ends with .zip
                    zfiledata = io.BytesIO(zfile1.read(fname1))
                    zfile2 = zipfile.ZipFile(zfiledata)
                    for fname2 in zfile2.namelist():
                        try:
                            print "Decompressing ..... " + fname2                          
                            zfile2.extract(fname2, self.get_dir_paths()[1]) #extract files
                        except IOError:
                            print "Could NOT decompress .... " + fname2
                else:
                    try:
                        print "Decompressing ..... " + fname1
                        zfile1.extract(fname1, self.get_dir_paths()[1])
                    except IOError:
                        print "Could NOT decompress .... " + fname1
            print "FINISHED decompressing files from .... " + root_path
        print "DONE decompressing ALL files"

def main():
    """Main program"""
    unzipper = FileExtractor()
    f_paths = unzipper.get_file_paths()
    unzipper.extract_zip(f_paths)

if __name__ == "__main__":
    main()
