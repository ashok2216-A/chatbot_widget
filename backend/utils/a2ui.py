import re
import json

# Keys that indicate an A2UI block
A2UI_KEYS = {"a2ui", "data_view"}

def parse_a2ui_chunks(text: str):
    """
    Enhanced parser for A2UI Hybrid Protocol v3.
    Splits text into chunks of 'text' and 'a2ui' (JSON blocks).
    Supports both:
      - New node-tree: { "a2ui": { "component": "...", ... } }
      - Legacy cards:  { "data_view": { "text": "...", "items": [...] } }
    Handles malformed JSON and trailing commas gracefully.
    """
    if not text:
        return []

    chunks = []
    pattern = r'```(?:[\w\-]*)\s*(\{[\s\S]*?\})\s*```'
    last_pos = 0

    def clean_json(s: str) -> str:
        """Remove trailing commas before closing braces/brackets."""
        s = re.sub(r",\s*([\]\}])", r"\1", s)
        return s

    def is_a2ui_block(obj: dict) -> bool:
        return bool(A2UI_KEYS & set(obj.keys()))

    for match in re.finditer(pattern, text):
        start, end = match.span()

        # Add preceding text chunk
        if start > last_pos:
            pre_text = text[last_pos:start].strip()
            if pre_text:
                chunks.append({"type": "text", "content": pre_text})

        json_str = clean_json(match.group(1).strip())
        try:
            obj = json.loads(json_str)
            if is_a2ui_block(obj):
                chunks.append({"type": "a2ui", "content": obj})
            else:
                # Valid JSON but not an A2UI block — render as text
                chunks.append({"type": "text", "content": match.group(0)})
        except Exception:
            # Malformed JSON — render block as raw text
            chunks.append({"type": "text", "content": match.group(0)})
        last_pos = end

    # Handle remaining text after the last backtick block
    remaining = text[last_pos:].strip()
    if remaining:
        # Fallback: detect "naked" a2ui/data_view blocks without backticks
        has_naked_block = any(f'"{key}"' in remaining for key in A2UI_KEYS)
        if has_naked_block:
            try:
                start_idx = remaining.find('{')
                end_idx = remaining.rfind('}')
                if start_idx != -1 and end_idx > start_idx:
                    json_str = clean_json(remaining[start_idx:end_idx + 1])
                    obj = json.loads(json_str)
                    if is_a2ui_block(obj):
                        pre = remaining[:start_idx].strip()
                        if pre:
                            chunks.append({"type": "text", "content": pre})
                        chunks.append({"type": "a2ui", "content": obj})
                        remaining = remaining[end_idx + 1:].strip()
            except Exception:
                pass  # Fall through to plain text

        if remaining:
            chunks.append({"type": "text", "content": remaining})

    return chunks
