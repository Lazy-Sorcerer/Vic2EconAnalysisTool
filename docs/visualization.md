# Visualization Scripts

This document describes how to generate charts from the extracted Victoria 2 economic data.

## Setup

Install dependencies:

```bash
venv\Scripts\pip.exe install -r requirements.txt
```

## Quick Start

Generate all charts:

```bash
cd viz
..\venv\Scripts\python.exe plot_all.py --all
```

Charts are saved to the `charts/` directory.

## Command Line Options

```bash
python plot_all.py [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--all` | Generate all charts (default if no options) |
| `--global` | Generate global statistics charts |
| `--market` | Generate world market charts |
| `--countries` | Generate country comparison charts |
| `--country TAG` | Generate profile for specific country (e.g., `--country ENG`) |

### Examples

```bash
# Generate only global statistics charts
python plot_all.py --global

# Generate only market charts
python plot_all.py --market

# Generate profile for France
python plot_all.py --country FRA

# Generate market and country charts
python plot_all.py --market --countries
```

## Generated Charts

### Global Statistics (`--global`)

| Chart | Description |
|-------|-------------|
| `global_population.png` | World population over time |
| `global_wealth.png` | Total world wealth (cash + bank savings) |
| `global_needs_satisfaction.png` | Average life/everyday/luxury needs |
| `global_social_indicators.png` | Literacy, consciousness, militancy |
| `global_population_by_type.png` | Population stacked by POP type |
| `global_population_composition.png` | Population percentages by POP type |

### World Market (`--market`)

| Chart | Description |
|-------|-------------|
| `market_raw_resources.png` | Raw resource prices (coal, iron, grain, etc.) |
| `market_industrial.png` | Industrial goods prices (steel, cement, etc.) |
| `market_consumer.png` | Consumer goods prices (clothes, furniture, etc.) |
| `market_military.png` | Military goods prices (ammunition, artillery, etc.) |
| `market_luxury.png` | Luxury resource prices (silk, tea, coffee, etc.) |
| `market_price_indices.png` | Composite price indices by category |
| `market_volatility.png` | Price volatility (12-month rolling) |
| `market_[commodity].png` | Individual commodity charts (coal, iron, steel, grain, cotton) |

### Country Comparisons (`--countries`)

| Chart | Description |
|-------|-------------|
| `country_treasury.png` | National treasury comparison |
| `country_prestige.png` | Prestige score comparison |
| `country_factories.png` | Factory count comparison |
| `country_factory_income.png` | Factory income comparison |
| `country_population.png` | Population comparison |
| `country_literacy.png` | Literacy rate comparison |
| `country_industrialization_index.png` | Factories per million population |
| `country_gdp_proxy.png` | GDP proxy (factory + RGO income) |
| `country_gdp_per_capita.png` | GDP per capita proxy |
| `country_tax_income.png` | Total tax income comparison |
| `country_profile_[TAG].png` | Multi-panel country profiles |

## Countries Compared

By default, the following Great Powers are compared:

- **ENG** - United Kingdom
- **FRA** - France
- **PRU** - Prussia
- **AUS** - Austria
- **RUS** - Russia
- **USA** - United States

## Individual Scripts

You can also run individual visualization modules:

```bash
cd viz

# Global statistics only
..\venv\Scripts\python.exe plot_global.py

# Market data only
..\venv\Scripts\python.exe plot_market.py

# Country comparisons only
..\venv\Scripts\python.exe plot_countries.py
```

## Customization

### Adding Countries to Comparisons

Edit `viz/plot_countries.py` and modify the `GREAT_POWERS` list:

```python
GREAT_POWERS = ['ENG', 'FRA', 'PRU', 'AUS', 'RUS', 'USA', 'JAP', 'ITA']
```

### Custom Country Colors

Edit `viz/utils.py` and add to `COUNTRY_COLORS`:

```python
COUNTRY_COLORS = {
    'ENG': '#C8102E',
    'FRA': '#0055A4',
    # Add more...
    'BRA': '#009739',
}
```

### Custom Commodity Groups

Edit `viz/plot_market.py` and modify the commodity lists:

```python
RAW_RESOURCES = ['coal', 'iron', 'timber', 'cotton', 'wool', 'grain', 'cattle']
INDUSTRIAL_GOODS = ['steel', 'cement', 'machine_parts', ...]
```

## Creating Custom Charts

Use the utility functions in `viz/utils.py`:

```python
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from utils import (
    load_json,
    load_country,
    parse_date,
    setup_style,
    format_date_axis,
    format_large_numbers,
    save_chart,
)

# Setup
setup_style()

# Load data
data = load_json('global_statistics.json')
dates = [parse_date(d['date']) for d in data]
values = [d['total_population'] for d in data]

# Create chart
fig, ax = plt.subplots()
ax.plot(dates, values)
ax.set_title('My Custom Chart')

format_date_axis(ax, dates)
format_large_numbers(ax)

save_chart('my_custom_chart')
```

## Output Format

- **Format:** PNG
- **Resolution:** 150 DPI
- **Default size:** 12x6 inches (1800x900 pixels)
- **Multi-panel:** 18x10 inches for country profiles

## Troubleshooting

### "No module named 'matplotlib'"

Install dependencies:
```bash
venv\Scripts\pip.exe install matplotlib numpy
```

### Charts look different on different systems

The scripts use the 'ggplot' style which should be consistent across platforms.

### Memory issues with large datasets

The visualization scripts load data as needed. If memory is an issue, generate chart categories separately:
```bash
python plot_all.py --global
python plot_all.py --market
python plot_all.py --countries
```
