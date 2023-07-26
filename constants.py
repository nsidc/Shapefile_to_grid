import netCDF4
import numpy as np

PROJ_DEST = 'EPSG:4326'
bb = 20.
land = 20.
offgrid = 1.
finalbb = 115.
finalland = 120.
finaloffgrid = 105.

def get_latlon():

   latlon=netCDF4.Dataset("latlonlandmask.nc")
   latdst=latlon['latitude'][:]
   londst=latlon['longitude'][:]
   landmask=latlon['LandRegion_mask'][:,:]

   numlat = len(latdst)
   numlon = len(londst)

# Create 2d lat and lon arrays
   lat2d=np.empty((numlat,numlon),"float")
   lon2d=np.empty((numlat,numlon),"float")
   for i in range(numlon):
      lat2d[:,i]=latdst[:]

   for i in range(numlat):
      lon2d[i,:]=londst[:]

   return lat2d,lon2d,latdst,londst,landmask,numlat,numlon
