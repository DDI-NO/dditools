from http.client import InvalidURL
from pyxnat import Interface
from pyxnat.core.errors import DatabaseError
import streamlit as st
import os
from config import config_manager

VISITS = {
    'Prior assessment': '0',
    'Prior extra assessment': '-101',
    'First assessment': '1',
    'Second assessment': '2',
    'Third assessment': '3',
    'Fourth assessment': '4',
    'Fifth assessment': '5',
    'Sixth assessment': '6',
    'Seventh assessment': '7',
    'Eighth assessment': '8',
    'Extra First assessment 1': '101',
    'Extra First assessment 2': '102',
    'Extra First assessment 3': '103',
    'Extra Second assessment 1': '201',
    'Extra Second assessment 2': '202',
    'Extra Second assessment 3': '203',
    'Extra Third assessment 1': '301',
    'Extra Third assessment 2': '302',
    'Extra Third assessment 3': '303',
    'Extra Fourth assessment 1': '401',
    'Extra Fourth assessment 2': '402',
    'Extra Fourth assessment 3': '403',
    'Extra Fifth assessment 1': '501',
    'Extra Fifth assessment 2': '502',
    'Extra Fifth assessment 3': '503',
    'Extra Sixth assessment 1': '601',
    'Extra Sixth assessment 2': '602',
    'Extra Sixth assessment 3': '603',
    'Other': '900'
    }

HOST = config_manager.get('XNAT', 'xnat_host')

def check_credentials(username, password):
    """Tries a connection to XNAT and returns True if successful, False otherwise."""
    try:
        host = f"http://{os.environ.get('XNAT_HOST')}/xnat"
        # host = os.environ.get('XNAT_HOST')
        # st.text(f'XNAT {host}')
        xnat = Interface(server=HOST, user=username, password=password)
        xnat.disconnect()
        return True
    
    except DatabaseError as e:
        st.error("Invalid credentials")
        return False
    except ConnectionError as e:
        st.error(f"Could not connect to XNAT, check it is up running.")
        return False
    except InvalidURL as e:
        st.error(f"Could not connect to XNAT, check it is up running.")
        return False
    except Exception as e:
        st.exception(e)
        return False

def get_xnat(username, password):
    host = f"http://{os.environ.get('XNAT_HOST')}/xnat"
    # host = os.environ.get('XNAT_HOST')
    xnat = Interface(server=HOST, user=username, password=password)
    return xnat

def subject_exists(username, password, project, subject_id):
    """Returns True if the subject exists in XNAT, False otherwise."""
    xnat = get_xnat(username, password)
    try:
        xnat.select.project(project).subject(subject_id).get()
        xnat.disconnect()
        return True
    except Exception as e:
        xnat.disconnect()
        return False
    
def get_external_xnat_address():
    host = config_manager.get('XNAT', 'external_xnat_host')
    return host

def get_subject_link(subject, project='apgem'):
    """Returns a link to the subject in XNAT."""
    host = get_external_xnat_address()
    return f"{host}/data/projects/{project}/subjects/{subject}"

def get_projects(username, password):
    """Returns a list of projects the user has access to."""
    xnat = get_xnat(username, password)
    projects = xnat.select.projects().get()
    xnat.disconnect()
    return projects

def get_experiments_by_type(username, password, project, subject, experiment_type):
    """Returns a list of experiments of the given type for the subject."""
    xnat = get_xnat(username, password)
    endpoint = f'data/projects/{project}/subjects/{subject}/experiments?xsiType={experiment_type}'
    experiments = xnat.get(endpoint).json()
    id_list = [record['ID'] for record in experiments['ResultSet']['Result']]
    xnat.disconnect()
    return experiments