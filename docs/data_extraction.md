# Economic Data Extraction Pipeline

This document describes how to extract economic statistics from Victoria 2 save files.

## Files

| File | Description |
|------|-------------|
| `parser.py` | Paradox save file format parser |
| `extractor.py` | Economic data extraction functions |
| `process_saves.py` | Main processing script |

## Usage

### Basic Usage

```bash
venv\Scripts\python.exe process_saves.py
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--limit N` | Process only first N files (useful for testing) |
| `--resume` | Resume from partial progress if interrupted |
| `--batch-size N` | Save progress every N files (default: 50) |

### Examples

```bash
# Process all save files
venv\Scripts\python.exe process_saves.py

# Test with first 10 files
venv\Scripts\python.exe process_saves.py --limit 10

# Resume interrupted processing
venv\Scripts\python.exe process_saves.py --resume

# Save progress more frequently
venv\Scripts\python.exe process_saves.py --batch-size 25
```

## Output Files

All output is written to the `output/` directory.

### Main Data Files

| File | Description |
|------|-------------|
| `economic_data.json` | Complete data for all dates (large file) |
| `global_statistics.json` | World population, money, needs satisfaction over time |
| `global_population_by_type.json` | POP type distribution over time |
| `world_market_prices.json` | Commodity prices over time |

### CSV Files (Spreadsheet-Friendly)

| File | Description |
|------|-------------|
| `global_summary.csv` | Global economic statistics over time |
| `major_countries_summary.csv` | Top 20 countries (by final population) over time |

### Per-Country Data

Individual country time series are stored in `output/countries/`:

```
output/countries/
├── ENG.json
├── FRA.json
├── USA.json
├── PRU.json
└── ... (one file per country)
```

## Data Extracted

### Per Country

| Statistic | Description |
|-----------|-------------|
| `treasury` | National treasury (money) |
| `bank_reserves` | National bank reserves |
| `bank_money_lent` | Money lent by national bank |
| `prestige` | Prestige score |
| `infamy` | Infamy (badboy) score |
| `tax_base` | Tax base value |
| `rich_tax_rate` | Rich strata tax rate (0-1) |
| `middle_tax_rate` | Middle strata tax rate (0-1) |
| `poor_tax_rate` | Poor strata tax rate (0-1) |
| `rich_tax_income` | Income from rich taxes |
| `middle_tax_income` | Income from middle taxes |
| `poor_tax_income` | Income from poor taxes |
| `total_tax_income` | Total tax income |
| `education_spending` | Education budget slider (0-1) |
| `military_spending` | Military budget slider (0-1) |
| `social_spending` | Social budget slider (0-1) |
| `total_factory_count` | Number of factories |
| `total_factory_levels` | Sum of all factory levels |
| `total_factory_income` | Total factory revenue |
| `total_factory_employment` | Workers employed in factories |
| `total_rgo_income` | Total RGO revenue |
| `total_rgo_employment` | Workers employed in RGOs |

### Per Country - Population Data

| Statistic | Description |
|-----------|-------------|
| `population.total` | Total population |
| `population.by_type` | Population count per POP type |
| `population.total_money` | Total cash held by POPs |
| `population.total_bank_savings` | Total bank savings of POPs |
| `population.money_by_type` | Cash held per POP type |
| `population.avg_life_needs` | Average life needs satisfaction (0-1) |
| `population.avg_everyday_needs` | Average everyday needs satisfaction (0-1) |
| `population.avg_luxury_needs` | Average luxury needs satisfaction (0-1) |
| `population.avg_literacy` | Average literacy rate (0-1) |
| `population.avg_consciousness` | Average consciousness (0-10) |
| `population.avg_militancy` | Average militancy (0-10) |

### Global Statistics

| Statistic | Description |
|-----------|-------------|
| `total_population` | World population |
| `population_by_type` | World population per POP type |
| `total_pop_money` | Total cash held by all POPs |
| `total_pop_bank_savings` | Total bank savings worldwide |
| `money_by_pop_type` | Cash per POP type worldwide |
| `avg_life_needs` | World average life needs satisfaction |
| `avg_everyday_needs` | World average everyday needs satisfaction |
| `avg_luxury_needs` | World average luxury needs satisfaction |
| `avg_literacy` | World average literacy |
| `avg_consciousness` | World average consciousness |
| `avg_militancy` | World average militancy |
| `total_employed_craftsmen` | Factory workers employed worldwide |
| `total_employed_labourers` | RGO workers employed worldwide |

### World Market

| Statistic | Description |
|-----------|-------------|
| `prices` | Current price per commodity |
| `supply` | Supply per commodity |
| `actual_sold` | Quantity sold per commodity |

## Performance

- Processing time: ~5 seconds per save file
- For 1201 save files: approximately **1.5 hours**
- Progress is saved every 50 files (configurable with `--batch-size`)
- Processing can be safely interrupted and resumed with `--resume`

## Output Format Examples

### global_statistics.json

```json
[
  {
    "date": "1836.1.1",
    "total_population": 245500909,
    "total_pop_money": 136204662.59,
    "total_pop_bank_savings": 25791.19,
    "avg_life_needs": 0.362,
    "avg_everyday_needs": 0.321,
    "avg_luxury_needs": 0.171,
    "avg_literacy": 0.141,
    "avg_consciousness": 0.878,
    "avg_militancy": 0.019
  },
  ...
]
```

### countries/ENG.json

```json
[
  {
    "date": "1836.1.1",
    "treasury": 20349.41,
    "bank_reserves": 240.0,
    "prestige": 100.052,
    "infamy": 0.0,
    "total_tax_income": 3668091.59,
    "total_factory_count": 15,
    "total_factory_levels": 16,
    "total_factory_income": 809332.0,
    "total_factory_employment": 95444,
    "total_rgo_income": 6235330.11,
    "total_rgo_employment": 26245143,
    "population_total": 31962786,
    "pop_money": 20010547.57,
    "pop_bank_savings": 1224.9,
    "avg_life_needs": 0.057,
    "avg_everyday_needs": 0.469,
    "avg_literacy": 0.169
  },
  ...
]
```

### global_summary.csv

```csv
date,total_population,total_pop_money,total_pop_bank_savings,avg_life_needs,avg_everyday_needs,avg_luxury_needs,avg_literacy,avg_consciousness,avg_militancy
1836.1.1,245500909,136204662.59,25791.19,0.362,0.321,0.171,0.141,0.878,0.019
1836.2.1,245565929,91708756.12,217275.26,0.370,0.296,0.076,0.141,0.875,0.026
...
```
