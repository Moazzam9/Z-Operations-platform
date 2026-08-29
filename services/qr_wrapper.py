import os
import io
import pymupdf as fitz
import qrcode
from PIL import Image
from tqdm import tqdm

def generate_qr_code_image(data, size_pixels=150):
    """Generate QR code as PIL Image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size_pixels, size_pixels), Image.Resampling.LANCZOS)
    return img

def overlay_qr_on_pdf(pdf_path, qr_img, output_path, x, y, width_pt):
    """
    Overlay QR code on first page of PDF at (x, y) with given width in points.
    QR keeps aspect ratio (square).
    """
    doc = fitz.open(pdf_path)
    page = doc[0]

    height_pt = width_pt  # square
    qr_rect = fitz.Rect(x, y, x + width_pt, y + height_pt)

    img_bytes = io.BytesIO()
    qr_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    page.insert_image(qr_rect, stream=img_bytes.getvalue())
    doc.save(output_path)
    doc.close()

def process_certificates_batch(pdf_files, ids, output_dir, qr_x=400, qr_width=70, bottom_margin=60, progress_callback=None):
    """
    pdf_files: dict mapping lowercase filename to full path
    ids: list of certificate IDs
    output_dir: directory to save processed PDFs
    """
    sample_pdf = None
    for f in pdf_files.values():
        sample_pdf = f
        break
    
    if not sample_pdf:
        raise ValueError("No PDF found in the ZIP.")
        
    sample_doc = fitz.open(sample_pdf)
    page_height = sample_doc[0].rect.height
    sample_doc.close()

    # Compute Y coordinate using bottom margin
    qr_y = page_height - qr_width - bottom_margin
    
    success_count = 0
    failed_ids = []
    
    total = len(ids)
    
    for idx, cert_id in enumerate(ids):
        expected = f"{cert_id}.pdf".lower()
        pdf_path = pdf_files.get(expected)
        
        if not pdf_path:
            failed_ids.append(f"{cert_id} (PDF not found: {expected})")
        else:
            qr_url = f"https://www.zynvexcert.live/verify/{cert_id}"
            qr_img = generate_qr_code_image(qr_url, size_pixels=150)
            
            out_pdf = os.path.join(output_dir, f"{cert_id}.pdf")
            try:
                overlay_qr_on_pdf(pdf_path, qr_img, out_pdf, x=qr_x, y=qr_y, width_pt=qr_width)
                success_count += 1
            except Exception as e:
                failed_ids.append(f"{cert_id} (error: {str(e)})")
                
        if progress_callback:
            progress_callback(idx + 1, total)
            
    return success_count, failed_ids, page_height, qr_y
