"""Paperless-ngx API client for document upload integration."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx
from ..config import Config

logger = logging.getLogger(__name__)


class PaperlessUploadError(Exception):
    """Exception raised when paperless-ngx upload fails."""

    pass


class PaperlessClient:
    """Client for interacting with paperless-ngx API."""

    def __init__(self, config: Config):
        """Initialize paperless client with configuration.

        Args:
            config: Application configuration with paperless settings
        """
        self.config = config
        self.base_url = (
            config.paperless_url.rstrip("/") if config.paperless_url else None
        )
        self.headers = (
            {
                "Authorization": f"Token {config.paperless_token}",
                "Content-Type": "application/json",
            }
            if config.paperless_token
            else {}
        )

    def is_enabled(self) -> bool:
        """Check if paperless integration is enabled and properly configured.

        Returns:
            bool: True if paperless is enabled and configured
        """
        return (
            self.config.paperless_enabled
            and self.base_url is not None
            and self.config.paperless_token is not None
        )

    def test_connection(self) -> bool:
        """Test connection to paperless-ngx API.

        Returns:
            bool: True if connection successful

        Raises:
            PaperlessUploadError: If connection test fails
        """
        if not self.is_enabled():
            raise PaperlessUploadError(
                "Paperless integration not enabled or configured"
            )

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/documents/",
                    headers=self.headers,
                    params={"page_size": 1},
                )
                response.raise_for_status()
                logger.info("Successfully connected to paperless-ngx API")
                return True

        except httpx.RequestError as e:
            error_msg = f"Failed to connect to paperless-ngx: {str(e)}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_msg = f"Paperless API returned error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e

    def upload_document(
        self,
        file_path: Path,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        correspondent: Optional[str] = None,
        document_type: Optional[str] = None,
        storage_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a document to paperless-ngx.

        Args:
            file_path: Path to the PDF file to upload
            title: Document title (defaults to filename)
            tags: List of tags to apply (uses config defaults if None)
            correspondent: Correspondent name (uses config default if None)
            document_type: Document type (uses config default if None)
            storage_path: Storage path name (uses config default if None)

        Returns:
            Dict containing upload response with document ID and status

        Raises:
            PaperlessUploadError: If upload fails
        """
        if not self.is_enabled():
            raise PaperlessUploadError(
                "Paperless integration not enabled or configured"
            )

        if not file_path.exists():
            raise PaperlessUploadError(f"File not found: {file_path}")

        # Prepare metadata
        title = title or file_path.stem
        tags = tags or self.config.paperless_tags or []
        correspondent = correspondent or self.config.paperless_correspondent
        document_type = document_type or self.config.paperless_document_type
        storage_path = storage_path or self.config.paperless_storage_path

        # Resolve names to IDs
        resolved_tags = self._resolve_tags(tags) if tags else []
        resolved_correspondent = (
            self._resolve_correspondent(correspondent) if correspondent else None
        )
        resolved_document_type = (
            self._resolve_document_type(document_type) if document_type else None
        )
        resolved_storage_path = (
            self._resolve_storage_path(storage_path) if storage_path else None
        )

        logger.debug(
            f"Upload metadata resolution: tags={tags} -> {resolved_tags}, correspondent={correspondent} -> {resolved_correspondent}, document_type={document_type} -> {resolved_document_type}, storage_path={storage_path} -> {resolved_storage_path}"
        )

        # Prepare form data
        form_data = {
            "title": title,
            "created": None,  # Let paperless detect from document
        }

        # Add optional fields if configured (now using IDs)
        # For tags, paperless expects individual form fields like tags.0, tags.1, etc.
        if resolved_tags:
            for i, tag_id in enumerate(resolved_tags):
                form_data[f"tags.{i}"] = str(tag_id)
        if resolved_correspondent:
            form_data["correspondent"] = str(resolved_correspondent)
        if resolved_document_type:
            form_data["document_type"] = str(resolved_document_type)
        if resolved_storage_path:
            form_data["storage_path"] = str(resolved_storage_path)

        try:
            with httpx.Client(timeout=60.0) as client:
                # Upload file using multipart form
                files = {
                    "document": (
                        file_path.name,
                        file_path.read_bytes(),
                        "application/pdf",
                    )
                }

                # Remove Content-Type header for multipart upload
                upload_headers = {
                    k: v for k, v in self.headers.items() if k != "Content-Type"
                }

                response = client.post(
                    f"{self.base_url}/api/documents/post_document/",
                    data=form_data,
                    files=files,
                    headers=upload_headers,
                )
                response.raise_for_status()

                result = response.json()
                logger.debug(f"Upload response: {result}, type: {type(result)}")

                # Paperless-ngx post_document endpoint returns a task ID (string) or document object (dict)
                if isinstance(result, str):
                    # Task ID returned - document is being processed
                    task_id = result
                    document_id = None
                    logger.info(
                        f"Successfully queued document for processing: {title} (Task ID: {task_id})"
                    )
                elif isinstance(result, dict):
                    # Direct document object returned
                    document_id = result.get("id")
                    task_id = None
                    logger.info(
                        f"Successfully uploaded document: {title} (Document ID: {document_id})"
                    )
                else:
                    # Unexpected response format
                    task_id = None
                    document_id = None
                    logger.warning(
                        f"Unexpected response format for upload: {type(result)}"
                    )

                return {
                    "success": True,
                    "document_id": document_id,
                    "task_id": task_id,
                    "title": title,
                    "file_path": str(file_path),
                    "tags": tags,
                    "correspondent": correspondent,
                    "document_type": document_type,
                    "storage_path": storage_path,
                    "response": result,
                }

        except httpx.RequestError as e:
            error_msg = f"Failed to upload {file_path.name} to paperless-ngx: {str(e)}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_msg = f"Paperless upload failed with status {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e

    def upload_multiple_documents(
        self,
        file_paths: List[Path],
        base_title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        correspondent: Optional[str] = None,
        document_type: Optional[str] = None,
        storage_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload multiple documents to paperless-ngx.

        Args:
            file_paths: List of PDF file paths to upload
            base_title: Base title for documents (will be numbered)
            tags: List of tags to apply to all documents
            correspondent: Correspondent name for all documents
            document_type: Document type for all documents
            storage_path: Storage path name for all documents

        Returns:
            Dict containing upload results for all documents
        """
        if not file_paths:
            return {"success": True, "uploads": [], "errors": []}

        results = {"success": True, "uploads": [], "errors": []}

        for i, file_path in enumerate(file_paths, 1):
            try:
                # Generate numbered title if base_title provided
                if base_title:
                    title = f"{base_title} - Statement {i}"
                else:
                    title = None

                upload_result = self.upload_document(
                    file_path=file_path,
                    title=title,
                    tags=tags,
                    correspondent=correspondent,
                    document_type=document_type,
                    storage_path=storage_path,
                )
                results["uploads"].append(upload_result)
                logger.info(f"Successfully uploaded {file_path.name}")

            except PaperlessUploadError as e:
                error_info = {"file_path": str(file_path), "error": str(e)}
                results["errors"].append(error_info)
                results["success"] = False
                logger.error(f"Failed to upload {file_path.name}: {e}")

        return results

    def _resolve_tags(self, tag_names: List[str]) -> List[int]:
        """Resolve tag names to tag IDs, creating tags if they don't exist.

        Args:
            tag_names: List of tag names to resolve

        Returns:
            List of tag IDs

        Raises:
            PaperlessUploadError: If API call fails
        """
        tag_ids = []

        for tag_name in tag_names:
            try:
                with httpx.Client(timeout=30.0) as client:
                    # First try to find existing tag
                    response = client.get(
                        f"{self.base_url}/api/tags/",
                        headers=self.headers,
                        params={"name__iexact": tag_name},
                    )
                    response.raise_for_status()

                    results = response.json()["results"]
                    if results:
                        # Tag exists, use its ID
                        tag_ids.append(results[0]["id"])
                        logger.debug(
                            f"Found existing tag '{tag_name}' with ID {results[0]['id']}"
                        )
                    else:
                        # Tag doesn't exist, create it
                        logger.debug(f"Tag '{tag_name}' not found, creating new tag")
                        create_response = client.post(
                            f"{self.base_url}/api/tags/",
                            headers=self.headers,
                            json={"name": tag_name},
                        )
                        create_response.raise_for_status()

                        new_tag = create_response.json()
                        tag_ids.append(new_tag["id"])
                        logger.info(
                            f"Created new tag '{tag_name}' with ID {new_tag['id']}"
                        )

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Failed to resolve tag '{tag_name}': {e}")
                # Skip this tag rather than failing the entire upload
                continue

        return tag_ids

    def _resolve_correspondent(self, correspondent_name: str) -> Optional[int]:
        """Resolve correspondent name to correspondent ID, creating if it doesn't exist.

        Args:
            correspondent_name: Name of correspondent to resolve

        Returns:
            Correspondent ID or None if resolution fails
        """
        if not correspondent_name:
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                # First try to find existing correspondent
                response = client.get(
                    f"{self.base_url}/api/correspondents/",
                    headers=self.headers,
                    params={"name__iexact": correspondent_name},
                )
                response.raise_for_status()

                results = response.json()["results"]
                if results:
                    # Correspondent exists, use its ID
                    logger.debug(
                        f"Found existing correspondent '{correspondent_name}' with ID {results[0]['id']}"
                    )
                    return results[0]["id"]
                else:
                    # Correspondent doesn't exist, create it
                    create_response = client.post(
                        f"{self.base_url}/api/correspondents/",
                        headers=self.headers,
                        json={"name": correspondent_name},
                    )
                    create_response.raise_for_status()

                    new_correspondent = create_response.json()
                    logger.info(
                        f"Created new correspondent '{correspondent_name}' with ID {new_correspondent['id']}"
                    )
                    return new_correspondent["id"]

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(
                f"Failed to resolve correspondent '{correspondent_name}': {e}"
            )
            return None

    def _resolve_document_type(self, document_type_name: str) -> Optional[int]:
        """Resolve document type name to document type ID, creating if it doesn't exist.

        Args:
            document_type_name: Name of document type to resolve

        Returns:
            Document type ID or None if resolution fails
        """
        if not document_type_name:
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                # First try to find existing document type
                response = client.get(
                    f"{self.base_url}/api/document_types/",
                    headers=self.headers,
                    params={"name__iexact": document_type_name},
                )
                response.raise_for_status()

                results = response.json()["results"]
                if results:
                    # Document type exists, use its ID
                    logger.debug(
                        f"Found existing document type '{document_type_name}' with ID {results[0]['id']}"
                    )
                    return results[0]["id"]
                else:
                    # Document type doesn't exist, create it
                    create_response = client.post(
                        f"{self.base_url}/api/document_types/",
                        headers=self.headers,
                        json={"name": document_type_name},
                    )
                    create_response.raise_for_status()

                    new_document_type = create_response.json()
                    logger.info(
                        f"Created new document type '{document_type_name}' with ID {new_document_type['id']}"
                    )
                    return new_document_type["id"]

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(
                f"Failed to resolve document type '{document_type_name}': {e}"
            )
            return None

    def _resolve_storage_path(self, storage_path_name: str) -> Optional[int]:
        """Resolve storage path name to storage path ID, creating if it doesn't exist.

        Args:
            storage_path_name: Name of storage path to resolve

        Returns:
            Storage path ID or None if resolution fails
        """
        if not storage_path_name:
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                # First try to find existing storage path
                response = client.get(
                    f"{self.base_url}/api/storage_paths/",
                    headers=self.headers,
                    params={"name__iexact": storage_path_name},
                )
                response.raise_for_status()

                results = response.json()["results"]
                if results:
                    # Storage path exists, use its ID
                    logger.debug(
                        f"Found existing storage path '{storage_path_name}' with ID {results[0]['id']}"
                    )
                    return results[0]["id"]
                else:
                    # Storage path doesn't exist, create it
                    create_response = client.post(
                        f"{self.base_url}/api/storage_paths/",
                        headers=self.headers,
                        json={
                            "name": storage_path_name,
                            "path": f"/{storage_path_name.lower().replace(' ', '_')}/",
                        },
                    )
                    create_response.raise_for_status()

                    new_storage_path = create_response.json()
                    logger.info(
                        f"Created new storage path '{storage_path_name}' with ID {new_storage_path['id']}"
                    )
                    return new_storage_path["id"]

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Failed to resolve storage path '{storage_path_name}': {e}")
            return None
