# crf/crfsplitui.py
import streamlit as st
from PIL import Image
from utilities.xnat import *


def load_crf(crf_file, project, subject, visit_date, visit_number, process_callback: callable):
    with Image.open(crf_file) as im:
        page_count = im.n_frames

        col1, col2 = st.columns([0.4, 0.6])
        with col2:
            st.write(f"Number of pages: {page_count}")
            # add streamlit process button
            process_button = st.button("Process")
            if process_button:
                process_callback(crf_file, project, subject, visit_date, visit_number)
        with col1:
            # display the first image
            im.seek(0)
            st.image(im, use_column_width=True)

def crf_ui(projects, process_callback: callable, check_subject=True):
    st.subheader("CRF")
    col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.22, 0.38])
    project = col1.selectbox("Project", projects)
    subject = col2.text_input("Subject")
    visit_date = col3.date_input("Visit date", value=None)
    visit = col4.selectbox('Assessment visit', VISITS.keys(), index=2)
    visit_number = VISITS[visit]

    if project and subject and visit_date and visit_number:
        visit_date = visit_date.strftime("%Y%m%d")
        subject_exists_check = True
        if check_subject:
            subject_exists_check = subject_exists(st.session_state['username'], st.session_state['password'], project, subject)
        if subject_exists_check:
            uploaded_file = st.file_uploader("CRF Scan", type=["tiff", "tif"])
            if uploaded_file is not None:
                load_crf(uploaded_file, project, subject, visit_date, visit_number, process_callback)
        else:
            st.error(f"Subject {subject} does not exist in project {project}.")

