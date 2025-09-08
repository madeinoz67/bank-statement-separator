"""Paperless-ngx API client for document upload integration."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import date
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
        return self.query_documents(
            tags=tags,
            page_size=page_size
        )

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
        return self.query_documents(
            correspondent=correspondent,
            page_size=page_size
        )

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
        return self.query_documents(
            document_type=document_type,
            page_size=page_size
        )

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
                params["tags__id__in"] = ",".join(str(tag_id) for tag_id in resolved_tags)

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
            with httpx.Client(timeout=float(self.config.paperless_query_timeout)) as client:
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
            with httpx.Client(timeout=float(self.config.paperless_query_timeout)) as client:
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
                    document_id=doc_id,
                    output_directory=output_directory
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
