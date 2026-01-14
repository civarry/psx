import pandas as pd
import pytest
from io import BytesIO
from utils.excel_handler import validate_excel_columns, load_excel_file

@pytest.fixture
def sample_excel_file():
    """Create a sample Excel file in memory"""
    df = pd.DataFrame({
        'EmployeeNumber': ['001', '002'],
        'Name': ['Alice', 'Bob'],
        'Position': ['Dev', 'Test'],
        'PayrollPeriod': ['Jan 2025', 'Jan 2025'],
        'BasicSalary': [1000, 2000],
        # Add other required columns if necessary, but we can test partials too
        'Email': ['alice@example.com', 'bob@example.com']
    })
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    return output

def test_validate_excel_columns_missing():
    """Test validation detects missing columns"""
    df = pd.DataFrame({'Name': ['Alice']})
    is_valid, missing, extra = validate_excel_columns(df)
    
    assert is_valid is False
    assert 'EmployeeNumber' in missing
    assert 'NetPay' in missing

def test_validate_excel_columns_valid():
    """Test validation with all required columns"""
    # Create DF with ALL required columns from the validator list
    required_columns = [
        'EmployeeNumber', 'Name', 'Position', 'PayrollPeriod',
        'BasicSalary', 'MonthlyAllowance', 'Allowance',
        'RegularHours', 'RegularAmount',
        'RegularOTHours', 'RegularOTAmount',
        'LegalHolidayHours', 'LegalHolidayAmount',
        'SpecialHolidayHours', 'SpecialHolidayAmount',
        'NightDiffHours', 'NightDiffAmount',
        'OffsetHours', 'OffsetAmount',
        'PaidLeaveHours', 'PaidLeaveAmount',
        'AdjustmentEarnings', 'ThirteenthMonthPay',
        'OthersEarnings', 'GrossIncome',
        'SSSContribution', 'PhilhealthContribution', 'PagibigContribution',
        'PagibigLoan', 'SSSLoan', 'WithholdingTax',
        'AdjustmentDeductions', 'OthersDeductions',
        'TotalDeductions', 'NetPay'
    ]
    data = {col: [0] for col in required_columns}
    df = pd.DataFrame(data)
    
    is_valid, missing, extra = validate_excel_columns(df)
    assert is_valid is True
    assert len(missing) == 0

def test_load_excel_file(sample_excel_file):
    """Test loading Excel file cleans data correctly"""
    df = load_excel_file(sample_excel_file)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'EmployeeNumber' in df.columns
    # Check string stripping
    assert df['Name'].iloc[0] == 'Alice'
    # Check numeric conversion/defaulting (BasicSalary was int)
    assert df['BasicSalary'].iloc[0] == 1000
