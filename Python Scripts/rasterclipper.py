__author__ = 'nkoech'

import os
import arcpy
from arcpy import env
from arcpy.sa import *


class RasterClipper(object):
    """Get raster files and clip"""

    def __init__(self, s_dir):
        self.s_dir = s_dir

    def get_dir_paths(self):
        """Get file directory path"""
        tiff_dirs = []
        for root_path, dir_names, files in os.walk(self.s_dir):  # walk through root directory
            for dir_name in dir_names:
                if dir_name == "TRMM":
                    dir_join = os.path.join(root_path, dir_name).replace("\\","/")  # Join rooth to sub-directory
                    tiff_dirs.append(dir_join)
        print(tiff_dirs)
        return tiff_dirs

    def clip_ras(self):
        """Clip all rasters in the directory"""
        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith("TANA_") & file.endswith(".tif"):  # Check if TIF file
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    out_ras = "D:/Data/Projects/Kenya_Upper_Tana/Precipitation/TRMM/Clipped/" + file
                    print("CLIPPING ...... " + file)
                    arcpy.Clip_management(file_path, "36.5442763785232 -1.22080482941539 37.9720188111957 -5.83562203289034E-02", out_ras, "D:/Data/Projects/Kenya_Upper_Tana/Watershed Boundaries/UTNWF_Rectangle_GCS.shp", "-3.40282346639e+038", "ClippingGeometry")
        print("ALL RASTERS CLIPPED SUCCESSFULLY!!!!!")


def main():
    """Main program"""
    # Check out any necessary licenses
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    ras_extractor = RasterClipper("D:/Data/Projects/Kenya_Upper_Tana")
    ras_extractor.clip_ras()

if __name__ == "__main__":
    main()
