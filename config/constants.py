"""Configuration constants for payslip automation"""

# Document Types
DOCUMENT_TYPES = {
    'PAYSLIP': 'Payslip',
    'EXCESS_OT': 'Excess OT',
    'ALLOWANCE': 'Allowance'
}

# Required Excel columns for PAYSLIP
PAYSLIP_REQUIRED_COLUMNS = [
    # Employee Info
    'EmployeeNumber', 'Name', 'Position', 'Email', 'PayrollPeriod',

    # Salary
    'BasicSalary', 'MonthlyAllowance', 'Allowance',

    # Regular Work
    'RegularHours', 'RegularAmount',
    'RegularOTHours', 'RegularOTAmount',

    # Holidays
    'LegalHolidayHours', 'LegalHolidayAmount',
    'SpecialHolidayHours', 'SpecialHolidayAmount',

    # Other Earnings
    'NightDiffHours', 'NightDiffAmount',
    'OffsetHours', 'OffsetAmount',
    'PaidLeaveHours', 'PaidLeaveAmount',
    'AdjustmentEarnings', 'ThirteenthMonthPay', 'OthersEarnings',

    # Totals
    'GrossIncome',

    # Deductions
    'SSSContribution', 'PhilhealthContribution', 'PagibigContribution',
    'PagibigLoan', 'SSSLoan', 'WithholdingTax',
    'AdjustmentDeductions', 'OthersDeductions',
    'TotalDeductions', 'NetPay'
]

# Required Excel columns for EXCESS OT
EXCESS_OT_REQUIRED_COLUMNS = [
    # Employee Info
    'Period', 'Name',

    # Hours
    'RH Hours', 'ND Hours', 'ROT Hours',
    'Sunday/SPH Hours', 'Sunday/SPH OT Hours', 'Sunday/SPH ND Hours',

    # Pay
    'RH Pay', 'ND Pay', 'ROT Pay',
    'Sunday/SPH Pay', 'Sunday/SPH OT Pay', 'Sunday/SPH ND Pay',

    # Totals
    'Adjustment', 'Total Pay'
]

# Optional columns for EXCESS OT
EXCESS_OT_OPTIONAL_COLUMNS = ['Email', 'Statement']

# Required Excel columns for ALLOWANCE
ALLOWANCE_REQUIRED_COLUMNS = [
    'Period', 'EMP ID NO', 'Name', 'Department', 'Total Pay'
]

# Optional columns for ALLOWANCE
ALLOWANCE_OPTIONAL_COLUMNS = ['Email']

# Backward compatibility - keep for existing code
REQUIRED_COLUMNS = PAYSLIP_REQUIRED_COLUMNS

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Default Company Details (empty for security)
DEFAULT_COMPANY_NAME = ""
DEFAULT_FOOTER_TEXT = ""
DEFAULT_DOCUMENT_ID = ""
DEFAULT_EFFECTIVITY_DATE = ""

# File Upload Settings
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = ['.xlsx']

# PDF Configuration
DEFAULT_LOGO_PATH = "assets/logo.png"
