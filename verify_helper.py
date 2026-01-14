import sys
from unittest.mock import MagicMock
import pandas as pd
from tabs.process_helper import process_single_document

def test_single_process_dry_run():
    # Mock data
    row = pd.Series({'Name': 'Test User', 'Email': 'test@example.com'})
    
    # Mock generator 
    def mock_generator(row, output_dir, logo_path, company_config):
        return f"{output_dir}/test.pdf"
        
    # Run
    result = process_single_document(
        row=row,
        document_type='EXCESS_OT',
        pdf_generator_func=mock_generator,
        output_dir='./test_output',
        logo_path=None,
        company_config={},
        dry_run=True,
        smtp_config={}
    )
    
    print("Result:", result)
    assert result['Status'] == 'Generated'
    assert result['PDF'] == 'test.pdf'

if __name__ == "__main__":
    test_single_process_dry_run()
    print("Test passed!")
