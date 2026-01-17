# Victoria 2 Economy Analysis Tool - Architecture Guide

This document provides a detailed technical overview of the codebase architecture,
designed for developers who want to understand, modify, or extend the tool.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VICTORIA 2 ECONOMY ANALYZER                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │   COLLECTION    │───▶│   PROCESSING    │───▶│    VISUALIZATION        │  │
│  │                 │    │                 │    │                         │  │
│  │  save_watcher   │    │  parser         │    │  viz/plot_all           │  │
│  │  (watchdog)     │    │  extractor      │    │  viz/plot_global        │  │
│  │                 │    │  process_saves  │    │  viz/plot_market        │  │
│  └────────┬────────┘    └────────┬────────┘    │  viz/plot_countries     │  │
│           │                      │             │  viz/utils              │  │
│           ▼                      ▼             └─────────────────────────┘  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │     saves/      │    │     output/     │    │       charts/           │  │
│  │   (raw files)   │    │  (JSON + CSV)   │    │  (PNG visualizations)   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
                    ┌──────────────────┐
                    │   save_watcher   │
                    │   (standalone)   │
                    └──────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│     parser       │◀───│   process_saves  │───▶│   extractor      │
│                  │    │                  │    │                  │
│  SaveParser      │    │  process_*       │    │  WorldMarketData │
│  parse_save_file │    │  create_*        │    │  PopData         │
│  iterate_*       │    │  main()          │    │  CountryData     │
└──────────────────┘    └──────────────────┘    └──────────────────┘

                    ┌──────────────────┐
                    │   viz/utils      │
                    │                  │
                    │  Data loading    │
                    │  Tag succession  │
                    │  Chart styling   │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  viz/plot_global │ │ viz/plot_market  │ │viz/plot_countries│
└──────────────────┘ └──────────────────┘ └──────────────────┘
        │                    │                    │
        └────────────────────┴────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   viz/plot_all   │
                    │   (entry point)  │
                    └──────────────────┘
```

## Core Components

### 1. Parser Module (parser.py)

**Purpose**: Parse Paradox script format into Python data structures.

**Design Pattern**: Recursive Descent Parser

```python
class SaveParser:
    """
    State machine that maintains position in text and parses recursively.
    """
    text: str       # Full file content
    pos: int        # Current position (cursor)
    length: int     # Total length

    def parse(self) -> dict:
        """Entry point - treats entire input as block contents."""

    def _parse_block_contents(self) -> dict | list:
        """Auto-detect if block contains dict or list."""

    def _parse_dict(self) -> dict:
        """Parse key=value pairs, handling duplicates."""

    def _parse_list(self) -> list:
        """Parse space-separated values."""

    def _parse_value(self) -> Any:
        """Parse any value type (string, number, bool, block)."""
```

**Key Design Decisions**:

1. **Full-text loading**: Entire file loaded for fast random access
2. **Position-based parsing**: Single `pos` cursor advances through text
3. **Lookahead for type detection**: Peek without consuming to determine structure
4. **Duplicate key handling**: Converts to lists automatically

**Public API**:

| Function | Use Case | Memory |
|----------|----------|--------|
| `parse_save_file()` | Full parsing | High |
| `fast_extract_sections()` | Specific sections only | Medium |
| `iterate_country_sections()` | Stream countries | Low |
| `iterate_province_sections()` | Stream provinces | Low |

### 2. Extractor Module (extractor.py)

**Purpose**: Transform parsed data into typed dataclasses.

**Design Pattern**: Data Transfer Objects (DTOs)

```
┌─────────────────────────────────────────────────────────────┐
│                        SaveData                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │WorldMarket  │  │ PopData     │  │   CountryData       │  │
│  │  Data       │  │ (global)    │  │   ┌─────────────┐   │  │
│  │             │  │             │  │   │  PopData    │   │  │
│  │ prices{}    │  │ population  │  │   │  (country)  │   │  │
│  │ supply{}    │  │ literacy    │  │   └─────────────┘   │  │
│  │ demand{}    │  │ militancy   │  │   ┌─────────────┐   │  │
│  │ actual_sold │  │ needs       │  │   │  StateData  │   │  │
│  └─────────────┘  └─────────────┘  │   │ ┌─────────┐ │   │  │
│                                    │   │ │ Factory │ │   │  │
│                                    │   │ │  Data   │ │   │  │
│                                    │   │ └─────────┘ │   │  │
│                                    │   └─────────────┘   │  │
│                                    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key Functions**:

```python
def extract_world_market(data: dict) -> WorldMarketData
def extract_country_data(tag, country_block, provinces) -> CountryData
def extract_factory_data(building_block) -> FactoryData
def extract_rgo_data(rgo_block) -> RGOData
def aggregate_global_pop_data(countries) -> PopData
```

**Weighted Average Calculation**:

```python
# Population-weighted averaging for needs, literacy, etc.
# Formula: sum(value * population) / total_population

weighted_sum = sum(pop['literacy'] * pop['size'] for pop in all_pops)
avg_literacy = weighted_sum / total_population
```

### 3. Processing Pipeline (process_saves.py)

**Purpose**: Batch process save files into JSON/CSV output.

**Design Pattern**: Pipeline/ETL

```
Input Stage          Transform Stage         Output Stage
───────────          ───────────────         ────────────
                     ┌───────────────┐
saves/*.txt ───────▶ │ Parse + Extract│ ────▶ economic_data.json
                     └───────────────┘       global_statistics.json
                            │                world_market_*.json
                            ▼                countries/*.json
                     ┌───────────────┐       *.csv
                     │   Aggregate    │
                     │   Transform    │
                     └───────────────┘
```

**Progress Tracking**:

```python
# Resume capability via partial file
if args.resume and partial_file.exists():
    all_data = json.load(partial_file)
    processed_dates = {entry['date'] for entry in all_data}

# Periodic saves
if len(all_data) % batch_size == 0:
    json.dump(all_data, partial_file)
```

### 4. Visualization Module (viz/)

**Purpose**: Generate matplotlib charts from processed data.

**Design Pattern**: Template Method + Strategy

**Module Structure**:

```
viz/
├── __init__.py          # Package marker
├── utils.py             # Shared utilities (data loading, styling)
├── plot_all.py          # Entry point, orchestration
├── plot_global.py       # World-level charts
├── plot_market.py       # Commodity market charts
└── plot_countries.py    # Country + comparison charts
```

**Common Chart Pattern**:

```python
def plot_metric_chart():
    """Standard chart generation pattern."""
    # 1. Setup
    setup_style()

    # 2. Load data
    data = load_json('some_file.json')

    # 3. Extract
    dates = [parse_date(d['date']) for d in data]
    values = [d['metric'] for d in data]

    # 4. Create figure
    fig, ax = plt.subplots()
    ax.plot(dates, values, color='#2E86AB', linewidth=2)

    # 5. Format
    ax.set_title('Title')
    format_date_axis(ax, dates)
    format_large_numbers(ax)

    # 6. Save
    save_chart('chart_name', subdir='category')
```

**Tag Succession System**:

```python
# Prussia → North German Federation → Germany
TAG_GROUPS = {
    'GER': ['PRU', 'NGF', 'GER'],
    'KUK': ['AUS', 'SGF', 'KUK'],
}

def load_country_group(tag):
    """
    For each date, select the most advanced tag that exists.
    Later tags (higher index) take precedence.
    """
    all_data = {}
    for tag_idx, tag in enumerate(tags):
        for entry in load_country(tag):
            date = entry['date']
            if date not in all_data or tag_idx > all_data[date][0]:
                all_data[date] = (tag_idx, entry)
    return [entry for _, entry in sorted(all_data.items())]
```

## Data Flow Details

### Save File → Parsed Dict

```
Input: "key=value\nblock={\n  inner=123\n}"

Parsing:
1. Read "key" token
2. Skip "="
3. Read "value" token → string
4. Read "block" token
5. Skip "="
6. Enter block, detect dict (has "=")
7. Parse inner key-value pairs
8. Exit block

Output: {"key": "value", "block": {"inner": 123}}
```

### Parsed Dict → Dataclass

```
Input: {
    "money": 50000.0,
    "state": {
        "provinces": [300, 301],
        "state_buildings": {"building": "factory", "level": 2}
    }
}

Extraction:
1. country.treasury = safe_float(data["money"])
2. For each state block:
   a. state.provinces = data["provinces"]
   b. For each state_buildings:
      - factory.name = building_block["building"]
      - factory.level = int(building_block["level"])

Output: CountryData(treasury=50000.0, states=[StateData(...)])
```

### Dataclass → JSON

```
Input: CountryData(tag="ENG", treasury=50000.0, ...)

Serialization:
1. Convert dataclass to dict
2. Filter relevant fields
3. Add derived calculations
4. JSON serialize

Output: {
    "date": "1836.1.1",
    "countries": {
        "ENG": {
            "treasury": 50000.0,
            "total_tax_income": 1234.5,
            ...
        }
    }
}
```

## Extension Points

### Adding a New Data Field

1. **Add to dataclass** (extractor.py):
```python
@dataclass
class CountryData:
    new_field: float = 0.0
```

2. **Extract in function** (extractor.py):
```python
def extract_country_data(...):
    country.new_field = safe_float(data.get('new_key', 0))
```

3. **Include in output** (process_saves.py):
```python
result['countries'][tag]['new_field'] = country.new_field
```

4. **Visualize** (viz/plot_countries.py):
```python
COUNTRY_STATS['new_field'] = {
    'title': 'New Field',
    'ylabel': 'Units',
    'color': '#123456',
}
```

### Adding a New Chart Type

1. **Create function** (appropriate plot_*.py):
```python
def plot_new_chart():
    setup_style()
    data = load_json('data_file.json')
    # ... chart logic ...
    save_chart('new_chart', subdir='category')
```

2. **Register in plot_all()**:
```python
def plot_all():
    # ...
    plot_new_chart()
```

### Adding a New Commodity Category

1. **Define category** (viz/plot_market.py):
```python
NEW_CATEGORY = ['item1', 'item2', 'item3']

ALL_CATEGORIES['new'] = ('New Category', NEW_CATEGORY)
```

2. **Add colors** (viz/utils.py):
```python
COMMODITY_COLORS['item1'] = '#ABCDEF'
COMMODITY_COLORS['item2'] = '#123456'
```

## Performance Considerations

### Memory Management

| Approach | Memory | Speed | Use Case |
|----------|--------|-------|----------|
| `parse_save_file()` | High | Fast | Single file, full data |
| `fast_extract_sections()` | Medium | Faster | Specific sections |
| `iterate_country_sections()` | Low | Slower | Many countries |
| Batch processing | Controlled | Variable | Many files |

### Optimization Strategies

1. **Lazy loading**: Only load needed data files
2. **Generator patterns**: Use iterators for large datasets
3. **Caching**: JSON files as cached intermediate format
4. **Batch saves**: Periodic progress saves prevent loss

### Chart Generation

- Close figures after saving (`plt.close()`)
- Use consistent figure sizes for batch generation
- Apply `tight_layout()` for proper spacing
- Save at appropriate DPI (150 for files, 100 for screen)

## Testing Approach

### Manual Testing

```bash
# Test parser with sample file
python -c "from parser import parse_save_file; print(parse_save_file('saves/test.txt'))"

# Test single save processing
python -c "from process_saves import process_single_save; print(process_single_save('saves/test.txt'))"

# Test chart generation
cd viz && python -c "from plot_global import plot_total_population; plot_total_population()"
```

### Data Validation

Key assertions in extraction:
- Population > 0 for existing countries
- Prices, supply > 0 for traded commodities
- Needs satisfaction in [0, 1] range typically
- Date format matches "YYYY.M.D"

## Conclusion

This architecture provides:

1. **Separation of Concerns**: Parsing, extraction, processing, visualization
2. **Extensibility**: Easy to add new metrics and charts
3. **Performance**: Options for memory/speed tradeoffs
4. **Maintainability**: Typed dataclasses, documented modules

The modular design allows each component to be modified independently while
maintaining clear interfaces between stages.
