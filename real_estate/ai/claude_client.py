"""
Central Claude API client for the real_estate app.
API key stored in site_config.json as `real_estate_claude_api_key`.
"""
import frappe


MODEL = "claude-sonnet-4-6"


def _get_client():
    try:
        import anthropic
    except ImportError:
        frappe.throw("The 'anthropic' Python package is not installed. Run: pip install anthropic")
    api_key = frappe.conf.get("real_estate_claude_api_key")
    if not api_key:
        frappe.throw(
            "Claude API key not configured. Add `real_estate_claude_api_key` to site_config.json."
        )
    return anthropic.Anthropic(api_key=api_key)


def call_claude(prompt: str, max_tokens: int = 1024, system: str = None) -> str:
    """
    Send a prompt to Claude and return the text response.
    Returns empty string on any error (caller decides how to surface it).
    """
    try:
        client = _get_client()
        kwargs = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text
    except Exception as e:
        frappe.log_error(f"Claude API error: {e}", "Real Estate AI")
        return ""


def stream_claude(prompt: str, max_tokens: int = 1024, system: str = None):
    """
    Generator that yields text chunks from a Claude streaming response.
    Use in SSE / websocket contexts.
    """
    try:
        client = _get_client()
        kwargs = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        frappe.log_error(f"Claude stream error: {e}", "Real Estate AI")
        yield ""
