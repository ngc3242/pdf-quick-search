"""Tests for DOI extraction service.

TDD RED Phase: Write failing tests first.
"""

import os
import tempfile


class TestDOIValidation:
    """Test cases for DOI format validation."""

    def test_validate_doi_valid_format(self):
        """Test validation of valid DOI format."""
        from app.services.doi_service import DOIService

        # Standard DOI format
        assert DOIService.validate_doi("10.1000/xyz123") is True
        assert DOIService.validate_doi("10.1038/nature12373") is True
        assert DOIService.validate_doi("10.1371/journal.pone.0000000") is True

    def test_validate_doi_with_special_characters(self):
        """Test DOI validation with special characters."""
        from app.services.doi_service import DOIService

        # DOIs can contain special characters
        assert DOIService.validate_doi("10.1000/abc-def.123") is True
        assert DOIService.validate_doi("10.1000/abc_def") is True
        assert DOIService.validate_doi("10.1000/abc(def)") is True

    def test_validate_doi_invalid_format(self):
        """Test validation rejects invalid DOI formats."""
        from app.services.doi_service import DOIService

        # Missing 10. prefix
        assert DOIService.validate_doi("9.1000/xyz123") is False

        # Missing registrant code
        assert DOIService.validate_doi("10./xyz123") is False

        # Missing suffix
        assert DOIService.validate_doi("10.1000/") is False

        # Empty string
        assert DOIService.validate_doi("") is False

        # None value
        assert DOIService.validate_doi(None) is False

    def test_validate_doi_short_registrant(self):
        """Test DOI validation with short registrant code."""
        from app.services.doi_service import DOIService

        # Registrant code must be at least 4 digits
        assert DOIService.validate_doi("10.123/xyz") is False
        assert DOIService.validate_doi("10.1234/xyz") is True


class TestDOIExtractionFromText:
    """Test cases for extracting DOI from text."""

    def test_extract_doi_from_text_simple(self):
        """Test extracting DOI from simple text."""
        from app.services.doi_service import DOIService

        text = "This paper has DOI: 10.1038/nature12373"
        result = DOIService.extract_doi_from_text(text)
        assert result == "10.1038/nature12373"

    def test_extract_doi_from_text_with_url(self):
        """Test extracting DOI from URL format."""
        from app.services.doi_service import DOIService

        text = "Available at https://doi.org/10.1371/journal.pone.0000000"
        result = DOIService.extract_doi_from_text(text)
        assert result == "10.1371/journal.pone.0000000"

    def test_extract_doi_from_text_with_dx_doi(self):
        """Test extracting DOI from dx.doi.org URL."""
        from app.services.doi_service import DOIService

        text = "Link: http://dx.doi.org/10.1000/xyz123"
        result = DOIService.extract_doi_from_text(text)
        assert result == "10.1000/xyz123"

    def test_extract_doi_from_text_multiple_dois(self):
        """Test extracting first DOI when multiple exist."""
        from app.services.doi_service import DOIService

        text = "DOI: 10.1000/first and also 10.2000/second"
        result = DOIService.extract_doi_from_text(text)
        assert result == "10.1000/first"

    def test_extract_doi_from_text_no_doi(self):
        """Test returns None when no DOI found."""
        from app.services.doi_service import DOIService

        text = "This text has no DOI information."
        result = DOIService.extract_doi_from_text(text)
        assert result is None

    def test_extract_doi_from_text_empty(self):
        """Test handles empty text."""
        from app.services.doi_service import DOIService

        assert DOIService.extract_doi_from_text("") is None
        assert DOIService.extract_doi_from_text(None) is None

    def test_extract_doi_from_text_with_newlines(self):
        """Test extracting DOI from text with newlines."""
        from app.services.doi_service import DOIService

        text = "Reference:\nDOI: 10.1038/nature12373\nEnd"
        result = DOIService.extract_doi_from_text(text)
        assert result == "10.1038/nature12373"

    def test_extract_doi_from_text_with_trailing_punctuation(self):
        """Test DOI extraction removes trailing punctuation."""
        from app.services.doi_service import DOIService

        # DOI followed by period
        text = "See DOI 10.1000/xyz123."
        result = DOIService.extract_doi_from_text(text)
        assert result == "10.1000/xyz123"

        # DOI followed by comma
        text = "DOI: 10.1000/xyz123, which is important"
        result = DOIService.extract_doi_from_text(text)
        assert result == "10.1000/xyz123"


class TestDOIExtractionFromPDF:
    """Test cases for extracting DOI from PDF files."""

    def test_extract_doi_from_pdf_success(self, app):
        """Test successful DOI extraction from PDF."""
        from app.services.doi_service import DOIService

        with app.app_context():
            # Create a temp PDF with DOI
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                c.drawString(100, 750, "DOI: 10.1038/nature12373")
                c.showPage()
                c.save()

                result, error = DOIService.extract_doi_from_pdf(temp_path)
                assert result == "10.1038/nature12373"
                assert error is None

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_extract_doi_from_pdf_no_doi(self, app):
        """Test PDF without DOI returns None."""
        from app.services.doi_service import DOIService

        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                c.drawString(100, 750, "No DOI in this document")
                c.showPage()
                c.save()

                result, error = DOIService.extract_doi_from_pdf(temp_path)
                assert result is None
                assert error is None

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_extract_doi_from_pdf_file_not_found(self, app):
        """Test handles missing file gracefully."""
        from app.services.doi_service import DOIService

        with app.app_context():
            result, error = DOIService.extract_doi_from_pdf("/nonexistent/path.pdf")
            assert result is None
            assert error is not None
            assert "not found" in error.lower() or "no such file" in error.lower()

    def test_extract_doi_from_pdf_invalid_pdf(self, app):
        """Test handles invalid PDF file."""
        from app.services.doi_service import DOIService

        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"This is not a valid PDF")
                temp_path = f.name

            try:
                result, error = DOIService.extract_doi_from_pdf(temp_path)
                assert result is None
                assert error is not None

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_extract_doi_from_pdf_first_pages_only(self, app):
        """Test DOI extraction checks first few pages only for performance."""
        from app.services.doi_service import DOIService

        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                # First page has DOI
                c.drawString(100, 750, "DOI: 10.1038/nature12373")
                c.showPage()
                # Add more pages
                for i in range(5):
                    c.drawString(100, 750, f"Page {i + 2} content")
                    c.showPage()
                c.save()

                result, error = DOIService.extract_doi_from_pdf(temp_path)
                assert result == "10.1038/nature12373"
                assert error is None

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_extract_doi_from_pdf_multipage_search(self, app):
        """Test DOI extraction searches multiple pages."""
        from app.services.doi_service import DOIService

        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                # First page has no DOI
                c.drawString(100, 750, "Title Page")
                c.showPage()
                # Second page has DOI
                c.drawString(100, 750, "DOI: 10.1038/nature12373")
                c.showPage()
                c.save()

                result, error = DOIService.extract_doi_from_pdf(temp_path)
                assert result == "10.1038/nature12373"
                assert error is None

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


class TestDOIServiceTupleReturn:
    """Test cases for tuple return pattern consistency."""

    def test_extract_doi_from_pdf_returns_tuple_on_error(self, app):
        """Test that extract_doi_from_pdf returns tuple (result, error) on error."""
        from app.services.doi_service import DOIService

        with app.app_context():
            result = DOIService.extract_doi_from_pdf("/nonexistent/path.pdf")
            # Should return tuple
            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_extract_doi_from_pdf_returns_tuple_on_success(self, app):
        """Test that extract_doi_from_pdf returns tuple (result, None) on success."""
        from app.services.doi_service import DOIService

        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                c.drawString(100, 750, "DOI: 10.1038/nature12373")
                c.showPage()
                c.save()

                result = DOIService.extract_doi_from_pdf(temp_path)
                # Should return tuple
                assert isinstance(result, tuple)
                assert len(result) == 2
                assert result[0] == "10.1038/nature12373"
                assert result[1] is None

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
