# utilities/login_form.py

import streamlit as st
from utilities.xnat import check_credentials

def xnat_login(info=False):
    st.subheader("XNAT Credentials")
    if info:
        st.info('This tool needs your XNAT credentials, please enter them bellow', icon="ℹ️")
    # two cols for the text inputs
    col1, col2 = st.columns(2)

    username = col1.text_input("Username")
    password = col2.text_input("Password", type="password")

    return username, password
    

def xnat_login_with_credentials(callback: callable):
    username, password = xnat_login()
    if username and password:
        credentials_valid = check_credentials(username, password)
        if credentials_valid:
            st.session_state['username'] = username
            st.session_state['password'] = password
            st.write(f"ww {credentials_valid}")
            callback()
        else:
            st.error("Invalid credentials")
