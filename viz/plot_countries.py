"""
Visualizations for country statistics.

Generates:
- Individual charts for each statistic for every country (in charts/countries/TAG/)
- Comparison charts across major powers (in charts/comparisons/)
"""

import matplotlib.pyplot as plt
from pathlib import Path

from utils import (
    load_json,
    load_country,
    load_country_group,
    parse_date,
    setup_style,
    format_date_axis,
    format_large_numbers,
    save_chart,
    get_country_color,
    get_pop_color,
    OUTPUT_DIR,
    TAG_GROUPS,
)


# =============================================================================
# Country Statistics Configuration
# =============================================================================

# All country statistics with their display config
COUNTRY_STATS = {
    # National Finances
    'treasury': {
        'title': 'Treasury',
        'ylabel': '£',
        'color': '#2E86AB',
        'category': 'finances'
    },
    'bank_reserves': {
        'title': 'Bank Reserves',
        'ylabel': '£',
        'color': '#457B9D',
        'category': 'finances'
    },

    # National Standing
    'prestige': {
        'title': 'Prestige',
        'ylabel': 'Points',
        'color': '#A23B72',
        'category': 'standing'
    },
    'infamy': {
        'title': 'Infamy',
        'ylabel': 'Badboy Points',
        'color': '#E63946',
        'category': 'standing'
    },

    # Taxation
    'total_tax_income': {
        'title': 'Total Tax Income',
        'ylabel': '£',
        'color': '#2A9D8F',
        'category': 'taxation'
    },

    # Industrial Sector
    'total_factory_count': {
        'title': 'Factory Count',
        'ylabel': 'Factories',
        'color': '#F18F01',
        'category': 'industry'
    },
    'total_factory_levels': {
        'title': 'Total Factory Levels',
        'ylabel': 'Levels',
        'color': '#C73E1D',
        'category': 'industry'
    },
    'total_factory_income': {
        'title': 'Factory Income',
        'ylabel': '£',
        'color': '#9B2335',
        'category': 'industry'
    },
    'total_factory_employment': {
        'title': 'Factory Employment',
        'ylabel': 'Workers',
        'color': '#8B4513',
        'category': 'industry'
    },

    # Primary Sector (RGO)
    'total_rgo_income': {
        'title': 'RGO Income',
        'ylabel': '£',
        'color': '#228B22',
        'category': 'rgo'
    },
    'total_rgo_employment': {
        'title': 'RGO Employment',
        'ylabel': 'Workers',
        'color': '#556B2F',
        'category': 'rgo'
    },

    # Population
    'population_total': {
        'title': 'Total Population',
        'ylabel': 'People',
        'color': '#1D3557',
        'category': 'population'
    },

    # POP Wealth
    'pop_money': {
        'title': 'POP Cash Holdings',
        'ylabel': '£',
        'color': '#2E86AB',
        'category': 'wealth'
    },
    'pop_bank_savings': {
        'title': 'POP Bank Savings',
        'ylabel': '£',
        'color': '#A23B72',
        'category': 'wealth'
    },

    # Welfare Indicators
    'avg_life_needs': {
        'title': 'Life Needs Satisfaction',
        'ylabel': 'Satisfaction (0-1)',
        'color': '#E63946',
        'ylim': (0, 1),
        'category': 'welfare'
    },
    'avg_everyday_needs': {
        'title': 'Everyday Needs Satisfaction',
        'ylabel': 'Satisfaction (0-1)',
        'color': '#457B9D',
        'ylim': (0, 1),
        'category': 'welfare'
    },
    'avg_luxury_needs': {
        'title': 'Luxury Needs Satisfaction',
        'ylabel': 'Satisfaction (0-1)',
        'color': '#2A9D8F',
        'ylim': (0, 1),
        'category': 'welfare'
    },

    # Social Indicators
    'avg_literacy': {
        'title': 'Literacy Rate',
        'ylabel': 'Rate (0-1)',
        'color': '#1D3557',
        'ylim': (0, 1),
        'category': 'social'
    },
    'avg_consciousness': {
        'title': 'Political Consciousness',
        'ylabel': 'Consciousness (0-10)',
        'color': '#457B9D',
        'ylim': (0, 10),
        'category': 'social'
    },
    'avg_militancy': {
        'title': 'Militancy',
        'ylabel': 'Militancy (0-10)',
        'color': '#E63946',
        'ylim': (0, 10),
        'category': 'social'
    },
}

# Major powers for comparison charts
GREAT_POWERS = ['ENG', 'FRA', 'GER', 'KUK', 'RUS', 'USA', 'SPA', 'TUR', 'CHI', 'JAP']


# =============================================================================
# Helper Functions
# =============================================================================

def get_available_countries() -> list[str]:
    """Get list of all countries with data files."""
    countries_dir = OUTPUT_DIR / 'countries'
    return sorted([f.stem for f in countries_dir.glob('*.json')])


def country_has_data(tag: str) -> bool:
    """Check if a country has meaningful data (not just empty records)."""
    try:
        data = load_country_group(tag)
        if not data:
            return False
        # Check if there's at least some valid data
        for entry in data:
            if entry.get('population_total', 0) > 0:
                return True
        return False
    except (FileNotFoundError, KeyError):
        return False


# =============================================================================
# Individual Country Charts
# =============================================================================

def plot_country_stat(tag: str, stat_key: str, data: list[dict] = None):
    """Plot a single statistic for a country."""
    if data is None:
        data = load_country_group(tag)

    if not data:
        return False

    config = COUNTRY_STATS.get(stat_key)
    if not config:
        return False

    # Filter entries that have this statistic
    valid_entries = [d for d in data if stat_key in d]
    if not valid_entries:
        return False

    setup_style()

    dates = [parse_date(d['date']) for d in valid_entries]
    values = [d[stat_key] for d in valid_entries]

    fig, ax = plt.subplots()

    ax.plot(dates, values, color=config['color'], linewidth=2)
    ax.fill_between(dates, values, alpha=0.3, color=config['color'])

    ax.set_title(f"{tag} - {config['title']}")
    ax.set_xlabel('Year')
    ax.set_ylabel(config['ylabel'])

    if 'ylim' in config:
        ax.set_ylim(config['ylim'])

    format_date_axis(ax, dates)

    # Format large numbers for most stats
    if config['ylabel'] in ['£', 'People', 'Workers', 'Factories', 'Levels']:
        format_large_numbers(ax)

    save_chart(stat_key, subdir=f'countries/{tag}')
    return True


def plot_country_gdp_proxy(tag: str, data: list[dict] = None):
    """Plot GDP proxy (factory + RGO income) for a country."""
    if data is None:
        data = load_country_group(tag)

    if not data:
        return False

    valid_entries = [d for d in data
                     if 'total_factory_income' in d and 'total_rgo_income' in d]
    if not valid_entries:
        return False

    setup_style()

    dates = [parse_date(d['date']) for d in valid_entries]
    values = [d['total_factory_income'] + d['total_rgo_income'] for d in valid_entries]

    fig, ax = plt.subplots()

    ax.plot(dates, values, color='#2A9D8F', linewidth=2)
    ax.fill_between(dates, values, alpha=0.3, color='#2A9D8F')

    ax.set_title(f"{tag} - GDP Proxy (Factory + RGO Income)")
    ax.set_xlabel('Year')
    ax.set_ylabel('£')

    format_date_axis(ax, dates)
    format_large_numbers(ax)

    save_chart('gdp_proxy', subdir=f'countries/{tag}')
    return True


def plot_country_total_wealth(tag: str, data: list[dict] = None):
    """Plot total POP wealth (cash + savings) for a country."""
    if data is None:
        data = load_country_group(tag)

    if not data:
        return False

    valid_entries = [d for d in data if 'pop_money' in d]
    if not valid_entries:
        return False

    setup_style()

    dates = [parse_date(d['date']) for d in valid_entries]
    cash = [d.get('pop_money', 0) for d in valid_entries]
    savings = [d.get('pop_bank_savings', 0) for d in valid_entries]

    fig, ax = plt.subplots()

    ax.stackplot(dates, cash, savings,
                 labels=['Cash', 'Bank Savings'],
                 colors=['#2E86AB', '#A23B72'], alpha=0.8)

    ax.set_title(f"{tag} - Total POP Wealth")
    ax.set_xlabel('Year')
    ax.set_ylabel('£')

    format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='upper left')

    save_chart('total_pop_wealth', subdir=f'countries/{tag}')
    return True


def plot_country_needs_combined(tag: str, data: list[dict] = None):
    """Plot all needs satisfaction on one chart for a country."""
    if data is None:
        data = load_country_group(tag)

    if not data:
        return False

    valid_entries = [d for d in data if 'avg_life_needs' in d]
    if not valid_entries:
        return False

    setup_style()

    dates = [parse_date(d['date']) for d in valid_entries]
    life = [d.get('avg_life_needs', 0) for d in valid_entries]
    everyday = [d.get('avg_everyday_needs', 0) for d in valid_entries]
    luxury = [d.get('avg_luxury_needs', 0) for d in valid_entries]

    fig, ax = plt.subplots()

    ax.plot(dates, life, label='Life', color='#E63946', linewidth=2)
    ax.plot(dates, everyday, label='Everyday', color='#457B9D', linewidth=2)
    ax.plot(dates, luxury, label='Luxury', color='#2A9D8F', linewidth=2)

    ax.set_title(f"{tag} - Needs Satisfaction")
    ax.set_xlabel('Year')
    ax.set_ylabel('Satisfaction (0-1)')
    ax.set_ylim(0, 1)

    format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('all_needs', subdir=f'countries/{tag}')
    return True


def plot_country_industrialization(tag: str, data: list[dict] = None):
    """Plot industrialization index (factories per million pop) for a country."""
    if data is None:
        data = load_country_group(tag)

    if not data:
        return False

    valid_entries = [d for d in data
                     if 'total_factory_count' in d and 'population_total' in d
                     and d.get('population_total', 0) > 0]
    if not valid_entries:
        return False

    setup_style()

    dates = [parse_date(d['date']) for d in valid_entries]
    values = [(d['total_factory_count'] / d['population_total'] * 1_000_000)
              for d in valid_entries]

    fig, ax = plt.subplots()

    ax.plot(dates, values, color='#C73E1D', linewidth=2)
    ax.fill_between(dates, values, alpha=0.3, color='#C73E1D')

    ax.set_title(f"{tag} - Industrialization (Factories per Million Pop)")
    ax.set_xlabel('Year')
    ax.set_ylabel('Factories per Million')

    format_date_axis(ax, dates)

    save_chart('industrialization_index', subdir=f'countries/{tag}')
    return True


def plot_country_overview(tag: str, data: list[dict] = None):
    """Plot a multi-panel overview for a country."""
    if data is None:
        data = load_country_group(tag)

    if not data:
        return False

    valid_data = [d for d in data if 'treasury' in d]
    if not valid_data:
        return False

    setup_style()
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'{tag} Economic Overview', fontsize=16)

    dates = [parse_date(d['date']) for d in valid_data]

    # Treasury
    ax = axes[0, 0]
    values = [d.get('treasury', 0) for d in valid_data]
    ax.plot(dates, values, color='#2E86AB', linewidth=2)
    ax.set_title('Treasury')
    ax.set_ylabel('£')
    format_date_axis(ax, dates)
    format_large_numbers(ax)

    # Prestige
    ax = axes[0, 1]
    values = [d.get('prestige', 0) for d in valid_data]
    ax.plot(dates, values, color='#A23B72', linewidth=2)
    ax.set_title('Prestige')
    format_date_axis(ax, dates)

    # Population
    ax = axes[0, 2]
    values = [d.get('population_total', 0) for d in valid_data]
    ax.plot(dates, values, color='#F18F01', linewidth=2)
    ax.set_title('Population')
    format_date_axis(ax, dates)
    format_large_numbers(ax)

    # Factory count
    ax = axes[1, 0]
    values = [d.get('total_factory_count', 0) for d in valid_data]
    ax.plot(dates, values, color='#C73E1D', linewidth=2)
    ax.set_title('Factory Count')
    format_date_axis(ax, dates)

    # GDP Proxy
    ax = axes[1, 1]
    values = [d.get('total_factory_income', 0) + d.get('total_rgo_income', 0)
              for d in valid_data]
    ax.plot(dates, values, color='#2A9D8F', linewidth=2)
    ax.set_title('GDP Proxy (Factory + RGO Income)')
    ax.set_ylabel('£')
    format_date_axis(ax, dates)
    format_large_numbers(ax)

    # Literacy
    ax = axes[1, 2]
    values = [d.get('avg_literacy', 0) for d in valid_data]
    ax.plot(dates, values, color='#1D3557', linewidth=2)
    ax.set_title('Literacy Rate')
    ax.set_ylim(0, 1)
    format_date_axis(ax, dates)

    save_chart('overview', subdir=f'countries/{tag}')
    return True


def plot_all_country_stats(tag: str):
    """Generate all charts for a single country."""
    data = load_country_group(tag)
    if not data:
        print(f"  No data for {tag}, skipping")
        return 0

    # Check if country has meaningful data
    has_pop = any(d.get('population_total', 0) > 0 for d in data)
    if not has_pop:
        return 0

    count = 0

    # Individual statistic charts
    for stat_key in COUNTRY_STATS:
        if plot_country_stat(tag, stat_key, data):
            count += 1

    # Derived/combined charts
    if plot_country_gdp_proxy(tag, data):
        count += 1
    if plot_country_total_wealth(tag, data):
        count += 1
    if plot_country_needs_combined(tag, data):
        count += 1
    if plot_country_industrialization(tag, data):
        count += 1
    if plot_country_overview(tag, data):
        count += 1

    return count


# =============================================================================
# Comparison Charts
# =============================================================================

def plot_comparison(countries: list[str], stat_key: str, title: str = None,
                    filename: str = None):
    """Compare a statistic across multiple countries."""
    config = COUNTRY_STATS.get(stat_key, {})
    if not config:
        return

    setup_style()
    fig, ax = plt.subplots(figsize=(14, 7))

    all_dates = []

    for tag in countries:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data if stat_key in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [d[stat_key] for d in valid_entries]

        all_dates.extend(dates)

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    if not all_dates:
        plt.close()
        return

    ax.set_title(title or f"{config['title']} Comparison")
    ax.set_xlabel('Year')
    ax.set_ylabel(config.get('ylabel', stat_key.replace('_', ' ').title()))

    if 'ylim' in config:
        ax.set_ylim(config['ylim'])

    format_date_axis(ax, all_dates)

    if config.get('ylabel') in ['£', 'People', 'Workers', 'Factories', 'Levels']:
        format_large_numbers(ax)

    ax.legend(loc='best')

    save_chart(filename or f'comparison_{stat_key}', subdir='comparisons')
    print(f'  Saved: comparisons/{filename or f"comparison_{stat_key}"}.png')


def plot_gdp_comparison():
    """Compare GDP proxy across countries."""
    setup_style()
    fig, ax = plt.subplots(figsize=(14, 7))

    all_dates = []

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data
                         if 'total_factory_income' in d and 'total_rgo_income' in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [d['total_factory_income'] + d['total_rgo_income']
                  for d in valid_entries]

        all_dates.extend(dates)

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    if not all_dates:
        plt.close()
        return

    ax.set_title('GDP Proxy Comparison (Factory + RGO Income)')
    ax.set_xlabel('Year')
    ax.set_ylabel('£')

    format_date_axis(ax, all_dates)
    format_large_numbers(ax)
    ax.legend(loc='best')

    save_chart('comparison_gdp_proxy', subdir='comparisons')
    print('  Saved: comparisons/comparison_gdp_proxy.png')


def plot_gdp_per_capita_comparison():
    """Compare GDP per capita across countries."""
    setup_style()
    fig, ax = plt.subplots(figsize=(14, 7))

    all_dates = []

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data
                         if 'total_factory_income' in d
                         and 'total_rgo_income' in d
                         and d.get('population_total', 0) > 0]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [(d['total_factory_income'] + d['total_rgo_income']) / d['population_total']
                  for d in valid_entries]

        all_dates.extend(dates)

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    if not all_dates:
        plt.close()
        return

    ax.set_title('GDP Per Capita Comparison')
    ax.set_xlabel('Year')
    ax.set_ylabel('£ per Person')

    format_date_axis(ax, all_dates)
    ax.legend(loc='best')

    save_chart('comparison_gdp_per_capita', subdir='comparisons')
    print('  Saved: comparisons/comparison_gdp_per_capita.png')


def plot_industrialization_comparison():
    """Compare industrialization index across countries."""
    setup_style()
    fig, ax = plt.subplots(figsize=(14, 7))

    all_dates = []

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data
                         if 'total_factory_count' in d
                         and d.get('population_total', 0) > 0]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [(d['total_factory_count'] / d['population_total'] * 1_000_000)
                  for d in valid_entries]

        all_dates.extend(dates)

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    if not all_dates:
        plt.close()
        return

    ax.set_title('Industrialization Index Comparison (Factories per Million Pop)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Factories per Million')

    format_date_axis(ax, all_dates)
    ax.legend(loc='best')

    save_chart('comparison_industrialization', subdir='comparisons')
    print('  Saved: comparisons/comparison_industrialization.png')


def plot_pop_wealth_comparison():
    """Compare POP wealth across countries."""
    setup_style()
    fig, ax = plt.subplots(figsize=(14, 7))

    all_dates = []

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data if 'pop_money' in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [d.get('pop_money', 0) + d.get('pop_bank_savings', 0)
                  for d in valid_entries]

        all_dates.extend(dates)

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    if not all_dates:
        plt.close()
        return

    ax.set_title('POP Wealth Comparison (Cash + Savings)')
    ax.set_xlabel('Year')
    ax.set_ylabel('£')

    format_date_axis(ax, all_dates)
    format_large_numbers(ax)
    ax.legend(loc='best')

    save_chart('comparison_pop_wealth', subdir='comparisons')
    print('  Saved: comparisons/comparison_pop_wealth.png')


def plot_all_comparisons():
    """Generate all comparison charts."""
    print("Generating comparison charts...")

    # Compare each statistic
    for stat_key in COUNTRY_STATS:
        plot_comparison(GREAT_POWERS, stat_key)

    # Derived comparisons
    plot_gdp_comparison()
    plot_gdp_per_capita_comparison()
    plot_industrialization_comparison()
    plot_pop_wealth_comparison()


# =============================================================================
# Main Entry Points
# =============================================================================

def plot_country_profile(tag: str):
    """Generate complete profile for a single country (legacy function name)."""
    count = plot_all_country_stats(tag)
    if count > 0:
        print(f"Generated {count} charts for {tag}")
    else:
        print(f"No data available for {tag}")


def plot_all_countries():
    """Generate charts for all countries in the dataset."""
    countries = get_available_countries()
    print(f"Found {len(countries)} countries in dataset")

    total_charts = 0
    countries_with_data = 0

    for i, tag in enumerate(countries, 1):
        count = plot_all_country_stats(tag)
        if count > 0:
            print(f"  [{i}/{len(countries)}] {tag}: {count} charts")
            total_charts += count
            countries_with_data += 1

    print(f"Generated {total_charts} charts for {countries_with_data} countries")


def plot_all():
    """Generate all country visualizations."""
    print("Generating country charts...")

    # Generate comparison charts for major powers
    print("\n  Comparison charts...")
    plot_all_comparisons()

    # Generate individual country charts for ALL countries
    print("\n  Individual country charts...")
    plot_all_countries()

    print("Done with countries!")


if __name__ == '__main__':
    plot_all()
