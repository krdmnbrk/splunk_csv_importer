import splunklib.client as client
import splunklib.results as results
import csv
import os
import argparse
from dotenv import load_dotenv
from datetime import datetime
from splunklib.binding import AuthenticationError

# Load environment variables from .env file
load_dotenv()

# Retrieve Splunk configuration from environment variables
SPLUNK_HOST = os.getenv("SPLUNK_HOST")
SPLUNK_PORT = os.getenv("SPLUNK_PORT")
SPLUNK_TOKEN = os.getenv("SPLUNK_TOKEN")


def csv_to_dict(csv_file_path):
    """
    Reads a CSV file and converts it into a dictionary where keys are column names
    and values are lists of column data.

    Args:
        csv_file_path (str): Path to the CSV file.

    Returns:
        dict: Dictionary representation of the CSV data.
    """
    print(f"Reading CSV file: {csv_file_path}")
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        result_dict = {column: [] for column in reader.fieldnames}

        for row in reader:
            for column in reader.fieldnames:
                result_dict[column].append(row[column])

    print(f"CSV file read successfully: {len(result_dict)} columns found.")
    return result_dict


def oneshot_search(spl_query):
    """
    Executes a one-shot search on a Splunk instance using a token for authentication.

    Args:
        spl_query (str): The SPL query to be executed.

    Returns:
        list: List of search results as dictionaries.
    """
    print(f"Executing search query: {spl_query[:50]}...")  # Only show first 50 characters of the query
    try:
        # Connect to the Splunk service using token-based authentication
        service = client.connect(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            splunkToken=SPLUNK_TOKEN
        )

        # Execute the one-shot search with the specified query
        oneshot_search_results = service.jobs.oneshot(spl_query, output_mode='json')

        # Parse the JSON results returned from Splunk
        reader = results.JSONResultsReader(oneshot_search_results)
        search_results = [result for result in reader if isinstance(result, dict)]

        print(f"Search query executed successfully, {len(search_results)} result(s) found.")
        return search_results

    except AuthenticationError:
        print(f"[ERROR] Authentication failed! Please check your .env file and ensure that the SPLUNK_HOST, SPLUNK_PORT, and SPLUNK_TOKEN are correct.")
        exit(1)


def backup_lookup_if_exists(lookup_name):
    """
    Backs up the existing lookup table if it contains data. The backup file name
    will have a timestamp appended to it.

    Args:
        lookup_name (str): Name of the lookup table to check and backup.

    Returns:
        None
    """
    print(f"Checking if lookup '{lookup_name}' contains data...")
    # SPL query to check if the lookup contains any data
    spl_query = f"| inputlookup {lookup_name} | head 1"

    # Run the query to see if there's any data in the lookup
    results = oneshot_search(spl_query)

    if results:
        # If the lookup has data, create a backup with a timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_lookup_name = f"{lookup_name.split('.')[0]}_backup_{timestamp}.csv"

        # SPL query to create a backup of the lookup
        backup_query = f"| inputlookup {lookup_name} | outputlookup {backup_lookup_name}"

        # Run the backup query
        oneshot_search(backup_query)

        print(f"Backup created for '{lookup_name}' as '{backup_lookup_name}'")
    else:
        print(f"No data found in '{lookup_name}', no backup created.")


def generate_lookup(csv_file_path, lookup_name):
    """
    Generates a Splunk lookup table from CSV data and sends it to Splunk as a new lookup.

    Args:
        csv_file_path (str): Path to the CSV file.
        lookup_name (str): Name for the lookup table in Splunk.

    Returns:
        None
    """
    # Check if the lookup already contains data and backup if necessary
    backup_lookup_if_exists(lookup_name)

    # SPL template used to generate lookup content
    SPL_TEMPLATE = """
    | makeresults
    | eval "{field}"="{data}"
    | makemv delim="," "{field}"
    | mvexpand "{field}"
    """

    print(f"Generating lookup from CSV data: {csv_file_path}")
    # Convert the CSV data into a dictionary
    datas = csv_to_dict(csv_file_path)

    # Build the SPL (Splunk Processing Language) query
    spl_parts = []
    for index, (key, value) in enumerate(datas.items()):
        spl_query = SPL_TEMPLATE.format(field=key, data=','.join(value))
        if index > 0:
            spl_parts.append(f"| appendcols [{spl_query}]")
        else:
            spl_parts.append(spl_query)

    # Combine all parts of the SPL and prepare for output to lookup
    SPL = "\n".join(spl_parts)
    SPL += f"| fields - _time | outputlookup {lookup_name}"

    # Execute the SPL query in Splunk
    oneshot_search(SPL)

    # Print the final SPL query for debugging or review
    print(f"Lookup '{lookup_name}' created successfully from CSV '{csv_file_path}'.")

    # Verify the number of rows in the new lookup
    verify_query = f"| inputlookup {lookup_name} | stats count"
    result = oneshot_search(verify_query)
    if result:
        row_count = result[0].get('count', 0)
        print(f"Lookup '{lookup_name}' contains {row_count} rows.")


def main():
    # Argument parser for command-line usage
    parser = argparse.ArgumentParser(
        description="Generate a Splunk lookup from a CSV file.",
        epilog="Example: python script.py --source_file cyber_attacks.csv --target_lookup_name attacks_lookup.csv"
    )
    
    # Define command-line arguments with help descriptions
    parser.add_argument('--source_file', required=True, help='Path to the CSV file to upload as a lookup.')
    parser.add_argument('--target_lookup_name', required=True, help='Name of the target lookup file in Splunk (e.g., attacks_lookup.csv).')

    args = parser.parse_args()

    # Call the generate_lookup function with the provided arguments
    generate_lookup(args.source_file, args.target_lookup_name)


if __name__ == "__main__":
    main()