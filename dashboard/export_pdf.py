from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import os
import streamlit as st
from PIL import Image
from datetime import datetime

def save_plotly_to_buffer(fig):
    from plotly.io import to_image
    try:
        img_data = to_image(fig, format="png", width=1000, height=800)
        return BytesIO(img_data)
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None
def generate_pdf(figures, filters):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setTitle(f"WAAS Event Report - {datetime.now().strftime('%A, %d %B %Y')}")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, f"WAAS Event Report - {datetime.now().strftime('%A, %d %B %Y')}")
    c.setFont("Helvetica", 8)
    c.drawString(100, 730, "Filter Applied:")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(100, 720, f"Attack Type: {', '.join(attack for attack in filters['Attack Type']) if isinstance(filters['Attack Type'], list) else filters['Attack Type']}")
    c.drawString(100, 710, f"Namespace: {', '.join(ns for ns in filters['Namespace']) if isinstance(filters['Namespace'], list) else filters['Namespace']}")
    c.drawString(100, 700, f"Host: {', '.join(host for host in filters['Host']) if isinstance(filters['Host'], list) else filters['Host']}")
    c.drawString(100, 690, f"Path: {', '.join(path for path in filters['Path']) if isinstance(filters['Path'], list) else filters['Path']}")

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