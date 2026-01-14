"""
Visualizations for country comparisons.
"""

import matplotlib.pyplot as plt
import numpy as np
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
    OUTPUT_DIR,
    TAG_GROUPS,
)


# Major powers for comparison
# Use group names (GER, KUK) which will automatically merge PRU→NGF→GER and AUS→SGF→KUK
GREAT_POWERS = ['ENG', 'FRA', 'GER', 'KUK', 'RUS', 'USA']
EUROPEAN_POWERS = ['ENG', 'FRA', 'GER', 'KUK', 'RUS', 'SPA', 'ITA', 'TUR']


def get_available_countries() -> list[str]:
    """Get list of countries with data files."""
    countries_dir = OUTPUT_DIR / 'countries'
    return [f.stem for f in countries_dir.glob('*.json')]


def plot_country_comparison(countries: list[str], metric: str, title: str,
                           filename: str, ylabel: str = None):
    """Compare a metric across multiple countries."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    for tag in countries:
        # Use load_country_group to handle tag transitions (PRU→NGF→GER, etc.)
        data = load_country_group(tag)
        if not data:
            continue

        # Filter entries that have the metric
        valid_entries = [d for d in data if metric in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [d[metric] for d in valid_entries]

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel or metric.replace('_', ' ').title())

    if dates:
        format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='best')

    save_chart(filename)
    print(f'Saved: {filename}.png')


def plot_treasury_comparison():
    """Compare national treasuries."""
    plot_country_comparison(
        GREAT_POWERS, 'treasury',
        'National Treasury Comparison',
        'country_treasury',
        'Treasury (£)'
    )


def plot_prestige_comparison():
    """Compare prestige scores."""
    plot_country_comparison(
        GREAT_POWERS, 'prestige',
        'Prestige Comparison',
        'country_prestige',
        'Prestige'
    )


def plot_factory_comparison():
    """Compare factory counts."""
    plot_country_comparison(
        GREAT_POWERS, 'total_factory_count',
        'Factory Count Comparison',
        'country_factories',
        'Number of Factories'
    )


def plot_factory_income_comparison():
    """Compare factory income."""
    plot_country_comparison(
        GREAT_POWERS, 'total_factory_income',
        'Factory Income Comparison',
        'country_factory_income',
        'Factory Income (£)'
    )


def plot_population_comparison():
    """Compare populations."""
    plot_country_comparison(
        GREAT_POWERS, 'population_total',
        'Population Comparison',
        'country_population',
        'Population'
    )


def plot_literacy_comparison():
    """Compare literacy rates."""
    plot_country_comparison(
        GREAT_POWERS, 'avg_literacy',
        'Literacy Rate Comparison',
        'country_literacy',
        'Literacy Rate'
    )


def plot_industrialization_index():
    """Plot industrialization index (factories per capita)."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data if 'total_factory_count' in d and 'population_total' in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = []
        for d in valid_entries:
            pop = d['population_total']
            factories = d['total_factory_count']
            # Factories per million population
            index = (factories / pop * 1_000_000) if pop > 0 else 0
            values.append(index)

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    ax.set_title('Industrialization Index (Factories per Million Pop)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Factories per Million')

    if dates:
        format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('country_industrialization_index')
    print('Saved: country_industrialization_index.png')


def plot_gdp_proxy():
    """Plot GDP proxy (factory income + RGO income)."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data if 'total_factory_income' in d and 'total_rgo_income' in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [d['total_factory_income'] + d['total_rgo_income'] for d in valid_entries]

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    ax.set_title('GDP Proxy (Factory + RGO Income)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Income (£)')

    if dates:
        format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='best')

    save_chart('country_gdp_proxy')
    print('Saved: country_gdp_proxy.png')


def plot_gdp_per_capita():
    """Plot GDP per capita proxy."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data
                        if 'total_factory_income' in d
                        and 'total_rgo_income' in d
                        and 'population_total' in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = []
        for d in valid_entries:
            gdp = d['total_factory_income'] + d['total_rgo_income']
            pop = d['population_total']
            gdp_pc = gdp / pop if pop > 0 else 0
            values.append(gdp_pc)

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    ax.set_title('GDP Per Capita Proxy')
    ax.set_xlabel('Year')
    ax.set_ylabel('Income per Person (£)')

    if dates:
        format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('country_gdp_per_capita')
    print('Saved: country_gdp_per_capita.png')


def plot_country_profile(tag: str):
    """Generate a multi-panel profile for a single country."""
    data = load_country_group(tag)
    if not data:
        print(f'Country {tag} not found')
        return

    valid_data = [d for d in data if 'treasury' in d]
    if not valid_data:
        print(f'No valid data for {tag}')
        return

    setup_style()
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'{tag} Economic Profile', fontsize=16)

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
    values = [d.get('total_factory_income', 0) + d.get('total_rgo_income', 0) for d in valid_data]
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

    save_chart(f'country_profile_{tag}')
    print(f'Saved: country_profile_{tag}.png')


def plot_tax_comparison():
    """Compare total tax income across countries."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    for tag in GREAT_POWERS:
        data = load_country_group(tag)
        if not data:
            continue

        valid_entries = [d for d in data if 'total_tax_income' in d]
        if not valid_entries:
            continue

        dates = [parse_date(d['date']) for d in valid_entries]
        values = [d['total_tax_income'] for d in valid_entries]

        color = get_country_color(tag)
        ax.plot(dates, values, label=tag, linewidth=2, color=color)

    ax.set_title('Total Tax Income Comparison')
    ax.set_xlabel('Year')
    ax.set_ylabel('Tax Income (£)')

    if dates:
        format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='best')

    save_chart('country_tax_income')
    print('Saved: country_tax_income.png')


def plot_all():
    """Generate all country comparison visualizations."""
    print("Generating country comparison charts...")

    plot_treasury_comparison()
    plot_prestige_comparison()
    plot_factory_comparison()
    plot_factory_income_comparison()
    plot_population_comparison()
    plot_literacy_comparison()
    plot_industrialization_index()
    plot_gdp_proxy()
    plot_gdp_per_capita()
    plot_tax_comparison()

    # Individual country profiles
    for tag in GREAT_POWERS:
        plot_country_profile(tag)

    print("Done!")


if __name__ == '__main__':
    plot_all()
