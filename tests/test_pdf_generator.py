import os
import pandas as pd
import pytest
from pathlib import Path
from utils.pdf_generator import create_allowance_pdf, create_payslip_pdf, create_excess_ot_pdf

def test_create_allowance_pdf(temp_output_dir, sample_logo_path, mock_company_config):
    """Test generating an allowance PDF"""
    sample_data = {
        "EMP ID NO": "MP-TEST-001",
        "Name": "Juan Test",
        "Period": "DECEMBER 2025",
        "Department": "Production",
        "Total Pay": 2500.00
    }
    row = pd.Series(sample_data)
    
    pdf_path = create_allowance_pdf(row, temp_output_dir, sample_logo_path, mock_company_config)
    
    assert os.path.exists(pdf_path)
    assert "allowance" in getattr(pdf_path, 'lower', lambda: str(pdf_path).lower())()
    assert pdf_path.endswith(".pdf")
    
    # Check file size to ensure it's not empty
    assert os.path.getsize(pdf_path) > 1000

def test_create_payslip_pdf(temp_output_dir, sample_logo_path, mock_company_config):
    """Test generating a payslip PDF"""
    sample_data = {
        "EmployeeNumber": "MP-TEST-002",
        "Name": "Maria Test",
        "PayrollPeriod": "December 1-15, 2025",
        "Position": "Engineer",
        "BasicSalary": 25000.00,
        "MonthlyAllowance": 2000.00,
        "RegularHours": 88,
        "RegularAmount": 12500.00,
        "RegularOTHours": 0,
        "RegularOTAmount": 0,
        "LegalHolidayHours": 0,
        "LegalHolidayAmount": 0,
        "LegalOTHours": 0,
        "LegalOTAmount": 0,
        "SpecialHolidayHours": 0,
        "SpecialHolidayAmount": 0,
        "SpecialHolidayOTHours": 0,
        "SpecialHolidayOTAmount": 0,
        "NightDiffHours": 0,
        "NightDiffAmount": 0,
        "OffsetHours": 0,
        "OffsetAmount": 0,
        "PaidLeaveHours": 0,
        "PaidLeaveAmount": 0,
        "AdjustmentEarnings": 0,
        "Allowance": 1000.00,
        "ThirteenthMonthPay": 0,
        "OthersEarnings": 0,
        "GrossIncome": 13500.00,
        "PagibigContribution": 100.00,
        "PhilhealthContribution": 300.00,
        "SSSContribution": 900.00,
        "PagibigLoan": 0,
        "SSSLoan": 0,
        "WithholdingTax": 1000.00,
        "AdjustmentDeductions": 0,
        "OthersDeductions": 0,
        "TotalDeductions": 2300.00,
        "NetPay": 11200.00
    }
    
    row = pd.Series(sample_data)
    pdf_path = create_payslip_pdf(row, temp_output_dir, sample_logo_path, mock_company_config)
    
    assert os.path.exists(pdf_path)
    assert "payslip" in getattr(pdf_path, 'lower', lambda: str(pdf_path).lower())()
    assert os.path.getsize(pdf_path) > 1000

def test_create_excess_ot_pdf(temp_output_dir, sample_logo_path, mock_company_config):
    """Test generating an excess OT PDF"""
    sample_data = {
        "Name": "Pedro Test",
        "Period": "DECEMBER 2025",
        "RH HOURS": 0, "RH PAY": 0,
        "ND HOURS": 0, "ND PAY": 0,
        "ROT HOURS": 10.0, "ROT PAY": 1000.00,
        "SUNDAY HOURS": 0, "SUNDAY PAY": 0,
        "SUN/SPH HOURS": 0, "SUN/SPH PAY": 0,
        "SUN/SPH OT HOURS": 0, "SUN/SPH OT PAY": 0,
        "SUN/SPH ND HOURS": 0, "SUN/SPH ND PAY": 0,
        "RD+SPH HOURS": 0, "RD+SPH PAY": 0,
        "RD+SPH OT HOURS": 0, "RD+SPH OT PAY": 0,
        "RD+SPH ND HOURS": 0, "RD+SPH ND PAY": 0,
        "OFFSET": 0, "OFFSET Pay": 0,
        "Adjustment": 0,
        "Total Pay": 1000.00
    }
    
    row = pd.Series(sample_data)
    pdf_path = create_excess_ot_pdf(row, temp_output_dir, sample_logo_path, mock_company_config)
    
    assert os.path.exists(pdf_path)
    assert "excess" in getattr(pdf_path, 'lower', lambda: str(pdf_path).lower())()
    assert os.path.getsize(pdf_path) > 1000
