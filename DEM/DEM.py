""" 
This file contains functions to download DEM tiles from a
variety of providers
"""

import os
import re
import tarfile
import zipfile

import requests

import numpy as np
import urllib.request

from os import path, remove, listdir, makedirs
from DEM.CDEM import CDEM


def get_tile_path_CDED(tileName):
    """ Get FTP path for a CDEM tile
    
    *Parameters*
    
    tileCode : str
        Code of DEM tile desired
    
    *Returns*
    
    str
        FTP location for tile
    
    Example
    -------
    get_tile_path_CDED("079D01")
    get_tile_path_CDED("079D")
    """
    
    # base path for all files
    basepath =  "https://ftp.maps.canada.ca/pub/nrcan_rncan/elevation/cdem_mnec"
    
    # build ftp path
    tile = tileName[0:3]
    ftp_path = "{}/{}/cdem_dem_{}_tif".format(basepath, tile, tileName)
    ftp_path = ftp_path + ".zip"
    
    return(ftp_path)

def SRTM_tile_name(lon, lat):
    """ Build name of SRTM DEM file
    
    *Parameters*
    
    lon : int
        Longitude (whole number) for corner of DEM tile. Negative numbers correspond to W
    lat : int
        Lattiude (whole number) for corner of DEM tile. Negative numbers correspond to 

    *Returns*
    
    str
        File name of DEM tile for SRTM
        
    *Example*
    
    SRTM_tile_name(-110, 49)
    
    """
    
    EW = "W" if lon < 0 else "E"
    NS = "S" if lat < 0 else "N"
    lon = "{:03d}".format(np.abs(lon))
    lat = "{:02d}".format(np.abs(lat))
    name = "{}{}{}{}.SRTMGL1.hgt.zip".format(NS, lat, EW, lon)
 
    return(name)
    
def get_tile_path_SRTM(lon=None, lat=None, name=None):
    """
    get_tile_path_SRTM(-110, 49)
    """
    baseurl = "https://e4ftl01.cr.usgs.gov/DP133/SRTM/SRTMGL1.003/2000.02.11/"
    if name:
        url = baseurl + name
    else:
        name = SRTM_tile_name(lon, lat)
        url = baseurl + name
    return url

    
def download_single_DEM(DEM_id, DEM_dir, replace=False, product="CDEM", auth=None):
    """ Download a DEM tile 
    
    *Parameters*
    
    DEM_id : str
        Name of tile to download.
    DEM_dir : str 
        Path to which files are downloaded
    replace : boolean
        Whether or not existing files should be re-downloaded and overwritten
    product : str
        Which DEM tile series should be downloaded: ('SRTM', 'CDEM')
        
    *Returns*
    
    list
        List of file paths to DEM files. There may be more than one 
        file per single zipped tile.
        
    """
    output = True

    if product.upper() == "CDEM":
        ftp_path = get_tile_path_CDED(DEM_id)
    elif product.upper() == "SRTM":
        ftp_path = get_tile_path_SRTM(name = DEM_id)
    else:
        raise NotImplementedError("DEM product not implemented")
    
    # create appropriate file name / directory structure based on ftp path
    file_paths = ftp_path.split('/')[-3:]
    
    save_dir = path.join(DEM_dir, *file_paths[0:2])
    if not path.isdir(save_dir):
        makedirs(save_dir)
    
    destfile = path.join(DEM_dir, *file_paths)
    
    if destfile.endswith("tar.gz"):
        dest_dir = re.sub("\\.tar\\.gz", "", destfile)
    else:
        dest_dir = os.path.splitext(destfile)[0]

    # Check to see if file already exists
    if not replace and path.isdir(dest_dir):
        print("{} exists locally and was not downloaded\n".format(dest_dir))
    else:
        if product.upper() == "SRTM":
            output = download_and_unzip(ftp_path, destfile, product="SRTM", authToken=auth, exdir = dest_dir)
        else:
            output = download_and_unzip(ftp_path, destfile, exdir = dest_dir)
        
    # If an appropriate file was downloaded, return the corresponding file paths
    if output:
        pattern_dict = {"CDEM" : "dem[ew_].*[td][ie][fm]$",
                        "SRTM" : "hgt$"}
    
        pattern = pattern_dict[product]

        dem = [f for f in listdir(dest_dir) if re.search(pattern, f)]
        dem = [path.join(dest_dir, x) for x in dem]
        
        return(dem)
    
def download_and_unzip(url, destfile, exdir, product="CDEM", authToken=None, rmzip=True):
    """ 
    Downloads and unzips a file

    *Parameters*
    
    url : str
        Url path
    destfile :  str
        Filepath of output zipfile
    exdir : str 
        The directory to which files are extracted
    rmzip : boolean
        Whether or not to remove zipfile after extraction. 
        
    *Returns*
    
    str
        path(s) to target tiles
    """
    if product == "CDEM":
        try:
            print("Downloading file from {}".format(url))
            urllib.request.urlretrieve(url, destfile)

        # if the url doesn't exist
        except Exception as e:
            print(url)
            print(e)
            return(False)
    elif product == "SRTM":
        if authToken is None:
            raise PermissionError("Invalid token, NONE")

        try:
            print("Downloading file from {}".format(url))
            response = requests.get(url, headers={
                'Authorization': 'Bearer {}'.format(authToken)})

            response.raise_for_status()
            open(destfile, 'wb').write(response.content)

        except Exception as e:
            print(e)
            return (False)

    else:
        raise NotImplementedError
    
    if destfile.endswith("tar.gz"):
        with tarfile.open(destfile, "r:gz") as tarf:
            tarf.extractall(exdir)
        
    elif destfile.endswith("zip"):
        with zipfile.ZipFile(destfile, "r") as zipf:
            zipf.extractall(exdir)
            
    else:
        rmzip = False
        
    if rmzip:
        remove(destfile)
    
    return(True)
        

def download_multiple_DEM(DEM, DEM_dir, product="CDEM", auth=None):
    """ Download a list of DEM URLs. If they exist already, they are not downloaded
    
    *Parameters*
   
    DEM : list
        Bounding box (SRTM) or list of tiles (CDEM)
    DEM_dir : str 
        Path to which files are downloaded
    product : str
        Which DEM tile series should be downloaded: ('SRTM', 'CDEM')
        
    *Returns*
   
    list
        a list of file paths for target DEMs
    """
    # sanity check: make sure NTS names are well-formed
    if product.upper() in ["CDEM"]:
        if not all([re.search("^\\d{3}\\w(\\d{2})?$", x) for x in DEM]):
            raise Exception("Bad format for one or more NTS strings")

        # download each DEM file using the map function
        get_single = lambda x: download_single_DEM(x, DEM_dir=DEM_dir, product=product)
        files = map(get_single, DEM)

        # return list of files
        files = [f for f in files if f is not None]
        files = [dem for sublist in files for dem in sublist]
        return (files)

    elif product.upper() in "SRTM":
        for i in range (DEM['ymax'] - DEM['ymin'] + 1):
            for j in range(DEM['xmax'] - DEM['xmin'] + 1):
                name = SRTM_tile_name(DEM['xmin'] + j, DEM['ymin']+i)
                try:
                    download_single_DEM(name, DEM_dir = DEM_dir, product=product, auth=auth)
                except:
                    continue

        return

    else:
        raise NotImplementedError

def CDEM_tiles_from_extent(ext):
    ''' Determine which CDEM tiles are required to cover a target spatial extent

    *Parameters*

    ext : dict
        Dictionary with the following keys: {xmin, xmax, ymin, ymax} corresponding
        to the spatial extent in WGS84 decimal degrees
    scale : int


    *Examples*

        ext = {'ymin': 52, 'ymax': 53, 'xmin' : -114, 'xmax' : -112}
        CDEM_tiles_from_extent(ext)
    '''
    # unpack extent dictionary
    w = ext['xmin']
    e = ext['xmax']
    s = ext['ymin']
    n = ext['ymax']

    # find CDEM tiles
    bbox = CDEM.makebbox(n=n, e=e, s=s, w=w)
    tiles = CDEM.bybbox(bbox)

    # convert to list of strings
    tile_list = [''.join(tile) for tile in tiles]

    return(tile_list)

