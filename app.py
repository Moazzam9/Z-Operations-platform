import os
import re
import uuid
import shutil
import tempfile
import urllib.parse
import zipfile
import time
import random
import pandas as pd
import streamlit as st
import fitz  # PyMuPDF

from config import Config
from models import get_db_session, WhatsAppLink, SystemSetting
import services.generator_wrapper as generator
import services.compressor_wrapper as compressor
import services.emailer_wrapper as emailer
import services.qr_wrapper as qr_wrapper

# ── PAGE CONFIGURATION ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Zynvex Solutions Operations Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { color: #5E4B7A; font-weight: 700; }
    .card {
        background-color: #F7F4FC;
        border-left: 5px solid #7C6A9E;
        padding: 15px; border-radius: 5px; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ── DATABASE SEEDER ───────────────────────────────────────────────────────────
def seed_database_once():
    with get_db_session() as db:
        default_links = {
            "Frontend Development":    "https://chat.whatsapp.com/HvHKMvs6bXfFhF0y1r73dy",
            "Full Stack Development":  "https://chat.whatsapp.com/HeO8K1zT6aH121wZ5N1QWI",
            "Mern-Stack Development":  "https://chat.whatsapp.com/CwC5KC4TeSE3zHL37J3N49",
            "Web Development":         "https://chat.whatsapp.com/F8gneCwI8T7GHk70hsvmzw",
            "Cybersecurity Analyst":   "https://chat.whatsapp.com/Bk1NYnxjwvw8s9c8mxasCe",
            "Data Science Intern":     "https://chat.whatsapp.com/JAqv0ZpC8YNJ3zuk9iP3KU",
            "AI / Machine Learning":   "https://chat.whatsapp.com/FtRXZcE4qsOGZmgX2o8FJT",
            "Mobile App Development":  "https://chat.whatsapp.com/GryFrlVAOrI0irEjottsVh"
        }
        for role, url in default_links.items():
            if not db.query(WhatsAppLink).filter_by(role=role).first():
                db.add(WhatsAppLink(role=role, group_link=url))

        smtp_defaults = {
            "smtp_host":     "smtp.gmail.com",
            "smtp_port":     "587",
            "smtp_user":     "zynvexsolutions@gmail.com",
            "smtp_password": "fdalbitovysgxvth"
        }
        for key, val in smtp_defaults.items():
            if not db.query(SystemSetting).filter_by(key=key).first():
                db.add(SystemSetting(key=key, value=val))

        tpl_defaults = {
            "offer_subject":   emailer.OFFER_LETTER_SUBJECT,
            "offer_plain":     emailer.OFFER_LETTER_PLAIN,
            "offer_html":      emailer.OFFER_LETTER_HTML,
            "confirm_subject": emailer.CONFIRM_EMAIL_SUBJECT,
            "confirm_plain":   emailer.CONFIRM_EMAIL_PLAIN,
            "confirm_html":    emailer.CONFIRM_EMAIL_HTML
        }
        for key, val in tpl_defaults.items():
            if not db.query(SystemSetting).filter_by(key=key).first():
                db.add(SystemSetting(key=key, value=val))
        db.commit()


seed_database_once()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if "whatsapp_candidates" not in st.session_state:
    st.session_state.whatsapp_candidates = []


def get_temp_folder_size(folder_path):
    if not os.path.exists(folder_path):
        return 0, "0.0 KB"
    count, total_size = 0, 0
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            count += 1
            total_size += os.path.getsize(os.path.join(root, f))
    fmt = f"{total_size / (1024*1024):.2f} MB" if total_size >= 1024*1024 else f"{total_size / 1024:.1f} KB"
    return count, fmt


def parse_and_clean_csv(source):
    df = pd.read_csv(source, engine="python", encoding="utf-8", on_bad_lines="skip")
    df.columns = df.columns.str.strip()
    return df


def get_whatsapp_url_custom(cand):
    phone = re.sub(r'\D', '', cand.get("Phone Number", ""))
    link  = cand.get("WhatsApp Link", "")
    if phone:
        msg = (f"Hi, I'm {cand['Full Name']} joining as {cand['Internship Role']} "
               f"(ID: {cand['Internship ID']}). Joining now: {link}")
        return f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
    return link


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    "<h2 style='color:#5E4B7A; text-align:center;'>Zynvex Solutions</h2>",
    unsafe_allow_html=True
)
st.sidebar.markdown(
    "<p style='text-align:center; font-size:12px; margin-top:-10px;'>Operations Portal</p>",
    unsafe_allow_html=True
)
st.sidebar.divider()

view = st.sidebar.radio("Independent Toolkit Menu", [
    "📄 Offer Letter Generator",
    "🗜️ PDF Compressor",
    "✉️ Offer Letter Mailer",
    "💬 Role WhatsApp Mailer",
    "💬 CSV WhatsApp Invites",
    "🔲 Certificate QR Generator",
    "🧹 CSV Deduplicator & Formatter",
    "⚙️ Portal Settings"
])

st.sidebar.divider()
st.sidebar.markdown("### Session Disk Usage")
file_count, file_size_str = get_temp_folder_size(st.session_state.temp_dir)
st.sidebar.write(f"📁 Temp Files: **{file_count}**")
st.sidebar.write(f"💾 Storage: **{file_size_str}**")

if st.sidebar.button("🗑️ Clear Session Temp Files", type="primary"):
    shutil.rmtree(st.session_state.temp_dir)
    st.session_state.temp_dir = tempfile.mkdtemp()
    st.toast("Temporary session folder cleared!", icon="🗑️")
    st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 1 – OFFER LETTER GENERATOR
# ═════════════════════════════════════════════════════════════════════════════
if view == "📄 Offer Letter Generator":
    st.markdown("<h1 class='main-header'>Offer Letter PDF Generator</h1>", unsafe_allow_html=True)
    st.write("Upload candidate CSV and base PDF template to compile customised offer letters and download them as a ZIP.")

    st.markdown("""
    <div class="card">
        <strong>Required CSV columns:</strong>
        <code>Full Name</code>, <code>Internship Role</code>, <code>Internship ID</code>
    </div>
    """, unsafe_allow_html=True)

    csv_file     = st.file_uploader("1. Upload Candidate CSV", type=[".csv"])
    pdf_template = st.file_uploader("2. Upload Base PDF Template (Zynvex_Offer_Letter.pdf)", type=[".pdf"])

    if csv_file and pdf_template:
        if st.button("Generate Offer Letters", type="primary"):
            run_id        = uuid.uuid4().hex[:6]
            template_path = os.path.join(st.session_state.temp_dir, f"template_{run_id}.pdf")
            output_dir    = os.path.join(st.session_state.temp_dir, f"generated_{run_id}")
            os.makedirs(output_dir, exist_ok=True)

            with open(template_path, "wb") as fh:
                fh.write(pdf_template.getbuffer())

            try:
                df       = parse_and_clean_csv(csv_file)
                name_col = next((c for c in df.columns if c.lower() in ["full name", "name"]), None)
                role_col = next((c for c in df.columns if c.lower() in ["internship role", "role"]), None)
                id_col   = next((c for c in df.columns if c.lower() in ["internship id", "id"]), None)

                if not name_col or not role_col or not id_col:
                    st.error("CSV missing required columns: 'Full Name', 'Internship Role', 'Internship ID'.")
                else:
                    df = df.dropna(subset=[name_col, role_col, id_col])
                    candidates = [
                        {
                            "full_name":        str(row[name_col]).strip(),
                            "internship_role":  emailer.normalize_role(str(row[role_col])),
                            "internship_id":    str(row[id_col]).strip()
                        }
                        for _, row in df.iterrows()
                    ]

                    with st.spinner(f"Rendering {len(candidates)} offer letters…"):
                        g_count, errors = generator.generate_bulk(
                            candidates=candidates,
                            template_path=template_path,
                            output_dir=output_dir,
                            fonts_dir=Config.FONTS_DIR
                        )

                    zip_path = os.path.join(st.session_state.temp_dir, f"Zynvex_Offer_Letters_{run_id}.zip")
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                        for fname in os.listdir(output_dir):
                            z.write(os.path.join(output_dir, fname), arcname=fname)

                    st.success(f"Generated {g_count} offer letters!")
                    if errors:
                        st.warning(f"Skipped {len(errors)} errors.")

                    with open(zip_path, "rb") as fh:
                        st.download_button(
                            label="📥 Download Generated ZIP",
                            data=fh,
                            file_name="Zynvex_Offer_Letters.zip",
                            mime="application/zip",
                            type="primary"
                        )
            except Exception as e:
                st.error(f"Generation failed: {e}")
            finally:
                if os.path.exists(template_path):
                    os.remove(template_path)


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 2 – PDF COMPRESSOR  (matches original Colab script exactly)
# ═════════════════════════════════════════════════════════════════════════════
elif view == "🗜️ PDF Compressor":
    st.markdown("<h1 class='main-header'>Aggressive PDF Compressor</h1>", unsafe_allow_html=True)
    st.write(
        "Upload a ZIP of candidate PDFs. "
        "Ghostscript **`/ebook`** preset downsamples images to 150 dpi and applies JPEG medium quality, "
        "then qpdf linearises and recompresses streams — targeting **~75 % size reduction**."
    )

    # ── Engine status banner ──────────────────────────────────────────────────
    diags    = compressor.check_dependencies()
    col_gs, col_qpdf = st.columns(2)
    with col_gs:
        if diags["ghostscript"]["available"]:
            st.success(f"🟢 Ghostscript {diags['ghostscript']['version']} — ready")
        else:
            st.error("🔴 Ghostscript not found — **required** for compression")
    with col_qpdf:
        if diags["qpdf"]["available"]:
            st.success(f"🟢 qpdf {diags['qpdf']['version']} — stream optimisation active")
        else:
            st.warning("🟡 qpdf not installed — compression still works, streams won't be linearised")

    # ── Installation guide (shown only when GS is missing) ───────────────────
    if not diags["ghostscript"]["available"]:
        st.divider()
        st.markdown("### 📥 Install Ghostscript (required)")
        st.markdown("""
**Step 1 — Download the installer**

Go to [ghostscript.com/releases/gsdnld.html](https://ghostscript.com/releases/gsdnld.html)
and download **Ghostscript AGPL Release – Windows (64-bit)** (`.exe` installer).

**Step 2 — Run the installer**

Proceed through the wizard. Note the install folder, e.g.:
```
C:\\Program Files\\gs\\gs10.03.1
```

**Step 3 — Add the `bin\\` folder to your system PATH**
- Open Start → search **"Edit the system environment variables"**
- Click **Environment Variables → System variables → Path → Edit → New**
- Paste the path (adjust version number to match):
```
C:\\Program Files\\gs\\gs10.03.1\\bin
```
- Click **OK** on all three dialogs.

**Step 4 — Restart Streamlit**

Close the terminal and run `streamlit run app.py` again.
The green Ghostscript status badge will appear on this page automatically.
        """)
        st.stop()   # Don't render the uploader until GS is installed

    st.divider()

    # ── File uploader ─────────────────────────────────────────────────────────
    uploaded_zip = st.file_uploader("Upload ZIP archive containing offer letter PDFs", type=[".zip"])

    if uploaded_zip:
        if st.button("Compress PDFs", type="primary"):
            run_id         = uuid.uuid4().hex[:6]
            extract_dir    = os.path.join(st.session_state.temp_dir, f"ext_{run_id}")
            compressed_dir = os.path.join(st.session_state.temp_dir, f"comp_{run_id}")
            os.makedirs(extract_dir, exist_ok=True)
            os.makedirs(compressed_dir, exist_ok=True)
            zip_temp_path  = os.path.join(st.session_state.temp_dir, f"uploaded_{run_id}.zip")

            with open(zip_temp_path, "wb") as fh:
                fh.write(uploaded_zip.getbuffer())

            try:
                # Extract ZIP
                with zipfile.ZipFile(zip_temp_path, "r") as z:
                    z.extractall(extract_dir)

                # Collect PDFs (mirrors Colab script)
                pdf_files = []
                for root, _, files in os.walk(extract_dir):
                    for fname in files:
                        if fname.lower().endswith(".pdf"):
                            pdf_files.append({
                                "input":  os.path.join(root, fname),
                                "output": os.path.join(compressed_dir, fname),
                                "name":   fname
                            })

                if not pdf_files:
                    st.error("No PDF files found inside the uploaded ZIP.")
                else:
                    st.write(f"Total PDFs: **{len(pdf_files)}** — compressing with Ghostscript `/ebook` + qpdf…")
                    progress_bar = st.progress(0)

                    def progress_cb(idx, total, res):
                        progress_bar.progress(idx / total)

                    # Raises RuntimeError if GS vanished between page load & click
                    c_count, results = compressor.compress_bulk(
                        pdf_files=pdf_files,
                        gs_exe=diags["ghostscript"]["executable"],
                        progress_callback=progress_cb
                    )

                    # Bundle output into ZIP
                    final_zip_path = os.path.join(
                        st.session_state.temp_dir, f"compressed_pdfs_{run_id}.zip"
                    )
                    with zipfile.ZipFile(final_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                        for root, _, files in os.walk(compressed_dir):
                            for fname in files:
                                z.write(os.path.join(root, fname), arcname=fname)

                    st.success(f"Compression complete! Processed {c_count} / {len(pdf_files)} PDFs.")

                    # ── Report (mirrors Colab script output format) ───────────
                    report_rows              = []
                    total_before, total_after = 0.0, 0.0

                    for r in results:
                        ratio = (1 - r["after"] / r["before"]) * 100 if r["before"] else 0
                        report_rows.append({
                            "Filename":    r["name"],
                            "Before (KB)": f"{r['before']:.1f}",
                            "After (KB)":  f"{r['after']:.1f}",
                            "Saved (%)":   f"{ratio:.1f}%",
                            "Note":        r["msg"]
                        })
                        total_before += r["before"]
                        total_after  += r["after"]

                    total_ratio = (1 - total_after / total_before) * 100 if total_before else 0

                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Before", f"{total_before / 1024:.2f} MB")
                    col_b.metric("After",  f"{total_after  / 1024:.2f} MB")
                    col_c.metric("Saved",  f"{total_ratio:.1f}%")

                    st.dataframe(pd.DataFrame(report_rows), use_container_width=True)

                    with open(final_zip_path, "rb") as fh:
                        st.download_button(
                            label="📥 Download Compressed PDFs ZIP",
                            data=fh,
                            file_name="compressed_pdfs.zip",
                            mime="application/zip",
                            type="primary"
                        )

            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Compression workflow failed: {e}")
            finally:
                if os.path.exists(zip_temp_path):
                    os.remove(zip_temp_path)


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 3 – OFFER LETTER MAILER
# ═════════════════════════════════════════════════════════════════════════════
elif view == "✉️ Offer Letter Mailer":
    st.markdown("<h1 class='main-header'>Offer Letter Mailer</h1>", unsafe_allow_html=True)
    st.write(
        "Upload candidate CSV and a ZIP of generated PDFs. "
        "The system matches files by Internship ID, shows a preview checklist, "
        "then emails each candidate with their PDF attached."
    )

    with get_db_session() as db:
        smtp_config = {
            "host":     SystemSetting.get(db, "smtp_host"),
            "port":     SystemSetting.get(db, "smtp_port"),
            "user":     SystemSetting.get(db, "smtp_user"),
            "password": SystemSetting.get(db, "smtp_password")
        }
        smtp_configured = bool(smtp_config["host"] and smtp_config["user"])
        offer_templates = {
            "subject": SystemSetting.get(db, "offer_subject", emailer.OFFER_LETTER_SUBJECT),
            "plain":   SystemSetting.get(db, "offer_plain",   emailer.OFFER_LETTER_PLAIN),
            "html":    SystemSetting.get(db, "offer_html",    emailer.OFFER_LETTER_HTML)
        }

    if not smtp_configured:
        st.error("🔴 SMTP unconfigured. Go to ⚙️ Portal Settings first.")
        st.stop()

    st.success(f"🟢 SMTP ready via {smtp_config['user']}")

    csv_uploader = st.file_uploader("1. Upload Candidate CSV", type=[".csv"], key="mailer_csv")
    zip_uploader = st.file_uploader("2. Upload Offer Letters ZIP", type=[".zip"], key="mailer_zip")

    if csv_uploader and zip_uploader:
        run_id          = uuid.uuid4().hex[:6]
        pdf_extract_dir = os.path.join(st.session_state.temp_dir, f"ext_mail_{run_id}")
        os.makedirs(pdf_extract_dir, exist_ok=True)
        zip_temp_path   = os.path.join(st.session_state.temp_dir, f"mail_zip_{run_id}.zip")

        with open(zip_temp_path, "wb") as fh:
            fh.write(zip_uploader.getbuffer())

        try:
            with zipfile.ZipFile(zip_temp_path, "r") as z:
                z.extractall(pdf_extract_dir)

            df        = parse_and_clean_csv(csv_uploader)
            name_col  = next((c for c in df.columns if c.lower() in ["full name", "name"]), None)
            email_col = next((c for c in df.columns if c.lower() in ["email address", "email"]), None)
            id_col    = next((c for c in df.columns if c.lower() in ["internship id", "id"]), None)

            if not name_col or not email_col or not id_col:
                st.error("CSV missing required columns: 'Full Name', 'Email Address', 'Internship ID'.")
            else:
                df = df.dropna(subset=[name_col, email_col])
                candidates_list = []

                for idx, row in df.iterrows():
                    name    = str(row[name_col]).strip()
                    email   = str(row[email_col]).strip()
                    raw_id  = str(row[id_col]).strip() if not pd.isna(row[id_col]) else ""
                    csv_num = emailer.clean_id(raw_id)

                    matched_path, matched_filename = None, "N/A"
                    if csv_num:
                        for root, _, files in os.walk(pdf_extract_dir):
                            for fname in files:
                                if fname.lower().endswith(".pdf"):
                                    _, pdf_id = emailer.parse_pdf(fname)
                                    if pdf_id == csv_num:
                                        matched_path     = os.path.join(root, fname)
                                        matched_filename = fname
                                        break
                            if matched_path:
                                break

                    candidates_list.append({
                        "idx":          idx,
                        "Select":       matched_path is not None,
                        "Full Name":    name,
                        "Email":        email,
                        "Internship ID": raw_id,
                        "PDF Filename": matched_filename,
                        "PDF Path":     matched_path,
                        "Match":        "✔ MATCH" if matched_path else "✘ NO MATCH"
                    })

                st.subheader("Candidate Match Checklist")
                edited_df = st.data_editor(
                    pd.DataFrame(candidates_list),
                    column_config={
                        "Select":   st.column_config.CheckboxColumn(default=False),
                        "PDF Path": None,
                        "idx":      None
                    },
                    disabled=["idx", "Full Name", "Email", "Internship ID",
                              "PDF Filename", "Match", "PDF Path"],
                    use_container_width=True,
                    key="mailer_editor"
                )

                selected_rows = edited_df[edited_df["Select"] == True].to_dict(orient="records")
                st.write(f"**{len(selected_rows)} candidate(s) selected.**")

                confirm = st.checkbox("I have reviewed the match list and confirm sending")

                if st.button("Start Mailing", type="primary",
                             disabled=not confirm or len(selected_rows) == 0):
                    prog     = st.progress(0)
                    msg_area = st.empty()
                    total    = len(selected_rows)
                    sent, failed = 0, 0

                    for i, cand in enumerate(selected_rows, 1):
                        msg_area.write(f"Sending {i}/{total}: **{cand['Full Name']}**")
                        try:
                            emailer.send_smtp_email(
                                smtp_config=smtp_config,
                                to_email=cand["Email"],
                                subject=offer_templates["subject"],
                                plain_body=offer_templates["plain"].format(name=cand["Full Name"]),
                                html_body=offer_templates["html"].format(name=cand["Full Name"]),
                                attachment_path=cand["PDF Path"]
                            )
                            sent += 1
                        except Exception as e:
                            st.error(f"Failed for {cand['Full Name']}: {e}")
                            failed += 1
                        prog.progress(i / total)
                        if i < total:
                            time.sleep(random.randint(10, 12))

                    st.success(f"Done! Sent: {sent}, Failed: {failed}")

        except Exception as e:
            st.error(f"Mailer failed: {e}")
        finally:
            if os.path.exists(zip_temp_path):
                os.remove(zip_temp_path)


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 4 – ROLE WHATSAPP MAILER
# ═════════════════════════════════════════════════════════════════════════════
elif view == "💬 Role WhatsApp Mailer":
    st.markdown("<h1 class='main-header'>Role WhatsApp Group Mailer</h1>", unsafe_allow_html=True)
    st.write(
        "Upload candidate CSV. Roles are normalised and matched to default group links "
        "stored in Settings, then confirmation emails are sent."
    )

    with get_db_session() as db:
        smtp_config = {
            "host":     SystemSetting.get(db, "smtp_host"),
            "port":     SystemSetting.get(db, "smtp_port"),
            "user":     SystemSetting.get(db, "smtp_user"),
            "password": SystemSetting.get(db, "smtp_password")
        }
        smtp_configured     = bool(smtp_config["host"] and smtp_config["user"])
        confirm_templates   = {
            "subject": SystemSetting.get(db, "confirm_subject", emailer.CONFIRM_EMAIL_SUBJECT),
            "plain":   SystemSetting.get(db, "confirm_plain",   emailer.CONFIRM_EMAIL_PLAIN),
            "html":    SystemSetting.get(db, "confirm_html",    emailer.CONFIRM_EMAIL_HTML)
        }
        whatsapp_links_dict = {lnk.role: lnk.group_link for lnk in db.query(WhatsAppLink).all()}

    if not smtp_configured:
        st.error("🔴 SMTP unconfigured. Go to ⚙️ Portal Settings first.")
        st.stop()

    st.success(f"🟢 SMTP ready via {smtp_config['user']}")

    uploaded_csv = st.file_uploader("Upload Candidates CSV", type=[".csv"], key="role_wa_csv")

    if uploaded_csv:
        df        = parse_and_clean_csv(uploaded_csv)
        name_col  = next((c for c in df.columns if c.lower() in ["full name", "name"]), None)
        email_col = next((c for c in df.columns if c.lower() in ["email address", "email"]), None)
        role_col  = next((c for c in df.columns if c.lower() in ["internship role", "role"]), None)
        id_col    = next((c for c in df.columns if c.lower() in ["internship id", "id"]), None)

        if not all([name_col, email_col, role_col, id_col]):
            st.error("CSV missing required columns.")
        else:
            df = df.dropna(subset=[name_col, email_col])
            candidates_list, missing_roles = [], set()

            for idx, row in df.iterrows():
                name       = str(row[name_col]).strip()
                email      = str(row[email_col]).strip()
                raw_role   = emailer.normalize_role(str(row[role_col]))
                raw_id     = str(row[id_col]).strip()
                group_link = whatsapp_links_dict.get(raw_role)
                if not group_link:
                    missing_roles.add(raw_role)
                candidates_list.append({
                    "idx":                idx,
                    "Select":             group_link is not None,
                    "Full Name":          name,
                    "Email":              email,
                    "Normalised Role":    raw_role,
                    "Internship ID":      raw_id,
                    "WhatsApp Group Link": group_link or "⚠️ Missing mapping!",
                    "Status":             "Linked" if group_link else "Unmapped"
                })

            st.subheader("Role Mapping Preview")
            edited_df = st.data_editor(
                pd.DataFrame(candidates_list),
                column_config={
                    "Select": st.column_config.CheckboxColumn(default=False),
                    "idx":    None
                },
                disabled=["idx", "Full Name", "Email", "Normalised Role",
                          "Internship ID", "WhatsApp Group Link", "Status"],
                use_container_width=True,
                key="role_invite_editor"
            )

            selected_rows = edited_df[edited_df["Select"] == True].to_dict(orient="records")
            st.write(f"**{len(selected_rows)} candidate(s) selected.**")

            if missing_roles:
                st.warning(f"⚠️ No group link for: {', '.join(sorted(missing_roles))}. Add them in ⚙️ Settings.")

            confirm = st.checkbox("Confirm sending WhatsApp seat confirmation emails")

            if st.button("Send Group Invites", type="primary",
                         disabled=not confirm or len(selected_rows) == 0):
                prog     = st.progress(0)
                msg_area = st.empty()
                total    = len(selected_rows)
                sent, failed = 0, 0

                for i, cand in enumerate(selected_rows, 1):
                    msg_area.write(f"Sending {i}/{total}: **{cand['Full Name']}**")
                    try:
                        emailer.send_smtp_email(
                            smtp_config=smtp_config,
                            to_email=cand["Email"],
                            subject=confirm_templates["subject"],
                            plain_body=confirm_templates["plain"].format(
                                name=cand["Full Name"],
                                role=cand["Normalised Role"],
                                internship_id=cand["Internship ID"],
                                group_link=cand["WhatsApp Group Link"]
                            ),
                            html_body=confirm_templates["html"].format(
                                name=cand["Full Name"],
                                role=cand["Normalised Role"],
                                internship_id=cand["Internship ID"],
                                group_link=cand["WhatsApp Group Link"]
                            )
                        )
                        sent += 1
                    except Exception as e:
                        st.error(f"Failed for {cand['Full Name']}: {e}")
                        failed += 1
                    prog.progress(i / total)
                    if i < total:
                        time.sleep(10)

                st.success(f"Done! Sent: {sent}, Failed: {failed}")


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 5 – CSV WHATSAPP INVITES
# ═════════════════════════════════════════════════════════════════════════════
elif view == "💬 CSV WhatsApp Invites":
    st.markdown("<h1 class='main-header'>CSV WhatsApp Invites</h1>", unsafe_allow_html=True)
    st.write(
        "Upload a CSV with custom WhatsApp links per candidate. "
        "Completely separate from the main database — stored in session memory only."
    )

    with get_db_session() as db:
        smtp_config = {
            "host":     SystemSetting.get(db, "smtp_host"),
            "port":     SystemSetting.get(db, "smtp_port"),
            "user":     SystemSetting.get(db, "smtp_user"),
            "password": SystemSetting.get(db, "smtp_password")
        }
        smtp_configured   = bool(smtp_config["host"] and smtp_config["user"])
        confirm_templates = {
            "subject": SystemSetting.get(db, "confirm_subject", emailer.CONFIRM_EMAIL_SUBJECT),
            "plain":   SystemSetting.get(db, "confirm_plain",   emailer.CONFIRM_EMAIL_PLAIN),
            "html":    SystemSetting.get(db, "confirm_html",    emailer.CONFIRM_EMAIL_HTML)
        }

    st.write("**Required columns:** `Full Name`, `Email Address`, `Internship Role`, `Internship ID`, `WhatsApp Link`  (Optional: `Phone Number`)")
    uploaded_invite_csv = st.file_uploader("Upload Invites CSV", type=[".csv"], key="invite_csv_uploader")

    if uploaded_invite_csv:
        csv_temp = os.path.join(st.session_state.temp_dir, f"invite_{uuid.uuid4().hex[:6]}.csv")
        with open(csv_temp, "wb") as fh:
            fh.write(uploaded_invite_csv.getbuffer())
        try:
            df        = parse_and_clean_csv(csv_temp)
            name_col  = next((c for c in df.columns if c.lower() in ["full name", "name"]), None)
            email_col = next((c for c in df.columns if c.lower() in ["email address", "email"]), None)
            role_col  = next((c for c in df.columns if c.lower() in ["internship role", "role"]), None)
            id_col    = next((c for c in df.columns if c.lower() in ["internship id", "id"]), None)
            link_col  = next((c for c in df.columns if c.lower() in ["whatsapp link", "group link", "link"]), None)
            phone_col = next((c for c in df.columns if c.lower() in ["phone number", "phone", "contact"]), None)

            if not all([name_col, email_col, role_col, id_col, link_col]):
                st.error("Missing required columns. Ensure CSV has: Full Name, Email Address, Internship Role, Internship ID, WhatsApp Link.")
            else:
                df = df.dropna(subset=[name_col, email_col]).drop_duplicates(subset=[email_col])
                parsed = []
                for idx, row in df.iterrows():
                    parsed.append({
                        "id":              f"csv-{idx}-{uuid.uuid4().hex[:6]}",
                        "Full Name":       str(row[name_col]).strip().title(),
                        "Email Address":   str(row[email_col]).strip(),
                        "Internship Role": emailer.normalize_role(str(row[role_col])),
                        "Internship ID":   str(row[id_col]).strip(),
                        "WhatsApp Link":   str(row[link_col]).strip(),
                        "Phone Number":    str(row[phone_col]).strip() if phone_col and not pd.isna(row.get(phone_col, float('nan'))) else "",
                        "Status":          "Pending"
                    })
                st.session_state.whatsapp_candidates = parsed
                st.toast(f"Loaded {len(parsed)} candidates!", icon="💬")
        except Exception as e:
            st.error(f"Error parsing CSV: {e}")
        finally:
            if os.path.exists(csv_temp):
                os.remove(csv_temp)
        st.rerun()

    if st.session_state.whatsapp_candidates:
        st.subheader("CSV Invites Registry")
        cands_df = pd.DataFrame(st.session_state.whatsapp_candidates)
        cands_df.insert(0, "Select", False)

        edited_df = st.data_editor(
            cands_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(default=False),
                "id":     None
            },
            disabled=["id", "Full Name", "Email Address", "Internship Role",
                      "Internship ID", "WhatsApp Link", "Phone Number", "Status"],
            use_container_width=True,
            key="csv_invites_editor"
        )

        selected_ids = edited_df[edited_df["Select"] == True]["id"].tolist()
        if selected_ids:
            st.write(f"**{len(selected_ids)} candidate(s) selected.**")
            if st.button("📨 Email Group Invites to Selected", type="primary", disabled=not smtp_configured):
                prog     = st.progress(0)
                msg_area = st.empty()
                total    = len(selected_ids)
                sent, failed = 0, 0

                for i, cid in enumerate(selected_ids, 1):
                    cand = next((c for c in st.session_state.whatsapp_candidates if c["id"] == cid), None)
                    if not cand:
                        continue
                    msg_area.write(f"Sending {i}/{total}: **{cand['Full Name']}**")
                    try:
                        emailer.send_smtp_email(
                            smtp_config=smtp_config,
                            to_email=cand["Email Address"],
                            subject=confirm_templates["subject"],
                            plain_body=confirm_templates["plain"].format(
                                name=cand["Full Name"],
                                role=cand["Internship Role"],
                                internship_id=cand["Internship ID"],
                                group_link=cand["WhatsApp Link"]
                            ),
                            html_body=confirm_templates["html"].format(
                                name=cand["Full Name"],
                                role=cand["Internship Role"],
                                internship_id=cand["Internship ID"],
                                group_link=cand["WhatsApp Link"]
                            )
                        )
                        cand["Status"] = "Sent"
                        sent += 1
                    except Exception as e:
                        cand["Status"] = "Failed"
                        failed += 1
                    prog.progress(i / total)
                    if i < total:
                        time.sleep(10)
                st.success(f"Done! Sent: {sent}, Failed: {failed}")
                st.rerun()

        st.divider()
        st.subheader("Individual Operations")
        options = {
            f"{c['Full Name']} ({c['Internship ID']})": c["id"]
            for c in st.session_state.whatsapp_candidates
        }
        selected_option = st.selectbox("Select candidate", list(options.keys()))

        if selected_option:
            cid  = options[selected_option]
            cand = next((c for c in st.session_state.whatsapp_candidates if c["id"] == cid), None)
            if cand:
                col_d1, col_d2 = st.columns(2)
                col_d1.markdown(f"""
**Full Name:** {cand['Full Name']}
**Email:** {cand['Email Address']}
**Phone:** {cand['Phone Number'] or 'N/A'}
**Role:** {cand['Internship Role']}
**ID:** `{cand['Internship ID']}`
                """)
                col_d2.write(f"**Status:** `{cand['Status']}`")
                col_d2.write(f"**Link:** `{cand['WhatsApp Link']}`")
                st.write("---")

                a1, a2 = st.columns(2)
                if a1.button("📧 Mail WhatsApp Invite", disabled=not smtp_configured):
                    try:
                        emailer.send_smtp_email(
                            smtp_config=smtp_config,
                            to_email=cand["Email Address"],
                            subject=confirm_templates["subject"],
                            plain_body=confirm_templates["plain"].format(
                                name=cand["Full Name"],
                                role=cand["Internship Role"],
                                internship_id=cand["Internship ID"],
                                group_link=cand["WhatsApp Link"]
                            ),
                            html_body=confirm_templates["html"].format(
                                name=cand["Full Name"],
                                role=cand["Internship Role"],
                                internship_id=cand["Internship ID"],
                                group_link=cand["WhatsApp Link"]
                            )
                        )
                        cand["Status"] = "Sent"
                        st.success("Invite email sent!")
                        st.rerun()
                    except Exception as e:
                        cand["Status"] = "Failed"
                        st.error(f"Failed: {e}")
                        st.rerun()

                a2.link_button("💬 Open WhatsApp redirect", get_whatsapp_url_custom(cand))

    else:
        st.info("No invite list loaded. Upload a CSV above to begin.")


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 6 – CERTIFICATE QR GENERATOR
# ═════════════════════════════════════════════════════════════════════════════
elif view == "🔲 Certificate QR Generator":
    st.markdown("<h1 class='main-header'>Certificate QR Code Generator</h1>", unsafe_allow_html=True)
    st.write(
        "Upload a CSV with Internship IDs and a ZIP containing PDF certificates. "
        "The system will generate a QR code for each certificate, overlay it on the PDF, "
        "and provide a ZIP containing the updated certificates."
    )

    st.markdown("""
    <div class="card">
        <strong>Required CSV column:</strong>
        <code>Internship ID</code><br>
        <strong>Note:</strong> PDF filenames must exactly match the Internship ID (e.g. <code>ZYNVEX-FE-1042.pdf</code>).
    </div>
    """, unsafe_allow_html=True)

    with st.expander("QR Code Configuration", expanded=False):
        col_x, col_w, col_m = st.columns(3)
        qr_x = col_x.number_input("X Coordinate (points from left)", value=400, step=10)
        qr_width = col_w.number_input("QR Width (points)", value=70, step=5)
        bottom_margin = col_m.number_input("Bottom Margin (points)", value=60, step=5)
        st.caption("Default values are optimized for Zynvex Certificates. (60 points ≈ 0.83 inch)")

    csv_uploader = st.file_uploader("1. Upload Candidate CSV", type=[".csv"], key="qr_csv")
    zip_uploader = st.file_uploader("2. Upload Certificates ZIP", type=[".zip"], key="qr_zip")

    if csv_uploader and zip_uploader:
        if st.button("Generate & Apply QR Codes", type="primary"):
            run_id = uuid.uuid4().hex[:6]
            pdf_extract_dir = os.path.join(st.session_state.temp_dir, f"ext_qr_{run_id}")
            output_dir = os.path.join(st.session_state.temp_dir, f"qr_out_{run_id}")
            os.makedirs(pdf_extract_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            
            zip_temp_path = os.path.join(st.session_state.temp_dir, f"qr_in_{run_id}.zip")
            out_zip_path = os.path.join(st.session_state.temp_dir, f"certificates_with_qr_{run_id}.zip")

            with open(zip_temp_path, "wb") as fh:
                fh.write(zip_uploader.getbuffer())

            try:
                # 1. Parse CSV
                df = parse_and_clean_csv(csv_uploader)
                id_col = next((c for c in df.columns if c.lower() in ["internship id", "id"]), None)
                
                if not id_col:
                    st.error("CSV missing required column: 'Internship ID'.")
                else:
                    ids = df[id_col].dropna().astype(str).str.strip().tolist()
                    ids = [id_ for id_ in ids if id_]
                    st.info(f"Found {len(ids)} certificate IDs in CSV.")

                    # 2. Extract ZIP
                    with zipfile.ZipFile(zip_temp_path, "r") as z:
                        z.extractall(pdf_extract_dir)

                    # 3. Build mapping: filename (lowercase) -> full path
                    pdf_files = {}
                    for root, _, files in os.walk(pdf_extract_dir):
                        for f in files:
                            if f.lower().endswith(".pdf"):
                                pdf_files[f.lower()] = os.path.join(root, f)

                    if not pdf_files:
                        st.error("No PDF files found inside the uploaded ZIP.")
                    else:
                        st.write("Processing certificates...")
                        progress_bar = st.progress(0)
                        
                        def progress_cb(idx, total):
                            progress_bar.progress(idx / total)

                        # 4. Process
                        success_count, failed_ids, page_height, qr_y = qr_wrapper.process_certificates_batch(
                            pdf_files=pdf_files,
                            ids=ids,
                            output_dir=output_dir,
                            qr_x=qr_x,
                            qr_width=qr_width,
                            bottom_margin=bottom_margin,
                            progress_callback=progress_cb
                        )

                        # 5. Bundle Output
                        with zipfile.ZipFile(out_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                            for root, _, files in os.walk(output_dir):
                                for f in files:
                                    z.write(os.path.join(root, f), arcname=f)

                        st.success(f"Successfully processed {success_count} certificates! (Page Height: {page_height} pt, QR Y: {qr_y:.2f} pt)")
                        if failed_ids:
                            with st.expander(f"❌ Failed ({len(failed_ids)})"):
                                for err in failed_ids:
                                    st.write(f"- {err}")

                        if success_count > 0:
                            with open(out_zip_path, "rb") as fh:
                                st.download_button(
                                    label="📥 Download Certificates with QR",
                                    data=fh,
                                    file_name="certificates_with_qr.zip",
                                    mime="application/zip",
                                    type="primary"
                                )

            except Exception as e:
                st.error(f"Processing failed: {e}")
            finally:
                if os.path.exists(zip_temp_path):
                    os.remove(zip_temp_path)


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 7 – CSV DEDUPLICATOR & FORMATTER
# ═════════════════════════════════════════════════════════════════════════════
elif view == "🧹 CSV Deduplicator & Formatter":
    st.markdown("<h1 class='main-header'>CSV Deduplicator & Formatter</h1>", unsafe_allow_html=True)
    st.write(
        "Upload a CSV file. This tool will format the columns and remove duplicate records "
        "based on **Email Address** or **Phone Number**, keeping the most complete entry."
    )

    uploaded_csv = st.file_uploader("Upload Raw CSV", type=[".csv"], key="dedup_csv")

    if uploaded_csv:
        try:
            df = parse_and_clean_csv(uploaded_csv)
            
            # Identify columns robustly, prioritizing the order of possible_names
            def find_col(possible_names):
                for name in possible_names:
                    for col in df.columns:
                        if str(col).strip().lower() == name.lower():
                            return col
                return None

            name_col = find_col(["Full Name", "Name", "Candidate Name", "First Name"])
            email_col = find_col(["Email Address", "Email", "Email ID"])
            phone_col = find_col(["Phone Number (WhatsApp)", "Phone Number", "Phone", "WhatsApp Number", "WhatsApp", "Contact", "Contact Number"])
            role_col = find_col(["Internship Role", "Role", "Position", "Applied For", "Domain", "Course", "Internship Domain", "Program", "Track"])
            id_col = find_col(["Offer Letter ID", "Registration ID", "Internship ID", "ID", "Candidate ID", "Intern ID"])

            if not name_col and not email_col:
                st.error("Could not confidently find 'Full Name' or 'Email Address' columns. Please check your CSV headers.")
            else:
                rename_map = {}
                if name_col: rename_map[name_col] = "Full Name"
                if email_col: rename_map[email_col] = "Email Address"
                if phone_col: rename_map[phone_col] = "Phone Number (WhatsApp)"
                if role_col: rename_map[role_col] = "Internship Role"
                if id_col: rename_map[id_col] = "Internship ID"
                
                df = df.rename(columns=rename_map)
                
                std_cols = ["Full Name", "Email Address", "Phone Number (WhatsApp)", "Internship Role", "Internship ID"]
                for c in std_cols:
                    if c not in df.columns:
                        df[c] = ""
                
                df_std = df[std_cols].copy()
                
                # String conversion and NaN handling
                for c in std_cols:
                    df_std[c] = df_std[c].astype(str).str.strip().replace({'nan': '', 'None': ''})
                
                # Match and format Internship Role
                def map_internship_role(raw_role):
                    r = str(raw_role).lower()
                    if not r: return ""
                    if 'mern' in r:
                        return 'MERN-Stack Developer'
                    if 'frontend' in r or 'front-end' in r or 'front end' in r:
                        return 'Frontend Developer'
                    if 'full stack' in r or 'full-stack' in r:
                        return 'Full Stack Developer'
                    if 'web' in r:
                        return 'Web Developer'
                    if 'cyber' in r or 'security' in r:
                        return 'Cybersecurity Analyst'
                    if 'data' in r:
                        return 'Data Science Intern'
                    if re.search(r'\bai\b', r) or 'machine learning' in r or re.search(r'\bml\b', r) or 'artificial intelligence' in r:
                        return 'AI / Machine Learning'
                    if 'mobile' in r or 'app' in r or 'android' in r or re.search(r'\bios\b', r) or 'flutter' in r:
                        return 'Mobile App Developer'
                    return raw_role

                df_std['Internship Role'] = df_std['Internship Role'].apply(map_internship_role)
                
                # Calculate completeness score
                df_std['completeness'] = df_std[std_cols].apply(lambda x: (x != "").sum(), axis=1)
                
                # Sort by completeness to keep the best record first
                df_std = df_std.sort_values('completeness', ascending=False)
                
                original_count = len(df_std)
                
                # Format Internship ID
                df_std['Internship ID'] = df_std['Internship ID'].astype(str).str.strip().str.upper()
                
                # Normalized columns for duplicate checking
                df_std['_clean_email'] = df_std['Email Address'].str.lower()
                df_std['_clean_phone'] = df_std['Phone Number (WhatsApp)'].str.replace(r'\D', '', regex=True)
                
                # Identify ALL duplicates for detailed reporting
                all_email_dupes = df_std[df_std.duplicated(subset=['_clean_email'], keep=False) & (df_std['_clean_email'] != "")]
                all_phone_dupes = df_std[df_std.duplicated(subset=['_clean_phone'], keep=False) & (df_std['_clean_phone'] != "")]
                
                # Group them to show related IDs
                email_dupe_groups = []
                for email, group in all_email_dupes.groupby('_clean_email'):
                    ids = [i if str(i).strip() else "NO_ID" for i in group['Internship ID'].tolist()]
                    names = group['Full Name'].tolist()
                    email_dupe_groups.append({"Email": email, "Names": ", ".join(names), "Duplicated IDs": ", ".join(ids), "Count": len(group)})
                
                phone_dupe_groups = []
                for phone, group in all_phone_dupes.groupby('_clean_phone'):
                    ids = [i if str(i).strip() else "NO_ID" for i in group['Internship ID'].tolist()]
                    names = group['Full Name'].tolist()
                    phone_dupe_groups.append({"Phone": phone, "Names": ", ".join(names), "Duplicated IDs": ", ".join(ids), "Count": len(group)})
                
                # Identify duplicates for reporting
                email_dupe_mask = df_std.duplicated(subset=['_clean_email'], keep='first') & (df_std['_clean_email'] != "")
                removed_emails_df = df_std[email_dupe_mask]
                
                # Filter out email duplicates
                df_std = df_std[~email_dupe_mask]
                
                phone_dupe_mask = df_std.duplicated(subset=['_clean_phone'], keep='first') & (df_std['_clean_phone'] != "")
                removed_phones_df = df_std[phone_dupe_mask]
                
                # Filter out phone duplicates
                df_std = df_std[~phone_dupe_mask]
                
                # Identify invalid formatting in IDs (missing or no alphanumeric characters)
                def is_invalid_id(val):
                    s = str(val).strip()
                    if not s: return True
                    # Check if it matches ZYNVEX-CERT-0000 or ZYNVEX-CERT-00000
                    if not re.match(r'^ZYNVEX-CERT-\d{4,5}$', s, re.IGNORECASE): return True
                    if s.lower() in ['nan', 'none', 'n/a', 'na']: return True
                    return False
                
                invalid_id_mask = df_std['Internship ID'].apply(is_invalid_id)
                invalid_ids_df = df_std[invalid_id_mask]
                
                # Prepare invalid IDs summary
                invalid_summary = []
                for idx, row in invalid_ids_df.iterrows():
                    invalid_summary.append({
                        "Original Row (approx)": idx + 2,
                        "Full Name": row['Full Name'],
                        "Invalid ID": row['Internship ID'] if str(row['Internship ID']).strip() else "(Empty)"
                    })
                
                final_count = len(df_std)
                duplicates_removed = len(removed_emails_df) + len(removed_phones_df)
                invalid_count = len(invalid_ids_df)
                
                # Clean up temp columns and reset index
                df_out = df_std[std_cols].reset_index(drop=True)
                
                # Render summary
                st.success(f"Processed successfully! Retained **{final_count}** unique records out of **{original_count}**.")
                
                st.subheader("📊 Processing Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Rows Processed", original_count)
                col2.metric("Duplicates Removed", duplicates_removed)
                col3.metric("Invalid/Missing IDs", invalid_count)
                
                if duplicates_removed > 0:
                    with st.expander(f"🔍 View Duplicate Details ({duplicates_removed} removed)"):
                        if email_dupe_groups:
                            st.markdown("**Shared Email Addresses (Which IDs were duplicated):**")
                            st.dataframe(pd.DataFrame(email_dupe_groups), use_container_width=True)
                        if phone_dupe_groups:
                            st.markdown("**Shared Phone Numbers (Which IDs were duplicated):**")
                            st.dataframe(pd.DataFrame(phone_dupe_groups), use_container_width=True)
                
                if invalid_count > 0:
                    with st.expander(f"⚠️ View Invalid Format IDs ({invalid_count})"):
                        st.markdown("The following records have missing, completely empty, or improperly formatted Internship IDs:")
                        st.dataframe(pd.DataFrame(invalid_summary), use_container_width=True)
                
                st.dataframe(df_out, use_container_width=True)
                
                csv_buffer = df_out.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Formatted CSV",
                    data=csv_buffer,
                    file_name="Formatted_Candidates.csv",
                    mime="text/csv",
                    type="primary"
                )

        except Exception as e:
            st.error(f"Error processing CSV: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 8 – PORTAL SETTINGS
# =============================================================================
elif view == "⚙️ Portal Settings":
    st.markdown("<h1 class='main-header'>Portal Settings</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📧 SMTP Credentials", "💬 WhatsApp Default Links", "📝 Email Templates"])

    # ── SMTP ──────────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("SMTP Server Setup")
        with get_db_session() as db:
            s_host = SystemSetting.get(db, "smtp_host", "")
            s_port = SystemSetting.get(db, "smtp_port", "587")
            s_user = SystemSetting.get(db, "smtp_user", "")

        with st.form("smtp_form"):
            host_val = st.text_input("SMTP Server Host", value=s_host)
            port_val = st.text_input("SMTP Server Port", value=s_port)
            user_val = st.text_input("Sender Email Address", value=s_user)
            pass_val = st.text_input("SMTP App Password", type="password",
                                     placeholder="Leave blank to keep existing password")
            if st.form_submit_button("Save SMTP Settings"):
                with get_db_session() as db:
                    SystemSetting.set(db, "smtp_host", host_val.strip())
                    SystemSetting.set(db, "smtp_port", port_val.strip())
                    SystemSetting.set(db, "smtp_user", user_val.strip())
                    if pass_val:
                        SystemSetting.set(db, "smtp_password", pass_val.strip())
                    db.commit()
                st.success("SMTP settings saved.")
                st.rerun()

    # =========================================================================
    # TAB 2 - WHATSAPP GROUP LINK MANAGER (card grid + inline edit)
    # =========================================================================
    with tab2:
        st.subheader("Program WhatsApp Group Links")
        st.write(
            "Manage the WhatsApp group link for each internship program. "
            "Links are stored persistently in the database and used automatically "
            "when sending seat confirmation emails. No source-code changes required."
        )

        with get_db_session() as db:
            wa_links_all = db.query(WhatsAppLink).order_by(WhatsAppLink.role).all()
            links_list   = [{"role": l.role, "group_link": l.group_link} for l in wa_links_all]

        # -- Card grid (2 columns) --------------------------------------------
        if links_list:
            st.markdown("#### Current Program Links")
            for i in range(0, len(links_list), 2):
                card_cols = st.columns(2)
                for j, cc in enumerate(card_cols):
                    if i + j < len(links_list):
                        item = links_list[i + j]
                        cc.markdown(
                            f"""<div style="border:1px solid #D5C9F0;border-radius:8px;
                                padding:14px 16px;background:#F7F4FC;margin-bottom:10px;">
                                <div style="font-weight:700;color:#5E4B7A;font-size:14px;
                                     margin-bottom:6px;">💬 {item['role']}</div>
                                <div style="font-size:12px;color:#555;word-break:break-all;">
                                <a href="{item['group_link']}" target="_blank"
                                   style="color:#7C6A9E;">{item['group_link']}</a></div>
                                </div>""",
                            unsafe_allow_html=True
                        )
        else:
            st.info("No program links configured yet. Add one below.")

        st.divider()

        # -- Edit existing link -----------------------------------------------
        if links_list:
            st.markdown("#### Edit Existing Program Link")
            edit_role    = st.selectbox("Select program to edit",
                                        [l["role"] for l in links_list], key="edit_role_sel")
            current_link = next((l["group_link"] for l in links_list if l["role"] == edit_role), "")
            with st.form("wa_edit_form"):
                new_link = st.text_input("New WhatsApp Group Link URL", value=current_link)
                if st.form_submit_button("Update Link"):
                    if not new_link.strip():
                        st.error("Link URL cannot be empty.")
                    else:
                        with get_db_session() as db:
                            ex = db.query(WhatsAppLink).filter_by(role=edit_role).first()
                            if ex:
                                ex.group_link = new_link.strip()
                                db.commit()
                        st.success(f"Updated link for **{edit_role}**.")
                        st.rerun()
            st.divider()

        # -- Add new program --------------------------------------------------
        st.markdown("#### Add New Program Link")
        with st.form("wa_add_form"):
            new_role = st.text_input("Program / Role Title",
                                     placeholder="e.g. Frontend Development")
            new_url  = st.text_input("WhatsApp Group Link URL",
                                     placeholder="https://chat.whatsapp.com/...")
            if st.form_submit_button("Add Program Link"):
                if not new_role.strip() or not new_url.strip():
                    st.error("Both Program name and Link URL are required.")
                else:
                    norm = emailer.normalize_role(new_role.strip())
                    with get_db_session() as db:
                        ex = db.query(WhatsAppLink).filter_by(role=norm).first()
                        if ex:
                            ex.group_link = new_url.strip()
                        else:
                            db.add(WhatsAppLink(role=norm, group_link=new_url.strip()))
                        db.commit()
                    st.success(f"Saved link for **{norm}**.")
                    st.rerun()

        # -- Delete program ---------------------------------------------------
        if links_list:
            st.divider()
            st.markdown("#### Remove Program Link")
            del_role = st.selectbox("Select program to remove",
                                    [l["role"] for l in links_list], key="del_role_sel")
            if st.button("Delete This Program Link", type="primary"):
                with get_db_session() as db:
                    db.query(WhatsAppLink).filter_by(role=del_role).delete()
                    db.commit()
                st.toast(f"Removed link for '{del_role}'", icon="🗑️")
                st.rerun()

    # =========================================================================
    # TAB 3 - EMAIL TEMPLATE MANAGER (split pane editor + live HTML preview)
    # =========================================================================
    with tab3:
        import streamlit.components.v1 as components

        st.subheader("Email Template Manager")
        st.write(
            "Edit the full HTML body of each email template directly from this page. "
            "Changes are saved to the database and used automatically when sending emails — "
            "no source-code changes required."
        )

        tpl_choice = st.selectbox("Select template to edit", [
            "Offer Letter Email  (sent with PDF attachment)",
            "WhatsApp Seat Confirmation Email"
        ], key="tpl_selector")

        is_offer = tpl_choice.startswith("Offer")

        with get_db_session() as db:
            if is_offer:
                db_subject   = SystemSetting.get(db, "offer_subject",   emailer.OFFER_LETTER_SUBJECT)
                db_html      = SystemSetting.get(db, "offer_html",      emailer.OFFER_LETTER_HTML)
                db_plain     = SystemSetting.get(db, "offer_plain",     emailer.OFFER_LETTER_PLAIN)
                save_subject_key = "offer_subject"
                save_html_key    = "offer_html"
                save_plain_key   = "offer_plain"
                placeholder_info = "`{name}` — candidate's full name"
                sample_vars = {"name": "Ahmed Khan"}
            else:
                db_subject   = SystemSetting.get(db, "confirm_subject", emailer.CONFIRM_EMAIL_SUBJECT)
                db_html      = SystemSetting.get(db, "confirm_html",    emailer.CONFIRM_EMAIL_HTML)
                db_plain     = SystemSetting.get(db, "confirm_plain",   emailer.CONFIRM_EMAIL_PLAIN)
                save_subject_key = "confirm_subject"
                save_html_key    = "confirm_html"
                save_plain_key   = "confirm_plain"
                placeholder_info = "`{name}`, `{role}`, `{internship_id}`, `{group_link}`"
                sample_vars = {
                    "name":          "Ahmed Khan",
                    "role":          "Frontend Development",
                    "internship_id": "ZYNVEX-FE-1042",
                    "group_link":    "https://chat.whatsapp.com/example"
                }

        # Variable reference badge
        st.markdown(
            f"<div style='background:#F2ECFA;border-left:4px solid #7C6A9E;"
            f"border-radius:4px;padding:10px 14px;margin-bottom:12px;font-size:13px;'>"
            f"<strong>Supported placeholders:</strong> {placeholder_info}<br>"
            f"<span style='color:#777;'>Replaced with real candidate data when emails are sent.</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        st.divider()

        # Split-pane: editor on left, live preview on right
        edit_col, preview_col = st.columns([1, 1], gap="large")

        with edit_col:
            st.markdown("**Editor**")
            # Dynamic keys prevent Streamlit from holding onto values when switching templates
            ed_subject = st.text_input("Email Subject Line",
                                       value=db_subject, key=f"ed_subject_{is_offer}")
            ed_html    = st.text_area("HTML Body (full HTML document)",
                                      value=db_html, height=520, key=f"ed_html_{is_offer}",
                                      help="Paste your complete HTML email here.")
            ed_plain   = st.text_area("Plain Text Fallback",
                                      value=db_plain, height=160, key=f"ed_plain_{is_offer}")

            btn_save, btn_reset = st.columns(2)
            with btn_save:
                if st.button("Save Template", type="primary", use_container_width=True):
                    with get_db_session() as db:
                        SystemSetting.set(db, save_subject_key, ed_subject)
                        SystemSetting.set(db, save_html_key,    ed_html)
                        SystemSetting.set(db, save_plain_key,   ed_plain)
                        db.commit()
                    st.success("Template saved! Used automatically on next send.")
                    st.rerun()
            with btn_reset:
                if st.button("Reset to Default", use_container_width=True):
                    with get_db_session() as db:
                        if is_offer:
                            SystemSetting.set(db, "offer_subject", emailer.OFFER_LETTER_SUBJECT)
                            SystemSetting.set(db, "offer_html",    emailer.OFFER_LETTER_HTML)
                            SystemSetting.set(db, "offer_plain",   emailer.OFFER_LETTER_PLAIN)
                        else:
                            SystemSetting.set(db, "confirm_subject", emailer.CONFIRM_EMAIL_SUBJECT)
                            SystemSetting.set(db, "confirm_html",    emailer.CONFIRM_EMAIL_HTML)
                            SystemSetting.set(db, "confirm_plain",   emailer.CONFIRM_EMAIL_PLAIN)
                        db.commit()
                    st.success("Reset to built-in default.")
                    st.rerun()

        with preview_col:
            st.markdown("**Live Preview** *(with sample data)*")
            st.caption(f"Sample substitution: {sample_vars}")
            # Substitute placeholders safely; show raw HTML if substitution fails
            try:
                preview_html = ed_html.format(**sample_vars)
            except (KeyError, ValueError):
                preview_html = ed_html
            # Render in sandboxed iframe
            components.html(preview_html, height=700, scrolling=True)
