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


class RasterReprojector:
    def __init__(self):
        self.file_date_id = []
        self.mos_out_ras = []
        self.clean_ras = []
        self.tool_settings = self._get_user_parameters()
        self.src = self.tool_settings['src_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']
        self.dest_dir = self.tool_settings['dest_dir']
        self.target_ref = self.tool_settings['reproject_to_ESPG']
        self.res_method = self.tool_settings['resample_method']
        self.cell_size = self.tool_settings['cell_size']

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
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):

            # Reproject raster
            proj_out_ras = None
            if self.target_ref:
                current_ref, target_ref = self._get_spatial_ref(file_path, self.target_ref)
                try:
                    if current_ref.name != target_ref.name:
                        proj_out_ras = self._reproject_raster(current_ref, target_ref, file_path)  # Reproject raster
                    else:
                        raise ValueError(
                            'Raster processing FAILED! {0} projection is similar to that of the target reference.'.format(
                                current_ref.name
                            )
                        )
                except ValueError as e:
                    print (e)

            # Resample raster
            if self.res_method:
                if proj_out_ras:
                    self._resample_processor(proj_out_ras)
                else:
                    self._resample_processor(file_path)

    def validate_data(self):
        """ First check for  invalid/corrupted data """
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            self._get_spatial_ref(file_path)
            print('Validated..... {0}'.format(file_name))

    def _reproject_raster(self, current_ref, target_ref, file_path):
        """ Reproject raster """
        file_name = ntpath.basename(file_path)
        proj_out_ras = self.dest_dir + '/PROJ_' + file_name
        print('Projecting..... {0} from {1} to {2}'.format(file_name, current_ref.name, str(target_ref.name)))
        arcpy.ProjectRaster_management(file_path, proj_out_ras, target_ref, '', '', '', '', current_ref)
        return proj_out_ras

    def _get_spatial_ref(self, file_path, target_ref=None):
        """ Get raster spatial reference """
        try:
            desc = arcpy.Describe(file_path)
            current_ref = desc.spatialReference
            if target_ref:
                target_ref = arcpy.SpatialReference(target_ref)
                return current_ref, target_ref
            else:
                return None
        except IOError as (e):
            print(str(e) + ' or is invalid/corrupted. Remove the bad file and run the process again')

    def _resample_processor(self, file_path):
        """ Resample image to coarse or fine cell size """
        out_res_ras = self._create_file_name(file_path)  # Create new file name from existing file
        print('Resampling..... {}'.format(ntpath.basename(file_path)))
        upper_res_method = self.res_method.upper()
        arcpy.Resample_management(file_path, out_res_ras, self.cell_size, upper_res_method)

    def _create_file_name(self, in_path):
        """ Create new file name """
        file_name = ntpath.basename(in_path)
        dir_path = ntpath.dirname(in_path)
        out_ras_name = 'RES_' + file_name
        new_ras_path = os.path.join(dir_path, out_ras_name).replace('\\', '/')
        return new_ras_path


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    read_file = RasterReprojector()
    read_file.validate_data()
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()
