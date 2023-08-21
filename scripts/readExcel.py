import click
import pandas as pd
import re

def create_user_map(excel_file):
    # Read the Excel file
    try:
        df = pd.read_excel(excel_file, sheet_name='UserMap')
    except pd.errors.EmptyDataError:
        click.echo("The UserMap sheet is empty.")
        return
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")
        return
    expected_columns = ['Name', 'UserName', 'Email', 'GirderId']
    if not all(col in df.columns for col in expected_columns):
        click.echo("The sheet UserMap does not contain all the expected columns.")
        return

    # Create a dictionary to store user data
    users = {}

    # Iterate through the rows and create a dictionary for each user
    for _, row in df.iterrows():
        user_data = {
            'Name': row['Name'],
            'UserName': row['UserName'],
            'Email': row['Email'],
            'GirderId': row['GirderId']
        }
        users[user_data['Name']] = user_data
    return users

def read_sheet(excel_file, sheet_name):
        # Name of the sheet you want to extract data from
    sheet_name = 'FLE VAE'

    # Read the Excel file
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=1)  # Skip the first row (header) in the data
    except pd.errors.EmptyDataError:
        click.echo(f"The '{sheet_name}' sheet is empty.")
        return
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")
        return

    # Verify that the expected columns exist in the sheet
    expected_columns = ['File Name', 'Link', 'Annotator', 'Status', 'Completion Date']
    if not all(col in df.columns for col in expected_columns):
        click.echo(f"The sheet '{sheet_name}' does not contain all the expected columns.")
        return
    df = df.dropna(subset=['File Name', 'Link'])

    # Create a dictionary to store the desired data
    data_dict = {}

    # Iterate through the rows and extract the desired fields
    for _, row in df.iterrows():
        file_name = row['File Name']
        link = row['Link']
        annotator = row['Annotator']
        status = row['Status']
        completion_date = row['Completion Date']
        # Extract GirderId from the link
        girder_id_match = re.search(r'/([a-f0-9\-]+)\?', link)
        girder_id = girder_id_match.group(1) if girder_id_match else None

        # Create a dictionary for the current row
        row_data = {
            'FileName': file_name,
            'Link': link,
            'GirderId': girder_id,
            'Annotator': annotator,
            'Status': status,
            'Completion Date': completion_date
        }

        # Use the FileName as the dictionary key
        data_dict[girder_id] = row_data

    return data_dict


@click.command()
@click.argument('excel_file', type=click.Path(exists=True))
def main(excel_file):
    # Name of the sheet you want to extract data from
    sheet_name = 'UserMap'

    userMap = create_user_map(excel_file)
    print(userMap)
    fle_vae = read_sheet(excel_file, 'FLE VAUE')
    fle_social_norms = read_sheet(excel_file, 'FLE Social Norms')
    change_point = read_sheet(excel_file, 'Changepoint')
    sme_social_norms = read_sheet(excel_file, 'SME Social Norms')

    print(fle_vae)
    print(fle_social_norms)
    print(change_point)
    print(sme_social_norms)

if __name__ == '__main__':
    main()
