from st_pages import show_pages_from_config, add_page_title
import streamlit as st

show_pages_from_config(".streamlit/pages_sections.toml")
add_page_title()
st.write("Select a tool from the sidebar to begin.")