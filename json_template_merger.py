#!/usr/bin/env python3
"""
JSON Structure Merger - Merges simple JSON into complete template structure
Usage: python merge_json.py <source_file> <output_file>
"""

import json
import sys
import os

# Template structure with all required fields
TEMPLATE_STRUCTURE = {
    "part_number": "",
    "color": "",
    "printer_model": "",
    "consumable_type": "",
    "yield": "",
    "region_zone": "",
    "metered_sold": "",
    "iot_codename": "",
    "chip_type": ""
}

def merge_json(source_file, output_file):
    """
    Merge source JSON into the complete template structure
    Handles both single objects and arrays of objects
    """
    try:
        # Read source JSON
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        results = []
        
        # Handle different types of input
        if isinstance(source_data, dict):
            # Single object
            results.append(process_single_object(source_data))
        elif isinstance(source_data, list):
            # Array of objects
            for index, item in enumerate(source_data):
                if isinstance(item, dict):
                    results.append(process_single_object(item))
                else:
                    print(f"⚠️ Warning: Skipping item at index {index} - not an object")
        else:
            print(f"❌ Error: Source JSON must be an object or array of objects, got {type(source_data)}")
            return False
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Successfully processed {source_file} -> {output_file}")
        print(f"📊 Processed {len(results)} item(s)")
        
        # Show preview of first 2 items
        print(f"\n📋 Preview (first 2 items):")
        for i, item in enumerate(results[:2]):
            print(f"\nItem {i + 1}:")
            print(json.dumps(item, indent=2))
        
        if len(results) > 2:
            print(f"\n... and {len(results) - 2} more item(s)")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: File '{source_file}' not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{source_file}': {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_single_object(source_obj):
    """
    Process a single JSON object
    """
    # Create result based on template
    result = TEMPLATE_STRUCTURE.copy()
    
    # Merge matching fields from source
    for key in source_obj:
        if key in result:
            result[key] = source_obj[key]
    
    return result

def main():
    # Check command line arguments
    if len(sys.argv) != 3:
        print("JSON Structure Merger")
        print("=" * 40)
        print("Usage: python merge_json.py <source_file> <output_file>")
        print("\nExamples:")
        print("  python merge_json.py simple.json complete.json")
        print("  python merge_json.py input.json output.json")
        print("\nTemplate structure includes these fields:")
        for field in TEMPLATE_STRUCTURE.keys():
            print(f"  - {field}")
        sys.exit(1)
    
    source_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Check if source file exists
    if not os.path.exists(source_file):
        print(f"❌ Source file '{source_file}' not found")
        sys.exit(1)
    
    # Execute merge
    print(f"🔄 Processing '{source_file}'...")
    success = merge_json(source_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()