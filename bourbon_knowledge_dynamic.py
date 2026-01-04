"""
Dynamic bourbon knowledge database - AI-researched bourbons added automatically.
This file is auto-populated when users ask about bourbons not in the main database.
"""

BOURBON_KNOWLEDGE_DYNAMIC = {
    # This dictionary will be populated automatically as Claude researches new bourbons
    # Format matches bourbon_knowledge.py structure with full tier metadata
}


def get_bourbon_info_dynamic(bourbon_name: str):
    """Get detailed information about a bourbon from dynamic database."""
    bourbon_lower = bourbon_name.lower().strip()
    
    # Direct lookup
    if bourbon_lower in BOURBON_KNOWLEDGE_DYNAMIC:
        return BOURBON_KNOWLEDGE_DYNAMIC[bourbon_lower]
    
    # Fuzzy matching with normalization
    bourbon_normalized = bourbon_lower.replace("'s", "s").replace("'", "")
    for key, info in BOURBON_KNOWLEDGE_DYNAMIC.items():
        key_normalized = key.replace("'s", "s").replace("'", "")
        
        # Check exact match after normalization
        if bourbon_normalized == key_normalized:
            return info
        
        # Check if search term is in the key
        if bourbon_normalized in key_normalized or key_normalized in bourbon_normalized:
            return info
        
        # Check if search term is in the official name
        name_normalized = info["name"].lower().replace("'s", "s").replace("'", "")
        if bourbon_normalized in name_normalized:
            return info
    
    return None


def add_bourbon_to_dynamic_database(bourbon_info: dict):
    """Add a newly researched bourbon to the dynamic database and persist to file."""
    import fcntl
    import os
    
    try:
        # Generate key from bourbon name
        key = bourbon_info.get("name", "").lower()
        if not key:
            return False
        
        # Add to in-memory dictionary
        BOURBON_KNOWLEDGE_DYNAMIC[key] = bourbon_info
        
        # Persist to file
        file_path = os.path.join(os.path.dirname(__file__), "bourbon_knowledge_dynamic.py")
        
        # Read current file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Find the dictionary definition
        dict_start = None
        dict_end = None
        for i, line in enumerate(lines):
            if "BOURBON_KNOWLEDGE_DYNAMIC = {" in line:
                dict_start = i
            if dict_start is not None and line.strip() == "}":
                dict_end = i
                break
        
        if dict_start is None or dict_end is None:
            print("ERROR: Could not find dictionary in dynamic file")
            return False
        
        # Generate new entry as Python code
        import json
        entry_lines = [f'    "{key}": {{\n']
        for field_key, field_value in bourbon_info.items():
            if isinstance(field_value, str):
                entry_lines.append(f'        "{field_key}": "{field_value}",\n')
            elif isinstance(field_value, list):
                entry_lines.append(f'        "{field_key}": {json.dumps(field_value)},\n')
            elif isinstance(field_value, (int, float)):
                entry_lines.append(f'        "{field_key}": {field_value},\n')
            else:
                entry_lines.append(f'        "{field_key}": {json.dumps(field_value)},\n')
        entry_lines.append('    },\n')
        
        # Insert before closing brace
        new_lines = lines[:dict_end] + entry_lines + lines[dict_end:]
        
        # Write back with file locking
        with open(file_path, 'w') as f:
            # Try to get exclusive lock (non-blocking)
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except:
                pass  # Continue anyway if lock fails
            
            f.writelines(new_lines)
            
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except:
                pass
        
        print(f"✅ Added {bourbon_info['name']} to dynamic database")
        return True
        
    except Exception as e:
        print(f"ERROR adding bourbon to dynamic database: {e}")
        return False
