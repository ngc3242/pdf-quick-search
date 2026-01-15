"""Report Generator Service for typo check results.

This service generates HTML and PDF reports from typo check results.
Uses reportlab for PDF generation (pure Python, no system dependencies).
"""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


class ReportGenerator:
    """Service for generating typo check reports in various formats."""

    @staticmethod
    def _register_korean_font():
        """Register Korean font for PDF generation."""
        import platform

        system = platform.system()

        # Try to register a Korean font based on OS
        font_paths = []

        if system == "Darwin":  # macOS
            font_paths = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/Library/Fonts/AppleGothic.ttf",
                "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            ]
        elif system == "Linux":
            font_paths = [
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            ]
        elif system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/malgun.ttf",
                "C:/Windows/Fonts/gulim.ttc",
            ]

        for font_path in font_paths:
            try:
                import os

                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont("Korean", font_path))
                    return "Korean"
            except Exception:
                continue

        # Fallback to Helvetica (won't display Korean properly but won't crash)
        return "Helvetica"

    @staticmethod
    def _build_proofread_text(corrected_text: str, issues: list) -> str:
        """Build proofread text with inline corrections.

        Args:
            corrected_text: The corrected text
            issues: List of issues with original/corrected pairs

        Returns:
            Text with inline correction markup
        """
        if not issues:
            return corrected_text

        # Get ordered issues with numbers
        ordered_issues = ReportGenerator._get_ordered_issues(corrected_text, issues)

        # Process from end to start to preserve positions
        result = corrected_text
        processed_positions = set()

        for pos, issue, number in reversed(ordered_issues):
            if pos == float("inf") or pos in processed_positions:
                continue

            original = issue.get("original", "")
            corrected_word = issue.get("corrected", "")

            # Create inline markup with number: (N) <del>원본</del> <ins>수정</ins>
            markup = (
                f'<span class="correction">'
                f'<span class="correction-number">({number})</span>'
                f"<del>{original}</del> <ins>{corrected_word}</ins>"
                f"</span>"
            )
            result = result[:pos] + markup + result[pos + len(corrected_word) :]
            processed_positions.add(pos)

        return result

    @staticmethod
    def _get_ordered_issues(corrected_text: str, issues: list) -> list:
        """Get issues ordered by their appearance in the corrected text.

        Args:
            corrected_text: The corrected text
            issues: List of issues

        Returns:
            List of (position, issue, number) tuples sorted by position
        """
        positioned_issues = []
        for issue in issues:
            corrected_word = issue.get("corrected", "")
            if corrected_word:
                pos = corrected_text.find(corrected_word)
                if pos != -1:
                    positioned_issues.append((pos, issue))
                else:
                    positioned_issues.append((float("inf"), issue))
            else:
                positioned_issues.append((float("inf"), issue))

        # Sort by position
        positioned_issues.sort(key=lambda x: x[0])

        # Add numbers
        return [
            (pos, issue, idx + 1) for idx, (pos, issue) in enumerate(positioned_issues)
        ]

    @staticmethod
    def _build_proofread_pdf(corrected_text: str, issues: list, font_name: str):
        """Build proofread Paragraph for PDF with inline corrections.

        Args:
            corrected_text: The corrected text
            issues: List of issues with original/corrected pairs
            font_name: Font name to use

        Returns:
            Paragraph object with inline correction markup
        """
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

        styles = getSampleStyleSheet()
        body_style = ParagraphStyle(
            "ProofreadBody",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=18,
            textColor=colors.HexColor("#333333"),
        )

        if not issues:
            text = corrected_text.replace("\n", "<br/>")
            return Paragraph(text, body_style)

        # Get ordered issues with numbers
        ordered_issues = ReportGenerator._get_ordered_issues(corrected_text, issues)

        # Process from end to start to preserve positions
        result = corrected_text
        processed_positions = set()

        for pos, issue, number in reversed(ordered_issues):
            if pos == float("inf") or pos in processed_positions:
                continue

            original = issue.get("original", "")
            corrected_word = issue.get("corrected", "")

            # Create inline markup for PDF with number: (N) strikethrough original + bold corrected
            markup = (
                f'<font color="#3b82f6"><b>({number})</b></font> '
                f'<font color="#dc2626" size="9"><strike>{original}</strike></font> '
                f'<font color="#16a34a"><b>{corrected_word}</b></font>'
            )
            result = result[:pos] + markup + result[pos + len(corrected_word) :]
            processed_positions.add(pos)

        # Replace newlines with HTML breaks
        result = result.replace("\n", "<br/>")

        return Paragraph(result, body_style)

    @staticmethod
    def generate_html(data: Dict[str, Any]) -> bytes:
        """Generate HTML report from typo check result.

        Args:
            data: TypoCheckResult data containing corrected_text, issues, etc.

        Returns:
            HTML content as bytes
        """
        corrected_text = data.get("corrected_text", "")
        issues = data.get("issues", [])
        provider = data.get("provider", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build proofread text with inline corrections
        proofread_text = ReportGenerator._build_proofread_text(corrected_text, issues)

        # Build issues summary HTML with numbers
        issues_html = ""
        if issues:
            # Get ordered issues for consistent numbering
            ordered_issues = ReportGenerator._get_ordered_issues(corrected_text, issues)

            issues_html = "<ul class='issues-list'>"
            for _pos, issue, number in ordered_issues:
                original = issue.get("original", "")
                corrected = issue.get("corrected", "")
                issue_type = issue.get("type", issue.get("issue_type", "unknown"))
                explanation = issue.get("explanation", "")

                type_label = {
                    "spelling": "맞춤법",
                    "spacing": "띄어쓰기",
                    "grammar": "문법",
                    "punctuation": "구두점",
                    "style": "스타일",
                }.get(issue_type, issue_type)

                issues_html += f"""
                <li class="issue-item">
                    <span class="issue-number">{number}</span>
                    <span class="issue-type">[{type_label}]</span>
                    <span class="original">{original}</span>
                    <span class="arrow">→</span>
                    <span class="corrected">{corrected}</span>
                    <p class="explanation">{explanation}</p>
                </li>
                """
            issues_html += "</ul>"
        else:
            issues_html = "<p class='no-issues'>발견된 오류가 없습니다.</p>"

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>맞춤법 검사 결과</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a1a;
            font-size: 24px;
            margin-bottom: 8px;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 12px;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #1a1a1a;
            font-size: 18px;
            margin: 30px 0 15px;
        }}
        .corrected-text {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            white-space: pre-wrap;
            font-size: 15px;
            line-height: 1.8;
        }}
        .issues-list {{
            list-style: none;
        }}
        .issue-item {{
            background: #fff7ed;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid #f97316;
        }}
        .issue-type {{
            background: #f97316;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        }}
        .original {{
            color: #dc2626;
            text-decoration: line-through;
        }}
        .arrow {{
            color: #666;
            margin: 0 8px;
        }}
        .corrected {{
            color: #16a34a;
            font-weight: bold;
        }}
        .explanation {{
            color: #666;
            font-size: 14px;
            margin-top: 8px;
            padding-left: 10px;
            border-left: 2px solid #ddd;
        }}
        .no-issues {{
            background: #f0fdf4;
            padding: 20px;
            border-radius: 8px;
            color: #16a34a;
            text-align: center;
        }}
        .summary {{
            background: #eff6ff;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .summary-item {{
            display: inline-block;
            margin-right: 20px;
        }}
        .summary-label {{
            color: #666;
            font-size: 13px;
        }}
        .summary-value {{
            color: #3b82f6;
            font-weight: bold;
            font-size: 18px;
        }}
        /* Inline correction styles */
        .correction {{
            background: #fffbeb;
            padding: 2px 4px;
            border-radius: 4px;
            border-bottom: 2px solid #f59e0b;
        }}
        .correction-number {{
            color: #3b82f6;
            font-weight: bold;
            margin-right: 2px;
        }}
        .correction del {{
            color: #dc2626;
            text-decoration: line-through;
            font-size: 0.9em;
        }}
        .correction ins {{
            color: #16a34a;
            font-weight: bold;
            text-decoration: none;
        }}
        .issue-number {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            background: #3b82f6;
            color: white;
            border-radius: 50%;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
            flex-shrink: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>맞춤법 검사 결과</h1>
        <p class="meta">생성일: {timestamp} | AI 모델: {provider.upper()}</p>

        <div class="summary">
            <span class="summary-item">
                <span class="summary-label">발견된 오류</span>
                <span class="summary-value">{len(issues)}개</span>
            </span>
        </div>

        <h2>교정된 텍스트</h2>
        <div class="corrected-text">{proofread_text}</div>

        <h2>발견된 오류 목록</h2>
        {issues_html}
    </div>
</body>
</html>"""

        return html.encode("utf-8")

    @staticmethod
    def generate_pdf(data: Dict[str, Any]) -> bytes:
        """Generate PDF report from typo check result using reportlab.

        Args:
            data: TypoCheckResult data containing corrected_text, issues, etc.

        Returns:
            PDF content as bytes
        """
        buffer = BytesIO()

        # Register Korean font
        font_name = ReportGenerator._register_korean_font()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        # Get data
        corrected_text = data.get("corrected_text", "")
        issues = data.get("issues", [])
        provider = data.get("provider", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create styles
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=18,
            spaceAfter=10,
            textColor=colors.HexColor("#1a1a1a"),
        )

        meta_style = ParagraphStyle(
            "Meta",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            textColor=colors.HexColor("#666666"),
            spaceAfter=20,
        )

        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#1a1a1a"),
        )

        summary_style = ParagraphStyle(
            "Summary",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=12,
            textColor=colors.HexColor("#3b82f6"),
            backColor=colors.HexColor("#eff6ff"),
            borderPadding=10,
        )

        # Build document content
        story = []

        # Title
        story.append(Paragraph("맞춤법 검사 결과", title_style))

        # Meta info
        story.append(
            Paragraph(f"생성일: {timestamp} | AI 모델: {provider.upper()}", meta_style)
        )

        # Summary
        story.append(Paragraph(f"발견된 오류: {len(issues)}개", summary_style))
        story.append(Spacer(1, 10))

        # Corrected text section with inline proofreading
        story.append(Paragraph("교정된 텍스트", heading_style))

        # Build proofread text with inline corrections for PDF
        proofread_pdf_text = ReportGenerator._build_proofread_pdf(
            corrected_text, issues, font_name
        )
        story.append(proofread_pdf_text)

        # Issues summary section
        story.append(Spacer(1, 10))
        story.append(Paragraph("수정 내역", heading_style))

        if issues:
            # Issue item style
            issue_style = ParagraphStyle(
                "Issue",
                parent=styles["Normal"],
                fontName=font_name,
                fontSize=10,
                leading=14,
                spaceBefore=6,
                spaceAfter=6,
                leftIndent=10,
                textColor=colors.HexColor("#333333"),
            )

            type_labels = {
                "spelling": "맞춤법",
                "spacing": "띄어쓰기",
                "grammar": "문법",
                "punctuation": "구두점",
                "style": "스타일",
            }

            # Get ordered issues with numbers
            ordered_issues = ReportGenerator._get_ordered_issues(corrected_text, issues)

            for _pos, issue, number in ordered_issues:
                issue_type = type_labels.get(
                    issue.get("type", issue.get("issue_type", "")),
                    issue.get("type", issue.get("issue_type", "기타")),
                )
                original = issue.get("original", "")
                corrected_word = issue.get("corrected", "")
                explanation = issue.get("explanation", "")

                # Format: (N) [유형] 원본 → 수정 : 설명
                issue_text = (
                    f'<font color="#3b82f6"><b>({number})</b></font> '
                    f'<font color="#f97316"><b>[{issue_type}]</b></font> '
                    f'<font color="#dc2626"><strike>{original}</strike></font> '
                    f'<font color="#666666">→</font> '
                    f'<font color="#16a34a"><b>{corrected_word}</b></font>'
                )
                if explanation:
                    issue_text += (
                        f'<br/><font color="#666666" size="9">{explanation}</font>'
                    )

                story.append(Paragraph(issue_text, issue_style))
        else:
            no_issues_style = ParagraphStyle(
                "NoIssues",
                parent=styles["Normal"],
                fontName=font_name,
                fontSize=12,
                textColor=colors.HexColor("#16a34a"),
                alignment=1,  # Center
            )
            story.append(Paragraph("발견된 오류가 없습니다.", no_issues_style))

        # Build PDF
        doc.build(story)

        buffer.seek(0)
        return buffer.read()
