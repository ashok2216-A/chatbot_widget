import re
import json

def parse_a2ui_chunks(text: str):
    """
    Enhanced parser for A2UI Hybrid Protocol.
    Splits text into chunks of 'text' and 'a2ui' (JSON blocks).
    Handles malformed JSON and trailing commas gracefully.
    """
    if not text: return []
    chunks = []
    # Match triple backtick JSON blocks
    pattern = r'```(?:[\w\-]*)\s*(\{[\s\S]*?\})\s*```'
    last_pos = 0

    def clean_json(s: str) -> str:
        # Remove trailing commas in arrays/objects before parsing
        s = re.sub(r",\s*([\]\}])", r"\1", s)
        return s

    for match in re.finditer(pattern, text):
        start, end = match.span()
        # Add preceding text
        if start > last_pos:
            pre_text = text[last_pos:start].strip()
            if pre_text: chunks.append({"type": "text", "content": pre_text})
        
        json_str = clean_json(match.group(1).strip())
        try:
            chunks.append({"type": "a2ui", "content": json.loads(json_str)})
        except Exception:
            # If JSON parsing fails, treat it as raw text
            chunks.append({"type": "text", "content": match.group(0)})
        last_pos = end
    
    # Check for any remaining text after the last block
    remaining = text[last_pos:].strip()
    if remaining:
        # Fallback for "naked" data_view blocks without backticks
        if "data_view" in remaining:
            try:
                # Basic search for the first { and last }
                start_idx = remaining.find('{')
                end_idx = remaining.rfind('}')
                if start_idx != -1 and end_idx > start_idx:
                    json_str = clean_json(remaining[start_idx:end_idx+1])
                    content = json.loads(json_str)
                    pre = remaining[:start_idx].strip()
                    if pre: chunks.append({"type": "text", "content": pre})
                    chunks.append({"type": "a2ui", "content": content})
                    remaining = remaining[end_idx+1:].strip()
            except Exception:
                pass
        
        if remaining:
            chunks.append({"type": "text", "content": remaining})
            
    return chunks
