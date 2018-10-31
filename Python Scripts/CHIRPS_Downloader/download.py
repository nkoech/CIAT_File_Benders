__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"

from contextlib import closing
from datetime import datetime
import ftplib
import os
import re
import urlparse


def _is_item_dir(ftp_handle, item, param):
    """Checks if an item is directory or file"""
    if param['extension']:
        if len(item.rsplit('/', 1)[-1]) >= 4:
            if item[-3:] == param['extension'] or item[-4:] == param['extension']:
                return False
    original_cwd = ftp_handle.pwd()
    try:
        ftp_handle.cwd(item)  # Try to change to the new directory
        ftp_handle.cwd(original_cwd)  # Set cwd to the original working directory
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

def _set_path(ftp_path, param):
    """Create local paths"""
    ftp_items = ftp_path.split('/')
    region = param['region'] + '_'
    product = [region + i for i in param['product'] if region + i in ftp_items]
    idx = ftp_items.index(product[0])
    dir_items = ftp_items[idx:-1]
    return os.path.join(param['dest'], '/'.join(dir_items)).replace('\\', '/') 

def _download_ftp_file(ftp_handle, ftp_path, param):
    """Download a single file from FTP server """ 
    dest = _set_path(ftp_path, param)   
    print(dest)           
    # if not os.path.exists(dest):
    #     try:
    #         with open(dest, 'wb') as f:
    #             ftp_handle.retrbinary("RETR {0}".format(ftp_path), f.write)
    #         print("downloaded: {0}".format(dest))
    #     except FileNotFoundError:
    #         print("FAILED: {0}".format(dest))
    # else:
    #     print("already exists: {0}".format(dest))


def _format_date(raw_date):
    """Format date into year, month and day"""
    date = []
    for c, v in enumerate(raw_date):
        if c > 0 and len(v) >= 3:
            for i in range(0, len(v), 2):
                date.append(v[i:i + 2])
        else:
            date.append(v)
    ln = len(date)
    if ln == 3:
        return {'y': int(date[0]), 'm': int(date[1]), 'd': int(date[2])}
    elif ln == 2:
        return {'y': int(date[0]), 'm': int(date[1])}
    else:
        return {'y': int(date[0])}


def _get_date(ftp_path, years):
    """Get file date as digits"""
    f_name = ftp_path.rsplit('/', 1)[-1]
    f_name = f_name.split('.')
    for c, v in enumerate(f_name):
        if _is_int(v):
            if int(v) in years:
                raw_date = [i for i in f_name[c:] if _is_int(i)]
                return _format_date(raw_date)

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
            years = [datetime.today().year - i for i in xrange(49)]
            date = _get_date(item, years)
            year, month, day = param['year'], param['month'], param['date']
            if date:
                if len(date) == 3 and date['y'] in year and date['m'] in month and date['d'] in day:
                    _download_ftp_file(ftp_handle, item, param)
                elif len(date) == 2 and date['y'] in year and date['m'] in month:
                    _download_ftp_file(ftp_handle, item, param)
                elif len(date) == 1 and date['y'] in year:
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
        region_url = urlparse.urljoin(base_url, param['region'].strip('/'))
        if param['product']:
            for i in param['product']:
                if i == 'daily':
                    product_url = urlparse.urljoin(region_url + '_' + i + '/', 'tifs/p05/')
                    _download_ftp_tree(product_url, param)
                else:
                    product_url = urlparse.urljoin(region_url + '_' + i + '/', 'tifs/') 
                    _download_ftp_tree(product_url, param)
        else:
            product_url = urlparse.urljoin(region_url + '_daily/', 'tifs/p05/')  # Daily product used as default
            param['product'] = 'daily'
            _download_ftp_tree(product_url, param)
            
    else:
        print('Region is not set. Please include it in .json file.')
