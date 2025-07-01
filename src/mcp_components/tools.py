from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from src.openmetadata import OpenMetadataClient

# Tool definitions
SEARCH_METADATA_TOOL = Tool(
    name="search_metadata",
    description="Search metadata entities with optional filters",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string",
                "default": "*",
            },
            "entity_type": {
                "type": "string",
                "description": "Entity type to search (optional)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 10,
            },
            "include_deleted": {
                "type": "boolean",
                "description": "Whether to include deleted entities",
                "default": False,
            },
        },
    },
)

GET_ENTITY_DETAILS_TOOL = Tool(
    name="get_entity_details",
    description="Get details of a specific entity by fully qualified name",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": "Type of entity (e.g. table, dashboard)",
            },
            "fqn": {
                "type": "string",
                "description": "Fully qualified name of the entity",
            },
            "fields": {
                "type": "string",
                "description": "Comma separated list of fields to include",
                "default": "*",
            },
        },
        "required": ["entity_type", "fqn"],
    },
)

CREATE_GLOSSARY_TOOL = Tool(
    name="create_glossary",
    description="Create a new glossary",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Glossary name"},
            "description": {"type": "string", "description": "Glossary description"},
            "owners": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of owner usernames",
            },
            "reviewers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of reviewer usernames",
            },
        },
        "required": ["name", "description"],
    },
)

CREATE_GLOSSARY_TERM_TOOL = Tool(
    name="create_glossary_term",
    description="Create a new glossary term",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Term name"},
            "glossary": {"type": "string", "description": "Parent glossary name"},
            "description": {"type": "string", "description": "Term description"},
            "parent_term": {"type": "string", "description": "Parent term name"},
            "owners": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of owner usernames",
            },
        },
        "required": ["name", "glossary", "description"],
    },
)

PATCH_ENTITY_TOOL = Tool(
    name="patch_entity",
    description="Update an entity via JSON Patch operations",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {"type": "string", "description": "Entity type"},
            "fqn": {"type": "string", "description": "Fully qualified name"},
            "patch_operations": {
                "type": "array",
                "items": {"type": "object"},
                "description": "JSON Patch operation list",
            },
        },
        "required": ["entity_type", "fqn", "patch_operations"],
    },
)

GET_ENTITY_LINEAGE_TOOL = Tool(
    name="get_entity_lineage",
    description="Get lineage information for an entity",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {"type": "string", "description": "Entity type"},
            "fqn": {"type": "string", "description": "Fully qualified name"},
            "upstream_depth": {
                "type": "integer",
                "description": "Upstream lineage depth",
                "default": 1,
            },
            "downstream_depth": {
                "type": "integer",
                "description": "Downstream lineage depth",
                "default": 1,
            },
        },
        "required": ["entity_type", "fqn"],
    },
)


def list_all_tools() -> List[Tool]:
    return [
        SEARCH_METADATA_TOOL,
        GET_ENTITY_DETAILS_TOOL,
        CREATE_GLOSSARY_TOOL,
        CREATE_GLOSSARY_TERM_TOOL,
        PATCH_ENTITY_TOOL,
        GET_ENTITY_LINEAGE_TOOL,
    ]


def call_tool(name: str, arguments: Dict[str, Any], client: OpenMetadataClient) -> List[TextContent]:
    if name == SEARCH_METADATA_TOOL.name:
        results = client.search_metadata(
            query=arguments.get("query", "*"),
            entity_type=arguments.get("entity_type"),
            limit=arguments.get("limit", 10),
            include_deleted=arguments.get("include_deleted", False),
        )
        return [TextContent(type="text", text=str(results))]
    if name == GET_ENTITY_DETAILS_TOOL.name:
        results = client.get_entity_details(
            entity_type=arguments["entity_type"],
            fqn=arguments["fqn"],
            fields=arguments.get("fields", "*"),
        )
        return [TextContent(type="text", text=str(results))]
    if name == CREATE_GLOSSARY_TOOL.name:
        results = client.create_glossary(
            name=arguments["name"],
            description=arguments["description"],
            owners=arguments.get("owners"),
            reviewers=arguments.get("reviewers"),
        )
        return [TextContent(type="text", text=str(results))]
    if name == CREATE_GLOSSARY_TERM_TOOL.name:
        results = client.create_glossary_term(
            name=arguments["name"],
            glossary=arguments["glossary"],
            description=arguments["description"],
            parent_term=arguments.get("parent_term"),
            owners=arguments.get("owners"),
        )
        return [TextContent(type="text", text=str(results))]
    if name == PATCH_ENTITY_TOOL.name:
        results = client.patch_entity(
            entity_type=arguments["entity_type"],
            fqn=arguments["fqn"],
            patch_data=arguments["patch_operations"],
        )
        return [TextContent(type="text", text=str(results))]
    if name == GET_ENTITY_LINEAGE_TOOL.name:
        results = client.get_entity_lineage(
            entity_type=arguments["entity_type"],
            fqn=arguments["fqn"],
            upstream_depth=arguments.get("upstream_depth", 1),
            downstream_depth=arguments.get("downstream_depth", 1),
        )
        return [TextContent(type="text", text=str(results))]
    raise ValueError(f"Unknown tool: {name}")
