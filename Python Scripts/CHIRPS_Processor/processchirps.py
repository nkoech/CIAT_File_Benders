__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


# import arcpy
from extractdata import extract_data
from ftpdownload import ftp_download
from filelocation import get_file_location
import ntpath
import os
from readjson import get_json_data
from sourcedirectory import get_directory


class ProcessCHIRPS:
    def __init__(self):
        self.tool_settings = self._get_user_parameters()

        self.base_url = self.tool_settings['base_url']
        self.region = self.tool_settings['region']
        self.product = self.tool_settings['product']
        self.year = self.tool_settings['year']
        self.month = self.tool_settings['month']
        self.date = self.tool_settings['date']
        self.extension = self.tool_settings['extension']
        self.download_dir = self.tool_settings['download_dir']

        self.src = self.tool_settings['src_dir'] 
        self.dest_dir = self.tool_settings['dest_dir']
        self.dir_startswith = self.tool_settings['dir_param']
        self.file_startswith = self.tool_settings['file_start']
        self.file_endswith = self.tool_settings['file_end']
        self.clip_poly = self.tool_settings['aoi_poly']
        self.place_name = self.tool_settings['aoi_place_name']
        self.extract_file = self.tool_settings['unzip_file']
        self.cal_sum = self.tool_settings['cal_sum']
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

    def init_geoprocess_raster(self):
        """ Initialize raster geoprocessing """
        self.region = self._lower_case(self.region)
        self.product = self._lower_case(self.product)
        ftp_params = {'base_url': self.base_url, 'region': self.region, 'product': self.product, 'year': self.year,
                      'month': self.month, 'date': self.date, 'extension': self.extension, 'dest': self.download_dir}
        ftp_download(ftp_params)


        # if self.extract_file:
        #     self._uncompress_file()  # Extract file

        # self.validate_data()  # Validated raster

        # if not os.path.exists(self.dest_dir):
        #     os.makedirs(self.dest_dir)  # Create destination folder

        # if not int(self.no_data_val):
        #     self.no_data_val = ''  # Assign NoData value to none

        # if self.cal_sum:
        #     self._calculate_sum_raster()  # Add all rasters
        #     self._clip_raster(self.no_data_val)  # Clip raster
        # else:
        #     self._clip_raster(self.no_data_val)  # Clip raster
        # print('RASTER PROCESSING COMPLETED SUCCESSFULLY!!!')
    
    def _lower_case (self, item):
        """Convert string to lower case"""
        if item:
            if isinstance(item, list):
                lower_items = []
                for i in item:
                    lower_items.append(i.lower())
                return lower_items
            else:
                return item.lower()

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
        except IOError as e:
            print(str(e) + ' or is invalid/corrupted. Remove the bad file and run the process again')

    def _calculate_sum_raster(self):
        """ Add all rasters """
        stat_type = "SUM"
        ignore_nodata = True
        ras_year = self._get_raster_year()
        for year in ras_year:
            ras_files = self._get_sum_rasters(year)
            if ras_files:
                out_ras_name = ntpath.basename(ras_files[0])[:-7] + ".tif"
                out_ras_dir = ntpath.dirname(ras_files[0])
                out_sum_ras = os.path.join(out_ras_dir, out_ras_name).replace('\\', '/')
                self._cell_statistics(ras_files, out_sum_ras, stat_type, ignore_nodata)
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

    def _get_sum_rasters(self, year):
        """ Get rasters for summation """
        ras_file_list = []
        root_dir = get_directory(self.src, self.dir_startswith)
        for source_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
            if file_name[12:16] == year:
                if len(file_name) > 20:
                    ras_file_list.append(file_path)
        return ras_file_list

    def _cell_statistics(self, ras_files, out_sum_ras, stat_type, ignore_nodata):
        """ Perform cell statistics """
        print('Processing cell statistics for..... {0}'.format(out_sum_ras))
        if ignore_nodata:
            ignore_nodata = 'DATA'
        else:
            ignore_nodata = ''
        arcpy.gp.CellStatistics_sa(ras_files, out_sum_ras, stat_type, ignore_nodata)

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
    # arcpy.env.overwriteOutput = True
    # arcpy.CheckOutExtension("spatial")
    read_file = ProcessCHIRPS()
    read_file.init_geoprocess_raster()

if __name__ == '__main__':
    main()
