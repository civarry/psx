"""Excess OT tab for generating and sending Excess OT PDFs"""

import streamlit as st
from utils.excel_handler import load_excel_file
from utils.pdf_generator import create_excess_ot_pdf
from config.constants import EXCESS_OT_REQUIRED_COLUMNS
from tabs.shared_ui import (
    render_file_upload,
    render_data_preview,
    process_documents,
    render_results
)


def render_excess_ot_tab():
    """Render the Excess OT tab"""

    # Get dry run mode from session state
    dry_run = st.session_state.get('dry_run_mode', False)

    # Main content
    uploaded_file = render_file_upload('EXCESS_OT')

    if uploaded_file:
        try:
            # Load Excel data
            df = load_excel_file(uploaded_file)

            # Validate and preview data
            is_valid, errors = render_data_preview(df, EXCESS_OT_REQUIRED_COLUMNS)

            if is_valid:
                # Process button
                if st.button("Generate Excess OT Documents", key="process_excess_ot", type="primary"):
                    results_df = process_documents(
                        df,
                        'EXCESS_OT',
                        create_excess_ot_pdf,
                        dry_run=dry_run
                    )

                    if results_df is not None:
                        st.session_state.excess_ot_results = results_df

        except Exception as e:
            st.error(f"Error loading file: {e}")

    # Display results if available
    if 'excess_ot_results' in st.session_state:
        st.divider()
        render_results(st.session_state.excess_ot_results, dry_run, "excess_ot")

        if st.button("Clear Results", key="clear_excess_ot_results"):
            del st.session_state.excess_ot_results
            st.rerun()
