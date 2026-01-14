"""
Generate all visualizations for Victoria 2 economic data.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from plot_global import plot_all as plot_global_all
from plot_market import plot_all as plot_market_all
from plot_countries import plot_all as plot_countries_all, plot_country_profile


def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 2 economic visualizations')
    parser.add_argument('--global', dest='do_global', action='store_true',
                       help='Generate global statistics charts')
    parser.add_argument('--market', action='store_true',
                       help='Generate world market charts')
    parser.add_argument('--countries', action='store_true',
                       help='Generate country comparison charts')
    parser.add_argument('--country', type=str,
                       help='Generate profile for specific country (e.g., ENG)')
    parser.add_argument('--all', action='store_true',
                       help='Generate all charts')

    args = parser.parse_args()

    # If no arguments, default to --all
    if not any([args.do_global, args.market, args.countries, args.country, args.all]):
        args.all = True

    if args.all or args.do_global:
        plot_global_all()

    if args.all or args.market:
        plot_market_all()

    if args.all or args.countries:
        plot_countries_all()

    if args.country:
        plot_country_profile(args.country)

    print("\nAll charts saved to 'charts/' directory")


if __name__ == '__main__':
    main()
