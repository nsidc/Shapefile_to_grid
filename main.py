import glob
import constants
import all_functions as af

def main(infile):

# Call function to get lat/lon/landmask data
   lat2d,lon2d,latdst,londst,landmask,numlat,numlon = constants.get_latlon()

# Call function to read in shapefile
   gdf = af.read_shapefile(infile)

   data_date = gdf.Date[0]
   outdir = "Output_directory/"
   outfile = outdir+"Gridded_output_"+data_date[0:7]+".nc"

# CRS info for input data (crs_in)and output grid (crs_out)
   crs_in = gdf.crs
   crs_out = constants.PROJ_DEST

# Call function to create grid in original map projection
   gridpoints = af.create_grid(lat2d,lon2d,crs_in,crs_out,numlat,numlon)
 
# Call function to create a mask for areas outside of the domain
   domain_boundary = af.create_boundary_mask(gridpoints,numlat,numlon,crs_in,crs_out)

# Call function to find gridpoints inside each of the seaice concentration shapefiles
   finalconc,x2d,y2d = af.get_final_arr(gridpoints,gdf,landmask,domain_boundary,numlat,numlon)
 
# Call function to write out all the data to a netcdf file
   af.write_netcdf(finalconc,latdst,londst,x2d,y2d,data_date,outfile,numlat,numlon)

if (__name__ == "__main__"):
   datadir="Input_directory/"
   ffiles = glob.glob(datadir+"*.shp")
   for i in ffiles:
      print(i)
      main(i)
