import json
import sys
from typing import Dict, List, Any, Union

def load_json_file(filepath: str) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    """Load JSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{filepath}': {e}")
        return None
    except Exception as e:
        print(f"Error loading file '{filepath}': {e}")
        return None

def save_json_file(filepath: str, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> bool:
    """Save JSON data to file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving file '{filepath}': {e}")
        return False

def find_and_update_printer_models(
    data: Union[List[Dict[str, Any]], Dict[str, Any]], 
    target_model: str,
    field_updates: Dict[str, str]
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Find all exact printer_model matches and update specified fields.
    
    Args:
        data: JSON data (could be list, dict, or single object)
        target_model: Exact printer_model string to match
        field_updates: Dictionary of {field_name: new_value} to update
    
    Returns:
        Updated JSON data with the same structure as input
    """
    if not field_updates:
        return data
    
    # Handle different data structures
    if isinstance(data, dict):
        # Single dictionary
        if data.get("printer_model") == target_model:
            for field, new_value in field_updates.items():
                if field in data:
                    data[field] = new_value
        return data
    
    elif isinstance(data, list):
        # List of dictionaries
        updated_data = []
        matches_found = 0
        
        for item in data:
            if isinstance(item, dict) and item.get("printer_model") == target_model:
                # Create a copy to avoid modifying the original
                updated_item = item.copy()
                for field, new_value in field_updates.items():
                    if field in updated_item:
                        updated_item[field] = new_value
                updated_data.append(updated_item)
                matches_found += 1
            else:
                # Keep non-matching items unchanged
                updated_data.append(item)
        
        print(f"Found {matches_found} exact match(es) for printer model: '{target_model}'")
        return updated_data
    
    else:
        # Unsupported data type
        print(f"Warning: Unsupported data type: {type(data)}. Returning data unchanged.")
        return data

def get_field_updates_from_user() -> Dict[str, str]:
    """Get field updates from user input."""
    field_updates = {}
    
    print("\n--- Field Updates ---")
    print("Enter field names and new values to update.")
    print("Press Enter on field name to finish.")
    
    while True:
        field_name = input("\nEnter field name to update (or press Enter to finish): ").strip()
        
        if not field_name:
            break
        
        new_value = input(f"Enter new value for '{field_name}': ").strip()
        field_updates[field_name] = new_value
    
    return field_updates

def process_json_file():
    """Main function to process JSON file."""
    print("=== JSON Printer Model Updater ===\n")
    
    # Get input file path
    input_file = input("Enter path to input JSON file: ").strip()
    if not input_file:
        print("No file specified. Exiting.")
        return
    
    # Load JSON data
    print(f"\nLoading data from '{input_file}'...")
    data = load_json_file(input_file)
    if data is None:
        return
    
    # Show data structure info
    if isinstance(data, list):
        print(f"Loaded {len(data)} items from JSON file.")
        if data and isinstance(data[0], dict):
            print("Available fields:", list(data[0].keys()))
    elif isinstance(data, dict):
        print("Loaded single object from JSON file.")
        print("Available fields:", list(data.keys()))
    
    # Get target printer model
    print("\n" + "="*50)
    target_model = input("Enter exact printer_model string to find: ").strip()
    if not target_model:
        print("No printer model specified. Exiting.")
        return
    
    # Get field updates
    print("\n" + "="*50)
    field_updates = get_field_updates_from_user()
    
    if not field_updates:
        print("No fields specified for update. Exiting.")
        return
    
    # Apply updates
    print("\n" + "="*50)
    print("Applying updates...")
    updated_data = find_and_update_printer_models(data, target_model, field_updates)
    
    # Output options
    print("\n" + "="*50)
    print("Output Options:")
    print("1. Save to new file")
    print("2. Overwrite original file")
    print("3. Print to console")
    print("4. Save and print")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice in ["1", "4"]:
        output_file = input("Enter path for output JSON file: ").strip()
        if output_file:
            if save_json_file(output_file, updated_data):
                print(f"\nData saved to '{output_file}'")
    
    if choice in ["3", "4"]:
        print("\n" + "="*50)
        print("Updated JSON Output:")
        print(json.dumps(updated_data, indent=2, ensure_ascii=False))
    
    if choice == "2":
        confirm = input(f"\nWARNING: This will overwrite '{input_file}'. Continue? (yes/no): ").strip().lower()
        if confirm in ["yes", "y"]:
            if save_json_file(input_file, updated_data):
                print(f"\nOriginal file '{input_file}' updated successfully.")
        else:
            print("Overwrite cancelled.")
    
    print("\nDone!")

def batch_process_files():
    """Process multiple JSON files with the same updates."""
    print("=== Batch JSON Processor ===\n")
    
    # Get file list
    files_input = input("Enter JSON file paths (comma-separated): ").strip()
    if not files_input:
        print("No files specified. Exiting.")
        return
    
    file_paths = [f.strip() for f in files_input.split(",") if f.strip()]
    
    # Get target and updates once
    print("\n" + "="*50)
    target_model = input("Enter exact printer_model string to find: ").strip()
    
    print("\n" + "="*50)
    field_updates = get_field_updates_from_user()
    
    if not field_updates:
        print("No fields specified for update. Exiting.")
        return
    
    # Process each file
    for filepath in file_paths:
        print(f"\n{'='*50}")
        print(f"Processing: {filepath}")
        
        data = load_json_file(filepath)
        if data is None:
            continue
        
        updated_data = find_and_update_printer_models(data, target_model, field_updates)
        
        # Save with "_updated" suffix
        base_name, ext = filepath.rsplit('.', 1) if '.' in filepath else (filepath, 'json')
        output_file = f"{base_name}_updated.{ext}"
        
        if save_json_file(output_file, updated_data):
            print(f"Saved updated data to: {output_file}")

if __name__ == "__main__":
    print("JSON Printer Model Updater")
    print("=" * 50)
    print("1. Process single file")
    print("2. Batch process multiple files")
    
    mode_choice = input("\nSelect mode (1 or 2): ").strip()
    
    if mode_choice == "1":
        process_json_file()
    elif mode_choice == "2":
        batch_process_files()
    else:
        print("Invalid choice. Exiting.")