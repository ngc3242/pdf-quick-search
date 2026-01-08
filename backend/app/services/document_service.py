"""Document service for PDF management."""

from typing import Optional, Tuple, List
from werkzeug.datastructures import FileStorage

from app.models import db
from app.models.document import SearchDocument
from app.utils.storage import allowed_file, save_file, delete_file


class DocumentService:
    """Service class for document operations."""

    @staticmethod
    def upload_document(
        file: FileStorage, owner_id: str
    ) -> Tuple[Optional[SearchDocument], Optional[str]]:
        """Upload and save a document.

        Args:
            file: Uploaded file
            owner_id: User ID of document owner

        Returns:
            Tuple of (SearchDocument, error_message)
        """
        if not file or not file.filename:
            return None, "No file provided"

        if not allowed_file(file.filename):
            return None, "Only PDF files are allowed"

        # Save file
        unique_filename, file_path, file_size = save_file(file)

        if not unique_filename:
            return None, "Failed to save file"

        # Create document record
        document = SearchDocument(
            owner_id=owner_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size_bytes=file_size,
            mime_type="application/pdf",
        )

        db.session.add(document)
        db.session.commit()

        # Add to extraction queue for background processing
        from app.services.extraction_service import ExtractionService

        ExtractionService.add_to_queue(document.id)

        # Wake up the extraction worker (if it's paused)
        from app.worker import extraction_worker

        extraction_worker.wake_up()

        return document, None

    @staticmethod
    def get_documents_by_owner(
        owner_id: str, page: int = 1, per_page: int = 20
    ) -> Tuple[List[SearchDocument], int]:
        """Get documents for a specific owner with pagination.

        Args:
            owner_id: User ID
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Tuple of (documents list, total count)
        """
        query = SearchDocument.query.filter_by(
            owner_id=owner_id, is_active=True
        ).order_by(SearchDocument.uploaded_at.desc())

        total = query.count()
        documents = query.offset((page - 1) * per_page).limit(per_page).all()

        return documents, total

    @staticmethod
    def get_document_by_id(document_id: int) -> Optional[SearchDocument]:
        """Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            SearchDocument or None
        """
        return SearchDocument.query.filter_by(id=document_id, is_active=True).first()

    @staticmethod
    def delete_document(document_id: int, owner_id: str) -> Tuple[bool, Optional[str]]:
        """Delete a document.

        Args:
            document_id: Document ID
            owner_id: User ID for ownership verification

        Returns:
            Tuple of (success, error_message)
        """
        document = DocumentService.get_document_by_id(document_id)

        if not document:
            return False, "Document not found"

        if document.owner_id != owner_id:
            return False, "Access denied"

        # Delete file from storage
        delete_file(document.file_path)

        # Delete from database
        db.session.delete(document)
        db.session.commit()

        return True, None

    @staticmethod
    def verify_document_access(
        document_id: int, owner_id: str
    ) -> Tuple[Optional[SearchDocument], Optional[str]]:
        """Verify user has access to document.

        Args:
            document_id: Document ID
            owner_id: User ID

        Returns:
            Tuple of (document, error_message)
        """
        document = DocumentService.get_document_by_id(document_id)

        if not document:
            return None, "Document not found"

        if document.owner_id != owner_id:
            return None, "Access denied"

        return document, None
