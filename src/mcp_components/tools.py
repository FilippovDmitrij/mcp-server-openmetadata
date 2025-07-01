from typing import Any, Dict, List, Optional # Добавил Optional

from mcp.types import TextContent, Tool

from src.openmetadata import OpenMetadataClient # OpenMetadataClient уже async

# Определения новых инструментов

SEARCH_METADATA_TOOL = Tool(
    name="search_metadata",
    description="Search for metadata entities in OpenMetadata with filtering.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string (e.g., 'sales fact', 'owner:John Doe', 'tags:PII').",
                "default": "*",
            },
            "entity_type": {
                "type": "string",
                "description": "Type of entity to search (e.g., table, dashboard, topic). Empty for all.",
                "default": "",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return.",
                "default": 10,
            },
            "include_deleted": {
                "type": "boolean",
                "description": "Whether to include deleted entities in results.",
                "default": False,
            },
        },
    },
)

GET_ENTITY_DETAILS_TOOL = Tool(
    name="get_entity_details",
    description="Get detailed information for a specific metadata entity.",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": "Type of the entity (plural, e.g., 'tables', 'dashboards', 'topics').",
            },
            "fqn": {
                "type": "string",
                "description": "Fully Qualified Name of the entity.",
            },
            "fields": {
                "type": "string",
                "description": "Comma-separated list of fields to retrieve (e.g., 'owner,tags,description'). '*' for all.",
                "default": "*",
            },
        },
        "required": ["entity_type", "fqn"],
    },
)

CREATE_GLOSSARY_TOOL = Tool(
    name="create_glossary",
    description="Create a new glossary.",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Unique name of the glossary."},
            "description": {"type": "string", "description": "Description of the glossary."},
            "owners": {
                "type": "array",
                "items": {"type": "object", "properties": {"id": {"type": "string"}, "type": {"type": "string"}}},
                "description": "Optional. List of owner references e.g., [{'id': 'uuid', 'type': 'user'}]. Needs prior resolution of names to IDs.",
                "default": [],
            },
            "reviewers": {
                "type": "array",
                "items": {"type": "object", "properties": {"id": {"type": "string"}, "type": {"type": "string"}}},
                "description": "Optional. List of reviewer references. Needs prior resolution of names to IDs.",
                "default": [],
            },
            # "tags": { # Теги можно добавить, если нужно
            #     "type": "array",
            #     "items": {"type": "object", "properties": {"tagFQN": {"type": "string"}}},
            #     "description": "Optional. List of tags to apply.",
            #     "default": []
            # }
        },
        "required": ["name", "description"],
    },
)

CREATE_GLOSSARY_TERM_TOOL = Tool(
    name="create_glossary_term",
    description="Create a new term within a glossary.",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of the glossary term."},
            "glossary_fqn": {
                "type": "string",
                "description": "Fully Qualified Name of the parent glossary.",
            },
            "description": {"type": "string", "description": "Description of the term."},
            "parent_term_fqn": {
                "type": "string",
                "description": "Optional. FQN of the parent glossary term for hierarchical terms.",
                "default": None, # Явное указание, что может быть null/None
            },
            "owners": {
                "type": "array",
                "items": {"type": "object", "properties": {"id": {"type": "string"}, "type": {"type": "string"}}},
                "description": "Optional. List of owner references. Needs prior resolution of names to IDs.",
                "default": [],
            },
            "synonyms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional. List of synonyms for the term.",
                "default": [],
            },
            # "related_terms_fqn": {
            #     "type": "array",
            #     "items": {"type": "string"},
            #     "description": "Optional. List of FQNs of related terms.",
            #     "default": []
            # },
            # "tags": {
            #     "type": "array",
            #     "items": {"type": "object", "properties": {"tagFQN": {"type": "string"}}},
            #     "description": "Optional. List of tags to apply.",
            #     "default": []
            # }
        },
        "required": ["name", "glossary_fqn", "description"],
    },
)

PATCH_ENTITY_TOOL = Tool(
    name="patch_entity",
    description="Update an entity using JSON Patch operations (RFC 6902).",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": "Type of the entity to patch (plural, e.g., 'tables', 'dashboards').",
            },
            "fqn": {
                "type": "string",
                "description": "Fully Qualified Name of the entity to patch.",
            },
            "patch_operations": {
                "type": "array",
                "items": {"type": "object"}, # Каждая операция - это объект {"op": "...", "path": "...", "value": ...}
                "description": "List of JSON Patch operations. Example: [{'op': 'add', 'path': '/description', 'value': 'New desc'}]",
            },
        },
        "required": ["entity_type", "fqn", "patch_operations"],
    },
)

GET_ENTITY_LINEAGE_TOOL = Tool(
    name="get_entity_lineage",
    description="Get lineage information for an entity.",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": "Type of the entity (singular, e.g., 'table', 'dashboard', 'pipeline').",
            },
            "entity_id": { # Изменено с FQN на ID, как ожидает обновленный клиент
                "type": "string",
                "description": "UUID of the entity for which to fetch lineage.",
            },
            "upstream_depth": {
                "type": "integer",
                "description": "Depth of upstream lineage to fetch.",
                "default": 1,
            },
            "downstream_depth": {
                "type": "integer",
                "description": "Depth of downstream lineage to fetch.",
                "default": 1,
            },
            "include_deleted": {
                "type": "boolean",
                "description": "Whether to include deleted entities in lineage.",
                "default": False,
            }
        },
        "required": ["entity_type", "entity_id"],
    },
)


def list_all_tools() -> List[Tool]:
    """Returns a list of all available tools."""
    return [
        SEARCH_METADATA_TOOL,
        GET_ENTITY_DETAILS_TOOL,
        CREATE_GLOSSARY_TOOL,
        CREATE_GLOSSARY_TERM_TOOL,
        PATCH_ENTITY_TOOL,
        GET_ENTITY_LINEAGE_TOOL,
    ]


async def call_tool(name: str, arguments: Dict[str, Any], client: OpenMetadataClient) -> List[TextContent]:
    """
    Calls the specified tool with the given arguments using the OpenMetadata client.
    This function is now asynchronous.
    """
    results: Any = {} # Инициализация results
    error_message: Optional[str] = None

    try:
        if name == SEARCH_METADATA_TOOL.name:
            query = arguments.get("query", "*")
            entity_type = arguments.get("entity_type", "")
            limit = arguments.get("limit", 10)
            include_deleted = arguments.get("include_deleted", False)
            results = await client.search_metadata(
                query=query,
                entity_type=entity_type if entity_type else None, # Pass None if empty string for client
                limit=limit,
                include_deleted=include_deleted,
            )
        elif name == GET_ENTITY_DETAILS_TOOL.name:
            entity_type = arguments["entity_type"]
            fqn = arguments["fqn"]
            fields = arguments.get("fields", "*")
            results = await client.get_entity(entity_type=entity_type, fqn=fqn, fields=fields)
        elif name == CREATE_GLOSSARY_TOOL.name:
            # Важно: 'owners' и 'reviewers' должны быть переданы как [{'id': 'uuid', 'type': 'user/team'}]
            # Если передаются имена, их нужно предварительно разрешить в ID.
            # В inputSchema указан формат, но реальное разрешение не делается здесь.
            results = await client.create_glossary(
                name=arguments["name"],
                description=arguments["description"],
                owners=arguments.get("owners"), # Передаем как есть
                reviewers=arguments.get("reviewers"), # Передаем как есть
                # tags=arguments.get("tags") # Если будет добавлено
            )
        elif name == CREATE_GLOSSARY_TERM_TOOL.name:
            # Аналогично 'owners' для create_glossary
            results = await client.create_glossary_term(
                name=arguments["name"],
                glossary_fqn=arguments["glossary_fqn"],
                description=arguments["description"],
                parent_term_fqn=arguments.get("parent_term_fqn"),
                owners=arguments.get("owners"), # Передаем как есть
                synonyms=arguments.get("synonyms"),
                # related_terms_fqn=arguments.get("related_terms_fqn"), # Если будет добавлено
                # tags=arguments.get("tags") # Если будет добавлено
            )
        elif name == PATCH_ENTITY_TOOL.name:
            results = await client.patch_entity(
                entity_type=arguments["entity_type"],
                fqn=arguments["fqn"],
                patch_data=arguments["patch_operations"],
            )
        elif name == GET_ENTITY_LINEAGE_TOOL.name:
            results = await client.get_lineage(
                entity_type=arguments["entity_type"], # singular
                entity_id=arguments["entity_id"], # UUID
                upstream_depth=arguments.get("upstream_depth", 1),
                downstream_depth=arguments.get("downstream_depth", 1),
                include_deleted=arguments.get("include_deleted", False)
            )
        else:
            error_message = f"Unknown tool: {name}"

    except KeyError as e: # Обработка отсутствия обязательных аргументов
        error_message = f"Missing required argument '{e.args[0]}' for tool '{name}'."
    except Exception as e: # Общая обработка ошибок от клиента или других проблем
        # Логирование ошибки можно добавить здесь, если оно централизовано
        error_message = f"Error calling tool '{name}': {type(e).__name__} - {str(e)}"

    if error_message:
        # В случае ошибки, возвращаем TextContent с сообщением об ошибке
        # Можно также логировать ошибку здесь или в вызывающем коде.
        # import logging
        # logging.error(error_message)
        return [TextContent(type="error", text=error_message)] # или type="text"

    # Преобразование результата в строку для TextContent
    # Используем json.dumps для красивого вывода словарей/списков
    import json
    if isinstance(results, (dict, list)):
        try:
            text_results = json.dumps(results, indent=2, ensure_ascii=False)
        except TypeError: # Если в результатах есть что-то несериализуемое в JSON
            text_results = str(results)
    else:
        text_results = str(results)

    return [TextContent(type="text", text=text_results)]
