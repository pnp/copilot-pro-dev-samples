import json
import os
from typing import Any

from azure.data.tables import TableClient, UpdateMode

from .utilities import HttpError


class DbService:
    """Generic database service for Azure Table Storage."""

    def __init__(self, ok_to_cache_locally: bool = False):
        self._connection_string = os.environ.get("STORAGE_ACCOUNT_CONNECTION_STRING", "")
        if not self._connection_string:
            raise RuntimeError("STORAGE_ACCOUNT_CONNECTION_STRING is not set")
        self._ok_to_cache_locally = ok_to_cache_locally
        self._entity_cache: list[dict] = []

    async def get_entity_by_row_key(self, table_name: str, row_key: str) -> dict:
        if not self._ok_to_cache_locally:
            table_client = TableClient.from_connection_string(self._connection_string, table_name)
            entity = table_client.get_entity(partition_key=table_name, row_key=row_key)
            return self._expand_property_values(dict(entity))
        else:
            entities = await self.get_entities(table_name)
            matches = [e for e in entities if e.get("RowKey") == row_key]
            if not matches:
                raise HttpError(404, f"Entity {row_key} not found")
            return matches[0]

    async def get_entities(self, table_name: str) -> list[dict]:
        if not self._ok_to_cache_locally or not self._entity_cache:
            table_client = TableClient.from_connection_string(self._connection_string, table_name)
            entities = table_client.list_entities()
            self._entity_cache = []
            seen_keys = set()
            for entity in entities:
                rk = entity.get("RowKey", "")
                if rk not in seen_keys:
                    seen_keys.add(rk)
                    self._entity_cache.append(self._expand_property_values(dict(entity)))
        return self._entity_cache

    async def create_entity(self, table_name: str, row_key: str, new_entity: dict) -> None:
        self._entity_cache = []
        entity = self._compress_property_values(new_entity)
        table_client = TableClient.from_connection_string(self._connection_string, table_name)
        try:
            table_client.create_entity(entity={
                "PartitionKey": table_name,
                "RowKey": row_key,
                **entity,
            })
        except Exception as ex:
            # 409 = conflict / already exists — ignore
            status = getattr(ex, "status_code", None) or getattr(getattr(ex, "response", None), "status_code", None)
            if status != 409:
                raise HttpError(500, str(ex))

    async def update_entity(self, table_name: str, updated_entity: dict) -> None:
        self._entity_cache = []
        entity = self._compress_property_values(updated_entity)
        table_client = TableClient.from_connection_string(self._connection_string, table_name)
        table_client.update_entity(entity=entity, mode=UpdateMode.REPLACE)

    # --- helpers ---

    def _expand_property_values(self, entity: dict) -> dict:
        result = {}
        for key, value in entity.items():
            result[key] = self._expand_property_value(value)
        return result

    @staticmethod
    def _expand_property_value(v: Any) -> Any:
        if isinstance(v, str) and v and v[0] in ("{", "["):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return v
        return v

    def _compress_property_values(self, entity: dict) -> dict:
        result = {}
        for key, value in entity.items():
            result[key] = self._compress_property_value(value)
        return result

    @staticmethod
    def _compress_property_value(v: Any) -> Any:
        if isinstance(v, (dict, list)):
            return json.dumps(v)
        return v
