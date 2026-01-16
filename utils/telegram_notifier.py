"""Telegram notification utility for error alerts (privacy-safe)"""

import requests
import streamlit as st
from datetime import datetime


def get_telegram_config():
    """
    Get Telegram configuration from Streamlit secrets.
    Returns None if not configured.
    """
    try:
        bot_token = st.secrets.get("telegram", {}).get("bot_token")
        chat_id = st.secrets.get("telegram", {}).get("chat_id")
        
        if bot_token and chat_id:
            return {"bot_token": bot_token, "chat_id": chat_id}
        return None
    except Exception:
        return None


def send_telegram_message(message: str) -> bool:
    """
    Send a message to Telegram.
    
    Args:
        message: The message text to send
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    config = get_telegram_config()
    if not config:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        response = requests.post(
            url,
            data={
                "chat_id": config["chat_id"],
                "text": message,
                "parse_mode": "HTML"
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False


def send_error_alert(error_type: str, error_message: str, affected_count: int = 1):
    """
    Send an error alert to Telegram (privacy-safe, no PII).
    
    Args:
        error_type: Type of error (CONNECTION, QUOTA, AUTH, SMTP, FILE)
        error_message: Sanitized error message (no employee data)
        affected_count: Number of documents affected
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = (
        f"🚨 <b>PAYSLIP AUTOMATION ERROR</b>\n\n"
        f"<b>Type:</b> {error_type}\n"
        f"<b>Message:</b> {error_message}\n"
        f"<b>Affected:</b> {affected_count} document(s)\n"
        f"<b>Time:</b> {timestamp}"
    )
    
    send_telegram_message(message)


def send_session_summary(sent: int, failed: int, skipped: int, errors: dict = None):
    """
    Send a session summary to Telegram after processing completes.
    
    Args:
        sent: Number of emails successfully sent
        failed: Number of failed emails
        skipped: Number of skipped emails
        errors: Optional dict of error counts by type
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = sent + failed + skipped
    
    # Only send if there were failures
    if failed == 0:
        return
    
    message = (
        f"📊 <b>PAYSLIP SESSION SUMMARY</b>\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"⏭️ Skipped: {skipped}\n"
        f"📄 Total: {total}\n"
        f"⏰ Time: {timestamp}"
    )
    
    if errors:
        message += "\n\n<b>Errors by Type:</b>\n"
        for error_type, count in errors.items():
            message += f"  • {error_type}: {count}\n"
    
    send_telegram_message(message)
