import numpy as np
import geopandas as gpd
import pyproj
import shapely
import netCDF4
import pandas as pd
import constants
import calendar
from datetime import datetime, timedelta, date, timezone

# Function to read shapefile using geopandas
def read_shapefile(infile):
   gdf=gpd.read_file(infile)
   return gdf

# Function to create grid in original map projection for shapefile matching purposes
def create_grid(lat2d,lon2d,crs_in,crs_out,numlat,numlon):

   xx = np.empty((numlat,numlon),"double")
   yy = np.empty((numlat,numlon),"double")
   transformer = pyproj.Transformer.from_crs(crs_out,crs_in)
   xx,yy = transformer.transform(lat2d,lon2d)

   x1d = xx.flatten()
   y1d = yy.flatten()
   df = pd.DataFrame({'x':x1d,'y':y1d})
   df['coords'] = list(zip(df['x'],df['y']))
   df['coords'] = df['coords'].apply(shapely.geometry.Point)

   gridpoints=gpd.GeoDataFrame(df,geometry='coords',crs=crs_in)

   return gridpoints

# Function to create an array to mask out gridpoints outside of shapefile domains
def create_boundary_mask(gridpoints,numlat,numlon,crs_in,crs_out):
   lat_points = [40.,38.,35.,43.,40.]
   lon_points = [-163.,120.,20.,-52.,-163.]
   transformer = pyproj.Transformer.from_crs(crs_out,crs_in)
   xpts,ypts=transformer.transform(lat_points,lon_points)
   pts = zip(ypts,xpts)

   boundary_geometry = shapely.geometry.Polygon(pts)
   boundary = gpd.GeoDataFrame(index=[0],crs=crs_in,geometry = [boundary_geometry])
   
   temp_mask=gpd.tools.sjoin(gridpoints,boundary,predicate="within",how='left')
   values = np.array(temp_mask.index_right)
   boundary_mask = np.nan_to_num(values,nan=1)
   boundary_mask2d=boundary_mask.reshape(numlat,numlon)

   return boundary_mask2d

# Function to get final array
def get_final_arr(gridpoints,gdf,landmask,domain_boundary,numlat,numlon):
   
# Find gridpoints inside each of the shapefiles corresponding to different 
# seaice concentrations
   insidepts_t = gpd.tools.sjoin(gridpoints,gdf,predicate="within",how='left')
   insidepts_t['Conc'] = insidepts_t['Conc'].fillna(0)
   insidepts=insidepts_t.groupby(insidepts_t.index).first()

# Reshape arrays to 2d, convert concentration to %
   xes=insidepts['x'].to_numpy()
   yes=insidepts['y'].to_numpy()
   conc=insidepts['Conc'].to_numpy()

   x2d = xes.reshape(numlat,numlon)
   y2d = yes.reshape(numlat,numlon)
   conc2d = conc.reshape(numlat,numlon)
   conc2d = conc2d*10.

# Find land points according to land mask
   addland = np.where(landmask == constants.land,constants.finalland,conc2d)
# Convert 20s to a flag for bergy bit (see user manual)
   addbb = np.where(addland == constants.bb,constants.finalbb, addland)
# Set flag for gridpoints outside of domain
   finalconc = np.where(domain_boundary == constants.offgrid,constants.finaloffgrid,addbb)
# Convert to datatype byte
   finalconc = finalconc.astype(np.byte) 

   return finalconc,x2d,y2d

# Function to write everything to a netcdf file
def write_netcdf(finalconc,latdst,londst,xx,yy,data_date,outfile,numlat,numlon):

   curdate = datetime(int(data_date[0:4]),int(data_date[5:7]),int(data_date[8:10]),0,0,0)
   start_date = datetime(1900,1,1,0,0,0)
   numdays = curdate - start_date
   days = numdays.days
   tcs = datetime(int(data_date[0:4]),int(data_date[5:7]),1,0,0,0)
   time_coverage_start = tcs.strftime("%Y-%m-%d %H:%M:%S")
   dyinmo = calendar.monthrange(int(data_date[0:4]),int(data_date[5:7]))[1]
   tce = datetime(int(data_date[0:4]),int(data_date[5:7]),dyinmo,23,59,59)
   time_coverage_end = tce.strftime("%Y-%m-%d %H:%M:%S")

   ncfile = netCDF4.Dataset(outfile,mode="w",format="NETCDF4_CLASSIC")

# Global attributes
   ncfile.Conventions = "CF-1.10, ACDD-1.3"
   ncfile.title = "Arctic Sea Ice Concentration and Extent from Danish Meteorological Institute Sea Ice Charts, 1901-1956"
   ncfile.summary = "This data set provides estimates of Arctic sea ice concentration from 1901 to 1956 created from a collection of historic, hand-drawn sea ice charts from the Danish Meteorological Institute (DMI)."
   ncfile.keywords = "EARTH SCIENCE > CRYOSPHERE > SEA ICE > SEA ICE CONCENTRATION, OCEAN > ARCTIC OCEAN"
   ncfile.keywords_vocabulary = "NASA Global Change Master Directory (GCMD) Keywords, Version 15.9"
   ncfile.creator_name = "NOAA at the National Snow and Ice Data Center (NOAA@NSIDC)"
   ncfile.creator_email = "nsidc@nsidc.org"
   ncfile.creator_url = "https://nsidc.org/data/data-programs/noaa-nsidc"
   ncfile.institution = "National Snow and Ice Data Center (NSIDC)"
   ncfile.creator_type = "Insitution"
   ncfile.creator_institution = "National Snow and Ice Data Center (NSIDC)"
   ncfile.date_created = datetime.now(timezone.utc).replace(tzinfo=None,microsecond=0).isoformat()+'Z'
   ncfile.geospatial_lat_max = 90.00
   ncfile.geospatial_lat_min = 30.00
   ncfile.geospatial_lat_resolution = "1/4 degreee"
   ncfile.lat_units = "degrees_north"
   ncfile.geospatial_lon_max = 360.
   ncfile.geospatial_lon_min= 0.
   ncfile.geospatial_lon_resolution = "1/4 degreee"
   ncfile.lon_units = "degrees_east"
   ncfile.time_coverage_start = time_coverage_start
   ncfile.time_coverage_end = time_coverage_end
   ncfile.time_coverage_resolution = "P1M" 
   ncfile.time_coverage_duration = "P1M" 
   ncfile.id = "G10007"
   ncfile.license = "No constraints on data access or use"
   ncfile.acknowledgement = "Development of this product was supported by NOAA NCEI through NOAA cooperative agreement NA22OAR4320151."
   ncfile.processing_level = "NOAA Level 4"
   ncfile.standard_name_vocabulary = "CF Standard Name Table (Version 81, April 2023)"
   ncfile.cdm_data_type = "Grid"
   ncfile.contributor_name = "NOAA at NSIDC"
   ncfile.contributor_role = "Producer"
   ncfile.platform = "Charts"
   ncfile.platform_vocabulary = "NASA Global Change Master Directory (GCMD) Keywords, Version 9.0"
   ncfile.product_version = "Version 2"
   ncfile.publisher_email = "nsidc@nsidc.org"
   ncfile.publisher_name = "National Snow and Ice Data Center"
   ncfile.publisher_url = "https://nsidc.org/"
   ncfile.publisher_institution = "National Snow and Ice Data Center"
   ncfile.publisher_type = "Institution"
   ncfile.metadata_link = "https://nsidc.org/data/G10007"
   ncfile.naming_authority = "org.nsidc"
   ncfile.source = "The input data are the Arctic Sea Ice Charts from Danish Meteorological Institute, 1893 - 1956, Version 1 (https://nsidc.org/data/g02203)"
   
   lat_dim = ncfile.createDimension('lat',numlat)
   lon_dim = ncfile.createDimension('lon',numlon)

   time = ncfile.createVariable('time',np.float32)
   time.standard_name = "time"
   time.long_name = "time"
   time.units = "days since 1900-01-01 00:00:00"
   time.calendar = "julian"
   time.coverage_content_type = "coordinate"
   time.axis = "T"

   crsout = netCDF4.stringtochar(np.array('crs',dtype='S3'))
   crs = ncfile.createVariable('crs','S1')
   crs.grid_mapping_name = "latitude_longitude"
   crs.long_name = "Quarter-degree Latitude-Longitude Grid North of 30 degrees"
   crs.longitude_of_prime_meridian = 0.
   crs.semi_major_axis = 6378137.
   crs.inverse_flattening = 298.257223563 
   crs.crs_wkt = "GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563,AUTHORITY[\"EPSG\",\"7030\"]],AUTHORITY[\"EPSG\",\"6326\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AXIS[\"Latitude\",NORTH],AXIS[\"Longitude\",EAST],AUTHORITY[\"EPSG\",\"4326\"]]" 
   crs.GeoTransform = "-180 0.25 0 90 0 -0.25 "
   
   latitude = ncfile.createVariable('latitude', np.float32, ('lat',))
   latitude.units = 'degrees_north'
   latitude.long_name = 'latitude'
   latitude.standard_name = 'latitude'
   latitude.valid_range = [30.125,89.875]

   longitude = ncfile.createVariable('longitude', np.float32, ('lon',))
   longitude.units = 'degrees_east'
   longitude.long_name = 'longitude'
   longitude.standard_name = 'longitude'
   longitude.valid_range = [0.125,359.875]

   x = ncfile.createVariable('x', np.float64, ('lat','lon'))
   x.valid_range = [-7346358.404107877,7346358.404107877]
   x.units = 'm'
   x.standard_name = 'projection_x_coordinate'
   x.long_name = 'x'
   x.coverage_content_type = 'coordinate'

   y = ncfile.createVariable('y', np.float64, ('lat','lon'))
   y.valid_range = [-7346358.404107877,7346358.404107877]
   y.units = 'm'
   y.standard_name = 'projection_y_coordinate'
   y.long_name = 'y'
   y.coverage_content_type = 'coordinate'

   seaice_conc=ncfile.createVariable("seaice_conc",np.byte,('lat','lon'),fill_value=105)
   seaice_conc.units="percent"
   seaice_conc.short_name="Concentration"
   seaice_conc.long_name="Sea Ice Concentration"
   seaice_conc.standard_name="sea_ice_area_fraction"
   seaice_conc.valid_range = [0,120]
   seaice_conc.flag_values="105,110,115,120"
   seaice_conc.flag_meanings="off_grid unknown_sea_ice_or_ice_edge bergy_bit land"
   seaice_conc.comment = "Values of  percent concentration are from 0 to 100. Sentinel values of 110, 115, and 120 in the concentration array indicate ice present but concentration is unknown, bergy bit, and land, respectively."
   seaice_conc.coverage_content_type="image"
   seaice_conc.grid_mapping = "crs"
   seaice_conc.date=data_date
   latitude[:]=latdst
   longitude[:]=londst
   x[:,:]=xx
   y[:,:]=yy
   time[:]=np.asarray(days)
   crs=crsout
   seaice_conc[:,:]=finalconc
   ncfile.close()
