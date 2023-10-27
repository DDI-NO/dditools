# crf/crfsplitui.py
import streamlit as st
from st_pages import add_page_title
from utilities.login_form import *
from utilities.xnat import check_credentials

from crf.crfgui import *
from crf.crfsplit import split_crf

add_page_title()

def load_ui():
    st.write("Upload a scanned CRF document to split by detected QR codes and upload the resulting documents to XNAT.")
    username, password = xnat_login()
    if username and password:
        credentials_valid = check_credentials(username, password)
        if credentials_valid:
            st.session_state['username'] = username
            st.session_state['password'] = password
            projects = get_projects(username, password)
            crf_ui(projects, split_crf)


load_ui()