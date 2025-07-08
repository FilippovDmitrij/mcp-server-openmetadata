from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from src.openmetadata import OpenMetadataClient

# Valid entity types for OpenMetadata search API (/api/v1/search/query)
VALID_SEARCH_ENTITY_TYPES = [
    # Core Data Assets
    "table",
    "database",
    "databaseSchema",
    "dashboard",
    "chart",
    "pipeline",
    "topic",
    "container",
    "storedProcedure",

    # ML and Analytics
    "mlmodel",
    "metric",
    "report",
    "dataProduct",

    # Search and Data Indices
    "searchIndex",

    # Services
    "databaseService",
    "dashboardService",
    "pipelineService",
    "messagingService",
    "metadataService",
    "storageService",
    "searchService",
    "mlmodelService",
    "apiService",

    # Governance and Glossary
    "glossary",
    "glossaryTerm",
    "tag",
    "classification",
    "policy",
    "domain",

    # Data Quality
    "testCase",
    "testSuite",
    "testDefinition",
    "dataQualityDashboard",

    # Users and Teams
    "user",
    "team",
    "role",
    "persona",

    # Automation and Workflows
    "ingestionPipeline",
    "automationWorkflow",
    "application",
    "bot",
    "workflow",

    # Analytics and Insights
    "kpiObjective",
    "dataInsightChart",
    "dataInsightCustomChart",
    "webAnalyticEvent",
    "customMetric",

    # API and Functions
    "apiEndpoint",
    "apiCollection",
    "serverlessFunction",
    "query",

    # Communication and Alerts
    "eventSubscription",
    "alert",
    "thread",
    "announcement",

    # Configuration and Settings
    "customProperty",
    "knowledgePanel",
    "page"
]

# Valid entity types for direct API endpoints (for get_entity_details, patch_entity, etc.)
# These correspond to the API endpoint paths: /api/v1/{entity_type}/name/{fqn}
VALID_API_ENTITY_TYPES = [
    # Core Data Assets (plural in endpoints, but entity_type uses singular)
    "tables",  # /api/v1/tables
    "databases",  # /api/v1/databases
    "databaseSchemas",  # /api/v1/databaseSchemas
    "dashboards",  # /api/v1/dashboards
    "charts",  # /api/v1/charts
    "pipelines",  # /api/v1/pipelines
    "topics",  # /api/v1/topics
    "containers",  # /api/v1/containers
    "storedProcedures",  # /api/v1/storedProcedures

    # ML and Analytics
    "mlmodels",  # /api/v1/mlmodels
    "metrics",  # /api/v1/metrics
    "reports",  # /api/v1/reports
    "dataProducts",  # /api/v1/dataProducts

    # Search
    "searchIndexes",  # /api/v1/searchIndexes

    # Services
    "services/databaseService",  # /api/v1/services/databaseService
    "services/dashboardService",  # /api/v1/services/dashboardService
    "services/pipelineService",  # /api/v1/services/pipelineService
    "services/messagingService",  # /api/v1/services/messagingService
    "services/metadataService",  # /api/v1/services/metadataService
    "services/storageService",  # /api/v1/services/storageService
    "services/searchService",  # /api/v1/services/searchService
    "services/mlmodelService",  # /api/v1/services/mlmodelService

    # Governance
    "glossaries",  # /api/v1/glossaries
    "glossaryTerms",  # /api/v1/glossaryTerms
    "tags",  # /api/v1/tags
    "classification",  # /api/v1/classification
    "policies",  # /api/v1/policies
    "domains",  # /api/v1/domains

    # Data Quality
    "testCases",  # /api/v1/testCases
    "testSuites",  # /api/v1/testSuites
    "testDefinitions",  # /api/v1/testDefinitions

    # Users and Teams
    "users",  # /api/v1/users
    "teams",  # /api/v1/teams
    "roles",  # /api/v1/roles
    "personas",  # /api/v1/personas

    # Automation
    "automations/workflows",  # /api/v1/automations/workflows
    "apps",  # /api/v1/apps
    "bots",  # /api/v1/bots
]

# Tool definitions
SEARCH_METADATA_TOOL = Tool(
    name="search_metadata",
    description="Search metadata entities with optional filters. Use this to find entities across OpenMetadata.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string. Use '*' for all entities, or specific terms to search",
                "default": "*",
            },
            "entity_type": {
                "type": "string",
                "description": f"Entity type to search (search index name). Most common: table, database, dashboard, topic, pipeline, glossaryTerm, user, team. Valid values: {', '.join(sorted(VALID_SEARCH_ENTITY_TYPES))}",
                "enum": VALID_SEARCH_ENTITY_TYPES,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 1000,
            },
            "include_deleted": {
                "type": "boolean",
                "description": "Whether to include deleted entities in search results",
                "default": False,
            },
        },
    },
)

GET_ENTITY_DETAILS_TOOL = Tool(
    name="get_entity_details",
    description="Get detailed information about a specific entity by its fully qualified name (FQN)",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": f"API endpoint entity type (plural form). Common examples: tables, databases, dashboards, topics, pipelines.",
                "enum": VALID_API_ENTITY_TYPES,
            },
            "fqn": {
                "type": "string",
                "description": "Fully qualified name of the entity (e.g., 'service.database.schema.table')",
            },
            "fields": {
                "type": "string",
                "description": "Comma-separated list of fields to include. Use '*' for all fields, or specify: columns,tags,owner,domain,dataModel,etc.",
                "default": "*",
            },
        },
        "required": ["entity_type", "fqn"],
    },
)

CREATE_GLOSSARY_TOOL = Tool(
    name="create_glossary",
    description="Create a new glossary for organizing business terms and definitions",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Glossary name (must be unique)"
            },
            "description": {
                "type": "string",
                "description": "Glossary description explaining its purpose"
            },
            "owners": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of owner usernames who can manage this glossary",
            },
            "reviewers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of reviewer usernames who can approve terms",
            },
        },
        "required": ["name", "description"],
    },
)

CREATE_GLOSSARY_TERM_TOOL = Tool(
    name="create_glossary_term",
    description="Create a new glossary term within an existing glossary",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Term name (business term)"
            },
            "glossary": {
                "type": "string",
                "description": "Parent glossary name where this term belongs"
            },
            "description": {
                "type": "string",
                "description": "Term definition and explanation"
            },
            "parent_term": {
                "type": "string",
                "description": "Parent term name if this is a sub-term (optional)"
            },
            "owners": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of owner usernames responsible for this term",
            },
        },
        "required": ["name", "glossary", "description"],
    },
)

PATCH_ENTITY_TOOL = Tool(
    name="patch_entity",
    description="Update an entity using JSON Patch operations (RFC 6902)",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": f"API endpoint entity type (plural form). Valid values: {', '.join(sorted(VALID_API_ENTITY_TYPES))}",
                "enum": VALID_API_ENTITY_TYPES,
            },
            "fqn": {
                "type": "string",
                "description": "Fully qualified name of the entity to update"
            },
            "patch_operations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "op": {
                            "type": "string",
                            "enum": ["add", "remove", "replace", "move", "copy", "test"],
                            "description": "JSON Patch operation type"
                        },
                        "path": {
                            "type": "string",
                            "description": "JSON path to the field being modified (e.g., '/description', '/tags')"
                        },
                        "value": {
                            "description": "New value for the field (not needed for 'remove' operation)"
                        }
                    },
                    "required": ["op", "path"]
                },
                "description": "List of JSON Patch operations to apply",
            },
        },
        "required": ["entity_type", "fqn", "patch_operations"],
    },
)

GET_ENTITY_LINEAGE_TOOL = Tool(
    name="get_entity_lineage",
    description="Get data lineage information showing upstream and downstream dependencies",
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": f"API endpoint entity type (plural form). Valid values: {', '.join(sorted(VALID_API_ENTITY_TYPES))}",
                "enum": VALID_API_ENTITY_TYPES,
            },
            "fqn": {
                "type": "string",
                "description": "Fully qualified name of the entity to get lineage for"
            },
            "upstream_depth": {
                "type": "integer",
                "description": "How many levels of upstream dependencies to include",
                "default": 1,
                "minimum": 0,
                "maximum": 10,
            },
            "downstream_depth": {
                "type": "integer",
                "description": "How many levels of downstream dependencies to include",
                "default": 1,
                "minimum": 0,
                "maximum": 10,
            },
        },
        "required": ["entity_type", "fqn"],
    },
)


def list_all_tools() -> List[Tool]:
    """Return all available OpenMetadata tools."""
    return [
        SEARCH_METADATA_TOOL,
        GET_ENTITY_DETAILS_TOOL,
        CREATE_GLOSSARY_TOOL,
        CREATE_GLOSSARY_TERM_TOOL,
        PATCH_ENTITY_TOOL,
        GET_ENTITY_LINEAGE_TOOL,

    ]


def call_tool(name: str, arguments: Dict[str, Any], client: OpenMetadataClient) -> List[TextContent]:
    """Call a tool with the given arguments and return the results."""
    try:
        if name == SEARCH_METADATA_TOOL.name:
            # For search, use the search entity types (singular form)
            entity_type = arguments.get("entity_type")
            if entity_type and entity_type not in VALID_SEARCH_ENTITY_TYPES:
                return [TextContent(
                    type="text",
                    text=f"Invalid entity_type '{entity_type}' for search. Valid search types: {', '.join(sorted(VALID_SEARCH_ENTITY_TYPES))}"
                )]

            results = client.search_metadata(
                query=arguments.get("query", "*"),
                entity_type=entity_type,
                limit=arguments.get("limit", 10),
                include_deleted=arguments.get("include_deleted", False),
            )
            return [TextContent(type="text", text=str(results))]

        elif name == GET_ENTITY_DETAILS_TOOL.name:
            # For API calls, use the API entity types (plural form)
            entity_type = arguments["entity_type"]
            if entity_type not in VALID_API_ENTITY_TYPES:
                return [TextContent(
                    type="text",
                    text=f"Invalid entity_type '{entity_type}' for API calls. Valid API types: {', '.join(sorted(VALID_API_ENTITY_TYPES))}"
                )]

            results = client.get_entity_details(
                entity_type=entity_type,
                fqn=arguments["fqn"],
                fields=arguments.get("fields", "*"),
            )
            return [TextContent(type="text", text=str(results))]

        elif name == CREATE_GLOSSARY_TOOL.name:
            results = client.create_glossary(
                name=arguments["name"],
                description=arguments["description"],
                owners=arguments.get("owners"),
                reviewers=arguments.get("reviewers"),
            )
            return [TextContent(type="text", text=str(results))]

        elif name == CREATE_GLOSSARY_TERM_TOOL.name:
            results = client.create_glossary_term(
                name=arguments["name"],
                glossary=arguments["glossary"],
                description=arguments["description"],
                parent_term=arguments.get("parent_term"),
                owners=arguments.get("owners"),
            )
            return [TextContent(type="text", text=str(results))]

        elif name == PATCH_ENTITY_TOOL.name:
            entity_type = arguments["entity_type"]
            if entity_type not in VALID_API_ENTITY_TYPES:
                return [TextContent(
                    type="text",
                    text=f"Invalid entity_type '{entity_type}' for API calls. Valid API types: {', '.join(sorted(VALID_API_ENTITY_TYPES))}"
                )]

            results = client.patch_entity(
                entity_type=entity_type,
                fqn=arguments["fqn"],
                patch_data=arguments["patch_operations"],
            )
            return [TextContent(type="text", text=str(results))]

        elif name == GET_ENTITY_LINEAGE_TOOL.name:
            entity_type = arguments["entity_type"]
            if entity_type not in VALID_API_ENTITY_TYPES:
                return [TextContent(
                    type="text",
                    text=f"Invalid entity_type '{entity_type}' for API calls. Valid API types: {', '.join(sorted(VALID_API_ENTITY_TYPES))}"
                )]

            results = client.get_entity_lineage(
                entity_type=entity_type,
                fqn=arguments["fqn"],
                upstream_depth=arguments.get("upstream_depth", 1),
                downstream_depth=arguments.get("downstream_depth", 1),
            )
            return [TextContent(type="text", text=str(results))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]


# Helper function to convert between search and API entity types
def get_api_entity_type_from_search(search_entity_type: str) -> str:
    """Convert search entity type (singular) to API entity type (plural)."""
    mapping = {
        "table": "tables",
        "database": "databases",
        "databaseSchema": "databaseSchemas",
        "dashboard": "dashboards",
        "chart": "charts",
        "pipeline": "pipelines",
        "topic": "topics",
        "container": "containers",
        "storedProcedure": "storedProcedures",
        "mlmodel": "mlmodels",
        "metric": "metrics",
        "report": "reports",
        "dataProduct": "dataProducts",
        "searchIndex": "searchIndexes",
        "glossary": "glossaries",
        "glossaryTerm": "glossaryTerms",
        "tag": "tags",
        "policy": "policies",
        "domain": "domains",
        "testCase": "testCases",
        "testSuite": "testSuites",
        "testDefinition": "testDefinitions",
        "user": "users",
        "team": "teams",
        "role": "roles",
        "persona": "personas",
        "bot": "bots",
        # Services have special paths
        "databaseService": "services/databaseService",
        "dashboardService": "services/dashboardService",
        "pipelineService": "services/pipelineService",
        "messagingService": "services/messagingService",
        "metadataService": "services/metadataService",
        "storageService": "services/storageService",
        "searchService": "services/searchService",
        "mlmodelService": "services/mlmodelService",
    }
    return mapping.get(search_entity_type, search_entity_type)