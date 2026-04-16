import json
import os

FILE = "hashes.json"

def get_hashes():
    if not os.path.exists(FILE):
        return set()
    with open(FILE, "r") as f:
        return set(json.load(f))

def save_hash(h):
    hashes = get_hashes()
    hashes.add(h)
    with open(FILE, "w") as f:
        json.dump(list(hashes), f)
