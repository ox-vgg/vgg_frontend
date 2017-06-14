#!/bin/bash

# Check the parameter to the script.
# The strings used as parameter should correspond to the
# engines short-name in the settings of visorgen
case "${1}" in
    text)
        ## Start the text-search engine ##

        # run text-retrieval backend
        screen -dm -S visorgen-text-backend-service bash -l -c 'cd /webapps/visorgen/; source ./bin/activate; cd /webapps/visorgen/text_search/; python text_retrieval_backend.py'
    ;;
    cpuvisor-srv)
        ## Start the cpuvisor-srv engine ##

        # run cpuvisor services
        screen -dm -S visorgen-cpuvisor-service bash -l -c 'cd /webapps/visorgen/vgg_classifier/bin/; ./cpuvisor_service'
        screen -dm -S visorgen-backend-service bash  -l -c 'cd /webapps/visorgen/; source ./bin/activate; cd /webapps/visorgen/vgg_classifier/; python legacy_serve.py'

        # run image downloader tool
        screen -dm -S visorgen-img_downloader bash  -l -c 'cd /webapps/visorgen/; source ./bin/activate; cd /webapps/visorgen/vgg_frontend/vgg_img_downloader; ./start_service.sh'
    ;;
    *)
        echo "Usage: ${0} {text|cpuvisor-srv}" >&2
    ;;
esac

exit 0
