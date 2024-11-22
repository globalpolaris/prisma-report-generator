from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os
import streamlit as st
from PIL import Image
from datetime import datetime
import plotly.graph_objs as go
from textwrap import wrap

def create_cover(pdf, subtitle, date):
    width, height = letter
    img_width, img_height = 3*inch, 1*inch
    x = (width-img_width)/2
    y = height-img_height - 1 * inch
    # Add logo
    try:
        pdf.drawImage("./ntt.png", x,y, img_width, img_height, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"Error adding logo: {e}")
        
    text_height = 3*inch
    start_y = (height-text_height)/2
    # Add Title
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, start_y + 2*inch, "Event Report")
    
    # Add Subtitle
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, start_y + 1.5 * inch, subtitle)
    
    # Add Author or Other Details
    pdf.setFont("Helvetica-Oblique", 12)
    pdf.drawCentredString(width / 2, start_y + 1*inch, date)
    

def save_plotly_to_buffer(fig):
    from plotly.io import to_image
    try:
        img_data = to_image(fig, format="png", width=1000, height=800)
        return BytesIO(img_data)
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None
    
### UNUSED ###
# def wrap_text_to_fit(text, max_width=200):
#     """
#     Wrap the text to fit within the specified max width.
#     """
#     from reportlab.lib.pagesizes import letter
#     from reportlab.lib import colors
#     from reportlab.lib.styles import getSampleStyleSheet
#     lines = text.split('\n')

#     style = getSampleStyleSheet()['Normal']
#     style.fontName = 'Helvetica'
#     style.fontSize = 8
#     style.textColor = colors.black
#     style.leading = 10  # Set line spacing for each paragraph

#     # Create a list to hold Paragraph objects for each line of text
#     wrapped_text = []
#     for line in lines:
#         paragraph = Paragraph(line, style)
#         wrapped_text.append(paragraph)

#     return wrapped_text

# def draw_table_on_canvas(c, data, max_width, page_width):
#     table = Table(data, colWidths=[100, 100, 100, max_width - 300])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, -1), 8),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
#     ]))
#     table.wrapOn(c, page_width, 0)
#     table.drawOn(c, 50, 50)  # Adjust the x and y position for table

# def add_paginated_table(c, dataframe, page_width, page_height):
#     styles = getSampleStyleSheet()
#     header = ['Container', 'Image', 'Namespace', 'Message']
#     max_width = page_width - 100  # Adjust to fit landscape page margins
#     available_height = page_height - 100  # Top and bottom margins

#     # Table styling
#     table_style = TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, -1), 8),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
#     ])

#     current_page_data = [header]
#     current_page_height = 0

#     def split_message(message, max_chars=500):
#         """Splits a long message into chunks to fit across pages."""
#         return wrap(message, max_chars)

#     for _, row in dataframe.iterrows():
#         # Split the message into smaller parts
#         message_parts = split_message(row['Message'], max_chars=300)

#         for part in message_parts:
#             message_paragraph = Paragraph(part, styles['BodyText'])
#             container = wrap_text_to_fit(row["Container"])
#             image = wrap_text_to_fit(row["Image"])
#             namespace = wrap_text_to_fit(row["Namespace"])
#             message = wrap_text_to_fit(row["Message"])
#             cell_data = [container, image, namespace, message]
#             temp_table = Table([cell_data], colWidths=[100, 100, 100, max_width - 300])
#             temp_table.setStyle(table_style)

#             # Calculate height of the row
#             row_height = temp_table.wrap(0, available_height)[1]

#             # If adding this row exceeds the page height, save current page and start a new one
#             if current_page_height + row_height > available_height:
#                 draw_table_on_canvas(c, current_page_data, max_width, page_width)
#                 c.showPage()
#                 c.setPageSize(landscape(letter))
#                 current_page_data = [header]
#                 current_page_height = 0

#             current_page_data.append(cell_data)
#             current_page_height += row_height

#     # Add the last page
#     if current_page_data:
#         draw_table_on_canvas(c, current_page_data, max_width, page_width)

### UNUSED ###

def generate_pdf(figures, filters, event):
    print("Generating PDF...")
    buffer = BytesIO()
    date = datetime.now().strftime('%A, %d %B %Y')
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    if event.lower() == "waas":
        create_cover(c, "WAAS", date)
    elif event.lower() == "runtime":
        create_cover(c, "Runtime", date)
    else:
        st.error("Invalid event type")
        return None
    c.showPage()
    c.setTitle(f"{event} Event Report - {date}")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, f"{event} Event Report - {date}")
    c.setFont("Helvetica", 8)
    c.drawString(100, 730, "Filter Applied:")
    c.setFont("Helvetica-Bold", 8)
    filter_y = 720
    for _, value in enumerate(filters):
        # print(filters[value])
        c.drawString(100, filter_y, f"{value}: {', '.join(attack for attack in filters[value]) if isinstance(filters[value], list) else filters[value]}")
        filter_y -= 10
    
    y_pos = 650
    for i, fig in enumerate(figures):
        try:
            # Convert Plotly chart to image
            img_buffer = save_plotly_to_buffer(fig)
            if img_buffer:
                img_buffer.seek(0)
                # Open the image with PIL
                img = Image.open(img_buffer)
                # Save the image to a temporary file
                temp_image_path = f"temp_chart_{i}.png"
                img.save(temp_image_path)

                c.drawImage(temp_image_path, 100, y_pos - 300, width=400, height=300)
                y_pos -= 350  # Move below the image
                # Optional cleanup
                os.remove(temp_image_path)
                if y_pos < 100:
                    c.showPage()
                    y_pos = 750
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            return None

    c.save()
    buffer.seek(0)
    return buffer