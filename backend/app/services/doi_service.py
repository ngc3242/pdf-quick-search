"""DOI extraction service.

Extracts Digital Object Identifiers (DOIs) from text and PDF documents.
DOI format: 10.XXXX/SUFFIX where XXXX is a registrant code (4+ digits).
"""

import os
import re
from typing import Optional, Tuple

import pdfplumber


class DOIService:
    """Service class for DOI extraction operations."""

    # DOI regex pattern: 10.XXXX/SUFFIX where XXXX is 4-9 digits
    # Matches DOIs in various formats including URLs
    DOI_PATTERN = re.compile(r"10\.\d{4,9}/[^\s]+")

    # Maximum pages to search for DOI (performance optimization)
    MAX_PAGES_TO_SEARCH = 5

    @staticmethod
    def validate_doi(doi: Optional[str]) -> bool:
        """Validate DOI format.

        DOI must start with '10.' followed by a registrant code (4+ digits),
        a forward slash, and a suffix.

        Args:
            doi: DOI string to validate

        Returns:
            True if valid DOI format, False otherwise
        """
        if not doi:
            return False

        # Check basic format: 10.XXXX/suffix
        pattern = re.compile(r"^10\.\d{4,9}/[^\s]+$")
        return bool(pattern.match(doi))

    @staticmethod
    def _clean_doi(doi: str) -> str:
        """Clean DOI by removing trailing punctuation.

        Args:
            doi: Raw DOI string

        Returns:
            Cleaned DOI string
        """
        # Remove trailing punctuation that might be captured
        trailing_chars = ".,;:)>]}"
        while doi and doi[-1] in trailing_chars:
            doi = doi[:-1]
        return doi

    @staticmethod
    def extract_doi_from_text(text: Optional[str]) -> Optional[str]:
        """Extract first valid DOI from text.

        Searches for DOI patterns in various formats:
        - Plain: 10.1000/xyz123
        - URL: https://doi.org/10.1000/xyz123
        - dx.doi.org: http://dx.doi.org/10.1000/xyz123

        Args:
            text: Text to search for DOI

        Returns:
            First valid DOI found, or None if no DOI found
        """
        if not text:
            return None

        # Search for DOI pattern
        match = DOIService.DOI_PATTERN.search(text)
        if match:
            doi = DOIService._clean_doi(match.group())
            if DOIService.validate_doi(doi):
                return doi

        return None

    @staticmethod
    def extract_doi_from_pdf(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DOI from PDF file.

        Searches the first few pages of the PDF for a DOI.
        Returns tuple following the (result, error) pattern.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (DOI string or None, error message or None)
        """
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"

        try:
            with pdfplumber.open(file_path) as pdf:
                # Search first N pages for DOI
                pages_to_search = min(len(pdf.pages), DOIService.MAX_PAGES_TO_SEARCH)

                for page_num in range(pages_to_search):
                    page = pdf.pages[page_num]
                    text = page.extract_text()

                    if text:
                        doi = DOIService.extract_doi_from_text(text)
                        if doi:
                            return doi, None

            # No DOI found in searched pages
            return None, None

        except Exception as e:
            return None, f"Error reading PDF: {str(e)}"
