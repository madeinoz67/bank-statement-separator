"""Paperless-ngx API client for document upload integration."""

import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def apply_tags_to_document(
        self, document_id: int, tags: List[str], wait_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """Apply additional tags to a document using bulk_edit API to preserve existing tags.

        This method uses the bulk_edit endpoint to ADD tags to a document without replacing
        existing system-applied tags. This is crucial for preserving paperless-ngx system
        rule tags while still applying our custom output tags.

        Args:
            document_id: ID of the document to apply tags to
            tags: List of tag names to apply
            wait_time: Wait time in seconds before applying tags (uses config default if None)

        Returns:
            Dict containing operation results

        Raises:
            PaperlessUploadError: If tag application fails
        """
        if not self.is_enabled():
            raise PaperlessUploadError(
                "Paperless integration not enabled or configured"
            )

        if not tags:
            logger.debug(f"No tags to apply to document {document_id}")
            return {"success": True, "tags_applied": 0}

        # Wait for document processing to complete before applying tags
        actual_wait_time = (
            wait_time if wait_time is not None else self.config.paperless_tag_wait_time
        )
        if actual_wait_time > 0:
            logger.debug(
                f"Waiting {actual_wait_time} seconds for document {document_id} processing to complete before applying tags"
            )
            import time

            time.sleep(actual_wait_time)

        try:
            # Resolve tag names to IDs
            tag_ids = self._resolve_tags(tags)
            if not tag_ids:
                logger.warning(f"No valid tag IDs resolved from tags: {tags}")
                return {"success": False, "error": "No valid tags resolved"}

            successful_applications = []
            failed_applications = []

            # Apply each tag individually using bulk_edit add_tag method
            # This preserves existing tags while adding new ones
            for i, tag_id in enumerate(tag_ids):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        response = client.post(
                            f"{self.base_url}/api/documents/bulk_edit/",
                            headers=self.headers,
                            json={
                                "documents": [document_id],
                                "method": "add_tag",
                                "parameters": {"tag": tag_id},
                            },
                        )
                        response.raise_for_status()

                        successful_applications.append(
                            {
                                "tag_name": tags[i],
                                "tag_id": tag_id,
                                "response": response.json(),
                            }
                        )

                        logger.debug(
                            f"Successfully applied tag '{tags[i]}' (ID: {tag_id}) to document {document_id}"
                        )

                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    error_msg = f"Failed to apply tag '{tags[i]}' (ID: {tag_id}) to document {document_id}: {str(e)}"
                    logger.warning(error_msg)
                    failed_applications.append(
                        {"tag_name": tags[i], "tag_id": tag_id, "error": error_msg}
                    )

            # Return comprehensive results
            result = {
                "success": len(failed_applications) == 0,
                "document_id": document_id,
                "tags_applied": len(successful_applications),
                "tags_failed": len(failed_applications),
                "successful_applications": successful_applications,
                "failed_applications": failed_applications,
            }

            if result["success"]:
                logger.info(
                    f"Successfully applied {len(successful_applications)} tags to document {document_id}"
                )
            else:
                logger.warning(
                    f"Applied {len(successful_applications)}/{len(tag_ids)} tags to document {document_id}, {len(failed_applications)} failed"
                )

            return result

        except Exception as e:
            error_msg = f"Failed to apply tags to document {document_id}: {str(e)}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e

    def poll_task_completion(
        self, task_id: str, timeout_seconds: int = 300, poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Poll a paperless-ngx task until completion or timeout.

        Args:
            task_id: Task ID to monitor
            timeout_seconds: Maximum time to wait for completion
            poll_interval: Seconds between polling attempts

        Returns:
            Dict containing task status and document_id if successful

        Raises:
            PaperlessUploadError: If polling fails or times out
        """
        if not self.is_enabled():
            raise PaperlessUploadError(
                "Paperless integration not enabled or configured"
            )

        import time

        start_time = time.time()
        logger.info(f"Starting task polling for {task_id}, timeout={timeout_seconds}s")

        try:
            while True:
                # Check if we've exceeded timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise PaperlessUploadError(
                        f"Task {task_id} polling timed out after {timeout_seconds}s"
                    )

                # Query task status
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.base_url}/api/tasks/",
                        headers=self.headers,
                        params={"task_id": task_id},
                    )
                    response.raise_for_status()

                    response_data = response.json()
                    logger.debug(f"Tasks API response: {response_data}")

                    # Handle both paginated and direct list responses
                    if isinstance(response_data, dict) and "results" in response_data:
                        tasks = response_data["results"]
                    elif isinstance(response_data, list):
                        tasks = response_data
                    else:
                        logger.warning(
                            f"Unexpected tasks API response format: {type(response_data)}"
                        )
                        tasks = []

                    task = None

                    # Find our specific task
                    for t in tasks:
                        if isinstance(t, dict) and t.get("task_id") == task_id:
                            task = t
                            break

                    if not task:
                        # Task not found in active tasks - might be completed and cleaned up
                        # Try to find recently created documents that might match
                        logger.warning(
                            f"Task {task_id} not found in task list, checking recent documents"
                        )
                        return {
                            "success": False,
                            "status": "task_not_found",
                            "document_id": None,
                        }

                    status = task.get("status")
                    logger.debug(f"Task {task_id} status: {status}")

                    if status == "SUCCESS":
                        # Task completed successfully
                        # The result might contain document information
                        result_data = task.get("result", {})
                        document_id = (
                            result_data.get("document_id")
                            if isinstance(result_data, dict)
                            else None
                        )

                        logger.info(
                            f"Task {task_id} completed successfully, document_id: {document_id}"
                        )
                        return {
                            "success": True,
                            "status": "completed",
                            "document_id": document_id,
                            "task_data": task,
                        }

                    elif status == "FAILURE":
                        # Task failed
                        error_info = task.get("result", "Unknown error")
                        logger.error(f"Task {task_id} failed: {error_info}")
                        return {
                            "success": False,
                            "status": "failed",
                            "error": error_info,
                            "task_data": task,
                        }

                    elif status in ["PENDING", "STARTED", "PROGRESS"]:
                        # Task still running, continue polling
                        logger.debug(
                            f"Task {task_id} still running ({status}), polling again in {poll_interval}s"
                        )
                        time.sleep(poll_interval)
                        continue

                    else:
                        # Unknown status
                        logger.warning(f"Task {task_id} has unknown status: {status}")
                        time.sleep(poll_interval)
                        continue

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            error_msg = f"Failed to poll task {task_id}: {str(e)}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e
        except Exception as e:
            error_msg = f"Task polling failed with unexpected error: {str(e)}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e

    def find_document_by_title_pattern(
        self, title_pattern: str, created_after: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a document by title pattern, optionally filtered by creation date.

        This is useful for finding documents that were just uploaded when we only have a task_id.

        Args:
            title_pattern: Pattern to search for in document titles
            created_after: ISO datetime string to filter documents created after this time

        Returns:
            Document dict if found, None otherwise
        """
        if not self.is_enabled():
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                params = {
                    "page_size": 20,
                    "ordering": "-created",  # Most recent first
                }

                if created_after:
                    params["created__gte"] = created_after

                response = client.get(
                    f"{self.base_url}/api/documents/",
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()

                documents = response.json().get("results", [])

                # Search for document with matching title pattern
                for doc in documents:
                    if title_pattern.lower() in doc.get("title", "").lower():
                        logger.info(
                            f"Found document by title pattern '{title_pattern}': ID={doc['id']}, Title='{doc['title']}'"
                        )
                        return doc

                logger.warning(
                    f"No document found matching title pattern: {title_pattern}"
                )
                return None

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(
                f"Failed to search for document by title pattern '{title_pattern}': {e}"
            )
            return None

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

    def query_documents_by_tags(
        self,
        tags: List[str],
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query documents by tags, returning only PDF documents.

        Args:
            tags: List of tag names to filter by
            page_size: Maximum number of documents to return

        Returns:
            Dict containing query results with PDF documents only

        Raises:
            PaperlessUploadError: If query fails
        """
        return self.query_documents(tags=tags, page_size=page_size)

    def query_documents_by_correspondent(
        self,
        correspondent: str,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query documents by correspondent, returning only PDF documents.

        Args:
            correspondent: Correspondent name to filter by
            page_size: Maximum number of documents to return

        Returns:
            Dict containing query results with PDF documents only

        Raises:
            PaperlessUploadError: If query fails
        """
        return self.query_documents(correspondent=correspondent, page_size=page_size)

    def query_documents_by_document_type(
        self,
        document_type: str,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query documents by document type, returning only PDF documents.

        Args:
            document_type: Document type name to filter by
            page_size: Maximum number of documents to return

        Returns:
            Dict containing query results with PDF documents only

        Raises:
            PaperlessUploadError: If query fails
        """
        return self.query_documents(document_type=document_type, page_size=page_size)

    def query_documents(
        self,
        tags: Optional[List[str]] = None,
        correspondent: Optional[str] = None,
        document_type: Optional[str] = None,
        created_after: Optional[date] = None,
        created_before: Optional[date] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query documents with various filters, returning only PDF documents.

        Args:
            tags: List of tag names to filter by
            correspondent: Correspondent name to filter by
            document_type: Document type name to filter by
            created_after: Filter documents created after this date
            created_before: Filter documents created before this date
            page_size: Maximum number of documents to return

        Returns:
            Dict containing query results with PDF documents only

        Raises:
            PaperlessUploadError: If query fails
        """
        if not self.is_enabled():
            raise PaperlessUploadError(
                "Paperless integration not enabled or configured"
            )

        # Build query parameters
        params = {
            "mime_type": "application/pdf",  # Only PDF documents
            "page_size": page_size or self.config.paperless_max_documents,
        }

        # Resolve and add filters
        if tags:
            resolved_tags = self._resolve_tags(tags)
            if resolved_tags:
                params["tags__id__in"] = ",".join(
                    str(tag_id) for tag_id in resolved_tags
                )

        if correspondent:
            resolved_correspondent = self._resolve_correspondent(correspondent)
            if resolved_correspondent:
                params["correspondent"] = resolved_correspondent

        if document_type:
            resolved_document_type = self._resolve_document_type(document_type)
            if resolved_document_type:
                params["document_type"] = resolved_document_type

        if created_after:
            params["created__date__gte"] = created_after.isoformat()

        if created_before:
            params["created__date__lte"] = created_before.isoformat()

        try:
            with httpx.Client(
                timeout=float(self.config.paperless_query_timeout)
            ) as client:
                response = client.get(
                    f"{self.base_url}/api/documents/",
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()

                data = response.json()
                results = data.get("results", [])

                # Filter results to ensure only PDF documents (double-check)
                pdf_documents = [doc for doc in results if self._is_pdf_document(doc)]

                logger.info(
                    f"Found {len(pdf_documents)} PDF documents out of {len(results)} total documents"
                )

                return {
                    "success": True,
                    "count": len(pdf_documents),
                    "documents": pdf_documents,
                    "total_available": data.get("count", 0),
                }

        except httpx.RequestError as e:
            error_msg = f"Failed to query documents from paperless-ngx: {str(e)}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_msg = f"Document query failed with status {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e

    def download_document(
        self,
        document_id: int,
        output_path: Optional[Path] = None,
        output_directory: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Download a document from paperless-ngx.

        Args:
            document_id: ID of the document to download
            output_path: Specific output file path
            output_directory: Directory to save the file (uses auto-naming)

        Returns:
            Dict containing download result information

        Raises:
            PaperlessUploadError: If download fails
        """
        if not self.is_enabled():
            raise PaperlessUploadError(
                "Paperless integration not enabled or configured"
            )

        if not output_path and not output_directory:
            raise PaperlessUploadError(
                "Either output_path or output_directory must be specified"
            )

        try:
            with httpx.Client(
                timeout=float(self.config.paperless_query_timeout)
            ) as client:
                response = client.get(
                    f"{self.base_url}/api/documents/{document_id}/download/",
                    headers=self.headers,
                )
                response.raise_for_status()

                # Validate content type is PDF
                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("application/pdf"):
                    raise PaperlessUploadError(
                        f"Document {document_id} is not a PDF file (content-type: {content_type})"
                    )

                # Determine output path
                if output_path:
                    file_path = Path(output_path)
                else:
                    file_path = Path(output_directory) / f"document_{document_id}.pdf"

                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write content to file
                file_path.write_bytes(response.content)
                file_size = len(response.content)

                logger.info(
                    f"Successfully downloaded document {document_id} to {file_path} ({file_size} bytes)"
                )

                return {
                    "success": True,
                    "document_id": document_id,
                    "output_path": str(file_path),
                    "file_size": file_size,
                    "content_type": content_type,
                }

        except httpx.RequestError as e:
            error_msg = f"Failed to download document {document_id} from paperless-ngx: {str(e)}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_msg = f"Document download failed with status {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise PaperlessUploadError(error_msg) from e

    def download_multiple_documents(
        self,
        document_ids: List[int],
        output_directory: Path,
    ) -> Dict[str, Any]:
        """Download multiple documents from paperless-ngx.

        Args:
            document_ids: List of document IDs to download
            output_directory: Directory to save all files

        Returns:
            Dict containing download results for all documents
        """
        if not document_ids:
            return {"success": True, "downloads": [], "errors": []}

        results = {"success": True, "downloads": [], "errors": []}

        for doc_id in document_ids:
            try:
                download_result = self.download_document(
                    document_id=doc_id, output_directory=output_directory
                )
                results["downloads"].append(download_result)
                logger.info(f"Successfully downloaded document {doc_id}")

            except PaperlessUploadError as e:
                error_info = {"document_id": doc_id, "error": str(e)}
                results["errors"].append(error_info)
                results["success"] = False
                logger.error(f"Failed to download document {doc_id}: {e}")

        return results

    def _is_pdf_document(self, document: Dict[str, Any]) -> bool:
        """Check if a document is a PDF based on its metadata.

        Args:
            document: Document metadata from paperless-ngx API

        Returns:
            bool: True if document is a PDF
        """
        # Check content_type field (primary)
        content_type = document.get("content_type", "").lower()
        if content_type.startswith("application/pdf"):
            return True

        # Check mime_type field (alternative)
        mime_type = document.get("mime_type", "").lower()
        if mime_type.startswith("application/pdf"):
            return True

        # File extension alone is not sufficient - we need content type information
        # This ensures we don't process documents that might not actually be PDFs
        return False

    def _resolve_tag(self, tag_name: str) -> Optional[int]:
        """Resolve a single tag name to its ID.

        Args:
            tag_name: Tag name to resolve

        Returns:
            Tag ID if found, None if not found

        Raises:
            PaperlessUploadError: If API call fails
        """
        if not self.is_enabled():
            raise PaperlessUploadError("Paperless integration not enabled")

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/api/tags/",
                    headers=self.headers,
                    params={"name": tag_name},
                )
                response.raise_for_status()
                tags_data = response.json()

                if tags_data["results"]:
                    return tags_data["results"][0]["id"]

                return None

        except httpx.RequestError as e:
            raise PaperlessUploadError(f"Failed to resolve tag '{tag_name}': {e}")
        except httpx.HTTPStatusError as e:
            raise PaperlessUploadError(
                f"Tag resolution failed with status {e.response.status_code}: {e.response.text}"
            )

    def should_mark_input_document_processed(self) -> bool:
        """Check if input document processing marking is enabled and configured.

        Returns:
            bool: True if input document marking should be performed
        """
        if not self.is_enabled():
            return False

        if not self.config.paperless_input_tagging_enabled:
            return False

        # Check if at least one tagging option is configured
        has_add_tag = bool(self.config.paperless_input_processed_tag)
        has_remove_tag = bool(self.config.paperless_input_remove_unprocessed_tag)
        has_custom_tag = bool(self.config.paperless_input_processing_tag)

        return has_add_tag or has_remove_tag or has_custom_tag

    def mark_input_document_processed(self, document_id: int) -> Dict[str, Any]:
        """Mark an input document as processed by applying configured tags.

        Args:
            document_id: ID of the document to mark as processed

        Returns:
            dict: Result of the tagging operation with success status and details

        Raises:
            PaperlessUploadError: If paperless integration is disabled
        """
        if not self.is_enabled():
            raise PaperlessUploadError("Paperless integration not enabled")

        if not self.config.paperless_input_tagging_enabled:
            return {
                "success": True,
                "document_id": document_id,
                "action": "disabled",
                "message": "Input document tagging is disabled",
            }

        # Determine which tagging action to perform (precedence order)
        if self.config.paperless_input_processed_tag:
            return self._add_tag_to_document(
                document_id, self.config.paperless_input_processed_tag
            )
        elif self.config.paperless_input_remove_unprocessed_tag:
            return self._remove_tag_from_document(
                document_id, self.config.paperless_input_unprocessed_tag_name
            )
        elif self.config.paperless_input_processing_tag:
            return self._add_tag_to_document(
                document_id, self.config.paperless_input_processing_tag
            )
        else:
            return {
                "success": False,
                "document_id": document_id,
                "error": "No input document tagging configuration specified",
            }

    def _add_tag_to_document(self, document_id: int, tag_name: str) -> Dict[str, Any]:
        """Add a tag to a document by updating its tags list.

        Args:
            document_id: ID of the document
            tag_name: Name of the tag to add

        Returns:
            dict: Result of the tagging operation
        """
        try:
            # Resolve tag name to ID
            tag_id = self._resolve_tag(tag_name)
            if tag_id is None:
                return {
                    "success": False,
                    "document_id": document_id,
                    "error": f"Tag '{tag_name}' not found in paperless-ngx",
                }

            # Get current document to retrieve existing tags
            with httpx.Client() as client:
                # Get current document data
                response = client.get(
                    f"{self.base_url}/api/documents/{document_id}/",
                    headers=self.headers,
                )
                response.raise_for_status()
                document_data = response.json()

                current_tags = document_data.get("tags", [])

                # Add tag if not already present
                if tag_id not in current_tags:
                    updated_tags = current_tags + [tag_id]

                    # Update document with new tags
                    update_response = client.patch(
                        f"{self.base_url}/api/documents/{document_id}/",
                        headers=self.headers,
                        json={"tags": updated_tags},
                    )
                    update_response.raise_for_status()

                    return {
                        "success": True,
                        "document_id": document_id,
                        "action": "add_tag",
                        "tag_name": tag_name,
                        "tag_id": tag_id,
                    }
                else:
                    # Tag already present, return early with success message
                    return {
                        "success": True,
                        "document_id": document_id,
                        "action": "add_tag",
                        "tag_name": tag_name,
                        "tag_id": tag_id,
                        "message": f"Tag '{tag_name}' already present on document",
                    }

        except Exception as e:
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
            }

    def _remove_tag_from_document(
        self, document_id: int, tag_name: str
    ) -> Dict[str, Any]:
        """Remove a tag from a document by updating its tags list.

        Args:
            document_id: ID of the document
            tag_name: Name of the tag to remove

        Returns:
            dict: Result of the tagging operation
        """
        try:
            # Resolve tag name to ID
            tag_id = self._resolve_tag(tag_name)
            if tag_id is None:
                return {
                    "success": False,
                    "document_id": document_id,
                    "error": f"Tag '{tag_name}' not found in paperless-ngx",
                }

            # Get current document to retrieve existing tags
            with httpx.Client() as client:
                # Get current document data
                response = client.get(
                    f"{self.base_url}/api/documents/{document_id}/",
                    headers=self.headers,
                )
                response.raise_for_status()
                document_data = response.json()

                current_tags = document_data.get("tags", [])

                # Remove tag if present
                if tag_id in current_tags:
                    updated_tags = [t for t in current_tags if t != tag_id]

                    # Update document with new tags
                    update_response = client.patch(
                        f"{self.base_url}/api/documents/{document_id}/",
                        headers=self.headers,
                        json={"tags": updated_tags},
                    )
                    update_response.raise_for_status()

                    return {
                        "success": True,
                        "document_id": document_id,
                        "action": "remove_tag",
                        "tag_name": tag_name,
                        "tag_id": tag_id,
                    }
                else:
                    # Tag not present, return early with success message
                    return {
                        "success": True,
                        "document_id": document_id,
                        "action": "remove_tag",
                        "tag_name": tag_name,
                        "tag_id": tag_id,
                        "message": f"Tag '{tag_name}' not present on document",
                    }

        except Exception as e:
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
            }

    def mark_multiple_input_documents_processed(
        self, document_ids: List[int]
    ) -> Dict[str, Any]:
        """Mark multiple input documents as processed.

        Args:
            document_ids: List of document IDs to mark as processed

        Returns:
            dict: Results of the tagging operations with success status and details
        """
        if not document_ids:
            return {
                "success": True,
                "processed": [],
                "errors": [],
            }

        processed = []
        errors = []

        for document_id in document_ids:
            try:
                result = self.mark_input_document_processed(document_id)
                if result["success"]:
                    processed.append(result)
                else:
                    errors.append(result)
            except Exception as e:
                error_info = {
                    "document_id": document_id,
                    "error": str(e),
                }
                errors.append(error_info)

        return {
            "success": len(errors) == 0,
            "processed": processed,
            "errors": errors,
        }
