"""
Process all Victoria 2 save files and extract economic data into structured format.

This module is the main processing pipeline that transforms raw Victoria 2 save
files into structured JSON and CSV data suitable for analysis and visualization.
It handles batch processing, progress tracking, and output generation.

PROCESSING PIPELINE OVERVIEW
============================

```
Input: saves/*.txt (save files)
         │
         ├──> [1] Load & Parse (parser.py)
         │         │
         │         └──> Paradox script → Python dict
         │
         ├──> [2] Extract Economic Data (extractor.py)
         │         │
         │         ├──> World Market → prices, supply, demand
         │         ├──> Countries → treasury, taxes, factories
         │         └──> Provinces → POPs, RGOs
         │
         ├──> [3] Aggregate & Transform
         │         │
         │         └──> Calculate global statistics
         │
         └──> [4] Output Generation
                   │
                   ├──> economic_data.json (complete dataset)
                   ├──> global_statistics.json (world aggregates)
                   ├──> world_market_*.json (commodity data)
                   ├──> countries/*.json (per-country series)
                   └──> *.csv (spreadsheet-friendly)
```

DATA FLOW
=========

1. **Input Stage**
   - Reads save files from `saves/` directory
   - Files should be named YYYY.M.D.txt (e.g., 1836.1.1.txt)
   - Sorts files chronologically for time-series analysis

2. **Processing Stage**
   - Parses each save file using SaveParser
   - Extracts world market, country, and province data
   - Aggregates global population statistics

3. **Output Stage**
   - Writes comprehensive JSON data
   - Creates time-series files for specific data types
   - Generates CSV summaries for spreadsheet analysis

COMMAND-LINE OPTIONS
====================

--limit N       : Process only first N save files (useful for testing)
--resume        : Continue from previous partial run (uses _partial.json)
--batch-size N  : Save progress every N files (default: 50)

USAGE EXAMPLES
==============

Process all save files:
    $ python process_saves.py

Process first 10 files for testing:
    $ python process_saves.py --limit 10

Resume interrupted processing:
    $ python process_saves.py --resume

OUTPUT FILES GENERATED
======================

Main Data:
    - economic_data.json: Complete dataset with all extracted data

Time Series:
    - global_statistics.json: World population, wealth, welfare
    - global_population_by_type.json: Population breakdown by POP type
    - world_market_prices.json: Commodity prices over time
    - world_market_supply.json: Commodity supply over time
    - world_market_sold.json: Actual quantities sold over time

Per-Country:
    - countries/{TAG}.json: Time series for each country

CSV Summaries:
    - global_summary.csv: World statistics in spreadsheet format
    - major_countries_summary.csv: Top 20 countries' key metrics

Author: Victoria 2 Economy Analysis Tool Project
"""

import json
import os
import re
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from parser import SaveParser, iterate_country_sections, iterate_province_sections
from extractor import (
    extract_world_market,
    extract_country_data,
    aggregate_global_pop_data,
    SaveData,
    WorldMarketData,
    CountryData,
    PopData,
)


# =============================================================================
# DATE HANDLING UTILITIES
# =============================================================================

def parse_date(date_str: str) -> tuple[int, int, int]:
    """
    Parse Victoria 2 date string to (year, month, day) tuple.

    Victoria 2 uses the format "YYYY.M.D" for dates, where months and days
    may be single digits (e.g., "1836.1.1" for January 1st, 1836).

    Args:
        date_str: Date string in "YYYY.M.D" format, optionally quoted

    Returns:
        tuple: (year, month, day) as integers

    Examples:
        >>> parse_date("1836.1.1")
        (1836, 1, 1)
        >>> parse_date('"1850.12.15"')
        (1850, 12, 15)

    Note:
        The game spans 1836-1936, so year will typically be in that range.
    """
    parts = date_str.strip('"').split('.')
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def date_sort_key(filename: str) -> tuple[int, int, int]:
    """
    Extract date from filename for chronological sorting.

    Save files are expected to be named YYYY.M.D.txt, matching the
    in-game date format. This function extracts the date for sorting.

    Args:
        filename: Filename or path to save file

    Returns:
        tuple: (year, month, day) for sorting, or (0, 0, 0) if parsing fails

    Examples:
        >>> date_sort_key("1836.1.1.txt")
        (1836, 1, 1)
        >>> date_sort_key("saves/1850.6.15.txt")
        (1850, 6, 15)
        >>> date_sort_key("invalid.txt")
        (0, 0, 0)

    Note:
        Returns (0, 0, 0) for unparseable filenames to sort them first,
        keeping them visible for investigation.
    """
    name = Path(filename).stem  # Remove directory and extension
    try:
        return parse_date(name)
    except (ValueError, IndexError):
        # Invalid filename format, return default for sorting
        return (0, 0, 0)


# =============================================================================
# SAVE FILE PROCESSING
# =============================================================================

def process_single_save(filepath: str) -> dict:
    """
    Process a single save file and return extracted economic data.

    This is the core processing function that handles one save file.
    It parses the file, extracts all economic data, and returns a
    dictionary suitable for JSON serialization.

    Args:
        filepath: Path to the .txt or .v2 save file

    Returns:
        dict: Comprehensive economic data with structure:
            {
                'date': "YYYY.M.D",
                'world_market': {prices, supply, actual_sold},
                'global_statistics': {population, wealth, welfare...},
                'countries': {TAG: {treasury, prestige, ...}, ...}
            }

    Processing Steps:
        1. Read file with Latin-1 encoding
        2. Parse using SaveParser
        3. Extract date from file header
        4. Extract world market data
        5. Build province dictionary for country processing
        6. Extract data for each country
        7. Aggregate global statistics
        8. Structure and return result

    Example:
        >>> result = process_single_save("saves/1836.1.1.txt")
        >>> print(result['date'])
        1836.1.1
        >>> print(result['countries']['ENG']['treasury'])
        50000.0

    Note:
        Province data must be collected first because country POP data
        is extracted from provinces (POPs are stored in province blocks,
        not country blocks in the save file).
    """
    print(f"Processing: {Path(filepath).name}")

    # ==== STEP 1: Read and Parse ====
    # Victoria 2 save files use Latin-1 encoding
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    parser = SaveParser(text)
    data = parser.parse()

    # ==== STEP 2: Extract Date ====
    # The date is at the top of the save file
    date_str = data.get('date', '').strip('"')

    # ==== STEP 3: Extract World Market ====
    world_market = extract_world_market(data)

    # ==== STEP 4: Collect Province Data ====
    # Provinces are stored with numeric keys (province IDs)
    # We need this for extracting POP data per country
    provinces = {}
    for key, value in data.items():
        # Province keys are integers (1, 2, ..., 3000+)
        # They might be parsed as int or str depending on context
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            prov_id = int(key)
            # Provinces have a 'name' field to distinguish from other numeric blocks
            if isinstance(value, dict) and 'name' in value:
                provinces[prov_id] = value

    # ==== STEP 5: Extract Country Data ====
    # Countries are stored with 3-letter uppercase tags (ENG, FRA, PRU, etc.)
    # We skip 'REB' which is the rebels pseudo-country
    countries = {}
    for key, value in data.items():
        if isinstance(key, str) and len(key) == 3 and key.isupper() and key != 'REB':
            if isinstance(value, dict):
                country = extract_country_data(key, value, provinces)
                countries[key] = country

    # ==== STEP 6: Aggregate Global Statistics ====
    # Sum/average population data across all countries
    global_pop = aggregate_global_pop_data(countries)

    # ==== STEP 7: Build Result Dictionary ====
    # Structure data for JSON output
    result = {
        'date': date_str,
        'world_market': {
            'prices': world_market.prices,
            'supply': world_market.supply,
            'actual_sold': world_market.actual_sold,
        },
        'global_statistics': {
            # Population totals
            'total_population': global_pop.total_population,
            'population_by_type': global_pop.population_by_type,
            # Wealth
            'total_pop_money': global_pop.total_money,
            'total_pop_bank_savings': global_pop.total_bank_savings,
            'money_by_pop_type': global_pop.money_by_type,
            # Welfare (needs satisfaction)
            'avg_life_needs': global_pop.avg_life_needs,
            'avg_everyday_needs': global_pop.avg_everyday_needs,
            'avg_luxury_needs': global_pop.avg_luxury_needs,
            # Social indicators
            'avg_literacy': global_pop.avg_literacy,
            'avg_consciousness': global_pop.avg_consciousness,
            'avg_militancy': global_pop.avg_militancy,
            # Employment
            'total_employed_craftsmen': global_pop.employed_craftsmen,
            'total_employed_labourers': global_pop.employed_labourers,
        },
        'countries': {},
    }

    # ==== STEP 8: Add Country Data ====
    for tag, country in countries.items():
        result['countries'][tag] = {
            # Government finances
            'treasury': country.treasury,
            'bank_reserves': country.bank_reserves,
            'bank_money_lent': country.bank_money_lent,
            # International standing
            'prestige': country.prestige,
            'infamy': country.infamy,
            # Economy
            'tax_base': country.tax_base,
            'civilized': country.civilized,
            # Taxation (rates and income)
            'rich_tax_rate': country.rich_tax_rate,
            'middle_tax_rate': country.middle_tax_rate,
            'poor_tax_rate': country.poor_tax_rate,
            'rich_tax_income': country.rich_tax_income,
            'middle_tax_income': country.middle_tax_income,
            'poor_tax_income': country.poor_tax_income,
            'total_tax_income': (country.rich_tax_income +
                                country.middle_tax_income +
                                country.poor_tax_income),
            # Government spending
            'education_spending': country.education_spending,
            'military_spending': country.military_spending,
            'social_spending': country.social_spending,
            # Industry (factories)
            'total_factory_count': country.total_factory_count,
            'total_factory_levels': country.total_factory_levels,
            'total_factory_income': country.total_factory_income,
            'total_factory_employment': country.total_factory_employment,
            # Agriculture/Mining (RGOs)
            'total_rgo_income': country.total_rgo_income,
            'total_rgo_employment': country.total_rgo_employment,
            # Population data
            'population': {
                'total': country.pop_data.total_population,
                'by_type': country.pop_data.population_by_type,
                'total_money': country.pop_data.total_money,
                'total_bank_savings': country.pop_data.total_bank_savings,
                'money_by_type': country.pop_data.money_by_type,
                'avg_life_needs': country.pop_data.avg_life_needs,
                'avg_everyday_needs': country.pop_data.avg_everyday_needs,
                'avg_luxury_needs': country.pop_data.avg_luxury_needs,
                'avg_literacy': country.pop_data.avg_literacy,
                'avg_consciousness': country.pop_data.avg_consciousness,
                'avg_militancy': country.pop_data.avg_militancy,
            },
        }

    return result


def process_save_file_wrapper(filepath: str) -> tuple[str, dict | None]:
    """
    Wrapper for process_single_save that catches exceptions.

    Used for parallel processing where we don't want one failure
    to crash the entire batch.

    Args:
        filepath: Path to save file

    Returns:
        tuple: (filepath, result_dict) or (filepath, None) on error

    Note:
        Currently not used (parallel processing disabled for stability),
        but kept for potential future use.
    """
    try:
        result = process_single_save(filepath)
        return (filepath, result)
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return (filepath, None)


# =============================================================================
# MAIN PROCESSING PIPELINE
# =============================================================================

def main():
    """
    Main entry point for the processing pipeline.

    Command-Line Arguments:
        --limit N       : Process only first N files (for testing)
        --resume        : Continue from existing partial data
        --batch-size N  : Save progress every N files (default: 50)

    Processing Flow:
        1. Discover save files in saves/ directory
        2. Sort files chronologically by in-game date
        3. Optionally load previous partial progress
        4. Process each file sequentially
        5. Save progress periodically (batch-size)
        6. Generate output files when complete

    Progress Tracking:
        - Displays progress counter and ETA
        - Saves partial results to economic_data_partial.json
        - Can resume from partial data if interrupted

    Output Generation:
        After processing, calls create_time_series() and create_summary_csv()
        to generate all derivative output files.
    """
    import argparse
    import time

    # ==== PARSE COMMAND-LINE ARGUMENTS ====
    arg_parser = argparse.ArgumentParser(
        description='Process Victoria 2 save files into structured economic data'
    )
    arg_parser.add_argument(
        '--limit', type=int,
        help='Process only first N files (useful for testing)'
    )
    arg_parser.add_argument(
        '--resume', action='store_true',
        help='Resume from existing partial data file'
    )
    arg_parser.add_argument(
        '--batch-size', type=int, default=50,
        help='Save progress every N files (default: 50)'
    )
    args = arg_parser.parse_args()

    # ==== SET UP DIRECTORIES ====
    saves_dir = Path(__file__).parent / 'saves'
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)  # Create output/ if it doesn't exist

    # ==== DISCOVER SAVE FILES ====
    # Find all .txt files in saves/ and sort by date
    save_files = sorted(
        saves_dir.glob('*.txt'),
        key=lambda p: date_sort_key(p.name)
    )

    if not save_files:
        print("No save files found in 'saves' directory.")
        print("Copy your save files to the 'saves' folder first.")
        return

    if args.limit:
        save_files = save_files[:args.limit]

    print(f"Found {len(save_files)} save files to process")

    # ==== CHECK FOR PARTIAL DATA (RESUME SUPPORT) ====
    partial_file = output_dir / 'economic_data_partial.json'
    all_data = []
    processed_dates = set()

    if args.resume and partial_file.exists():
        print("Loading existing partial data...")
        with open(partial_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        processed_dates = {entry['date'] for entry in all_data}
        print(f"Loaded {len(all_data)} previously processed entries")

    # ==== PROCESS EACH FILE ====
    failed = []
    start_time = time.time()

    for i, filepath in enumerate(save_files):
        # Skip if already processed (for resume mode)
        filename_date = Path(filepath).stem
        if filename_date in processed_dates:
            print(f"[{i+1}/{len(save_files)}] Skipping {filename_date} (already processed)")
            continue

        # Show progress indicator
        print(f"[{i+1}/{len(save_files)}] ", end='', flush=True)

        try:
            result = process_single_save(str(filepath))
            all_data.append(result)

            # ==== PERIODIC PROGRESS SAVE ====
            if len(all_data) % args.batch_size == 0:
                # Calculate progress statistics
                elapsed = time.time() - start_time
                rate = len(all_data) / elapsed if elapsed > 0 else 0
                remaining = len(save_files) - i - 1
                eta = remaining / rate / 60 if rate > 0 else 0
                print(f"  Progress: {len(all_data)} processed, ~{eta:.0f} min remaining")

                # Save partial results to allow resume
                with open(partial_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f)

        except Exception as e:
            print(f"Error: {e}")
            failed.append(str(filepath))

    # ==== PROCESSING COMPLETE ====
    elapsed_total = time.time() - start_time
    print(f"\nProcessed {len(all_data)} files in {elapsed_total/60:.1f} minutes")
    print(f"Failed: {len(failed)}")

    if failed:
        print("Failed files:")
        for f in failed[:10]:
            print(f"  {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    # ==== SORT BY DATE ====
    # Ensure chronological order for time-series analysis
    all_data.sort(key=lambda x: parse_date(x['date']) if x['date'] else (0, 0, 0))

    # ==== WRITE MAIN OUTPUT FILE ====
    output_file = output_dir / 'economic_data.json'
    print(f"Writing full data to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)

    # Remove partial file since processing is complete
    if partial_file.exists():
        partial_file.unlink()

    # ==== GENERATE DERIVATIVE OUTPUT FILES ====
    create_time_series(all_data, output_dir)

    print("Done!")


# =============================================================================
# OUTPUT FILE GENERATION
# =============================================================================

def create_time_series(all_data: list[dict], output_dir: Path):
    """
    Create separate time series files for different data categories.

    This function takes the complete dataset and splits it into focused
    files for easier analysis:

    Args:
        all_data: List of processed save data dictionaries
        output_dir: Directory to write output files

    Generated Files:
        World Market:
            - world_market_prices.json: Commodity prices over time
            - world_market_supply.json: Commodity supply over time
            - world_market_sold.json: Quantities sold over time

        Global Statistics:
            - global_statistics.json: Population, wealth, welfare metrics
            - global_population_by_type.json: Population by POP type

        Per-Country:
            - countries/{TAG}.json: Time series for each country

    File Structure:
        Each file contains a list of dated entries:
        [
            {"date": "1836.1.1", "iron": 35.0, "coal": 2.3, ...},
            {"date": "1836.2.1", "iron": 35.5, "coal": 2.4, ...},
            ...
        ]

    Benefits:
        - Smaller files load faster for specific analyses
        - Easier to work with in visualization tools
        - Country files can be loaded individually
    """

    # ==== WORLD MARKET: PRICES ====
    # Commodity prices over time (for price trend analysis)
    prices_series = []
    for entry in all_data:
        prices_series.append({
            'date': entry['date'],
            **entry['world_market']['prices']  # Spread all commodity prices
        })

    with open(output_dir / 'world_market_prices.json', 'w', encoding='utf-8') as f:
        json.dump(prices_series, f, indent=2)

    # ==== WORLD MARKET: SUPPLY ====
    # Commodity supply (production capacity analysis)
    supply_series = []
    for entry in all_data:
        supply_series.append({
            'date': entry['date'],
            **entry['world_market']['supply']
        })

    with open(output_dir / 'world_market_supply.json', 'w', encoding='utf-8') as f:
        json.dump(supply_series, f, indent=2)

    # ==== WORLD MARKET: ACTUAL SOLD ====
    # Quantities actually traded (demand proxy)
    sold_series = []
    for entry in all_data:
        sold_series.append({
            'date': entry['date'],
            **entry['world_market']['actual_sold']
        })

    with open(output_dir / 'world_market_sold.json', 'w', encoding='utf-8') as f:
        json.dump(sold_series, f, indent=2)

    # ==== GLOBAL STATISTICS ====
    # Aggregate world data (population, wealth, welfare)
    global_series = []
    for entry in all_data:
        gs = entry['global_statistics']
        global_series.append({
            'date': entry['date'],
            # Population
            'total_population': gs['total_population'],
            # Wealth
            'total_pop_money': gs['total_pop_money'],
            'total_pop_bank_savings': gs['total_pop_bank_savings'],
            # Welfare (needs satisfaction, 0-1 scale)
            'avg_life_needs': gs['avg_life_needs'],
            'avg_everyday_needs': gs['avg_everyday_needs'],
            'avg_luxury_needs': gs['avg_luxury_needs'],
            # Social indicators
            'avg_literacy': gs['avg_literacy'],
            'avg_consciousness': gs['avg_consciousness'],
            'avg_militancy': gs['avg_militancy'],
        })

    with open(output_dir / 'global_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(global_series, f, indent=2)

    # ==== POPULATION BY TYPE ====
    # World population breakdown by POP type (demographic analysis)
    pop_type_series = []
    for entry in all_data:
        pop_type_series.append({
            'date': entry['date'],
            **entry['global_statistics']['population_by_type']
        })

    with open(output_dir / 'global_population_by_type.json', 'w', encoding='utf-8') as f:
        json.dump(pop_type_series, f, indent=2)

    # ==== PER-COUNTRY TIME SERIES ====
    # Collect all country tags that appear in any save
    all_countries = set()
    for entry in all_data:
        all_countries.update(entry['countries'].keys())

    # Initialize country series dictionary
    country_series = {tag: [] for tag in all_countries}

    # Build time series for each country
    for entry in all_data:
        date = entry['date']
        for tag in all_countries:
            if tag in entry['countries']:
                c = entry['countries'][tag]
                country_series[tag].append({
                    'date': date,
                    # Government finances
                    'treasury': c['treasury'],
                    'bank_reserves': c['bank_reserves'],
                    # International standing
                    'prestige': c['prestige'],
                    'infamy': c['infamy'],
                    # Economy
                    'total_tax_income': c['total_tax_income'],
                    # Industry
                    'total_factory_count': c['total_factory_count'],
                    'total_factory_levels': c['total_factory_levels'],
                    'total_factory_income': c['total_factory_income'],
                    'total_factory_employment': c['total_factory_employment'],
                    # Agriculture/Mining
                    'total_rgo_income': c['total_rgo_income'],
                    'total_rgo_employment': c['total_rgo_employment'],
                    # Population
                    'population_total': c['population']['total'],
                    'pop_money': c['population']['total_money'],
                    'pop_bank_savings': c['population']['total_bank_savings'],
                    # Welfare
                    'avg_life_needs': c['population']['avg_life_needs'],
                    'avg_everyday_needs': c['population']['avg_everyday_needs'],
                    'avg_literacy': c['population']['avg_literacy'],
                })
            else:
                # Country doesn't exist at this date (annexed, not yet formed, etc.)
                country_series[tag].append({
                    'date': date,
                    'exists': False
                })

    # Write individual country files
    countries_dir = output_dir / 'countries'
    countries_dir.mkdir(exist_ok=True)

    for tag, series in country_series.items():
        # Only write if country has any real data (not just 'exists': False entries)
        if any('treasury' in entry for entry in series):
            with open(countries_dir / f'{tag}.json', 'w', encoding='utf-8') as f:
                json.dump(series, f, indent=2)

    # ==== CREATE CSV SUMMARIES ====
    create_summary_csv(all_data, output_dir)


def create_summary_csv(all_data: list[dict], output_dir: Path):
    """
    Create CSV summary files for spreadsheet analysis.

    CSV format is more convenient for:
    - Excel/Google Sheets analysis
    - Quick data exploration
    - Importing into other tools (R, SPSS, etc.)

    Args:
        all_data: List of processed save data dictionaries
        output_dir: Directory to write CSV files

    Generated Files:
        global_summary.csv:
            World-level statistics over time
            Columns: date, total_population, total_pop_money, etc.

        major_countries_summary.csv:
            Top 20 countries by final population
            Columns: date, {TAG}_treasury, {TAG}_prestige, etc.

    CSV Design Notes:
        - Headers use descriptive names
        - Dates in YYYY.M.D format (matches game)
        - Numeric values with full precision
        - Missing data represented as 0
    """
    import csv

    # ==== GLOBAL SUMMARY CSV ====
    # World-level statistics for easy spreadsheet import
    with open(output_dir / 'global_summary.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Column headers
        headers = [
            'date',
            'total_population',
            'total_pop_money',
            'total_pop_bank_savings',
            'avg_life_needs',
            'avg_everyday_needs',
            'avg_luxury_needs',
            'avg_literacy',
            'avg_consciousness',
            'avg_militancy'
        ]
        writer.writerow(headers)

        # Data rows
        for entry in all_data:
            gs = entry['global_statistics']
            writer.writerow([
                entry['date'],
                gs['total_population'],
                gs['total_pop_money'],
                gs['total_pop_bank_savings'],
                gs['avg_life_needs'],
                gs['avg_everyday_needs'],
                gs['avg_luxury_needs'],
                gs['avg_literacy'],
                gs['avg_consciousness'],
                gs['avg_militancy'],
            ])

    # ==== MAJOR COUNTRIES SUMMARY CSV ====
    # Select top 20 countries by final population
    # (focuses on historically significant nations)
    final_entry = all_data[-1] if all_data else {}
    final_countries = final_entry.get('countries', {})
    sorted_countries = sorted(
        final_countries.items(),
        key=lambda x: x[1].get('population', {}).get('total', 0),
        reverse=True
    )[:20]  # Top 20
    major_country_tags = [tag for tag, _ in sorted_countries]

    with open(output_dir / 'major_countries_summary.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Build header row with columns for each country
        # Format: date, ENG_treasury, ENG_prestige, ..., FRA_treasury, FRA_prestige, ...
        base_headers = ['date']
        for tag in major_country_tags:
            base_headers.extend([
                f'{tag}_treasury',
                f'{tag}_prestige',
                f'{tag}_population',
                f'{tag}_factory_count',
                f'{tag}_factory_income',
                f'{tag}_rgo_income',
                f'{tag}_pop_money',
            ])
        writer.writerow(base_headers)

        # Data rows
        for entry in all_data:
            row = [entry['date']]
            for tag in major_country_tags:
                c = entry['countries'].get(tag, {})
                if c:
                    row.extend([
                        c.get('treasury', 0),
                        c.get('prestige', 0),
                        c.get('population', {}).get('total', 0),
                        c.get('total_factory_count', 0),
                        c.get('total_factory_income', 0),
                        c.get('total_rgo_income', 0),
                        c.get('population', {}).get('total_money', 0),
                    ])
                else:
                    # Country doesn't exist at this date
                    row.extend([0, 0, 0, 0, 0, 0, 0])
            writer.writerow(row)


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    main()
