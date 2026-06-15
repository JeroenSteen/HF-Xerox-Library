#!/usr/bin/env python3
import json
import re
import sys
import os

def parse_yield(val):
    """
    Parse yield values with various formats
    """
    if not val or not isinstance(val, str) or not val.strip():
        return ""
    
    s = val.strip()
    
    # Handle ranges like "60K/80K" or "387K/446K" - take first value
    if '/' in s:
        parts = s.split('/')
        for part in parts:
            part = part.strip()
            if 'K' in part.upper() or part.isdigit() or (part.replace('.', '').isdigit()):
                s = part
                break
        else:
            return val.strip()
    
    # Handle grams (weight measurements) - extract numeric value
    g_match = re.match(r'^(\d+(?:\.\d+)?)g$', s, re.IGNORECASE)
    if g_match:
        return g_match.group(1)
    
    # Handle K suffix (thousands)
    k_match = re.match(r'^(\d+(?:\.\d+)?)K$', s, re.IGNORECASE)
    if k_match:
        num = float(k_match.group(1))
        return str(int(num * 1000))
    
    # Handle numbers with commas
    comma_match = re.match(r'^(\d{1,3}(?:,\d{3})*)$', s)
    if comma_match:
        return str(int(s.replace(',', '')))
    
    # Handle plain numbers
    plain_match = re.match(r'^(\d+(?:\.\d+)?)$', s)
    if plain_match:
        num = float(plain_match.group(1))
        return str(int(num))
    
    # Fallback: return original stripped
    return val.strip()

def main():
    # Check command line arguments
    if len(sys.argv) < 3:
        print("Usage: python3 norm_yield.py <input_file.json> <output_file.json>")
        print("\nExample:")
        print("  python3 norm_yield.py data.json output.json")
        print("  python3 norm_yield.py /path/to/input.json /path/to/output.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)
    
    try:
        # Read input JSON
        print(f"Reading from: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("Error: Expected JSON array at root")
            sys.exit(1)
        
        print(f"Loaded {len(data)} records")
        
        # Process records
        modified = 0
        samples = []
        
        for item in data:
            if isinstance(item, dict):
                original = item.get('yield', '')
                parsed = parse_yield(original)
                
                if original != parsed and len(samples) < 10:
                    samples.append((original, parsed))
                
                if original != parsed:
                    modified += 1
                
                item['yield'] = parsed
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Write output JSON
        print(f"Writing to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*50)
        print("COMPLETE")
        print("="*50)
        print(f"Total records: {len(data)}")
        print(f"Modified: {modified}")
        
        if samples:
            print("\nSample normalizations:")
            for orig, parsed in samples:
                print(f"  {orig!r:30s} -> {parsed!r}")
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()