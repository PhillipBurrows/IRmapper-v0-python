import slint, sys, os, geopandas


class MainWindow(slint.loader.ui.app_window.AppWindow):
    @slint.callback
    def kml_to_shapefile(self, kml_path):
        """
        Converts a .kml file to a shapefile and saves it in the same directory.
        Args:
            kml_path (str): Path to the .kml file.
        Returns:
            str: Path to the created shapefile (.shp).
        """
        # Read the KML file
        gdf = geopandas.read_file(kml_path, driver='KML')##.columns("FID", "Name", "Object", "geometry")
        print(gdf.head())

        # Prepare output path
        base = os.path.splitext(kml_path)[0]
        shp_path = base + ".shp"
        
        # Save as shapefile
        gdf.to_file(shp_path, driver='ESRI Shapefile')
        #return shp_path

    def open_file_dump_folder(self):
        """
        Opens the file dump folder in the default file explorer.
        """
        print("Opening file dump folder...")


main_window = MainWindow()
main_window.show()
main_window.run()
