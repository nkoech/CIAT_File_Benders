__author__ = 'Koech Nicholas'

#import modules
import os, json
import shutil

class DirCopy(object):
    """Copy an entire directory from source to destination"""

    def get_json_file(self):
        """Get the current directory and search for a json file"""
        cwd = os.getcwd()
        for file in os.listdir(cwd):
            if file.startswith("dir_copy") & file.endswith(".json"):
                file_path = os.path.join(cwd, file).replace("\\","/")
                return file_path

    def get_params(self):
        """Reads json file and return paths"""
        json_param = json.loads(open(self.get_json_file()).read()) #read and load a json file
        src = self.loop_json(json_param, "src", "src_dir")
        dest = self.loop_json(json_param, "dest", "dest_dir")
        dir_startswith = self.loop_json(json_param, "dir_startswith", "dir_param")
        return (src, dest, dir_startswith)

    def loop_json(self, json_param, key_1, key_2):
        """Get contents from a Json file"""
        for key in json_param[key_1]: #loop through json keys
            value = key[key_2] #get key values
        return value

    def get_file_paths(self):
        """Returns MODIS file paths"""
        for root_path, dir_names, files in os.walk(self.get_params()[0]):
            for dir_name in dir_names:
                if dir_name.startswith(self.get_params()[2]):
                    src = os.path.join(root_path, dir_name).replace("\\","/")
                    print("COPYING .... " + src + " TO " + self.get_params()[1])
                    shutil.copytree(src, self.get_params()[1] + "/" + dir_name) #copy directory tree from source to destination
        print("COPYING COMPLETED SUCCESSFULLY!!!")

def main():
    """Main program"""
    d_copy = DirCopy()
    d_copy.get_file_paths()

if __name__ == "__main__":
    main()