import json
import os

from azure.data.tables import TableClient, TableServiceClient

from .utilities import HttpError


class DbService:
    """Generic database service for Azure Table Storage operations."""

    def __init__(self, ok_to_cache_locally: bool = False):
        self._connection_string = os.environ.get("STORAGE_ACCOUNT_CONNECTION_STRING", "")
        if not self._connection_string:
            raise RuntimeError("STORAGE_ACCOUNT_CONNECTION_STRING is not set")
        self._ok_to_cache_locally = ok_to_cache_locally
        self._entity_cache: list = []

    def get_entity_by_row_key(self, table_name: str, row_key: str) -> dict:
        if not self._ok_to_cache_locally:
            table_client = TableClient.from_connection_string(self._connection_string, table_name)
            entity = table_client.get_entity(partition_key=table_name, row_key=row_key)
            return self._expand_property_values(entity)
        else:
            entities = self.get_entities(table_name)
            result = [e for e in entities if e.get("rowKey") == row_key or e.get("RowKey") == row_key]
            if not result:
                raise HttpError(404, f"Entity {row_key} not found")
            return result[0]

    def get_entities(self, table_name: str) -> list:
        if not self._ok_to_cache_locally or not self._entity_cache:
            table_client = TableClient.from_connection_string(self._connection_string, table_name)
            entities = table_client.list_entities()
            self._entity_cache = []
            seen_keys = set()
            for entity in entities:
                rk = entity.get("RowKey", "")
                if rk not in seen_keys:
                    seen_keys.add(rk)
                    self._entity_cache.append(self._expand_property_values(entity))
        return self._entity_cache

    def create_entity(self, table_name: str, row_key: str, entity: dict) -> None:
        self._entity_cache = []
        compressed = self._compress_property_values(entity)
        table_client = TableClient.from_connection_string(self._connection_string, table_name)
        try:
            table_client.create_entity(entity={
                "PartitionKey": table_name,
                "RowKey": row_key,
                **compressed
            })
        except Exception as ex:
            if hasattr(ex, "status_code") and ex.status_code == 409:
                pass  # Entity already exists
            else:
                raise HttpError(500, str(ex))

    def update_entity(self, table_name: str, entity: dict) -> None:
        self._entity_cache = []
        compressed = self._compress_property_values(entity)
        table_client = TableClient.from_connection_string(self._connection_string, table_name)
        table_client.update_entity(entity=compressed, mode="replace")

    def _expand_property_values(self, entity: dict) -> dict:
        result = {}
        for key, value in entity.items():
            result[key] = self._expand_property_value(value)
        return result

    def _expand_property_value(self, value):
        if isinstance(value, str) and len(value) > 0 and value[0] in ('{', '['):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return value

    def _compress_property_values(self, entity: dict) -> dict:
        result = {}
        for key, value in entity.items():
            result[key] = self._compress_property_value(value)
        return result

    def _compress_property_value(self, value):
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value
