import os
import time
import pandas as pd
from utils.email_sender import EmailSender
from utils.telegram_notifier import send_error_alert

def process_single_document(row, document_type, pdf_generator_func, output_dir, logo_path, company_config, dry_run, smtp_config):
    """
    Process a single document (generate PDF and optionally send email)
    Designed to be run in a separate thread.
    """
    # Get employee identifier
    if document_type == 'PAYSLIP':
        identifier = f"{row.get('EmployeeNumber', 'N/A')} - {row.get('Name', 'N/A')}"
    elif document_type == 'EXCESS_OT':
        identifier = f"{row.get('Name', 'N/A')}"
    elif document_type == 'ALLOWANCE':
        identifier = f"{row.get('EMP ID NO', 'N/A')} - {row.get('Name', 'N/A')}"
    else:
        identifier = "Unknown"

    result = {
        'Identifier': identifier,
        'PDF': 'N/A',
        'Status': 'Processing',
        'Message': ''
    }

    try:
        # Generate PDF
        pdf_path = pdf_generator_func(row, output_dir, logo_path, company_config)
        result['PDF'] = os.path.basename(pdf_path)
        result['Status'] = 'Generated' if dry_run else 'Processing'

        # Send email if not dry run
        if not dry_run:
            email = row.get('Email', '')
            if pd.notna(email) and email:
                # Instantiate a NEW sender for this thread
                # This ensures thread safety and avoids race conditions on the socket
                sender = EmailSender(
                    smtp_config['email'],
                    smtp_config['password'],
                    smtp_config.get('server', 'smtp.gmail.com'),
                    smtp_config.get('port', 587),
                    smtp_config.get('template', {})
                )
                
                try:
                    # Connect
                    success, message = sender.connect()
                    if not success:
                        result['Status'] = 'Failed'
                        result['Message'] = f"Connection failed: {message}"
                        # Send Telegram alert for connection failure
                        send_error_alert("CONNECTION", message)
                        return result

                    # Send
                    doc_type_name = document_type.replace('_', ' ').title()
                    success, message, quota_exceeded = sender.send_document(row, pdf_path, doc_type_name)

                    if success:
                        result['Status'] = 'Sent'
                        result['Message'] = 'Email sent successfully'
                    else:
                        result['Status'] = 'Failed'
                        result['Message'] = message
                        if quota_exceeded:
                            result['Message'] += " (Quota Exceeded)"
                            send_error_alert("QUOTA", "Gmail daily sending limit reached")
                        else:
                            send_error_alert("SMTP", message)
                finally:
                    # Always disconnect to prevent file descriptor leaks
                    sender.disconnect()

            else:
                result['Status'] = 'Skipped'
                result['Message'] = 'No valid email address'

    except Exception as e:
        result['Status'] = 'Error'
        result['Message'] = str(e)

    return result


def process_document_batch(rows_df, document_type, pdf_generator_func, output_dir,
                           logo_path, company_config, dry_run, smtp_config,
                           delay_seconds=0.5):
    """
    Process a batch of documents with a single SMTP connection.
    This reduces connection overhead and helps avoid rate limiting.

    Args:
        rows_df: DataFrame chunk containing rows to process
        document_type: Type of document (PAYSLIP, EXCESS_OT, ALLOWANCE)
        pdf_generator_func: Function to generate PDF
        output_dir: Directory for output files
        logo_path: Path to company logo
        company_config: Company configuration dict
        dry_run: If True, only generate PDFs without sending emails
        smtp_config: SMTP configuration dict
        delay_seconds: Delay between emails to avoid rate limiting

    Returns:
        list: List of result dictionaries
    """
    results = []
    sender = None
    quota_exceeded = False

    # Create ONE sender for the entire batch (if not dry run)
    if not dry_run:
        sender = EmailSender(
            smtp_config['email'],
            smtp_config['password'],
            smtp_config.get('server', 'smtp.gmail.com'),
            smtp_config.get('port', 587),
            smtp_config.get('template', {})
        )

        success, message = sender.connect()
        if not success:
            # Return all rows as failed if can't connect initially
            send_error_alert("CONNECTION", message)
            for idx, row in rows_df.iterrows():
                if document_type == 'PAYSLIP':
                    identifier = f"{row.get('EmployeeNumber', 'N/A')} - {row.get('Name', 'N/A')}"
                elif document_type == 'EXCESS_OT':
                    identifier = f"{row.get('Name', 'N/A')}"
                elif document_type == 'ALLOWANCE':
                    identifier = f"{row.get('EMP ID NO', 'N/A')} - {row.get('Name', 'N/A')}"
                else:
                    identifier = "Unknown"
                results.append({
                    'Identifier': identifier,
                    'PDF': 'N/A',
                    'Status': 'Failed',
                    'Message': f"Initial connection failed: {message}"
                })
            return results

    try:
        for idx, row in rows_df.iterrows():
            # Get employee identifier
            if document_type == 'PAYSLIP':
                identifier = f"{row.get('EmployeeNumber', 'N/A')} - {row.get('Name', 'N/A')}"
            elif document_type == 'EXCESS_OT':
                identifier = f"{row.get('Name', 'N/A')}"
            elif document_type == 'ALLOWANCE':
                identifier = f"{row.get('EMP ID NO', 'N/A')} - {row.get('Name', 'N/A')}"
            else:
                identifier = "Unknown"

            result = {
                'Identifier': identifier,
                'PDF': 'N/A',
                'Status': 'Processing',
                'Message': ''
            }

            try:
                # Generate PDF
                pdf_path = pdf_generator_func(row, output_dir, logo_path, company_config)
                result['PDF'] = os.path.basename(pdf_path)
                result['Status'] = 'Generated' if dry_run else 'Processing'

                # Send email if not dry run and quota not exceeded
                if not dry_run and not quota_exceeded:
                    email = row.get('Email', '')
                    if pd.notna(email) and email:
                        doc_type_name = document_type.replace('_', ' ').title()

                        # Use send_document_with_retry for automatic reconnection
                        success, message, quota = sender.send_document_with_retry(
                            row, pdf_path, doc_type_name
                        )

                        if success:
                            result['Status'] = 'Sent'
                            result['Message'] = 'Email sent successfully'
                        else:
                            result['Status'] = 'Failed'
                            result['Message'] = message
                            if quota:
                                result['Message'] += " (Quota Exceeded)"
                                send_error_alert("QUOTA", "Gmail daily sending limit reached")
                                quota_exceeded = True
                            else:
                                send_error_alert("SMTP", message)

                        # Add delay between emails to avoid rate limiting
                        if not quota_exceeded:
                            time.sleep(delay_seconds)
                    else:
                        result['Status'] = 'Skipped'
                        result['Message'] = 'No valid email address'

            except Exception as e:
                result['Status'] = 'Error'
                result['Message'] = str(e)

            results.append(result)

    finally:
        # Always disconnect
        if sender:
            sender.disconnect()

    return results
