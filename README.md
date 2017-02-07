BEng Project: Avalanche Hazard Visualiser 
===================

An app to visualise avalanche hazards in Scottish mountains, using data from Ordnance Survey and Scottish Avalanche Information Service, a complex system programmed in Python, MATLAB, JavaScript and many other languages.

#Installation#
This system is to be deployed on an Ubuntu 14.04 LTS or 16.04 LTS system. Currently, the GDAL package in pip does not have gdal_array, so it cannot be used. Instead, the easy_install GDAL package works fine.

Locations of the height map and aspect raster files are defined in `GeoData/raster.py`, change them as necessary before proceeding. The system requires the following rasters computed in QGIS:
* `HEIGHT_RASTER`: height map DTM raster.
* `ASPECT_RASTER`: terrain aspect map raster, computed by gdaldem.
* `CONTOUR_RASTER`: a useful overlay map from an OS 1:25000 map raster.
* `RISK_RASTER`: static risk raster computed by `Computations/static_risk.m`, which in addition to `ASPECT_RASTER` requires a raster of terrain slope (by gdaldem) and a raster of curvature (by r.slope.aspect from GRASS).

Install system-level dependencies:

        sudo apt-get install libgdal-dev python-setuptools python-pip virtualenv nginx uwsgi 

Download Cesium and place it in a directory for NGINX:

        wget https://cesiumjs.org/releases/Cesium-1.27.zip
        unzip Cesium-1.27.zip

Suppose the project directory is `/home/BEngProject` and the Cesium web directory is `/home/cesium`.
        
Remove the original index.html and Terrain.html, replace it with ours:

        cd /home/cesium
        mv index.html index.old.html
        mv Apps/Sandcastle/gallery/Terrain.html Apps/Sandcastle/gallery/Terrain.old.html
        ln -s /home/BEngProject/Cesium/index.html /home/cesium/index.html
        ln -s /home/BEngProject/Cesium/Apps/Sandcastle/gallery/Terrain.html /home/cesium/Apps/Sandcastle/gallery/Terrain.html

Now copy over the configuration files for uwsgi. For 14.04 LTS with upstart, this is:

        cd /home/BEngProject
        ln -s Scripts/terrain_api_server.conf /etc/init/terrain_api_server.conf 

For 16.04 LTS with systemd:

        cd /home/BEngProject
        ln -s Scripts/terrain_api_server.service /etc/systemd/system/terrain_api_server.service 

Adapt the NGINX virtual host configuration `Scripts/avalanche.ebornet.com` for your needs, particularly the locations of TLS certificates you use. Then link the configuration for NGINX:

        ln -s Scripts/avalanche.ebornet.com /etc/nginx/sites-enabled/avalanche.ebornet.com

Now to configure python environment:

        cd /home/BEngProject
        virtualenv env
        source env/bin/activate
        easy_install GDAL #The pip package does not work.
        pip install -r DEPENDENCIES #Install the rest of dependencies.
        deactivate
 
Now to start all services, for 14.04 LTS with upstart:
        
        sudo start terrain_api_server
        # Check /var/log/upstart/terrain_api_server.log for any problems.
        sudo nginx -t #Test config
        sudo service nginx restart

For 16.04 LTS with systemd:

        sudo systemctl start terrain_api_server
        sudo systemctl status terrain_api_server #Check for any problems.
        sudo nginx -t #Test config
        sudo systemctl restart nginx

Any problems with installation should be indicated in the relevant logs. 
        


