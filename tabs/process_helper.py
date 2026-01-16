import os
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
