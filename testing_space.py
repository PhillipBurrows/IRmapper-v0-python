import geopandas
import os

def kml_to_shapefile(kml_path):
    """
    Converts a .kml file to a shapefile and saves it in the same directory.
    Args:
        kml_path (str): Path to the .kml file.
    Returns:
        str: Path to the created shapefile (.shp).
    """
    # Read the KML file
    gdf = geopandas.read_file(kml_path, driver='KML')
        
    # Prepare output path
    base = os.path.splitext(kml_path)[0]
    shp_path = base + ".shp"
        
    # Save as shapefile
    gdf.to_file(shp_path, driver='ESRI Shapefile')
    #return shp_path

kml_to_shapefile("/Users/phillipburrows/Documents/verimap/IRmapper-v0-python/IRmapper-test-data/YYC_line.kml")  # Replace with your KML file path