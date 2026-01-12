"""
Payroll System - Streamlit Application
Generate and email payslips, excess OT, and allowance documents automatically from Excel data
"""

import streamlit as st
import streamlit.components.v1 as components
import tempfile
import shutil
import atexit
import json
from pathlib import Path
from datetime import datetime

from config.constants import (
    DEFAULT_COMPANY_NAME, DEFAULT_FOOTER_TEXT,
    DEFAULT_DOCUMENT_ID, DEFAULT_EFFECTIVITY_DATE,
    DEFAULT_LOGO_PATH
)

from tabs.payslip_tab import render_payslip_tab
from tabs.excess_ot_tab import render_excess_ot_tab
from tabs.allowance_tab import render_allowance_tab


# ---------- TEMP FILE CLEANUP ----------

def cleanup_old_temp_dirs():
    """Clean up old temporary directories created by this app"""
    try:
        temp_base = Path(tempfile.gettempdir())
        current_time = datetime.now()

        # Find all temp directories older than 24 hours
        for temp_dir in temp_base.glob("tmp*"):
            if temp_dir.is_dir():
                try:
                    # Check if directory is older than 24 hours
                    dir_mtime = datetime.fromtimestamp(temp_dir.stat().st_mtime)
                    age_hours = (current_time - dir_mtime).total_seconds() / 3600

                    # If older than 24 hours and contains document PDFs, clean it up
                    if age_hours > 24:
                        pdf_files = list(temp_dir.glob("*.pdf"))
                        if pdf_files:  # Only delete if it looks like our temp dir
                            shutil.rmtree(temp_dir, ignore_errors=True)
                except (OSError, PermissionError):
                    # Skip directories we can't access
                    pass
    except Exception:
        # Don't fail app startup if cleanup fails
        pass


def cleanup_temp_dir(temp_dir_path):
    """Safely cleanup a temporary directory"""
    if temp_dir_path and Path(temp_dir_path).exists():
        try:
            # Only cleanup if it's in the system temp directory (safety check)
            if str(Path(temp_dir_path).parent) == tempfile.gettempdir():
                shutil.rmtree(temp_dir_path, ignore_errors=True)
        except Exception:
            pass


# Cleanup old temp directories on app startup
cleanup_old_temp_dirs()


# Register cleanup on exit
@atexit.register
def cleanup_on_exit():
    """Cleanup temp directory when app exits"""
    if hasattr(st.session_state, 'temp_dir') and st.session_state.temp_dir:
        cleanup_temp_dir(st.session_state.temp_dir)


# ---------- PAGE CONFIGURATION ----------

st.set_page_config(
    page_title="Payroll System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- HIDE STREAMLIT BRANDING ----------

st.markdown("""
<style>
    /* Hide Fork button and GitHub icon (toolbar action buttons) */
    [data-testid="stToolbarActionButton"] {
        display: none !important;
    }

    /* Hide footer */
    footer {
        visibility: hidden !important;
    }

    /* Hide profile preview */
    div[class*="_profilePreview_"],
    a[href*="share.streamlit.io/user"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }

    /* Hide Streamlit Cloud badge */
    a[href*="streamlit.io/cloud"],
    div[class*="_viewerBadge_"],
    a[class*="_viewerBadge_"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }

    /* Hide app creator avatar */
    img[data-testid="appCreatorAvatar"],
    img[alt="App Creator Avatar"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE INITIALIZATION ----------

def init_session_state():
    """Initialize session state variables"""
    if 'smtp_email' not in st.session_state:
        st.session_state.smtp_email = ""
    if 'smtp_password' not in st.session_state:
        st.session_state.smtp_password = ""
    if 'smtp_validated' not in st.session_state:
        st.session_state.smtp_validated = False
    if 'temp_dir' not in st.session_state:
        # Create a persistent temp directory for the session
        try:
            st.session_state.temp_dir = tempfile.mkdtemp(prefix="doc_automation_")
        except Exception:
            # Fallback to None if temp directory creation fails
            st.session_state.temp_dir = None
    if 'company_name' not in st.session_state:
        st.session_state.company_name = DEFAULT_COMPANY_NAME
    if 'footer_text' not in st.session_state:
        st.session_state.footer_text = DEFAULT_FOOTER_TEXT
    if 'document_id' not in st.session_state:
        st.session_state.document_id = DEFAULT_DOCUMENT_ID
    if 'effectivity_date' not in st.session_state:
        st.session_state.effectivity_date = DEFAULT_EFFECTIVITY_DATE
    if 'company_logo_path' not in st.session_state:
        st.session_state.company_logo_path = DEFAULT_LOGO_PATH
    if 'config_loaded' not in st.session_state:
        st.session_state.config_loaded = False
    if 'output_directory' not in st.session_state:
        st.session_state.output_directory = "./output"
    if 'smtp_server' not in st.session_state:
        st.session_state.smtp_server = "smtp.gmail.com"
    if 'smtp_port' not in st.session_state:
        st.session_state.smtp_port = 587
    if 'dry_run_mode' not in st.session_state:
        st.session_state.dry_run_mode = False


init_session_state()


# ---------- SIDEBAR ----------

with st.sidebar:
    st.title("Payroll System")

    # Templates Section
    with st.expander("Download Templates", expanded=False):
        # Company config template
        with st.container(border=True):
            st.markdown("**Company Config Template**")
            st.markdown("Basic company setup details and configuration file.")
            config_template_path = "templates/company_config.json"
            if Path(config_template_path).exists():
                with open(config_template_path, "rb") as template_file:
                    st.download_button(
                        label="Company Config",
                        data=template_file,
                        file_name="company_config.json",
                        mime="application/json",
                        type="primary",
                        help="Download template to fill in your company details",
                        width='stretch'
                    )

        # Excel templates
        with st.container(border=True):
            st.markdown("**Excel Templates**")
            st.markdown("Standard Excel templates used for payroll computation.")

            # Payroll template
            payroll_template_path = "templates/payroll_template.xlsx"
            if Path(payroll_template_path).exists():
                with open(payroll_template_path, "rb") as template_file:
                    st.download_button(
                        label="Payroll",
                        data=template_file,
                        file_name="payroll_template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        help="Download Excel template for payroll data",
                        width='stretch'
                    )

            # Excess OT template
            ot_template_path = "templates/excess_ot_template.xlsx"
            if Path(ot_template_path).exists():
                with open(ot_template_path, "rb") as template_file:
                    st.download_button(
                        label="Excess OT",
                        data=template_file,
                        file_name="excess_ot_template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        help="Download Excel template for excess overtime data",
                        width='stretch'
                    )

            # Allowance template
            allowance_template_path = "templates/allowance_template.xlsx"
            if Path(allowance_template_path).exists():
                with open(allowance_template_path, "rb") as template_file:
                    st.download_button(
                        label="Allowance",
                        data=template_file,
                        file_name="allowance_template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        help="Download Excel template for allowance data",
                        width='stretch'
                    )

    # Settings Section
    with st.expander("Settings", expanded=False):
        # Configuration Container
        with st.container(border=True):
            st.subheader("Configuration")

            # Show current config if loaded, otherwise show uploader
            if st.session_state.get('config_loaded', False) and st.session_state.company_name:
                st.caption("**Company:** " + st.session_state.company_name)
                st.caption("**Email:** " + st.session_state.smtp_email)

                if st.button("Clear Configuration", help="Clear configuration", width='stretch'):
                    st.session_state.company_name = ""
                    st.session_state.footer_text = ""
                    st.session_state.document_id = ""
                    st.session_state.effectivity_date = ""
                    st.session_state.smtp_email = ""
                    st.session_state.smtp_password = ""
                    st.session_state.smtp_validated = False
                    st.session_state.config_loaded = False
                    st.rerun()
            else:
                # Config file upload
                config_file = st.file_uploader(
                    "Upload Config File",
                    type=['json'],
                    help="Upload your company_config.json file (download template above)",
                    key="company_config_uploader"
                )

                # Load config if uploaded
                if config_file is not None:
                    try:
                        config_data = json.load(config_file)

                        # Validate SMTP nested structure
                        smtp_config = config_data.get('smtp', {})
                        if not smtp_config.get('email') or not smtp_config.get('password'):
                            st.error("SMTP configuration incomplete. Both email and password are required.")
                        else:
                            # Load company details
                            st.session_state.company_name = config_data.get('company_name', '')
                            st.session_state.footer_text = config_data.get('footer_text', '')
                            st.session_state.document_id = config_data.get('document_id', '')
                            st.session_state.effectivity_date = config_data.get('effectivity_date', '')

                            # Load SMTP credentials
                            st.session_state.smtp_email = smtp_config.get('email', '')
                            st.session_state.smtp_password = smtp_config.get('password', '')

                            st.session_state.config_loaded = True
                            st.rerun()

                    except json.JSONDecodeError:
                        st.error("Invalid JSON file. Please check the file format.")
                    except Exception as e:
                        st.error(f"Error loading config: {str(e)}")

        # Logo Container
        with st.container(border=True):
            st.subheader("Company Logo")

            # Check if custom logo is uploaded
            has_custom_logo = (
                st.session_state.get('company_logo_path') and
                st.session_state.company_logo_path != 'assets/logo.png' and
                Path(st.session_state.company_logo_path).exists()
            )

            if has_custom_logo:
                st.caption("**Status:** Custom logo uploaded")

                if st.button("Clear Logo", help="Remove custom logo", width='stretch'):
                    st.session_state.company_logo_path = 'assets/logo.png'
                    st.rerun()
            else:
                company_logo = st.file_uploader(
                    "Upload Logo (optional)",
                    type=['png', 'jpg', 'jpeg'],
                    help="Appears at top of documents"
                )

                if company_logo:
                    # Ensure temp_dir exists
                    if not st.session_state.temp_dir:
                        st.session_state.temp_dir = tempfile.mkdtemp(prefix="doc_automation_")

                    # Save logo to temp location
                    logo_path = Path(st.session_state.temp_dir) / "custom_logo.png"
                    with open(logo_path, "wb") as f:
                        f.write(company_logo.getbuffer())
                    st.session_state.company_logo_path = str(logo_path)
                    st.rerun()

        # Processing Mode Container
        with st.container(border=True):
            st.subheader("Processing Mode")
            dry_run = st.checkbox(
                "Dry Run Mode",
                value=False,
                help="Generate PDFs without sending emails",
                key="global_dry_run"
            )

            if dry_run:
                output_dir = st.text_input(
                    "Output Directory",
                    value="./output",
                    help="Directory to save generated PDFs",
                    key="global_output_dir"
                )
                st.session_state.output_directory = output_dir

            # Store dry run state
            st.session_state.dry_run_mode = dry_run

    # Gmail App Password Guide
    with st.expander("Gmail App Password Guide"):
        st.markdown("""
        **1. Enable 2-Factor Authentication**
        - Go to [Google Account](https://myaccount.google.com/)
        - Navigate to Security
        - Enable 2-Step Verification

        **2. Generate App Password**
        - Search for "App passwords"
        - Select "Mail" and your device
        - Copy the 16-character password

        **3. Use in config file**
        - Paste the app password in the `smtp.password` field
        - Note: Use app password, not regular password!
        """)


# ---------- MAIN APPLICATION ----------

# Create tabs
tab1, tab2, tab3 = st.tabs([
    "Payslips",
    "Excess OT",
    "Allowance"
])

# Render each tab
with tab1:
    render_payslip_tab()

with tab2:
    render_excess_ot_tab()

with tab3:
    render_allowance_tab()

# ---------- HIDE STREAMLIT CLOUD BRANDING (via component) ----------
# This runs at the end to ensure elements are loaded
components.html("""
<script>
    const topDoc = window.top.document;

    // Inject CSS into top document
    const css = `
        [class*="_profilePreview_"] { display: none !important; }
        [class*="_profileContainer_"] { display: none !important; }
        a[href*="streamlit.io/cloud"] { display: none !important; }
        [class*="_viewerBadge_"] { display: none !important; }
    `;
    const style = document.createElement('style');
    style.textContent = css;
    try { topDoc.head.appendChild(style); } catch(e) {}

    // Hide elements via JS (backup for CSS)
    function hideElements() {
        try {
            topDoc.querySelectorAll('[class*="_profilePreview_"], [class*="_profileContainer_"]').forEach(el => el.style.display = 'none');
            topDoc.querySelectorAll('a[href*="streamlit.io/cloud"]').forEach(el => el.style.display = 'none');
            topDoc.querySelectorAll('[class*="_viewerBadge_"]').forEach(el => el.style.display = 'none');
        } catch(e) {}
    }

    setInterval(hideElements, 500);
</script>
""", height=0, scrolling=False)
