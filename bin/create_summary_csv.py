import pandas as pd
import os

def create_summary_csv(input_path, output_path):
    try:
        # Read the trials.csv file
        trials_df = pd.read_csv(input_path)
        
        # Select the required columns
        summary_df = trials_df[['RCT_ID', 'Title', 'Primary Investigator', 'DOI Number', 'First registered on']].copy()
        # Extract the numerical part of the RCT_ID
        summary_df.loc[:, 'RCT_ID_num'] = summary_df['RCT_ID'].str.extract(r'(\d+)').astype(int)
        # Write the selected columns to summary.csv
        summary_df.to_csv(output_path, index=False)
        print(f"Summary CSV created successfully at {output_path}")
    except Exception as e:
        print(f"Error creating summary CSV: {e}")

def main():
    input_path = '_data/trials.csv'
    output_path = '_data/summary.csv'
    
    # Ensure the _data directory exists
    if not os.path.exists('_data'):
        os.makedirs('_data')
    
    create_summary_csv(input_path, output_path)

if __name__ == "__main__":
    main()
