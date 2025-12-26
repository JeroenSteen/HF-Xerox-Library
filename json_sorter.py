#!/usr/bin/env python3
"""
JSON File Sorter - Sort JSON files by multiple keys with priority
Usage: python json_sorter.py input.json output.json --keys key1 key2 key3 [--reverse] [--indent]
"""

import json
import argparse
import sys
import os
from typing import List, Dict, Any, Union, Optional

def sort_json_data(
    data: Union[str, List[Dict], Dict],
    sort_keys: List[str],
    reverse: Union[bool, List[bool]] = False,
    missing_key_strategy: str = 'last'
) -> Any:
    """
    Sort JSON data by multiple keys
    
    Args:
        data: JSON data to sort
        sort_keys: List of keys to sort by (in priority order)
        reverse: True for descending, or list of bools per key
        missing_key_strategy: How to handle missing keys ('first', 'last', 'error')
    
    Returns:
        Sorted JSON data
    """
    # Handle dictionary with single list
    if isinstance(data, dict) and len(data) == 1:
        # Try to find a list in the dictionary
        for key, value in data.items():
            if isinstance(value, list):
                # Sort the list and keep the dictionary structure
                sorted_list = sort_json_data(value, sort_keys, reverse, missing_key_strategy)
                return {key: sorted_list}
    
    # If data is a single dictionary (not a list), wrap it in a list
    if isinstance(data, dict):
        data = [data]
    
    # Parse JSON string if needed
    if isinstance(data, str):
        data = json.loads(data)
    
    # If not a list at this point, return as-is
    if not isinstance(data, list):
        return data
    
    # Normalize reverse parameter
    if isinstance(reverse, bool):
        reverse_list = [reverse] * len(sort_keys)
    else:
        reverse_list = reverse
        if len(reverse_list) != len(sort_keys):
            raise ValueError("Length of reverse list must match number of sort keys")
    
    # Create sort key function
    def get_sort_value(item: Dict, key: str, is_reverse: bool) -> Any:
        """Get value for sorting with missing key handling"""
        if key not in item:
            if missing_key_strategy == 'error':
                raise KeyError(f"Key '{key}' not found in item")
            elif missing_key_strategy == 'first':
                return float('-inf') if not is_reverse else float('inf')
            elif missing_key_strategy == 'last':
                return float('inf') if not is_reverse else float('-inf')
        
        value = item[key]
        
        # Handle None values
        if value is None:
            return float('-inf') if not is_reverse else float('inf')
        
        return value
    
    def sort_key(item: Dict) -> tuple:
        """Create tuple for multi-key sorting"""
        return tuple(
            get_sort_value(item, key, rev)
            for key, rev in zip(sort_keys, reverse_list)
        )
    
    # Sort the data
    sorted_data = sorted(data, key=sort_key)
    
    return sorted_data

def load_json_file(file_path: str) -> Any:
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

def save_json_file(data: Any, file_path: str, indent: Optional[int] = 2) -> None:
    """Save JSON data to file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        print(f"✓ Successfully saved sorted JSON to '{file_path}'")
    except IOError as e:
        print(f"Error: Could not write to '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Sort JSON files by multiple keys with priority',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sort by name, then age (both ascending)
  python json_sorter.py data.json sorted.json --keys name age
  
  # Sort with different directions
  python json_sorter.py data.json sorted.json --keys name age --reverse false true
  
  # Sort and overwrite original file
  python json_sorter.py data.json data.json --keys priority date --indent 4
  
  # Sort complex nested JSON
  python json_sorter.py data.json sorted.json --keys "user.name" "user.age" --missing-key last
        """
    )
    
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('output_file', help='Output JSON file path (can be same as input to overwrite)')
    
    parser.add_argument('--keys', '-k', nargs='+', required=True,
                       help='Keys to sort by, in priority order (use dot notation for nested keys: user.name)')
    
    parser.add_argument('--reverse', '-r', nargs='+', type=lambda x: x.lower() == 'true',
                       help='Reverse sorting for each key (true/false). Single value applies to all keys.')
    
    parser.add_argument('--missing-key', '-m', choices=['first', 'last', 'error'],
                       default='last', help='How to handle missing keys (default: last)')
    
    parser.add_argument('--indent', '-i', type=int, default=2,
                       help='Indentation for output JSON (default: 2, use 0 for compact)')
    
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show preview without saving')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed information')
    
    return parser.parse_args()

def get_nested_value(item: Dict, key_path: str) -> Any:
    """Get value from nested dictionary using dot notation"""
    keys = key_path.split('.')
    value = item
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"Key '{key}' not found in path '{key_path}'")
    return value

def prepare_data_with_nested_keys(data: List[Dict], sort_keys: List[str]) -> List[Dict]:
    """Flatten nested keys for sorting"""
    prepared_data = []
    
    for item in data:
        flat_item = item.copy()
        for key_path in sort_keys:
            if '.' in key_path:
                # Extract nested value and add to flat item
                try:
                    value = get_nested_value(item, key_path)
                    flat_item[key_path] = value
                except KeyError:
                    flat_item[key_path] = None
        prepared_data.append(flat_item)
    
    return prepared_data

def main():
    """Main function"""
    args = parse_arguments()
    
    if args.verbose:
        print(f"Input file: {args.input_file}")
        print(f"Output file: {args.output_file}")
        print(f"Sort keys: {args.keys}")
        print(f"Missing key strategy: {args.missing_key}")
    
    # Load JSON data
    data = load_json_file(args.input_file)
    
    if args.verbose:
        print(f"Loaded JSON with {len(data) if isinstance(data, list) else 1} items")
    
    # Check if data is a list
    original_is_dict = isinstance(data, dict) and not isinstance(data, list)
    
    # Handle nested keys by flattening
    has_nested_keys = any('.' in key for key in args.keys)
    
    if has_nested_keys and isinstance(data, list):
        # Prepare data with flattened nested keys
        data_to_sort = prepare_data_with_nested_keys(data, args.keys)
        sort_keys = args.keys  # Use the same keys (now they exist in flattened data)
    else:
        data_to_sort = data
        sort_keys = args.keys
    
    # Parse reverse argument
    if args.reverse:
        if len(args.reverse) == 1:
            # Single value applies to all keys
            reverse_arg = args.reverse[0]
            if args.verbose:
                direction = "descending" if reverse_arg else "ascending"
                print(f"Sort direction: {direction} for all keys")
        else:
            reverse_arg = args.reverse
            if len(reverse_arg) != len(args.keys):
                print(f"Error: Number of reverse flags ({len(reverse_arg)}) must match number of keys ({len(args.keys)})", file=sys.stderr)
                sys.exit(1)
            if args.verbose:
                for key, rev in zip(args.keys, reverse_arg):
                    direction = "descending" if rev else "ascending"
                    print(f"  {key}: {direction}")
    else:
        reverse_arg = False
    
    try:
        # Sort the data
        sorted_data = sort_json_data(
            data=data_to_sort,
            sort_keys=sort_keys,
            reverse=reverse_arg,
            missing_key_strategy=args.missing_key
        )
        
        # If we flattened for nested keys, restore original structure
        if has_nested_keys and isinstance(data, list) and isinstance(sorted_data, list):
            # Remove the flattened keys we added
            restored_data = []
            for item in sorted_data:
                original_item = {k: v for k, v in item.items() if k not in args.keys or '.' not in k}
                restored_data.append(original_item)
            sorted_data = restored_data
        
        # If original was a single dict, extract it
        if original_is_dict and isinstance(sorted_data, list) and len(sorted_data) == 1:
            sorted_data = sorted_data[0]
        
    except Exception as e:
        print(f"Error during sorting: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Show preview if dry-run or verbose
    if args.dry_run or args.verbose:
        print("\n" + "="*50)
        print("SORTED DATA PREVIEW:")
        print("="*50)
        preview = json.dumps(
            sorted_data[:3] if isinstance(sorted_data, list) and len(sorted_data) > 3 else sorted_data,
            indent=2,
            ensure_ascii=False
        )
        print(preview)
        
        if isinstance(sorted_data, list) and len(sorted_data) > 3:
            print(f"\n... and {len(sorted_data) - 3} more items")
    
    # Save or show message
    if args.dry_run:
        print("\n✓ Dry run completed. No files were modified.")
        if args.input_file == args.output_file:
            print("⚠ Warning: This would overwrite the original file!")
    else:
        save_json_file(sorted_data, args.output_file, args.indent)
        
        if args.input_file == args.output_file:
            print("⚠ Original file has been overwritten.")

if __name__ == '__main__':
    main()