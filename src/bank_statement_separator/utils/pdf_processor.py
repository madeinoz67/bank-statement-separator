"""PDF processing utilities using PyMuPDF."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class PDFPage:
    """Represents a single PDF page with extracted content."""

    page_number: int
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    word_count: int

    def __post_init__(self):
        """Calculate word count after initialization."""
        self.word_count = len(self.text.split()) if self.text else 0


@dataclass
class PDFDocument:
    """Represents a PDF document with extracted content."""

    file_path: str
    total_pages: int
    pages: List[PDFPage]
    metadata: Dict
    file_size_mb: float

    @property
    def total_words(self) -> int:
        """Get total word count across all pages."""
        return sum(page.word_count for page in self.pages)

    @property
    def total_text(self) -> str:
        """Get concatenated text from all pages."""
        return "\n\n".join(page.text for page in self.pages)


class PDFProcessor:
    """PDF processing class using PyMuPDF for text extraction and manipulation."""

    def __init__(self, max_file_size_mb: int = 100, max_pages: int = 500):
        """
        Initialize PDF processor.

        Args:
            max_file_size_mb: Maximum allowed file size in MB
            max_pages: Maximum allowed number of pages
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_pages = max_pages

    def validate_pdf(self, file_path: str) -> bool:
        """
        Validate PDF file before processing.

        Args:
            file_path: Path to PDF file

        Returns:
            bool: True if valid, False otherwise
        """
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            logger.error(f"PDF file does not exist: {file_path}")
            return False

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            logger.error(
                f"PDF file too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB"
            )
            return False

        # Check if it's a PDF file
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            doc.close()

            if page_count > self.max_pages:
                logger.error(f"PDF has too many pages: {page_count} > {self.max_pages}")
                return False

        except Exception as e:
            logger.error(f"Invalid PDF file: {e}")
            return False

        return True

    def extract_text_from_pdf(self, file_path: str) -> PDFDocument:
        """
        Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            PDFDocument: Extracted document content

        Raises:
            ValueError: If PDF is invalid or too large
            RuntimeError: If extraction fails
        """
        if not self.validate_pdf(file_path):
            raise ValueError(f"PDF validation failed for: {file_path}")

        try:
            doc = fitz.open(file_path)
            pages = []

            logger.info(f"Extracting text from {len(doc)} pages")

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extract text
                text = page.get_text()

                # Get page bounding box
                bbox = page.bound()

                pdf_page = PDFPage(
                    page_number=page_num + 1,  # 1-based page numbers
                    text=text.strip(),
                    bbox=(bbox.x0, bbox.y0, bbox.x1, bbox.y1),
                    word_count=0,  # Will be calculated in __post_init__
                )

                pages.append(pdf_page)
                logger.debug(
                    f"Extracted {pdf_page.word_count} words from page {pdf_page.page_number}"
                )

            # Get document metadata
            metadata = doc.metadata
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)

            doc.close()

            pdf_document = PDFDocument(
                file_path=file_path,
                total_pages=len(pages),
                pages=pages,
                metadata=metadata,
                file_size_mb=file_size_mb,
            )

            logger.info(
                f"Successfully extracted {pdf_document.total_words} words from {pdf_document.total_pages} pages"
            )
            return pdf_document

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise RuntimeError(f"PDF text extraction failed: {e}")

    def extract_page_range(
        self, file_path: str, start_page: int, end_page: int, output_path: str
    ) -> bool:
        """
        Extract a range of pages to a new PDF file.

        Args:
            file_path: Source PDF file path
            start_page: Start page (1-based)
            end_page: End page (1-based, inclusive)
            output_path: Output PDF file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc = fitz.open(file_path)

            # Convert to 0-based indexing and validate range
            start_idx = start_page - 1
            end_idx = end_page - 1

            if start_idx < 0 or end_idx >= len(doc) or start_idx > end_idx:
                logger.error(
                    f"Invalid page range: {start_page}-{end_page} for document with {len(doc)} pages"
                )
                doc.close()
                return False

            # Create new document with selected pages
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx)

            # Save the new document
            new_doc.save(output_path)
            new_doc.close()
            doc.close()

            logger.info(f"Extracted pages {start_page}-{end_page} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to extract page range: {e}")
            return False

    def get_page_text(self, file_path: str, page_number: int) -> Optional[str]:
        """
        Get text from a specific page.

        Args:
            file_path: PDF file path
            page_number: Page number (1-based)

        Returns:
            str: Page text or None if failed
        """
        try:
            doc = fitz.open(file_path)

            if page_number < 1 or page_number > len(doc):
                logger.error(
                    f"Invalid page number: {page_number} for document with {len(doc)} pages"
                )
                doc.close()
                return None

            page = doc[page_number - 1]  # Convert to 0-based
            text = page.get_text()
            doc.close()

            return text.strip()

        except Exception as e:
            logger.error(f"Failed to get page text: {e}")
            return None

    def split_pdf_by_pages(
        self,
        file_path: str,
        page_ranges: List[Tuple[int, int]],
        output_dir: str,
        filename_prefix: str = "statement",
    ) -> List[str]:
        """
        Split PDF into multiple files based on page ranges.

        Args:
            file_path: Source PDF file path
            page_ranges: List of (start_page, end_page) tuples (1-based, inclusive)
            output_dir: Output directory
            filename_prefix: Prefix for output filenames

        Returns:
            List[str]: List of created file paths
        """
        output_files = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, (start_page, end_page) in enumerate(page_ranges):
            output_file = (
                output_path
                / f"{filename_prefix}_{i + 1:02d}_pages_{start_page}-{end_page}.pdf"
            )

            if self.extract_page_range(
                file_path, start_page, end_page, str(output_file)
            ):
                output_files.append(str(output_file))
            else:
                logger.warning(f"Failed to create {output_file}")

        logger.info(f"Created {len(output_files)} PDF files in {output_dir}")
        return output_files

    def get_document_info(self, file_path: str) -> Dict:
        """
        Get basic information about a PDF document.

        Args:
            file_path: PDF file path

        Returns:
            dict: Document information
        """
        try:
            doc = fitz.open(file_path)
            info = {
                "file_path": file_path,
                "page_count": len(doc),
                "metadata": doc.metadata,
                "file_size_mb": Path(file_path).stat().st_size / (1024 * 1024),
                "is_encrypted": doc.is_encrypted,
                "needs_pass": doc.needs_pass,
            }
            doc.close()
            return info

        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return {}
