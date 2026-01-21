"""Tests for search API and service."""

import pytest
import json


class TestSearchService:
    """Test cases for search service."""

    def test_search_returns_matching_documents(self, app):
        """Test search returns documents with matching content."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.search_service import SearchService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

            doc1 = SearchDocument(
                owner_id=user.id,
                filename="doc1.pdf",
                original_filename="doc1.pdf",
                file_path="/storage/doc1.pdf",
                extraction_status="completed"
            )
            doc2 = SearchDocument(
                owner_id=user.id,
                filename="doc2.pdf",
                original_filename="doc2.pdf",
                file_path="/storage/doc2.pdf",
                extraction_status="completed"
            )
            db.session.add_all([doc1, doc2])
            db.session.commit()

            # Add pages with content
            page1 = SearchPage(
                document_id=doc1.id,
                page_number=1,
                content="Python programming language",
                content_normalized="python programming language"
            )
            page2 = SearchPage(
                document_id=doc2.id,
                page_number=1,
                content="JavaScript tutorial",
                content_normalized="javascript tutorial"
            )
            db.session.add_all([page1, page2])
            db.session.commit()

            results, total = SearchService.search(user.id, "python")

            assert total == 1
            assert len(results) == 1
            assert results[0]["document"]["filename"] == "doc1.pdf"

    def test_search_query_minimum_length(self, app):
        """Test search requires minimum 2 characters."""
        from app.services.search_service import SearchService

        with app.app_context():
            results, total = SearchService.search("user-id", "a")

            assert total == 0
            assert len(results) == 0

    def test_search_filters_by_owner(self, app):
        """Test search only returns documents owned by the user."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.search_service import SearchService

        with app.app_context():
            user1 = User(
                email="user1@example.com",
                name="User 1",
                password="password123",
                approval_status="approved"
            )
            user2 = User(
                email="user2@example.com",
                name="User 2",
                password="password123",
                approval_status="approved"
            )
            db.session.add_all([user1, user2])
            db.session.commit()

            doc1 = SearchDocument(
                owner_id=user1.id,
                filename="doc1.pdf",
                original_filename="doc1.pdf",
                file_path="/storage/doc1.pdf",
                extraction_status="completed"
            )
            doc2 = SearchDocument(
                owner_id=user2.id,
                filename="doc2.pdf",
                original_filename="doc2.pdf",
                file_path="/storage/doc2.pdf",
                extraction_status="completed"
            )
            db.session.add_all([doc1, doc2])
            db.session.commit()

            page1 = SearchPage(
                document_id=doc1.id,
                page_number=1,
                content="Python tutorial",
                content_normalized="python tutorial"
            )
            page2 = SearchPage(
                document_id=doc2.id,
                page_number=1,
                content="Python programming",
                content_normalized="python programming"
            )
            db.session.add_all([page1, page2])
            db.session.commit()

            # User1 should only see their document
            results, total = SearchService.search(user1.id, "python")

            assert total == 1
            assert results[0]["document"]["owner_id"] == user1.id

    def test_search_generates_snippet(self, app):
        """Test search generates snippet with context."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.search_service import SearchService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

            doc = SearchDocument(
                owner_id=user.id,
                filename="doc.pdf",
                original_filename="doc.pdf",
                file_path="/storage/doc.pdf",
                extraction_status="completed"
            )
            db.session.add(doc)
            db.session.commit()

            long_content = "A" * 50 + " Python " + "B" * 50
            page = SearchPage(
                document_id=doc.id,
                page_number=1,
                content=long_content,
                content_normalized=long_content.lower()
            )
            db.session.add(page)
            db.session.commit()

            results, total = SearchService.search(user.id, "python")

            assert total == 1
            assert "snippet" in results[0]
            # Snippet should contain the search term
            assert "python" in results[0]["snippet"].lower()

    def test_search_pagination(self, app):
        """Test search pagination with limit and offset."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.search_service import SearchService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

            # Create multiple documents with matching content
            for i in range(5):
                doc = SearchDocument(
                    owner_id=user.id,
                    filename=f"doc{i}.pdf",
                    original_filename=f"doc{i}.pdf",
                    file_path=f"/storage/doc{i}.pdf",
                    extraction_status="completed"
                )
                db.session.add(doc)
                db.session.commit()

                page = SearchPage(
                    document_id=doc.id,
                    page_number=1,
                    content=f"Python content {i}",
                    content_normalized=f"python content {i}"
                )
                db.session.add(page)
                db.session.commit()

            # Test with limit
            results, total = SearchService.search(user.id, "python", limit=2)
            assert total == 5
            assert len(results) == 2

            # Test with offset
            results, total = SearchService.search(user.id, "python", limit=2, offset=2)
            assert total == 5
            assert len(results) == 2

    def test_search_case_insensitive(self, app):
        """Test search is case insensitive."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.search_service import SearchService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

            doc = SearchDocument(
                owner_id=user.id,
                filename="doc.pdf",
                original_filename="doc.pdf",
                file_path="/storage/doc.pdf",
                extraction_status="completed"
            )
            db.session.add(doc)
            db.session.commit()

            page = SearchPage(
                document_id=doc.id,
                page_number=1,
                content="PYTHON PROGRAMMING",
                content_normalized="python programming"
            )
            db.session.add(page)
            db.session.commit()

            # Search with different cases should all match
            results1, _ = SearchService.search(user.id, "python")
            results2, _ = SearchService.search(user.id, "PYTHON")
            results3, _ = SearchService.search(user.id, "Python")

            assert len(results1) == 1
            assert len(results2) == 1
            assert len(results3) == 1

    def test_generate_snippet_with_context(self, app):
        """Test snippet generation with context around match."""
        from app.services.search_service import SearchService

        with app.app_context():
            content = "The quick brown fox jumps over the lazy dog. Python is great."
            snippet = SearchService.generate_snippet(content, "python")

            assert "python" in snippet.lower()
            # Should have some context
            assert len(snippet) > len("python")

    def test_generate_snippet_no_match(self, app):
        """Test snippet generation when query not in content."""
        from app.services.search_service import SearchService

        with app.app_context():
            content = "This content has no matching terms"
            snippet = SearchService.generate_snippet(content, "python")

            # Should return empty or truncated content
            assert snippet is not None


class TestSearchAPI:
    """Test cases for search API endpoints."""

    def test_search_endpoint_success(self, app, client):
        """Test successful search via API endpoint."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

            doc = SearchDocument(
                owner_id=user.id,
                filename="doc.pdf",
                original_filename="doc.pdf",
                file_path="/storage/doc.pdf",
                extraction_status="completed"
            )
            db.session.add(doc)
            db.session.commit()

            page = SearchPage(
                document_id=doc.id,
                page_number=1,
                content="Python programming guide",
                content_normalized="python programming guide"
            )
            db.session.add(page)
            db.session.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        # Search
        response = client.get(
            "/api/search?q=python",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "results" in data
        assert "total" in data
        assert data["total"] == 1

    def test_search_endpoint_no_query(self, app, client):
        """Test search endpoint with missing query returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/search",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_search_endpoint_query_too_short(self, app, client):
        """Test search endpoint with query too short returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/search?q=a",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_search_endpoint_unauthorized(self, client):
        """Test search endpoint requires authentication."""
        response = client.get("/api/search?q=python")

        assert response.status_code == 401

    def test_search_endpoint_pagination(self, app, client):
        """Test search endpoint pagination parameters."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

            # Create multiple documents
            for i in range(5):
                doc = SearchDocument(
                    owner_id=user.id,
                    filename=f"doc{i}.pdf",
                    original_filename=f"doc{i}.pdf",
                    file_path=f"/storage/doc{i}.pdf",
                    extraction_status="completed"
                )
                db.session.add(doc)
                db.session.commit()

                page = SearchPage(
                    document_id=doc.id,
                    page_number=1,
                    content=f"Python content {i}",
                    content_normalized=f"python content {i}"
                )
                db.session.add(page)
                db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        # Test with limit
        response = client.get(
            "/api/search?q=python&limit=2",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data["total"] == 5
        assert len(data["results"]) == 2

    def test_search_isolates_user_data(self, app, client):
        """Test search does not return other users' documents."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

        with app.app_context():
            user1 = User(
                email="user1@example.com",
                name="User 1",
                password="password123",
                approval_status="approved"
            )
            user2 = User(
                email="user2@example.com",
                name="User 2",
                password="password123",
                approval_status="approved"
            )
            db.session.add_all([user1, user2])
            db.session.commit()

            # User1's document
            doc1 = SearchDocument(
                owner_id=user1.id,
                filename="user1_doc.pdf",
                original_filename="user1_doc.pdf",
                file_path="/storage/user1_doc.pdf",
                extraction_status="completed"
            )
            # User2's document
            doc2 = SearchDocument(
                owner_id=user2.id,
                filename="user2_doc.pdf",
                original_filename="user2_doc.pdf",
                file_path="/storage/user2_doc.pdf",
                extraction_status="completed"
            )
            db.session.add_all([doc1, doc2])
            db.session.commit()

            page1 = SearchPage(
                document_id=doc1.id,
                page_number=1,
                content="Secret Python data",
                content_normalized="secret python data"
            )
            page2 = SearchPage(
                document_id=doc2.id,
                page_number=1,
                content="Secret Python data",
                content_normalized="secret python data"
            )
            db.session.add_all([page1, page2])
            db.session.commit()

        # Login as user1
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user1@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        # User1 should only see their own document
        response = client.get(
            "/api/search?q=python",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.get_json()
        assert data["total"] == 1
        assert data["results"][0]["document"]["original_filename"] == "user1_doc.pdf"
