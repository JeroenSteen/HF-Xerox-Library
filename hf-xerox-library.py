#!/usr/bin/env python3
"""
Xerox Consumables Library - Terminal/CMD Interface
Search and manage Xerox printer consumables data
"""

import json
import sys
import os
from pathlib import Path
import argparse
from collections import defaultdict

# Configuration
DATA_FILE = "xerox_data.json"


def load_data():
    """Load data from JSON file"""
    try:
        if not Path(DATA_FILE).exists():
            print(f"⚠️  Database file '{DATA_FILE}' not found.")
            print("   Please create a JSON file or run the script with sample data.")
            return []
        
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error: '{DATA_FILE}' contains invalid JSON.")
        return []
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return []


def save_data(data):
    """Save data to JSON file"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving data: {e}")
        return False


def parse_yield_range(query):
    """Parse yield range query like '5000-10000' or '>5000' or '<10000'"""
    query = query.strip()

    # Handle ranges like "5000-10000"
    if "-" in query and not query.startswith("-"):
        parts = query.split("-")
        if len(parts) == 2:
            try:
                min_val = int(parts[0].strip())
                max_val = int(parts[1].strip())
                return ("range", min_val, max_val)
            except ValueError:
                return None

    # Handle ">5000"
    if query.startswith(">"):
        try:
            val = int(query[1:].strip())
            return ("greater", val, None)
        except ValueError:
            return None

    # Handle "<10000"
    if query.startswith("<"):
        try:
            val = int(query[1:].strip())
            return ("less", val, None)
        except ValueError:
            return None

    # Handle exact match "5000"
    try:
        val = int(query)
        return ("exact", val, None)
    except ValueError:
        return None


def search_data(search_type, query):
    """Search data based on type and query"""
    data = load_data()
    results = []

    query_lower = query.lower()

    for item in data:
        match = False

        if search_type == "model":
            # Search in printer_model field
            if query_lower in item.get("printer_model", "").lower():
                match = True

        elif search_type == "part":
            # Exact match for part number (case-insensitive)
            if query_lower == item.get("part_number", "").lower():
                match = True

        elif search_type == "color":
            # Exact match for color (case-insensitive)
            if query_lower == item.get("color", "").lower():
                match = True

        elif search_type == "iot":
            # Search in iot_codename field
            if query_lower in item.get("iot_codename", "").lower():
                match = True

        elif search_type == "region":
            # Search in region_zone field
            if query_lower in item.get("region_zone", "").lower():
                match = True

        elif search_type == "consumable_type":
            # Exact match for consumable_type (case-insensitive)
            if query_lower == item.get("consumable_type", "").lower():
                match = True

        elif search_type == "yield":
            # Parse yield range and compare
            yield_spec = parse_yield_range(query)
            if yield_spec:
                item_yield = item.get("yield", "")
                if item_yield:
                    try:
                        item_yield_val = int(str(item_yield).replace(",", ""))
                        op_type, val1, val2 = yield_spec

                        if op_type == "range":
                            if val1 <= item_yield_val <= val2:
                                match = True
                        elif op_type == "greater":
                            if item_yield_val > val1:
                                match = True
                        elif op_type == "less":
                            if item_yield_val < val1:
                                match = True
                        elif op_type == "exact":
                            if item_yield_val == val1:
                                match = True
                    except (ValueError, TypeError):
                        pass

        if match:
            results.append(item)

    return results


def format_yield(yield_str):
    """Format yield for display - shorten large numbers"""
    if not yield_str or str(yield_str).lower() == "n/a":
        return "N/A"
    
    try:
        # Remove commas and convert to int
        yield_val = int(str(yield_str).replace(",", ""))
        
        # Format based on size
        if yield_val >= 1000000:
            return f"{yield_val/1000000:.1f}M"
        elif yield_val >= 1000:
            return f"{yield_val/1000:.0f}K"
        else:
            return str(yield_val)
    except (ValueError, TypeError):
        return str(yield_str)[:8]  # Truncate if not a number


def display_results_clustered(results):
    """Display results clustered by printer model in column format"""
    if not results:
        print("No results found.")
        return

    print(f"\n📋 Found {len(results)} result(s):")
    print("=" * 140)

    # Group results by printer model
    model_groups = defaultdict(list)
    for item in results:
        model = item.get("printer_model", "Unknown Model").strip()
        if not model:
            model = "Unknown Model"
        model_groups[model].append(item)

    # Sort models alphabetically
    sorted_models = sorted(model_groups.keys())

    for model_idx, model in enumerate(sorted_models, 1):
        items = model_groups[model]
        
        print(f"\n🔷 MODEL #{model_idx}: {model}")
        print("─" * 140)
        
        # Group items by consumable type (toner/drum)
        consumable_types = defaultdict(list)
        for item in items:
            ctype = item.get("consumable_type", "unknown").lower()
            if ctype not in ["toner", "drum"]:
                ctype = "other"
            consumable_types[ctype].append(item)
        
        # Display toners first, then drums, then others
        for ctype in ["toner", "drum", "other"]:
            if ctype in consumable_types and consumable_types[ctype]:
                ctype_items = consumable_types[ctype]
                
                # Get emoji for consumable type
                emoji = "🖨️" if ctype == "toner" else "⚙️" if ctype == "drum" else "📦"
                print(f"\n{emoji} {ctype.upper()}S ({len(ctype_items)} item(s)):")
                print("├" + "─" * 138)
                
                # Column headers and widths - INCLUDING CHIP TYPE
                headers = ["Part Number", "Color", "Yield", "Region", "Metered/Sold", "IOT", "Chip Type"]
                max_widths = [18, 12, 10, 12, 14, 15, 12]
                
                # Print header
                header_line = "│ "
                for i, header in enumerate(headers):
                    header_line += f"{header:<{max_widths[i]}} │ "
                print(header_line)
                print("├" + "─" * 138)
                
                # Print items
                for item in sorted(ctype_items, key=lambda x: (x.get("color", ""), x.get("part_number", ""))):
                    # Get and format values
                    part_num = item.get("part_number", "N/A")
                    color = item.get("color", "N/A") or "N/A"
                    yield_val = format_yield(item.get("yield", "N/A"))
                    region = item.get("region_zone", "N/A") or "N/A"
                    metered = item.get("metered_sold", "N/A") or "N/A"
                    iot = item.get("iot_codename", "N/A") or "N/A"
                    chip = item.get("chip_type", "N/A") or "N/A"
                    
                    # Truncate values if needed
                    part_display = part_num[:max_widths[0]]
                    color_display = color[:max_widths[1]]
                    yield_display = yield_val[:max_widths[2]]
                    region_display = region[:max_widths[3]]
                    metered_display = metered[:max_widths[4]]
                    iot_display = iot[:max_widths[5]]
                    chip_display = chip[:max_widths[6]]
                    
                    # Color coding for part numbers (blue)
                    part_display = f"\033[94m{part_display:<{max_widths[0]}}\033[0m"
                    
                    # Color coding for colors
                    color_map = {
                        "black": "\033[90m",    # Dark gray
                        "cyan": "\033[96m",     # Cyan
                        "magenta": "\033[95m",  # Magenta
                        "yellow": "\033[93m",   # Yellow
                    }
                    color_code = color_map.get(color.lower(), "")
                    color_display = f"{color_code}{color_display:<{max_widths[1]}}\033[0m"
                    
                    # Build the line
                    line = "│ "
                    line += f"{part_display} │ "
                    line += f"{color_display} │ "
                    line += f"{yield_display:<{max_widths[2]}} │ "
                    line += f"{region_display:<{max_widths[3]}} │ "
                    line += f"{metered_display:<{max_widths[4]}} │ "
                    line += f"{iot_display:<{max_widths[5]}} │ "
                    line += f"{chip_display:<{max_widths[6]}} │"
                    print(line)
                
                print("└" + "─" * 138)
        
        # Print summary for this model
        print("\n📊 MODEL SUMMARY:")
        print("├" + "─" * 60)
        
        # Count by color for this model
        color_counts = defaultdict(int)
        for item in items:
            color = item.get("color", "Unknown") or "Unknown"
            color_counts[color] += 1
        
        if color_counts:
            colors_display = []
            for color, count in sorted(color_counts.items()):
                if color != "N/A":
                    colors_display.append(f"{color} ({count})")
            
            if colors_display:
                print(f"│ 🎨 Colors: {', '.join(colors_display)}")
        
        # Yield statistics
        yields = []
        for item in items:
            if item.get("yield"):
                try:
                    yields.append(int(str(item["yield"]).replace(",", "")))
                except (ValueError, TypeError):
                    pass
        
        if yields:
            print(f"│ 📊 Yield Range: {min(yields):,} - {max(yields):,} pages")
        
        # Region info
        regions = set()
        for item in items:
            if item.get("region_zone"):
                regions.add(item["region_zone"])
        
        if regions:
            print(f"│ 🌍 Regions: {', '.join(sorted(regions))}")
        
        print("└" + "─" * 60)


def display_results_simple(results):
    """Simple display for non-model searches (like part number search)"""
    if not results:
        print("No results found.")
        return

    print(f"\n📋 Found {len(results)} result(s):")
    print("=" * 120)

    for idx, item in enumerate(results, 1):
        print(f"\n📦 ITEM #{idx}:")
        print("─" * 120)
        
        # Main details in columns WITH CHIP TYPE
        print("│ Part Number     │ Color        │ Yield     │ Region       │ Metered/Sold │ IOT         │ Chip Type   │")
        print("├─────────────────┼──────────────┼───────────┼──────────────┼──────────────┼─────────────┼─────────────┤")
        
        part_num = item.get("part_number", "N/A")
        color = item.get("color", "N/A") or "N/A"
        yield_val = format_yield(item.get("yield", "N/A"))
        region = item.get("region_zone", "N/A") or "N/A"
        metered = item.get("metered_sold", "N/A") or "N/A"
        iot = item.get("iot_codename", "N/A") or "N/A"
        chip = item.get("chip_type", "N/A") or "N/A"
        
        # Color coding
        part_display = f"\033[94m{part_num[:15]:<15}\033[0m"
        
        color_map = {
            "black": "\033[90m",
            "cyan": "\033[96m",
            "magenta": "\033[95m",
            "yellow": "\033[93m",
        }
        color_code = color_map.get(color.lower(), "")
        color_display = f"{color_code}{color[:12]:<12}\033[0m"
        
        line = f"│ {part_display} │ {color_display} │ {yield_val[:9]:<9} │ {region[:12]:<12} │ {metered[:12]:<12} │ {iot[:11]:<11} │ {chip[:11]:<11} │"
        print(line)
        print("└─────────────────┴──────────────┴───────────┴──────────────┴──────────────┴─────────────┴─────────────┘")
        
        # Additional details below
        print("\n📝 Additional Details:")
        details = [
            ("🖨️  Printer Model", item.get("printer_model", "N/A")),
            ("🔧 Type", item.get("consumable_type", "N/A")),
        ]
        
        for emoji, label in details:
            key = label.lower().replace(" ", "_").replace("️", "").replace("  ", " ").strip()
            if key == "printer_model":
                value = item.get("printer_model", "N/A")
            elif key == "type":
                value = item.get("consumable_type", "N/A")
            else:
                value = "N/A"
            
            if value and value != "N/A":
                print(f"  {emoji} {label}: {value}")
        
        print("─" * 120)


def add_item():
    """Add a new item interactively"""
    print("\n➕ Add New Consumable Item")
    print("=" * 40)

    item = {}
    item["part_number"] = input("Part Number: ").strip()
    item["color"] = input("Color/Drum: ").strip()
    item["printer_model"] = input("Printer Model: ").strip()
    item["consumable_type"] = input("Consumable Type (toner/drum): ").strip()
    item["yield"] = input("Yield (pages, optional): ").strip()
    item["region_zone"] = input("Region/Zone (optional): ").strip()
    item["metered_sold"] = input("Metered/Sold (optional): ").strip()
    item["iot_codename"] = input("IOT Codename (optional): ").strip()
    item["chip_type"] = input("Chip Type (optional): ").strip()

    data = load_data()
    data.append(item)
    if save_data(data):
        print(f"\n✅ Item '{item['part_number']}' added successfully!")
    else:
        print(f"\n❌ Failed to save item '{item['part_number']}'.")


def list_all():
    """List all items with pagination"""
    data = load_data()

    if not data:
        print("No items in database.")
        return

    print(f"\n📚 Total items: {len(data)}")
    print("=" * 80)

    # Group by model for better overview
    models = defaultdict(list)
    for item in data:
        model = item.get("printer_model", "Unknown")
        models[model].append(item)

    page_size = 5  # Show 5 models per page
    model_list = sorted(models.keys())
    total_pages = (len(model_list) + page_size - 1) // page_size

    for page in range(total_pages):
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_models = model_list[start_idx:end_idx]

        print(f"\n📄 Page {page + 1}/{total_pages}:")
        print("─" * 40)

        for model in page_models:
            items = models[model]
            toner_count = sum(1 for i in items if i.get("consumable_type", "").lower() == "toner")
            drum_count = sum(1 for i in items if i.get("consumable_type", "").lower() == "drum")
            
            print(f"\n🖨️  {model[:60]}...")
            print(f"   📦 Items: {len(items)} (🖨️ {toner_count} toner(s), ⚙️ {drum_count} drum(s))")
            
            # Show unique part numbers count
            unique_parts = len(set(i.get("part_number", "") for i in items))
            print(f"   🔢 Unique Parts: {unique_parts}")
            
            # Show color summary
            colors = set(i.get("color", "") for i in items if i.get("color"))
            if colors:
                print(f"   🎨 Colors: {', '.join(sorted(colors)[:3])}" + ("..." if len(colors) > 3 else ""))
        
        if page < total_pages - 1:
            input("\nPress Enter for next page...")


def import_from_text():
    """Import data from text format"""
    print("\n📥 Import from Text Format")
    print("=" * 40)
    print("Paste your data (Ctrl+D or Ctrl+Z to finish):")
    print(
        "Format: partnumber\\tcolor\\tprintermodel\\tconsumable_type\\tyield\\tregion/zone\\tm/s\\tiot-codename\\tchiptype"
    )
    print("-" * 40)

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    data = load_data()
    imported_count = 0

    for line in lines:
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) >= 3:  # At least part, color, model
            item = {
                "part_number": parts[0].strip(),
                "color": parts[1].strip(),
                "printer_model": parts[2].strip(),
                "consumable_type": parts[3].strip() if len(parts) > 3 else "",
                "yield": parts[4].strip() if len(parts) > 4 else "",
                "region_zone": parts[5].strip() if len(parts) > 5 else "",
                "metered_sold": parts[6].strip() if len(parts) > 6 else "",
                "iot_codename": parts[7].strip() if len(parts) > 7 else "",
                "chip_type": parts[8].strip() if len(parts) > 8 else "",
            }
            data.append(item)
            imported_count += 1

    if save_data(data):
        print(f"\n✅ Imported {imported_count} items successfully!")
    else:
        print(f"\n❌ Failed to save imported items.")


def export_to_json():
    """Export current database to JSON file"""
    data = load_data()
    if not data:
        print("No data to export.")
        return
    
    export_file = input("Enter export filename (default: xerox_export.json): ").strip()
    if not export_file:
        export_file = "xerox_export.json"
    
    if not export_file.endswith('.json'):
        export_file += '.json'
    
    try:
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Database exported to '{export_file}' successfully!")
        print(f"   Total items: {len(data)}")
    except Exception as e:
        print(f"❌ Error exporting data: {e}")


def show_menu():
    """Display main menu"""
    print("\n" + "=" * 50)
    print("🖨️  XEROX CONSUMABLES LIBRARY")
    print("=" * 50)
    print("1. 🔍 Search by Printer Model")
    print("2. 🔢 Search by Part Number")
    print("3. 🎨 Search by Color/Drum")
    print("4. 🔧 Search by IOT Codename")
    print("5. 🌍 Search by Region/Zone")
    print("6. 📊 Search by Yield Range")
    print("7. 🔧 Search by Consumable Type (toner/drum)")
    print("8. 📋 List All Items")
    print("9. ➕ Add New Item")
    print("10. 📥 Import from Text")
    print("11. 📤 Export to JSON")
    print("12. 📊 Show Statistics")
    print("0. 🚪 Exit")
    print("-" * 50)


def show_statistics():
    """Display database statistics"""
    data = load_data()

    if not data:
        print("Database is empty.")
        return

    # Count by color and consumable type
    colors = {}
    consumable_types = {}
    models = set()
    regions = set()
    yields = []
    chip_types = set()

    for item in data:
        color = item.get("color", "Unknown")
        colors[color] = colors.get(color, 0) + 1

        ctype = item.get("consumable_type", "Unknown")
        consumable_types[ctype] = consumable_types.get(ctype, 0) + 1

        models.add(item.get("printer_model", ""))
        if item.get("region_zone"):
            regions.add(item.get("region_zone"))
        if item.get("yield"):
            try:
                yield_val = int(str(item.get("yield")).replace(",", ""))
                yields.append(yield_val)
            except (ValueError, TypeError):
                pass
        if item.get("chip_type"):
            chip_types.add(item.get("chip_type"))

    print("\n📊 Database Statistics")
    print("=" * 40)
    print(f"Total Items: {len(data)}")
    print(f"Unique Printer Models: {len(models)}")
    print(f"Regions/Zones: {len(regions)}")
    print(f"Chip Types: {len(chip_types)}")

    if yields:
        print(f"\n📊 Yield Statistics:")
        print(f"  Average Yield: {sum(yields) // len(yields):,} pages")
        print(f"  Min Yield: {min(yields):,} pages")
        print(f"  Max Yield: {max(yields):,} pages")

    print("\n🎨 By Color/Drum Type:")
    for color, count in colors.items():
        print(f"  {color}: {count} items")

    print("\n🔧 By Consumable Type:")
    for ctype, count in consumable_types.items():
        print(f"  {ctype}: {count} items")
    
    if chip_types:
        print(f"\n💾 Chip Types:")
        for chip in sorted(chip_types):
            count = sum(1 for item in data if item.get("chip_type") == chip)
            print(f"  {chip}: {count} items")


def interactive_mode():
    """Run in interactive menu mode"""
    while True:
        show_menu()

        try:
            choice = input("\nSelect option (0-12): ").strip()

            if choice == "0":
                print("\n👋 Goodbye!")
                break
            elif choice == "1":
                query = input("Enter printer model to search: ").strip()
                results = search_data("model", query)
                display_results_clustered(results)
            elif choice == "2":
                query = input("Enter part number: ").strip()
                results = search_data("part", query)
                display_results_simple(results)
            elif choice == "3":
                query = input("Enter color/drum type: ").strip()
                results = search_data("color", query)
                display_results_clustered(results)
            elif choice == "4":
                query = input("Enter IOT codename: ").strip()
                results = search_data("iot", query)
                display_results_clustered(results)
            elif choice == "5":
                query = input("Enter region/zone: ").strip()
                results = search_data("region", query)
                display_results_clustered(results)
            elif choice == "6":
                print("\nYield search examples:")
                print("  - Range: 5000-10000")
                print("  - Greater than: >5000")
                print("  - Less than: <10000")
                print("  - Exact: 5000")
                query = input("Enter yield range: ").strip()
                results = search_data("yield", query)
                display_results_clustered(results)
            elif choice == "7":
                query = input("Enter consumable type (toner/drum): ").strip()
                results = search_data("consumable_type", query)
                display_results_clustered(results)
            elif choice == "8":
                list_all()
            elif choice == "9":
                add_item()
            elif choice == "10":
                import_from_text()
            elif choice == "11":
                export_to_json()
            elif choice == "12":
                show_statistics()
            else:
                print("❌ Invalid choice. Please try again.")

            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def command_line_mode():
    """Run in command-line argument mode"""
    parser = argparse.ArgumentParser(
        description="Xerox Consumables Library - Search and manage printer consumables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --search-model "Phaser 5500"
  %(prog)s --search-part "006R01452"
  %(prog)s --search-color "Cyan"
  %(prog)s --search-type "drum"
  %(prog)s --search-yield "5000-10000"
  %(prog)s --search-yield ">5000"
  %(prog)s --list-all
  %(prog)s --add-item
  %(prog)s --interactive
        """,
    )

    # Search arguments
    parser.add_argument("--search-model", help="Search by printer model")
    parser.add_argument("--search-part", help="Search by part number")
    parser.add_argument("--search-color", help="Search by color/drum type")
    parser.add_argument("--search-iot", help="Search by IOT codename")
    parser.add_argument("--search-region", help="Search by region/zone")
    parser.add_argument(
        "--search-yield", help="Search by yield range (e.g., 5000-10000, >5000, <10000)"
    )
    parser.add_argument("--search-type", help="Search by consumable type (toner/drum)")

    # Action arguments
    parser.add_argument("--list-all", action="store_true", help="List all items")
    parser.add_argument("--add-item", action="store_true", help="Add new item")
    parser.add_argument("--import-text", action="store_true", help="Import from text")
    parser.add_argument("--export-json", action="store_true", help="Export to JSON")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )

    args = parser.parse_args()

    # Check if any arguments provided
    if not any(vars(args).values()):
        parser.print_help()
        return

    # Execute commands
    if args.interactive:
        interactive_mode()
        return

    if args.search_model:
        results = search_data("model", args.search_model)
        display_results_clustered(results)

    if args.search_part:
        results = search_data("part", args.search_part)
        display_results_simple(results)

    if args.search_color:
        results = search_data("color", args.search_color)
        display_results_clustered(results)

    if args.search_iot:
        results = search_data("iot", args.search_iot)
        display_results_clustered(results)

    if args.search_region:
        results = search_data("region", args.search_region)
        display_results_clustered(results)

    if args.search_yield:
        results = search_data("yield", args.search_yield)
        display_results_clustered(results)

    if args.search_type:
        results = search_data("consumable_type", args.search_type)
        display_results_clustered(results)

    if args.list_all:
        list_all()

    if args.add_item:
        add_item()

    if args.import_text:
        import_from_text()

    if args.export_json:
        export_to_json()

    if args.stats:
        show_statistics()


def main():
    """Main function"""
    print("🖨️  Xerox Consumables Library")
    print("=" * 40)

    # Check if database exists
    if not Path(DATA_FILE).exists():
        print(f"⚠️  Database file '{DATA_FILE}' not found.")
        print("   The application will work with an empty database.")
        print("   You can add items manually or import from text format.")
        print("   To create a sample database, copy your JSON data to this file.\n")
    
    # Check if command-line arguments provided
    if len(sys.argv) > 1:
        command_line_mode()
    else:
        interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")