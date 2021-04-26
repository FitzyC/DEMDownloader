"""
Downloads DEM tiles for orthorectification. Tiles are downloaded at 1:250k scale to save on space.

Python Libraries needed: Numpy, requests
"""

from DEM.DEM import NTS_tiles_from_extent, download_multiple_DEM

if __name__ == "__main__":
    ###USER INPUT###
    DEM_dir = ""  #Full path to folder where downloaded DEMs will be placed
    demType = 'SRTM'  #One of CDED or SRTM
    # Latitude and Longitude mins/maxs of bounding box to download DEMs within, example for NewBrunswick included
    area = {'ymin': 44, 'ymax': 48, 'xmin': -70, 'xmax': -64}
    ###          ###

    if demType == 'SRTM':
        download_multiple_DEM(area, DEM_dir, 'SRTM')
    elif demType == 'CDED':
        tiles = NTS_tiles_from_extent(area, scale=1)
        download_multiple_DEM(tiles, DEM_dir, 'CDED')
