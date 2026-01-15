"""Report Generation Service for Typo Check Results.

This service generates HTML and PDF reports from typo check results.
"""

import json
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Any

from flask import render_template
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models.typo_check_result import TypoCheckResult


# Issue type translations (Korean)
ISSUE_TYPE_KOREAN = {
    "spelling": "맞춤법",
    "spacing": "띄어쓰기",
    "grammar": "문법",
    "punctuation": "구두점",
    "typo": "오타",
    "other": "기타",
}


class ReportService:
    """Service for generating reports from typo check results.

    Provides HTML and PDF report generation with professional styling
    and Korean language support.
    """

    @staticmethod
    def generate_html(result_id: int, user_id: str) -> Optional[str]:
        """Generate HTML report from a typo check result.

        Args:
            result_id: ID of the typo check result
            user_id: User ID for access verification

        Returns:
            HTML string or None if result not found or access denied
        """
        # Fetch result with access verification
        result = TypoCheckResult.query.filter_by(
            id=result_id, user_id=user_id
        ).first()

        if not result:
            return None

        # Parse issues
        try:
            issues = json.loads(result.issues) if result.issues else []
        except json.JSONDecodeError:
            issues = []

        # Add Korean translations to issues
        processed_issues = ReportService._process_issues(issues)

        # Count issues by type
        issue_counts = ReportService._count_issues_by_type(issues)

        # Format created_at
        created_at = result.created_at.strftime("%Y-%m-%d %H:%M:%S") if result.created_at else ""

        # Render template
        html = render_template(
            "typo_report.html",
            corrected_text=result.corrected_text,
            issues=processed_issues,
            total_issues=len(issues),
            spelling_count=issue_counts.get("spelling", 0),
            spacing_count=issue_counts.get("spacing", 0),
            grammar_count=issue_counts.get("grammar", 0),
            provider=result.provider_used,
            created_at=created_at,
        )

        return html

    @staticmethod
    def generate_pdf(result_id: int, user_id: str) -> Optional[bytes]:
        """Generate PDF report from a typo check result.

        Args:
            result_id: ID of the typo check result
            user_id: User ID for access verification

        Returns:
            PDF bytes or None if result not found or access denied
        """
        # Fetch result with access verification
        result = TypoCheckResult.query.filter_by(
            id=result_id, user_id=user_id
        ).first()

        if not result:
            return None

        # Parse issues
        try:
            issues = json.loads(result.issues) if result.issues else []
        except json.JSONDecodeError:
            issues = []

        # Process issues with Korean translations
        processed_issues = ReportService._process_issues(issues)

        # Count issues by type
        issue_counts = ReportService._count_issues_by_type(issues)

        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        # Build PDF content
        elements = ReportService._build_pdf_elements(
            corrected_text=result.corrected_text,
            issues=processed_issues,
            issue_counts=issue_counts,
            provider=result.provider_used,
            created_at=result.created_at,
        )

        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    @staticmethod
    def _process_issues(issues: List[Dict]) -> List[Dict]:
        """Process issues and add Korean translations.

        Args:
            issues: List of issue dictionaries

        Returns:
            Processed issues with Korean type names
        """
        processed = []
        for issue in issues:
            processed_issue = issue.copy()
            issue_type = issue.get("issue_type", "other")
            processed_issue["issue_type_korean"] = ISSUE_TYPE_KOREAN.get(
                issue_type, ISSUE_TYPE_KOREAN["other"]
            )
            processed.append(processed_issue)
        return processed

    @staticmethod
    def _count_issues_by_type(issues: List[Dict]) -> Dict[str, int]:
        """Count issues by type.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with counts by issue type
        """
        counts: Dict[str, int] = {}
        for issue in issues:
            issue_type = issue.get("issue_type", "other")
            counts[issue_type] = counts.get(issue_type, 0) + 1
        return counts

    @staticmethod
    def _build_pdf_elements(
        corrected_text: str,
        issues: List[Dict],
        issue_counts: Dict[str, int],
        provider: str,
        created_at: Optional[datetime],
    ) -> List[Any]:
        """Build PDF document elements.

        Args:
            corrected_text: The corrected text
            issues: Processed issues list
            issue_counts: Issue counts by type
            provider: AI provider used
            created_at: Creation timestamp

        Returns:
            List of reportlab elements
        """
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Center
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=6,
        )

        # Title
        elements.append(Paragraph("Typo Check Report", title_style))
        elements.append(Spacer(1, 10))

        # Meta information
        if created_at:
            meta_text = f"Generated: {created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            elements.append(Paragraph(meta_text, body_style))

        elements.append(Paragraph(f"Provider: {provider}", body_style))
        elements.append(Spacer(1, 20))

        # Summary section
        elements.append(Paragraph("Summary", heading_style))

        summary_data = [
            ["Total Issues", str(len(issues))],
            ["Spelling", str(issue_counts.get("spelling", 0))],
            ["Spacing", str(issue_counts.get("spacing", 0))],
            ["Grammar", str(issue_counts.get("grammar", 0))],
        ]

        summary_table = Table(summary_data, colWidths=[100, 50])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.white),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Corrected text section
        elements.append(Paragraph("Corrected Text", heading_style))
        # Escape special characters for PDF
        safe_text = corrected_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elements.append(Paragraph(safe_text, body_style))
        elements.append(Spacer(1, 20))

        # Issues section
        if issues:
            elements.append(Paragraph("Issues Found", heading_style))

            for i, issue in enumerate(issues, 1):
                original = issue.get("original", "")
                corrected = issue.get("corrected", "")
                issue_type = issue.get("issue_type_korean", "")
                position = issue.get("position", 0)
                explanation = issue.get("explanation", "")

                # Escape special characters
                original = original.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                corrected = corrected.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                explanation = explanation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                issue_text = (
                    f"{i}. [{issue_type}] Position {position}: "
                    f"'{original}' -> '{corrected}'"
                )
                elements.append(Paragraph(issue_text, body_style))

                if explanation:
                    elements.append(Paragraph(f"   {explanation}", body_style))

        else:
            elements.append(Paragraph("No issues found.", body_style))

        return elements
