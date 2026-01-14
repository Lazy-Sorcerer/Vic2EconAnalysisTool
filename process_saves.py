"""
Process all Victoria 2 save files and extract economic data into structured format.
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


def parse_date(date_str: str) -> tuple[int, int, int]:
    """Parse date string to (year, month, day) tuple."""
    parts = date_str.strip('"').split('.')
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def date_sort_key(filename: str) -> tuple[int, int, int]:
    """Extract date from filename for sorting."""
    name = Path(filename).stem
    try:
        return parse_date(name)
    except (ValueError, IndexError):
        return (0, 0, 0)


def process_single_save(filepath: str) -> dict:
    """
    Process a single save file and return extracted economic data.
    Returns a dictionary that can be serialized to JSON.
    """
    print(f"Processing: {Path(filepath).name}")

    # Read and parse the file
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    parser = SaveParser(text)
    data = parser.parse()

    # Get date
    date_str = data.get('date', '').strip('"')

    # Extract world market
    world_market = extract_world_market(data)

    # Collect provinces first (needed for country POP data)
    provinces = {}
    for key, value in data.items():
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            prov_id = int(key)
            if isinstance(value, dict) and 'name' in value:
                provinces[prov_id] = value

    # Extract country data
    countries = {}
    for key, value in data.items():
        if isinstance(key, str) and len(key) == 3 and key.isupper() and key != 'REB':
            if isinstance(value, dict):
                country = extract_country_data(key, value, provinces)
                countries[key] = country

    # Aggregate global data
    global_pop = aggregate_global_pop_data(countries)

    # Build result
    result = {
        'date': date_str,
        'world_market': {
            'prices': world_market.prices,
            'supply': world_market.supply,
            'actual_sold': world_market.actual_sold,
        },
        'global_statistics': {
            'total_population': global_pop.total_population,
            'population_by_type': global_pop.population_by_type,
            'total_pop_money': global_pop.total_money,
            'total_pop_bank_savings': global_pop.total_bank_savings,
            'money_by_pop_type': global_pop.money_by_type,
            'avg_life_needs': global_pop.avg_life_needs,
            'avg_everyday_needs': global_pop.avg_everyday_needs,
            'avg_luxury_needs': global_pop.avg_luxury_needs,
            'avg_literacy': global_pop.avg_literacy,
            'avg_consciousness': global_pop.avg_consciousness,
            'avg_militancy': global_pop.avg_militancy,
            'total_employed_craftsmen': global_pop.employed_craftsmen,
            'total_employed_labourers': global_pop.employed_labourers,
        },
        'countries': {},
    }

    # Add country data
    for tag, country in countries.items():
        result['countries'][tag] = {
            'treasury': country.treasury,
            'bank_reserves': country.bank_reserves,
            'bank_money_lent': country.bank_money_lent,
            'prestige': country.prestige,
            'infamy': country.infamy,
            'tax_base': country.tax_base,
            'civilized': country.civilized,
            'rich_tax_rate': country.rich_tax_rate,
            'middle_tax_rate': country.middle_tax_rate,
            'poor_tax_rate': country.poor_tax_rate,
            'rich_tax_income': country.rich_tax_income,
            'middle_tax_income': country.middle_tax_income,
            'poor_tax_income': country.poor_tax_income,
            'total_tax_income': country.rich_tax_income + country.middle_tax_income + country.poor_tax_income,
            'education_spending': country.education_spending,
            'military_spending': country.military_spending,
            'social_spending': country.social_spending,
            'total_factory_count': country.total_factory_count,
            'total_factory_levels': country.total_factory_levels,
            'total_factory_income': country.total_factory_income,
            'total_factory_employment': country.total_factory_employment,
            'total_rgo_income': country.total_rgo_income,
            'total_rgo_employment': country.total_rgo_employment,
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
    """Wrapper for multiprocessing that catches exceptions."""
    try:
        result = process_single_save(filepath)
        return (filepath, result)
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return (filepath, None)


def main():
    """Main entry point."""
    import argparse
    import time

    arg_parser = argparse.ArgumentParser(description='Process Victoria 2 save files')
    arg_parser.add_argument('--limit', type=int, help='Process only first N files')
    arg_parser.add_argument('--resume', action='store_true', help='Resume from existing partial data')
    arg_parser.add_argument('--batch-size', type=int, default=50, help='Save progress every N files')
    args = arg_parser.parse_args()

    saves_dir = Path(__file__).parent / 'saves'
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)

    # Get all save files sorted by date
    save_files = sorted(saves_dir.glob('*.txt'), key=lambda p: date_sort_key(p.name))

    if not save_files:
        print("No save files found in 'saves' directory.")
        return

    if args.limit:
        save_files = save_files[:args.limit]

    print(f"Found {len(save_files)} save files to process")

    # Check for existing partial data
    partial_file = output_dir / 'economic_data_partial.json'
    all_data = []
    processed_dates = set()

    if args.resume and partial_file.exists():
        print("Loading existing partial data...")
        with open(partial_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        processed_dates = {entry['date'] for entry in all_data}
        print(f"Loaded {len(all_data)} previously processed entries")

    # Process files
    failed = []
    start_time = time.time()

    for i, filepath in enumerate(save_files):
        # Check if already processed
        filename_date = Path(filepath).stem
        if filename_date in processed_dates:
            print(f"[{i+1}/{len(save_files)}] Skipping {filename_date} (already processed)")
            continue

        print(f"[{i+1}/{len(save_files)}] ", end='', flush=True)
        try:
            result = process_single_save(str(filepath))
            all_data.append(result)

            # Save progress periodically
            if len(all_data) % args.batch_size == 0:
                elapsed = time.time() - start_time
                rate = len(all_data) / elapsed if elapsed > 0 else 0
                remaining = len(save_files) - i - 1
                eta = remaining / rate / 60 if rate > 0 else 0
                print(f"  Progress: {len(all_data)} processed, ~{eta:.0f} min remaining")

                # Save partial results
                with open(partial_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f)

        except Exception as e:
            print(f"Error: {e}")
            failed.append(str(filepath))

    elapsed_total = time.time() - start_time
    print(f"\nProcessed {len(all_data)} files in {elapsed_total/60:.1f} minutes")
    print(f"Failed: {len(failed)}")

    if failed:
        print("Failed files:")
        for f in failed[:10]:
            print(f"  {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    # Sort by date
    all_data.sort(key=lambda x: parse_date(x['date']) if x['date'] else (0, 0, 0))

    # Write full data to JSON
    output_file = output_dir / 'economic_data.json'
    print(f"Writing full data to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)

    # Remove partial file if complete
    if partial_file.exists():
        partial_file.unlink()

    # Create time series for easier analysis
    create_time_series(all_data, output_dir)

    print("Done!")


def create_time_series(all_data: list[dict], output_dir: Path):
    """Create separate time series files for different data categories."""

    # World market prices over time
    prices_series = []
    for entry in all_data:
        prices_series.append({
            'date': entry['date'],
            **entry['world_market']['prices']
        })

    with open(output_dir / 'world_market_prices.json', 'w', encoding='utf-8') as f:
        json.dump(prices_series, f, indent=2)

    # World market supply over time
    supply_series = []
    for entry in all_data:
        supply_series.append({
            'date': entry['date'],
            **entry['world_market']['supply']
        })

    with open(output_dir / 'world_market_supply.json', 'w', encoding='utf-8') as f:
        json.dump(supply_series, f, indent=2)

    # World market actual_sold (demand proxy) over time
    sold_series = []
    for entry in all_data:
        sold_series.append({
            'date': entry['date'],
            **entry['world_market']['actual_sold']
        })

    with open(output_dir / 'world_market_sold.json', 'w', encoding='utf-8') as f:
        json.dump(sold_series, f, indent=2)

    # Global statistics over time
    global_series = []
    for entry in all_data:
        gs = entry['global_statistics']
        global_series.append({
            'date': entry['date'],
            'total_population': gs['total_population'],
            'total_pop_money': gs['total_pop_money'],
            'total_pop_bank_savings': gs['total_pop_bank_savings'],
            'avg_life_needs': gs['avg_life_needs'],
            'avg_everyday_needs': gs['avg_everyday_needs'],
            'avg_luxury_needs': gs['avg_luxury_needs'],
            'avg_literacy': gs['avg_literacy'],
            'avg_consciousness': gs['avg_consciousness'],
            'avg_militancy': gs['avg_militancy'],
        })

    with open(output_dir / 'global_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(global_series, f, indent=2)

    # Population by type over time
    pop_type_series = []
    for entry in all_data:
        pop_type_series.append({
            'date': entry['date'],
            **entry['global_statistics']['population_by_type']
        })

    with open(output_dir / 'global_population_by_type.json', 'w', encoding='utf-8') as f:
        json.dump(pop_type_series, f, indent=2)

    # Get list of all countries that appear
    all_countries = set()
    for entry in all_data:
        all_countries.update(entry['countries'].keys())

    # Per-country time series
    country_series = {tag: [] for tag in all_countries}

    for entry in all_data:
        date = entry['date']
        for tag in all_countries:
            if tag in entry['countries']:
                c = entry['countries'][tag]
                country_series[tag].append({
                    'date': date,
                    'treasury': c['treasury'],
                    'bank_reserves': c['bank_reserves'],
                    'prestige': c['prestige'],
                    'infamy': c['infamy'],
                    'total_tax_income': c['total_tax_income'],
                    'total_factory_count': c['total_factory_count'],
                    'total_factory_levels': c['total_factory_levels'],
                    'total_factory_income': c['total_factory_income'],
                    'total_factory_employment': c['total_factory_employment'],
                    'total_rgo_income': c['total_rgo_income'],
                    'total_rgo_employment': c['total_rgo_employment'],
                    'population_total': c['population']['total'],
                    'pop_money': c['population']['total_money'],
                    'pop_bank_savings': c['population']['total_bank_savings'],
                    'avg_life_needs': c['population']['avg_life_needs'],
                    'avg_everyday_needs': c['population']['avg_everyday_needs'],
                    'avg_literacy': c['population']['avg_literacy'],
                })
            else:
                # Country doesn't exist at this date
                country_series[tag].append({
                    'date': date,
                    'exists': False
                })

    # Write country data
    countries_dir = output_dir / 'countries'
    countries_dir.mkdir(exist_ok=True)

    for tag, series in country_series.items():
        # Only write if country has any real data
        if any('treasury' in entry for entry in series):
            with open(countries_dir / f'{tag}.json', 'w', encoding='utf-8') as f:
                json.dump(series, f, indent=2)

    # Create summary CSV for easier spreadsheet import
    create_summary_csv(all_data, output_dir)


def create_summary_csv(all_data: list[dict], output_dir: Path):
    """Create CSV summary files."""
    import csv

    # Global summary
    with open(output_dir / 'global_summary.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = [
            'date', 'total_population', 'total_pop_money', 'total_pop_bank_savings',
            'avg_life_needs', 'avg_everyday_needs', 'avg_luxury_needs',
            'avg_literacy', 'avg_consciousness', 'avg_militancy'
        ]
        writer.writerow(headers)

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

    # Major countries summary (top 20 by final population)
    # Get final populations
    final_entry = all_data[-1] if all_data else {}
    final_countries = final_entry.get('countries', {})
    sorted_countries = sorted(
        final_countries.items(),
        key=lambda x: x[1].get('population', {}).get('total', 0),
        reverse=True
    )[:20]
    major_country_tags = [tag for tag, _ in sorted_countries]

    with open(output_dir / 'major_countries_summary.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
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
                    row.extend([0, 0, 0, 0, 0, 0, 0])
            writer.writerow(row)


if __name__ == '__main__':
    main()
