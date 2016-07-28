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
import re
from readjson import get_json_data
from sourcedirectory import get_directory
import sys
import traceback


class TrendCorrelation:
    def __init__(self):
        self.tool_settings = self._get_user_parameters()
        self.src_var_1 = self.tool_settings['src_dir_1']
        self.data_name_1 = self.tool_settings['datatype_in_filename_1']
        self.data_name_2 = self.tool_settings['datatype_in_filename_2']
        self.data_var = [self.data_name_1, self.data_name_2]
        self.dir_startswith_var_1 = self.tool_settings['dir_startswith_1']
        self.file_startswith_var_1 = self.tool_settings['file_startswith_1']
        self.file_endswith_var_1 = self.tool_settings['file_endswith_1']
        self.src_var_2 = self.tool_settings['src_dir_2']
        self.dir_startswith_var_2 = self.tool_settings['dir_startswith_2']
        self.file_startswith_var_2 = self.tool_settings['file_startswith_2']
        self.file_endswith_var_2 = self.tool_settings['file_endswith_2']
        self.dest_dir = self.tool_settings['dest_dir']
        self.place_name = self.tool_settings['aoi_place_name']
        self.res_fine = self.tool_settings['resample_fine']
        self.res_method = self.tool_settings['resample_method']

    def _get_user_parameters(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data('dir_meta', '.json')
        for i in data:
            for j in data[i]:
                if isinstance(j, dict):
                    tool_settings.update(j)
        return tool_settings

    def init_geoprocess_raster(self):
        """ Initialize raster geoprocessing """
        cell_size, data_years = self._validate_data()  # Validated raster

        if len(cell_size) > 1:
            self._resample_raster(cell_size)  # Modify raster resolution

        if not os.path.exists(self.dest_dir):
            os.makedirs(self.dest_dir)  # Create destination folder

        self._calculate_mean_raster()  # Calculate average raster
        self._calculate_sxy()

        print('RASTER PROCESSING COMPLETED SUCCESSFULLY!!!')

    def _validate_data(self):
        """ Check for  invalid/corrupted data """
        prev_file_path = ''
        ras_resolution = []
        data_years = {}
        data_years_pair = []
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            for source_dir, file_path, file_name in get_file_location(root_dir, file_startswith, file_endswith):
                year = self._validate_file_name(file_name, data_id)  # Check file naming convention and return year
                if year:
                    data_years_pair.append(year)
                self._validate_spatial_ref(file_path, prev_file_path)  # Validate spatial reference
                print('Validated..... {0}'.format(file_name))
                cell_size = self._get_raster_resolution(file_path, ras_resolution)  # Get raster resolution
                if cell_size:
                    ras_resolution.append(cell_size)
                prev_file_path = file_path  # For spatial reference validation
            data_years[data_id] = data_years_pair

        self._validated_place_name()  # Validated area of interest name as three letter acronym
        return ras_resolution, data_years

    def _validate_file_name(self, file_name, data_id):
        """ Validate file name and return year """
        self._validate_data_type(data_id, file_name)  # Validate data type name as set by the user
        data_year = self._validate_data_year(file_name)  # Validate file name and return year
        return data_year

    def _validate_data_type(self, data_id, file_name):
        """ Validate data type name as set by user """
        regex_pattern = r'[^a-zA-Z\d:]' + re.escape(data_id) + r'[^a-zA-Z\d:]'
        match = re.search(regex_pattern, file_name, re.I)
        try:
            if match:
                return None
            else:
                raise ValueError('BAD USER SETTINGS!. "datatype_in_filename_n" should match the data type name recorded in the file name i.e. NDVI, CHIRPS, etc.'.format(data_id))
        except ValueError as e:
            sys.exit(e)

    def _validate_data_year(self, file_name):
        """  Validate file name and return the year """
        regex = re.compile(r'([1-3][0-9]{3})')
        match = regex.search(file_name)
        try:
            if match:
                return match.group()
            else:
                raise ValueError('{} has a bad naming convention. Make sure the file name has year in the format "yyyy"'.format(file_name))
        except ValueError as e:
            sys.exit(e)

    def _validate_spatial_ref(self, file_path, prev_file_path):
        """ Get raster spatial reference """
        try:
            current_spatial_ref = self._get_spatial_ref(file_path)
            if prev_file_path:
                prev_spatial_ref = self._get_spatial_ref(prev_file_path)
                try:
                    if current_spatial_ref.factoryCode == prev_spatial_ref.factoryCode:
                        return current_spatial_ref
                    else:
                        raise ValueError("{} has a different spatial reference. Please correct it and run the process again".format(file_path))
                except ValueError, e:
                    sys.exit(e)
            else:
                return current_spatial_ref
        except IOError as (e):
            print(str(e) + ' or is invalid/corrupted. Remove the bad file and run the process again')

    def _get_spatial_ref(self, file_path):
        """ Describe raster spatial reference """
        return arcpy.Describe(file_path).spatialReference

    def _get_raster_resolution(self, file_path, ras_resolution):
        """ Get all raster files resolution """
        cell_width = self._get_cell_width(file_path)
        if ras_resolution:
            if cell_width not in set(ras_resolution):
                return cell_width
        else:
            return cell_width

    def _validated_place_name(self):
        """ Check place name acronym """
        try:
            if len(self.place_name) != 3:
                raise ValueError('Input value "{0}" should be made of three characters'.format(self.place_name))
        except ValueError as e:
            print(e)

    def _resample_raster(self, cell_size):
        """ Modify raster resolution """
        new_file_startwith = "RES_"
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            for source_dir, file_path, file_name in get_file_location(root_dir, file_startswith, file_endswith):
                fine_cell_size = min(cell_size)
                coarse_cell_size = max(cell_size)
                in_cell_size = self._get_cell_width(file_path)  # For current file
                if self.res_fine:
                    if in_cell_size != fine_cell_size:
                        self._resample_processor(file_path, fine_cell_size, new_file_startwith)  # Resample geoprocessor
                        self._update_file_startwith(file_startswith, new_file_startwith)
                else:
                    if in_cell_size != coarse_cell_size:
                        self._resample_processor(file_path, coarse_cell_size, new_file_startwith)
                        self._update_file_startwith(file_startswith, new_file_startwith)

    def _get_cell_width(self, file_path):
        """ Get raster cell size """
        return arcpy.Describe(file_path).meanCellWidth

    def _resample_processor(self, file_path, cell_size, file_start_char):
        """ Resample image to coarse or fine cell size """
        in_ras = ntpath.basename(file_path)
        out_ras_name = file_start_char + in_ras
        out_ras_dir = ntpath.dirname(file_path)
        out_res_ras = os.path.join(out_ras_dir, out_ras_name).replace('\\', '/')
        print('Resampling..... {}'.format(in_ras))
        arcpy.Resample_management(file_path, out_res_ras, cell_size, self.res_method)

    def _update_file_startwith(self, file_startswith, new_file_startwith):
        """ Update file startswith variable """
        if file_startswith == self.file_startswith_var_1:
            self.file_startswith_var_1 = new_file_startwith + file_startswith
        elif file_startswith == self.file_startswith_var_2:
            self.file_startswith_var_2 = new_file_startwith + file_startswith

    def _calculate_mean_raster(self):
        """ Calculate mean raster """
        stat_type = 'MEAN'
        ignore_nodata = True
        ras_file_list = self._get_mean_calculation_rasters()
        if ras_file_list:
            for ras_files in ras_file_list:
                if ras_files:
                    out_ras_name = 'MEAN_' + ntpath.basename(ras_files[0])
                    out_ras_dir = ntpath.dirname(ras_files[0])
                    out_mean_ras = os.path.join(out_ras_dir, out_ras_name).replace('\\', '/')
                    self._cell_statistics(ras_files, out_mean_ras, stat_type, ignore_nodata)

    def _get_mean_calculation_rasters(self):
        """ Get rasters for mean calculation """
        outer_ras_list = []
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            inner_ras_list = []
            for source_dir, file_path, file_name in get_file_location(root_dir, file_startswith, file_endswith):
                    inner_ras_list.append(file_path)
            outer_ras_list.append(inner_ras_list)
        return outer_ras_list

    def _cell_statistics(self, ras_files, out_mean_ras, stat_type, ignore_nodata):
        """ Perform cell statistics """
        print('Processing cell statistics for..... {0}'.format(out_mean_ras))
        if ignore_nodata:
            ignore_nodata = 'DATA'
        else:
            ignore_nodata = ''
        arcpy.gp.CellStatistics_sa(ras_files, out_mean_ras, stat_type, ignore_nodata)

    def _calculate_sxy(self):
        """ Calculate sxy from; input raster, mean input raster, year and median year """
        mean_rasters = self._get_all_mean_rasters()
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            mean_ras = self._get_mean_raster(mean_rasters, data_id)  # Get averaged raster for calculation
            for source_dir, file_path, file_name in get_file_location(root_dir, file_startswith, file_endswith):
                print(mean_ras + '============' + file_name)

    def _get_all_mean_rasters(self):
        """ Get mean rasters to be used in sxy calculation """
        mean_rasters = []
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            file_startswith = 'MEAN_'
            for source_dir, file_path, file_name in get_file_location(root_dir, file_startswith, file_endswith):
                mean_rasters.append(file_path)
        return mean_rasters

    def _get_mean_raster(self, mean_rasters, data_id):
        """ Identify appropriate average raster to be used in calculation """
        if mean_rasters:
            for ras_file in mean_rasters:
                mean_file_name = ntpath.basename(ras_file)
                match = re.search(data_id, mean_file_name, re.I)  # Wrong
                if match:
                    if match.group().lower() == data_id.lower():
                        return ras_file

    def _get_source_parameters(self, data_var):
        """ Get files root directory """
        try:
            if len(set(data_var)) > 1:
                for i in data_var:
                    if i == self.data_name_1:
                        root_dir, file_startswith, file_endswith = self._set_source_parameters(self.src_var_1, self.dir_startswith_var_1, self.file_startswith_var_1, self.file_endswith_var_1)
                        yield root_dir, file_startswith, file_endswith, i
                    elif i == self.data_name_2:
                        root_dir, file_startswith, file_endswith = self._set_source_parameters(self.src_var_2, self.dir_startswith_var_2, self.file_startswith_var_2, self.file_endswith_var_2)
                        yield root_dir, file_startswith, file_endswith, i
            else:
                raise ValueError('Processing ABORTED! Satellite type settings should not be similar or empty. Please change your settings'.format(self.data_name_1, self.data_name_2))
        except ValueError as e:
            sys.exit(e)

    def _set_source_parameters(self, src_var, dir_startswith_var, file_startswith_var, file_endswith_var):
        """ Set file source parameters """
        root_dir = get_directory(src_var, dir_startswith_var)
        file_startswith = file_startswith_var
        file_endswith = file_endswith_var
        return root_dir, file_startswith, file_endswith

    def _delete_raster_file(self, del_file):
        """ Delete extracted file """
        for f in del_file:
            arcpy.Delete_management(f)


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    read_file = TrendCorrelation()
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()