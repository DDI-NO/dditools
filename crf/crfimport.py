
import streamlit as st
from st_pages import add_page_title
from utilities.login_form import *
from utilities.xnat import *
from crf.crfgui import *

from crf.loaders import CRFLoader, InvalidVersionException, CheckingErrorException
from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol
import subprocess
import shutil
from pathlib import Path

import PyPDF2
import logging
from ddidb import DB
from crf.crfsplit import split_crf

# Create a logger for this module
logger = logging.getLogger(__name__)

# Configure the logger
# Check if logger already has handlers (prevents adding multiple handlers)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('logs/crf.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def count_pdf_pages(pdf_file):
    """Counts the number of pages in a PDF file"""
    with open(pdf_file, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        return len(pdf_reader.pages)

def create_working_directory(uploaded_file):
    """creates the working directory for the CRF, using the name of the file"""
    basename = Path(uploaded_file.name).stem
    working_directory = os.path.join(os.getcwd(), "tmp", basename)
    if not os.path.exists(working_directory):
        os.makedirs(working_directory)
    return working_directory

def copy_sdaps_project(crf_version, target_directory):
    """Copies the directory structure of the SDAPS project matching the CRF version to the target directory"""
    sdaps_project = os.path.join(os.getcwd(), f"crf/sdaps_projects/{crf_version}")
    if not os.path.exists(sdaps_project):
        raise ValueError(f'Version {crf_version} is not compatible')
    # copy the sdaps_project to the target directory using the name sdaps
    if not os.path.exists(os.path.join(target_directory, "sdaps")):
        shutil.copytree(sdaps_project, os.path.join(target_directory, "sdaps"))


def prepare_sdaps_input(uploaded_file, working_directory):
    """Gets the number of pages of working_directory/sdaps/questionnaire.pdf and copies the same amount of pages from uploaded_file to the working directory as sdaps_input.tiff"""
    # find the number of pages of the questionnaire
    questionnaire = os.path.join(working_directory, "sdaps/questionnaire.pdf")
    target_pages = count_pdf_pages(questionnaire)
    input_file = os.path.join(working_directory, "sdaps_input.tiff")
    # copies the same amount of pages from uploaded_file to the working directory as sdaps_input.tiff
    with Image.open(uploaded_file) as tiff_image:
        # copy the first target_pages pages to sdaps_input.tiff
        pages = []
        for page_number in range(target_pages):
            tiff_image.seek(page_number)
            pages.append(tiff_image.copy())
        pages[0].save(input_file, save_all=True, append_images=pages[1:])
    return input_file

def sdaps_add(working_directory):
    add_cmd = ['sdaps', 
                'add', 
                f'{working_directory}/sdaps', 
                f'{working_directory}/sdaps_input.tiff'
                ]
    # logger.debug('<CMD> %s', add_cmd)
    current_subprocess = subprocess.run(
        add_cmd,  stdout=subprocess.PIPE, check=True,
    )
    output = current_subprocess.stdout.decode('utf-8')
    # st.write(output)
    if 'error' in output or 'Invalid input' in output:
        # raise a subprocess.CalledProcessError
        raise subprocess.CalledProcessError(1, add_cmd, output=output)
    
def sdaps_recognize(working_directory):
    recog_cmd = f'sdaps recognize {working_directory}/sdaps'.split(' ')
    # logger.debug('<CMD> %s', recog_cmd)
    current_subprocess = subprocess.run(
        recog_cmd,  stdout=subprocess.PIPE, check=True,
    )
    output = current_subprocess.stdout.decode('utf-8')
    st.write(output)

def sdaps_export(working_directory):
    output = f'{working_directory}/sdaps/data.csv'
    export_cmd = f'sdaps export csv -o {output} {working_directory}/sdaps'.split(' ')
    # logger.debug('<CMD> %s', export_cmd)
    current_subprocess = subprocess.run(
        export_cmd,  stdout=subprocess.PIPE, check=True,
    )
    output = current_subprocess.stdout.decode('utf-8')
    st.write(output)

def find_crf_version(uploaded_file):
    crf_version = None
    with Image.open(uploaded_file) as tiff_image:
        tiff_image.seek(0)

        # Decode the QR code
        data = decode(tiff_image, symbols=[ZBarSymbol.QRCODE])
        if len(data) > 0:
            # get the data wich rec is most to the left
            data = sorted(data, key=lambda x: x.rect.left)
            # Print the decoded data
            current_code = data[0].data.decode('utf-8')
            if current_code.startswith('OMR'): #OMRCRFvx.x.x
                crf_version = current_code.split('v')[1]
    return crf_version

def upload_subject(project, subject_label, xnat_subject, xnat_dem, ddi_dem, progress_bar):
    write = True
    
    if not xnat_subject.exists():
        progress_bar.progress(1, text=f'Creating subject {subject_label}')
        # logger.debug('creating %s', subject_label)
        xnat_subject.create()
        # self.upload_scan(xnat_subject, self.manager.input_file)
        
    # else:
    #     write = self.view.ask_overwrite(f'{subject_label} already exists, do you want to overwrite DEMOGRAFIC data?')
    
    # if write:
    logger.debug('setting base demographics')
    progress_bar.progress(1, text=f'Setting base demographics')
    xnat_subject.attrs.mset(xnat_dem)

    progress_bar.progress(1, text=f'Creating demographics experiment')
    label = '_'.join([subject_label, 'dem'])
    
    with DB() as db:
        datatype = 'dem:ddiDemographicData'
        logger.debug('searching experiment %s %s %s', datatype, subject_label, project)
        xnat_exp = db.find_experiment(datatype, subject_label, project=project)
        logger.debug('database result %s', xnat_exp)
        if not xnat_exp:
            xnat_exp = label
        
        ddi_exp = xnat_subject.experiment(label)
        if not ddi_exp.exists():
            logger.debug('creating %s', label)
            ddi_exp.create(experiments=datatype)
        
        progress_bar.progress(1, text=f'Setting data')
        logger.debug('setting data for %s', label)
        ddi_exp.attrs.mset(ddi_dem)

def upload_experiment(db, project, subject, visit_date, visit, xnat_subject, experiment_info, experiment_data, progress_bar, n_steps, progress):
    experiment_prefix = experiment_info['prefix']
    datatype = experiment_info['xml_name']
    exp_title = experiment_info['title']
    
    # MDS is a special case for PD patients, if it is all NULL, skip it
    if datatype == 'mds:MDSData':
        # check if all values in experiment_data are 'NULL'
        if all([v == 'NULL' for v in experiment_data['mds']['data'].values()]):
            return
    
    label = f'{subject}_{experiment_prefix}_{visit_date}_{visit}'
    # cover experiments have a different label pattern
    if datatype == 'cover:CoverData':
        label = f'{subject}_{experiment_prefix}'
        visit = ''
    logging.debug('searching experiment %s %s %s %s', datatype, subject, visit, project)
    xnat_exp = db.find_experiment(datatype, subject, visit=visit, project=project)
    logging.debug('database result %s', xnat_exp)
            
    
    write = True
    if not xnat_exp:
        progress_bar.progress(progress, text=f'Creating {label}')
        experiment = xnat_subject.experiment(label)
        logging.debug('creating %s', label)
        experiment.insert(**{
            'experiments' : datatype, 
            'date' : visit_date,
            'label' : label, 
            'visit_id' : visit
            })
        
    else:
        # write = self.view.ask_overwrite(f'{exp_title} already exists ({label}).\n do you want to overwrite the data?')
        experiment = xnat_subject.experiment(xnat_exp)
    
    if write:
        #print(experiment_data)
        # vars = len(experiment_data)
        # i = 0
        # for k,v in experiment_data.items():
        #     i += 1
        #     self.upload_msg.set_msg(datatype, f'Setting vars {i}/{vars}')
        #     experiment.attrs.set(k, v)    
        
        for section, section_conf in experiment_data.items():
            title = section_conf['title']
            xnat_data = section_conf['data']
            progress_bar.progress(progress/n_steps, text=f'Setting {exp_title} {title}')
            logging.debug('setting data for %s', label)
            experiment.attrs.mset(xnat_data)
            progress += 1
    return progress    

def upload_experiments(loader, project, subject, visit_date, visit_number, crf_experiments, xnat_subject, progress_bar, n_steps):
    with DB() as db:
        progress = 1
        for key, experiment_info in crf_experiments.items():
            try:
                experiment_data = loader.get_data(key)
                progress = upload_experiment(db, project, subject, visit_date, visit_number, xnat_subject, experiment_info, experiment_data, progress_bar, n_steps, progress)
                
                
            except KeyError as e:
                logging.error('Error getting %s in %s', key, experiment_info['xml_name'])
                raise e
        progress_bar.progress(1, text=f'Finished importing data')


def import_data(crf_version, working_directory, project, subject, visit_date, visit_number, progress_bar):
    csv_data = f'{working_directory}/sdaps/data.csv'
    loader = CRFLoader.get_loader(crf_version, csv_data) # type: ignore
    xnat = get_xnat(st.session_state['username'], st.session_state['password'])
    # get subject data and experiments
    xnat_dem, ddi_dem = loader.get_subjectdata()
    exps = loader.get_configured_experiments()

    # the number of steps to show progress. 
    # 1 for base and DDI demographics + the number of configured experiment sections
    n_steps = 1 
    for exp in exps:
        n_steps += len(exp['sections'])
    xnat_subject = xnat.select.project(project).subject(subject)
    progress_bar.progress(0, text='Creating subject')
    upload_subject(project, subject, xnat_subject, xnat_dem, ddi_dem, progress_bar)
    progress_bar.progress(1/n_steps, text='Subject created')

    upload_experiments(loader, project, subject, visit_date, visit_number, exps, xnat_subject, progress_bar, n_steps)
    

def load_crf(uploaded_file, project, subject, visit_date, visit_number):
    crf_version = find_crf_version(uploaded_file)
    if crf_version:
        try:
            working_directory = create_working_directory(uploaded_file)
            copy_sdaps_project(crf_version, working_directory)
            prepare_sdaps_input(uploaded_file, working_directory)
            with st.status("Running mark recognition...", expanded=True) as status:
                st.write("Adding scan...")
                sdaps_add(working_directory)
                st.write("Recognizing scan...")
                sdaps_recognize(working_directory)
                st.write("Preparing recognized data...")
                sdaps_export(working_directory)
                status.update(label="Recognition complete!", state="complete", expanded=False)


            progress_bar = st.progress(0, text='Importing data...')
            import_data(crf_version, working_directory, project, subject, visit_date, visit_number, progress_bar)
            progress_bar.progress(0, text='Preparing CRF documents...')
            docs_directory = os.path.join(working_directory, "docs")
            split_crf(uploaded_file, project, subject, visit_date, visit_number, progress_bar=progress_bar, output_folder=docs_directory)
            
        except Exception as e:
            st.error(f"Error importing CRF: {e}")
            logger.exception(e)
            return
        finally:
            if os.path.exists(working_directory):
                shutil.rmtree(working_directory)
        
    else:
        st.error("Could not find a valid CRF version. Check that the QR code is present and readable.")
        return


def load_ui():
    st.write("Upload a scanned CRF document to run the optical mark recognition, \
             import the recognized data into XNAT, and split by detected QR codes and upload the resulting documents.")
    username, password = xnat_login()
    if username and password:
        credentials_valid = check_credentials(username, password)
        if credentials_valid:
            st.session_state['username'] = username
            st.session_state['password'] = password
            projects = get_projects(username, password)
            crf_ui(projects, load_crf, check_subject=False)

add_page_title()
load_ui()