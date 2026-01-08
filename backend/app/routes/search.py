"""Search API routes."""

from flask import Blueprint, request, jsonify, g

from app.services.search_service import SearchService
from app.utils.auth import jwt_required

search_bp = Blueprint("search", __name__)


@search_bp.route("", methods=["GET"])
@jwt_required
def search():
    """Search documents for matching content.

    Query parameters:
        q: Search query (required, minimum 2 characters)
        limit: Maximum results (default 50, max 100)
        offset: Results to skip (default 0)

    Returns:
        JSON with results array and total count
    """
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Search query 'q' is required"}), 400

    if len(query) < SearchService.MIN_QUERY_LENGTH:
        return jsonify({
            "error": f"Search query must be at least {SearchService.MIN_QUERY_LENGTH} characters"
        }), 400

    limit = request.args.get("limit", SearchService.DEFAULT_LIMIT, type=int)
    offset = request.args.get("offset", 0, type=int)

    results, total = SearchService.search(
        user_id=g.user_id,
        query=query,
        limit=limit,
        offset=offset
    )

    return jsonify({
        "results": results,
        "total": total,
        "query": query,
        "limit": min(limit, SearchService.MAX_LIMIT),
        "offset": offset
    }), 200
