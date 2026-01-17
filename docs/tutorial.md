# Victoria 2 Economy Analysis Tool - Tutorial

This comprehensive tutorial explains how to use the Victoria 2 Economy Analysis Tool
to extract, process, and visualize economic data from your game saves.

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Understanding Victoria 2 Saves](#understanding-victoria-2-saves)
4. [Step-by-Step Workflow](#step-by-step-workflow)
5. [Data Processing Pipeline](#data-processing-pipeline)
6. [Economic Concepts](#economic-concepts)
7. [Visualization Guide](#visualization-guide)
8. [Extending the Tool](#extending-the-tool)
9. [Troubleshooting](#troubleshooting)

---

## Introduction

### What This Tool Does

This tool transforms Victoria 2 save files into analyzable economic data:

```
Victoria 2 Game
      │
      └──> autosave.v2 (Paradox script format)
              │
              └──> Parser (parser.py)
                      │
                      └──> Extractor (extractor.py)
                              │
                              └──> JSON/CSV Data (output/)
                                      │
                                      └──> Visualizations (charts/)
```

### Educational Value

This codebase demonstrates several important software engineering concepts:

1. **Recursive Descent Parsing**: The parser implements a classic parsing technique
   for handling nested data structures
2. **Data Extraction with Dataclasses**: Type-safe data structures for economic data
3. **Batch Processing**: Efficient handling of multiple large files
4. **Data Visualization**: Time series charts with matplotlib
5. **File System Monitoring**: Real-time file watching with watchdog

---

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install watchdog matplotlib numpy
```

### Three-Step Process

```bash
# Step 1: Collect saves while playing
python save_watcher.py
# (Play Victoria 2 with autosave enabled)

# Step 2: Process collected saves
python process_saves.py

# Step 3: Generate visualizations
cd viz
python plot_all.py
```

---

## Understanding Victoria 2 Saves

### Save File Format

Victoria 2 uses the Paradox script format - a hierarchical text format:

```
date="1836.1.1"
player="ENG"

worldmarket={
    price_pool={
        iron=35.000
        coal=2.300
        grain=2.500
    }
    supply_pool={
        iron=1000.500
        coal=5000.000
    }
}

ENG={
    money=50000.00
    prestige=100.5
    state={
        provinces={ 300 301 302 }
        state_buildings={
            building="steel_factory"
            level=2
        }
    }
}
```

### Key Characteristics

| Feature | Description |
|---------|-------------|
| Encoding | Latin-1 (ISO-8859-1) |
| Format | Key-value pairs with nested blocks |
| Block delimiters | Curly braces `{ }` |
| Value types | Strings, integers, floats, booleans (yes/no) |
| Comments | Lines starting with `#` |

### Data Structure

```
Save File
├── Header (date, player)
├── worldmarket (global prices/supply)
├── Provinces (1-3000+)
│   ├── name, owner, controller
│   ├── rgo (resource gathering)
│   └── POPs (population units)
└── Countries (ENG, FRA, PRU, etc.)
    ├── Treasury, prestige, infamy
    ├── Taxation rates and income
    └── States and factories
```

---

## Step-by-Step Workflow

### Step 1: Collecting Save Data

**Start the watcher before playing:**

```bash
python save_watcher.py
```

**What happens:**
1. Watcher monitors Victoria 2's save game folder
2. When autosave.v2 is updated, it's copied to `saves/`
3. Filename is based on in-game date (e.g., `1836.1.1.txt`)

**In-game setup:**
- Settings → Autosave: Monthly (recommended)
- This creates ~1200 data points for a full game

**Stop the watcher:**
- Press Ctrl+C when done playing

### Step 2: Processing Saves

**Process all collected saves:**

```bash
python process_saves.py
```

**Command-line options:**

```bash
# Process first 10 files only (for testing)
python process_saves.py --limit 10

# Resume interrupted processing
python process_saves.py --resume

# Save progress every 25 files
python process_saves.py --batch-size 25
```

**Output files generated:**

| File | Description |
|------|-------------|
| `economic_data.json` | Complete dataset (large!) |
| `global_statistics.json` | World aggregates |
| `global_population_by_type.json` | Population by POP type |
| `world_market_prices.json` | Commodity prices |
| `world_market_supply.json` | Commodity supply |
| `world_market_sold.json` | Quantities traded |
| `countries/*.json` | Per-country time series |
| `global_summary.csv` | World stats (spreadsheet) |
| `major_countries_summary.csv` | Top 20 countries |

### Step 3: Generating Charts

**Generate all charts:**

```bash
cd viz
python plot_all.py
```

**Generate specific categories:**

```bash
# World-level statistics
python plot_all.py --global

# Commodity market charts
python plot_all.py --market

# Country comparison charts
python plot_all.py --comparisons

# All country charts
python plot_all.py --countries

# Single country
python plot_all.py --country ENG
```

---

## Data Processing Pipeline

### Parsing Stage (parser.py)

The parser uses recursive descent to handle nested structures:

```python
# Main entry point
data = parse_save_file("autosave.v2")

# Fast extraction for specific sections
market_data = fast_extract_sections("save.v2", ["worldmarket"])

# Memory-efficient iteration
for tag, country_data in iterate_country_sections("save.v2"):
    print(f"{tag}: {country_data.get('prestige', 0)}")
```

**Key parsing concepts:**

1. **Tokenization**: Characters are consumed one at a time
2. **Lookahead**: Peek at next character without consuming
3. **Recursive blocks**: Blocks can contain other blocks
4. **Duplicate key handling**: Multiple same-named keys become lists

### Extraction Stage (extractor.py)

Data is extracted into typed dataclasses:

```python
@dataclass
class CountryData:
    tag: str                      # e.g., "ENG"
    treasury: float               # Government cash
    prestige: float               # National standing
    pop_data: PopData            # Population statistics
    states: list[StateData]      # Administrative regions
    # ... more fields
```

**POP Types (Population Units):**

| Type | Role | Economic Function |
|------|------|-------------------|
| aristocrats | Landowners | Receive RGO profits |
| capitalists | Factory owners | Invest in industry |
| artisans | Independent craftsmen | Produce goods |
| clerks | White-collar | Factory employment |
| craftsmen | Blue-collar | Factory employment |
| farmers | Agricultural | Work in farming RGOs |
| labourers | Manual | Work in mining RGOs |
| bureaucrats | Government | Administration |
| clergymen | Religious | Education, stability |
| officers | Military | Lead armies |
| soldiers | Military | Form armies |
| slaves | Unfree labor | (In slave states) |

### Processing Stage (process_saves.py)

Multiple save files are processed into time series:

```python
# Process a single save
result = process_single_save("saves/1836.1.1.txt")

# Result structure:
{
    'date': '1836.1.1',
    'world_market': {
        'prices': {'iron': 35.0, 'coal': 2.3, ...},
        'supply': {'iron': 1000.0, ...},
        'actual_sold': {'iron': 950.0, ...}
    },
    'global_statistics': {
        'total_population': 250000000,
        'avg_literacy': 0.15,
        ...
    },
    'countries': {
        'ENG': {'treasury': 50000, 'prestige': 100, ...},
        'FRA': {...},
        ...
    }
}
```

---

## Economic Concepts

### World Market

Victoria 2 simulates a global commodity market:

- **Supply**: Total production from all countries
- **Demand**: Total consumption needs
- **Price**: Fluctuates based on supply/demand
- **Actual Sold**: What was actually traded (min of supply/demand)

**Commodity Categories:**

| Category | Examples | Producers |
|----------|----------|-----------|
| Raw Resources | coal, iron, oil | RGOs |
| Agricultural | grain, cotton, cattle | Farming RGOs |
| Industrial | steel, cement, machine_parts | Factories |
| Consumer | clothes, furniture, wine | Factories |
| Military | ammunition, small_arms | Factories |

### Population Economics

**Needs System:**

POPs have three tiers of needs:

1. **Life Needs** (0.0-1.0): Food, fuel, basic clothing
   - Below 0.5 causes population decline
   - Critical for survival

2. **Everyday Needs** (0.0-1.0): Services, furniture
   - Affects happiness and productivity
   - Middle-class aspiration

3. **Luxury Needs** (0.0-1.0): Luxury goods
   - Upper/middle class focus
   - Status indicator

**Wealth Distribution:**

- **Cash**: Liquid money for purchases
- **Bank Savings**: Deposits earning interest
- Total Wealth = Cash + Bank Savings

### Industrialization

**Factory System:**

- Factories transform input goods into output goods
- Employment: Craftsmen (production) + Clerks (efficiency)
- Profitability tracked via `unprofitable_days`
- Can be subsidized by government

**Metrics:**

| Metric | Formula | Meaning |
|--------|---------|---------|
| Factory Count | Sum of factories | Industrialization level |
| Factory Levels | Sum of all levels | Production capacity |
| Factory Employment | Craftsmen + Clerks | Industrial workforce |
| GDP Proxy | Factory + RGO Income | Economic output |
| Industrialization Index | Factories / Pop × 1M | Intensity |

### Social Indicators

| Indicator | Range | Meaning |
|-----------|-------|---------|
| Literacy | 0-1 | Education level |
| Consciousness | 0-10 | Political awareness |
| Militancy | 0-10 | Revolutionary tendency |

**Threshold Effects:**

- Militancy > 5: Revolt risk increases
- Militancy > 7: Revolts highly likely
- Consciousness > 5: Strong reform demands

---

## Visualization Guide

### Chart Types

**1. Time Series (Line Charts)**

Most charts show metrics over time with filled area:

```
┌────────────────────────────────┐
│        World Population        │
│                           /""""│
│                      /"""""    │
│                 /""""          │
│            /""""               │
│       /""""                    │
│  /""""                         │
└────────────────────────────────┘
 1836        1880        1920
```

**2. Stacked Area Charts**

Show composition over time (e.g., population by type):

```
┌────────────────────────────────┐
│ ████████████ soldiers          │
│ ░░░░░░░░░░░░ craftsmen         │
│ ▓▓▓▓▓▓▓▓▓▓▓▓ farmers           │
└────────────────────────────────┘
```

**3. Comparison Charts**

Multiple countries on same chart:

```
┌────────────────────────────────┐
│  ─── ENG (red)                 │
│  ─── FRA (blue)                │
│  ─── GER (black)               │
└────────────────────────────────┘
```

**4. Multi-Panel Overview**

6-panel summary for each country:

```
┌──────────┬──────────┬──────────┐
│ Treasury │ Prestige │Population│
├──────────┼──────────┼──────────┤
│ Factories│   GDP    │ Literacy │
└──────────┴──────────┴──────────┘
```

### Chart Categories

**Global Charts (charts/global/):**
- Population trends
- Wealth accumulation
- Welfare indicators
- Social metrics

**Market Charts (charts/market/):**
- Price trends by category
- Supply analysis
- Demand analysis
- Price indices

**Comparison Charts (charts/comparisons/):**
- Great powers side-by-side
- GDP comparison
- Industrialization race

**Country Charts (charts/countries/TAG/):**
- Individual country profiles
- All economic metrics
- Historical overview

### Reading the Charts

**Understanding Trends:**

```
Rising Sharply:  Rapid growth
Rising Slowly:   Steady progress
Flat:            Stagnation
Declining:       Problems!
Volatile:        Instability
```

**Key Patterns to Watch:**

1. **Industrial Takeoff**: Factory count accelerating
2. **Economic Crisis**: Falling life needs satisfaction
3. **Revolutionary Pressure**: Rising militancy
4. **Modernization**: Rising literacy with stable militancy

---

## Extending the Tool

### Adding New Metrics

**1. Add to extractor.py:**

```python
@dataclass
class CountryData:
    # Add new field
    naval_spending: float = 0.0

def extract_country_data(tag, country_block, provinces):
    # ... existing code ...

    # Extract new metric
    naval = country_block.get('naval_spending', {})
    if isinstance(naval, dict):
        country.naval_spending = safe_float(naval.get('settings', 0.0))
```

**2. Add to process_saves.py:**

```python
# In process_single_save()
result['countries'][tag] = {
    # ... existing fields ...
    'naval_spending': country.naval_spending,
}
```

**3. Add visualization in viz/plot_countries.py:**

```python
COUNTRY_STATS = {
    # ... existing stats ...
    'naval_spending': {
        'title': 'Naval Spending',
        'ylabel': 'Slider (0-1)',
        'color': '#1E90FF',
        'ylim': (0, 1),
        'category': 'military'
    },
}
```

### Adding New Charts

**Create a new chart function:**

```python
def plot_custom_analysis():
    """Custom analysis chart."""
    setup_style()

    # Load data
    data = load_json('global_statistics.json')

    # Process data
    dates = [parse_date(d['date']) for d in data]
    values = [d['your_metric'] for d in data]

    # Create plot
    fig, ax = plt.subplots()
    ax.plot(dates, values, color='#2E86AB', linewidth=2)

    # Format and save
    ax.set_title('Custom Analysis')
    format_date_axis(ax, dates)
    save_chart('custom_analysis', subdir='custom')
```

### Working with the Data

**Loading data programmatically:**

```python
from viz.utils import load_json, load_country_group

# Load global data
global_stats = load_json('global_statistics.json')

# Load country data (with succession handling)
germany = load_country_group('GER')  # Includes PRU, NGF, GER

# Access specific dates
for entry in germany:
    print(f"{entry['date']}: Treasury = {entry['treasury']}")
```

---

## Troubleshooting

### Common Issues

**"No save files found"**

```
Problem: saves/ directory is empty
Solution:
1. Run save_watcher.py first
2. Play Victoria 2 with autosave enabled
3. Check saves are being copied
```

**"Encoding error when parsing"**

```
Problem: File not using Latin-1 encoding
Solution: The parser uses latin-1 by default
Check: Ensure you're loading V2 saves, not EU4/HOI4
```

**"Memory error during processing"**

```
Problem: Large save files using too much RAM
Solutions:
1. Use --limit to process fewer files
2. Use iterate_country_sections() for streaming
3. Process in smaller batches
```

**"Charts directory empty"**

```
Problem: Visualization not finding data
Solutions:
1. Run process_saves.py first
2. Check output/ contains JSON files
3. Ensure you're in viz/ directory
```

### Performance Tips

1. **For many saves**: Use `--batch-size` to save progress
2. **For specific data**: Use `fast_extract_sections()` instead of full parse
3. **For memory**: Use generator functions like `iterate_country_sections()`
4. **For speed**: Process only needed countries/dates

---

## Appendix: File Reference

### Input/Output Paths

| Path | Purpose |
|------|---------|
| `saves/` | Collected save files |
| `output/` | Processed JSON/CSV data |
| `charts/` | Generated PNG visualizations |
| `docs/` | Documentation |

### Key Functions

| Module | Function | Purpose |
|--------|----------|---------|
| parser.py | `parse_save_file()` | Full file parsing |
| parser.py | `fast_extract_sections()` | Partial extraction |
| parser.py | `iterate_country_sections()` | Stream countries |
| extractor.py | `extract_world_market()` | Get market data |
| extractor.py | `extract_country_data()` | Get country data |
| process_saves.py | `process_single_save()` | Process one file |
| viz/utils.py | `load_country_group()` | Load with succession |
| viz/plot_all.py | `main()` | Generate all charts |

---

## Conclusion

This tool provides a complete pipeline for analyzing Victoria 2's economic simulation:

1. **Collection**: Automatic save capture during gameplay
2. **Processing**: Structured data extraction
3. **Visualization**: Comprehensive charting

The modular design allows easy extension for custom analyses while the
comprehensive documentation supports learning and modification.

Happy analyzing!
