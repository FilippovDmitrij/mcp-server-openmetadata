#!/usr/bin/env python3
"""
OpenMetadata Client
Provides methods to interact with OpenMetadata API
"""

import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp

# Configure logging - можно оставить или убрать, если в проекте своя система логирования
logger = logging.getLogger(__name__)


class OpenMetadataError(Exception):
    """Base exception for OpenMetadata client errors."""
    pass


class OpenMetadataClient:
    """Client for interacting with OpenMetadata API"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        if not self.base_url.startswith(('http://', 'https://')):
            raise OpenMetadataError(f"Invalid base_url: {base_url}. Must include scheme (http/https).")
        self.token = token
        self._session: Optional[aiohttp.ClientSession] = None # Изменено на приватное

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close_session(self):
        """Close the aiohttp session if it exists and is open."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to OpenMetadata API"""
        session = await self._get_session()
        url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))

        try:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                # Некоторые API OpenMetadata могут возвращать 204 No Content или другие не-JSON ответы
                if response.status == 204:
                    return {} # Возвращаем пустой dict для No Content
                # Проверяем Content-Type перед попыткой .json()
                if 'application/json' in response.headers.get('Content-Type', ''):
                    return await response.json()
                else:
                    # Если не JSON, вернуть текстовый ответ или ошибку
                    text_response = await response.text()
                    logger.warning(
                        f"API response for {method} {url} is not JSON: {response.status} - {text_response}"
                    )
                    # В зависимости от требований, можно вернуть {'raw_response': text_response} или кинуть ошибку
                    return {"raw_response": text_response, "status_code": response.status}

        except aiohttp.ClientResponseError as e:
            logger.error(f"API request failed: {method} {url} - Status: {e.status}, Message: {e.message}, Headers: {e.headers}")
            # Попытаемся прочитать тело ошибки, если оно есть
            error_body = await e.response.text() if e.response else "No response body"
            logger.error(f"Error body: {error_body}")
            raise OpenMetadataError(f"API request to {method} {url} failed with status {e.status}: {e.message}. Body: {error_body}") from e
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {method} {url} - {e}")
            raise OpenMetadataError(f"API request to {method} {url} failed: {e}") from e
        except Exception as e: # Общий Exception для непредвиденных ошибок
            logger.error(f"An unexpected error occurred during API request: {method} {url} - {e}")
            raise OpenMetadataError(f"Unexpected error for {method} {url}: {e}") from e


    async def search_metadata(self, query: str = "*", entity_type: Optional[str] = None,
                              limit: int = 10, include_deleted: bool = False) -> Dict[str, Any]:
        """Search metadata entities"""
        params: Dict[str, Any] = { # Указываем тип params
            'q': query,
            'size': limit,
            'deleted': str(include_deleted).lower()
        }

        if entity_type:
            params['index'] = entity_type # 'index' это правильный параметр для OpenMetadata search API

        return await self._make_request('GET', 'v1/search/query', params=params)

    async def get_entity(self, entity_type: str, fqn: str, fields: str = "*") -> Dict[str, Any]:
        """Get entity details by FQN. entity_type should be plural (e.g., tables, dashboards)"""
        params = {'fields': fields}
        return await self._make_request('GET', f'v1/{entity_type}/name/{fqn}', params=params)

    async def create_glossary(self, name: str, description: str, owners: Optional[List[Dict[str, str]]] = None,
                              reviewers: Optional[List[Dict[str, str]]] = None,
                              tags: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Create a new glossary. owners/reviewers should be list of {'id': 'uuid', 'type': 'user'/'team'}"""
        data: Dict[str, Any] = {
            'name': name,
            'displayName': name, # Часто displayName используется для отображения
            'description': description,
            'reviewers': reviewers or [],
            'owners': owners or [],
            'tags': tags or []
        }
        # OpenMetadata API ожидает 'owners' и 'reviewers' как список объектов со ссылками (id, type)
        # Пример: data['owners'] = [{'id': owner_uuid, 'type': 'user'}]
        # Это должно быть подготовлено перед вызовом этого метода или внутри него, если передаются просто имена.
        # В коде из первого сообщения было: data['owners'] = [{'name': owner, 'type': 'user'} for owner in owners]
        # Это неверно, OpenMetadata ожидает ID существующих пользователей/команд.
        # Для простоты, пока оставляю как есть, но это нужно будет исправить для реальной работы.
        # Если owners/reviewers передаются как списки FQN или имен, потребуется дополнительный шаг по их разрешению в ID.

        return await self._make_request('POST', 'v1/glossaries', json=data)

    async def create_glossary_term(self, name: str, glossary_fqn: str, description: str,
                                   parent_term_fqn: Optional[str] = None,
                                   owners: Optional[List[Dict[str, str]]] = None, # Same as for glossary
                                   synonyms: Optional[List[str]] = None,
                                   related_terms_fqn: Optional[List[str]] = None,
                                   tags: Optional[List[Dict[str, str]]] = None
                                   ) -> Dict[str, Any]:
        """Create a new glossary term. glossary_fqn is FQN of the parent glossary."""
        data: Dict[str, Any] = {
            'name': name,
            'displayName': name,
            'description': description,
            'glossary': {'fullyQualifiedName': glossary_fqn, 'type': 'glossary'},
            'synonyms': synonyms or [],
            'owners': owners or [],
            'tags': tags or []
        }

        if parent_term_fqn:
            data['parent'] = {'fullyQualifiedName': parent_term_fqn, 'type': 'glossaryTerm'}

        if related_terms_fqn:
            data['relatedTerms'] = [{'fullyQualifiedName': term_fqn, 'type': 'glossaryTerm'} for term_fqn in related_terms_fqn]


        return await self._make_request('POST', 'v1/glossaryTerms', json=data)

    async def patch_entity(self, entity_type: str, fqn: str, patch_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Patch an entity with JSON patch operations. entity_type is plural (e.g., tables)"""
        # Заголовок Content-Type для PATCH должен быть 'application/json-patch+json'
        # _make_request устанавливает 'application/json' по умолчанию.
        # Мы можем либо передать headers в _make_request, либо временно изменить их в сессии.
        # Предпочтительнее передавать явно для конкретного запроса.
        custom_headers = {'Content-Type': 'application/json-patch+json'}

        # Сохраняем оригинальные заголовки сессии, если они есть
        session = await self._get_session()
        original_content_type = session.headers.get('Content-Type')

        session.headers['Content-Type'] = custom_headers['Content-Type']

        try:
            result = await self._make_request('PATCH', f'v1/{entity_type}/name/{fqn}', json=patch_data)
        finally:
            # Восстанавливаем оригинальный Content-Type в сессии
            if original_content_type:
                session.headers['Content-Type'] = original_content_type
            else:
                # Если его не было, удаляем, чтобы вернуться к поведению по умолчанию
                session.headers.pop('Content-Type', None)
                session.headers['Content-Type'] = 'application/json' # Восстанавливаем стандартный

        return result

    async def get_lineage(self, entity_type: str, entity_id: str, # OpenMetadata API использует ID для lineage, не FQN
                          upstream_depth: int = 1, downstream_depth: int = 1,
                          include_deleted: bool = False) -> Dict[str, Any]:
        """Get entity lineage by ID. entity_type is singular (e.g., table, dashboard)"""
        params = {
            'upstreamDepth': upstream_depth,
            'downstreamDepth': downstream_depth,
            'includeDeleted': str(include_deleted).lower()
        }
        # Эндпоинт API: /api/v1/lineage/{entityType}/{entityId}
        return await self._make_request('GET', f'v1/lineage/{entity_type}/{entity_id}', params=params)

    # Дополнительные методы из исходного файла src/openmetadata.py (на httpx),
    # которые не были в вашем первом примере, но могут быть полезны.
    # Их нужно будет адаптировать под aiohttp, если они нужны.
    # Пока я их закомментирую, чтобы не было конфликта имен и чтобы сфокусироваться на запрошенных.
    # Если они нужны, их нужно будет переписать с использованием self._make_request и async/await.

    # def list_tables(...)
    # def get_table(...)
    # def get_table_by_name(...)
    # def create_table(...)
    # def update_table(...)
    # def delete_table(...)

# Пример использования (для тестирования, можно удалить)
# async def main_test():
#     # Замените на ваши реальные данные
#     OM_BASE_URL = os.getenv("OPENMETADATA_URL", "http://localhost:8585/api")
#     OM_TOKEN = os.getenv("OPENMETADATA_TOKEN", "your_jwt_token_here")

#     if OM_TOKEN == "your_jwt_token_here":
#         print("Please set OPENMETADATA_URL and OPENMETADATA_TOKEN environment variables.")
#         return

#     client = OpenMetadataClient(base_url=OM_BASE_URL, token=OM_TOKEN)
#     try:
#         # Пример поиска таблиц
#         print("Searching tables...")
#         search_results = await client.search_metadata(query="dim*", entity_type="table", limit=5)
#         print(json.dumps(search_results, indent=2))

#         # Пример получения деталей таблицы (замените FQN на существующий)
#         # table_fqn = "your_service.your_database.your_schema.your_table"
#         # print(f"\nGetting details for table: {table_fqn}")
#         # table_details = await client.get_entity("tables", table_fqn, fields="columns,tags,owner")
#         # print(json.dumps(table_details, indent=2))

#         # Пример создания глоссария (потребует ID существующих пользователей/команд для owners/reviewers)
#         # print("\nCreating glossary...")
#         # new_glossary = await client.create_glossary(
#         #     name="MyNewGlossary",
#         #     description="A test glossary created via API."
#         #     # owners=[{'id': 'user_uuid', 'type': 'user'}] # Замените на реальные ID
#         # )
#         # print(json.dumps(new_glossary, indent=2))
#         # glossary_fqn = new_glossary.get('fullyQualifiedName')

#         # if glossary_fqn:
#         #     print("\nCreating glossary term...")
#         #     new_term = await client.create_glossary_term(
#         #         name="MyNewTerm",
#         #         glossary_fqn=glossary_fqn,
#         #         description="A test term."
#         #     )
#         #     print(json.dumps(new_term, indent=2))


#     except OpenMetadataError as e:
#         print(f"An error occurred: {e}")
#     finally:
#         await client.close_session()

# if __name__ == "__main__":
#     import asyncio
#     import os
#     import json # для pretty print в main_test
#     logging.basicConfig(level=logging.INFO)
#     asyncio.run(main_test())
