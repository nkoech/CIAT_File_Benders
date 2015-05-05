__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2014, CIAT"
__license__ = "GPL"
__maintainer__ = "Koech Nicholas"
__email__ = "n.koech@cgiar.org"
__status__ = "Alpha"

import os
import calendar
import arcpy
from arcpy import env
from arcpy.sa import *


class NetCdfConverter(object):
    """Get NetCDF files and convert them to TIFF"""

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
        return tiff_dirs

    def convert_netcdf(self):
        """Convert NetCDF to a different file type"""

        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith("3B43") & file.endswith(".nc"):
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    out_ras = source_path + "/TIFF_" + file[-23:-7] + ".tif"
                    out_pcp = file[-23:-7]
                    print("CONVERTING ...... " + file + " TO TIFF")
                    arcpy.MakeNetCDFRasterLayer_md(file_path, "pcp", "longitude", "latitude", out_pcp, "", "", "BY_VALUE")  # Make NetCDF Raster Layer
                    arcpy.CopyRaster_management(out_pcp, out_ras, "", "", "-9999.90039063", "NONE", "NONE", "32_BIT_FLOAT", "NONE", "NONE")  # Copy Raster
        print("ALL FILES CONVERTED SUCCESSFULLY!!!!!")

    def calc_prep_mm(self):
        """Convert hourly data precipitation into monthly precipitation in mm"""

        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith("TIFF_") & file.endswith(".tif"):  # Check if TIF file
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    out_ras = source_path + "/BBAT_TRMM_" + file[5:]
                    days_month = calendar.monthrange(int(file[10:14]), int(file[14:16].strip("0")))  # Total month days
                    print("CALCULATING PRECIPITAION PER MONTH FOR ...... " + file)
                    arcpy.gp.Times_sa(file_path, days_month[1]*24, out_ras)  # TRMM  monthly precipitation
        print("CALCULATION SUCCESSFULLY COMPLETED!!!!!")

    def clip_ras(self):
        """Clip all rasters in the directory"""
        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith("BBAT_") & file.endswith(".tif"):  # Check if TIF file
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    out_ras = "D:/Data/Projects/Tanzania_Babati/Fred/TRMM/Clipped/" + file
                    print("CLIPPING ...... " + file)
                    arcpy.Clip_management(file_path, "34.8600815069245 -4.88786718585976 36.6732307933672 -3.07947682142878", out_ras, "D:/Data/Projects/Tanzania_Babati/LDM/Administrative/TRMM_Clipper.shp", "-9.999900e+003", "ClippingGeometry")
        print("ALL RASTERS CLIPPED SUCCESSFULLY!!!!!")

def main():
    """main program"""
    # Check out any necessary licenses
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    converter = NetCdfConverter("D:/Data/Projects/Tanzania_Babati/Fred")
    converter.convert_netcdf()
    converter.calc_prep_mm()
    converter.clip_ras()

if __name__ == "__main__":
    main()
