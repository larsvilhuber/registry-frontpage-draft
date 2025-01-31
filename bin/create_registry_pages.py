import pandas as pd
import os
import sys
import re

# Load the Abstracts.csv file
trials_df = pd.read_csv('_data/trials.csv')

# Ensure the _trials directory exists
os.makedirs('_trials', exist_ok=True)

# Title,Url,Last update date,Published at,First registered on,RCT_ID,DOI Number,Primary Investigator,Status,Start date,End date,Keywords,Country names,Other Primary Investigators,Jel code,Secondary IDs,Abstract,External Links,Sponsors,Partners,Intervention start date,Intervention end date,Intervention,Primary outcome end points,Primary outcome explanation,Secondary outcome end points,Secondary outcome explanation,Experimental design,Experimental design details,Randomization method,Randomization unit,Sample size number clusters,Sample size number observations,Sample size number arms,Minimum effect size,IRB,Analysis Plan Documents,Intervention completion date,Data collection completion,Data collection completion date,Number of clusters,Attrition correlated,Total number of observations,Treatment arms,Public data,Public data url,Program files,Program files url,Post trial documents csv,Relevant papers for csv

# Iterate through each row and create a Jekyll stub file
total_rows = len(trials_df)
for index, row in trials_df.iterrows():
    # Extract the numerical part of the RCT_ID
    RCT_ID_num = int(re.search(r'\d+', row['RCT_ID']).group())
    filename = f"_trials/{RCT_ID_num}.md"
    with open(filename, 'w', encoding='utf-8') as file:
        file.write('---\n')
        file.write(f"title: \"{row['Title']}\"\n")
        file.write(f"rct_id: \"{row['RCT_ID']}\"\n")
        file.write(f"rct_id_num: \"{RCT_ID_num}\"\n")
        file.write(f"doi: \"{row['DOI Number']}\"\n")
        file.write(f"date: \"{row['First registered on']}\"\n")
        file.write(f"status: \"{row['Status']}\"\n")
        # Handle NaN values for jel
        jel_code = row['Jel code']
        if pd.isna(jel_code):
            file.write(f"jel: \"\"\n")
        else:
            file.write(f"jel: \"{jel_code}\"\n")
        
        # Format start date
        start_date = row['Start date']
        if pd.isna(start_date):
            file.write(f"start_year: \"\"\n")
        else:
            file.write(f"start_year: \"{pd.to_datetime(start_date).strftime('%Y-%m-%d')}\"\n")
        
        # Handle NaN values for end year and format it
        end_year = row['End date']
        if pd.isna(end_year):
            file.write(f"end_year: \"\"\n")
        else:
            file.write(f"end_year: \"{pd.to_datetime(end_year).strftime('%Y-%m-%d')}\"\n")

        # Remove email addresses from the "Primary Investigator" field
        primary_investigator = re.sub(r'\s*\S+@\S+\s*', '', row['Primary Investigator'])
        file.write(f"pi: \"{primary_investigator}\"\n")
        
        # Process the "Other Primary Investigators" field
        other_primary_investigators = row['Other Primary Investigators']
        other_investigators_list = []
        if not pd.isna(other_primary_investigators):
            for investigator in other_primary_investigators.split(';'):
                match = re.match(r'^(.*?)\s*\((.*?)\)\s*(.*)$', investigator.strip())
                if match:
                    other_investigators_list.append({
                        'name': match.group(1),
                        'email': match.group(2),
                        'affiliation': match.group(3)
                    })
        
        file.write("pi_other:\n")
        for investigator in other_investigators_list:
            file.write(f"  - name: {investigator['name']}\n")
            file.write(f"    email: {investigator['email']}\n")
            file.write(f"    affiliation: {investigator['affiliation']}\n")
        
        file.write(f"abstract: \"{row['Abstract']}\"\n")
        file.write(f"layout: registration\n")
        file.write('---\n\n')

    if (index + 1) % 100 == 0 or index + 1 == total_rows:
        sys.stdout.write(f"\rProcessed {index + 1}/{total_rows} ({(index + 1) / total_rows * 100:.2f}%)")
        sys.stdout.flush()

print("\nJekyll stubs created in _trials directory.\n")
