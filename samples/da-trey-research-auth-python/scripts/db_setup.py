"""
Database setup script for Azure Table Storage.
Creates tables and populates them with seed data from JSON files.
"""

import json
import sys
import time
import uuid
from pathlib import Path

from azure.data.tables import TableServiceClient, TableClient


TABLE_NAMES = ["Project", "Consultant", "Assignment"]


def get_tables(table_service_client: TableServiceClient) -> list[str]:
    return [t.name for t in table_service_client.list_tables()]


def main():
    connection_string = sys.argv[1] if len(sys.argv) > 1 else "UseDevelopmentStorage=true"
    reset = len(sys.argv) > 2 and sys.argv[2] in ("--reset", "-r")

    table_service_client = TableServiceClient.from_connection_string(connection_string)

    # If reset is true, delete all tables
    if reset:
        tables = get_tables(table_service_client)
        for table in tables:
            print(f"Deleting table: {table}")
            table_service_client.delete_table(table)

        while True:
            print("Waiting for tables to be deleted...")
            tables = get_tables(table_service_client)
            if not tables:
                print("All tables deleted.")
                break
            time.sleep(1)

    # Create and populate tables
    for table_name in TABLE_NAMES:
        tables = get_tables(table_service_client)
        if table_name in tables:
            print(f"Table {table_name} already exists, skipping...")
            continue

        print(f"Creating table: {table_name}")
        while True:
            try:
                table_service_client.create_table(table_name)
                break
            except Exception as err:
                if hasattr(err, "status_code") and err.status_code == 409:
                    print("Table is marked for deletion, retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise

        # Add entities to table
        table_client = TableClient.from_connection_string(connection_string, table_name)
        json_path = Path(__file__).parent / "db" / f"{table_name}.json"
        data = json.loads(json_path.read_text(encoding="utf-8"))

        for entity in data["rows"]:
            row_key = str(entity.get("id", uuid.uuid4()))
            # Convert nested objects/arrays to JSON strings
            for key in list(entity.keys()):
                if isinstance(entity[key], (dict, list)):
                    entity[key] = json.dumps(entity[key])

            table_client.create_entity(entity={
                "PartitionKey": table_name,
                "RowKey": row_key,
                **entity,
            })
            print(f"Added entity to {table_name} with key {row_key}")


if __name__ == "__main__":
    main()
