__author__ = 'nkoech'

import os
import arcpy
from arcpy import env


class TrmmAverager(object):
    """Get all TRMM tif files in a folder and find the mean"""

    def __init__(self, source_dir):
        """Class contructor"""
        self.source_dir = source_dir

    def calc_mean(self):
        """Get TRMM tiff files and calculate mean using cell statistics gp"""
        ras_input = []
        for file in os.listdir(self.source_dir):  # interate source folder
                if file.startswith('BBAT_') & file.endswith('.tif'):  # check for tiff files
                    file_path = os.path.join(self.source_dir, file).replace("\\","/") # create path
                    ras_input.append(file_path)  # push file paths to array
        out_ras = self.source_dir + "/AVG_BBAT_TRMM.tif"  # output path
        print("CALCULATING MEAN FOR TIFF FILES IN......... " + self.source_dir[-11:])
        arcpy.gp.CellStatistics_sa(ras_input, out_ras, "MEAN", "DATA")  # derive mean raster
        print("PROCESSING COMPLETED SUCCESSFULLY!!!")


def main():
    """Main program"""
    # Check out any necessary licenses
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")

    # Initialize the object passing in the TRMM source folder
    averager = TrmmAverager("D:/Dropbox/Interviews/Interview_GIS_Analyst/Data/Babati_TRMM")
    averager.calc_mean()

if __name__ == "__main__":
    main()


