"""
Visualizations for global statistics.
"""

import matplotlib.pyplot as plt
import numpy as np

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


def plot_world_population():
    """Plot world population over time."""
    setup_style()
    data = load_json('global_statistics.json')

    dates, values = get_dates_and_values(data, 'total_population')

    fig, ax = plt.subplots()
    ax.plot(dates, values, color='#2E86AB', linewidth=2)
    ax.fill_between(dates, values, alpha=0.3, color='#2E86AB')

    ax.set_title('World Population Over Time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Population')

    format_date_axis(ax, dates)
    format_large_numbers(ax)

    save_chart('global_population')
    print('Saved: global_population.png')


def plot_world_wealth():
    """Plot total world wealth (POP money + bank savings)."""
    setup_style()
    data = load_json('global_statistics.json')

    dates = [parse_date(d['date']) for d in data]
    pop_money = [d['total_pop_money'] for d in data]
    bank_savings = [d['total_pop_bank_savings'] for d in data]

    fig, ax = plt.subplots()

    ax.stackplot(dates, pop_money, bank_savings,
                 labels=['Cash Holdings', 'Bank Savings'],
                 colors=['#2E86AB', '#A23B72'], alpha=0.8)

    ax.set_title('World Wealth Over Time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Total Wealth (£)')

    format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='upper left')

    save_chart('global_wealth')
    print('Saved: global_wealth.png')


def plot_needs_satisfaction():
    """Plot average needs satisfaction over time."""
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

    save_chart('global_needs_satisfaction')
    print('Saved: global_needs_satisfaction.png')


def plot_social_indicators():
    """Plot literacy, consciousness, and militancy."""
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

    ax.set_title('World Social Indicators')
    ax.set_xlabel('Year')
    ax.set_ylabel('Value (normalized 0-1)')
    ax.set_ylim(0, 1)

    format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('global_social_indicators')
    print('Saved: global_social_indicators.png')


def plot_population_by_type():
    """Plot population distribution by POP type over time."""
    setup_style()
    data = load_json('global_population_by_type.json')

    dates = [parse_date(d['date']) for d in data]

    # Get all POP types
    pop_types = [k for k in data[0].keys() if k != 'date']

    # Sort by final population size
    final_pops = {pt: data[-1].get(pt, 0) for pt in pop_types}
    pop_types = sorted(pop_types, key=lambda x: final_pops[x], reverse=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    # Stack plot
    values = [[d.get(pt, 0) for d in data] for pt in pop_types]
    colors = [get_pop_color(pt) for pt in pop_types]

    ax.stackplot(dates, *values, labels=pop_types, colors=colors, alpha=0.8)

    ax.set_title('World Population by Type')
    ax.set_xlabel('Year')
    ax.set_ylabel('Population')

    format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='upper left', ncol=3)

    save_chart('global_population_by_type')
    print('Saved: global_population_by_type.png')


def plot_population_composition():
    """Plot population composition as percentages."""
    setup_style()
    data = load_json('global_population_by_type.json')

    dates = [parse_date(d['date']) for d in data]

    # Get all POP types
    pop_types = [k for k in data[0].keys() if k != 'date']

    # Calculate percentages
    totals = []
    for d in data:
        total = sum(d.get(pt, 0) for pt in pop_types)
        totals.append(total)

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

    save_chart('global_population_composition')
    print('Saved: global_population_composition.png')


def plot_all():
    """Generate all global visualizations."""
    print("Generating global statistics charts...")
    plot_world_population()
    plot_world_wealth()
    plot_needs_satisfaction()
    plot_social_indicators()
    plot_population_by_type()
    plot_population_composition()
    print("Done!")


if __name__ == '__main__':
    plot_all()
