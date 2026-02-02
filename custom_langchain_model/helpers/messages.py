from typing import Tuple, Optional
import base64
import requests
import mimetypes
from urllib.parse import urlparse
import json
from baml_client.types import ContentBlock, ToolCall
from baml_py import Image as BamlImage

import logging
logger = logging.getLogger(__name__)


def get_image_base64_from_url(url: str, timeout: int = 10) -> Optional[Tuple[str, str]]:
    """
    Fetch image from URL and return (mime_type, base64_string)
    
    Returns:
        Tuple[str, str]: (MIME type like 'image/png', base64-encoded string)
        None: On failure (with error logged)
    
    Example:
        mime, b64 = get_image_base64("https://example.com/image.png")
        # mime = "image/png"
        # b64 = "iVBORw0KGgoAAAANSUhEUgAA..."
    """
    try:
        # Fetch image with timeout and user-agent
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ImageFetcher/1.0)"}
        )
        response.raise_for_status()
        
        # Extract MIME type from Content-Type header (cleaned)
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        
        # Fallback 1: Guess from URL extension
        if not content_type or content_type == "application/octet-stream":
            parsed = urlparse(url)
            content_type, _ = mimetypes.guess_type(parsed.path)
        
        # Fallback 2: Default to JPEG if still unknown
        if not content_type or not content_type.startswith("image/"):
            content_type = "image/jpeg"
        
        # Encode to base64 string (UTF-8 decoded)
        base64_string = base64.b64encode(response.content).decode("utf-8")
        
        return content_type, base64_string
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error fetching {url}: {e}")
    except Exception as e:
        print(f"❌ Processing error for {url}: {e}")
    
    return None

def convert_to_baml_image(block: dict) -> BamlImage:
    if block.get("url"):
        # convert to base64
        # due to vllm server got 500 Internal Server Error when passing url directly
        url = block["url"]
        result = get_image_base64_from_url(url)
        if result is None:
            raise ValueError(f"Failed to fetch image from URL: {url}")
        mime_type, base64 = result
        return BamlImage.from_base64(mime_type, base64)
    if block.get("base64"):
        base64 = block["base64"]
        return BamlImage.from_base64(block["mime_type"], block["base64"])

    raise ValueError("Input image block must have either 'url' or 'base64' field.")

from typing import List, Tuple, Dict, Any

def convert_to_baml_content_block(content_blocks: List[Dict[str, Any]]) -> ContentBlock:
    """
    Extract all text strings and image data from multi-modal content blocks.
    
    Returns:
        ContentBlock: Baml ContentBlock with extracted text and image
    """
    text: str = ""
    image: BamlImage | None = None 
    tool_call: ToolCall | None = None
    for block in content_blocks:
        match block:
            # ✅ Text block (Anthropic/OpenAI format)
            case {"type": "text", "text": str(text)}:
                text = text
            
            # ✅ Image block (langchain v1 format)
            case {
                    "type": "image", 
                    "url": url
                } as img_block:
                baml_img = convert_to_baml_image(img_block)
                image = baml_img
            # Base64 image block
            case {
                    "type": "image", 
                    "base64": base64_str,
                    "mime_type": mime_type
                } as img_block:
                baml_img = convert_to_baml_image(img_block)
                image = baml_img
            # {'type': 'tool_call', 'id': '3f9e5d9d-ef81-476b-b5be-5bf48fa7f9f7', 'name': 'add', 'args': {'a': 60, 'b': 10}}
            case {
                    "type": "tool_call",
                    "name": str(name),
                    "args": dict(args)
                }:
                tool_call = ToolCall(
                    name=name,
                    args=json.dumps(args)
                )
            case _:
                logger.warning(f"Skipping unknown content block: {block}")
                
    return ContentBlock(
        text=text,
        img=image,
        tool_call=tool_call
    )

__all__ = [
    "get_image_base64_from_url",
    "convert_to_baml_image",
    "convert_to_baml_content_block",
]