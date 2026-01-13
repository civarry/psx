# Payroll Document System

A web application for generating and distributing payslips, excess overtime, and allowance documents to employees via email.

## Features

- Generate professional PDF documents (Payslips, Excess OT, Allowances)
- Bulk email distribution to employees
- Excel-based data import
- Configurable company branding (logo, company name, footer)
- Dry-run mode for testing without sending emails
- Export results as CSV or download PDFs as ZIP

## Getting Started

### Prerequisites

- Python 3.8+
- Gmail account with App Password enabled

### Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

The application will open at `http://localhost:8501`

## Configuration

### 1. Company Config File

Download the `company_config.json` template from the sidebar and fill in:

- `company_name` - Your company name
- `footer_text` - Document disclaimer text
- `smtp.email` - Gmail address
- `smtp.password` - Gmail App Password

### 2. Gmail App Password Setup

1. Enable 2-Factor Authentication in [Google Account Settings](https://myaccount.google.com/)
2. Go to Security > App passwords
3. Generate a new app password for "Mail"
4. Use this 16-character password in your config file

### 3. Upload Configuration

1. Open Settings in the sidebar
2. Upload your `company_config.json`
3. Optionally upload a company logo (PNG/JPG)

## Usage

1. Select document type tab (Payslip, Excess OT, or Allowance)
2. Upload the corresponding Excel file
3. Preview and verify the data
4. Toggle dry-run mode if testing
5. Click "Generate Documents" to process
6. Download results or PDFs as needed

## Excel Templates

Download templates from the sidebar. Each document type has specific required columns:

- **Payslip** - Employee info, earnings, deductions
- **Excess OT** - Period, hours worked, pay calculations
- **Allowance** - Period, employee info, allowance amounts

## Security

- Config files are stored locally on your device
- Credentials are only kept in session memory
- Uploaded files are processed temporarily and auto-cleaned
- No data is shared externally except via your SMTP email

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Verify Gmail App Password (not regular password) |
| Missing columns | Compare Excel with downloaded template |
| Emails not sending | Check Gmail security alerts and daily limits (500/day) |

