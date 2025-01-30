import pandas as pd
import os

# Load the Excel file
excel_file = 'ProjectsAllMetadata.xlsx'

# Read the Excel file
xls = pd.ExcelFile(excel_file)

# Ensure the _data directory exists
os.makedirs('_data', exist_ok=True)

# Iterate through each sheet and save as CSV
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    csv_file = os.path.join('_data', f"{sheet_name}.csv")
    df.to_csv(csv_file, index=False)
    print(f"Saved {sheet_name} to {csv_file}")