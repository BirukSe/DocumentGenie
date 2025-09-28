from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_test_pdf():
    # Create a test PDF
    output_path = "test_document.pdf"
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add some sample content
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 100, "This is a test PDF document.")
    c.drawString(100, height - 120, "We'll use this to test background color changes.")
    
    # Save the PDF
    c.save()
    print(f"Test PDF created at: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

if __name__ == "__main__":
    pdf_path = create_test_pdf()
    print(f"You can now test the background color change with:")
    print(f"python3 test_background_color.py {pdf_path}")
