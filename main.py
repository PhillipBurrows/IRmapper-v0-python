import slint, sys, os, geopandas, subprocess, sys, shutil, pandas
from osgeo import ogr

class MainWindow(slint.loader.ui.app_window.AppWindow):


    @slint.callback
    def open_request_dump_folder(self):
        """ 
        Opens the 'request-dump' folder in the default file explorer. 
        """
        print("...Opening request dump folder...")
        folder_path = os.path.join(os.path.dirname(__file__), 'databases/requests/request-dump/')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', folder_path])
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['explorer', folder_path])
        else:
            print(f"Unsupported OS: {sys.platform}")

    @slint.callback
    def purge_request_dump_folder(self):
        """ 
        Deletes all objects in the 'request-dump' folder. 
        """
        print("...Emptying request dump folder...")
        folder_path = os.path.join(os.path.dirname(__file__), 'databases/requests/request-dump/')
        if not os.path.exists(folder_path):
            print("Request-dump folder does not exist.")
            return
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
        print("...Request dump folder cleared...")

    @slint.callback
    def process_request_dump_folder(self):
        """ 
        Processes request files in the 'request-dump' folder and push them to the requestGDB.
        """
        print("...Processing request dump folder...")
        request_dump_folder = os.path.join(os.path.dirname(__file__), 'databases/requests/request-dump/')

        ## Validation: verify file contains column "FIRE_NUMBE"
        for root, dirs, files in os.walk(request_dump_folder):
            for name in files:        
                if name.endswith('.shp'):
                    gdf = geopandas.read_file(os.path.join(root, name))
                    if "FIRE_NUMBE" not in gdf:
                        print(f"Shapefile {name} does not contain a 'FIRE_NUMBE' column - add field to attribute table")
                        self.request_data_validity_issue = f"Shapefile {name} does not contain a 'FIRE_NUMBE' column - \n add field to attribute table"
                        self.request_data_validity_status = "invalid"
                        return
                    else:
                        print("1) All files contain FIRE_NUMBE identification column")
                    
        ## Validation: verify correct CRS
        for root, dirs, files in os.walk(request_dump_folder):
            for name in files:
                if name.endswith('.shp'):
                    gdf = geopandas.read_file(os.path.join(root, name))
                    if gdf.crs != "EPSG:3400":
                        issue = f"CRS incorrect for this jursidiction - file: {name} - change crs to EPSG:3400"
                        self.request_data_validity_issue = issue
                        self.request_data_validity_status = "invalid"
                        print(issue)
                        return
                    else:
                        print("2) All perimeters have correct CRS")

        ## Validation: verify each fire is a single multipart object - not multiple singlepart geometries
        import collections
        for root, dirs, files in os.walk(request_dump_folder):
            for name in files:
                if name.endswith('.shp'):
                    gdf = geopandas.read_file(os.path.join(root, name))
                    fireID_list = list(gdf['FIRE_NUMBE'])
                    duplicated = [k for k, v in collections.Counter(fireID_list).items() if v > 1]
                    if duplicated != []:
                        issue = f"Fire(s) {duplicated} in file {name} is in multiple singlepart features: merge into multipart geometry"
                        self.request_data_validity_issue = issue
                        self.request_data_validity_status = "invalid"
                        print(issue)
                        return
                    else:
                        print("3) All perimeters are built of a single multipart geometry")

        ## Validation: verify no repeated fires between files
        requested_fires = []
        for root, dirs, files in os.walk(request_dump_folder):
            for name in files:        
                if name.endswith('.shp'):
                    shapefile = geopandas.read_file(os.path.join(root, name))
                    for fire in shapefile['FIRE_NUMBE']:
                        requested_fires.append(fire)
        duplicated = [k for k, v in collections.Counter(requested_fires).items() if v > 1]
        if duplicated != []:
            issue = f"Fires {duplicated} are duplicated across request files: delete down to one instance of fire"
            self.request_data_validity_issue = issue
            self.request_data_validity_status = "invalid"
            print(issue)
            return
        else:
            print("4) No fire IDs are repeated across different request files")

        ## Pass validation
        self.request_data_validity_issue = "passed checks"
        self.request_data_validity_status = "valid"
        print("request dump folder processing complete...")

    @slint.callback
    def purge_perimeter_geodatabase(self):
        """ 
        Deletes all objects in the perimeter geodatabase.
        """
        print("...Purging the perimeter geodatabase...")
        # Path to your GeoPackage file
        gpkg_path = os.path.join(os.path.dirname(__file__), 'databases/requests/requests-geodatabase.gpkg')
        if not os.path.exists(gpkg_path):
            print("Perimeter geodatabase does not exist.")
            return
        
        # Open the GeoPackage in update mode
        driver = ogr.GetDriverByName("GPKG")
        datasource = driver.Open(gpkg_path, 1)  # 1 for update mode
        if datasource is None:
            print(f"Error: Could not open GeoPackage at {gpkg_path}")
            return
        
        # Get the number of layers
        num_layers = datasource.GetLayerCount()
        print(f"Found {num_layers} layers in {gpkg_path}")
 
        # Delete layers in reverse order to avoid issues with index changes
        for i in range(num_layers - 1, -1, -1):
            layer = datasource.GetLayerByIndex(i)
            layer_name = layer.GetName()
            print(f"Deleting layer: {layer_name}")
            datasource.DeleteLayer(i)

        # Close the datasource to ensure changes are written
        datasource = None

        # Compact the GeoPackage (optional but recommended for space optimization)
        # This requires reopening the GeoPackage and performing a VACUUM operation
        print("...Compacting GeoPackage...")
        driver = ogr.GetDriverByName("GPKG")
        datasource = driver.Open(gpkg_path, 1)
        if datasource:
            datasource.ExecuteSQL("VACUUM;")
            datasource = None
            print("...Compacting GeoPackage...")
        else:
            print("-Could not reopen GeoPackage for compaction.")

        print("Perimeter geodatabase purged.")

    @slint.callback
    def inject_perimeter_geodatabase(self):
        """ 
        Injects the request perimeters into the perimeter geodatabase.
        """
        print("...Injecting request perimeters into perimeters-geodatabase...")
        request_dump_folder = os.path.join(os.path.dirname(__file__), 'databases/requests/request-dump/')
        gdb_path = os.path.join(os.path.dirname(__file__), 'databases/requests/requests-geodatabase.gpkg')

        if not os.path.exists(gdb_path):
            print("Perimeter geodatabase does not exist.")
            return
        
        requested_fires = []
        for root, dirs, files in os.walk(request_dump_folder):
            for name in files:        
                if name.endswith('.shp'):
                    gdf_fires = geopandas.read_file(os.path.join(root, name))
                    fires_list = gdf_fires['FIRE_NUMBE'].unique()
                    print(f'fires_list from {name}: {fires_list}')
                    for fire in fires_list:
                        requested_fires.append(fire)
                        single_fire_gdf = gdf_fires[gdf_fires['FIRE_NUMBE'] == fire]
                        single_fire_gdf = single_fire_gdf.filter(items = ['FIRE_NUMBE', 'geometry'])
                        # add a new column called injection_timestamp with the current date and time   
                        single_fire_gdf['update_timestamp'] = pandas.Timestamp.now()
                        print(single_fire_gdf.head())
                        single_fire_gdf.to_file(gdb_path, layer=fire, driver="GPKG", mode="a")
                        print(f"Injected {fire} into perimeter geodatabase.")
        print("...Request perimeters injected into perimeter geodatabase...")




main_window = MainWindow()
main_window.show()
main_window.run()