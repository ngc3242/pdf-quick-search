"""Tests for Report Generation Service.

This module tests the report generation service including HTML
and PDF report generation for typo check results.
"""

import json


from app import db
from app.models.user import User
from app.models.typo_check_result import TypoCheckResult
from app.services.report_service import ReportService


class TestReportServiceBasics:
    """Tests for basic ReportService functionality."""

    def test_report_service_exists(self, app):
        """Test that ReportService class exists."""
        assert ReportService is not None

    def test_report_service_has_generate_html_method(self, app):
        """Test that service has generate_html method."""
        assert hasattr(ReportService, "generate_html")
        assert callable(getattr(ReportService, "generate_html", None))

    def test_report_service_has_generate_pdf_method(self, app):
        """Test that service has generate_pdf method."""
        assert hasattr(ReportService, "generate_pdf")
        assert callable(getattr(ReportService, "generate_pdf", None))


class TestHTMLReportGeneration:
    """Tests for HTML report generation."""

    def create_test_result(self, user_id: str) -> TypoCheckResult:
        """Create a test typo check result."""
        issues = [
            {
                "original": "안녕하세여",
                "corrected": "안녕하세요",
                "position": 0,
                "issue_type": "spelling",
                "explanation": "맞춤법 오류: '세여' -> '세요'"
            },
            {
                "original": "감사 합니다",
                "corrected": "감사합니다",
                "position": 10,
                "issue_type": "spacing",
                "explanation": "띄어쓰기 오류"
            }
        ]

        result = TypoCheckResult(
            user_id=user_id,
            original_text_hash="test_hash_html",
            corrected_text="안녕하세요 감사합니다",
            issues=json.dumps(issues),
            provider_used="claude"
        )
        db.session.add(result)
        db.session.commit()
        return result

    def test_generate_html_returns_string(self, app):
        """Test that generate_html returns a string."""
        user = User(
            email="html_test@example.com",
            name="HTML Test User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = self.create_test_result(user.id)

        html = ReportService.generate_html(result.id, user.id)

        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_html_contains_corrected_text(self, app):
        """Test that HTML report contains corrected text."""
        user = User(
            email="html_content@example.com",
            name="HTML Content User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = self.create_test_result(user.id)

        html = ReportService.generate_html(result.id, user.id)

        assert "안녕하세요 감사합니다" in html

    def test_generate_html_contains_issues(self, app):
        """Test that HTML report contains issue details."""
        user = User(
            email="html_issues@example.com",
            name="HTML Issues User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = self.create_test_result(user.id)

        html = ReportService.generate_html(result.id, user.id)

        # Should contain issue information
        assert "안녕하세여" in html or "spelling" in html.lower()

    def test_generate_html_returns_none_for_invalid_id(self, app):
        """Test that generate_html returns None for invalid result ID."""
        user = User(
            email="html_invalid@example.com",
            name="HTML Invalid User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = ReportService.generate_html(99999, user.id)

        assert result is None

    def test_generate_html_returns_none_for_wrong_user(self, app):
        """Test that generate_html returns None for wrong user."""
        user1 = User(
            email="html_user1@example.com",
            name="HTML User 1",
            password="password123"
        )
        user2 = User(
            email="html_user2@example.com",
            name="HTML User 2",
            password="password123"
        )
        db.session.add_all([user1, user2])
        db.session.commit()

        result = self.create_test_result(user1.id)

        html = ReportService.generate_html(result.id, user2.id)

        assert html is None

    def test_generate_html_contains_provider_info(self, app):
        """Test that HTML report contains provider information."""
        user = User(
            email="html_provider@example.com",
            name="HTML Provider User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = self.create_test_result(user.id)

        html = ReportService.generate_html(result.id, user.id)

        assert "claude" in html.lower()


class TestPDFReportGeneration:
    """Tests for PDF report generation."""

    def create_test_result(self, user_id: str) -> TypoCheckResult:
        """Create a test typo check result."""
        issues = [
            {
                "original": "테스트",
                "corrected": "테스트 수정",
                "position": 0,
                "issue_type": "typo",
                "explanation": "테스트 오류"
            }
        ]

        result = TypoCheckResult(
            user_id=user_id,
            original_text_hash="test_hash_pdf",
            corrected_text="테스트 수정",
            issues=json.dumps(issues),
            provider_used="claude"
        )
        db.session.add(result)
        db.session.commit()
        return result

    def test_generate_pdf_returns_bytes(self, app):
        """Test that generate_pdf returns bytes."""
        user = User(
            email="pdf_test@example.com",
            name="PDF Test User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = self.create_test_result(user.id)

        pdf = ReportService.generate_pdf(result.id, user.id)

        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_generate_pdf_is_valid_pdf(self, app):
        """Test that generated PDF has valid PDF header."""
        user = User(
            email="pdf_valid@example.com",
            name="PDF Valid User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = self.create_test_result(user.id)

        pdf = ReportService.generate_pdf(result.id, user.id)

        # PDF files start with %PDF
        assert pdf.startswith(b"%PDF")

    def test_generate_pdf_returns_none_for_invalid_id(self, app):
        """Test that generate_pdf returns None for invalid result ID."""
        user = User(
            email="pdf_invalid@example.com",
            name="PDF Invalid User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = ReportService.generate_pdf(99999, user.id)

        assert result is None

    def test_generate_pdf_returns_none_for_wrong_user(self, app):
        """Test that generate_pdf returns None for wrong user."""
        user1 = User(
            email="pdf_user1@example.com",
            name="PDF User 1",
            password="password123"
        )
        user2 = User(
            email="pdf_user2@example.com",
            name="PDF User 2",
            password="password123"
        )
        db.session.add_all([user1, user2])
        db.session.commit()

        result = self.create_test_result(user1.id)

        pdf = ReportService.generate_pdf(result.id, user2.id)

        assert pdf is None


class TestReportTemplate:
    """Tests for report template rendering."""

    def test_template_exists(self, app):
        """Test that typo report template exists."""
        import os
        template_path = os.path.join(
            app.root_path, "templates", "typo_report.html"
        )
        assert os.path.exists(template_path)

    def test_template_renders_without_error(self, app):
        """Test that template renders without error."""
        user = User(
            email="template_test@example.com",
            name="Template Test User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        issues = [
            {
                "original": "테스트",
                "corrected": "테스트",
                "position": 0,
                "issue_type": "test",
                "explanation": "테스트"
            }
        ]

        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash="template_hash",
            corrected_text="테스트",
            issues=json.dumps(issues),
            provider_used="claude"
        )
        db.session.add(result)
        db.session.commit()

        # Should not raise any exceptions
        html = ReportService.generate_html(result.id, user.id)
        assert html is not None


class TestIssueTypeTranslation:
    """Tests for issue type translation in reports."""

    def create_result_with_issue_types(self, user_id: str) -> TypoCheckResult:
        """Create result with various issue types."""
        issues = [
            {
                "original": "test1",
                "corrected": "test1",
                "position": 0,
                "issue_type": "spelling",
                "explanation": "맞춤법"
            },
            {
                "original": "test2",
                "corrected": "test2",
                "position": 10,
                "issue_type": "spacing",
                "explanation": "띄어쓰기"
            },
            {
                "original": "test3",
                "corrected": "test3",
                "position": 20,
                "issue_type": "grammar",
                "explanation": "문법"
            },
            {
                "original": "test4",
                "corrected": "test4",
                "position": 30,
                "issue_type": "punctuation",
                "explanation": "구두점"
            }
        ]

        result = TypoCheckResult(
            user_id=user_id,
            original_text_hash="issue_types_hash",
            corrected_text="테스트",
            issues=json.dumps(issues),
            provider_used="claude"
        )
        db.session.add(result)
        db.session.commit()
        return result

    def test_html_contains_all_issue_types(self, app):
        """Test that HTML report handles all issue types."""
        user = User(
            email="issue_types@example.com",
            name="Issue Types User",
            password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = self.create_result_with_issue_types(user.id)

        html = ReportService.generate_html(result.id, user.id)

        # Should render all issue types without error
        assert html is not None
        assert len(html) > 0
