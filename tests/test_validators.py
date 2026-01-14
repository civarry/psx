import pytest
import pandas as pd
from utils.validators import validate_email, validate_excel_data, test_smtp_connection as check_smtp_connection

def test_validate_email():
    """Test email validation regex"""
    assert validate_email("test@example.com") is True
    assert validate_email("user.name+tag@company.co.uk") is True
    assert validate_email("invalid-email") is False
    assert validate_email("user@domain") is False  # Missing TLD
    assert validate_email("") is False
    assert validate_email(None) is False

def test_validate_excel_data_valid():
    """Test validation with valid data"""
    df = pd.DataFrame({
        "EmployeeNumber": ["001", "002"],
        "Name": ["Alice", "Bob"],
        "Email": ["alice@example.com", "bob@example.com"],
        "PayrollPeriod": ["Jan 2025", "Jan 2025"],
        "NetPay": [1000, 2000]
    })
    required_cols = ["EmployeeNumber", "Name", "Email", "PayrollPeriod", "NetPay"]
    
    is_valid, errors = validate_excel_data(df, required_cols)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_excel_data_missing_cols():
    """Test validation with missing columns"""
    df = pd.DataFrame({
        "Name": ["Alice"],
        "Email": ["alice@example.com"]
    })
    required_cols = ["EmployeeNumber", "Name"]
    
    is_valid, errors = validate_excel_data(df, required_cols)
    assert is_valid is False
    assert any("Missing required columns" in err for err in errors)

def test_validate_excel_data_invalid_email():
    """Test validation with invalid emails"""
    df = pd.DataFrame({
        "Name": ["Alice"],
        "Email": ["invalid-email"]
    })
    required_cols = ["Name", "Email"]
    
    is_valid, errors = validate_excel_data(df, required_cols)
    assert is_valid is False
    assert any("Invalid email format" in err for err in errors)

def test_validate_excel_data_duplicates():
    """Test duplicate employee numbers"""
    df = pd.DataFrame({
        "EmployeeNumber": ["001", "001"],
        "Name": ["Alice", "Alice"],
        "Email": ["alice@example.com", "alice@example.com"]
    })
    required_cols = ["EmployeeNumber", "Name", "Email"]
    
    is_valid, errors = validate_excel_data(df, required_cols)
    assert is_valid is False
    assert any("Duplicate employee numbers" in err for err in errors)

def test_smtp_connection_success(mocker):
    """Test successful SMTP connection"""
    mock_smtp = mocker.patch("utils.validators.smtplib.SMTP")
    mock_server = mock_smtp.return_value
    
    success, message = check_smtp_connection("test@example.com", "password")
    
    assert success is True
    assert "successful" in message
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("test@example.com", "password")
    mock_server.quit.assert_called_once()

def test_smtp_connection_failure(mocker):
    """Test SMTP connection failure"""
    mock_smtp = mocker.patch("utils.validators.smtplib.SMTP")
    mock_smtp.side_effect = Exception("Connection refused")
    
    success, message = check_smtp_connection("test@example.com", "password")
    
    assert success is False
    assert "Connection error" in message
