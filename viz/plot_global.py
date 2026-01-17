"""
Visualizations for global (world-level) statistics.

This module generates charts showing aggregate statistics across the entire
world in Victoria 2, including population trends, wealth accumulation,
welfare indicators, and social metrics.

CHARTS GENERATED
================

Population Charts:
    - global_total_population.png: World population over time
    - population_by_type.png: Stacked area by POP type (farmers, craftsmen, etc.)
    - population_composition.png: Same as above, but as percentages (0-100%)
    - pop_{type}.png: Individual chart for each of 13 POP types

Wealth Charts:
    - global_total_pop_money.png: Cash held by all POPs
    - global_total_pop_bank_savings.png: Bank deposits by all POPs
    - total_wealth.png: Stacked area (cash + savings)

Welfare Charts (Needs Satisfaction):
    - global_avg_life_needs.png: Basic needs (food, fuel, shelter)
    - global_avg_everyday_needs.png: Standard living needs
    - global_avg_luxury_needs.png: Luxury consumption
    - all_needs.png: All three needs on one chart

Social Indicators:
    - global_avg_literacy.png: World literacy rate (0-1)
    - global_avg_consciousness.png: Political awareness (0-10)
    - global_avg_militancy.png: Revolutionary tendency (0-10)
    - all_social.png: All three normalized on one chart

UNDERSTANDING THE METRICS
=========================

Population by POP Type:
    POPs (population units) are categorized by occupation/class:
    - Upper class: aristocrats, capitalists, officers
    - Middle class: artisans, clerks, bureaucrats, clergymen
    - Working class: craftsmen, farmers, labourers, soldiers
    - Other: slaves

    The distribution shifts over time as industrialization converts
    farmers into craftsmen and creates new middle-class jobs.

Needs Satisfaction (0.0 - 1.0+):
    Each POP has three types of needs:
    - Life needs: Essential for survival (food, fuel). Below 0.5 causes death.
    - Everyday needs: Normal living standard. Affects happiness.
    - Luxury needs: Luxury goods. Only upper/middle class typically satisfies.

    Values can exceed 1.0 if POPs buy more than their base needs.

Social Indicators:
    - Literacy (0-1): Education level. Affects research, political awareness.
    - Consciousness (0-10): Political awareness. Higher = more reform demands.
    - Militancy (0-10): Revolutionary tendency. Above 5 = revolt risk.

USAGE
=====

Generate all global charts:
    >>> from plot_global import plot_all
    >>> plot_all()

Generate specific charts:
    >>> from plot_global import plot_total_population, plot_population_by_type
    >>> plot_total_population()
    >>> plot_population_by_type()

DEPENDENCIES
============

Requires global_statistics.json and global_population_by_type.json
in the output/ directory. These are created by process_saves.py.

Author: Victoria 2 Economy Analysis Tool Project
"""

import matplotlib.pyplot as plt

from utils import (
    load_json,
    parse_date,
    get_dates_and_values,
    setup_style,
    format_date_axis,
    format_large_numbers,
    save_chart,
    get_pop_color,
)


# Subdirectory for global statistics charts
SUBDIR = 'global'


# =============================================================================
# GENERIC PLOTTING HELPER
# =============================================================================

def plot_single_metric(data, key, title, ylabel, filename, color='#2E86AB',
                       fill=True, ylim=None, normalize_factor=1, format_y=True):
    """
    Generic function to plot a single metric over time.

    Creates a line chart with optional fill, suitable for time series data.
    This is a helper function used by the specific metric plotting functions.

    Args:
        data: List of dated entries (from load_json)
        key: The dictionary key to extract values from
        title: Chart title
        ylabel: Y-axis label
        filename: Output filename (without extension)
        color: Line and fill color (hex code)
        fill: Whether to fill area under line
        ylim: Optional (min, max) tuple for y-axis limits
        normalize_factor: Divide values by this (e.g., 1e6 for millions)
        format_y: Whether to format y-axis with K/M/B suffixes

    Example:
        >>> plot_single_metric(
        ...     data, 'total_population',
        ...     title='World Population',
        ...     ylabel='Population',
        ...     filename='global_total_population'
        ... )
    """
    setup_style()

    # Extract dates and values from the data
    dates, values = get_dates_and_values(data, key)
    if normalize_factor != 1:
        values = [v / normalize_factor for v in values]

    # Create the plot
    fig, ax = plt.subplots()
    ax.plot(dates, values, color=color, linewidth=2)
    if fill:
        ax.fill_between(dates, values, alpha=0.3, color=color)

    # Labels and formatting
    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)

    if ylim:
        ax.set_ylim(ylim)

    format_date_axis(ax, dates)
    if format_y:
        format_large_numbers(ax)

    save_chart(filename, subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/{filename}.png')


# =============================================================================
# POPULATION CHARTS
# =============================================================================

def plot_total_population():
    """
    Plot total world population over time.

    Creates a simple line chart showing global population growth
    from game start (1836) through the end of the dataset.

    Output: charts/global/global_total_population.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'total_population',
        title='World Population',
        ylabel='Population',
        filename='global_total_population',
        color='#2E86AB'
    )


def plot_population_by_type():
    """
    Plot population distribution by POP type over time (stacked area).

    Creates a stacked area chart showing how the world population is
    distributed across different occupational types. The ordering is
    by final population size (largest at bottom).

    POP Types Included:
        farmers, labourers, craftsmen, artisans, clerks, soldiers,
        aristocrats, capitalists, bureaucrats, clergymen, officers, slaves

    Output: charts/global/population_by_type.png

    Historical Pattern:
        - Early game: Dominated by farmers and labourers
        - Industrialization: Rise of craftsmen, clerks
        - Late game: More balanced distribution
    """
    setup_style()
    data = load_json('global_population_by_type.json')

    dates = [parse_date(d['date']) for d in data]
    pop_types = [k for k in data[0].keys() if k != 'date']

    # Sort by final population size (largest types at bottom of stack)
    final_pops = {pt: data[-1].get(pt, 0) for pt in pop_types}
    pop_types = sorted(pop_types, key=lambda x: final_pops[x], reverse=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    # Build value arrays for each POP type
    values = [[d.get(pt, 0) for d in data] for pt in pop_types]
    colors = [get_pop_color(pt) for pt in pop_types]

    # Create stacked area chart
    ax.stackplot(dates, *values, labels=pop_types, colors=colors, alpha=0.8)

    ax.set_title('World Population by Type')
    ax.set_xlabel('Year')
    ax.set_ylabel('Population')

    format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='upper left', ncol=3)

    save_chart('population_by_type', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/population_by_type.png')


def plot_population_composition():
    """
    Plot population composition as percentages (0-100%).

    Similar to plot_population_by_type, but shows each POP type as
    a percentage of total population. Useful for seeing relative
    changes in population structure.

    Output: charts/global/population_composition.png

    Use Case:
        See how the economy transforms from agricultural to industrial
        by watching farmers' percentage decline while craftsmen rise.
    """
    setup_style()
    data = load_json('global_population_by_type.json')

    dates = [parse_date(d['date']) for d in data]
    pop_types = [k for k in data[0].keys() if k != 'date']

    # Calculate total population for each date
    totals = []
    for d in data:
        total = sum(d.get(pt, 0) for pt in pop_types)
        totals.append(total)

    # Calculate percentages for each POP type
    percentages = {pt: [] for pt in pop_types}
    for i, d in enumerate(data):
        for pt in pop_types:
            pct = (d.get(pt, 0) / totals[i] * 100) if totals[i] > 0 else 0
            percentages[pt].append(pct)

    # Sort by final percentage
    pop_types = sorted(pop_types, key=lambda x: percentages[x][-1], reverse=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    values = [percentages[pt] for pt in pop_types]
    colors = [get_pop_color(pt) for pt in pop_types]

    ax.stackplot(dates, *values, labels=pop_types, colors=colors, alpha=0.8)

    ax.set_title('World Population Composition (%)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Percentage')
    ax.set_ylim(0, 100)

    format_date_axis(ax, dates)
    ax.legend(loc='upper left', ncol=3)

    save_chart('population_composition', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/population_composition.png')


def plot_pop_type(pop_type: str):
    """
    Plot a single POP type population over time.

    Creates an individual chart for one POP type, with filled area
    under the line. Color is determined by POP_TYPE_COLORS.

    Args:
        pop_type: Name of POP type (e.g., 'farmers', 'craftsmen')

    Output: charts/global/pop_{pop_type}.png
    """
    setup_style()
    data = load_json('global_population_by_type.json')

    dates = [parse_date(d['date']) for d in data]
    values = [d.get(pop_type, 0) for d in data]

    color = get_pop_color(pop_type)

    fig, ax = plt.subplots()
    ax.plot(dates, values, color=color, linewidth=2)
    ax.fill_between(dates, values, alpha=0.3, color=color)

    ax.set_title(f'World {pop_type.title()} Population')
    ax.set_xlabel('Year')
    ax.set_ylabel('Population')

    format_date_axis(ax, dates)
    format_large_numbers(ax)

    save_chart(f'pop_{pop_type}', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/pop_{pop_type}.png')


def plot_all_pop_types():
    """
    Plot individual charts for each POP type.

    Generates one chart per POP type found in the data.
    Typically produces 12-13 charts (one per occupation type).
    """
    data = load_json('global_population_by_type.json')
    pop_types = [k for k in data[0].keys() if k != 'date']

    for pop_type in pop_types:
        plot_pop_type(pop_type)


# =============================================================================
# WEALTH CHARTS
# =============================================================================

def plot_total_pop_money():
    """
    Plot total cash held by all POPs worldwide.

    Shows liquid money holdings (not including bank savings).
    This is money POPs use for daily purchases.

    Output: charts/global/global_total_pop_money.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'total_pop_money',
        title='World POP Cash Holdings',
        ylabel='Cash (£)',
        filename='global_total_pop_money',
        color='#2E86AB'
    )


def plot_total_pop_bank_savings():
    """
    Plot total bank savings of all POPs.

    Shows money deposited in banks. Upper and middle class POPs
    tend to save more. Bank savings generate interest income.

    Output: charts/global/global_total_pop_bank_savings.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'total_pop_bank_savings',
        title='World POP Bank Savings',
        ylabel='Savings (£)',
        filename='global_total_pop_bank_savings',
        color='#A23B72'
    )


def plot_total_wealth():
    """
    Plot total world wealth (cash + savings) as stacked area.

    Combines cash holdings and bank savings to show total POP wealth.
    The stacked format shows the breakdown between liquid and saved.

    Output: charts/global/total_wealth.png

    Economic Insight:
        Rising bank savings relative to cash indicates economic
        stability and middle class growth.
    """
    setup_style()
    data = load_json('global_statistics.json')

    dates = [parse_date(d['date']) for d in data]
    pop_money = [d['total_pop_money'] for d in data]
    bank_savings = [d['total_pop_bank_savings'] for d in data]

    fig, ax = plt.subplots()

    ax.stackplot(dates, pop_money, bank_savings,
                 labels=['Cash Holdings', 'Bank Savings'],
                 colors=['#2E86AB', '#A23B72'], alpha=0.8)

    ax.set_title('World POP Total Wealth')
    ax.set_xlabel('Year')
    ax.set_ylabel('Total Wealth (£)')

    format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='upper left')

    save_chart('total_wealth', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/total_wealth.png')


# =============================================================================
# WELFARE CHARTS (Needs Satisfaction)
# =============================================================================

def plot_avg_life_needs():
    """
    Plot world average life needs satisfaction.

    Life needs are basic survival needs (food, fuel, clothing).
    Values below 0.5 cause population decline.

    Scale: 0.0 (starving) to 1.0+ (fully satisfied)

    Output: charts/global/global_avg_life_needs.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'avg_life_needs',
        title='World Average Life Needs Satisfaction',
        ylabel='Satisfaction (0-1)',
        filename='global_avg_life_needs',
        color='#E63946',
        ylim=(0, 1),
        format_y=False
    )


def plot_avg_everyday_needs():
    """
    Plot world average everyday needs satisfaction.

    Everyday needs are standard living requirements (services,
    furniture, entertainment). Affects happiness and productivity.

    Scale: 0.0 to 1.0+

    Output: charts/global/global_avg_everyday_needs.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'avg_everyday_needs',
        title='World Average Everyday Needs Satisfaction',
        ylabel='Satisfaction (0-1)',
        filename='global_avg_everyday_needs',
        color='#457B9D',
        ylim=(0, 1),
        format_y=False
    )


def plot_avg_luxury_needs():
    """
    Plot world average luxury needs satisfaction.

    Luxury needs are optional high-end consumption (luxury goods,
    fine clothing). Typically only upper/middle class satisfies these.

    Scale: 0.0 to 1.0+

    Output: charts/global/global_avg_luxury_needs.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'avg_luxury_needs',
        title='World Average Luxury Needs Satisfaction',
        ylabel='Satisfaction (0-1)',
        filename='global_avg_luxury_needs',
        color='#2A9D8F',
        ylim=(0, 1),
        format_y=False
    )


def plot_all_needs():
    """
    Plot all three needs satisfaction types on one chart.

    Combines life, everyday, and luxury needs for easy comparison.
    Typically life > everyday > luxury.

    Output: charts/global/all_needs.png

    Interpretation:
        - Wide gap between life and luxury = high inequality
        - All three converging upward = prosperity
        - Life needs dropping = economic crisis
    """
    setup_style()
    data = load_json('global_statistics.json')

    dates = [parse_date(d['date']) for d in data]
    life = [d['avg_life_needs'] for d in data]
    everyday = [d['avg_everyday_needs'] for d in data]
    luxury = [d['avg_luxury_needs'] for d in data]

    fig, ax = plt.subplots()

    ax.plot(dates, life, label='Life Needs', color='#E63946', linewidth=2)
    ax.plot(dates, everyday, label='Everyday Needs', color='#457B9D', linewidth=2)
    ax.plot(dates, luxury, label='Luxury Needs', color='#2A9D8F', linewidth=2)

    ax.set_title('World Average Needs Satisfaction')
    ax.set_xlabel('Year')
    ax.set_ylabel('Satisfaction (0-1)')
    ax.set_ylim(0, 1)

    format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('all_needs', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/all_needs.png')


# =============================================================================
# SOCIAL INDICATORS
# =============================================================================

def plot_avg_literacy():
    """
    Plot world average literacy rate.

    Literacy represents education level. Affects:
    - Research point generation
    - Political consciousness growth
    - Reform desire
    - Promotion chances

    Scale: 0.0 (illiterate) to 1.0 (fully literate)

    Output: charts/global/global_avg_literacy.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'avg_literacy',
        title='World Average Literacy Rate',
        ylabel='Literacy (0-1)',
        filename='global_avg_literacy',
        color='#1D3557',
        ylim=(0, 1),
        format_y=False
    )


def plot_avg_consciousness():
    """
    Plot world average political consciousness.

    Consciousness represents political awareness. Higher values mean:
    - More demand for reforms
    - Higher voting participation
    - More likely to join political movements

    Scale: 0 (politically unaware) to 10 (highly aware)

    Output: charts/global/global_avg_consciousness.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'avg_consciousness',
        title='World Average Political Consciousness',
        ylabel='Consciousness (0-10)',
        filename='global_avg_consciousness',
        color='#457B9D',
        ylim=(0, 10),
        format_y=False
    )


def plot_avg_militancy():
    """
    Plot world average militancy.

    Militancy represents revolutionary tendency. Effects:
    - 0-2: Peaceful population
    - 2-5: Unrest, protests possible
    - 5-7: Revolt risk increasing
    - 7-10: Revolts highly likely

    Scale: 0 to 10

    Output: charts/global/global_avg_militancy.png
    """
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'avg_militancy',
        title='World Average Militancy',
        ylabel='Militancy (0-10)',
        filename='global_avg_militancy',
        color='#E63946',
        ylim=(0, 10),
        format_y=False
    )


def plot_all_social():
    """
    Plot literacy, consciousness, and militancy on one chart (normalized).

    All three indicators are normalized to 0-1 scale for comparison:
    - Literacy: Already 0-1
    - Consciousness: Divided by 10
    - Militancy: Divided by 10

    Output: charts/global/all_social.png

    Interpretation:
        - Rising literacy with low militancy = peaceful modernization
        - High consciousness + high militancy = revolutionary situation
        - Literacy rising faster than militancy = stable progress
    """
    setup_style()
    data = load_json('global_statistics.json')

    dates = [parse_date(d['date']) for d in data]
    literacy = [d['avg_literacy'] for d in data]
    consciousness = [d['avg_consciousness'] / 10 for d in data]  # Normalize to 0-1
    militancy = [d['avg_militancy'] / 10 for d in data]  # Normalize to 0-1

    fig, ax = plt.subplots()

    ax.plot(dates, literacy, label='Literacy', color='#1D3557', linewidth=2)
    ax.plot(dates, consciousness, label='Consciousness (÷10)', color='#457B9D', linewidth=2)
    ax.plot(dates, militancy, label='Militancy (÷10)', color='#E63946', linewidth=2)

    ax.set_title('World Social Indicators (Normalized)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Value (normalized 0-1)')
    ax.set_ylim(0, 1)

    format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('all_social', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/all_social.png')


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def plot_all():
    """
    Generate all global statistics visualizations.

    This is the main entry point called by plot_all.py.
    Generates approximately 25-30 charts covering population,
    wealth, welfare, and social indicators.
    """
    print("Generating global statistics charts...")

    # Population charts
    print("  Population charts...")
    plot_total_population()
    plot_population_by_type()
    plot_population_composition()
    plot_all_pop_types()

    # Wealth charts
    print("  Wealth charts...")
    plot_total_pop_money()
    plot_total_pop_bank_savings()
    plot_total_wealth()

    # Needs satisfaction charts
    print("  Needs satisfaction charts...")
    plot_avg_life_needs()
    plot_avg_everyday_needs()
    plot_avg_luxury_needs()
    plot_all_needs()

    # Social indicator charts
    print("  Social indicators charts...")
    plot_avg_literacy()
    plot_avg_consciousness()
    plot_avg_militancy()
    plot_all_social()

    print("Done with global statistics!")


if __name__ == '__main__':
    plot_all()
