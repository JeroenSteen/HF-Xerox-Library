# HF-Xerox-Library

A command-line tool for searching and managing Xerox printer consumables database. Quickly find compatible toners, drums, and other supplies by model number, part number, color, yield, or other specifications.

## Features

- 🔍 Search consumables by printer model, part number, color, IOT codename, yield range, region, or consumable type
- 📊 View results clustered by printer model for easy comparison
- ➕ Add new items manually or import from text files
- 💾 Export data to JSON format
- 🖥️ Interactive menu mode or direct command-line usage

## Prerequisites

- Python 3.11.3 or higher
- No external dependencies required (uses standard library only)

## Installation

```bash
# Clone the repository
git clone https://github.com/JeroenSteen/HF-Xerox-Library.git
cd HF-Xerox-Library
```

## Quick Start

### Interactive Mode

Launch the interactive menu for guided navigation:

```bash
python hf-xerox-library.py
```

### Command-Line Mode

Search directly from the command line:

```bash
# Search by printer model
python hf-xerox-library.py --search-model "C60"

# Search by part number
python hf-xerox-library.py --search-part "006R01521"

# Search by color
python hf-xerox-library.py --search-color "Cyan"

# Search by consumable type
python hf-xerox-library.py --search-type "toner"

# Search by yield range
python hf-xerox-library.py --search-yield "20000-40000"

# Search by IOT codename
python hf-xerox-library.py --search-iot "Hera2cXC"

# Search by region
python hf-xerox-library.py --search-region "WW"
```

## Example Output

```
Searching for model: C60

Found 4 results:

Printer Model: DCP 550/560/570
  Part: 006R01521 | Black Toner | Yield: 30000 | Region: WW | IOT: Hera2cXC
  Part: 006R01522 | Cyan Toner | Yield: 30000 | Region: WW | IOT: Hera2cXC
  Part: 006R01523 | Magenta Toner | Yield: 30000 | Region: WW | IOT: Hera2cXC
  Part: 006R01524 | Yellow Toner | Yield: 30000 | Region: WW | IOT: Hera2cXC
```

## Data Format

The tool uses `xerox_data.json` located in the same directory as the script. Each consumable entry follows this structure:

```json
{
  "part_number": "006R01521",
  "color": "Black",
  "printer_model": "DCP 550/560/570",
  "consumable_type": "toner",
  "yield": "30000",
  "region_zone": "WW",
  "metered_sold": "metered",
  "iot_codename": "Hera2cXC",
  "chip_type": "HFD1"
}
```

### Field Descriptions

- **part_number**: Xerox part/SKU number
- **color**: Consumable color (Black, Cyan, Magenta, Yellow, etc.)
- **printer_model**: Compatible printer model(s)
- **consumable_type**: Type of consumable (toner, drum, etc.)
- **yield**: Page yield capacity
- **region_zone**: Geographic region/zone (WW = Worldwide)
- **metered_sold**: Pricing model (metered or sold)
- **iot_codename**: Internal IOT system codename
- **chip_type**: Chip technology type

## File Structure

```
HF-Xerox-Library/
├── hf-xerox-library.py    # Main script
├── xerox_data.json         # Consumables database
└── README.md               # This file
```

## Adding Data

### Manual Entry

Use the interactive menu to add individual items with guided prompts.

### Bulk Import

Import multiple items from a text file with tab or comma-separated values.

### Direct JSON Edit

Edit `xerox_data.json` directly, ensuring proper JSON formatting.

## Use Cases

- **Service Technicians**: Quickly identify correct consumables for printer models
- **Inventory Management**: Track and organize printer supply stock
- **Parts Lookup**: Find part numbers by printer model or specifications
- **Cross-Reference**: Match IOT codenames to physical products

## Contributing

Contributions are welcome! Please feel free to:

- Report bugs or issues
- Suggest new features
- Submit pull requests
- Add more consumable data

Please open an issue first to discuss major changes.

## License

This project is open source and available under the MIT License.

## Support

If you encounter any problems or have questions:

- Open an issue on GitHub
- Check existing issues for solutions

## Acknowledgments

Created for managing Xerox printer consumables in technical support and inventory management contexts.

---

**Note**: This tool is not affiliated with or endorsed by Xerox Corporation. All product names and part numbers are trademarks of their respective owners.