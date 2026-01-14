# Victoria 2 Economic Dataset Summary

This document describes the statistics available in the extracted dataset. Data is captured monthly across the entire game timeline (1836-1936).

## Dataset Structure

```
output/
├── economic_data.json          # Complete dataset (all data in one file)
├── global_statistics.json      # World-level aggregates
├── global_population_by_type.json
├── world_market_prices.json
├── global_summary.csv          # Spreadsheet format
├── major_countries_summary.csv
└── countries/                  # Per-country time series
    ├── ENG.json
    ├── FRA.json
    └── ...
```

---

## Global Statistics

World-level aggregates computed across all countries.

### Population

| Statistic | Description | Unit |
|-----------|-------------|------|
| `total_population` | Total world population | People |
| `population_by_type` | Population breakdown by POP type | People per type |

### Wealth

| Statistic | Description | Unit |
|-----------|-------------|------|
| `total_pop_money` | Total cash held by all POPs worldwide | £ (currency) |
| `total_pop_bank_savings` | Total bank savings of all POPs | £ |
| `money_by_pop_type` | Cash holdings broken down by POP type | £ per type |

### Welfare Indicators

| Statistic | Description | Range |
|-----------|-------------|-------|
| `avg_life_needs` | World average life needs satisfaction | 0-1 (1 = fully satisfied) |
| `avg_everyday_needs` | World average everyday needs satisfaction | 0-1 |
| `avg_luxury_needs` | World average luxury needs satisfaction | 0-1 |

### Social Indicators

| Statistic | Description | Range |
|-----------|-------------|-------|
| `avg_literacy` | World average literacy rate | 0-1 (1 = 100% literate) |
| `avg_consciousness` | World average political consciousness | 0-10 |
| `avg_militancy` | World average militancy | 0-10 |

### Employment

| Statistic | Description | Unit |
|-----------|-------------|------|
| `total_employed_craftsmen` | Factory workers employed worldwide | People |
| `total_employed_labourers` | RGO workers employed worldwide | People |

---

## World Market

Global commodity market data.

### Price Data

| Statistic | Description | Unit |
|-----------|-------------|------|
| `prices` | Current market price per commodity | £ per unit |

### Market Activity

| Statistic | Description | Unit |
|-----------|-------------|------|
| `supply` | Total supply available per commodity | Units |
| `actual_sold` | Quantity actually sold per commodity | Units |

### Tracked Commodities

**Raw Resources:**
- `coal`, `iron`, `sulphur`, `timber`, `tropical_wood`
- `cotton`, `wool`, `silk`, `dye`
- `grain`, `cattle`, `fish`, `fruit`, `tobacco`
- `tea`, `coffee`, `opium`
- `precious_metal`, `oil`, `rubber`

**Industrial Goods:**
- `steel`, `cement`, `glass`, `fertilizer`, `explosives`
- `machine_parts`, `electric_gear`, `fuel`
- `fabric`, `lumber`, `paper`

**Consumer Goods:**
- `regular_clothes`, `luxury_clothes`
- `furniture`, `luxury_furniture`
- `wine`, `liquor`

**Military Goods:**
- `ammunition`, `small_arms`, `artillery`
- `canned_food`, `barrels`
- `clipper_convoy`, `steamer_convoy`
- `aeroplanes`, `automobiles`, `telephones`, `radio`

---

## Country Statistics

Per-country data available for all nations.

### National Finances

| Statistic | Description | Unit |
|-----------|-------------|------|
| `treasury` | National treasury balance | £ |
| `bank_reserves` | National bank cash reserves | £ |
| `bank_money_lent` | Money lent out by national bank | £ |

### National Standing

| Statistic | Description | Unit/Range |
|-----------|-------------|------------|
| `prestige` | Prestige score | Points |
| `infamy` | Infamy (badboy) score | 0-25+ |
| `tax_base` | Tax base value | £ |
| `civilized` | Civilized status | Boolean |

### Taxation

| Statistic | Description | Unit/Range |
|-----------|-------------|------------|
| `rich_tax_rate` | Tax rate on upper class | 0-1 |
| `middle_tax_rate` | Tax rate on middle class | 0-1 |
| `poor_tax_rate` | Tax rate on lower class | 0-1 |
| `rich_tax_income` | Revenue from rich taxes | £ |
| `middle_tax_income` | Revenue from middle taxes | £ |
| `poor_tax_income` | Revenue from poor taxes | £ |
| `total_tax_income` | Total tax revenue | £ |

### Government Spending

| Statistic | Description | Range |
|-----------|-------------|-------|
| `education_spending` | Education budget slider | 0-1 |
| `military_spending` | Military budget slider | 0-1 |
| `social_spending` | Social/welfare budget slider | 0-1 |

### Industrial Sector

| Statistic | Description | Unit |
|-----------|-------------|------|
| `total_factory_count` | Number of factories | Count |
| `total_factory_levels` | Sum of all factory levels | Levels |
| `total_factory_income` | Total factory revenue | £ |
| `total_factory_employment` | Workers in factories | People |

### Primary Sector (RGO)

| Statistic | Description | Unit |
|-----------|-------------|------|
| `total_rgo_income` | Total RGO revenue | £ |
| `total_rgo_employment` | Workers in RGOs | People |

---

## Country Population Statistics

Detailed population data per country.

### Demographics

| Statistic | Description | Unit |
|-----------|-------------|------|
| `population.total` | Total country population | People |
| `population.by_type` | Population per POP type | People |

### POP Types Tracked

| Type | Description |
|------|-------------|
| `aristocrats` | Landowners, receive RGO dividends |
| `artisans` | Independent craftsmen |
| `bureaucrats` | Government administrators |
| `capitalists` | Factory owners, investors |
| `clergymen` | Religious figures |
| `clerks` | White-collar factory workers |
| `craftsmen` | Blue-collar factory workers |
| `farmers` | Agricultural RGO workers |
| `labourers` | Mining/extraction RGO workers |
| `officers` | Military officers |
| `soldiers` | Military enlisted |
| `slaves` | Enslaved workers |

### Wealth Distribution

| Statistic | Description | Unit |
|-----------|-------------|------|
| `population.total_money` | Total cash held by POPs | £ |
| `population.total_bank_savings` | Total POP bank savings | £ |
| `population.money_by_type` | Cash per POP type | £ |

### Welfare

| Statistic | Description | Range |
|-----------|-------------|-------|
| `population.avg_life_needs` | Average life needs satisfaction | 0-1 |
| `population.avg_everyday_needs` | Average everyday needs satisfaction | 0-1 |
| `population.avg_luxury_needs` | Average luxury needs satisfaction | 0-1 |

### Social Metrics

| Statistic | Description | Range |
|-----------|-------------|-------|
| `population.avg_literacy` | Average literacy rate | 0-1 |
| `population.avg_consciousness` | Average political consciousness | 0-10 |
| `population.avg_militancy` | Average militancy | 0-10 |

---

## Data Dimensions

### Temporal Coverage

- **Start Date:** 1836.1.1
- **End Date:** 1936.1.1 (typical)
- **Frequency:** Monthly (1st of each month)
- **Data Points:** ~1200 snapshots per statistic

### Geographic Coverage

- **Countries:** ~270 nations tracked
- **Coverage:** All existing and formable nations

---

## Potential Analysis Use Cases

### Economic Analysis
- GDP proxies (factory income + RGO income + artisan production)
- Industrialization rates (factory count/levels over time)
- Wealth distribution (money by POP type)
- Trade balance indicators (supply vs sold)

### Social Analysis
- Living standards (needs satisfaction trends)
- Literacy campaigns (literacy rate changes)
- Political stability (consciousness + militancy)
- Urbanization (craftsmen vs farmers ratio)

### Comparative Analysis
- Country rankings over time
- Convergence/divergence patterns
- Colonial vs metropole economics

### Market Analysis
- Price volatility per commodity
- Supply/demand dynamics
- Market integration indicators

---

## File Formats

### JSON Files
- Full precision numeric values
- Nested structures for complex data
- Best for programmatic analysis

### CSV Files
- Flattened structure
- Compatible with spreadsheet software
- Best for quick visualization

---

## Notes

- All monetary values are in the game's currency unit (£)
- Population counts represent individual people
- Averages are population-weighted where applicable
- Missing data (country doesn't exist) marked with `exists: false`
