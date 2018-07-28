__author__ = "Koech Nicholas"
__copyright__ = "Copyright 208"
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


class RasterUtils:
    def __init__(self):
        self.tool_settings = self._get_user_parameters()
        self.src = self.tool_settings['src_dir']
        self.dest_dir = self.tool_settings['dest_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']
        self.prefix = self.tool_settings['prefix']
        self.suffix = self.tool_settings['suffix']

    def _get_user_parameters(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data('dir_meta', '.json')
        for i in data:
            for j in data[i]:
                if isinstance(j, dict):
                    tool_settings.update(j)
        return tool_settings

    def init_geoprocess(self):
        """ Initialize raster geoprocessing """
        file_paths = self._get_file_path()
        group_file_paths = self._group_files(file_paths)
        self._calculate_mean_raster(group_file_paths)

    def _get_file_path(self):
        """ Gets files source paths """
        file_paths = []
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            file_paths.append(str(file_path))
        return file_paths

    def _group_files(self, file_paths):
        """  Groups files according to provided prefix and suffix """
        group_file_paths = []
        for ids in self._create_file_id():
            common_files = []
            if file_paths:
                for fp in file_paths:
                    for i in ids:
                        if re.search(i, fp, re.I) is not None:
                            common_files.append(str(fp))
                if common_files:
                    group_file_paths.append(common_files)
        return group_file_paths

    def _create_file_id(self):
        """ Creates file identification parameters from provided prefix and suffix """
        for s in self.suffix:
            file_ids = [str(p + s) for p in self.prefix]
            yield file_ids

    def _calculate_mean_raster(self, group_file_paths):
        """ Calculate mean raster """
        stat_type = 'MEAN'
        ignore_nodata = True
        if group_file_paths:
            for ras_files in self._get_list(group_file_paths):
                if ras_files:
                    out_ras_file = self._create_file(ras_files[0], self.dest_dir, 'MEAN_')
                    self._cell_statistics(ras_files, out_ras_file, stat_type, ignore_nodata)

    def _get_list(self, lst):
        """ Gets a list from lists of list """
        for l in lst:
            yield l
        # if any(isinstance(i, list) for i in lst):
        #     for l in lst:
        #         yield l
        # yield lst

    def _create_file(self, in_path, out_dir, join_char):
        """ Create new file name """
        self._create_directory(out_dir)
        file_name = ntpath.basename(in_path)
        out_file_name = join_char + file_name
        new_file = os.path.join(out_dir, out_file_name).replace('\\', '/')
        return new_file

    def _create_directory(self, dest_dir):
        """ Create destination directory if it doesn't exist """
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)  # Create destination folder

    def _cell_statistics(self, in_file, out_file, stat_type, ignore_nodata):
        """ Perform cell statistics """
        print('Processing cell statistics for..... {0}'.format(out_file))
        if ignore_nodata:
            ignore_nodata = 'DATA'
        else:
            ignore_nodata = ''
        arcpy.gp.CellStatistics_sa(in_file, out_file, stat_type, ignore_nodata)


def main():
    """Main program"""
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    raster_util = RasterUtils()
    raster_util.init_geoprocess()

if __name__ == "__main__":
    main()