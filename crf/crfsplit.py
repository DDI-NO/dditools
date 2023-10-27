# crf/crfsplit.py
from PIL import Image
from reportlab.pdfgen import canvas
from pyzbar.pyzbar import decode, ZBarSymbol
import os
import streamlit as st

from utilities.xnat import get_xnat, get_subject_link

from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from io import BytesIO

from glob import glob

def upload_to_xnat(filepath, project, subject, visit_number, progress_bar):
    username = st.session_state['username']
    password = st.session_state['password']
    xnat = get_xnat(username, password)
    try:                
        xnat_project = xnat.select.project(project)
        xnat_subject = xnat_project.subject(subject)

        # get all PDFs in filepath
        docs = glob(os.path.join(filepath, '*.pdf'))
        n_docs = len(docs)
        for i, pdf in enumerate(docs):
            basename = os.path.basename(pdf)
            progress_bar.progress((i)/n_docs, text=f"Uploading {basename}")
            destination = f'{visit_number}/{basename}'
            r = xnat_subject.resource('SCANNED_DOCS').file(destination)
            r.insert(
                pdf,
                format='PDF',
                tags='CRF'
            )
            progress_bar.progress((i+1)/n_docs, text=f"Uploading {basename}")    
        
        subject_link = get_subject_link(subject, project=project)
        st.success(f"Upload complete. You can [inspect the uploaded files in XNAT]({subject_link}).")
    except Exception as e:
        st.exception(e)
    finally:
        xnat.disconnect()

    

def images_to_pdf(image_pages, pdf_path, progress_bar, progress_text):
    pdf = canvas.Canvas(pdf_path)

    # A4 dimensions in points
    a4_width, a4_height = A4
    n_pages = len(image_pages)
    for i, img in enumerate(image_pages):
        # Convert the image to RGB (remove alpha channel if it exists)
        rgb_im = img.convert("RGB")

        # Convert to bytestream
        img_data = BytesIO()
        rgb_im.save(img_data, format='JPEG', quality=85)

        # Get image dimensions
        img_width, img_height = rgb_im.size

        # Calculate scale factors
        width_scale = a4_width / img_width
        height_scale = a4_height / img_height
        scale = min(width_scale, height_scale)

        # Calculate scaled dimensions
        scaled_width = img_width * scale
        scaled_height = img_height * scale

        # Draw the image on the PDF using the bytestream, scaled to A4
        pdf.drawImage(ImageReader(img_data), 0, 0, width=scaled_width, height=scaled_height)


        # Add a new page for the next image
        pdf.showPage()

        progress_bar.progress((i+1)/n_pages, text=progress_text)

    # Save the PDF
    pdf.save()

def split_crf(crf_file, project, subject, visit_date, visit_number, output_folder=None, progress_bar=None):

    if not output_folder:
        output_folder = os.path.join(os.getcwd(), "tmp", f'{subject}_{visit_number}')

    if not os.path.exists(output_folder):
        # mkdir -p
        os.makedirs(output_folder)
    else:
        # remove directires and files
        for f in os.listdir(output_folder):
            os.remove(os.path.join(output_folder, f))

    with Image.open(crf_file) as tiff_image:
        # get the page count
        page_count = tiff_image.n_frames
        page_number = 0
        sub_docs = {}
        current_code = None

        if not progress_bar:
            progress_bar = st.progress(0)
        for page_number in range(page_count):
            tiff_image.seek(page_number)
            # Decode the QR code
            data = decode(tiff_image, symbols=[ZBarSymbol.QRCODE])
            if len(data) > 0:
                # get the data wich rec is most to the left
                data = sorted(data, key=lambda x: x.rect.left)
                decoded_info = None
                # Print the decoded data
                current_code = data[0].data.decode('utf-8')
            
            if current_code:
                if current_code not in sub_docs:
                    sub_docs[current_code] = []
                sub_docs[current_code].append(tiff_image.copy())
            
            progress_text = f"Processing page {page_number+1}. Current tag: {current_code}"
            progress_bar.progress((page_number+1)/page_count, text=progress_text)
            
        progress_bar.progress(0, text='Converting to PDF...')

        for code, pages in sub_docs.items():
            progress_text = f"Converting {code} to PDF"

            output_filepath = os.path.join(output_folder, f"{subject}_{code}_{visit_number}.tiff")
            pdf_filepath = os.path.join(output_folder, f"{subject}_{code}_{visit_date}_{visit_number}.pdf")
            # pages[0].save(output_filepath, save_all=True, append_images=pages[1:])
            # Convert the image pages to PDF
            images_to_pdf(pages, pdf_filepath, progress_bar, progress_text)

    upload_to_xnat(output_folder, project, subject, visit_number, progress_bar)
    # remove the output_folder directory completly
    for f in os.listdir(output_folder):
        os.remove(os.path.join(output_folder, f))
    os.rmdir(output_folder)