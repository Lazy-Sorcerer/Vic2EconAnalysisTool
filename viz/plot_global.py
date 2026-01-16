"""
Visualizations for global statistics - one chart per statistic.
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


SUBDIR = 'global'


def plot_single_metric(data, key, title, ylabel, filename, color='#2E86AB',
                       fill=True, ylim=None, normalize_factor=1, format_y=True):
    """Generic function to plot a single metric over time."""
    setup_style()

    dates, values = get_dates_and_values(data, key)
    if normalize_factor != 1:
        values = [v / normalize_factor for v in values]

    fig, ax = plt.subplots()
    ax.plot(dates, values, color=color, linewidth=2)
    if fill:
        ax.fill_between(dates, values, alpha=0.3, color=color)

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
# Population Statistics
# =============================================================================

def plot_total_population():
    """Plot total world population over time."""
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'total_population',
        title='World Population',
        ylabel='Population',
        filename='global_total_population',
        color='#2E86AB'
    )


def plot_population_by_type():
    """Plot population distribution by POP type over time (stacked area)."""
    setup_style()
    data = load_json('global_population_by_type.json')

    dates = [parse_date(d['date']) for d in data]
    pop_types = [k for k in data[0].keys() if k != 'date']

    # Sort by final population size
    final_pops = {pt: data[-1].get(pt, 0) for pt in pop_types}
    pop_types = sorted(pop_types, key=lambda x: final_pops[x], reverse=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    values = [[d.get(pt, 0) for d in data] for pt in pop_types]
    colors = [get_pop_color(pt) for pt in pop_types]

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
    """Plot population composition as percentages."""
    setup_style()
    data = load_json('global_population_by_type.json')

    dates = [parse_date(d['date']) for d in data]
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

    save_chart('population_composition', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/population_composition.png')


# Individual POP type charts
def plot_pop_type(pop_type: str):
    """Plot a single POP type population over time."""
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
    """Plot individual charts for each POP type."""
    data = load_json('global_population_by_type.json')
    pop_types = [k for k in data[0].keys() if k != 'date']

    for pop_type in pop_types:
        plot_pop_type(pop_type)


# =============================================================================
# Wealth Statistics
# =============================================================================

def plot_total_pop_money():
    """Plot total cash held by all POPs worldwide."""
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'total_pop_money',
        title='World POP Cash Holdings',
        ylabel='Cash (£)',
        filename='global_total_pop_money',
        color='#2E86AB'
    )


def plot_total_pop_bank_savings():
    """Plot total bank savings of all POPs."""
    data = load_json('global_statistics.json')
    plot_single_metric(
        data, 'total_pop_bank_savings',
        title='World POP Bank Savings',
        ylabel='Savings (£)',
        filename='global_total_pop_bank_savings',
        color='#A23B72'
    )


def plot_total_wealth():
    """Plot total world wealth (cash + savings) as stacked area."""
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
# Welfare Indicators (Needs Satisfaction)
# =============================================================================

def plot_avg_life_needs():
    """Plot world average life needs satisfaction."""
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
    """Plot world average everyday needs satisfaction."""
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
    """Plot world average luxury needs satisfaction."""
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
    """Plot all three needs satisfaction types on one chart."""
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
# Social Indicators
# =============================================================================

def plot_avg_literacy():
    """Plot world average literacy rate."""
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
    """Plot world average political consciousness."""
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
    """Plot world average militancy."""
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
    """Plot literacy, consciousness, and militancy on one chart (normalized)."""
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
# Main Entry Point
# =============================================================================

def plot_all():
    """Generate all global statistics visualizations."""
    print("Generating global statistics charts...")

    # Population
    print("  Population charts...")
    plot_total_population()
    plot_population_by_type()
    plot_population_composition()
    plot_all_pop_types()

    # Wealth
    print("  Wealth charts...")
    plot_total_pop_money()
    plot_total_pop_bank_savings()
    plot_total_wealth()

    # Needs satisfaction
    print("  Needs satisfaction charts...")
    plot_avg_life_needs()
    plot_avg_everyday_needs()
    plot_avg_luxury_needs()
    plot_all_needs()

    # Social indicators
    print("  Social indicators charts...")
    plot_avg_literacy()
    plot_avg_consciousness()
    plot_avg_militancy()
    plot_all_social()

    print("Done with global statistics!")


if __name__ == '__main__':
    plot_all()
