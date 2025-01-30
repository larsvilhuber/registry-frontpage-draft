import pandas as pd

# Load the Researcher.csv file, testing if it is there, otherwise exit with error message
try:
    researcher_df = pd.read_csv('_data/Researchers.csv')
except FileNotFoundError:
    print("File not found: _data/Researchers.csv")
    exit()

# Extract unique names from PI and Researcher columns
unique_names = pd.unique(researcher_df[['PI', 'Researcher']].values.ravel('K'))

# Initialize the new DataFrame
new_df = pd.DataFrame(columns=['Name', 'PI', 'Researcher'])

# Populate the new DataFrame
rows = []
for name in unique_names:
    pi_projects = set(researcher_df[researcher_df['PI'] == name]['Proj ID'].astype(str).tolist())
    researcher_projects = set(researcher_df[researcher_df['Researcher'] == name]['Proj ID'].astype(str).tolist())
    # Remove projects where the name is also a PI
    researcher_projects = researcher_projects - pi_projects
    rows.append({
        'Name': name,
        'PI': ', '.join(pi_projects),
        'Researcher': ', '.join(researcher_projects)
    })

new_df = pd.concat([new_df, pd.DataFrame(rows)], ignore_index=True)



# Save the new DataFrame to a CSV file
new_df.to_csv('_data/UniqueResearchers.csv', index=False)
print("Saved unique researchers to _data/UniqueResearchers.csv")