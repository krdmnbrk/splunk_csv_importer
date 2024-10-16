
# CSV to Splunk Lookup Importer

To make it easier to upload CSV files as lookups in Splunk remotely, I developed a solution using SPL (Splunk Processing Language). This approach worked well for me, and I’m sharing it in hopes that it will help others in the community too.

## Features

- **CSV to Lookup**: Upload `.csv` files as Splunk lookups.
- **Backup Existing Lookups**: Automatically backup lookups with a timestamp if they already exist.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/krdmnbrk/splunk_csv_importer.git
    cd splunk_csv_importer
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up `.env`**:
    ```ini
    # Splunk instance's host (usually localhost or a specific IP)
    SPLUNK_HOST=

    # Splunk management port (usually 8089)
    SPLUNK_PORT=8089

    # Splunk token for authentication
    SPLUNK_TOKEN=

    # Splunk username & password for authentication
    SPLUNK_USERNAME=
    SPLUNK_PASSWORD=

    # Unique delimiter for the SPL
    # You don't need to change this unless you have a specific requirement.
    # E.g if your data contains "|^|" you can change this to something else.
    UNIQUE_DELIMITER=|^|
    ```

## Usage

```bash
python splunk_csv_importer.py --source_file path/to/your.csv --target_lookup_name your_lookup_name.csv
```

Example:
```bash
python splunk_csv_importer.py --source_file data.csv --target_lookup_name my_lookup.csv
```

If a lookup exists, it will be backed up with a timestamp.

## Example Workflow

1. Set up `.env` with your Splunk details.
2. Run the script with your CSV file.
3. Check your lookup in Splunk using:
    ```spl
    | inputlookup your_lookup_name.csv
    ```

## Contributions

Feel free to fork or submit PRs. I built this to solve a problem, and I'm happy if it helps others!
