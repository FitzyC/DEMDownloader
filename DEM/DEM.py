""" 
This file contains functions to download and mosaic DEM tiles from a 
variety of providers
"""

import itertools
import os
import re
import tarfile
import zipfile

import requests
import netrc

import numpy as np
import urllib.request

from os import path, remove, listdir, makedirs
from DEM.NTS import nts


def get_tile_path_CDED(NTS):
    """ Get FTP path for a CDED NTS tile 
    
    *Parameters*
    
    NTS : str
        Name of NTS sheet for which a DEM is desired
    
    *Returns*
    
    str
        FTP location for CDED DEM tile
    
    Example
    -------
    get_tile_path_CDED("079D01")
    get_tile_path_CDED("079D")
    """
    
    NTS = NTS.lower()
    
    # test resolution from NTS specification
    if len(NTS) == 6:
        resolution = "50k_dem" 
    elif len(NTS) == 4:
        resolution = "250k_dem" 
    else:
        raise Exception("Invalid NTS sheet!")
    
    # base path for all files
    basepath =  "http://ftp.geogratis.gc.ca/pub/nrcan_rncan/archive/elevation/geobase_cded_dnec"
    
    # build ftp path
    tile = NTS[0:3]
    ftp_path = "{}/{}/{}/{}".format(basepath, resolution, tile, NTS)
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
    baseurl = "http://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/"
    if name:
        url = baseurl + name
    else:
        name = SRTM_tile_name(lon, lat)
        url = baseurl + name
    return url


class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

   # Overrides from the library to keep headers when redirected to or from
   # the NASA auth host.

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)

            if (original_parsed.hostname != redirect_parsed.hostname) and \
                redirect_parsed.hostname != self.AUTH_HOST and \
                original_parsed.hostname != self.AUTH_HOST:

                del headers['Authorization']
        return
        
            
def downloadSRTM(url, destfile, username=None, password=None, retry=5):
    """
    Downloads an SRTM tile.  
    
    *Parameters*
    
    url : str
        path to SRTM tile
    username : str (optional)
        USGS Earthdata username. If missing, looks for the existence of a .netrc
        file in your home directory 
    password : str (optional)
        USGS Earthdata username. If missing, looks for the existence of a .netrc
        file in your home directory 
    retry : int
        how many times to retry downloading
    If username / password are not provided, the function requires a netrc
     file in your home directory (named either '_netrc' or '.netrc')
    with the following contents:
    machine <hostname>
    login <login>
    password <password>
    """
    print(url)
    if not (username and password):
        try:
            auth = netrc.netrc()
        except OSError:
            auth = netrc.netrc('_netrc')
        username, account, password = auth.authenticators("urs.earthdata.nasa.gov")

    session = SessionWithHeaderRedirection(username, password)
    filename = url[url.rfind('/')+1:] 

    while retry:
        try:
            # submit the request using the session
            response = session.get(url, stream=True)
            print(response.status_code)
            # raise an exception in case of http errors
            response.raise_for_status()  
        
            # save the file
            with open(destfile, 'wb') as fd:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    fd.write(chunk)
            break
            
        except requests.exceptions.HTTPError as e:
            retry -= 1
            print(e)
        
        except requests.exceptions.ConnectionError as e:
            retry -= 1
            print(e)
            
def download_and_unzip_SRTM(url, destfile, exdir, rmzip=True):
    downloadSRTM(url, destfile)
    with zipfile.ZipFile(destfile, "r") as zipf:
        zipf.extractall(exdir)
    if rmzip:
        os.remove(destfile)
    return(True)
    
def get_tile_path_CDEM():
    raise NotImplementedError()
    
def download_single_DEM(DEM_id, DEM_dir, replace=False, product="CDED"):
    """ Download a DEM tile 
    
    *Parameters*
    
    DEM_id : str
        Name or NTS sheet of tile to download. If product is "NED" or "SRTM", a name should
        be specified, but if product is "CDED", then a NTS sheet should be.
    DEM_dir : str 
        Path to which files are downloaded
    replace : boolean
        Whether or not existing files should be re-downloaded and overwritten
    product : str
        Which DEM tile series should be downloaded: ('NED', 'CDED')
        
    *Returns*
    
    list
        List of file paths to DEM files. There may be more than one 
        file per single zipped tile.
        
    """
    output = True

    if product.upper() == "CDED":
        ftp_path = get_tile_path_CDED(NTS = DEM_id)
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
            output = download_and_unzip_SRTM(url = ftp_path, destfile = destfile, exdir = dest_dir)
        else:
            output = download_and_unzip(url = ftp_path, destfile = destfile, exdir = dest_dir)
        
    # If an appropriate file was downloaded, return the corresponding file paths
    if output:
        pattern_dict = {"CDED" : "dem[ew_].*[td][ie][fm]$",
                        "CDEM" : "dem[ew_].*[td][ie][fm]$",
                        "SRTM" : "hgt$"}
    
        pattern = pattern_dict[product]

        dem = [f for f in listdir(dest_dir) if re.search(pattern, f)]
        dem = [path.join(dest_dir, x) for x in dem]
        
        return(dem)
    
def download_and_unzip(url, destfile, exdir, rmzip=True):
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
    
    try:
        print("Downloading file from {}".format(url))
        urllib.request.urlretrieve(url, destfile)
   
    # if the url doesn't exist    
    except Exception as e:
        print(url)
        print(e)
        return(False)
    
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
        

def download_multiple_DEM(DEM, DEM_dir, product="CDED"):
    """ Download a list of DEM URLs. If they exist already, they are not downloaded
    
    *Parameters*
   
    DEM : list
        List of DEM urls (NED) or NTS tiles (CDED)
    DEM_dir : str 
        Path to which files are downloaded
    product : str
        Which DEM tile series should be downloaded: ('NED', 'CDED')
        
    *Returns*
   
    list
        a list of file paths for target DEMs
    """
    # sanity check: make sure NTS names are well-formed
    if product.upper() in ["CDED", "CDEM", "CDSM"]:
        if not all([re.search("^\\d{3}\\w(\\d{2})?$", x) for x in DEM]):
            raise Exception("Bad format for one or more NTS strings")

    elif product.upper() in "SRTM":
        for i in range (DEM['ymax'] - DEM['ymin'] + 1):
            for j in range(DEM['xmax'] - DEM['xmin'] + 1):
                name = SRTM_tile_name(DEM['xmin'] + j, DEM['ymin']+i)
                try:
                    download_single_DEM(name, DEM_dir = DEM_dir, product=product)
                except:
                    continue

        return


    # download each DEM file using the map function
    get_single = lambda x: download_single_DEM(x, DEM_dir = DEM_dir, product=product)        
    files = map(get_single, DEM)
    
    # return list of files
    files = [f for f in files if f is not None]
    files = [dem for sublist in files for dem in sublist]
    return(files)
        

def SRTM_tiles_from_extent(ext):
    return degree_tiles_from_extent(ext, SRTM_tile_name, yoff=-1)

def degree_tiles_from_extent(ext, tile_function, xoff=0, yoff=0):
    """ Get a list of raster tiles required to cover a spatial extent

    *Parameters*

    ext : dict
        Dictionary with the following keys: {xmin, xmax, ymin, ymax} corresponding
        to the spatial extent in WGS84 decimal degrees
    tile_function : function
        function that takes lon, lat as keyword arguments and returns tile name

    *Returns*

    list
        List of tile names required to cover specified spatial extent

    *Examples*

    E = {'xmin': -110 ,'xmax': -108,'ymin': 48 ,'ymax': 51 }
    NED_tiles_from_extent(E)
    """

    # unpack extent dictionary
    xmin = ext['xmin']
    xmax = ext['xmax']
    ymin = ext['ymin']
    ymax = ext['ymax']

    # get all corner coordinates to cover extent
            # +1 beacuse of 0 indexing
    xrange = range(int(np.floor(xmin)), int(np.floor(xmax)) + 1)
    yrange = range(int(np.ceil(ymin)), int(np.ceil(ymax)) + 1)

    xrange = [x + xoff for x in xrange]
    yrange = [y + yoff for y in yrange]

    pts = itertools.product(xrange, yrange)

    # get tile index for all
    f = lambda x: tile_function(lon = x[0], lat = x[1])
    tiles =  [pth for pth in map(f, pts)]

    return(tiles)

def NTS_tiles_from_extent(ext, scale=1):
    ''' Determine which NTS tiles are required to cover a target spatial extent

    *Parameters*

    ext : dict
        Dictionary with the following keys: {xmin, xmax, ymin, ymax} corresponding
        to the spatial extent in WGS84 decimal degrees
    scale : int


    *Examples*

        ext = {'ymin': 52, 'ymax': 53, 'xmin' : -114, 'xmax' : -112}
        NTS_tiles_from_extent(ext)
    '''
    # unpack extent dictionary
    w = ext['xmin']
    e = ext['xmax']
    s = ext['ymin']
    n = ext['ymax']

    # find NTS tiles
    bbox = nts.makebbox(n=n, e=e, s=s, w=w)
    tiles = nts.bybbox(bbox, scale)

    # convert to list of strings
    tile_list = [''.join(tile) for tile in tiles]

    return(tile_list)

