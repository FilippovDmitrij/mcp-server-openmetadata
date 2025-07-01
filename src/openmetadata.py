from typing import Any, Dict, List, Optional

import httpx


class OpenMetadataError(Exception):
    """Base exception for OpenMetadata client errors."""

    pass


class OpenMetadataClient:
    """Client for interacting with OpenMetadata API."""

    def __init__(
        self, host: str, api_token: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None
    ):
        """Initialize OpenMetadata client.

        Args:
            host: OpenMetadata host URL
            api_token: API token for authentication
            username: Username for basic auth
            password: Password for basic auth

        Raises:
            OpenMetadataError: If neither API token nor username/password is provided
        """
        self.host = host.rstrip("/")
        self.session = httpx.Client()

        # Set up authentication
        if api_token:
            self.session.headers["Authorization"] = f"Bearer {api_token}"
        elif username and password:
            # Basic auth implementation would go here
            pass
        else:
            raise OpenMetadataError("Either API token or username/password must be provided")

    def list_tables(
        self,
        limit: int = 10,
        offset: int = 0,
        fields: Optional[str] = None,
        database: Optional[str] = None,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """List tables with pagination.

        Args:
            limit: Maximum number of tables to return (1 to 1000000)
            offset: Number of tables to skip
            fields: Comma-separated list of fields to include
            database: Filter tables by database fully qualified name
            include_deleted: Whether to include deleted tables

        Returns:
            Dictionary containing table list and metadata

        Raises:
            OpenMetadataError: If the API request fails
        """
        params = {"limit": min(max(1, limit), 1000000), "offset": max(0, offset)}
        if fields:
            params["fields"] = fields
        if database:
            params["database"] = database
        if include_deleted:
            params["include"] = "all"

        response = self.session.get(f"{self.host}/api/v1/tables", params=params)
        response.raise_for_status()
        return response.json()

    def get_table(self, table_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get details of a specific table by ID.

        Args:
            table_id: ID of the table
            fields: Comma-separated list of fields to include

        Returns:
            Table details

        Raises:
            OpenMetadataError: If the API request fails
        """
        params = {}
        if fields:
            params["fields"] = fields

        response = self.session.get(f"{self.host}/api/v1/tables/{table_id}", params=params)
        response.raise_for_status()
        return response.json()

    def get_table_by_name(self, fqn: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get details of a specific table by fully qualified name.

        Args:
            fqn: Fully qualified name of the table
            fields: Comma-separated list of fields to include

        Returns:
            Table details

        Raises:
            OpenMetadataError: If the API request fails
        """
        params = {}
        if fields:
            params["fields"] = fields

        response = self.session.get(f"{self.host}/api/v1/tables/name/{fqn}", params=params)
        response.raise_for_status()
        return response.json()

    def create_table(self, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new table.

        Args:
            table_data: Table data including name, description, columns, etc.

        Returns:
            Created table details

        Raises:
            OpenMetadataError: If the API request fails
        """
        response = self.session.post(f"{self.host}/api/v1/tables", json=table_data)
        response.raise_for_status()
        return response.json()

    def update_table(self, table_id: str, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing table.

        Args:
            table_id: ID of the table to update
            table_data: Updated table data

        Returns:
            Updated table details

        Raises:
            OpenMetadataError: If the API request fails
        """
        response = self.session.put(f"{self.host}/api/v1/tables/{table_id}", json=table_data)
        response.raise_for_status()
        return response.json()

    def delete_table(self, table_id: str, hard_delete: bool = False, recursive: bool = False) -> None:
        """Delete a table.

        Args:
            table_id: ID of the table to delete
            hard_delete: Whether to perform a hard delete
            recursive: Whether to recursively delete children

        Raises:
            OpenMetadataError: If the API request fails
        """
        params = {"hardDelete": hard_delete, "recursive": recursive}
        response = self.session.delete(f"{self.host}/api/v1/tables/{table_id}", params=params)
        response.raise_for_status()

    def search_metadata(
        self,
        query: str = "*",
        entity_type: Optional[str] = None,
        limit: int = 10,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """Search metadata entities."""

        params = {"q": query, "size": limit, "deleted": str(include_deleted).lower()}
        if entity_type:
            params["index"] = entity_type

        response = self.session.get(f"{self.host}/api/v1/search/query", params=params)
        response.raise_for_status()
        return response.json()

    def get_entity_details(self, entity_type: str, fqn: str, fields: str = "*") -> Dict[str, Any]:
        """Get entity details by fully qualified name."""

        params = {"fields": fields}
        response = self.session.get(f"{self.host}/api/v1/{entity_type}/name/{fqn}", params=params)
        response.raise_for_status()
        return response.json()

    def create_glossary(
        self,
        name: str,
        description: str,
        owners: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new glossary."""

        data: Dict[str, Any] = {"name": name, "description": description}
        if owners:
            data["owners"] = [{"name": o, "type": "user"} for o in owners]
        if reviewers:
            data["reviewers"] = [{"name": r, "type": "user"} for r in reviewers]

        response = self.session.post(f"{self.host}/api/v1/glossaries", json=data)
        response.raise_for_status()
        return response.json()

    def create_glossary_term(
        self,
        name: str,
        glossary: str,
        description: str,
        parent_term: Optional[str] = None,
        owners: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new glossary term."""

        data: Dict[str, Any] = {"name": name, "glossary": glossary, "description": description}
        if parent_term:
            data["parent"] = parent_term
        if owners:
            data["owners"] = [{"name": o, "type": "user"} for o in owners]

        response = self.session.post(f"{self.host}/api/v1/glossaryTerms", json=data)
        response.raise_for_status()
        return response.json()

    def patch_entity(self, entity_type: str, fqn: str, patch_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Patch an entity using JSON Patch operations."""

        headers = {"Content-Type": "application/json-patch+json"}
        response = self.session.patch(
            f"{self.host}/api/v1/{entity_type}/name/{fqn}",
            headers=headers,
            json=patch_data,
        )
        response.raise_for_status()
        return response.json()

    def get_entity_lineage(
        self,
        entity_type: str,
        fqn: str,
        upstream_depth: int = 1,
        downstream_depth: int = 1,
    ) -> Dict[str, Any]:
        """Retrieve lineage information for an entity."""

        params = {"upstreamDepth": upstream_depth, "downstreamDepth": downstream_depth}
        response = self.session.get(
            f"{self.host}/api/v1/lineage/{entity_type}/name/{fqn}",
            params=params,
        )
        response.raise_for_status()
        return response.json()
