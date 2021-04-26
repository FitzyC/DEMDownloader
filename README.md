# DEMDownloader

This set of scripts can be used to download either Shuttle Radar Topography Mission (SRTM) or Canadian Digital Elevation Data (CDED) digitial elevation model (DEM) tiles for large study areas. To run, first edit the USER INPUT section within download_DEM.py, and then running the script. 

The user inputs are:
--------------------

DEM_dir : Full path to the folder DEM tiles should be saved to

DEM_type : One of CDED or SRTM

area : Dictionary specifying the bottom-left coords of the extreme tiles (bottom-right, top-left) within the AOI. Since Canada has 'west' longitudes, xmin and xmax should have negatives, with xmin being the largest negative numerically, xmax the smallest negative numerically.

How to determine what area values you need: 
-------------------------------------------

For 'ymin' and 'ymax' determine the extreme latitudes of the study area, and round both values down to their nearest whole number. For 'xmin' and 'xmax', determine the extreme longitudes of the study area and round both values up to their nearest whole number.
For example, to download DEM tiles for the province of New Brunswick: area = {'ymin': 44, 'ymax': 48, 'xmin': -70, 'xmax': -64}

NOTE: If downloading SRTM tiles, an account is needed here: https://urs.earthdata.nasa.gov/
Once credentials are granted, add them as strings to the inputs of the downloadSRTM function in DEM.py (~line 132).
