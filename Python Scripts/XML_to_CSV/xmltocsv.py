__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2016"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"

from sourcedirectory import get_directory
from filelocation import get_file_location
from readjson import get_json_data
from readxml import get_xml_items
import csv


class XMLtoCSV:
    def __init__(self):
        self.user_settings = self._get_user_settings()
        self.base_dir = self.user_settings['src_dir']
        self.base_dir_startswith = self.user_settings['dir_startswith']
        self.file_startswith = self.user_settings['file_startswith']
        self.file_endswith = self.user_settings['file_endswith']
        self.char_start = self.user_settings['char_start']
        self.char_end = self.user_settings['char_end']

    def _get_user_settings(self):
        """
        Get contents from a JSON file
        :return: User inputs from a JSON file
        :rtype: Dictionary object
        """
        user_settings = {}
        data = get_json_data('dir_meta', '.json')
        for i in data:
            for j in data[i]:
                if isinstance(j, dict):
                    user_settings.update(j)
        return user_settings

    def convert_xml_to_csv(self):
        """
        Convert XML file into CSV file
        :return: None
        :rtype: None
        """
        id_range = self._get_identity_range()
        for root_dir in get_directory(self.base_dir, self.base_dir_startswith):
            print('Identified root directory ..... {0}'.format(root_dir))
            for src_dir, file_path, file_name in get_file_location(root_dir, self.file_startswith, self.file_endswith):
                print('Processing XML file ..... {0}'.format(file_name))
                xml_items = get_xml_items(file_path, id_range)
                csv_values = self._get_csv_values(id_range, xml_items)
                csv_out_file = src_dir + '/' + file_name[:-3] + 'csv'
                with open(csv_out_file, 'w') as csv_file:
                    print('Converting to CSV file ..... {0}'.format(csv_out_file))
                    for k, v in csv_values.items():
                        values, headers, blank_values = v
                        writer = csv.DictWriter(csv_file, headers, dialect='excel', lineterminator='\n')
                        writer.writeheader()
                        writer.writerow(values)
                        writer.writerow(blank_values)

    def _get_identity_range(self):
        """
        Get user input range
        :return: Alphabetical range values
        :rtype: List object
        """
        return [chr(i) for i in range(ord(self.char_start), ord(self.char_end) + 1)]

    def _get_csv_values(self, id_range, xml_items):
        """
        Get values to be used in CSV file creation
        :param id_range: Unique tag identifiers
        :param xml_items: List object with xml items
        :return: Dictionary with CSV values
        :rtype: Dictionary object
        """
        csv_values = {}
        for tag_id in id_range:
            tag_values = {}
            blank_values = {}
            column_headers = []
            for count, xml_item in enumerate(xml_items):
                if xml_item[0][1] == tag_id:
                    tag_key = xml_item[1][0]
                    tag_value = xml_item[1][1]
                    if tag_key not in set(column_headers):
                        tag_values[tag_key] = tag_value
                        blank_values[tag_key] = ''
                        column_headers.append(tag_key)
            csv_values[tag_id] = (tag_values, column_headers, blank_values)
        return csv_values

def main():
    """Main program"""
    xml_to_csv = XMLtoCSV()
    xml_to_csv.convert_xml_to_csv()

if __name__ == '__main__':
    main()

