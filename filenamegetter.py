__author__ = 'nkoech'

import os
import csv


class FileNameGetter(object):
    """ Get file names and save it in a txt file """

    def __init__(self, s_dir):
        self.s_dir = s_dir

    def get_file_name(self):
        """ Get file name from root directory"""
        file_list = []
        for root_path, dir_name, files in os.walk(self.s_dir):
            for f in files:
                file_list.append(f)
        return file_list

    def list_files(self):
        for f in self.get_file_name():
            print(f)

    def write_file(self):
        """ Write file names to a text file """
        with open(self.s_dir + "/file_names.csv", 'wb') as out_file:
            csv_writer = csv.writer(out_file, delimiter=',')
            for f in self.get_file_name():
                csv_writer.writerow([f])
    print("ALL FILES WRITTEN SUCCESSFULLY!!!")

def main():
    """ Main program """
    file_getter = FileNameGetter("C:/CCAFS_DATA/LULC_30m")
    file_getter.write_file()

if __name__  == "__main__":
    main()
