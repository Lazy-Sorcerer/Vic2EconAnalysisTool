"""
Generate all visualizations for Victoria 2 economic data.

This script generates comprehensive charts covering:
- Global Statistics: population, wealth, needs satisfaction, social indicators
- World Market: prices, supply, sold quantities for all commodities
- Country Statistics: individual charts for every country in the dataset
- Comparisons: cross-country comparisons for major powers

Output structure:
  charts/
    global/           - World-level statistics
    market/           - Commodity market data
    countries/TAG/    - Per-country statistics (one folder per country)
    comparisons/      - Cross-country comparison charts
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from plot_global import plot_all as plot_global_all
from plot_market import plot_all as plot_market_all
from plot_countries import (
    plot_all as plot_countries_all,
    plot_country_profile,
    plot_all_comparisons,
    plot_all_countries,
)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Victoria 2 economic visualizations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output structure:
  charts/global/          - World-level statistics
  charts/market/          - Commodity market data
  charts/countries/TAG/   - Per-country statistics
  charts/comparisons/     - Cross-country comparisons

Examples:
  python plot_all.py                  # Generate all charts
  python plot_all.py --global         # Generate global statistics only
  python plot_all.py --market         # Generate world market charts only
  python plot_all.py --countries      # Generate all country + comparison charts
  python plot_all.py --comparisons    # Generate comparison charts only
  python plot_all.py --country ENG    # Generate charts for England only
        """
    )
    parser.add_argument('--global', dest='do_global', action='store_true',
                       help='Generate global statistics charts (charts/global/)')
    parser.add_argument('--market', action='store_true',
                       help='Generate world market charts (charts/market/)')
    parser.add_argument('--countries', action='store_true',
                       help='Generate all country charts (charts/countries/*/)')
    parser.add_argument('--comparisons', action='store_true',
                       help='Generate comparison charts only (charts/comparisons/)')
    parser.add_argument('--country', type=str,
                       help='Generate charts for specific country (e.g., ENG)')
    parser.add_argument('--all', action='store_true',
                       help='Generate all charts')

    args = parser.parse_args()

    # If no arguments, default to --all
    if not any([args.do_global, args.market, args.countries, args.comparisons,
                args.country, args.all]):
        args.all = True

    print("=" * 60)
    print("Victoria 2 Economic Data Visualization")
    print("=" * 60)

    sections = []
    if args.all:
        sections = ['global', 'market', 'comparisons', 'countries']
    else:
        if args.do_global:
            sections.append('global')
        if args.market:
            sections.append('market')
        if args.comparisons:
            sections.append('comparisons')
        if args.countries:
            sections.append('comparisons')
            sections.append('countries')

    section_num = 1
    total_sections = len(sections) + (1 if args.country else 0)

    if 'global' in sections:
        print(f"\n[{section_num}/{total_sections}] GLOBAL STATISTICS -> charts/global/")
        print("-" * 40)
        plot_global_all()
        section_num += 1

    if 'market' in sections:
        print(f"\n[{section_num}/{total_sections}] WORLD MARKET -> charts/market/")
        print("-" * 40)
        plot_market_all()
        section_num += 1

    if 'comparisons' in sections:
        print(f"\n[{section_num}/{total_sections}] COUNTRY COMPARISONS -> charts/comparisons/")
        print("-" * 40)
        plot_all_comparisons()
        section_num += 1

    if 'countries' in sections:
        print(f"\n[{section_num}/{total_sections}] INDIVIDUAL COUNTRIES -> charts/countries/*/")
        print("-" * 40)
        plot_all_countries()
        section_num += 1

    if args.country:
        print(f"\n[{section_num}/{total_sections}] COUNTRY: {args.country} -> charts/countries/{args.country}/")
        print("-" * 40)
        plot_country_profile(args.country)

    print("\n" + "=" * 60)
    print("Charts saved to 'charts/' directory:")
    print("  charts/global/        - Global statistics")
    print("  charts/market/        - World market data")
    print("  charts/comparisons/   - Country comparisons")
    print("  charts/countries/*/   - Individual country data")
    print("=" * 60)


if __name__ == '__main__':
    main()
