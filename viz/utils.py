"""
Utility functions for Victoria 2 data visualization.

This module provides shared functionality for all visualization scripts:
- Data loading from processed JSON files
- Country tag succession handling (e.g., PRU → NGF → GER)
- Matplotlib styling and formatting
- Color palettes for countries, POP types, and commodities
- Chart saving with organized directory structure

VISUALIZATION ARCHITECTURE
==========================

```
viz/
├── utils.py          # This file - shared utilities
├── plot_all.py       # Master script (entry point)
├── plot_global.py    # World-level statistics
├── plot_market.py    # Commodity market analysis
└── plot_countries.py # Country-specific and comparison charts

charts/               # Output directory
├── global/           # World population, wealth, welfare
├── market/           # Commodity prices, supply, demand
├── comparisons/      # Cross-country comparison charts
└── countries/        # Per-country subdirectories
    ├── ENG/
    ├── FRA/
    └── ...
```

TAG SUCCESSION SYSTEM
=====================

Victoria 2 has country formations where nations change their tag:
- Prussia (PRU) → North German Federation (NGF) → Germany (GER)
- Austria (AUS) → South German Federation (SGF) → Austria-Hungary (KUK)

The load_country_group() function handles this by:
1. Loading data from all related tags
2. For each date, selecting the "most advanced" tag that exists
3. Returning a continuous time series

Example:
    >>> data = load_country_group('GER')
    # Returns PRU data until NGF forms, then NGF until GER forms, then GER

MATPLOTLIB STYLE
================

Uses the 'ggplot' style with customizations:
- 12x6 inch figures
- Light gray axes background (#f5f5f5)
- White grid lines
- Consistent font sizes for titles, labels, legends

Color Palettes:
- COUNTRY_COLORS: Distinctive colors for major nations
- POP_TYPE_COLORS: Colors representing each of 14 POP types
- COMMODITY_COLORS: Colors for raw/industrial/consumer goods

USAGE EXAMPLES
==============

Loading data:
    >>> from viz.utils import load_json, load_country_group
    >>> global_stats = load_json('global_statistics.json')
    >>> germany = load_country_group('GER')  # Includes PRU, NGF, GER

Creating charts:
    >>> from viz.utils import setup_style, save_chart
    >>> setup_style()
    >>> plt.figure()
    >>> plt.plot(dates, values)
    >>> save_chart('my_chart', subdir='global')

Author: Victoria 2 Economy Analysis Tool Project
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Project root directory (parent of viz/)
ROOT_DIR = Path(__file__).parent.parent

# Directory containing processed JSON data
OUTPUT_DIR = ROOT_DIR / 'output'

# Directory for generated chart images
CHARTS_DIR = ROOT_DIR / 'charts'


# =============================================================================
# DIRECTORY MANAGEMENT
# =============================================================================

def set_charts_base_dir(subfolder: str = None):
    """
    Set the base charts directory, optionally with a subfolder.

    This allows redirecting all chart output to a subfolder, useful for
    organizing charts from different game sessions (e.g., MP games).

    Args:
        subfolder: Optional subfolder name (e.g., 'MP_game_01')
                   If None, resets to the default 'charts/' directory.

    Examples:
        >>> set_charts_base_dir('MP_game_01')
        # All charts now go to charts/MP_game_01/...

        >>> set_charts_base_dir()
        # Reset to default charts/ directory
    """
    global CHARTS_DIR
    if subfolder:
        CHARTS_DIR = ROOT_DIR / 'charts' / subfolder
    else:
        CHARTS_DIR = ROOT_DIR / 'charts'


def ensure_charts_dir(subdir: str = None) -> Path:
    """
    Create charts directory (and optional subdirectory) if it doesn't exist.

    Args:
        subdir: Optional subdirectory path (e.g., 'global', 'market', 'countries/ENG')
                Can include nested paths separated by /

    Returns:
        Path: Absolute path to the target directory

    Examples:
        >>> ensure_charts_dir()
        PosixPath('.../charts')

        >>> ensure_charts_dir('global')
        PosixPath('.../charts/global')

        >>> ensure_charts_dir('countries/ENG')
        PosixPath('.../charts/countries/ENG')

    Note:
        Uses parents=True to create nested directories as needed.
    """
    target = CHARTS_DIR
    if subdir:
        target = CHARTS_DIR / subdir
    target.mkdir(parents=True, exist_ok=True)
    return target


# =============================================================================
# DATA LOADING
# =============================================================================

def load_json(filename: str) -> Any:
    """
    Load a JSON file from the output directory.

    Args:
        filename: Name of the JSON file (e.g., 'global_statistics.json')

    Returns:
        The parsed JSON data (typically a list or dict)

    Example:
        >>> stats = load_json('global_statistics.json')
        >>> print(stats[0]['date'])
        1836.1.1

    Available Files:
        - global_statistics.json: World aggregates
        - global_population_by_type.json: POP distribution
        - world_market_prices.json: Commodity prices
        - world_market_supply.json: Commodity supply
        - world_market_sold.json: Quantities sold
    """
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_country(tag: str) -> list[dict]:
    """
    Load country-specific data from the countries/ subdirectory.

    Args:
        tag: 3-letter country tag (e.g., 'ENG', 'FRA', 'PRU')

    Returns:
        list[dict]: Time series data for the country

    Raises:
        FileNotFoundError: If no data exists for this country

    Example:
        >>> england = load_country('ENG')
        >>> print(england[0]['treasury'])
        50000.0
    """
    filepath = OUTPUT_DIR / 'countries' / f'{tag}.json'
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
# COUNTRY TAG SUCCESSION SYSTEM
# =============================================================================

# Tag groups: lists of tags representing the same nation across formations
# The last tag (e.g., 'GER') is the "final" form
# When plotting, later tags take precedence for overlapping dates
TAG_GROUPS = {
    # Prussia → North German Federation → Germany
    # PRU forms NGF in 1867, NGF forms GER in 1871
    'GER': ['PRU', 'NGF', 'GER'],

    # Austria → South German Federation → Austria-Hungary
    # AUS can form SGF or become KUK (Austria-Hungary) in 1867
    'KUK': ['AUS', 'SGF', 'KUK'],
}

# Reverse lookup: given any tag, find its group
# Example: TAG_TO_GROUP['PRU'] = 'GER'
TAG_TO_GROUP = {}
for group_name, tags in TAG_GROUPS.items():
    for tag in tags:
        TAG_TO_GROUP[tag] = group_name


def get_display_name(tag: str) -> str:
    """
    Get display name for a tag (group name if part of a group).

    For tags that are part of a succession chain, returns the final
    form's tag for consistent labeling in charts.

    Args:
        tag: Original tag (e.g., 'PRU', 'NGF', 'GER')

    Returns:
        str: Display name (e.g., 'GER' for all German succession tags)

    Examples:
        >>> get_display_name('PRU')
        'GER'
        >>> get_display_name('ENG')
        'ENG'  # Not part of a group
    """
    return TAG_TO_GROUP.get(tag, tag)


def country_exists(entry: dict) -> bool:
    """
    Check if a country actually exists (not just a placeholder).

    A country is considered to exist if it has positive population.
    This is used to filter out placeholder entries for countries
    that don't exist at a given date.

    Args:
        entry: Country data entry from the time series

    Returns:
        bool: True if country has population > 0

    Example:
        >>> entry = {'population_total': 10000000, 'treasury': 50000}
        >>> country_exists(entry)
        True

        >>> entry = {'exists': False}
        >>> country_exists(entry)
        False
    """
    pop = entry.get('population_total', 0)
    if isinstance(pop, dict):
        pop = pop.get('total', 0)
    return pop > 0


def load_country_group(group_or_tag: str) -> list[dict]:
    """
    Load country data, merging multiple tags if they form a group.

    For succession chains (e.g., PRU → NGF → GER), this function:
    1. Loads data from all tags in the chain
    2. For each date, keeps data from the most advanced tag that exists
    3. Returns a continuous time series

    Args:
        group_or_tag: Either a group name ('GER') or individual tag ('PRU')

    Returns:
        list[dict]: Merged time series data, sorted by date

    Examples:
        >>> # Load Germany (includes PRU, NGF, GER data)
        >>> germany = load_country_group('GER')
        >>> # Early dates will have PRU data, later dates have GER

        >>> # Load a non-group country
        >>> england = load_country_group('ENG')
        >>> # Just returns ENG data

    Algorithm:
        For each date, store (tag_index, entry) where tag_index is the
        position in the succession chain. Later tags (higher index)
        take precedence. This ensures GER > NGF > PRU when data exists
        for multiple tags on the same date.
    """
    # Determine which tags to load
    if group_or_tag in TAG_GROUPS:
        # Group name provided (e.g., 'GER')
        tags = TAG_GROUPS[group_or_tag]
    elif group_or_tag in TAG_TO_GROUP:
        # Individual tag that's part of a group (e.g., 'PRU')
        tags = TAG_GROUPS[TAG_TO_GROUP[group_or_tag]]
    else:
        # Not part of any group (e.g., 'ENG')
        tags = [group_or_tag]

    # Load data from all tags, indexed by date
    # Format: {date: (tag_index, entry)}
    all_data = {}

    for tag_idx, tag in enumerate(tags):
        try:
            data = load_country(tag)
            for entry in data:
                # Only include entries where country actually exists
                if 'treasury' in entry and country_exists(entry):
                    date = entry['date']
                    if date not in all_data:
                        all_data[date] = (tag_idx, entry)
                    else:
                        # Later tags in succession take precedence
                        # (GER > NGF > PRU)
                        existing_tag_idx, _ = all_data[date]
                        if tag_idx > existing_tag_idx:
                            all_data[date] = (tag_idx, entry)
        except FileNotFoundError:
            # Tag data doesn't exist (country never formed)
            continue

    # Sort by date and return just the entries
    sorted_dates = sorted(all_data.keys(), key=lambda d: parse_date(d))
    return [all_data[d][1] for d in sorted_dates]


# =============================================================================
# DATE HANDLING
# =============================================================================

def parse_date(date_str: str) -> datetime:
    """
    Parse Victoria 2 date string to Python datetime.

    Args:
        date_str: Date in "YYYY.M.D" format

    Returns:
        datetime: Python datetime object

    Examples:
        >>> parse_date("1836.1.1")
        datetime.datetime(1836, 1, 1, 0, 0)

        >>> parse_date("1900.12.31")
        datetime.datetime(1900, 12, 31, 0, 0)
    """
    parts = date_str.split('.')
    return datetime(int(parts[0]), int(parts[1]), int(parts[2]))


def get_dates_and_values(data: list[dict], value_key: str) -> tuple[list[datetime], list[float]]:
    """
    Extract dates and values from time series data.

    Convenience function for preparing data for matplotlib plotting.
    Filters out entries that don't have the specified key.

    Args:
        data: List of time series entries with 'date' and value keys
        value_key: Name of the value to extract (e.g., 'treasury')

    Returns:
        tuple: (list of datetime objects, list of float values)

    Example:
        >>> data = [{'date': '1836.1.1', 'treasury': 50000},
        ...         {'date': '1836.2.1', 'treasury': 52000}]
        >>> dates, values = get_dates_and_values(data, 'treasury')
        >>> plt.plot(dates, values)
    """
    dates = []
    values = []
    for entry in data:
        if value_key in entry:
            dates.append(parse_date(entry['date']))
            values.append(entry[value_key])
    return dates, values


# =============================================================================
# MATPLOTLIB STYLING
# =============================================================================

def setup_style():
    """
    Setup matplotlib style for consistent charts.

    Applies the 'ggplot' base style with customizations:
    - Figure size: 12x6 inches (landscape, good for time series)
    - Font sizes: 10pt base, 14pt titles, 12pt labels
    - DPI: 100 (screen quality, save_chart uses 150 for files)
    - Background: Light gray (#f5f5f5) with white grid lines

    Call this once at the start of visualization scripts:
        >>> setup_style()
        >>> # Now create figures with consistent styling
    """
    plt.style.use('ggplot')

    # Figure dimensions and quality
    plt.rcParams['figure.figsize'] = (12, 6)   # Landscape format
    plt.rcParams['figure.dpi'] = 100            # Screen resolution
    plt.rcParams['figure.facecolor'] = 'white'  # White figure background

    # Font sizes
    plt.rcParams['font.size'] = 10              # Base font size
    plt.rcParams['axes.titlesize'] = 14         # Chart titles
    plt.rcParams['axes.labelsize'] = 12         # Axis labels
    plt.rcParams['legend.fontsize'] = 10        # Legend text

    # Axes styling
    plt.rcParams['axes.facecolor'] = '#f5f5f5'  # Light gray plot area
    plt.rcParams['grid.color'] = 'white'        # White grid lines
    plt.rcParams['grid.linewidth'] = 1.5        # Visible grid


def format_date_axis(ax, data_dates: list[datetime]):
    """
    Format x-axis for date display with appropriate intervals.

    Automatically selects major and minor tick intervals based on
    the time span of the data:
    - >50 years: Major every 10 years, minor every 5
    - >20 years: Major every 5 years, minor every 1
    - ≤20 years: Major every 2 years, minor every 1

    Args:
        ax: Matplotlib axes object
        data_dates: List of datetime objects being plotted
                   (used to calculate span)

    Example:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(dates, values)
        >>> format_date_axis(ax, dates)
    """
    # Calculate time span in years
    years_span = (data_dates[-1] - data_dates[0]).days / 365

    # Choose appropriate tick intervals
    if years_span > 50:
        ax.xaxis.set_major_locator(mdates.YearLocator(10))
        ax.xaxis.set_minor_locator(mdates.YearLocator(5))
    elif years_span > 20:
        ax.xaxis.set_major_locator(mdates.YearLocator(5))
        ax.xaxis.set_minor_locator(mdates.YearLocator(1))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_minor_locator(mdates.YearLocator(1))

    # Format as 4-digit year
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Rotate labels for readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')


def format_large_numbers(ax, axis='y'):
    """
    Format axis to show large numbers in abbreviated form.

    Uses K/M/B suffixes for thousands/millions/billions:
    - 1,000 → 1.0K
    - 1,000,000 → 1.0M
    - 1,000,000,000 → 1.0B

    Args:
        ax: Matplotlib axes object
        axis: Which axis to format ('y' or 'x')

    Example:
        >>> ax.plot(dates, population)  # Population in millions
        >>> format_large_numbers(ax, 'y')  # Shows "50.0M" instead of "50000000"
    """
    from matplotlib.ticker import FuncFormatter

    def formatter(x, pos):
        """Format number with K/M/B suffix."""
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


# =============================================================================
# CHART SAVING
# =============================================================================

def save_chart(name: str, tight: bool = True, subdir: str = None):
    """
    Save current figure to charts directory.

    Args:
        name: Chart filename (without extension, .png added automatically)
        tight: Whether to apply tight_layout (default True)
        subdir: Optional subdirectory (e.g., 'global', 'market', 'countries/ENG')

    Output:
        Saves PNG file at 150 DPI with tight bounding box

    Examples:
        >>> plt.plot(dates, values)
        >>> save_chart('population')  # → charts/population.png

        >>> save_chart('treasury', subdir='countries/ENG')
        # → charts/countries/ENG/treasury.png

    Note:
        Closes the figure after saving to free memory.
        Important for batch chart generation.
    """
    target_dir = ensure_charts_dir(subdir)
    if tight:
        plt.tight_layout()
    plt.savefig(target_dir / f'{name}.png', dpi=150, bbox_inches='tight')
    plt.close()


# =============================================================================
# COLOR PALETTES
# =============================================================================

# Country colors - distinctive, historically/flag-inspired
COUNTRY_COLORS = {
    # Great Powers
    'ENG': '#C8102E',  # Red (Union Jack)
    'FRA': '#0055A4',  # Blue (Tricolore)
    'RUS': '#009B3A',  # Green (Imperial)
    'USA': '#3C3B6E',  # Navy blue (Stars and Stripes)

    # German succession (all dark gray/black - Prussian tradition)
    'PRU': '#1E1E1E',  # Prussia
    'NGF': '#1E1E1E',  # North German Federation
    'GER': '#1E1E1E',  # German Empire

    # Austrian succession (all khaki/Habsburg yellow)
    'AUS': '#F0E68C',  # Austria
    'SGF': '#F0E68C',  # South German Federation
    'KUK': '#F0E68C',  # Austria-Hungary

    # Other major powers
    'JAP': '#BC002D',  # Crimson (Rising Sun)
    'ITA': '#009246',  # Green (Italian flag)
    'SPA': '#F1BF00',  # Yellow/Gold (Spanish flag)
    'TUR': '#E30A17',  # Red (Ottoman)
    'CHI': '#FFDE00',  # Yellow (Qing)
    'BRA': '#009739',  # Green (Brazilian flag)
}

# POP type colors - visually distinct for stacked charts
POP_TYPE_COLORS = {
    # Upper class (darker, richer colors)
    'aristocrats': '#800080',    # Purple - royalty/nobility
    'capitalists': '#FFD700',    # Gold - wealth
    'officers': '#DC143C',       # Crimson - military brass

    # Middle class (blues and business tones)
    'artisans': '#FFA500',       # Orange - craft/trade
    'clerks': '#4169E1',         # Royal Blue - white collar
    'bureaucrats': '#2F4F4F',    # Dark Slate - government
    'clergymen': '#000000',      # Black - religious vestments

    # Working class (earth tones)
    'craftsmen': '#8B4513',      # Saddle Brown - factory work
    'farmers': '#228B22',        # Forest Green - agriculture
    'labourers': '#A0522D',      # Sienna - manual labor
    'soldiers': '#556B2F',       # Dark Olive - military

    # Other
    'slaves': '#696969',         # Dim Gray - unfortunate reality
    'neets': '#778899',          # Light Slate Gray - unemployed (Crimea mod)
}

# Commodity colors by category
COMMODITY_COLORS = {
    # Raw resources (earth tones)
    'coal': '#2F4F4F',           # Dark slate
    'iron': '#708090',           # Slate gray
    'steel': '#4682B4',          # Steel blue
    'timber': '#8B4513',         # Saddle brown
    'grain': '#DAA520',          # Goldenrod
    'cotton': '#FFFAF0',         # Floral white
    'wool': '#F5F5DC',           # Beige

    # Industrial goods (blues and metallics)
    'machine_parts': '#4169E1',  # Royal blue
    'cement': '#A9A9A9',         # Dark gray
    'fertilizer': '#32CD32',     # Lime green
    'explosives': '#FF4500',     # Orange red

    # Consumer goods (varied)
    'fabric': '#DDA0DD',         # Plum
    'furniture': '#D2691E',      # Chocolate
    'liquor': '#8B0000',         # Dark red
    'wine': '#722F37',           # Wine red
    'regular_clothes': '#4682B4', # Steel blue
    'luxury_clothes': '#9400D3',  # Dark violet
}


# =============================================================================
# COLOR ACCESSOR FUNCTIONS
# =============================================================================

def get_country_color(tag: str) -> str:
    """
    Get color for a country, with fallback.

    Args:
        tag: Country tag (e.g., 'ENG', 'FRA')

    Returns:
        str: Hex color code, gray (#888888) if tag not in palette

    Example:
        >>> get_country_color('ENG')
        '#C8102E'
    """
    return COUNTRY_COLORS.get(tag, '#888888')


def get_pop_color(pop_type: str) -> str:
    """
    Get color for a POP type.

    Args:
        pop_type: POP type name (e.g., 'farmers', 'craftsmen')

    Returns:
        str: Hex color code, gray (#888888) if type not in palette

    Example:
        >>> get_pop_color('farmers')
        '#228B22'
    """
    return POP_TYPE_COLORS.get(pop_type, '#888888')


def get_commodity_color(commodity: str) -> str:
    """
    Get color for a commodity.

    Args:
        commodity: Commodity name (e.g., 'iron', 'grain')

    Returns:
        str: Hex color code, gray (#888888) if commodity not in palette

    Example:
        >>> get_commodity_color('iron')
        '#708090'
    """
    return COMMODITY_COLORS.get(commodity, '#888888')
