__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import arcpy
from arcpy import env
from arcpy.sa import *
from filelocation import get_file_location
import ntpath
import os
from readjson import get_json_data
from sourcedirectory import get_directory


class TrendCorrelation:
    def __init__(self):
        self.tool_settings = self._get_user_parameters()
        self.src_var_1 = self.tool_settings['src_dir_1']
        self.dir_startswith_var_1 = self.tool_settings['dir_startswith_1']
        self.file_startswith_var_1 = self.tool_settings['file_startswith_1']
        self.file_endswith_var_1 = self.tool_settings['file_endswith_1']
        self.src_var_2 = self.tool_settings['src_dir_2']
        self.dir_startswith_var_2 = self.tool_settings['dir_startswith_2']
        self.file_startswith_var_2 = self.tool_settings['file_startswith_2']
        self.file_endswith_var_2 = self.tool_settings['file_endswith_2']
        self.dest_dir = self.tool_settings['dest_dir']
        self.place_name = self.tool_settings['aoi_place_name']

    def _get_user_parameters(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data('dir_meta', '.json')
        for i in data:
            for j in data[i]:
                if isinstance(j, dict):
                    key = j.keys()[0]
                    tool_settings[key] = j[key]
                else:
                    for k in data[i][j]:
                        key = k.keys()[0]
                        tool_settings[key] = k[key]
        return tool_settings

    def init_geoprocess_raster(self):
        """ Initialize raster geoprocessing """
        self.validate_data()  # Validated raster

        if not os.path.exists(self.dest_dir):
            os.makedirs(self.dest_dir)  # Create destination folder
        print('RASTER PROCESSING COMPLETED SUCCESSFULLY!!!')

    def validate_data(self):
        """ Check for  invalid/corrupted data """
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            self._get_spatial_ref(file_path)
            print('Validated..... {0}'.format(file_name))
        try:
            if len(self.place_name) != 3:
                raise ValueError('Input value "{0}" should be made of three characters'.format(self.place_name))
        except ValueError as e:
            print(e)

    def _get_spatial_ref(self, file_path):
        """ Get raster spatial reference """
        try:
            return arcpy.Describe(file_path).spatialReference
        except IOError as (e):
            print(str(e) + ' or is invalid/corrupted. Remove the bad file and run the process again')

    def _delete_raster_file(self, in_file):
        """ Delete extracted file """
        for extracted_file in in_file:
            arcpy.Delete_management(extracted_file)


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    read_file = TrendCorrelation()
    #read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()