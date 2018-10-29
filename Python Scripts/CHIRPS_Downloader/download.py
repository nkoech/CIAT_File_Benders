__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"


from contextlib import closing
import ftplib
import os
import urlparse


def _is_item_dir(ftp_handle, item, param):
    """Checks if an item is directory or file"""
    if param['extension']:
        if len(item.rsplit('/', 1)[-1]) >= 4:
            if item[-3:] == param['extension'] or item[-4:] == param['extension']:
                return False
    original_cwd = ftp_handle.pwd()
    try:
        ftp_handle.cwd(item)
        ftp_handle.cwd(original_cwd)
        return True
    except:
        return False

def _is_int (str):
    """Check if string is an integer"""
    try:
        int(str)
        return True
    except ValueError:
        return False

def _get_item(item, ftp_path):
    """Get item in ftp link"""
    ftp_parts = ftp_path.split('/')
    for i in item:
        if str(i) in ftp_parts:
            return i  

def _download_ftp_file(ftp_handle, ftp_path, param):
    """Download a single file from FTP server """ 
    items = ftp_path.split('/')
    i = items.index(param['region'] + '_' + param['product'])
    dest = os.path.join(param['dest'], ','.join(items[i:-1]))
    print(dest)
    # product = _get_item([param['region'] + '_' + param['product']], ftp_path)
    # if param['year']:
    #     year = _get_item(param['year'], ftp_path)
    #     dest = os.path.join(param['dest'], product, year)
    # else:
    #     dest = os.path.join(param['dest'], product)
    
                
    # if not os.path.exists(dest):
    #     try:
    #         with open(dest, 'wb') as f:
    #             ftp_handle.retrbinary("RETR {0}".format(ftp_path), f.write)
    #         print("downloaded: {0}".format(dest))
    #     except FileNotFoundError:
    #         print("FAILED: {0}".format(dest))
    # else:
    #     print("already exists: {0}".format(dest))

def _mirror_ftp_dir(ftp_handle, ftp_path, param):
    """Replicates a directory on an ftp server recursively"""
    for item in ftp_handle.nlst(ftp_path):
        if _is_item_dir(ftp_handle, item, param):
            if param['year']:
                product_year = item.rsplit('/', 1)[-1]
                if _is_int(product_year) and int(product_year) in param['year']:
                    _mirror_ftp_dir(ftp_handle, item, param)                    
            else:
                _mirror_ftp_dir(ftp_handle, item, param)
        else:
            _download_ftp_file(ftp_handle, item, param)

def _download_ftp_tree(ftp_url, param):
    """List and download files"""
    with closing(ftplib.FTP(urlparse.urlsplit(ftp_url).netloc)) as ftp:
        try:
            ftp.login()
            ftp_path = urlparse.urlsplit(ftp_url).path.lstrip('/')
            _mirror_ftp_dir(ftp, ftp_path, param)
        except ftplib.all_errors as e:
            print('FTP error:', e)

def ftp_download(param):
    """Download data from FTP URL"""
    base_url = param['base_url'].strip('/') + '/'
    if param['region']:
        region_url = urlparse.urljoin(base_url, param['region'].strip('/').lower())
        if param['product']:
            for i in param['product']:
                if i == 'daily':
                    product_url = urlparse.urljoin(region_url + '_' + i.lower() + '/', 'tifs/p05/')
                    _download_ftp_tree(product_url, param)
                else:
                    product_url = urlparse.urljoin(region_url + '_' + i.lower() + '/', 'tifs/') 
                    _download_ftp_tree(product_url, param)
        else:
            product_url = urlparse.urljoin(region_url + '_daily/', 'tifs/p05/')  # Daily product used as default
            param['product'] = 'daily'
            _download_ftp_tree(product_url, param)
            
    else:
        print('Region is not set. Please include it in .json file.')
