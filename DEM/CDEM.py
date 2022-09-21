# Determine NTS tile sheets from coordinates.  
# e.g. 
# ext = nts.getextent(62, -110, 60, -112)
# tiles = nts.bybbox(ext, 1)
#
# Ported from R using code from: github.com/paleolimbot/rcanvec (/R/ntstiles.R)

import numpy as np


class CDEM:
    MAP_SERIES_N_OF_80 = np.array(("910", "780", "560", "340", "120", 
                                    None, "781", "561", "341", "121")).reshape(2,5)
    
    
    MAP_250K = np.array(("D", "C", "B", "A", 
                        "E", "F", "G", "H", 
                        "L", "K", "J", "I",
                        "M", "N", "O", "P")).reshape(4,4)
    
    
    
    MAP_250K_N_OF_68 = np.array(("B", "A", "C", "D", "F", "E", "G", "H")).reshape(4,2)
                        
    def __init__(self):
        pass

    @staticmethod
    def makebbox(n, e, s, w):
        '''  
           min max
        x -66 -64
        y  45  46
        '''
        bbox = np.array((w, e, s, n)).reshape((2,2))   
        return(bbox)
    
    @staticmethod
    def widthandoffset250(lat): 
        if (lat >= 80.0):
            wo = np.array((8.0, 8.0))
        elif (lat >= 68.0):
            wo = np.array((4.0, 0.0))
        else:
            wo = np.array((2.0, 0.0))
        return(wo)
     
    def mapsperseries(self, tile250ky):
        if (tile250ky >= 28):
            return(2)
        else:
            return(4)

    def validtileseries(self, tile):
        if (tile[1] == 0):
            if (7 <= tile[0] <= 11):
                return(True)
        
        elif (tile[1] == 1):
            if (6 <= tile[0] <= 11) or (tile[0] == 1) or (tile[0] == 2): 
                return(True)
            
        elif (2 <= tile[1] <= 4): 
            if (0 <= tile[0] <= 11): 
                return(True)
            
        elif (5 <= tile[1] <= 8):
            if(0 <= tile[0] <= 10): 
                return(True)
            
        elif (tile[1] == 9):
            if(0 <= tile[0] <= 9):
                return(True)
            
        elif (tile[1] == 10):
            if(0 <= tile[0] <= 4):
                return(True)
            
        elif(tile[1] == 11): 
            if(1 <= tile[0] <= 4): 
                return(True)
            
        return(False)
    
    
    def idseries(self, tile):
        if (not self.validtileseries(tile)):
            return(None)
        
        if (tile[1] >= 10):
            id = self.MAP_SERIES_N_OF_80[tile[1] - 10, tile[0]]
            return(id)
        else:
            seriesrow = str(tile[1])
            seriescol = str(11 - tile[0])
            if (len(seriescol) == 1):
                seriescol = "0" + seriescol
            id = seriescol + seriesrow
        
        return(id)

    def tileseriesfromtile250(self, tile250):
        mapsperseries = self.mapsperseries(tile250[1])
        tilex = int(np.floor(tile250[0] / mapsperseries))
        tiley = int(np.floor(tile250[1] / 4))
        tiles = (tilex, tiley)
        return(tiles)
        
    @staticmethod    
    def tile250y(lat):
        tile = int(np.floor(lat - 40.0))
        return(tile)
        
    def tile250x(self, lon, lat):
        wo = self.widthandoffset250(lat)
        tile = int(np.floor((lon + (144 - wo[1])) / wo[0]))
        return(tile)
            
    def tile250(self, lon, lat):
        tile = [self.tile250x(lon, lat), self.tile250y(lat)]
        return(tile)

    def id250(self, tile250):
        tileS = self.tileseriesfromtile250(tile250)
        seriesid = self.idseries(tileS)
        if (seriesid is None):
            return(None)
        
        seriesMinYTile = tileS[1] * 4
        yTileInSeries = tile250[1] - seriesMinYTile
        
        mapsPerSeries = self.mapsperseries(tile250[1])
        seriesMinXTile = tileS[0] * mapsPerSeries
        xTileInSeries = tile250[0] - seriesMinXTile
        
        arealetter = None
        if (tileS[1] >= 7):
            arealetter = self.MAP_250K_N_OF_68[yTileInSeries, xTileInSeries]
        else:
            arealetter = self.MAP_250K[yTileInSeries, xTileInSeries]
        
        id = [seriesid, arealetter]
        return(id)

    def bybboxgeneric(self, bbox, tilefuncx, tilefuncy, idfunc):
        minx = max(bbox[0,0], -144.0)
        miny = max(bbox[1,0], 40.0)
        maxx = min(bbox[0,1], -48.0)
        maxy = min(bbox[1,1], 88.0)

        if ((maxx < minx) or (maxy < miny)):
            raise Exception("Bounds provided may be outside the CDEM grid")
        
        containsabove80 = maxy > 80.0
        containsabove68 = containsabove80 or (miny >= 68.0) or (maxy>68.0)
        containsbelow68 = miny < 68.0
        containsbelow80 = miny < 80.0
        
        self.idlist = list()
        
        def ld(n=maxy, e=maxx, s=miny, w=minx):
            mint = (tilefuncx(w, s), tilefuncy(s))
            maxt = (tilefuncx(e, n), tilefuncy(n))
            
            for x in range(mint[0], maxt[0] + 1):
                for y in range(mint[1], maxt[1] + 1):
                    tileid = idfunc(np.array([x,y]))
                    if(np.atleast_1d(tileid)[0] is not None):
                        self.idlist.append(tileid)
                        

        if (containsabove80):
            if (containsbelow80):
                ld(s=80)
            else:
                ld()            
            return(np.array(self.idlist))

        
        tempn = maxy
        temps = miny
        
        if (containsabove68):
            if (containsabove80):
                tempn = 79.99

            if (containsbelow68):
                temps = 68.0

            ld(s=temps, n=tempn)

        
        if (containsbelow68):
            tempn = maxy
            if (containsabove68):
                tempn = 67.99
            
            ld(n=tempn)
            
        return(np.array(self.idlist))
            
            
    def _bybbox(self, bbox):
        tilexfunc = self.tile250x
        tileyfunc = self.tile250y
        idfunc    = self.id250

        sheets = self.bybboxgeneric(bbox, tilexfunc, tileyfunc, idfunc)
        
        return(sheets)
    
    @classmethod
    def bybbox(cls, bbox):
        N = cls()
        result = N._bybbox(bbox)
        return(result)

