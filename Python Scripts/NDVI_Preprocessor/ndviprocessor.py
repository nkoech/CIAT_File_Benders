__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


import os
import arcpy
from arcpy import env
from arcpy.sa import *
from filelocation import get_file_location
import ntpath
from readjson import get_json_data
from sourcedirectory import get_directory


class NDVIProcessor:
    def __init__(self, first_level_key, second_level_key):
        self.first_level_key = first_level_key
        self.second_level_key = second_level_key
        self.file_date_id = []
        self.mos_out_ras = []
        self.clean_ras = []
        self.tool_settings = self._get_user_parameters()
        self.src = self.tool_settings['src_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']
        self.dest_dir = self.tool_settings['dest_dir']
        self.target_ref = self.tool_settings['target_ref']
        self.clip_poly = self.tool_settings['aoi_poly']
        self.place_name = self.tool_settings['aoi_place_name']
        self.mosaic_operation = self.tool_settings['mosaic_operation']
        self.max_val_composite = self.tool_settings['max_value_composite']

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
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            file_name_date = file_name.split('.')[1]
            if not os.path.exists(self.dest_dir):
                os.makedirs(self.dest_dir)
            if self.mosaic_operation or self.max_val_composite:
                self._init_stitch_rasters(file_path, file_name_date)
            else:
                self.geoprocess_raster(file_path)

        # Perform basic preprocessing
        if self.mosaic_operation:
            if self.mos_out_ras:
                for mos_file_path in self.mos_out_ras:
                    self.geoprocess_raster(mos_file_path)

        # Perform cell statistics
        if self.mosaic_operation and self.max_val_composite:
            if self.clean_ras:
                self.mosaic_operation = False
                for clean_file_path in self.clean_ras:
                    file_name_date = ntpath.basename(clean_file_path).split('.')[1]
                    self._init_stitch_rasters(clean_file_path, file_name_date)
        print('RASTER PROCESSING COMPLETED SUCCESSFULLY!!!')

    def validate_data(self):
        """ First check for  invalid/corrupted data """
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            self._get_spatial_ref(file_path)
            print('Validated..... {0}'.format(file_name))
        try:
            if len(self.place_name) != 3:
                raise ValueError('Input value "{0}" should be made of three characters'.format(self.place_name))
        except ValueError as e:
            print(e)

    def _init_stitch_rasters(self, file_path, file_name_date):
        """ Get rasters to stitch, calculate 'Maximum Cell Statistics'"""
        masked_file_paths = None
        if self.max_val_composite and not self.mosaic_operation:
            file_name_date = file_name_date[:4]
        try:
            if int(file_name_date):
                if self.file_date_id:
                    if file_name_date not in set(self.file_date_id):
                        masked_file_paths = self._stitch_rasters(file_path)
                else:
                    masked_file_paths = self._stitch_rasters(file_path)
                if masked_file_paths:
                    for masked_file in masked_file_paths:
                        arcpy.Delete_management(masked_file)
            else:
                raise TypeError("Input file split fail. {0} is not an integer. Fix your file naming to that of MODIS file convention".format(file_name_date))
        except TypeError as e:
            print(e)

    def _stitch_rasters(self, file_path):
        """ Stitch several rasters together, calculate maximum value statistics """
        masked_file_paths = []
        file_name_id = ntpath.basename(file_path)
        stitch_out_ras_name = self._set_stitch_output(file_name_id)
        stitch_out_ras_file = self.dest_dir + '/' + stitch_out_ras_name

        # Perform mosaic and cell statistics
        for file_paths in self._get_stitch_files(file_name_id):
            if file_paths:
                current_ref, target_ref_name = self._get_spatial_ref(file_paths[0], self.target_ref)
                if self.mosaic_operation:
                    pixel_type = '8_BIT_UNSIGNED'
                    mosaic_operator = 'LAST'
                    self._mosaic_to_new_raster(file_paths, self.dest_dir, stitch_out_ras_name, current_ref, pixel_type, mosaic_operator)
                    self.mos_out_ras.append(stitch_out_ras_file)
                    masked_file_paths.extend(file_paths)
                else:
                    if self.max_val_composite and not self.mosaic_operation:
                        stat_type = "MAXIMUM"
                        ignore_nodata = True
                        self._cell_statistics(file_paths, stitch_out_ras_file, stat_type, ignore_nodata)
        if masked_file_paths:
            return masked_file_paths

    def _set_stitch_output(self, file_name_id):
        """ Sets stitch and MVC output location and name """
        stitch_out_ras_name = 'MOSK_' + file_name_id[:11] + file_name_id[-53:]
        mvc_output_dir = "MVC_Output"
        mvc_dest_dir = self.dest_dir + "/" + mvc_output_dir

        # Create directory to store MVC output raster
        if self.max_val_composite and self.mosaic_operation:
            if not os.path.exists(mvc_dest_dir):
                os.makedirs(mvc_dest_dir)

        # Set MVC output file name
        if self.max_val_composite and not self.mosaic_operation:
            first_name_text = file_name_id.split('.')[0]
            text_length = len(first_name_text)
            if os.path.exists(mvc_dest_dir):
                stitch_out_ras_name = mvc_output_dir + '/MVC.' + file_name_id[:text_length + 5] + file_name_id[-45:]
            else:
                stitch_out_ras_name = 'MVC.' + file_name_id[:text_length + 5] + file_name_id[-45:]
        return stitch_out_ras_name

    def _mosaic_to_new_raster(self, file_paths, dest_dir, stitch_out_ras_name, current_ref, pixel_type, mosaic_operator):
        """ Perform mosaicking """
        print('Mosaic raster..... {0}'.format(stitch_out_ras_name))
        arcpy.MosaicToNewRaster_management(file_paths, dest_dir, stitch_out_ras_name, current_ref, pixel_type, '', '1', mosaic_operator, 'FIRST')

    def _cell_statistics(self, file_paths, stat_out_ras_file, stat_type, ignore_nodata):
        """ Perform cell statistics """
        print('Processing cell statistics for..... {0}'.format(stat_out_ras_file))
        if ignore_nodata:
            ignore_nodata = 'DATA'
        else:
            ignore_nodata = ''
        arcpy.gp.CellStatistics_sa(file_paths, stat_out_ras_file, stat_type, ignore_nodata)

    def _get_stitch_files(self, init_file_name):
        """ Get files to be stitched and to calculate maximum values from """
        file_paths = []
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            file_name_date = file_name.split('.')[1]
            file_name_date_id = file_name_date
            if file_name == init_file_name:
                masked_out_ras = file_path
                if self.mosaic_operation:
                    masked_out_ras = self._preprocess_stitch_raster(source_dir, file_name)
                elif self.max_val_composite and not self.mosaic_operation:
                    file_name_date_id = file_name_date[:4]
                file_paths.append(masked_out_ras)
                if file_name_date_id not in set(self.file_date_id):
                    self.file_date_id.append(file_name_date_id)
            else:
                init_file_name_date = init_file_name.split('.')[1]
                if file_name_date == init_file_name_date:
                    masked_out_ras = os.path.join(source_dir, file_name).replace('\\', '/')
                    if self.mosaic_operation:
                        masked_out_ras = self._preprocess_stitch_raster(source_dir, file_name)
                    file_paths.append(masked_out_ras)
                elif file_name_date[:4] == init_file_name_date[:4]:
                    if self.max_val_composite and not self.mosaic_operation:
                        masked_out_ras = os.path.join(source_dir, file_name).replace('\\', '/')
                        file_paths.append(masked_out_ras)
        yield file_paths

    def _preprocess_stitch_raster(self, source_dir, file_name):
        """ Project and remove bad/background raster values - set to null """
        proj_out_ras = None
        where_clause_val1 = "VALUE = 0"
        file_path = os.path.join(source_dir, file_name).replace('\\', '/')
        current_ref, target_ref_name = self._get_spatial_ref(file_path, self.target_ref)
        try:
            if current_ref.name != target_ref_name:
                proj_out_ras = self._reproject_raster(current_ref, target_ref_name, file_path)  # Reproject raster
            else:
                raise ValueError('Raster processing FAILED! {0} projection is similar to that of the target reference.'.format(current_ref.name))
        except ValueError as e:
            print (e)
        masked_file = 'MASKED_' + file_name
        masked_out_ras = self._raster_setnull(proj_out_ras, masked_file, where_clause_val1)  # Set values to null
        arcpy.Delete_management(proj_out_ras)
        return masked_out_ras

    def geoprocess_raster(self, file_path):
        """ Raster geoprocessing interface """
        current_ref, target_ref_name = self._get_spatial_ref(file_path, self.target_ref)
        file_name = ntpath.basename(file_path)[5:]
        proj_out_ras = file_path
        if not self.mosaic_operation:
            file_name = ntpath.basename(file_path)
            try:
                if current_ref.name != target_ref_name:
                    # Reproject input raster
                    proj_out_ras = self._reproject_raster(current_ref, target_ref_name, file_path)
                else:
                    raise ValueError('Raster processing FAILED! {0} projection is similar to that of the target reference.'.format(current_ref.name))
            except ValueError as e:
                print(e)

        # Convert raster values to float values
        ndvi_out_ras = self._raster_to_float(proj_out_ras)
        arcpy.Delete_management(proj_out_ras)

        # Clip raster to area of interest
        clip_out_ras = self. _clip_raster(ndvi_out_ras)
        arcpy.Delete_management(ndvi_out_ras)

        # Set bad raster values to null
        where_clause_val1 = "VALUE > 1"
        where_clause_val2 = "VALUE < -1"
        masked_file = self.place_name + file_name[-54:]
        if self.mosaic_operation:
            masked_file = self.place_name + file_name[-53:]
        masked_out_ras = self._raster_setnull(clip_out_ras, masked_file, where_clause_val1, where_clause_val2)
        self.clean_ras.append(masked_out_ras)
        arcpy.Delete_management(clip_out_ras)

    def _get_spatial_ref(self, file_path, target_ref=None):
        """ Get raster spatial reference """
        try:
            desc = arcpy.Describe(file_path)
            current_ref = desc.spatialReference
            if target_ref:
                target_ref_name = target_ref.split('[')[1].split(',')[0].strip("'")
                return current_ref, target_ref_name
            else:
                return
        except IOError as (e):
            print(str(e) + ' or is invalid/corrupted. Remove the bad file and run the process again')

    def _reproject_raster(self, current_ref, target_ref_name, file_path):
        """ Reproject raster """
        file_name = ntpath.basename(file_path)
        proj_out_ras = self.dest_dir + '/PROJ_' + file_name
        print('Projecting..... {0} from {1} to {2}'.format(file_name, current_ref.name, target_ref_name))
        arcpy.ProjectRaster_management(file_path, proj_out_ras, '"' + self.target_ref + '"', '', '', '', '', current_ref)
        return proj_out_ras

    def _raster_to_float(self, proj_out_ras):
        """ Convert integer raster values to float values """
        print('Converting to NDVI values..... {0}'.format(ntpath.basename(proj_out_ras)))
        float_out_ras = (Raster(proj_out_ras) - 50) / 200.0
        ndvi_out_ras = self.dest_dir + '/NDVI_' + ntpath.basename(proj_out_ras)[5:]
        print('Saving rescaled raster..... {0}'.format(ntpath.basename(ndvi_out_ras)))
        float_out_ras.save(ndvi_out_ras)
        return ndvi_out_ras

    def _clip_raster(self, ndvi_out_ras):
        """ Clip raster to area of interest """
        clip_out_ras = self.dest_dir + '/CLIPPED_' + ntpath.basename(ndvi_out_ras)[5:]
        try:
            if self.clip_poly and self.clip_poly.endswith('.shp'):
                try:
                    if arcpy.Exists(self.clip_poly):
                        print('Clipping..... {0} to {1}'.format(ntpath.basename(ndvi_out_ras), ntpath.basename(clip_out_ras)))
                        arcpy.Clip_management(ndvi_out_ras, '#', clip_out_ras, self.clip_poly, "", 'ClippingGeometry')
                    else:
                        raise IOError('Clipping FAILED! Clipping feature class {0} does not exist'.format(self.clip_poly))
                except IOError as e:
                    print(e)
            else:
                raise ValueError('Clipping FAILED! Clipping geometry not provided')
        except ValueError as e:
            print(e)
        return clip_out_ras

    def _raster_setnull(self, in_ras, masked_file, where_clause_val1, where_clause_val2=None):
        """ Set raster values to null values """
        masked_out_ras = self.dest_dir + '/' + masked_file
        if where_clause_val2:
            print('Removing bad NDVI values..... {0}'.format(ntpath.basename(in_ras)))
            out_set_null = SetNull(in_ras, in_ras, where_clause_val1 or where_clause_val2)
        else:
            print('Removing bad raster values..... {0}'.format(ntpath.basename(in_ras)))
            out_set_null = SetNull(in_ras, in_ras, where_clause_val1)
        print('Saving masked raster..... {0}'.format(masked_file))
        out_set_null.save(masked_out_ras)
        return masked_out_ras


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    first_level_key = ['src', 'dest', 'dir_startswith', 'file_startswith', 'file_endswith', 'target_reference', 'aoi_geometry', 'aoi_name', 'mosaic', 'max_composite']
    second_level_key = ['src_dir', 'dest_dir', 'dir_param', 'file_start', 'file_end', 'target_ref', 'aoi_poly', 'aoi_place_name', 'mosaic_operation', 'max_value_composite']
    read_file = NDVIProcessor(first_level_key, second_level_key)
    read_file.validate_data()
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()