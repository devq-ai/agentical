"""
Input Sanitization Utilities for Agentical

This module provides utilities for sanitizing user input to prevent security
vulnerabilities like XSS, SQL injection, and other injection attacks.

Features:
- HTML content sanitization
- File path and filename sanitization
- SQL query parameter sanitization
- JSON sanitization
- General text input sanitization
"""

import re
import os
import html
import json
from typing import Any, Dict, List, Optional, Set, Union, Pattern
import logging
import unicodedata
from urllib.parse import urlparse, quote

import logfire
from fastapi import HTTPException, status

# Logger setup
logger = logging.getLogger(__name__)


def sanitize_html(content: str, allowed_tags: Optional[List[str]] = None) -> str:
    """Sanitize HTML content to prevent XSS attacks.
    
    Args:
        content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags, None for escaping all tags
        
    Returns:
        Sanitized HTML content
    """
    if allowed_tags is None:
        # Escape all HTML
        return html.escape(content)
    
    # Define the set of allowed tags
    allowed = set(allowed_tags)
    
    # Basic regex pattern for matching HTML tags
    tag_pattern = re.compile(r'<(/?)(\w+)([^>]*)>', re.IGNORECASE)
    
    def _replace_tag(match):
        closing, tag, attributes = match.groups()
        if tag.lower() in allowed:
            # Keep allowed tags
            return f'<{closing}{tag}{attributes}>'
        else:
            # Escape disallowed tags
            return html.escape(match.group(0))
    
    # Replace tags based on whether they're allowed
    sanitized = tag_pattern.sub(_replace_tag, content)
    
    # Remove potentially dangerous attributes
    dangerous_attrs = [
        'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 
        'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup',
        'onload', 'onerror', 'onabort', 'onunload', 'onbeforeunload',
        'onresize', 'onscroll', 'javascript:', 'expression', 'vbscript:',
        'data:'
    ]
    
    attr_pattern = re.compile(
        r'(\s)(' + '|'.join(dangerous_attrs) + r')(\s*=\s*["\'][^"\']*["\'])',
        re.IGNORECASE
    )
    sanitized = attr_pattern.sub(r'\1sanitized-\2\3', sanitized)
    
    return sanitized


def sanitize_filename(filename: str, replacement_char: str = '_') -> str:
    """Sanitize a filename to prevent path traversal and command injection.
    
    Args:
        filename: The filename to sanitize
        replacement_char: Character to replace invalid characters with
        
    Returns:
        Sanitized filename
    """
    # Replace directory separators
    sanitized = filename.replace('/', replacement_char).replace('\\', replacement_char)
    
    # Remove control characters
    sanitized = ''.join(c if ord(c) >= 32 else replacement_char for c in sanitized)
    
    # Remove null bytes
    sanitized = sanitized.replace('\0', '')
    
    # Remove potentially dangerous characters
    dangerous_chars = [':', '*', '?', '"', '<', '>', '|', ';', '&', '$', '`', '!']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, replacement_char)
    
    # Normalize unicode characters
    sanitized = unicodedata.normalize('NFKD', sanitized)
    
    # Handle special cases
    if sanitized in {'.', '..'}:
        sanitized = replacement_char * len(sanitized)
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = 'unnamed'
    
    return sanitized


def sanitize_path(path: str, allowed_paths: Optional[List[str]] = None) -> str:
    """Sanitize a file path to prevent path traversal and command injection.
    
    Args:
        path: The file path to sanitize
        allowed_paths: List of allowed root paths
        
    Returns:
        Sanitized file path
    
    Raises:
        HTTPException: If the path is not within allowed paths
    """
    # Normalize path (resolve ../, etc.)
    normalized = os.path.normpath(path)
    
    # Ensure path doesn't escape using normalization
    if '..' in normalized.split(os.path.sep):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal detected"
        )
    
    # If allowed paths are specified, ensure path is within them
    if allowed_paths:
        is_allowed = False
        abs_path = os.path.abspath(normalized)
        
        for allowed_path in allowed_paths:
            abs_allowed = os.path.abspath(allowed_path)
            if abs_path.startswith(abs_allowed):
                is_allowed = True
                break
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path not allowed"
            )
    
    return normalized


def sanitize_sql_param(param: str) -> str:
    """Sanitize SQL query parameters to prevent SQL injection.
    
    Args:
        param: The SQL parameter to sanitize
        
    Returns:
        Sanitized SQL parameter
    """
    # Replace single quotes
    sanitized = param.replace("'", "''")
    
    # Replace other potentially dangerous characters
    sanitized = sanitized.replace(";", "")
    
    # Remove comments
    sanitized = re.sub(r'--.*$', '', sanitized)
    sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)
    
    return sanitized


def sanitize_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """Sanitize a URL to prevent open redirect and SSRF vulnerabilities.
    
    Args:
        url: The URL to sanitize
        allowed_schemes: List of allowed URL schemes
        
    Returns:
        Sanitized URL
    
    Raises:
        HTTPException: If the URL uses a disallowed scheme
    """
    if not allowed_schemes:
        allowed_schemes = ['http', 'https']
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Check scheme
    if parsed.scheme not in allowed_schemes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL scheme not allowed: {parsed.scheme}"
        )
    
    # Sanitize path
    sanitized_path = quote(parsed.path)
    
    # Rebuild the URL
    return f"{parsed.scheme}://{parsed.netloc}{sanitized_path}"


def sanitize_json(data: Any) -> Any:
    """Sanitize JSON data for security.
    
    Args:
        data: The JSON data to sanitize
        
    Returns:
        Sanitized JSON data
    """
    if isinstance(data, dict):
        return {sanitize_input(k): sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(item) for item in data]
    elif isinstance(data, str):
        return sanitize_input(data)
    else:
        return data


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """General purpose input sanitization for text.
    
    Args:
        text: The text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Convert to string if necessary
    if not isinstance(text, str):
        text = str(text)
    
    # Trim whitespace
    sanitized = text.strip()
    
    # Remove control characters
    sanitized = ''.join(c for c in sanitized if unicodedata.category(c)[0] != 'C' or c in ['\t', '\n', '\r'])
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_email(email: str) -> str:
    """Sanitize an email address.
    
    Args:
        email: The email address to sanitize
        
    Returns:
        Sanitized email address
    
    Raises:
        HTTPException: If the email format is invalid
    """
    # Basic email format check
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Trim whitespace and convert to lowercase
    sanitized = email.strip().lower()
    
    return sanitized


def sanitize_phone(phone: str) -> str:
    """Sanitize a phone number.
    
    Args:
        phone: The phone number to sanitize
        
    Returns:
        Sanitized phone number
    """
    # Remove all non-digit characters
    sanitized = re.sub(r'\D', '', phone)
    
    # Ensure it's not too long
    if len(sanitized) > 15:  # International standard E.164 allows up to 15 digits
        sanitized = sanitized[:15]
    
    return sanitized