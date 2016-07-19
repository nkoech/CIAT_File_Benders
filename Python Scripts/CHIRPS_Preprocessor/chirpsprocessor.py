__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import arcpy
from arcpy import env
from arcpy.sa import *
from extractdata import extract_data
from filelocation import get_file_location
import ntpath
import os
from readjson import get_json_data
from sourcedirectory import get_directory


class CHIRPSProcessor:
    def __init__(self, first_level_key, second_level_key):
        self.first_level_key = first_level_key
        self.second_level_key = second_level_key
        self.tool_settings = self._get_user_parameters()
        self.src = self.tool_settings['src_dir']
        self.dest_dir = self.tool_settings['dest_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']
        self.clip_poly = self.tool_settings['aoi_poly']
        self.place_name = self.tool_settings['aoi_place_name']
        self.extract_file = self.tool_settings['unzip_file']
        self.cal_mean = self.tool_settings['ras_mean']
        self.no_data_val = self.tool_settings['no_data_value']

    def _get_user_parameters(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data('dir_meta', '.json')
        for key_1, key_2 in zip(self.first_level_key, self.second_level_key):
            for key in data[key_1]:
                value = key[key_2]
                tool_settings[key_2] = value
        return tool_settings

    def init_geoprocess_raster(self):
        """ Initialize raster geoprocessing """
        if self.extract_file:
            self._uncompress_file()  # Extract file

        self.validate_data()  # Validated raster

        if not os.path.exists(self.dest_dir):
            os.makedirs(self.dest_dir)  # Create destination folder

        if not int(self.no_data_val):
            self.no_data_val = ''  # Assign NoData value to none

        if self.cal_mean:
            self._calculate_mean_raster()  # Calculate mean  raster
            self._clip_raster(self.no_data_val)  # Clip raster
        else:
            self._clip_raster(self.no_data_val)  # Clip raster
        print('RASTER PROCESSING COMPLETED SUCCESSFULLY!!!')

    def _uncompress_file(self):
        """ Uncompress file """
        fname_endswith = '.gz'
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            print('Extracting..... {0}'.format(file_name))
            extract_data(source_dir, file_path, file_name, fname_endswith)
        self.file_endswith = '.tif'

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

    def _calculate_mean_raster(self):
        """ Calculate mean raster """
        stat_type = "MEAN"
        ignore_nodata = True
        ras_year = self._get_raster_year()
        for year in ras_year:
            ras_files = self._get_mean_rasters(year)
            if ras_files:
                out_ras_name = ntpath.basename(ras_files[0])[:-7] + ".tif"
                out_ras_dir = ntpath.dirname(ras_files[0])
                out_mean_ras = os.path.join(out_ras_dir, out_ras_name).replace('\\', '/')
                self._cell_statistics(ras_files, out_mean_ras, stat_type, ignore_nodata)
                self._delete_raster_file(ras_files)

    def _get_raster_year(self):
        """ Get year that raster represents """
        ras_year = []
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            file_year = file_name[12:16]
            if file_year not in set(ras_year):
                ras_year.append(file_year)
        return ras_year

    def _get_mean_rasters(self, year):
        """ Get rasters for mean calculation """
        ras_file_list = []
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            if file_name[12:16] == year:
                if len(file_name) > 20:
                    ras_file_list.append(file_path)
        return ras_file_list

    def _cell_statistics(self, ras_files, out_mean_ras, stat_type, ignore_nodata):
        """ Perform cell statistics """
        print('Processing cell statistics for..... {0}'.format(out_mean_ras))
        if ignore_nodata:
            ignore_nodata = 'DATA'
        else:
            ignore_nodata = ''
        arcpy.gp.CellStatistics_sa(ras_files, out_mean_ras, stat_type, ignore_nodata)

    def _clip_raster(self, no_data_val):
        """ Clip raster to area of interest """
        root_dir = get_directory(self.src, self.dir_startswith)
        try:
            if self.clip_poly and self.clip_poly.endswith('.shp') and arcpy.Exists(self.clip_poly):
                for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
                    clipped_ras = os.path.join(self.dest_dir, self.place_name + '_' + file_name).replace('\\', '/')
                    print('Clipping..... {0} to {1}'.format(file_name, ntpath.basename(clipped_ras)))
                    arcpy.Clip_management(file_path, '#', clipped_ras, self.clip_poly, no_data_val, 'ClippingGeometry')
            else:
                raise ValueError('Clipping FAILED! Clipping geometry not provided')
        except ValueError as e:
            print(e)

    def _delete_raster_file(self, in_file):
        """ Delete extracted file """
        for extracted_file in in_file:
            arcpy.Delete_management(extracted_file)


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    first_level_key = ['src', 'dest', 'dir_startswith', 'file_startswith', 'file_endswith', 'aoi_geometry', 'aoi_name', 'extract_file', 'cal_mean', 'no_data']
    second_level_key = ['src_dir', 'dest_dir', 'dir_param', 'file_start', 'file_end', 'aoi_poly', 'aoi_place_name', 'unzip_file', 'ras_mean', 'no_data_value']
    read_file = CHIRPSProcessor(first_level_key, second_level_key)
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()