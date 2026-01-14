"""
Utility functions for Victoria 2 data visualization.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Paths
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / 'output'
CHARTS_DIR = ROOT_DIR / 'charts'


def ensure_charts_dir():
    """Create charts directory if it doesn't exist."""
    CHARTS_DIR.mkdir(exist_ok=True)


def load_json(filename: str) -> Any:
    """Load a JSON file from the output directory."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_country(tag: str) -> list[dict]:
    """Load country-specific data."""
    filepath = OUTPUT_DIR / 'countries' / f'{tag}.json'
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# Country tag groups - tags that represent the same nation across formations
# The first tag is used as the display name
TAG_GROUPS = {
    'GER': ['PRU', 'NGF', 'GER'],      # Prussia → North German Federation → Germany
    'KUK': ['AUS', 'SGF', 'KUK'],      # Austria → South German Federation / Austria-Hungary
}

# Reverse lookup: which group does a tag belong to?
TAG_TO_GROUP = {}
for group_name, tags in TAG_GROUPS.items():
    for tag in tags:
        TAG_TO_GROUP[tag] = group_name


def get_display_name(tag: str) -> str:
    """Get display name for a tag (group name if part of a group)."""
    return TAG_TO_GROUP.get(tag, tag)


def load_country_group(group_or_tag: str) -> list[dict]:
    """
    Load country data, merging multiple tags if they form a group.
    For example, 'GER' will load and merge PRU, NGF, and GER data.
    """
    # Get the tags to load
    if group_or_tag in TAG_GROUPS:
        tags = TAG_GROUPS[group_or_tag]
    elif group_or_tag in TAG_TO_GROUP:
        tags = TAG_GROUPS[TAG_TO_GROUP[group_or_tag]]
    else:
        tags = [group_or_tag]

    # Load all available data
    all_data = {}
    for tag in tags:
        try:
            data = load_country(tag)
            for entry in data:
                if 'treasury' in entry:  # Valid entry
                    date = entry['date']
                    # Use this entry if we don't have data for this date yet,
                    # or if this is a later tag in the succession
                    if date not in all_data:
                        all_data[date] = entry
                    else:
                        # Later tags take precedence (GER over NGF over PRU)
                        current_tag_idx = tags.index(tag) if tag in tags else 0
                        # Check what tag the existing data is from (not stored, so overwrite)
                        all_data[date] = entry
        except FileNotFoundError:
            continue

    # Sort by date and return as list
    sorted_dates = sorted(all_data.keys(), key=lambda d: parse_date(d))
    return [all_data[d] for d in sorted_dates]


def parse_date(date_str: str) -> datetime:
    """Parse Victoria 2 date string to datetime."""
    parts = date_str.split('.')
    return datetime(int(parts[0]), int(parts[1]), int(parts[2]))


def get_dates_and_values(data: list[dict], value_key: str) -> tuple[list[datetime], list[float]]:
    """Extract dates and values from time series data."""
    dates = []
    values = []
    for entry in data:
        if value_key in entry:
            dates.append(parse_date(entry['date']))
            values.append(entry[value_key])
    return dates, values


def setup_style():
    """Setup matplotlib style for consistent charts."""
    plt.style.use('ggplot')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['axes.facecolor'] = '#f5f5f5'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['grid.color'] = 'white'
    plt.rcParams['grid.linewidth'] = 1.5


def format_date_axis(ax, data_dates: list[datetime]):
    """Format x-axis for date display."""
    years_span = (data_dates[-1] - data_dates[0]).days / 365

    if years_span > 50:
        ax.xaxis.set_major_locator(mdates.YearLocator(10))
        ax.xaxis.set_minor_locator(mdates.YearLocator(5))
    elif years_span > 20:
        ax.xaxis.set_major_locator(mdates.YearLocator(5))
        ax.xaxis.set_minor_locator(mdates.YearLocator(1))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_minor_locator(mdates.YearLocator(1))

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')


def format_large_numbers(ax, axis='y'):
    """Format axis to show large numbers in millions/billions."""
    from matplotlib.ticker import FuncFormatter

    def formatter(x, pos):
        if abs(x) >= 1e9:
            return f'{x/1e9:.1f}B'
        elif abs(x) >= 1e6:
            return f'{x/1e6:.1f}M'
        elif abs(x) >= 1e3:
            return f'{x/1e3:.1f}K'
        return f'{x:.0f}'

    if axis == 'y':
        ax.yaxis.set_major_formatter(FuncFormatter(formatter))
    else:
        ax.xaxis.set_major_formatter(FuncFormatter(formatter))


def save_chart(name: str, tight: bool = True):
    """Save current figure to charts directory."""
    ensure_charts_dir()
    if tight:
        plt.tight_layout()
    plt.savefig(CHARTS_DIR / f'{name}.png', dpi=150, bbox_inches='tight')
    plt.close()


# Color palettes
COUNTRY_COLORS = {
    'ENG': '#C8102E',  # Red
    'FRA': '#0055A4',  # Blue
    'PRU': '#000000',  # Black
    'NGF': '#000000',  # Black (North German Federation)
    'GER': '#000000',  # Black (Germany)
    'AUS': '#F0E68C',  # Khaki (Austria)
    'SGF': '#F0E68C',  # Khaki (South German Federation)
    'KUK': '#F0E68C',  # Khaki (Austria-Hungary)
    'RUS': '#009B3A',  # Green
    'USA': '#3C3B6E',  # Navy
    'JAP': '#BC002D',  # Red
    'ITA': '#009246',  # Green
    'SPA': '#F1BF00',  # Yellow
    'TUR': '#E30A17',  # Red
    'CHI': '#FFDE00',  # Yellow
}

POP_TYPE_COLORS = {
    'aristocrats': '#800080',    # Purple
    'capitalists': '#FFD700',    # Gold
    'artisans': '#FFA500',       # Orange
    'clerks': '#4169E1',         # Royal Blue
    'craftsmen': '#8B4513',      # Saddle Brown
    'bureaucrats': '#2F4F4F',    # Dark Slate
    'clergymen': '#000000',      # Black
    'officers': '#DC143C',       # Crimson
    'soldiers': '#556B2F',       # Dark Olive
    'farmers': '#228B22',        # Forest Green
    'labourers': '#A0522D',      # Sienna
    'slaves': '#696969',         # Dim Gray
}

COMMODITY_COLORS = {
    # Raw resources
    'coal': '#2F4F4F',
    'iron': '#708090',
    'steel': '#4682B4',
    'timber': '#8B4513',
    'grain': '#DAA520',
    'cotton': '#FFFAF0',
    'wool': '#F5F5DC',
    # Industrial
    'machine_parts': '#4169E1',
    'cement': '#A9A9A9',
    'fertilizer': '#32CD32',
    'explosives': '#FF4500',
    # Consumer
    'fabric': '#DDA0DD',
    'furniture': '#D2691E',
    'liquor': '#8B0000',
    'wine': '#722F37',
    'regular_clothes': '#4682B4',
    'luxury_clothes': '#9400D3',
}


def get_country_color(tag: str) -> str:
    """Get color for a country, with fallback."""
    return COUNTRY_COLORS.get(tag, '#888888')


def get_pop_color(pop_type: str) -> str:
    """Get color for a POP type."""
    return POP_TYPE_COLORS.get(pop_type, '#888888')


def get_commodity_color(commodity: str) -> str:
    """Get color for a commodity."""
    return COMMODITY_COLORS.get(commodity, '#888888')
