import os
import arcpy
from arcpy.sa import *
from arcpy import env
from readjson import get_json_data
from sourcedirectory import get_directory


class NDVIProcessor:
    def __init__(self, first_level_key, second_level_key):
        self.first_level_key = first_level_key
        self.second_level_key = second_level_key
        self.tool_settings = self.get_data()
        self.src = self.tool_settings['src_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']
        self.dest_dir = self.tool_settings['dest_dir']
        self.target_ref = self.tool_settings['target_ref']
        self.clip_poly = self.tool_settings['clip_poly']

    def get_data(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data("dir_meta", ".json")
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
                    current_ref, target_ref_name = self._get_spatial_ref(file_path, self.target_ref)
                    self.geoprocess_raster(file_name, current_ref, target_ref_name, file_path)
        print("RASTER PROCESSING COMPLETED SUCCESSFULLY!!!")

    def validate_raster(self):
        """ First check for  invalid/corrupted raster data """
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir in root_dir:
            for file_name in os.listdir(source_dir):
                if file_name.startswith(self.file_startswith) & file_name.endswith(self.file_endswith):
                    file_path = os.path.join(source_dir, file_name).replace('\\', '/')
                    self._get_spatial_ref(file_path)
                    print("Validated..... {0}".format(file_name))

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
            print(str(e) + " or is invalid/corrupted. Remove the bad file and run the process again")

    def geoprocess_raster(self, file_name, current_ref, target_ref_name, file_path):
        """ Project, calculate float values and clip raster to the area of interest """
        proj_out_ras = self.dest_dir + '/PROJ_' + file_name
        try:
            if current_ref.name != target_ref_name:
                print('Projecting..... {0} from {1} to {2}'.format(file_name, current_ref.name, target_ref_name))
                arcpy.ProjectRaster_management(file_path, proj_out_ras, '"' + self.target_ref + '"', '', '', '', '', current_ref)
                print('Calculating float values for..... PROJ_{0}'.format(file_name))
                float_out_ras = (Raster(proj_out_ras) - 50) / 200.0
                ndvi_out_ras = self.dest_dir + '/NDVI_' + file_name
                print('Saving rescaled raster..... {0}'.format('NDVI_' + file_name))
                float_out_ras.save(ndvi_out_ras)
                arcpy.Delete_management(proj_out_ras)
                clip_out_ras = self.dest_dir + '/AOI_NDVI_' + file_name
                if self.clip_poly and self.clip_poly.endswith('.shp'):
                    if arcpy.Exists(self.clip_poly):
                        print('Clipping..... {0} to {1}'.format('NDVI_' + file_name, 'AOI_NDVI_' + file_name))
                        arcpy.Clip_management(ndvi_out_ras, '#', clip_out_ras, self.clip_poly, "", 'ClippingGeometry')
                        arcpy.Delete_management(ndvi_out_ras)
                        # print('Condition for {0}'.format('AOI_NDVI_' + file_name))
                        # con_out_ras = self.dest_dir + '/CON_NDVI_' + file_name
                        # out_set_null = SetNull(clip_out_ras, clip_out_ras, "VALUE > 1" or "VALUE < -1")
                        # out_set_null.save(con_out_ras)
                    else:
                        raise ValueError('Clipping FAILED! Clipping feature class does not exist')
                else:
                    raise ValueError('Clipping FAILED! Clipping geometry not provided')
            else:
                raise ValueError('Raster processing FAILED! {0} projection is similar to that of the target reference.'.format(current_ref.name))
        except ValueError as e:
            print(e)


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    first_level_key = ['src', 'dest', 'dir_startswith', 'file_startswith', 'file_endswith', 'target_reference', 'clip_geometry']
    second_level_key = ['src_dir', 'dest_dir', 'dir_param', 'file_start', 'file_end', 'target_ref', 'clip_poly']
    read_file = NDVIProcessor(first_level_key, second_level_key)
    read_file.validate_raster()
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()