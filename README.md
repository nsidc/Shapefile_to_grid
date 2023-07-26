

<p align="center">
  <img alt="NSIDC logo" src="https://nsidc.org/themes/custom/nsidc/logo.svg" width="150" />
</p>


## Shapefile_to_grid

This code was used to grid the shapefiles in the following G10007 dataset at NSIDC (located here: https://nsidc.org/data/g10007/versions/1) to a 1/4 degree latitude/longitude grid to 30N. The code contains items very specific to this project (i.e. grid boundaries, flags for the data).

## Level of Support

This repository is not actively supported by NSIDC but we welcome issue submissions and
  pull requests in order to foster community contribution.

See the [LICENSE](LICENSE) for details on permissions and warranties. Please contact
nsidc@nsidc.org for more information.

## Requirements

This code was run in Python version 3.9. The following modules were used:
  - numpy=1.23.3
  - netCDF4=1.6.2
  - geopandas=0.12.1
  - pyproj=3.4.1
  - shapely=2.0.0
  - pandas=1.5.1

## Usage

- To run: python < main.py
- The program is currently structured to list all shapefiles (i.e. all files with the .shp suffix) in a directory.
- Each user will very likely need to change the following to their specific data:
-    The values in the constants.py file to their specifications.
-    The directory where their input data live (datadir in main.py)
-    The directory and name of the file that contains the information for their final output grid (get_latlon function in constants.py)
-    The directory and name for output data (outdir and outfile in main.py)

## Credit

This content was developed by the National Snow and Ice Data Center with funding from
multiple sources.
