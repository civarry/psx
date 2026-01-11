"""Shared UI components and logic for all tabs"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile

from utils.validators import validate_email, validate_excel_data, test_smtp_connection
from utils.email_sender import EmailSender


def render_file_upload(document_type):
    """
    Render file upload section

    Args:
        document_type: Type of document (PAYSLIP, EXCESS_OT, ALLOWANCE)

    Returns:
        DataFrame or None: Loaded data if successful
    """
    st.header(f"{document_type.replace('_', ' ').title()} Automation")

    uploaded_file = st.file_uploader(
        "Upload Excel File",
        type=['xlsx'],
        help="Upload an Excel file with employee data",
        key=f"file_upload_{document_type}"
    )

    if uploaded_file:
        return uploaded_file

    return None


def render_data_preview(df, required_columns):
    """
    Render data preview with validation

    Args:
        df: DataFrame to preview
        required_columns: List of required column names

    Returns:
        tuple: (is_valid, errors)
    """
    # Validate data
    is_valid, errors = validate_excel_data(df, required_columns)

    if not is_valid:
        st.error("Validation Errors:")
        for error in errors:
            st.error(f"- {error}")
        return False, errors

    st.success("Data validation passed!")

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Employees", len(df))
    with col2:
        email_col = 'Email' if 'Email' in df.columns else None
        if email_col:
            valid_emails = df[email_col].notna().sum()
            st.metric("Valid Emails", valid_emails)
    with col3:
        if 'Total Pay' in df.columns:
            total_amount = df['Total Pay'].sum()
            st.metric("Total Amount", f"₱{total_amount:,.2f}")
        elif 'NetPay' in df.columns:
            total_amount = df['NetPay'].sum()
            st.metric("Total Amount", f"₱{total_amount:,.2f}")

    # Display preview
    with st.expander("Data Preview", expanded=True):
        st.dataframe(df.head(10), width='stretch')

    return True, []


def process_documents(df, document_type, pdf_generator_func, dry_run=False):
    """
    Process documents (generate PDFs and optionally send emails)

    Args:
        df: DataFrame with employee data
        document_type: Type of document
        pdf_generator_func: Function to generate PDFs
        dry_run: If True, only generate PDFs without sending emails

    Returns:
        DataFrame: Results with status for each employee
    """
    # Verify configuration
    if not dry_run:
        if not st.session_state.config_loaded:
            st.error("Please upload company configuration first!")
            return None

        if not st.session_state.smtp_email or not st.session_state.smtp_password:
            st.error("SMTP credentials not found in configuration!")
            return None

        # Test SMTP connection
        if not st.session_state.smtp_validated:
            with st.spinner("Testing SMTP connection..."):
                success, message = test_smtp_connection(
                    st.session_state.smtp_email,
                    st.session_state.smtp_password,
                    st.session_state.get('smtp_server', 'smtp.gmail.com'),
                    st.session_state.get('smtp_port', 587)
                )

                if not success:
                    st.error(f"SMTP connection failed: {message}")
                    return None

                st.success("SMTP connection successful!")
                st.session_state.smtp_validated = True
    else:
        # Dry run mode - verify output directory
        output_dir = st.session_state.output_directory
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                st.error(f"Failed to create output directory: {e}")
                return None

    # Start processing
    st.info(f"Processing {len(df)} documents...")

    # Prepare company config
    company_config = {
        'company_name': st.session_state.get('company_name', ''),
        'footer_text': st.session_state.get('footer_text', ''),
        'document_id': st.session_state.get('document_id', ''),
        'effectivity_date': st.session_state.get('effectivity_date', '')
    }

    # Get logo path
    logo_path = st.session_state.get('company_logo_path', 'assets/logo.png')

    # Determine output directory
    if dry_run:
        output_dir = st.session_state.output_directory
    else:
        output_dir = st.session_state.temp_dir

    # Initialize email sender if not dry run
    email_sender = None
    if not dry_run:
        email_sender = EmailSender(
            st.session_state.smtp_email,
            st.session_state.smtp_password,
            st.session_state.get('smtp_server', 'smtp.gmail.com'),
            st.session_state.get('smtp_port', 587)
        )

        success, message = email_sender.connect()
        if not success:
            st.error(f"Failed to connect to SMTP server: {message}")
            return None

    # Process each employee
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, row in df.iterrows():
        # Update progress
        progress = (idx + 1) / len(df)
        progress_bar.progress(progress)

        # Get employee identifier
        if document_type == 'PAYSLIP':
            identifier = f"{row.get('EmployeeNumber', 'N/A')} - {row.get('Name', 'N/A')}"
        elif document_type == 'EXCESS_OT':
            identifier = f"{row.get('Name', 'N/A')}"
        elif document_type == 'ALLOWANCE':
            identifier = f"{row.get('EMP ID NO', 'N/A')} - {row.get('Name', 'N/A')}"

        status_text.text(f"Processing {identifier}...")

        try:
            # Generate PDF
            pdf_path = pdf_generator_func(row, output_dir, logo_path, company_config)

            result = {
                'Identifier': identifier,
                'PDF': os.path.basename(pdf_path),
                'Status': 'Generated' if dry_run else 'Processing'
            }

            # Send email if not dry run
            if not dry_run:
                email = row.get('Email', '')
                if pd.notna(email) and email:
                    # Map document type to friendly name
                    doc_type_name = document_type.replace('_', ' ').title()
                    success, message, quota_exceeded = email_sender.send_document(row, pdf_path, doc_type_name)

                    if success:
                        result['Status'] = 'Sent'
                        result['Message'] = 'Email sent successfully'
                    else:
                        result['Status'] = 'Failed'
                        result['Message'] = message

                    # Check for quota exceeded
                    if quota_exceeded:
                        st.warning("Gmail quota exceeded. Stopping email sending.")
                        results.append(result)
                        break
                else:
                    result['Status'] = 'Skipped'
                    result['Message'] = 'No valid email address'

            results.append(result)

        except Exception as e:
            results.append({
                'Identifier': identifier,
                'PDF': 'N/A',
                'Status': 'Error',
                'Message': str(e)
            })

    # Clean up
    progress_bar.empty()
    status_text.empty()

    if email_sender:
        email_sender.disconnect()

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    return results_df


def render_results(results_df, dry_run=False, document_type=""):
    """
    Render processing results

    Args:
        results_df: DataFrame with processing results
        dry_run: If True, show dry run specific messages
        document_type: Type of document for unique keys
    """
    st.success("Processing complete!")

    # Display summary
    col1, col2, col3 = st.columns(3)

    with col1:
        if dry_run:
            generated = len(results_df[results_df['Status'] == 'Generated'])
            st.metric("PDFs Generated", generated)
        else:
            successful = len(results_df[results_df['Status'] == 'Sent'])
            st.metric("Emails Sent", successful)

    with col2:
        if not dry_run:
            failed = len(results_df[results_df['Status'].isin(['Failed', 'Skipped'])])
            st.metric("Failed/Skipped", failed)

    with col3:
        errors = len(results_df[results_df['Status'] == 'Error'])
        st.metric("Errors", errors)

    # Display results table
    st.subheader("Detailed Results")
    st.dataframe(results_df, width='stretch')

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        csv = results_df.to_csv(index=False)
        st.download_button(
            "Download Results (CSV)",
            data=csv,
            file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv',
            key=f"download_csv_{document_type}"
        )

    with col2:
        # Create ZIP of PDFs if in dry run mode
        if dry_run:
            output_dir = st.session_state.output_directory
            zip_path = os.path.join(output_dir, f"pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")

            try:
                with ZipFile(zip_path, 'w') as zipf:
                    for pdf_file in results_df['PDF']:
                        if pdf_file != 'N/A':
                            pdf_path = os.path.join(output_dir, pdf_file)
                            if os.path.exists(pdf_path):
                                zipf.write(pdf_path, pdf_file)

                with open(zip_path, 'rb') as f:
                    st.download_button(
                        "Download PDFs (ZIP)",
                        data=f,
                        file_name=os.path.basename(zip_path),
                        mime='application/zip',
                        key=f"download_zip_{document_type}"
                    )
            except Exception as e:
                st.error(f"Failed to create ZIP file: {e}")
