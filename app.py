import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from PyPDF2 import PdfMerger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
import base64
from pdf2image import convert_from_path
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image
import streamlit as st
import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import Color
import re


st.set_page_config(layout="wide")
st.subheader("Nirmal Sahyog Poster Generator")

if 'generated' not in st.session_state:
    st.session_state.generated = False

if 'show_controls' not in st.session_state:
    st.session_state.show_controls = False

if 'y1' not in st.session_state:
  st.session_state.y1 = 208

if 'y2' not in st.session_state:
  st.session_state.y2 = 88

if 'date_font_size' not in st.session_state:
  st.session_state.date_font_size = 25

if 'name_font_size' not in st.session_state:
  st.session_state.name_font_size = 52


#Name input
raw_name = st.text_area("Name of sahyogi", height=68).strip().title()   

def clean_text(text):
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Strip each line and remove excess spaces
    lines = [line.strip() for line in text.strip().split('\n')]
    return '\n'.join(lines).title()

name = clean_text(raw_name)

#Date input
today = datetime.date.today()
days_until_sunday = (6 - today.weekday()) % 7
default_sunday = today + datetime.timedelta(days=days_until_sunday)
date = st.date_input("Date", value=default_sunday).strftime("%d/%m/%Y")

pdfmetrics.registerFont(TTFont('Eczar-SemiBold', "Eczar-SemiBold.ttf"))

def get_ideal_font_size_and_height(text):
    font_size = 25
    lines = text.splitlines()
    # Width of widest line (in points)
    widths = [pdfmetrics.stringWidth(line, 'Eczar-SemiBold', font_size) for line in lines]
    max_width_pt = max(widths)

    # Estimate line height (you can adjust the 1 factor for leading)
    line_height_pt = font_size * 1.0
    total_height_pt = line_height_pt * len(lines)

    actual_width = max_width_pt
    actual_height = total_height_pt

    safe_area_width, safe_area_height = 700, 100
    #width, height
    dim_option1 = (safe_area_width, safe_area_width*actual_height/actual_width) 
    dim_option2 = (safe_area_height*actual_width/actual_height, safe_area_height)

    if(dim_option1[0] <= safe_area_width and dim_option1[1] <= safe_area_height):
      ideal_width = dim_option1[0]
      ideal_height = dim_option1[1]
    else:
      ideal_width = dim_option2[0]
      ideal_height = dim_option2[1]
    
    ideal_font_size = min(ideal_height/len(lines), 70)
    bb_height = ideal_font_size * len(lines)
    if(len(lines) == 1): 
       ideal_font_height = 112-bb_height/2 + ideal_font_size*(len(lines)-1)
    else:
       ideal_font_height = 100-bb_height/2 + ideal_font_size*(len(lines)-1)

    return ideal_font_size, ideal_font_height



if not st.session_state.show_controls:

  y1= 208
  date_font_size = 25
  y2 = 88
  st.session_state.name_font_size = get_ideal_font_size_and_height(name)[0]
  st.session_state.y2 = get_ideal_font_size_and_height(name)[1]
  # st.session_state.y2 = 0




button = st.button("Generate Poster", type="primary")
# ——— Draw when inputs provided ———
if name and date and (button or st.session_state.generated):
    st.session_state.generated = True
    #text to overlay
    date_color = "#373737"
    name_color = "#961717"

    # Variables
    input_pdf = "template.pdf"
    output1_pdf = "output1.pdf"
    output2_pdf = "output2.pdf"

    font_path = "Eczar-SemiBold.ttf"  # Must be a valid TTF file

    overlay1_pdf = "overlay1.pdf"
    overlay2_pdf = "overlay2.pdf"

    def gen_overlay_pdf(overlay_pdf, text, font_size, color, y, angle=90):
        c = canvas.Canvas(overlay_pdf, pagesize=A4)
        c.setFont("CustomFont", font_size)
        c.setFillColor(HexColor(color))

        # Save current graphics state
        c.saveState()

        # Move origin to (y, half-page + 8)
        c.translate(y, A4[1]/2 + 8)

        # Rotate clockwise by angle degrees
        c.rotate(-angle)

        # ——— Draw multiline text ———
        lines = text.splitlines()
        line_height = font_size * 1  # adjust spacing if needed

        for i, line in enumerate(lines):
            # each subsequent line goes down by line_height
            c.drawCentredString(0, -i * line_height, line)

        # Restore original graphics state
        c.restoreState()
        c.save()

    def gen_overlay_dot_pdf(overlay_pdf_path, x, y, radius=3, color=Color(1, 0, 0)):
      """
      Create an A4‐sized PDF with just one filled circle (dot) at (x,y).

      Args:
          overlay_pdf_path (str): where to write the one‐page overlay
          x (float): PDF‐point X coordinate (origin bottom‐left)
          y (float): PDF‐point Y coordinate
          radius (float): circle radius in points
          color (reportlab.lib.colors.Color): fill color
      """
      c = canvas.Canvas(overlay_pdf_path, pagesize=A4)
      c.setFillColor(color)
      c.circle(x, y, radius, fill=1, stroke=0)
      c.save()


    def gen_output_pdf(input_pdf, overlay_pdf, output_pdf):
        reader_original = PdfReader(input_pdf)
        reader_overlay = PdfReader(overlay_pdf)
        writer = PdfWriter()

        for original_page, overlay_page in zip(reader_original.pages, reader_overlay.pages):
            original_page.merge_page(overlay_page)
            writer.add_page(original_page)

        with open(output_pdf, "wb") as f_out:
            writer.write(f_out)

        print("Done. Output saved as:", output_pdf)

    pdfmetrics.registerFont(TTFont("CustomFont", font_path))

    gen_overlay_pdf(overlay1_pdf, str(date), st.session_state.date_font_size, date_color, st.session_state.y1)
    gen_overlay_pdf(overlay2_pdf, name, st.session_state.name_font_size, name_color, st.session_state.y2)

    gen_output_pdf(input_pdf, overlay1_pdf, output1_pdf)
    gen_output_pdf(output1_pdf, overlay2_pdf, output2_pdf)    

    # NOW draw a dot:
    overlay_dot_pdf = "overlay_dot.pdf"
    # e.g. place a red dot at x=100, y=200, radius=5pt
    from reportlab.lib.colors import red
    gen_overlay_dot_pdf(overlay_dot_pdf, x=28, y=40, radius=5, color=red)


    # '''
    # x = 28, 817 bottom left corner
    # x = 28, 40 bottom right corner
    # x = 160, 817 top left corner
    # x = 160, 40 top right corner
    # ''' 
    # merge the dot into your final PDF
    final_output = "output2.pdf"
    gen_output_pdf(output2_pdf, overlay_dot_pdf, final_output)    
    
    # Load PDF and convert first page to image
    doc = fitz.open("output2.pdf")
    page = doc.load_page(0)  # Page 0 is the first page
    pix = page.get_pixmap(dpi=200)

    # Convert to PIL Image
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Show in Streamlit
    buf = BytesIO()
    image.save(buf, format="PNG")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(buf, use_container_width=True)



    with open("output2.pdf", "rb") as f:
        pdf_bytes = f.read()

    st.download_button(
        label="📥 Download Poster PDF",
        data=pdf_bytes,
        file_name="nirmal_sahyog_poster.pdf",
        mime="application/pdf"
    )

    # if st.checkbox("Show Controls"):
    #     st.session_state.show_controls = True
    # else:
    #     st.session_state.show_controls = False
    
    if st.session_state.show_controls:

      col1, col2 = st.columns([2, 2])
      with col1:
        st.session_state.y2 = st.slider(
          "Name vertical position", 
          min_value=0, 
          max_value=int(A4[1]), 
          value=88
        )
        st.session_state.name_font_size = st.slider(
            "Name font size", 
            min_value=0, 
            max_value=100, 
            value=52
        )
        
      with col2:
        st.session_state.y1 = st.slider(
            "Date vertical position", 
            min_value=0, 
            max_value=int(A4[1]), 
            value=208
        )
        st.session_state.date_font_size = st.slider(
            "Date font size", 
            min_value=0, 
            max_value=100, 
            value=25
        )
      
