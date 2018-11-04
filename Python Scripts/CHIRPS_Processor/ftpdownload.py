__author__ = "Koech Nicholas"
__copyright__ = "Copyright 2018"
__email__ = "koechnicholas@gmail.com"
__status__ = "draft"

from contextlib import closing
from datetime import datetime
import ftplib
import os
import re
import sys
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
    dest_dir = os.path.join(param['dest'], '/'.join(ftp_items[idx:-1])).replace('\\', '/')
    dest_file = os.path.join(param['dest'], '/'.join(ftp_items[idx:])).replace('\\', '/')
    return dest_dir, dest_file

def _make_parent_dir(fpath):
    """Creates parent directory if it does not exist"""
    dir_name = fpath
    while not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name)
            print("Created: {0}".format(dir_name))
        except:
            _make_parent_dir(dir_name)

def _download_ftp_file(ftp_handle, ftp_path, param):
    """Download a single file from FTP server """ 
    dest_dir, dest_file = _set_path(ftp_path, param)  
    _make_parent_dir(dest_dir) 
    if not os.path.exists(dest_file):
        try:
            with open(dest_file, 'wb') as f:
                ftp_handle.retrbinary("RETR {0}".format(ftp_path), f.write)
            print("Downloaded: {0}".format(dest_file))
        except IOError:
            print("FAILED: {0}".format(dest_file))
    else:
        print("already exists: {0}".format(dest_file))

def _format_date(raw_date):
    """Format date into year, month and day"""
    date = []
    for c, v in enumerate(raw_date):
        if c > 0 and len(v) >= 3:
            for i in range(0, len(v), 2):
                date.append(int(v[i:i + 2]))
        else:
            date.append(int(v))
    ln = len(date)
    if ln == 3:
        return {'year': date[0], 'month': date[1], 'date': date[2]}
    elif ln == 2:
        return {'year': date[0], 'month': date[1]}
    else:
        return {'year': date[0]}

def _get_date(ftp_path, years):
    """Get file date as digits"""
    f_name = ftp_path.rsplit('/', 1)[-1]
    f_name = f_name.split('.')
    for c, v in enumerate(f_name):
        if _is_int(v):
            if int(v) in years:
                raw_date = [i for i in f_name[c:] if _is_int(i)]
                return _format_date(raw_date)

def _filter_ftp_file(ftp_handle, ftp_path, param):
    """ Get valid file and download """
    num_years = [datetime.today().year - i for i in xrange(49)]  # number of years to be compared with
    date = _get_date(ftp_path, num_years)  # get file date
    param_keys = [k for k, v in param.items() if v and k in ('year', 'month', 'date')]  # user dates with values            
    if param_keys and date:
        param_date_keys = [k for k in param_keys if k in date.keys()]
        matched_keys = [k for k, v in date.items() if k in param_keys and v in param[k]]  # Matched keys
        if len(param_keys) >= len(date) and len(date) == len(matched_keys):
            _download_ftp_file(ftp_handle, ftp_path, param)
        elif len(date) > len(param_keys) and len(param_date_keys) == len(matched_keys):
            _download_ftp_file(ftp_handle, ftp_path, param)

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
            _filter_ftp_file(ftp_handle, item, param)  # get valid file and download
            # num_years = [datetime.today().year - i for i in xrange(49)]  # number of years to be compared with
            # date = _get_date(item, num_years)  # get file date

def _download_ftp_tree(ftp_url, param):
    """List and download files"""
    with closing(ftplib.FTP(urlparse.urlsplit(ftp_url).netloc)) as ftp:
        try:
            ftp.login()
            ftp_path = urlparse.urlsplit(ftp_url).path.lstrip('/')
            _mirror_ftp_dir(ftp, ftp_path, param)
        except ftplib.all_errors as e:
            print('FTP error:', e)

def _generate_list(param):
    """Generate integer values from range of values"""
    keys = ['year', 'month', 'date']
    for k in keys:
        if k in param.keys() and param[k]:
            for lst in list(param[k]):  # Copy original list for removal on iteration                
                if not _is_int(lst):                   
                    boundary_vals = map(int, lst.split('-'))
                    param[k].remove(lst)
                    param[k].extend(list(range(min(boundary_vals), max(boundary_vals) + 1)))

def ftp_download(param):
    """ Set the right product URL and downlaod """
    base_url = param['base_url'].strip('/') + '/'
    _generate_list(param)
    if param['region']:
        region_url = urlparse.urljoin(base_url, param['region'].strip('/'))
        if param['product']:
            for i in param['product']:
                url = region_url + '_' + i + '/'
                if i == 'daily':
                    product_url = urlparse.urljoin(url, 'tifs/p05/')                    
                else:
                    product_url = urlparse.urljoin(url, 'tifs/')
                _download_ftp_tree(product_url, param)
        else:
            product_url = urlparse.urljoin(region_url + '_daily/', 'tifs/p05/')  # Daily product used as default
            param['product'] = 'daily'
            _download_ftp_tree(product_url, param)            
    else:
        print('Region is not set. Please include it in the .json file.')
