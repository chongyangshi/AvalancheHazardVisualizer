BEng Project: Avalanche Hazard Visualiser
===================

An app to visualise avalanche hazards in Scottish mountains, using data from Ordnance Survey and Scottish Avalanche Information Service, a complex system programmed in Python, MATLAB, JavaScript and many other languages.

# Installation #
This system is to be deployed on an Ubuntu 14.04 LTS or 16.04 LTS system.

Locations of the height map and aspect raster files are defined in `GeoData/raster.py`, change them as necessary before proceeding. The system requires the following rasters computed in QGIS:
* `HEIGHT_RASTER`: height map DTM raster.
* `ASPECT_RASTER`: terrain aspect map raster, computed by gdaldem.
* `CONTOUR_RASTER`: a useful overlay map from an OS 1:25000 map raster.
* `RISK_RASTER`: static risk raster computed by `Computations/static_risk.m`, which in addition to `ASPECT_RASTER` requires a raster of terrain slope (by gdaldem) and a raster of curvature (by r.slope.aspect from GRASS).

Initial deployment requires root.

Install system-level dependencies:

        apt-get install python-setuptools python-pip virtualenv nginx

Install uwsgi with pip at system level (system package may be broken at this time):

        pip install uwsgi
        which uwsgi # Check that it is indeed /usr/local/bin/uwsgi or you may need to change terrain_api_server.service or terrain_api_server.conf in Scripts/

Build GDAL 2 since we only have GDAL 1 in the official repository:

        wget http://download.osgeo.org/gdal/2.1.3/gdal-2.1.3.tar.gz
        tar zxvf gdal-2.1.3.tar.gz
        cd gdal-2.1.3
        apt-get build-dep gdal
        ./configure --prefix=/usr/
        make && make install

Download Cesium and place it in a directory for NGINX:

        mkdir /home/cesium
        cd /home/cesium
        wget https://cesiumjs.org/releases/Cesium-1.30.zip
        unzip Cesium-1.30.zip

Suppose the project directory is `/home/BEngProject` and the Cesium web directory is `/home/cesium`.

Remove the original index.html and Terrain.html, replace it with ours:

        cd /home/cesium
        mv index.html index.old.html
        mv Apps/Sandcastle/gallery/Terrain.html Apps/Sandcastle/gallery/Terrain.old.html
        ln -s /home/BEngProject/Cesium/index.html /home/cesium/index.html
        ln -s /home/BEngProject/Cesium/Terrain.html /home/cesium/Apps/Sandcastle/gallery/Terrain.html

Now copy over the configuration files for uwsgi. For 14.04 LTS with upstart, this is:

        cd /home/BEngProject
        ln -s /home/BEngProject/Scripts/terrain_api_server.conf /etc/init/terrain_api_server.conf

For 16.04 LTS with systemd:

        cd /home/BEngProject
        ln -s /home/BEngProject/Scripts/terrain_api_server.service /etc/systemd/system/terrain_api_server.service

Adapt the NGINX virtual host configuration `Scripts/avalanche.ebornet.com` for your needs, particularly the locations of TLS certificates you use. Then link the configuration for NGINX:

        ln -s /home/BEngProject/Scripts/avalanche.ebornet.com /etc/nginx/sites-enabled/avalanche.ebornet.com

Now to configure python environment:

        cd /home/BEngProject
        virtualenv env
        source env/bin/activate
        easy_install GDAL # The only way to correctly install the Python bindings at this time.
        pip install -r DEPENDENCIES #Install the dependencies.
        deactivate

Set permissions:

        chown -R www-data:www-data /home/BEngProject /home/cesium

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
