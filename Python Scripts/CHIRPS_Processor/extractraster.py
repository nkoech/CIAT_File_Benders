__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


from extractdata import extract_data
from filelocation import get_file_location
import ntpath
import os
from readjson import get_json_data
from sourcedirectory import get_directory


class ExtractRaster:
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

    def init_extract_raster(self):
        """ Initialize raster extrcation"""
        self._uncompress_file()  # Extract file

    def _uncompress_file(self):
        """ Uncompress file """
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):            
            extract_data(self.dest_dir, file_path, file_name, self.file_endswith)
            print('Extracted: {0}'.format(file_name))


def main():
    """Main program"""
    extract = ExtractRaster()
    extract.init_extract_raster()

if __name__ == '__main__':
    main()
