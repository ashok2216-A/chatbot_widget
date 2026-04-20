import os
import requests
import urllib.parse
from typing import Dict, Any, Optional

def search_place(query: str) -> Dict[str, Any]:
    """Returns raw location data."""
    encoded_query = urllib.parse.quote(query)
    return {
        "location_name": query,
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
    }

def get_directions(origin: str, destination: str) -> Dict[str, Any]:
    """Returns raw directions data."""
    encoded_origin = urllib.parse.quote(origin)
    encoded_dest = urllib.parse.quote(destination)
    return {
        "origin": origin,
        "destination": destination,
        "directions_url": f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_dest}"
    }

"""
=== USAGE RULES ===
1. ALWAYS output your response as a raw JSON block wrapped in triple backticks.
2. The root must always be { "a2ui": { "component": "...", ... } }.
3. Do NOT add conversational filler or text outside the code block.
4. Use the `Map` component for all location displays.

=== EXAMPLES ===
User: "Where is the Burj Khalifa?"
Assistant: 
```json
{
  "a2ui": {
    "component": "Card",
    "title": "📍 Burj Khalifa",
    "children": [
      { "component": "Map", "location": "Burj Khalifa, Dubai", "zoom": 15 },
      { "component": "Text", "value": "I found the **Burj Khalifa** in Dubai.", "variant": "body" },
      { "component": "Button", "label": "View on Google Maps", "url": "https://www.google.com/maps/...", "icon": "explore" }
    ]
  }
}
```
"""
