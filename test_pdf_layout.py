"""
Simple PDF layout tester - run this to generate test PDFs without the app

Usage:
    python test_pdf_layout.py --allowance     # Test allowance PDF
    python test_pdf_layout.py --payslip       # Test payslip PDF
    python test_pdf_layout.py --excess-ot     # Test excess OT PDF
    python test_pdf_layout.py --all           # Test all PDFs
"""

import argparse
import pandas as pd
from pathlib import Path
from utils.pdf_generator import create_allowance_pdf, create_payslip_pdf, create_excess_ot_pdf

# Output directory for test PDFs
OUTPUT_DIR = "./test_output"
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Sample logo path (set to None if no logo)
LOGO_PATH = "assets/logo.png" if Path("assets/logo.png").exists() else None

# Company config
COMPANY_CONFIG = {
    "company_name": "MASSPOWER PHILIPPINES ELECTRONIC INC.",
    "footer_text": "Full details of your pay for the period covered are given above.",
    "document_id": "D-MPFA-20004.02",
    "effectivity_date": "January 20, 2024"
}


def test_allowance():
    """Generate a test allowance PDF"""
    sample_data = {
        "EMP ID NO": "MP-2022-352",
        "Name": "Barreda, Jeffrey Fernandez",
        "Period": "DECEMBER 2025",
        "Department": "Production",
        "Total Pay": 2386.36
    }

    row = pd.Series(sample_data)
    pdf_path = create_allowance_pdf(row, OUTPUT_DIR, LOGO_PATH, COMPANY_CONFIG)
    print(f"Allowance PDF created: {pdf_path}")
    return pdf_path


def test_payslip():
    """Generate a test payslip PDF"""
    sample_data = {
        "EmployeeNumber": "MP-2022-352",
        "Name": "Barreda, Jeffrey Fernandez",
        "PayrollPeriod": "December 1-15, 2025",
        "Position": "Production Operator",
        "BasicSalary": 15000.00,
        "MonthlyAllowance": 2000.00,
        "RegularHours": 88,
        "RegularAmount": 7500.00,
        "RegularOTHours": 8,
        "RegularOTAmount": 750.00,
        "LegalHolidayHours": 0,
        "LegalHolidayAmount": 0,
        "SpecialHolidayHours": 0,
        "SpecialHolidayAmount": 0,
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
        "GrossIncome": 9250.00,
        "PagibigContribution": 100.00,
        "PhilhealthContribution": 150.00,
        "SSSContribution": 450.00,
        "PagibigLoan": 0,
        "SSSLoan": 0,
        "WithholdingTax": 0,
        "AdjustmentDeductions": 0,
        "OthersDeductions": 0,
        "TotalDeductions": 700.00,
        "NetPay": 8550.00
    }

    row = pd.Series(sample_data)
    pdf_path = create_payslip_pdf(row, OUTPUT_DIR, LOGO_PATH, COMPANY_CONFIG)
    print(f"Payslip PDF created: {pdf_path}")
    return pdf_path


def test_excess_ot():
    """Generate a test excess OT PDF"""
    sample_data = {
        "Name": "Barreda, Jeffrey Fernandez",
        "Period": "DECEMBER 2025",
        "RH Hours": 8.0,
        "RH Pay": 1200.00,
        "ND Hours": 4.0,
        "ND Pay": 300.00,
        "ROT Hours": 10.0,
        "ROT Pay": 950.00,
        "Sunday/SPH Hours": 8.0,
        "Sunday/SPH Pay": 800.00,
        "Sunday/SPH OT Hours": 2.0,
        "Sunday/SPH OT Pay": 250.00,
        "Sunday/SPH ND Hours": 0,
        "Sunday/SPH ND Pay": 0,
        "Adjustment": 0,
        "Total Pay": 3500.00
    }

    row = pd.Series(sample_data)
    pdf_path = create_excess_ot_pdf(row, OUTPUT_DIR, LOGO_PATH, COMPANY_CONFIG)
    print(f"Excess OT PDF created: {pdf_path}")
    return pdf_path


def main():
    parser = argparse.ArgumentParser(
        description="PDF Layout Tester - Generate test PDFs without the app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_pdf_layout.py --allowance
    python test_pdf_layout.py --payslip
    python test_pdf_layout.py --excess-ot
    python test_pdf_layout.py --all
        """
    )

    parser.add_argument("--allowance", "-a", action="store_true", help="Generate test allowance PDF")
    parser.add_argument("--payslip", "-p", action="store_true", help="Generate test payslip PDF")
    parser.add_argument("--excess-ot", "-e", action="store_true", help="Generate test excess OT PDF")
    parser.add_argument("--all", action="store_true", help="Generate all test PDFs")

    args = parser.parse_args()

    # If no arguments, show help
    if not any([args.allowance, args.payslip, args.excess_ot, args.all]):
        parser.print_help()
        return

    print("=" * 50)
    print("PDF Layout Tester")
    print("=" * 50)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Logo: {LOGO_PATH or 'None'}")
    print()

    if args.allowance or args.all:
        test_allowance()

    if args.payslip or args.all:
        test_payslip()

    if args.excess_ot or args.all:
        test_excess_ot()

    print()
    print("Done! Check the test_output folder for generated PDFs.")


if __name__ == "__main__":
    main()
