__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2014, CIAT"
__license__ = "GPL"
__maintainer__ = "Koech Nicholas"
__email__ = "n.koech@cgiar.org"
__status__ = "Alpha"

import os
import arcpy
from arcpy import env
from arcpy.sa import *


class RasterManager(object):
    """Manages big number of raster datasets"""

    def get_dir_paths(self):
        """Get file directory path"""
        tiff_dirs = []
        for root_path, dir_names, files in os.walk("C:/CCAFS_DATA"):  # walk through root directory
            for dir_name in dir_names:
                for dir_Output in dir_name.split("_"):  # Split sub-directory names
                    if dir_Output == "SRTMCombined":
                        dir_join = os.path.join(root_path, dir_name).replace("\\","/")  # Join rooth to sub-directory
                        tiff_dirs.append(dir_join)
        return tiff_dirs

    def rename_dataset(self):
        """ Rename rasters in sub-directories """
        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith('LDM') & file.endswith('.tif'):  # Get necessary raster files
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    out_ras = source_path + "/Africa_GLC30m.tif"
                    print("RENAMING ...... " + file + " TO " + file[-20:])
                    arcpy.Rename_management(file_path, out_ras)  # Rename files

    def set_null(self):
        """ Set raster 0 values to NoData """
        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                #if (file.startswith('n') | file.startswith('s')) & file.endswith('.tif'):
                if file.startswith('Africa') & file.endswith('.tif'):  # Get necessary raster files
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    out_ras = source_path + "/Africa_GLC30m.tif"
                    print("SETTING NODATA VALUES FOR ......... " + file)
                    raster_nodata = SetNull(Raster(file_path) == 255, Raster(file_path))
                    raster_nodata.save(out_ras)
        print("SETNULL GEOPROCESSING COMPLETED!!!")

    def transform_ras(self):
        """ Tranform raster from one co-ordinate system to another """
        target_name = self.get_targetRef()[0]  # Get target reference system
        target_ref = self.get_targetRef()[1]
        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if (file.startswith('n') | file.startswith('s')) & file.endswith('.tif'):
                #if file.startswith("s") & file.endswith(".tif"):  # Get necessary raster files
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    desc = arcpy.Describe(file_path)
                    current_ref = desc.spatialReference  # Get input raster reference system
                    if current_ref.name != target_name:
                        out_ras = source_path + "/GCS_" + file[-20:]  # set
                        print("TRANSFORMING ..... " + file + " FROM " + current_ref.name + " TO " + target_name)
                        arcpy.ProjectRaster_management(file_path, out_ras, target_ref, "NEAREST", "", "", "", current_ref)  # Transform reference system
        print("TRANSFORMATION COMPLETED SUCCESSFULLY!!!")

    def get_targetRef(self):
        """Get target spatial reference name"""
        ref_name = ""
        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith('Target') & file.endswith('.tif'):  # Get target raster file
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    desc = arcpy.Describe(file_path)
                    spatial_ref = desc.spatialReference  # Get target raster reference system
                    ref_name = spatial_ref.name
        return ref_name, spatial_ref

    def mosaic_ras(self):
        """Get files and mosaic them using a mosaic gp"""
        for source_path in self.get_dir_paths():
            ras_input = []
            for file in os.listdir(source_path):
                if (file.startswith('n') | file.startswith('s')) & file.endswith('.tif'):
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    ras_input.append(file_path)
            print("MOSAICKING IMAGES. PLEASE WAIT ........")
            arcpy.MosaicToNewRaster_management(ras_input, source_path, "Africa_SRTM_30m.tif", "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", "16_BIT_SIGNED", "0.00027777778", "1", "LAST", "FIRST")
            #arcpy.MosaicToNewRaster_management(ras_input, source_path, "Africa_SRTM_30m.tif", "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")
        print("MOSAIC GENERATION COMPLETED!!!")

def main():
    """ Main program """
    # Check out any necessary licenses
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    nullsetter = RasterManager()
    nullsetter.mosaic_ras()
    #nullsetter.transform_ras()
    #nullsetter.set_null()
    #nullsetter.rename_dataset()

if __name__ == "__main__":
    main()



