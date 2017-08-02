#!/bin/bash

# Check the parameter to the script.
# The strings used as parameter should correspond to the
# engines short-name in the settings of visorgen
case "${1}" in
    text)
        ## Start the text-search engine ##
        /webapps/visorgen/visorgen/scripts/start_backend_service.sh text
        # Use the command below to overwrite the predefined settings and include setting for the text-search engine only (for docker deployment)
        cp -f /webapps/visorgen/backend_data/settings_text.py /webapps/visorgen/visorgen/visorgen/settings.py
    ;;
    category)
        ## Start the cpuvisor-srv engine ##
        /webapps/visorgen/visorgen/scripts/start_backend_service.sh cpuvisor-srv
        # Use the command below to overwrite the predefined settings and include setting for the cpuvisor-srv engine only (for docker deployment)
        cp -f /webapps/visorgen/backend_data/settings_cpuvisor-srv.py /webapps/visorgen/visorgen/visorgen/settings.py
    ;;
    *)
        ## Start both ##
        /webapps/visorgen/visorgen/scripts/start_backend_service.sh cpuvisor-srv
        /webapps/visorgen/visorgen/scripts/start_backend_service.sh text
        cp -f /webapps/visorgen/backend_data/settings.py /webapps/visorgen/visorgen/visorgen/settings.py
    ;;
esac
cd /webapps/visorgen/visorgen/
python manage.py runserver 0.0.0.0:8000
#tail -f /dev/null # (for docker deployment)
