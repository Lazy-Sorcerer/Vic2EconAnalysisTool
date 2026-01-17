"""
Master script to generate all Victoria 2 economic visualizations.

This is the main entry point for generating charts from processed save data.
It orchestrates the generation of charts across all categories:
- Global statistics (world population, wealth, welfare)
- World market (commodity prices, supply, demand)
- Country comparisons (major powers side-by-side)
- Individual country charts (per-country economic profiles)

QUICK START
===========

Generate all charts:
    $ cd viz
    $ python plot_all.py

Generate specific categories:
    $ python plot_all.py --global      # World-level statistics
    $ python plot_all.py --market      # Commodity market charts
    $ python plot_all.py --countries   # All country charts
    $ python plot_all.py --country ENG # Just England

Output to a subfolder (useful for multiple game sessions):
    $ python plot_all.py --subfolder MP_game_01  # Output to charts/MP_game_01/

COMMAND-LINE OPTIONS
====================

    --all              Generate all charts (default if no options given)
    --global           Generate global statistics charts (charts/global/)
    --market           Generate world market charts (charts/market/)
    --countries        Generate all country + comparison charts
    --comparisons      Generate comparison charts only (charts/comparisons/)
    --country TAG      Generate charts for a specific country (e.g., ENG, FRA)
    --subfolder NAME   Output to charts/NAME/ instead of charts/

OUTPUT DIRECTORY STRUCTURE
==========================

After running, charts are organized as:

    charts/
    ├── global/           # World-level statistics
    │   ├── global_total_population.png
    │   ├── population_by_type.png
    │   ├── total_wealth.png
    │   ├── all_needs.png
    │   └── ...
    │
    ├── market/           # Commodity market data
    │   ├── market_prices_raw.png
    │   ├── market_prices_industrial.png
    │   ├── full_iron.png
    │   ├── category_comparison.png
    │   └── ...
    │
    ├── comparisons/      # Cross-country comparisons
    │   ├── comparison_treasury.png
    │   ├── comparison_prestige.png
    │   ├── comparison_gdp_proxy.png
    │   └── ...
    │
    └── countries/        # Per-country charts
        ├── ENG/
        │   ├── treasury.png
        │   ├── prestige.png
        │   ├── overview.png
        │   └── ...
        ├── FRA/
        ├── PRU/
        └── ...

CHART TYPES GENERATED
=====================

Global (15+ charts):
    - Population: total, by type, composition percentages
    - Wealth: cash, bank savings, total wealth
    - Welfare: life/everyday/luxury needs satisfaction
    - Social: literacy, consciousness, militancy

Market (100+ charts):
    - By category: raw, agricultural, industrial, consumer, military
    - Price charts, supply charts, sold quantity charts
    - Price indices (base year = 100)
    - Supply/demand balance (surplus %)
    - Full commodity analysis (4-panel per commodity)

Countries (20+ charts per country):
    - Finances: treasury, bank reserves
    - Standing: prestige, infamy
    - Industry: factory count/levels/income/employment
    - RGO: income, employment
    - Population and wealth
    - Welfare indicators
    - Overview (6-panel summary)

Comparisons (25+ charts):
    - All statistics compared across great powers
    - GDP proxy and per-capita comparisons
    - Industrialization index
    - Wealth comparisons

DEPENDENCIES
============

Requires:
    - matplotlib (chart generation)
    - numpy (trend lines, calculations)
    - Processed data in output/ directory

Run process_saves.py first to create the required JSON files.

Author: Victoria 2 Economy Analysis Tool Project
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
# This allows running the script from the viz/ directory
sys.path.insert(0, str(Path(__file__).parent))

# Import the plotting modules
from plot_global import plot_all as plot_global_all
from plot_market import plot_all as plot_market_all
from plot_countries import (
    plot_all as plot_countries_all,
    plot_country_profile,
    plot_all_comparisons,
    plot_all_countries,
)
from utils import set_charts_base_dir


def main():
    """
    Main entry point for the visualization generator.

    Parses command-line arguments and dispatches to the appropriate
    plotting modules based on user selection.

    Default behavior (no arguments): Generate all charts.

    The script prints progress information showing which section
    is being processed and where output files are saved.
    """
    # ==== ARGUMENT PARSING ====
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
  python plot_all.py                           # Generate all charts
  python plot_all.py --global                  # Generate global statistics only
  python plot_all.py --market                  # Generate world market charts only
  python plot_all.py --countries               # Generate all country + comparison charts
  python plot_all.py --comparisons             # Generate comparison charts only
  python plot_all.py --country ENG             # Generate charts for England only
  python plot_all.py --subfolder MP_game_01    # Output to charts/MP_game_01/
        """
    )

    # Define command-line options
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
    parser.add_argument('--subfolder', type=str,
                       help='Output subfolder within charts/ (e.g., MP_game_01)')

    args = parser.parse_args()

    # Set custom output subfolder if specified
    if args.subfolder:
        set_charts_base_dir(args.subfolder)

    # ==== DEFAULT TO --all IF NO OPTIONS ====
    if not any([args.do_global, args.market, args.countries, args.comparisons,
                args.country, args.all]):
        args.all = True

    # ==== PRINT HEADER ====
    print("=" * 60)
    print("Victoria 2 Economic Data Visualization")
    if args.subfolder:
        print(f"Output subfolder: {args.subfolder}")
    print("=" * 60)

    # ==== DETERMINE SECTIONS TO GENERATE ====
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
            # Countries includes comparisons for context
            sections.append('comparisons')
            sections.append('countries')

    # ==== GENERATE CHARTS BY SECTION ====
    section_num = 1
    total_sections = len(sections) + (1 if args.country else 0)

    # Global statistics
    if 'global' in sections:
        print(f"\n[{section_num}/{total_sections}] GLOBAL STATISTICS -> charts/global/")
        print("-" * 40)
        plot_global_all()
        section_num += 1

    # World market
    if 'market' in sections:
        print(f"\n[{section_num}/{total_sections}] WORLD MARKET -> charts/market/")
        print("-" * 40)
        plot_market_all()
        section_num += 1

    # Country comparisons
    if 'comparisons' in sections:
        print(f"\n[{section_num}/{total_sections}] COUNTRY COMPARISONS -> charts/comparisons/")
        print("-" * 40)
        plot_all_comparisons()
        section_num += 1

    # Individual country charts
    if 'countries' in sections:
        print(f"\n[{section_num}/{total_sections}] INDIVIDUAL COUNTRIES -> charts/countries/*/")
        print("-" * 40)
        plot_all_countries()
        section_num += 1

    # Single country profile
    if args.country:
        print(f"\n[{section_num}/{total_sections}] COUNTRY: {args.country} -> charts/countries/{args.country}/")
        print("-" * 40)
        plot_country_profile(args.country)

    # ==== PRINT SUMMARY ====
    print("\n" + "=" * 60)
    base_path = f"charts/{args.subfolder}" if args.subfolder else "charts"
    print(f"Charts saved to '{base_path}/' directory:")
    print(f"  {base_path}/global/        - Global statistics")
    print(f"  {base_path}/market/        - World market data")
    print(f"  {base_path}/comparisons/   - Country comparisons")
    print(f"  {base_path}/countries/*/   - Individual country data")
    print("=" * 60)


if __name__ == '__main__':
    main()
