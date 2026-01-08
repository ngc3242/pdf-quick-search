"""Document management API routes."""

import os
from flask import Blueprint, request, jsonify, g, send_file, Response

from app.services.document_service import DocumentService
from app.utils.auth import jwt_required
from app.utils.storage import get_file_path

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("", methods=["POST"])
@jwt_required
def upload_document():
    """Upload a new document.

    Accepts multipart/form-data with file field.

    Returns:
        202 Accepted with document info on success
        400 Bad Request on validation error
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    document, error = DocumentService.upload_document(file, g.user_id)

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": "Document uploaded successfully",
        "document": document.to_dict()
    }), 202


@documents_bp.route("", methods=["GET"])
@jwt_required
def list_documents():
    """List documents for current user.

    Query parameters:
        page: Page number (default 1)
        per_page: Items per page (default 20, max 100)

    Returns:
        JSON with documents array and pagination info
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    documents, total = DocumentService.get_documents_by_owner(
        g.user_id, page, per_page
    )

    return jsonify({
        "documents": [doc.to_dict() for doc in documents],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }), 200


@documents_bp.route("/<int:document_id>", methods=["GET"])
@jwt_required
def get_document(document_id: int):
    """Get document details.

    Args:
        document_id: Document ID

    Returns:
        JSON with document info
        403 if not owner
        404 if not found
    """
    document, error = DocumentService.verify_document_access(
        document_id, g.user_id
    )

    if error:
        status_code = 404 if error == "Document not found" else 403
        return jsonify({"error": error}), status_code

    return jsonify({"document": document.to_dict()}), 200


@documents_bp.route("/<int:document_id>", methods=["DELETE"])
@jwt_required
def delete_document(document_id: int):
    """Delete a document.

    Args:
        document_id: Document ID

    Returns:
        200 on success
        403 if not owner
        404 if not found
    """
    success, error = DocumentService.delete_document(document_id, g.user_id)

    if not success:
        status_code = 404 if error == "Document not found" else 403
        return jsonify({"error": error}), status_code

    return jsonify({"message": "Document deleted successfully"}), 200


@documents_bp.route("/<int:document_id>/file", methods=["GET"])
@jwt_required
def download_document(document_id: int):
    """Download document file.

    Supports Range header for partial content.

    Args:
        document_id: Document ID

    Returns:
        File content with appropriate headers
        403 if not owner
        404 if not found
    """
    document, error = DocumentService.verify_document_access(
        document_id, g.user_id
    )

    if error:
        status_code = 404 if error == "Document not found" else 403
        return jsonify({"error": error}), status_code

    file_path = document.file_path

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found on disk"}), 404

    # Check for Range header
    range_header = request.headers.get("Range")

    if range_header:
        return _handle_range_request(
            file_path,
            document.original_filename,
            document.file_size_bytes
        )

    return send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=document.original_filename
    )


def _handle_range_request(
    file_path: str,
    filename: str,
    file_size: int
) -> Response:
    """Handle Range request for partial content.

    Args:
        file_path: Path to file
        filename: Original filename
        file_size: Total file size

    Returns:
        Response with partial content or full file
    """
    range_header = request.headers.get("Range", "")

    try:
        # Parse range header
        range_spec = range_header.replace("bytes=", "")
        start_str, end_str = range_spec.split("-")

        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1

        if start >= file_size:
            return Response(status=416)  # Range Not Satisfiable

        end = min(end, file_size - 1)
        length = end - start + 1

        with open(file_path, "rb") as f:
            f.seek(start)
            data = f.read(length)

        response = Response(
            data,
            status=206,
            mimetype="application/pdf",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(length),
                "Accept-Ranges": "bytes",
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        return response

    except (ValueError, OSError):
        # If range parsing fails, return full file
        return send_file(
            file_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
