import os
import arcpy
import ntpath
from arcpy.sa import *
from arcpy import env
from readjson import get_json_data
from sourcedirectory import get_directory


class NDVIProcessor:
    def __init__(self, first_level_key, second_level_key):
        self.first_level_key = first_level_key
        self.second_level_key = second_level_key
        self.file_date_id = []
        self.mos_out_ras = []
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
        for source_dir in root_dir:
            for file_name in os.listdir(source_dir):
                if file_name.startswith(self.file_startswith) & file_name.endswith(self.file_endswith):
                    file_path = os.path.join(source_dir, file_name).replace('\\', '/')
                    if not os.path.exists(self.dest_dir):
                        os.makedirs(self.dest_dir)
                    if self.mosaic_operation:
                        self.mosaic_rasters(file_path)
                    else:
                        self.geoprocess_raster(file_path)
        if self.mosaic_operation:
            if self.mos_out_ras:
                for mos_file_path in self.mos_out_ras:
                    self.geoprocess_raster(mos_file_path)
        print('RASTER PROCESSING COMPLETED SUCCESSFULLY!!!')

    def validate_raster(self):
        """ First check for  invalid/corrupted raster data """
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir in root_dir:
            for file_name in os.listdir(source_dir):
                if file_name.startswith(self.file_startswith) & file_name.endswith(self.file_endswith):
                    file_path = os.path.join(source_dir, file_name).replace('\\', '/')
                    self._get_spatial_ref(file_path)
                    print('Validated..... {0}'.format(file_name))

    def mosaic_rasters(self, file_path):
        """ Get rasters and stitch them together """
        file_name = ntpath.basename(file_path)
        if self.mosaic_operation:
            masked_file_paths = ""
            file_name_date = file_name.split('.')[1]
            if self.file_date_id:
                if file_name_date not in set(self.file_date_id):
                    masked_file_paths = self._mosaic_geoprocessing(file_path)
            else:
                masked_file_paths = self._mosaic_geoprocessing(file_path)
            for masked_file in masked_file_paths:
                arcpy.Delete_management(masked_file)

    def _mosaic_geoprocessing(self, file_path):
        """ Stitch several rasters together """
        masked_file_paths = []
        file_name = ntpath.basename(file_path)
        mos_out_ras_name = 'MOSK_' + file_name[:11] + file_name[-53:]
        mos_out_ras_file = self.dest_dir + '/' + mos_out_ras_name

        for file_paths in self._init_mosaic_raster(file_name):
            print('Mosaic raster..... {0}'.format(mos_out_ras_name))
            if file_paths:
                current_ref, target_ref_name = self._get_spatial_ref(file_paths[0], self.target_ref)
                arcpy.MosaicToNewRaster_management(file_paths, self.dest_dir, mos_out_ras_name, current_ref, '8_BIT_UNSIGNED', '', '1', 'LAST', 'FIRST')
                self.mos_out_ras.append(mos_out_ras_file)
                masked_file_paths.extend(file_paths)
        return masked_file_paths

    def _init_mosaic_raster(self, init_file_name):
        """ Get files to be stitched and preprocess them """
        file_paths = []
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir in root_dir:
            for file_name in os.listdir(source_dir):
                if file_name.startswith(self.file_startswith) & file_name.endswith(self.file_endswith):
                    file_name_date = file_name.split('.')[1]
                    if file_name == init_file_name:
                        masked_out_ras = self._init_mosaic_geoprocess(source_dir, file_name)
                        file_paths.append(masked_out_ras)
                        if file_name_date not in set(self.file_date_id):
                            self.file_date_id.append(file_name_date)
                    else:
                        if file_name_date == init_file_name.split('.')[1]:
                            masked_out_ras = self._init_mosaic_geoprocess(source_dir, file_name)
                            file_paths.append(masked_out_ras)
        yield file_paths

    def _init_mosaic_geoprocess(self, source_dir, file_name):
        """ Project and remove bad/background raster values - set to null """
        proj_out_ras = ""
        where_clause_val1 = "VALUE = 0"
        file_path = os.path.join(source_dir, file_name).replace('\\', '/')
        current_ref, target_ref_name = self._get_spatial_ref(file_path, self.target_ref)
        try:
            if current_ref.name != target_ref_name:
                proj_out_ras = self._reproject_raster(current_ref, target_ref_name, file_path)  # Reproject raster
            else:
                raise ValueError(
                    'Raster processing FAILED! {0} projection is similar to that of the target reference.'.format(
                        current_ref.name))
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
        if self.clip_poly and self.clip_poly.endswith('.shp'):
            if arcpy.Exists(self.clip_poly):
                print('Clipping..... {0} to {1}'.format(ntpath.basename(ndvi_out_ras), ntpath.basename(clip_out_ras)))
                arcpy.Clip_management(ndvi_out_ras, '#', clip_out_ras, self.clip_poly, "", 'ClippingGeometry')
            else:
                raise ValueError('Clipping FAILED! Clipping feature class does not exist')
        else:
            raise ValueError('Clipping FAILED! Clipping geometry not provided')
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
    first_level_key = ['src', 'dest', 'dir_startswith', 'file_startswith', 'file_endswith', 'target_reference', 'aoi_geometry', 'aoi_name', 'mosaic']
    second_level_key = ['src_dir', 'dest_dir', 'dir_param', 'file_start', 'file_end', 'target_ref', 'aoi_poly', 'aoi_place_name', 'mosaic_operation']
    read_file = NDVIProcessor(first_level_key, second_level_key)
    read_file.validate_raster()
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()