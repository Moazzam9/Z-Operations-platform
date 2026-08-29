# Zynvex Solutions — Operations & Offer Letter Portal (Streamlit Edition)

A complete, production-ready full-stack web application built entirely using **Streamlit** and **pure SQLAlchemy**. The portal manages candidate records in a SQLite database, generates individual candidate offer letter PDFs, performs aggressive file compression using Ghostscript and qpdf, executes bulk email delivery, and generates WhatsApp pre-filled confirmation redirects.

---

## 🌟 Key Features

1. **Dashboard Overview**: Access metrics for candidates (total, pending, emailed, confirmed), system disk usage for active temp session files, and a visual workflow wizard.
2. **Strict Storage Boundaries**:
   - **Database (SQLite)**: Permanent candidate records, SMTP settings, WhatsApp links, and email templates persist inside `instance/zynvex_portal.db`.
   - **Session Temp Folders**: PDF files, uploads, and archives are kept in session-specific directories (`tempfile.mkdtemp()`) stored in `st.session_state.temp_dir` and automatically cleared when sessions expire or when clicking the **Clear Session Temp Files** button.
3. **CSV Parsing & Cleaning**: Checks for duplicate email/phone numbers, normalizes role listings, automatically assigns sequential internship IDs, and deletes the uploaded CSV immediately after database import.
4. **Offer Letter Generator**: Downloads and caches Google Poppins fonts automatically, fits names onto the canvas dynamically with wrap protection, and formats the letter text and badge elements.
5. **Aggressive Compressor**: Downsamples PDFs to 150 DPI and linearizes object streams, yielding up to 75% size reductions.
6. **Robust Bulk Mailer**: Dispatches candidate offer letters (with attachment) and WhatsApp confirmation invites using a synchronous progress bar interface.
7. **Sequence Integrity Check**: Actively compares files in the temporary session directory against candidate profiles in the database to flag missing letters.
8. **WhatsApp confirmation CTA**: Admin buttons trigger custom redirections with pre-filled candidate messages and specific role links.
9. **Standalone CSV WhatsApp Invites**: Upload a CSV directly containing candidates and their corresponding WhatsApp group links. These records are held in memory only for the current session, keeping them completely separate from the main candidate database.

---

## 📋 Prerequisites

To run the application, you must have:
1. **Python 3.8+**
2. **Ghostscript** (Required for PDF compression):
   - **Windows**: Download and install Ghostscript (e.g., [Ghostscript Downloads](https://www.ghostscript.com/releases/gsdnld.html)). Make sure `gs` (or `gswin64c.exe`) is in your system environment variable `PATH`.
   - **Linux**: Install via package manager: `sudo apt-get update && sudo apt-get install -y ghostscript`
3. **QPDF** (Required for PDF structure layout cleanup):
   - **Windows**: Download and add to your system `PATH` (e.g., [QPDF Releases](https://github.com/qpdf/qpdf/releases)).
   - **Linux**: Install via package manager: `sudo apt-get install -y qpdf`

---

## ⚙️ Installation & Setup

1. **Extract/Clone** this repository into your workspace directory.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Launch the Portal**:
   ```bash
   streamlit run app.py
   ```
4. Access the web interface in your browser at the default address shown by Streamlit:
   ```
   http://localhost:8501
   ```

---

## 🚀 Operations Workflows

### Primary Workflow: Offer Letter Operations
1. **Configure Settings**: Go to **System Settings** -> Enter SMTP credentials -> Verify role-based default WhatsApp group links.
2. **Import Candidates**: Go to **Candidate Management** -> Upload candidate CSV. Duplicates are skipped and new candidates are assigned sequential IDs. CSV is deleted immediately.
3. **Upload Template & Generate**: Go to **Dashboard Overview** -> Upload PDF template -> Click **Generate for All Pending**.
4. **Compress (Optional)**: Click **Run Bulk Compression** on the Dashboard (requires Ghostscript).
5. **Bulk Email / Download**: Click **Send Bulk Offer Letters** or click **Download ZIP**.
6. **WhatsApp Redirection**: Go to **Candidate Management** -> Select candidate in the Operations dropdown -> Click **Open WhatsApp prefilled Confirmation Redirect** or **Mail Group Invite** to send role group link emails.

### Standalone Workflow: Ad-hoc CSV WhatsApp Invites
1. Navigate to the **CSV WhatsApp Invites** page in the sidebar.
2. Upload a CSV file containing candidates. The CSV must have these column headers: `Full Name`, `Email Address`, `Internship Role`, `Internship ID`, `WhatsApp Link`. (Optional: `Phone Number`).
3. The uploaded candidates list appears in the session table.
4. **Send in Bulk**: Check the select box next to candidates and click **Email Group Invites to Selected**. The system sends seat confirmation emails replacing `{group_link}` with the link provided in the candidate's CSV row.
5. **WhatsApp Redirection**: Scroll to individual operations -> Select candidate -> Click **Open WhatsApp redirect** to open WhatsApp Web containing a pre-filled invitation template with their unique ID and CSV-parsed link.
6. **Wipe / Upload New**: Click upload to load a different spreadsheet. The previous session list is immediately replaced.

---

## ☁️ Deployment Instructions

### Option 1: Streamlit Community Cloud (Easiest)
1. Push your codebase to a private/public GitHub repository.
2. Connect your GitHub account to [Streamlit Share](https://share.streamlit.io/).
3. Click **New app**, select your repository, branch, and set main file to `app.py`.
4. Under **Settings -> Secrets**, paste any environment variables (e.g. SMTP passwords or database details) if you want to override settings via secrets, although the portal fully supports configuring all settings inside the SQLite DB dynamically from the settings page.

### Option 2: Linux / Windows VPS (Self-Hosted)
1. Clone the repository onto your VPS server.
2. Install Python, Ghostscript, and qpdf on the server.
3. Set up a virtual environment and run:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py --server.port 80 --server.address 0.0.0.0
   ```
4. Configure Nginx as a reverse proxy if SSL/domain management is desired.
