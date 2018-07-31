__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import csv
from filelocation import get_file_location
import os
from readjson import get_json_data
from sourcedirectory import get_directory


class FileChecker:
    def __init__(self):
        self.tool_settings = self._get_user_parameters()
        self.src = self.tool_settings['src_dir']
        self.dest_dir = self.tool_settings['dest_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']

    def _get_user_parameters(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data('dir_meta', '.json')
        for i in data:
            for j in data[i]:
                if isinstance(j, dict):
                    tool_settings.update(j)
        return tool_settings

    def get_file_path(self):
        """ Gets files source paths """
        file_names = []
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            file_names.append(file_name)
        self._create_directory(self.dest_dir)
        self._write_csv(file_names)

    def _create_directory(self, dest_dir):
        """ Create destination directory if it doesn't exist """
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)  # Create destination folder

    def _write_csv(self, file_names):
        """ Write file names to CSV """
        csv_file = self.dest_dir + "/output.csv"
        with open(csv_file, "w") as output:
            for i in file_names:
                print("Saving {}".format(i))
                output.write(i + '\n')


def main():
    """Main program"""
    file_checker = FileChecker()
    file_checker.get_file_path()

if __name__ == "__main__":
    main()