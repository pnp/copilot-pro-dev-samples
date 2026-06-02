"""Database setup script for Azure Table Storage."""
import json
import os
import sys
import time
import uuid

from azure.data.tables import TableClient, TableServiceClient

TABLE_NAMES = ["Project", "Consultant", "Assignment"]


def get_tables(table_service_client: TableServiceClient) -> list:
    """Return list of table names in the storage account."""
    return [table.name for table in table_service_client.list_tables()]


def main():
    connection_string = sys.argv[1] if len(sys.argv) > 1 else "UseDevelopmentStorage=true"
    reset = "--reset" in sys.argv or "-r" in sys.argv

    table_service_client = TableServiceClient.from_connection_string(connection_string)

    # If reset is true, delete all tables
    if reset:
        tables = get_tables(table_service_client)
        for table in tables:
            print(f"Deleting table: {table}")
            table_client = TableClient.from_connection_string(connection_string, table)
            table_client.delete_table()

        tables_exist = True
        while tables_exist:
            print("Waiting for tables to be deleted...")
            tables = get_tables(table_service_client)
            if not tables:
                tables_exist = False
                print("All tables deleted.")
            time.sleep(1)

    # Create and populate tables
    for table_name in TABLE_NAMES:
        # Skip if table already exists
        tables = get_tables(table_service_client)
        if table_name in tables:
            print(f"Table {table_name} already exists, skipping...")
            continue

        # Create table
        print(f"Creating table: {table_name}")
        table_created = False
        while not table_created:
            try:
                table_service_client.create_table(table_name)
                table_created = True
            except Exception as err:
                if hasattr(err, "status_code") and err.status_code == 409:
                    print("Table is marked for deletion, retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise

        # Add entities to table
        table_client = TableClient.from_connection_string(connection_string, table_name)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "db", f"{table_name}.json")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entity in data["rows"]:
            row_key = str(entity.get("id", uuid.uuid4()))
            # Convert nested objects to JSON strings
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
