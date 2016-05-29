###############################################################
# Utility functions
###############################################################

import os

def get_project_full_path():
    ''' Return the full path of the project, for navigating directories.'''
    projectDirectory = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
    return projectDirectory
