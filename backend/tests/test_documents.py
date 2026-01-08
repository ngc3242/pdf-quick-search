"""Tests for document management API."""

import pytest
import json
import io
import os


class TestDocumentUpload:
    """Test cases for document upload endpoint."""

    def get_auth_token(self, app, client):
        """Helper to create user and get auth token."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        return response.get_json()["access_token"]

    def test_upload_pdf_success(self, app, client):
        """Test successful PDF upload returns 202."""
        token = self.get_auth_token(app, client)

        # Create a fake PDF file
        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (io.BytesIO(pdf_content), "test_document.pdf", "application/pdf")
        }

        response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type="multipart/form-data"
        )

        assert response.status_code == 202
        result = response.get_json()
        assert "document" in result
        assert result["document"]["original_filename"] == "test_document.pdf"
        assert result["document"]["extraction_status"] == "pending"

    def test_upload_sets_owner_id(self, app, client):
        """Test uploaded document has correct owner_id."""
        token = self.get_auth_token(app, client)

        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (io.BytesIO(pdf_content), "test_document.pdf", "application/pdf")
        }

        response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type="multipart/form-data"
        )

        result = response.get_json()
        assert result["document"]["owner_id"] is not None

    def test_upload_no_file(self, app, client):
        """Test upload without file returns 400."""
        token = self.get_auth_token(app, client)

        response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            content_type="multipart/form-data"
        )

        assert response.status_code == 400

    def test_upload_non_pdf(self, app, client):
        """Test upload of non-PDF file returns 400."""
        token = self.get_auth_token(app, client)

        # Create a fake text file
        txt_content = b"This is not a PDF"
        data = {
            "file": (io.BytesIO(txt_content), "document.txt", "text/plain")
        }

        response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type="multipart/form-data"
        )

        assert response.status_code == 400

    def test_upload_without_auth(self, client):
        """Test upload without authentication returns 401."""
        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (io.BytesIO(pdf_content), "test_document.pdf", "application/pdf")
        }

        response = client.post(
            "/api/documents",
            data=data,
            content_type="multipart/form-data"
        )

        assert response.status_code == 401


class TestDocumentList:
    """Test cases for document list endpoint."""

    def get_auth_token(self, app, client, email="test@example.com"):
        """Helper to create user and get auth token."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email=email,
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": email, "password": "password123"}),
            content_type="application/json"
        )
        return response.get_json()["access_token"], user_id

    def test_list_documents_empty(self, app, client):
        """Test listing documents when user has none."""
        token, _ = self.get_auth_token(app, client)

        response = client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        result = response.get_json()
        assert "documents" in result
        assert len(result["documents"]) == 0

    def test_list_documents_owner_filter(self, app, client):
        """Test that users only see their own documents."""
        from app.models.document import SearchDocument
        from app.models import db

        # Create first user and upload document
        token1, user1_id = self.get_auth_token(app, client, "user1@example.com")

        pdf_content = b"%PDF-1.4 test content"
        data = {"file": (io.BytesIO(pdf_content), "user1_doc.pdf", "application/pdf")}
        client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token1}"},
            data=data,
            content_type="multipart/form-data"
        )

        # Create second user
        token2, user2_id = self.get_auth_token(app, client, "user2@example.com")

        # User2 should see no documents
        response = client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {token2}"}
        )

        result = response.get_json()
        assert len(result["documents"]) == 0

        # User1 should see their document
        response = client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {token1}"}
        )

        result = response.get_json()
        assert len(result["documents"]) == 1
        assert result["documents"][0]["original_filename"] == "user1_doc.pdf"

    def test_list_documents_pagination(self, app, client):
        """Test document list pagination."""
        token, _ = self.get_auth_token(app, client)

        # Upload multiple documents
        for i in range(5):
            pdf_content = b"%PDF-1.4 test content"
            data = {"file": (io.BytesIO(pdf_content), f"doc_{i}.pdf", "application/pdf")}
            client.post(
                "/api/documents",
                headers={"Authorization": f"Bearer {token}"},
                data=data,
                content_type="multipart/form-data"
            )

        # Get first page
        response = client.get(
            "/api/documents?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"}
        )

        result = response.get_json()
        assert len(result["documents"]) == 2
        assert result["total"] == 5
        assert result["page"] == 1

    def test_list_documents_without_auth(self, client):
        """Test listing documents without auth returns 401."""
        response = client.get("/api/documents")
        assert response.status_code == 401


class TestDocumentDelete:
    """Test cases for document delete endpoint."""

    def get_auth_token(self, app, client, email="test@example.com"):
        """Helper to create user and get auth token."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email=email,
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": email, "password": "password123"}),
            content_type="application/json"
        )
        return response.get_json()["access_token"], user_id

    def test_delete_own_document(self, app, client):
        """Test deleting own document succeeds."""
        token, _ = self.get_auth_token(app, client)

        # Upload document
        pdf_content = b"%PDF-1.4 test content"
        data = {"file": (io.BytesIO(pdf_content), "to_delete.pdf", "application/pdf")}
        upload_response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type="multipart/form-data"
        )
        doc_id = upload_response.get_json()["document"]["id"]

        # Delete document
        response = client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify document is deleted
        list_response = client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert len(list_response.get_json()["documents"]) == 0

    def test_delete_other_user_document_forbidden(self, app, client):
        """Test deleting another user's document returns 403."""
        # User1 uploads document
        token1, _ = self.get_auth_token(app, client, "user1@example.com")

        pdf_content = b"%PDF-1.4 test content"
        data = {"file": (io.BytesIO(pdf_content), "user1_doc.pdf", "application/pdf")}
        upload_response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token1}"},
            data=data,
            content_type="multipart/form-data"
        )
        doc_id = upload_response.get_json()["document"]["id"]

        # User2 tries to delete
        token2, _ = self.get_auth_token(app, client, "user2@example.com")

        response = client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 403

    def test_delete_nonexistent_document(self, app, client):
        """Test deleting non-existent document returns 404."""
        token, _ = self.get_auth_token(app, client)

        response = client.delete(
            "/api/documents/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestDocumentDownload:
    """Test cases for document download endpoint."""

    def get_auth_token(self, app, client, email="test@example.com"):
        """Helper to create user and get auth token."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email=email,
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": email, "password": "password123"}),
            content_type="application/json"
        )
        return response.get_json()["access_token"], user_id

    def test_download_own_document(self, app, client):
        """Test downloading own document succeeds."""
        token, _ = self.get_auth_token(app, client)

        # Upload document
        pdf_content = b"%PDF-1.4 test content for download"
        data = {"file": (io.BytesIO(pdf_content), "download_test.pdf", "application/pdf")}
        upload_response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type="multipart/form-data"
        )
        doc_id = upload_response.get_json()["document"]["id"]

        # Download document
        response = client.get(
            f"/api/documents/{doc_id}/file",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.content_type == "application/pdf"

    def test_download_other_user_document_forbidden(self, app, client):
        """Test downloading another user's document returns 403."""
        # User1 uploads document
        token1, _ = self.get_auth_token(app, client, "user1@example.com")

        pdf_content = b"%PDF-1.4 test content"
        data = {"file": (io.BytesIO(pdf_content), "user1_doc.pdf", "application/pdf")}
        upload_response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token1}"},
            data=data,
            content_type="multipart/form-data"
        )
        doc_id = upload_response.get_json()["document"]["id"]

        # User2 tries to download
        token2, _ = self.get_auth_token(app, client, "user2@example.com")

        response = client.get(
            f"/api/documents/{doc_id}/file",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 403

    def test_download_with_range_header(self, app, client):
        """Test download with Range header for partial content."""
        token, _ = self.get_auth_token(app, client)

        # Upload document
        pdf_content = b"%PDF-1.4 test content for range download test"
        data = {"file": (io.BytesIO(pdf_content), "range_test.pdf", "application/pdf")}
        upload_response = client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type="multipart/form-data"
        )
        doc_id = upload_response.get_json()["document"]["id"]

        # Download with range header
        response = client.get(
            f"/api/documents/{doc_id}/file",
            headers={
                "Authorization": f"Bearer {token}",
                "Range": "bytes=0-9"
            }
        )

        # Should return 206 Partial Content or 200 OK
        assert response.status_code in [200, 206]
