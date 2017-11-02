#!/bin/bash

# Check the parameter to the script.
# The strings used as parameter should correspond to the
# engines short-name in the settings of visorgen
case "${1}" in
    text)
        ## Stop the text-backend engine ##

        GREP=$(ps -fe | grep "[t]ext_retrieval_backend")
        if [ "$GREP" ]; then
            SESSION=$(screen -ls | grep -o ".*.visorgen-text-backend-service")
            if [ "$SESSION" ]; then
                screen -X -S $SESSION quit
            fi
        fi
        pkill -9 -f 'python text_retrieval_backend.py'
    ;;
    cpuvisor-srv)
        ## Stop the cpuvisor-srv engine ##

        # stop cpuvisor_service

        GREP=$(ps -fe | grep "[c]puvisor_service")
        if [ "$GREP" ]; then
            SESSION=$(screen -ls | grep -o ".*.visorgen-cpuvisor-service")
            if [ "$SESSION" ]; then
                screen -X -S $SESSION quit
            fi
        fi
        pkill -9 -f 'cpuvisor_service'

        GREP=$(ps -fe | grep ".*[v]isorgen-backend-service.*")
        if [ "$GREP" ]; then
            SESSION=$(screen -ls | grep -o ".*.visorgen-backend-service")
            if [ "$SESSION" ]; then
                screen -X -S $SESSION quit
            fi
        fi
        pkill -9 -f 'python legacy_serve.py'

        # stop image downloader tool

        GREP=$(ps -fe | grep ".*[i]mg_downloader")
        if [ "$GREP" ]; then
            SESSION=$(screen -ls | grep -o ".*.visorgen-img_downloader")
            if [ "$SESSION" ]; then
                screen -X -S $SESSION quit
            fi
        fi
        pkill -9 -f 'imsearch'
    ;;
    faces)
        ## Stop the faces engine ##

        # stop faces backend

        GREP=$(ps -fe | grep ".*[v]isorgen-faces-backend-service.*")
        if [ "$GREP" ]; then
            SESSION=$(screen -ls | grep -o ".*.visorgen-faces-backend-service")
            if [ "$SESSION" ]; then
                screen -X -S $SESSION quit
            fi
        fi
        pkill -9 -f 'python backend.py'

        # stop image downloader tool

        GREP=$(ps -fe | grep ".*[i]mg_downloader")
        if [ "$GREP" ]; then
            SESSION=$(screen -ls | grep -o ".*.visorgen-img_downloader")
            if [ "$SESSION" ]; then
                screen -X -S $SESSION quit
            fi
        fi
        pkill -9 -f 'imsearch'
    ;;
    *)
        echo "Usage: ${0} {text|cpuvisor-srv|faces}" >&2
    ;;
esac

exit 0
