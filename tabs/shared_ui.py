"""Shared UI components and logic for all tabs"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile
import concurrent.futures

from utils.validators import validate_excel_data, test_smtp_connection
from utils.telegram_notifier import send_session_summary


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
    Uses parallel execution for performance.
    """
    # Verify configuration
    if not dry_run:
        if not st.session_state.config_loaded:
            st.error("Please upload company configuration first!")
            return None

        if not st.session_state.smtp_email or not st.session_state.smtp_password:
            st.error("SMTP credentials not found in configuration!")
            return None

        # Test SMTP connection (keep this main thread check for fast feedback)
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

    # Prepare SMTP config for workers
    smtp_config = {}
    if not dry_run:
        smtp_config = {
            'email': st.session_state.smtp_email,
            'password': st.session_state.smtp_password,
            'server': st.session_state.get('smtp_server', 'smtp.gmail.com'),
            'port': st.session_state.get('smtp_port', 587),
            'template': st.session_state.get('email_template', {})
        }

    # Process in batches with connection reuse
    results = []
    progress_bar = st.progress(0, text="Processing documents...")

    from tabs.process_helper import process_document_batch

    # Determine chunk size for frequent updates
    # User suggested updating every 10-20 emails.
    # Smaller chunks = more frequent UI updates but slightly more connection overhead.
    # Balance: Chunk size 5-10
    
    total_docs = len(df)
    chunk_size = 10  # Update progress approx every 5-10 seconds
    
    if total_docs <= 20: 
        chunk_size = 2 # Very frequent for small batches
        
    # Adaptive delay based on volume
    delay_between_emails = 0.5
    if total_docs >= 100:
        delay_between_emails = 1.0 # Slower for large batches
    elif total_docs >= 50:
        delay_between_emails = 0.5
    else:
        delay_between_emails = 0.3 # Faster for small batches
    
    # Split dataframe into chunks
    chunks = []
    num_chunks = (len(df) // chunk_size) + (1 if len(df) % chunk_size > 0 else 0)
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = df.iloc[start:end]
        if len(chunk) > 0:
            chunks.append(chunk)

    max_workers = 3 # Cap workers to avoid Gmail rate limits
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit batch tasks
        futures = []
        for chunk in chunks:
            future = executor.submit(
                process_document_batch,
                chunk,
                document_type,
                pdf_generator_func,
                output_dir,
                logo_path,
                company_config,
                dry_run,
                smtp_config,
                delay_between_emails
            )
            futures.append(future)

        # Collect results as they complete
        completed_count = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_results = future.result()
                results.extend(batch_results)
                
                # Update progress
                # Progress is based on total RESULTS collected vs total expected
                completed_count = len(results)
                progress = min(completed_count / total_docs, 0.99)
                progress_bar.progress(progress, text=f"Processed {completed_count}/{total_docs} documents")

                # Check for quota exceeded in batch
                for result in batch_results:
                    if 'Quota Exceeded' in result.get('Message', ''):
                        st.warning("Gmail quota exceeded. Some emails may not have been sent.")
            except Exception as e:
                st.error(f"Batch processing error: {str(e)}")

        # Final progress update
        progress_bar.progress(1.0, text=f"Completed {len(results)}/{total_docs}")

    # Clean up
    progress_bar.empty()

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    # Send Telegram session summary (always, not just on failures)
    # Moved here so it only runs ONCE when processing finishes, not on every app rerun
    if not dry_run:
        sent = len(results_df[results_df['Status'] == 'Sent'])
        failed = len(results_df[results_df['Status'] == 'Failed'])
        skipped = len(results_df[results_df['Status'] == 'Skipped'])
        company_name = st.session_state.get('company_name', '')
        
        # Collect error types if any
        errors = None
        if failed > 0:
            errors = results_df[results_df['Status'] == 'Failed']['Message'].value_counts().to_dict()
            
        send_session_summary(sent, failed, skipped, company_name, document_type, errors)

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
