__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import arcpy
from arcpy import env
from arcpy.sa import *
from filelocation import get_file_location
import ntpath
import numpy
import os
import re
from readjson import get_json_data
from sourcedirectory import get_directory
import sys


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
        slope_out_rasters, sxx_out_values, sxy_out_rasters, raw_mean_ras_startswith = self._calculate_slope(data_years)  # Calculate Sxy raster

        slope_test_out_rasters, syy_out_rasters = self._slope_test(data_years, slope_out_rasters, sxx_out_values, sxy_out_rasters, raw_mean_ras_startswith)  # Slope hypothesis testing (t0)

        print('RASTER PROCESSING COMPLETED SUCCESSFULLY!!!')

    def _validate_data(self):
        """ Check for  invalid/corrupted data """
        prev_file_path = ''
        ras_resolution = []
        data_years = {}
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            data_years_pair = []
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
            data_years[str(data_id)] = data_years_pair

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
                        self._resample_processor(file_path, fine_cell_size, new_file_startwith, self.res_method)  # Resample geoprocessor
                        self._update_file_startwith(file_startswith, new_file_startwith)
                else:
                    if in_cell_size != coarse_cell_size:
                        res_method = 'NEAREST'
                        self._resample_processor(file_path, coarse_cell_size, new_file_startwith, res_method)
                        self._update_file_startwith(file_startswith, new_file_startwith)

    def _get_cell_width(self, file_path):
        """ Get raster cell size """
        return arcpy.Describe(file_path).meanCellWidth

    def _resample_processor(self, file_path, cell_size, file_start_char, res_method):
        """ Resample image to coarse or fine cell size """
        out_res_ras = self._create_file_name(file_path, file_start_char)  # Create new file name from existing file
        print('Resampling..... {}'.format(ntpath.basename(file_path)))
        arcpy.Resample_management(file_path, out_res_ras, cell_size, res_method)

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
                    out_mean_ras = self._create_file_name(ras_files[0], 'MEAN_')
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

    def _calculate_slope(self, data_years):
        """ Calculate sxy from; input raster, mean input raster, year and median year """
        sxx_out_values = {}
        slope_out_rasters = {}
        sxy_out_rasters = {}
        sxy_ras_startswith = 'SXY_'
        raw_mean_ras_startswith = 'MRAW_'
        mean_rasters = self._get_all_mean_rasters()
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            mean_ras = self._get_mean_raster(mean_rasters, data_id)  # Calculate averaged raster
            median_year = self._get_median_year(data_years, data_id)  # Calculate average year as median
            sxx_out_val = self._calculate_sxx(data_years, data_id, median_year)  # Calculate sxx value
            sxx_out_values[str(data_id)] = sxx_out_val
            sxy_out_ras = self._calculate_sxy(root_dir, file_startswith, file_endswith, mean_ras, median_year, raw_mean_ras_startswith, sxy_ras_startswith)  # Calculate sxy raster
            sxy_out_rasters[str(data_id)] = str(sxy_out_ras)
            #  Calculate slope raster
            slope_out_ras = self._create_ouput_file_name('SLOPE_', self.place_name, data_id, self.dest_dir, '.tif')  # Create final raster name
            print('Calculating..... {0}'.format(slope_out_ras))
            temp_out_ras = arcpy.Raster(sxy_out_ras)/sxx_out_val
            print('Saving..... {0}'.format(slope_out_ras))
            temp_out_ras.save(slope_out_ras)
            slope_out_rasters[str(data_id)] = str(slope_out_ras)
        return slope_out_rasters, sxx_out_values, sxy_out_rasters, raw_mean_ras_startswith

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
                match = re.search(data_id, mean_file_name, re.I)
                if match:
                    if match.group().lower() == data_id.lower():
                        return ras_file

    def _get_median_year(self, data_years, data_id):
        """ Calculate median year from list """
        for k, v in data_years.items():
            if k == data_id:
                return numpy.median(numpy.array(sorted(v)))

    def _calculate_sxx(self, data_years, data_id, median_year):
        """ Calculate and return sxx """
        out_sxx = 0
        for k, v in data_years.items():
            if k == data_id:
                for year in v:
                    out_sxx += (year - median_year)**2
        return(out_sxx)

    def _calculate_sxy(self, root_dir, file_startswith, file_endswith, mean_ras, median_year, raw_mean_ras_startwith, sxy_ras_startswith):
        """ Calculate and return sxy raster """
        sxy_out_ras = ''
        first_sxy_out_ras = ''
        del_rasters = []
        for source_dir, file_path, file_name in get_file_location(root_dir, file_startswith, file_endswith):
            data_year = self._validate_data_year(file_name)  # Get raster year
            out_raw_mean_ras = os.path.join(source_dir, raw_mean_ras_startwith + file_name).replace('\\', '/')
            print('Calculating..... {0}'.format(out_raw_mean_ras))
            temp_raw_mean_ras = arcpy.Raster(file_path) - arcpy.Raster(mean_ras)
            print('Saving..... {0}'.format(out_raw_mean_ras))
            temp_raw_mean_ras.save(out_raw_mean_ras)
            sxy_out_ras_name = sxy_ras_startswith + file_name
            # Calculate Sxy raster
            sxy_out_ras, first_sxy_out_ras, del_raster = self._calculate_sxy_syy(sxy_out_ras_name, sxy_out_ras, first_sxy_out_ras, source_dir, file_path, data_year, median_year, temp_raw_mean_ras)
            if del_raster:
                del_rasters.append(del_raster)
        self._delete_raster_file(del_rasters)  # Delete collected rasters
        self._delete_raster_file(mean_ras)  # Delete mean raster
        return sxy_out_ras

    def _slope_test(self, data_years, slope_out_rasters, sxx_out_values, sxy_out_rasters, raw_mean_ras_startswith):
        """ Slope hypothesis testing (t0)"""
        slope_test_out_rasters ={}
        se_out_rasters, syy_out_rasters = self._calculate_standard_error(data_years, slope_out_rasters, sxx_out_values, sxy_out_rasters, raw_mean_ras_startswith)
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            slope_ras = self._get_calculated_raster(slope_out_rasters, data_id)
            se_ras = self._get_calculated_raster(se_out_rasters, data_id)
            slope_test_out_ras = self._create_ouput_file_name('SLOPE_TEST_', self.place_name, data_id, self.dest_dir, '.tif')
            print('Calculating..... {0}'.format(slope_test_out_ras))
            temp_out_ras = arcpy.Raster(slope_ras) / arcpy.Raster(se_ras)
            print('Saving..... {0}'.format(slope_test_out_ras))
            temp_out_ras.save(slope_test_out_ras)
            slope_test_out_rasters[str(data_id)] = str(slope_test_out_ras)
        return slope_test_out_rasters, syy_out_rasters

    def _calculate_standard_error(self, data_years, slope_out_rasters, sxx_out_values, sxy_out_rasters, raw_mean_ras_startswith):
        """ Calculate standard error """
        se_out_rasters = {}
        rss_ras_startswith = 'RSS_'
        rss_out_rasters, syy_out_rasters = self._calculate_rss(slope_out_rasters, sxy_out_rasters, raw_mean_ras_startswith, rss_ras_startswith)  # Compute residual sum of squares
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            rss_ras = self._get_calculated_raster(rss_out_rasters, data_id)  # Get intermediate raster
            data_yr = self._get_calculated_raster(data_years, data_id)  # Get data year
            data_yr_cal = float(len(data_yr) - 2)
            sxx_value = self._get_calculated_raster(sxx_out_values, data_id)
            se_out_ras = self._create_ouput_file_name('SE_', self.place_name, data_id, self.dest_dir, '.tif')
            print('Calculating..... {0}'.format(se_out_ras))
            temp_out_ras = SquareRoot(arcpy.Raster(rss_ras)/(data_yr_cal * sxx_value))
            print('Saving..... {0}'.format(se_out_ras))
            temp_out_ras.save(se_out_ras)
            se_out_rasters[str(data_id)] = str(se_out_ras)
            # self._delete_raster_file(rss_ras)
        return se_out_rasters, syy_out_rasters

    def _calculate_rss(self, slope_out_rasters, sxy_out_rasters, raw_mean_ras_startswith, rss_ras_startswith):
        """ Compute residual sum of squares """
        syy_out_rasters = {}
        rss_out_rasters = {}
        syy_ras_startswith = 'SYY_'
        for root_dir, file_startswith, file_endswith, data_id in self._get_source_parameters(self.data_var):
            syy_out_ras = self._calculate_syy(root_dir, raw_mean_ras_startswith, file_endswith, syy_ras_startswith)  # Calculate Syy variable
            syy_out_rasters[str(data_id)] = str(syy_out_ras)
            slope_ras = self._get_calculated_raster(slope_out_rasters, data_id)
            sxy_ras = self._get_calculated_raster(sxy_out_rasters, data_id)
            rss_out_ras = self._create_file_name(syy_out_ras, rss_ras_startswith, syy_ras_startswith)
            print('Calculating..... {0}'.format(rss_out_ras))
            temp_out_ras = arcpy.Raster(syy_out_ras) - (arcpy.Raster(slope_ras) * arcpy.Raster(sxy_ras))
            print('Saving..... {0}'.format(rss_out_ras))
            temp_out_ras.save(rss_out_ras)
            rss_out_rasters[str(data_id)] = str(rss_out_ras)
        return rss_out_rasters, syy_out_rasters

    def _calculate_syy(self, root_dir, raw_mean_ras_startswith, file_endswith, syy_ras_startswith):
        """ Calculate and return Syy raster """
        del_rasters = []
        syy_out_ras = ''
        first_syy_out_ras = ''
        for source_dir, file_path, file_name in get_file_location(root_dir, raw_mean_ras_startswith, file_endswith):
            syy_out_ras_name = syy_ras_startswith + file_name[len(raw_mean_ras_startswith):]
            # Calculate Syy raster
            syy_out_ras, first_syy_out_ras, del_raster = self._calculate_sxy_syy(syy_out_ras_name, syy_out_ras, first_syy_out_ras, source_dir, file_path)
            if del_raster:
                del_rasters.append(del_raster)
        self._delete_raster_file(del_rasters)  # Delete collected rasters
        return syy_out_ras

    def _calculate_sxy_syy(self, out_ras_name, out_ras, first_out_ras, source_dir, file_path=None, data_year=None, median_year=None, temp_raw_mean_ras=None):
        """ Calculate both Sxy and Syy """
        del_raster = ''
        if out_ras:
            if out_ras == first_out_ras:
                pass
            else:
                print('Calculating..... {0}'.format(out_ras))
            if median_year:
                temp_out_ras = arcpy.Raster(out_ras) + ((data_year - median_year) * temp_raw_mean_ras)
            else:
                temp_out_ras = arcpy.Raster(out_ras) + (arcpy.Raster(file_path) ** 2)
            del_raster = out_ras  # Collect unwanted rasters to be deleted
            out_ras = os.path.join(source_dir, out_ras_name).replace('\\', '/')
        else:
            out_ras = os.path.join(source_dir, out_ras_name).replace('\\', '/')
            first_out_ras = out_ras
            print('Calculating..... {0}'.format(out_ras))
            if median_year:
                temp_out_ras = (data_year - median_year) * temp_raw_mean_ras
            else:
                temp_out_ras = arcpy.Raster(file_path) ** 2
        print('Saving..... {0}'.format(out_ras))
        temp_out_ras.save(out_ras)
        return out_ras, first_out_ras, del_raster

    def _get_calculated_raster(self, in_raster, data_id):
        """ Get intermediate raster to be used in further calculation """
        for k, v in in_raster.items():
            if k == data_id:
                return v

    def _create_file_name(self, in_path, join_char, ras_startswith=None):
        """ Create new file name """
        file_name = ntpath.basename(in_path)
        dir_path = ntpath.dirname(in_path)
        if ras_startswith:
            out_ras_name = join_char + file_name[len(ras_startswith):]
        else:
            out_ras_name = join_char + file_name
        new_ras_path = os.path.join(dir_path, out_ras_name).replace('\\', '/')
        return new_ras_path

    def _create_ouput_file_name(self, join_char, place_name, data_id, file_dest, file_ext):
        """ Final output file name """
        ras_name = join_char + place_name + '_' + data_id + file_ext
        final_out_ras = os.path.join(file_dest, ras_name).replace('\\', '/')
        return final_out_ras

    def _validate_data_year(self, file_name):
        """  Validate file name and return the year """
        regex = re.compile(r'([1-3][0-9]{3})')
        match = regex.search(file_name)
        try:
            if match:
                return int(match.group())
            else:
                raise ValueError('{} has a bad naming convention. Make sure the file name has year in the format "yyyy"'.format(file_name))
        except ValueError as e:
            sys.exit(e)

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
        if type(del_file) is list:
            for f in del_file:
                arcpy.Delete_management(f)
        else:
            arcpy.Delete_management(del_file)


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    read_file = TrendCorrelation()
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()