import fitz
import os
import urllib.request
import shutil
import re

# Colors
TEXT_COLOR = (0x4a/255, 0x22/255, 0x78/255)   # #4a2278
WHITE = (1, 1, 1)

# Constants for layout from original script
PAGE_W, PAGE_H = 595.5, 842.25
LABEL_BOTTOM = 207.5

NAME_BOX = fitz.Rect(193.05, 190.94, 351.23, 236.51)
ID_BOX = fitz.Rect(351.41, 190.94, 560.65, 236.51)
NAME_VALUE = fitz.Rect(NAME_BOX.x0+2, LABEL_BOTTOM, NAME_BOX.x1-2, NAME_BOX.y1-2)
ID_VALUE = fitz.Rect(ID_BOX.x0+2,   LABEL_BOTTOM, ID_BOX.x1-2,   ID_BOX.y1-2)
DEAR_RECT = fitz.Rect(34, 248, 300, 272)
BODY_LINE1 = fitz.Rect(34, 278, 562, 296)

ROLE_LABELS = {
    "AI / Machine Learning": "AI / Machine Learning",
    "Full Stack Developer": "Full Stack Development",
    "Mern-Stack Developer": "Mern-Stack Development",
    "Web Development": "Web Development",
    "Frontend Developer": "Frontend Development",
    "Cybersecurity Analyst": "Cybersecurity",
    "Mobile App Developer": "Mobile App Development",
    "Data Science": "Data Science",
    "Digital Marketing Specialist": "Digital Marketing",
}

def get_first_name(n):
    return n.strip().split()[0]

def get_role_label(r):
    # Support both original role string and normalized role string
    r_clean = r.strip()
    return ROLE_LABELS.get(r_clean, r_clean)

def download_fonts_if_needed(fonts_dir):
    os.makedirs(fonts_dir, exist_ok=True)
    font_reg_path = os.path.join(fonts_dir, "Poppins-Regular.ttf")
    font_bold_path = os.path.join(fonts_dir, "Poppins-Bold.ttf")
    
    urls = {
        font_reg_path: "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
        font_bold_path: "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
    }
    
    for path, url in urls.items():
        if not os.path.exists(path):
            print(f"Downloading Poppins Font to {path}...")
            urllib.request.urlretrieve(url, path)
            
    return font_reg_path, font_bold_path

def make_clean_pixmap(template_path, dpi=200):
    doc = fitz.open(template_path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
    doc.close()
    sc = dpi / 72

    def blank(r, rgb):
        x0, y0 = max(0, int(r.x0*sc)), max(0, int(r.y0*sc))
        x1, y1 = min(pix.width, int(r.x1*sc)), min(pix.height, int(r.y1*sc))
        for py in range(y0, y1):
            for px in range(x0, x1):
                pix.set_pixel(px, py, rgb)

    blank(NAME_VALUE, (251, 245, 255))   # #fbf5ff for name background
    blank(ID_VALUE,   (251, 245, 255))   # #fbf5ff for ID background
    blank(DEAR_RECT,  (255, 255, 255))
    blank(BODY_LINE1, (255, 255, 255))
    return pix

def generate_offer_letter(clean_pix, font_reg, font_bold, intern_name, intern_role, intern_id, output_path):
    first_name = get_first_name(intern_name)
    role_label = get_role_label(intern_role)

    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    page.insert_image(fitz.Rect(0, 0, PAGE_W, PAGE_H), pixmap=clean_pix)

    page.insert_font(fontbuffer=font_reg.buffer,  fontname="PopR")
    page.insert_font(fontbuffer=font_bold.buffer, fontname="PopB")

    # NAME — auto-fit, wraps to 2 lines if needed
    max_w = NAME_VALUE.width - 8
    box_h = NAME_VALUE.height
    name_size = None
    for sz in range(11, 6, -1):
        if font_bold.text_length(intern_name, fontsize=sz) <= max_w:
            name_size = sz
            break

    if name_size:
        y = NAME_VALUE.y0 + (box_h + name_size) / 2 - 1
        page.insert_text((NAME_VALUE.x0+4, y), intern_name,
                         fontname="PopB", fontsize=name_size, color=TEXT_COLOR)
    else:
        words = intern_name.split()
        best = len(words) // 2
        for i in range(1, len(words)):
            if (font_bold.text_length(" ".join(words[:i]), fontsize=7) <= max_w and
                font_bold.text_length(" ".join(words[i:]), fontsize=7) <= max_w):
                best = i
                break
        sz = 7
        lh = sz * 1.4
        y1 = NAME_VALUE.y0 + (box_h - lh) / 2 + sz - 1
        page.insert_text((NAME_VALUE.x0+4, y1),    " ".join(words[:best]),
                         fontname="PopB", fontsize=sz, color=TEXT_COLOR)
        page.insert_text((NAME_VALUE.x0+4, y1+lh), " ".join(words[best:]),
                         fontname="PopB", fontsize=sz, color=TEXT_COLOR)

    # ID BADGE (background #fbf5ff, text dark purple and BOLD)
    bh = 13
    by = ID_VALUE.y0 + (ID_VALUE.height - bh) / 2
    badge = fitz.Rect(ID_VALUE.x0+2, by, ID_VALUE.x0+168, by+bh)
    page.draw_rect(badge, color=(251/255, 245/255, 255/255), fill=(251/255, 245/255, 255/255))  # #fbf5ff
    fs_id = 6.8
    tw = font_bold.text_length(intern_id, fontsize=fs_id)   # use bold font for width calc
    page.insert_text((badge.x0+(badge.width-tw)/2, badge.y0+(bh+fs_id)/2-1),
                     intern_id, fontname="PopB", fontsize=fs_id, color=TEXT_COLOR)   # BOLD

    # DEAR
    page.insert_text((DEAR_RECT.x0, DEAR_RECT.y0+14),
                     f"Dear {first_name},", fontname="PopB", fontsize=13.5, color=TEXT_COLOR)

    # BODY FIRST LINE — font size 8.5
    fs = 8.5
    y = BODY_LINE1.y0 + fs + 1
    x = BODY_LINE1.x0
    prefix = "It is with great pleasure that we formally confirm your selection for an internship in "
    suffix = ". Your profile"
    w1 = font_reg.text_length(prefix, fontsize=fs)
    page.insert_text((x, y), prefix, fontname="PopR", fontsize=fs, color=TEXT_COLOR)
    x += w1
    w2 = font_bold.text_length(role_label, fontsize=fs)
    page.insert_text((x, y), role_label, fontname="PopB", fontsize=fs, color=TEXT_COLOR)
    x += w2
    page.insert_text((x, y), suffix, fontname="PopR", fontsize=fs, color=TEXT_COLOR)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

def generate_bulk(candidates, template_path, output_dir, fonts_dir, progress_callback=None):
    """
    Generates offer letters in bulk.
    candidates: list of Candidate dictionaries or models with 'full_name', 'internship_role', 'internship_id'
    """
    font_reg_path, font_bold_path = download_fonts_if_needed(fonts_dir)
    
    font_reg = fitz.Font(fontfile=font_reg_path)
    font_bold = fitz.Font(fontfile=font_bold_path)
    clean_pix = make_clean_pixmap(template_path, dpi=200)

    os.makedirs(output_dir, exist_ok=True)
    
    total = len(candidates)
    generated = 0
    errors = []

    for idx, candidate in enumerate(candidates, start=1):
        try:
            name = candidate['full_name'].strip()
            role = candidate['internship_role'].strip()
            id_ = candidate['internship_id'].strip()
            id_num = id_.split("-")[-1]

            # Clean filename
            safe = "".join(c if c.isalnum() or c == " " else "_" for c in name).strip()
            filename = f"{safe}_{id_num}_offer_letter.pdf"
            out_path = os.path.join(output_dir, filename)

            generate_offer_letter(clean_pix, font_reg, font_bold, name, role, id_, out_path)
            generated += 1
            
            if progress_callback:
                progress_callback(idx, total, name, True, None)
                
        except Exception as e:
            errors.append((candidate['full_name'], str(e)))
            if progress_callback:
                progress_callback(idx, total, candidate['full_name'], False, str(e))
                
    return generated, errors
