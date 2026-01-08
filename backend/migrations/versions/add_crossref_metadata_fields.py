"""Add CrossRef metadata fields to search_documents

Revision ID: add_crossref_metadata
Revises: 52910e77e9d4
Create Date: 2026-01-09

SPEC-CROSSREF-001: Add CrossRef metadata fields for DOI, authors, journal info.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_crossref_metadata"
down_revision = "52910e77e9d4"
branch_labels = None
depends_on = None


def upgrade():
    """Add CrossRef metadata fields to search_documents table."""
    # Add DOI fields
    op.add_column(
        "search_documents", sa.Column("doi", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "search_documents", sa.Column("doi_url", sa.String(length=500), nullable=True)
    )

    # Add publication info fields
    op.add_column(
        "search_documents", sa.Column("publication_year", sa.Integer(), nullable=True)
    )

    # Add author fields
    op.add_column(
        "search_documents",
        sa.Column("first_author", sa.String(length=255), nullable=True),
    )
    op.add_column("search_documents", sa.Column("co_authors", sa.Text(), nullable=True))

    # Add journal/publisher fields
    op.add_column(
        "search_documents",
        sa.Column("journal_name", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "search_documents", sa.Column("publisher", sa.String(length=255), nullable=True)
    )

    # Add metadata status tracking fields
    op.add_column(
        "search_documents",
        sa.Column(
            "metadata_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "search_documents",
        sa.Column("metadata_fetched_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    """Remove CrossRef metadata fields from search_documents table."""
    op.drop_column("search_documents", "metadata_fetched_at")
    op.drop_column("search_documents", "metadata_status")
    op.drop_column("search_documents", "publisher")
    op.drop_column("search_documents", "journal_name")
    op.drop_column("search_documents", "co_authors")
    op.drop_column("search_documents", "first_author")
    op.drop_column("search_documents", "publication_year")
    op.drop_column("search_documents", "doi_url")
    op.drop_column("search_documents", "doi")
