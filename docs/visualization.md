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

Charts are saved to the `charts/` directory in organized subfolders.

## Output Structure

```
charts/
├── global/           # World-level statistics
│   ├── total_population.png
│   ├── total_wealth.png
│   └── ...
├── market/           # Commodity market data
│   ├── prices_raw.png
│   ├── supply_industrial.png
│   └── ...
├── comparisons/      # Cross-country comparison charts
│   ├── comparison_treasury.png
│   ├── comparison_gdp_proxy.png
│   └── ...
└── countries/        # Per-country statistics
    ├── ENG/
    │   ├── treasury.png
    │   ├── population_total.png
    │   └── ...
    ├── FRA/
    └── ...
```

## Command Line Options

```bash
python plot_all.py [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--all` | Generate all charts (default if no options) |
| `--global` | Generate global statistics charts |
| `--market` | Generate world market charts |
| `--countries` | Generate individual country charts for ALL countries |
| `--comparisons` | Generate comparison charts only |
| `--country TAG` | Generate charts for specific country (e.g., `--country ENG`) |

### Examples

```bash
# Generate only global statistics charts
python plot_all.py --global

# Generate only market charts
python plot_all.py --market

# Generate charts for England only
python plot_all.py --country ENG

# Generate market and all country charts
python plot_all.py --market --countries

# Generate just comparison charts (no individual country charts)
python plot_all.py --comparisons
```

## Generated Charts

### Global Statistics (`charts/global/`)

| Chart | Description |
|-------|-------------|
| `total_population.png` | World population over time |
| `population_by_type.png` | Population stacked by POP type |
| `population_composition.png` | Population percentages by POP type |
| `pop_[type].png` | Individual POP type population (aristocrats, farmers, etc.) |
| `total_pop_money.png` | World POP cash holdings |
| `total_pop_bank_savings.png` | World POP bank savings |
| `total_wealth.png` | Total wealth (cash + savings stacked) |
| `avg_life_needs.png` | Average life needs satisfaction |
| `avg_everyday_needs.png` | Average everyday needs satisfaction |
| `avg_luxury_needs.png` | Average luxury needs satisfaction |
| `all_needs.png` | All three needs on one chart |
| `avg_literacy.png` | World average literacy rate |
| `avg_consciousness.png` | World average political consciousness |
| `avg_militancy.png` | World average militancy |
| `all_social.png` | All social indicators (normalized) |

### World Market (`charts/market/`)

#### Category Charts

For each category (raw, agricultural, industrial, consumer, military):

| Chart Pattern | Description |
|---------------|-------------|
| `prices_[category].png` | Prices for category commodities |
| `supply_[category].png` | Supply for category commodities |
| `sold_[category].png` | Sold quantities for category commodities |
| `balance_[category].png` | Supply/demand balance (surplus %) |
| `price_index_[category].png` | Price index (base year = 100) |

#### Individual Commodity Charts

For each commodity (~47 total):

| Chart Pattern | Description |
|---------------|-------------|
| `price_[commodity].png` | Price over time with trend line |
| `supply_[commodity].png` | Supply over time |
| `sold_[commodity].png` | Sold quantity over time |
| `full_[commodity].png` | 4-panel analysis (price, supply, sold, comparison) |

#### Summary Charts

| Chart | Description |
|-------|-------------|
| `category_comparison.png` | Composite price index for all categories |

### Country Comparisons (`charts/comparisons/`)

Compares major powers across all statistics:

| Chart | Description |
|-------|-------------|
| `comparison_treasury.png` | Treasury comparison |
| `comparison_prestige.png` | Prestige comparison |
| `comparison_infamy.png` | Infamy comparison |
| `comparison_total_tax_income.png` | Tax income comparison |
| `comparison_total_factory_count.png` | Factory count comparison |
| `comparison_total_factory_levels.png` | Factory levels comparison |
| `comparison_total_factory_income.png` | Factory income comparison |
| `comparison_total_factory_employment.png` | Factory employment comparison |
| `comparison_total_rgo_income.png` | RGO income comparison |
| `comparison_total_rgo_employment.png` | RGO employment comparison |
| `comparison_population_total.png` | Population comparison |
| `comparison_pop_money.png` | POP cash comparison |
| `comparison_pop_bank_savings.png` | POP savings comparison |
| `comparison_avg_life_needs.png` | Life needs comparison |
| `comparison_avg_everyday_needs.png` | Everyday needs comparison |
| `comparison_avg_luxury_needs.png` | Luxury needs comparison |
| `comparison_avg_literacy.png` | Literacy comparison |
| `comparison_avg_consciousness.png` | Consciousness comparison |
| `comparison_avg_militancy.png` | Militancy comparison |
| `comparison_gdp_proxy.png` | GDP proxy (factory + RGO income) |
| `comparison_gdp_per_capita.png` | GDP per capita |
| `comparison_industrialization.png` | Industrialization index |
| `comparison_pop_wealth.png` | Total POP wealth comparison |

### Individual Country Charts (`charts/countries/[TAG]/`)

For each country with data, generates:

| Chart | Description |
|-------|-------------|
| `treasury.png` | National treasury |
| `bank_reserves.png` | Bank reserves |
| `prestige.png` | Prestige score |
| `infamy.png` | Infamy (badboy) |
| `total_tax_income.png` | Total tax revenue |
| `total_factory_count.png` | Number of factories |
| `total_factory_levels.png` | Sum of factory levels |
| `total_factory_income.png` | Factory revenue |
| `total_factory_employment.png` | Factory workers |
| `total_rgo_income.png` | RGO revenue |
| `total_rgo_employment.png` | RGO workers |
| `population_total.png` | Total population |
| `pop_money.png` | POP cash holdings |
| `pop_bank_savings.png` | POP bank savings |
| `avg_life_needs.png` | Life needs satisfaction |
| `avg_everyday_needs.png` | Everyday needs satisfaction |
| `avg_luxury_needs.png` | Luxury needs satisfaction |
| `avg_literacy.png` | Literacy rate |
| `avg_consciousness.png` | Political consciousness |
| `avg_militancy.png` | Militancy |
| `gdp_proxy.png` | GDP proxy (factory + RGO income) |
| `total_pop_wealth.png` | Stacked cash + savings |
| `all_needs.png` | All needs on one chart |
| `industrialization_index.png` | Factories per million pop |
| `overview.png` | 6-panel economic overview |

## Countries Compared

By default, the following Great Powers are compared:

- **ENG** - United Kingdom
- **FRA** - France
- **GER** - Germany (merges PRU → NGF → GER data)
- **KUK** - Austria-Hungary (merges AUS → SGF → KUK data)
- **RUS** - Russia
- **USA** - United States
- **SPA** - Spain
- **TUR** - Ottoman Empire
- **CHI** - Qing China
- **JAP** - Japan

Note: Country tag succession is handled automatically. For example, using `GER` will show continuous data from Prussia (PRU) through North German Federation (NGF) to unified Germany (GER).

## Individual Scripts

You can also run individual visualization modules:

```bash
cd viz

# Global statistics only
..\venv\Scripts\python.exe plot_global.py

# Market data only
..\venv\Scripts\python.exe plot_market.py

# Country charts only
..\venv\Scripts\python.exe plot_countries.py
```

## Customization

### Adding Countries to Comparisons

Edit `viz/plot_countries.py` and modify the `GREAT_POWERS` list:

```python
GREAT_POWERS = ['ENG', 'FRA', 'GER', 'KUK', 'RUS', 'USA', 'JAP', 'ITA']
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
RAW_RESOURCES = ['coal', 'iron', 'sulphur', 'timber', ...]
AGRICULTURAL = ['grain', 'cattle', 'cotton', 'wool', ...]
INDUSTRIAL_GOODS = ['steel', 'cement', 'machine_parts', ...]
CONSUMER_GOODS = ['regular_clothes', 'luxury_clothes', ...]
MILITARY_GOODS = ['ammunition', 'small_arms', 'artillery', ...]
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
    load_country_group,
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

# Save to custom subfolder
save_chart('my_custom_chart', subdir='custom')
```

## Output Format

- **Format:** PNG
- **Resolution:** 150 DPI
- **Default size:** 12x6 inches (1800x900 pixels)
- **Multi-panel:** 18x10 inches for overview panels
- **Market category charts:** 14x7 inches

## Troubleshooting

### "No module named 'matplotlib'"

Install dependencies:
```bash
venv\Scripts\pip.exe install matplotlib numpy
```

### Charts look different on different systems

The scripts use the 'ggplot' style which should be consistent across platforms.

### Memory issues with large datasets

Generate chart categories separately to reduce memory usage:
```bash
python plot_all.py --global
python plot_all.py --market
python plot_all.py --comparisons
python plot_all.py --countries
```

### Too many charts generated

For a quick overview, generate only comparisons:
```bash
python plot_all.py --global --comparisons
```

Or generate charts for specific countries:
```bash
python plot_all.py --country ENG --country FRA
```
