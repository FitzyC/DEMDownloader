"""
Downloads DEM tiles

Python Libraries needed: Numpy, requests
"""

from DEM.DEM import CDEM_tiles_from_extent, download_multiple_DEM

if __name__ == "__main__":
    ###USER INPUT###
    DEM_dir = ""  #Full path to folder where downloaded DEMs will be placed
    demType = 'CDEM'  #One of CDEM or SRTM
    auth=None
    # Latitude and Longitude mins/maxs of bounding box to download DEMs within, example for NewBrunswick included
    area = {'ymin': 44, 'ymax': 48, 'xmin': -70, 'xmax': -64}
    ###          ###

    if demType == 'SRTM':
        download_multiple_DEM(area, DEM_dir, 'SRTM', auth=auth)
    elif demType == 'CDEM':
        tiles = CDEM_tiles_from_extent(area)
        download_multiple_DEM(tiles, DEM_dir, 'CDEM')
