"""Payslip tab for generating and sending payslip PDFs"""

import streamlit as st
from utils.excel_handler import load_excel_file
from utils.pdf_generator import create_payslip_pdf
from config.constants import PAYSLIP_REQUIRED_COLUMNS
from tabs.shared_ui import (
    render_file_upload,
    render_data_preview,
    process_documents,
    render_results
)


def render_payslip_tab():
    """Render the Payslip tab"""

    # Get dry run mode from session state
    dry_run = st.session_state.get('dry_run_mode', False)

    # Main content
    uploaded_file = render_file_upload('PAYSLIP')

    if uploaded_file:
        try:
            # Load Excel data
            df = load_excel_file(uploaded_file)

            # Validate and preview data
            is_valid, errors = render_data_preview(df, PAYSLIP_REQUIRED_COLUMNS)

            if is_valid:
                # Process button
                if st.button("Generate Payslips", key="process_payslip", type="primary"):
                    results_df = process_documents(
                        df,
                        'PAYSLIP',
                        create_payslip_pdf,
                        dry_run=dry_run
                    )

                    if results_df is not None:
                        st.session_state.payslip_results = results_df

        except Exception as e:
            st.error(f"Error loading file: {e}")

    # Display results if available
    if 'payslip_results' in st.session_state:
        st.divider()
        render_results(st.session_state.payslip_results, dry_run, "payslip")

        if st.button("Clear Results", key="clear_payslip_results"):
            del st.session_state.payslip_results
            st.rerun()
