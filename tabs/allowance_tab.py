"""Allowance tab for generating and sending Allowance PDFs"""

import streamlit as st
from utils.excel_handler import load_excel_file
from utils.pdf_generator import create_allowance_pdf
from config.constants import ALLOWANCE_REQUIRED_COLUMNS
from tabs.shared_ui import (
    render_file_upload,
    render_data_preview,
    process_documents,
    render_results
)


def render_allowance_tab():
    """Render the Allowance tab"""

    # Get dry run mode from session state
    dry_run = st.session_state.get('dry_run_mode', False)

    # Main content
    uploaded_file = render_file_upload('ALLOWANCE')

    if uploaded_file:
        try:
            # Load Excel data
            df = load_excel_file(uploaded_file)

            # Validate and preview data
            is_valid, errors = render_data_preview(df, ALLOWANCE_REQUIRED_COLUMNS)

            if is_valid:
                # Process button
                if st.button("Generate Allowance Documents", key="process_allowance", type="primary"):
                    results_df = process_documents(
                        df,
                        'ALLOWANCE',
                        create_allowance_pdf,
                        dry_run=dry_run
                    )

                    if results_df is not None:
                        st.session_state.allowance_results = results_df

        except Exception as e:
            st.error(f"Error loading file: {e}")

    # Display results if available
    if 'allowance_results' in st.session_state:
        st.divider()
        render_results(st.session_state.allowance_results, dry_run, "allowance")

        if st.button("Clear Results", key="clear_allowance_results"):
            del st.session_state.allowance_results
            st.rerun()
