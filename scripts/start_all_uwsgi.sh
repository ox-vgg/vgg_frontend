#!/bin/bash

# Check the parameter to the script.
# The strings used as parameter should correspond to the
# engines short-name in the settings of visorgen
case "${1}" in
    text)
        ## Start the text-search engine ##
        /webapps/visorgen/vgg_frontend/scripts/start_backend_service.sh text
        # Use the command below to overwrite the predefined settings and include setting for the text-search engine only (optional for docker deployment)
        cp -f /webapps/visorgen/backend_data/settings_text.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
    ;;
    category)
        ## Start the cpuvisor-srv engine ##
        /webapps/visorgen/vgg_frontend/scripts/start_backend_service.sh cpuvisor-srv
        # Use the command below to overwrite the predefined settings and include setting for the cpuvisor-srv engine only (optional for docker deployment)
        cp -f /webapps/visorgen/backend_data/settings_cpuvisor-srv.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
    ;;
    faces)
        ## Start the cpuvisor-srv engine ##
        /webapps/visorgen/vgg_frontend/scripts/start_backend_service.sh faces
        # Use the command below to overwrite the predefined settings and include setting for the faces engine only (optional for docker deployment)
        cp -f /webapps/visorgen/backend_data/settings_faces.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
    ;;
    *)
        ## Start both ##
        /webapps/visorgen/vgg_frontend/scripts/start_backend_service.sh cpuvisor-srv
        /webapps/visorgen/vgg_frontend/scripts/start_backend_service.sh text
        /webapps/visorgen/vgg_frontend/scripts/start_backend_service.sh faces
        # Use the command below to overwrite the predefined settings (optional for docker deployment)
        cp -f /webapps/visorgen/backend_data/settings.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
    ;;
esac
cd /webapps/visorgen/vgg_frontend/
/etc/init.d/nginx restart
./start_uwsgi_server.sh
#tail -f /dev/null # (for docker deployment)
