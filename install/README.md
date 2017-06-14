vgg_frontend Installers
=======================

These installers are experimental. Please use caution when using them and read this README until the end before attempting the installation.

Ubuntu 14 LTS
-------------

 1. This script is to be run in a clean Ubuntu 14.04 LTS machine, by a sudoer user.
 2. Caffe is compiled for CPU use only.
 3. Use `install_ubuntu.sh` to install `vgg_frontend`. The application will be installed in `/webapps/visorgen/`
 4. If you plan to use the CATEGORY search engine, use `install_vgg_classifier_ubuntu.sh` to install it. It will be installed in the `/webapps/visorgen/vgg_classifier` folder.
 5. If you plan to use the TEXT search engine, use `install_text-backend_ubuntu.sh` to install it. It will be installed in the `/webapps/visorgen/text_search` folder. **Please NOTE that this repository is not open-source yet !, so only an authorized user will be able to access it. Please contact us for more information.**
 6. Remember that before the first use you need to configure the search engines. See <https://gitlab.com/vgg/vgg_classifier> and <https://gitlab.com/vgg/text_search>.

macOS Sierra v10.12.3
---------------------

 1. These scripts are VERY EXPERIMENTAL. Please be careful. Instead of running the full script, you might want to open it in a text editor and run one instruction at a time.
 2. The scripts assume Homebrew is available in the system (https://brew.sh/).
 3. The scripts assume GIT is installed (https://sourceforge.net/projects/git-osx-installer/files/).
 4. Make sure you have enough user privileges to install software using HomeBrew.
 5. Caffe is compiled for CPU use only.
 6. Use `install_macos.sh` to install `vgg_frontend`. The application will be installed in `$HOME/visorgen`
 7. Use `install_vgg_classifier_macos.sh` to install the CATEGORY search engine. It will be installed in the `$HOME/visorgen/vgg_classifier` folder.
 8. Unfortunately we are unable to provide at the moment an installer for the TEXT search engine. See <https://gitlab.com/vgg/text_search> for the source code.
 9. Remember that before the first use you need to configure the search engines. See <https://gitlab.com/vgg/vgg_classifier> and <https://gitlab.com/vgg/text_search>.
