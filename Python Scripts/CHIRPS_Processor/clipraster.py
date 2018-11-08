__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import arcpy
from filelocation import get_file_location
import ntpath
import os
from readjson import get_json_data
from sourcedirectory import get_directory


class ClipRaster:
    def __init__(self):
        self.tool_settings = self._get_user_parameters()
        self.src = self.tool_settings['src_dir'] 
        self.dest_dir = self.tool_settings['dest_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']
        self.clip_poly = self.tool_settings['aoi_poly']
        self.place_name = self.tool_settings['aoi_place_name']
        self.no_data_val = self.tool_settings['no_data_value']

    def _get_user_parameters(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data('dir_meta', '.json')
        for i in data:
            for j in data[i]:
                if isinstance(j, dict):
                    tool_settings.update(j)
        return tool_settings

    def init_clip_raster(self):
        """Initialize raster clipping"""
        self.validate_data()  # Validated raster
        self._clip_raster(self.no_data_val)  # Clip raster

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
        except IOError as e:
            print(str(e) + ' or is invalid/corrupted. Remove the bad file and run the process again')

    def _clip_raster(self, no_data_val):
        """Clip raster to area of interest"""
        root_dir = get_directory(self.src, self.dir_startswith)
        try:
            if self.clip_poly and self.clip_poly.endswith('.shp') and arcpy.Exists(self.clip_poly):
                for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
                    clipped_ras = os.path.join(self.dest_dir, file_name).replace('\\', '/')
                    if self.place_name:
                        clipped_ras = os.path.join(self.dest_dir, self.place_name + '_' + file_name).replace('\\', '/')
                    arcpy.Clip_management(file_path, '#', clipped_ras, self.clip_poly, no_data_val, 'ClippingGeometry')
                    print('Clipped: {0}'.format(clipped_ras))
            else:
                raise ValueError('Clipping FAILED! Clipping geometry not provided')
        except ValueError as e:
            print(e)
            

def main():
    """Main program"""
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    clip = ClipRaster()
    clip.init_clip_raster()

if __name__ == '__main__':
    main()
