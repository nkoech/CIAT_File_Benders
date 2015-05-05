__author__ = 'nkoech'

import os, calendar
import arcpy
import dbf
import csv
from arcpy import env
from arcpy.sa import *


class CsvExtractor(object):
    """Extract values form raster layers and convert to CSV"""

    def __init__(self, s_dir):
        self.s_dir = s_dir

    def get_dir_paths(self):
        """Get file directory path"""
        tiff_dirs = []
        for root_path, dir_names, files in os.walk(self.s_dir):  # walk through root directory
            for dir_name in dir_names:
                if dir_name == "Clipped":
                    dir_join = os.path.join(root_path, dir_name).replace("\\","/")  # Join rooth to sub-directory
                    tiff_dirs.append(dir_join)
        return tiff_dirs

    def get_ras_val(self):
        """Extract raster values and save as dbf table"""

        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith("BBAT_") & file.endswith(".tif"):  # Check if TIF file
                    file_path = os.path.join(source_path, file).replace("\\","/")
                    out_ras = source_path + "/DBF_" + file[15:23] + ".dbf"
                    print("EXTRACTING VALUES FOR ...... " + file)
                    arcpy.gp.Sample_sa(file_path, file_path, out_ras, "NEAREST")  # create dbf table
        print("VALUE EXTRACTION COMPLETED SUCCESSFULLY!!!!!")

    def get_file_year(self):
        """Get the year in the file name"""

        file_year = []
        for source_path in self.get_dir_paths():
            for file in os.listdir(source_path):
                if file.startswith("DBF_") & file.endswith(".dbf"):  # Check if TIF file
                    if file[4:8] not in file_year:
                        file_year.append(file[4:8])
        return file_year

    def create_csv(self):
        """Get alL DBF file records and create CSV files from them"""

        for source_path in self.get_dir_paths():
            for f_year in self.get_file_year():
                out_csv = source_path + "/BBAT_TRMM_" + f_year + ".csv"  # Output CSV file
                with open(out_csv, "wb") as output_csv:  # Open CSV file for write
                    csv_data = []
                    for file in os.listdir(source_path):
                        if file.startswith("DBF_") & file.endswith(".dbf"):  # Check if DBF file
                            if file[4:8] == f_year: # Check if file is correct year
                                csv_data.append(" ")
                                csv_data.append(file[4:8] + "_" + calendar.month_name[int(file[8:10].strip("0"))])  # Month and year as text
                                #csv_data.append(" ")
                                csv_data.append("ID,Monthly_mm")  # Append ID and precipitation
                                file_path = os.path.join(source_path, file).replace("\\","/")
                                print("READING RECORDS FROM ...... " + file)
                                with dbf.Table(file_path) as table:  # Open DBF file
                                    count = 0
                                    for record in table:  # Get DBF records
                                        count += 1
                                        csv_values = str(count) + "," + str(record.bbat_trmm1)  # Concatenate records and count
                                        csv_data.append(csv_values)  # Append DBF values of the year

                    writer = csv.writer(output_csv, delimiter=',')  # Create a CSV write object with comma delimiter
                    print("CREATING CSV FILE FOR ...... " + f_year)
                    for values in csv_data:  # Iterate data array
                        writer.writerow(values.split(","))  # Write each array row to CSV file
        print("CSV FILES SUCCESSFULLY CREATED!!!!!")

def main():
    """Main program"""
    # Check out any necessary licenses
    env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    csv_constructor = CsvExtractor("C:/CCAFS_DATA")
    csv_constructor.get_ras_val()
    csv_constructor.get_file_year()
    csv_constructor.create_csv()

if __name__ == "__main__":
    main()