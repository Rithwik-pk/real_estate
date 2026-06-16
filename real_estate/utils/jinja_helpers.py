"""Jinja helpers exposed to print formats."""


def get_qr_code_url(data: str) -> str:
    """Return a QR code URL for payment links on rent invoices."""
    import urllib.parse
    encoded = urllib.parse.quote(str(data))
    return f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={encoded}"
