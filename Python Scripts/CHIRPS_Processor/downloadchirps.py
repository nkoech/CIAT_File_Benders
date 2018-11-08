__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


from ftpdownload import ftp_download
from readjson import get_json_data

class DownloadCHIRPS:
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


    def _get_user_parameters(self):
        """Get contents from a Json file"""
        tool_settings = {}
        data = get_json_data('dir_meta', '.json')
        for i in data:
            for j in data[i]:
                if isinstance(j, dict):
                    tool_settings.update(j)
        return tool_settings

    def init_download(self):
        """Initialize file download"""
        self.region = self._lower_case(self.region)
        self.product = self._lower_case(self.product)
        ftp_params = {'base_url': self.base_url, 'region': self.region, 'product': self.product, 'year': self.year,
                      'month': self.month, 'date': self.date, 'extension': self.extension, 'dest': self.download_dir}
        ftp_download(ftp_params)
    
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


def main():
    """Main program"""
    download = DownloadCHIRPS()
    download.init_download()

if __name__ == '__main__':
    main()
