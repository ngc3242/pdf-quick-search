"""System prompts API routes for admin management."""

from flask import Blueprint, request, jsonify

from app.services.system_prompt_service import SystemPromptService
from app.utils.auth import jwt_required
from app.utils.admin import admin_required

system_prompts_bp = Blueprint("system_prompts", __name__)


@system_prompts_bp.route("", methods=["GET"])
@jwt_required
@admin_required
def get_all_prompts():
    """Get all system prompts with their current configurations.

    Returns prompts for all providers, using custom prompts when available
    and falling back to defaults.

    Returns:
        JSON with prompts array containing provider, prompt, and is_custom flag
    """
    prompts = []

    for provider in SystemPromptService.VALID_PROVIDERS:
        custom = SystemPromptService.get_prompt(provider)

        if custom:
            prompts.append(
                {
                    "provider": provider,
                    "prompt": custom["prompt"],
                    "is_active": custom["is_active"],
                    "is_custom": True,
                    "updated_at": custom.get("updated_at"),
                }
            )
        else:
            default_prompt = SystemPromptService.get_default_prompt(provider)
            prompts.append(
                {
                    "provider": provider,
                    "prompt": default_prompt,
                    "is_active": True,
                    "is_custom": False,
                    "updated_at": None,
                }
            )

    return jsonify({"prompts": prompts}), 200


@system_prompts_bp.route("/<provider>", methods=["GET"])
@jwt_required
@admin_required
def get_prompt(provider: str):
    """Get system prompt for a specific provider.

    Args:
        provider: The AI provider name (claude, gemini, openai)

    Returns:
        JSON with provider, prompt, is_custom flag and other metadata
        400 if provider is invalid
    """
    if provider not in SystemPromptService.VALID_PROVIDERS:
        return jsonify({"error": f"Invalid provider: {provider}"}), 400

    custom = SystemPromptService.get_prompt(provider)

    if custom:
        return jsonify(
            {
                "provider": provider,
                "prompt": custom["prompt"],
                "is_active": custom["is_active"],
                "is_custom": True,
                "updated_at": custom.get("updated_at"),
            }
        ), 200
    else:
        default_prompt = SystemPromptService.get_default_prompt(provider)
        return jsonify(
            {
                "provider": provider,
                "prompt": default_prompt,
                "is_active": True,
                "is_custom": False,
                "updated_at": None,
            }
        ), 200


@system_prompts_bp.route("/<provider>", methods=["PUT"])
@jwt_required
@admin_required
def update_prompt(provider: str):
    """Update or create a custom system prompt for a provider.

    Args:
        provider: The AI provider name (claude, gemini, openai)

    Request body:
        prompt: The new system prompt text (required)

    Returns:
        JSON with updated prompt configuration
        400 if provider is invalid or prompt is empty/missing
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    prompt = data.get("prompt")

    if prompt is None:
        return jsonify({"error": "prompt field is required"}), 400

    try:
        result = SystemPromptService.update_prompt(provider, prompt)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@system_prompts_bp.route("/<provider>/reset", methods=["POST"])
@jwt_required
@admin_required
def reset_prompt(provider: str):
    """Reset a provider's prompt to the default.

    Removes any custom configuration, causing the provider to use
    its built-in default prompt.

    Args:
        provider: The AI provider name (claude, gemini, openai)

    Returns:
        JSON with success message and the default prompt
        400 if provider is invalid
    """
    try:
        SystemPromptService.reset_to_default(provider)
        default_prompt = SystemPromptService.get_default_prompt(provider)
        return jsonify(
            {
                "message": "Prompt reset to default",
                "default_prompt": default_prompt,
            }
        ), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
