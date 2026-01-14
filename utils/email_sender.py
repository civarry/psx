"""Email sending functionality for payslips"""

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Tuple


class EmailSender:
    """Handle SMTP email sending for payslips"""

    # Default email template values
    DEFAULT_EMAIL_TEMPLATE = {
        "greeting": "Hi",
        "message": "Please find attached your document.",
        "footer": "This is a system-generated email. If you have any questions, please contact Finance/Accounting Department.",
        "signature": "Best regards,\nFinance/Accounting Department"
    }

    def __init__(self, email: str, password: str,
                 smtp_server: str = "smtp.gmail.com",
                 smtp_port: int = 587,
                 email_template: dict = None):
        """
        Initialize email sender

        Args:
            email: SMTP email address
            password: SMTP password (App Password for Gmail)
            smtp_server: SMTP server address
            smtp_port: SMTP port number
            email_template: Optional dict with greeting, message, footer, signature
        """
        # Sanitize email - remove any whitespace/non-breaking spaces
        self.email = "".join(c for c in email if c.isalnum() or c in '@._-')
        # Remove ALL non-alphanumeric characters from app password (handles any whitespace including U+00A0)
        self.password = "".join(c for c in password if c.isalnum())
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp = None
        self.email_template = email_template or {}

    def connect(self) -> Tuple[bool, str]:
        """
        Establish SMTP connection

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp.starttls()
            self.smtp.login(self.email, self.password)
            return True, "Connected successfully"
        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Check your email and app password."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def disconnect(self):
        """Close SMTP connection"""
        if self.smtp:
            try:
                self.smtp.quit()
            except:
                pass  # Ignore errors when closing
            self.smtp = None

    def send_document(self, row, pdf_path: str, document_type: str = "Payslip") -> Tuple[bool, str, bool]:
        """
        Send document email with PDF attachment

        Args:
            row: pandas Series with employee data (must have Email, Name, and Period columns)
            pdf_path: Path to PDF file
            document_type: Type of document (Payslip, Excess OT, Allowance)

        Returns:
            Tuple[bool, str, bool]: (success, message, quota_exceeded)
                - success: True if email sent successfully
                - message: Status message
                - quota_exceeded: True if Gmail daily quota was exceeded
        """
        try:
            # Check if PDF exists
            if not Path(pdf_path).exists():
                return False, f"PDF file not found: {pdf_path}", False

            # Check if SMTP connection is established
            if not self.smtp:
                return False, "Not connected to SMTP server", False

            # Helper to sanitize text (remove non-breaking spaces)
            def sanitize(text):
                if text:
                    return str(text).replace('\xa0', ' ').replace('\u00a0', ' ')
                return text

            # Build email message
            to_email = row["Email"]
            name = sanitize(row["Name"])

            # Get period field based on document type
            if "PayrollPeriod" in row.index:
                period = sanitize(row["PayrollPeriod"])
            elif "Period" in row.index:
                period = sanitize(row["Period"])
            else:
                period = "current period"

            msg = EmailMessage()
            msg["Subject"] = f"{document_type} for {period}"
            msg["From"] = self.email
            msg["To"] = to_email

            # Build email body from template with fallbacks
            greeting = sanitize(self.email_template.get("greeting") or self.DEFAULT_EMAIL_TEMPLATE["greeting"])
            message = sanitize(self.email_template.get("message") or self.DEFAULT_EMAIL_TEMPLATE["message"])
            footer = sanitize(self.email_template.get("footer") or self.DEFAULT_EMAIL_TEMPLATE["footer"])
            signature = sanitize(self.email_template.get("signature") or self.DEFAULT_EMAIL_TEMPLATE["signature"])

            # Build email body (document type and period are auto-appended)
            body = (
                f"{greeting} {name},\n\n"
                f"{message} ({document_type} for {period})\n\n"
                f"{footer}\n\n"
                f"{signature}"
            )
            msg.set_content(body)

            # Attach PDF
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            filename = Path(pdf_path).name
            msg.add_attachment(
                pdf_data,
                maintype="application",
                subtype="pdf",
                filename=filename
            )

            # Send email
            self.smtp.send_message(msg)
            return True, f"Sent to {to_email}", False

        except smtplib.SMTPSenderRefused as e:
            # Check if this is a quota exceeded error
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg or "554" in str(e) or "450" in str(e):
                return False, "QUOTA_EXCEEDED: Gmail daily sending limit reached", True
            return False, f"SMTP error: {str(e)}", False
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}", False
        except Exception as e:
            return False, f"Error: {str(e)}", False

    def send_payslip(self, row, pdf_path: str) -> Tuple[bool, str, bool]:
        """
        Send payslip email with PDF attachment (backward compatibility)

        Args:
            row: pandas Series with employee data
            pdf_path: Path to PDF file

        Returns:
            Tuple[bool, str, bool]: (success, message, quota_exceeded)
        """
        return self.send_document(row, pdf_path, "Payslip")
