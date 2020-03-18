import os
import sys
from django.conf import settings

# add 'views' to the path so that we can import stuff from it
sys.path.append(os.path.join(settings.BASE_DIR, 'visor', 'views'))

# imports from 'views'
from views.user import UserPages
from views.admin import AdminPages
from views.api import APIFunctions

# add 'controllers' to the path so that we can import stuff from it
sys.path.append(os.path.join(settings.BASE_DIR, 'visor', 'controllers'))

# imports from 'controllers'
from controller import VisorController

# Global variables to access API and views
api_functions = None
user_pages = None
admin_pages = None

def visor_static_init():
    """
        Static function to load main variables once.
        It changes its own code after the first execution.
    """
    global api_functions
    global user_pages
    global admin_pages
    if api_functions == None:
        visor_controller = VisorController()
        print ('Creating base controller ', visor_controller)
        api_functions = APIFunctions(visor_controller)
        user_pages = UserPages(visor_controller)
        admin_pages = AdminPages(visor_controller)
    visor_static_init.__code__ = (lambda: None).__code__

# Initialize, just once
visor_static_init()
