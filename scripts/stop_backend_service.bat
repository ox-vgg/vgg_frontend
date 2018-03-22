@echo off
if "%~1"=="text"         ( goto CASE_text )
if "%~1"=="cpuvisor-srv" ( goto CASE_cpuvisor-srv )
if "%~1"=="faces"        ( goto CASE_faces )
if "%~1"=="instances"    ( goto CASE_instances )
echo Usage: %0 {text^|cpuvisor-srv^|faces^|instances}
exit /B

:CASE_text
    echo Text search engine not yet supported in Windows
    exit /B
:CASE_cpuvisor-srv
    echo Category search engine not yet supported in Windows
    exit /B
:CASE_faces
    taskkill /FI "WINDOWTITLE eq vgg_img_downloader*" /F /T
    taskkill /FI "WINDOWTITLE eq vgg_face_search_service*" /F /T
    exit /B
:CASE_instances
    echo Instances search engine not yet supported in Windows
    exit /B
