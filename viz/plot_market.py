"""
Visualizations for world market data - prices, supply, and sold quantities.
Generates individual charts for each commodity and category summaries.
"""

import matplotlib.pyplot as plt
import numpy as np

from utils import (
    load_json,
    parse_date,
    setup_style,
    format_date_axis,
    format_large_numbers,
    save_chart,
    get_commodity_color,
)


# =============================================================================
# Commodity Categories
# =============================================================================

RAW_RESOURCES = [
    'coal', 'iron', 'sulphur', 'timber', 'tropical_wood',
    'precious_metal', 'oil', 'rubber'
]

AGRICULTURAL = [
    'grain', 'cattle', 'fish', 'fruit', 'cotton', 'wool', 'silk', 'dye',
    'tobacco', 'tea', 'coffee', 'opium'
]

INDUSTRIAL_GOODS = [
    'steel', 'cement', 'glass', 'fertilizer', 'explosives',
    'machine_parts', 'electric_gear', 'fuel', 'fabric', 'lumber', 'paper'
]

CONSUMER_GOODS = [
    'regular_clothes', 'luxury_clothes', 'furniture', 'luxury_furniture',
    'wine', 'liquor'
]

MILITARY_GOODS = [
    'ammunition', 'small_arms', 'artillery', 'canned_food', 'barrels',
    'clipper_convoy', 'steamer_convoy', 'aeroplanes', 'automobiles',
    'telephones', 'radio'
]

ALL_CATEGORIES = {
    'raw': ('Raw Resources', RAW_RESOURCES),
    'agricultural': ('Agricultural Goods', AGRICULTURAL),
    'industrial': ('Industrial Goods', INDUSTRIAL_GOODS),
    'consumer': ('Consumer Goods', CONSUMER_GOODS),
    'military': ('Military Goods', MILITARY_GOODS),
}

SUBDIR = 'market'


# =============================================================================
# Helper Functions
# =============================================================================

def get_all_commodities(data: list[dict]) -> list[str]:
    """Get all commodity names from market data."""
    return [k for k in data[0].keys() if k != 'date']


def plot_commodity_group(data: list[dict], commodities: list[str],
                         title: str, ylabel: str, filename: str):
    """Plot multiple commodities on one chart."""
    setup_style()

    dates = [parse_date(d['date']) for d in data]

    fig, ax = plt.subplots(figsize=(14, 7))

    for commodity in commodities:
        if commodity in data[0]:
            values = [d.get(commodity, 0) for d in data]
            color = get_commodity_color(commodity)
            label = commodity.replace('_', ' ').title()
            ax.plot(dates, values, label=label, linewidth=1.5,
                    color=color if color != '#888888' else None)

    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)

    format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend(loc='best', ncol=2)

    save_chart(filename, subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/{filename}.png')


def plot_single_commodity(data: list[dict], commodity: str,
                          title: str, ylabel: str, filename: str,
                          color: str = '#2E86AB'):
    """Plot a single commodity over time."""
    setup_style()

    if commodity not in data[0]:
        print(f'Commodity {commodity} not found')
        return

    dates = [parse_date(d['date']) for d in data]
    values = [d.get(commodity, 0) for d in data]

    fig, ax = plt.subplots()

    ax.plot(dates, values, color=color, linewidth=2)
    ax.fill_between(dates, values, alpha=0.3, color=color)

    # Add trend line
    x_numeric = np.arange(len(dates))
    z = np.polyfit(x_numeric, values, 1)
    p = np.poly1d(z)
    ax.plot(dates, p(x_numeric), '--', color='#E63946', alpha=0.8, label='Trend')

    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)

    format_date_axis(ax, dates)
    format_large_numbers(ax)
    ax.legend()

    save_chart(filename, subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/{filename}.png')


# =============================================================================
# Price Charts
# =============================================================================

def plot_prices_by_category(category_key: str):
    """Plot prices for a commodity category."""
    data = load_json('world_market_prices.json')
    cat_name, commodities = ALL_CATEGORIES[category_key]
    plot_commodity_group(
        data, commodities,
        title=f'{cat_name} Prices',
        ylabel='Price (£)',
        filename=f'market_prices_{category_key}'
    )


def plot_all_category_prices():
    """Plot prices for all commodity categories."""
    for category_key in ALL_CATEGORIES:
        plot_prices_by_category(category_key)


def plot_single_price(commodity: str):
    """Plot price for a single commodity."""
    data = load_json('world_market_prices.json')
    color = get_commodity_color(commodity)
    if color == '#888888':
        color = '#2E86AB'
    plot_single_commodity(
        data, commodity,
        title=f'{commodity.replace("_", " ").title()} Price',
        ylabel='Price (£)',
        filename=f'market_price_{commodity}',
        color=color
    )


def plot_all_individual_prices():
    """Plot individual price charts for all commodities."""
    data = load_json('world_market_prices.json')
    commodities = get_all_commodities(data)
    for commodity in commodities:
        plot_single_price(commodity)


# =============================================================================
# Supply Charts
# =============================================================================

def plot_supply_by_category(category_key: str):
    """Plot supply for a commodity category."""
    data = load_json('world_market_supply.json')
    cat_name, commodities = ALL_CATEGORIES[category_key]
    plot_commodity_group(
        data, commodities,
        title=f'{cat_name} Supply',
        ylabel='Supply (units)',
        filename=f'market_supply_{category_key}'
    )


def plot_all_category_supply():
    """Plot supply for all commodity categories."""
    for category_key in ALL_CATEGORIES:
        plot_supply_by_category(category_key)


def plot_single_supply(commodity: str):
    """Plot supply for a single commodity."""
    data = load_json('world_market_supply.json')
    color = get_commodity_color(commodity)
    if color == '#888888':
        color = '#2A9D8F'
    plot_single_commodity(
        data, commodity,
        title=f'{commodity.replace("_", " ").title()} Supply',
        ylabel='Supply (units)',
        filename=f'market_supply_{commodity}',
        color=color
    )


def plot_all_individual_supply():
    """Plot individual supply charts for all commodities."""
    data = load_json('world_market_supply.json')
    commodities = get_all_commodities(data)
    for commodity in commodities:
        plot_single_supply(commodity)


# =============================================================================
# Sold (Demand) Charts
# =============================================================================

def plot_sold_by_category(category_key: str):
    """Plot sold quantities for a commodity category."""
    data = load_json('world_market_sold.json')
    cat_name, commodities = ALL_CATEGORIES[category_key]
    plot_commodity_group(
        data, commodities,
        title=f'{cat_name} Sold',
        ylabel='Sold (units)',
        filename=f'market_sold_{category_key}'
    )


def plot_all_category_sold():
    """Plot sold quantities for all commodity categories."""
    for category_key in ALL_CATEGORIES:
        plot_sold_by_category(category_key)


def plot_single_sold(commodity: str):
    """Plot sold quantities for a single commodity."""
    data = load_json('world_market_sold.json')
    color = get_commodity_color(commodity)
    if color == '#888888':
        color = '#E76F51'
    plot_single_commodity(
        data, commodity,
        title=f'{commodity.replace("_", " ").title()} Sold',
        ylabel='Sold (units)',
        filename=f'market_sold_{commodity}',
        color=color
    )


def plot_all_individual_sold():
    """Plot individual sold charts for all commodities."""
    data = load_json('world_market_sold.json')
    commodities = get_all_commodities(data)
    for commodity in commodities:
        plot_single_sold(commodity)


# =============================================================================
# Combined Analysis Charts
# =============================================================================

def plot_commodity_full(commodity: str):
    """Plot complete market analysis for a single commodity (price, supply, sold)."""
    setup_style()

    price_data = load_json('world_market_prices.json')
    supply_data = load_json('world_market_supply.json')
    sold_data = load_json('world_market_sold.json')

    if commodity not in price_data[0]:
        print(f'Commodity {commodity} not found')
        return

    dates = [parse_date(d['date']) for d in price_data]
    prices = [d.get(commodity, 0) for d in price_data]
    supply = [d.get(commodity, 0) for d in supply_data]
    sold = [d.get(commodity, 0) for d in sold_data]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    title = commodity.replace('_', ' ').title()
    fig.suptitle(f'{title} Market Analysis', fontsize=14)

    # Price plot
    ax = axes[0, 0]
    ax.plot(dates, prices, color='#2E86AB', linewidth=2)
    ax.fill_between(dates, prices, alpha=0.3, color='#2E86AB')
    ax.set_title('Price')
    ax.set_ylabel('£')
    format_date_axis(ax, dates)

    # Supply plot
    ax = axes[0, 1]
    ax.plot(dates, supply, color='#2A9D8F', linewidth=2)
    ax.fill_between(dates, supply, alpha=0.3, color='#2A9D8F')
    ax.set_title('Supply')
    ax.set_ylabel('Units')
    format_date_axis(ax, dates)
    format_large_numbers(ax)

    # Sold plot
    ax = axes[1, 0]
    ax.plot(dates, sold, color='#E76F51', linewidth=2)
    ax.fill_between(dates, sold, alpha=0.3, color='#E76F51')
    ax.set_title('Sold (Demand)')
    ax.set_ylabel('Units')
    format_date_axis(ax, dates)
    format_large_numbers(ax)

    # Supply vs Sold comparison
    ax = axes[1, 1]
    ax.plot(dates, supply, label='Supply', color='#2A9D8F', linewidth=2)
    ax.plot(dates, sold, label='Sold', color='#E76F51', linewidth=2)
    ax.set_title('Supply vs Sold')
    ax.set_ylabel('Units')
    ax.legend()
    format_date_axis(ax, dates)
    format_large_numbers(ax)

    save_chart(f'full_{commodity}', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/full_{commodity}.png')


def plot_all_commodity_full():
    """Plot full market analysis for all commodities."""
    data = load_json('world_market_prices.json')
    commodities = get_all_commodities(data)
    for commodity in commodities:
        plot_commodity_full(commodity)


def plot_supply_demand_balance(category_key: str):
    """Plot supply/demand balance (surplus %) for a commodity category."""
    setup_style()

    supply_data = load_json('world_market_supply.json')
    sold_data = load_json('world_market_sold.json')

    cat_name, commodities = ALL_CATEGORIES[category_key]

    dates = [parse_date(d['date']) for d in supply_data]

    fig, ax = plt.subplots(figsize=(14, 7))

    for commodity in commodities:
        if commodity in supply_data[0] and commodity in sold_data[0]:
            balance = []
            for i in range(len(supply_data)):
                supply = supply_data[i].get(commodity, 0)
                sold = sold_data[i].get(commodity, 0)
                if supply > 0:
                    balance.append((supply - sold) / supply * 100)
                else:
                    balance.append(0)

            color = get_commodity_color(commodity)
            label = commodity.replace('_', ' ').title()
            ax.plot(dates, balance, label=label, linewidth=1.5,
                    color=color if color != '#888888' else None)

    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.set_title(f'{cat_name} Supply/Demand Balance')
    ax.set_xlabel('Year')
    ax.set_ylabel('Surplus (%)')

    format_date_axis(ax, dates)
    ax.legend(loc='best', ncol=2)

    save_chart(f'balance_{category_key}', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/balance_{category_key}.png')


def plot_all_supply_demand_balance():
    """Plot supply/demand balance for all categories."""
    for category_key in ALL_CATEGORIES:
        plot_supply_demand_balance(category_key)


def plot_price_index(category_key: str):
    """Plot price index (base 100) for a commodity category."""
    setup_style()

    data = load_json('world_market_prices.json')
    cat_name, commodities = ALL_CATEGORIES[category_key]

    dates = [parse_date(d['date']) for d in data]

    fig, ax = plt.subplots(figsize=(14, 7))

    for commodity in commodities:
        if commodity in data[0] and data[0][commodity] > 0:
            base_price = data[0][commodity]
            index = [(d.get(commodity, 0) / base_price * 100) for d in data]

            color = get_commodity_color(commodity)
            label = commodity.replace('_', ' ').title()
            ax.plot(dates, index, label=label, linewidth=1.5,
                    color=color if color != '#888888' else None)

    ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Baseline')
    ax.set_title(f'{cat_name} Price Index (Base Year = 100)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Price Index')

    format_date_axis(ax, dates)
    ax.legend(loc='best', ncol=2)

    save_chart(f'price_index_{category_key}', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/price_index_{category_key}.png')


def plot_all_price_indices():
    """Plot price indices for all categories."""
    for category_key in ALL_CATEGORIES:
        plot_price_index(category_key)


def plot_category_price_comparison():
    """Plot composite price index comparison across all categories."""
    setup_style()

    data = load_json('world_market_prices.json')
    dates = [parse_date(d['date']) for d in data]

    def calc_category_index(commodities):
        """Calculate average price index for a category."""
        base_prices = {}
        for commodity in commodities:
            if commodity in data[0] and data[0][commodity] > 0:
                base_prices[commodity] = data[0][commodity]

        index = []
        for d in data:
            total = 0
            count = 0
            for commodity in commodities:
                if commodity in d and commodity in base_prices:
                    total += d[commodity] / base_prices[commodity]
                    count += 1
            index.append((total / count * 100) if count > 0 else 100)
        return index

    fig, ax = plt.subplots(figsize=(14, 7))

    colors = ['#2E86AB', '#E63946', '#2A9D8F', '#F18F01', '#9B2335']

    for i, (cat_key, (cat_name, commodities)) in enumerate(ALL_CATEGORIES.items()):
        index = calc_category_index(commodities)
        ax.plot(dates, index, label=cat_name, linewidth=2, color=colors[i % len(colors)])

    ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Baseline')
    ax.set_title('Category Price Index Comparison')
    ax.set_xlabel('Year')
    ax.set_ylabel('Price Index (Base Year = 100)')

    format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('category_comparison', subdir=SUBDIR)
    print(f'Saved: {SUBDIR}/category_comparison.png')


# =============================================================================
# Main Entry Point
# =============================================================================

def plot_all():
    """Generate all world market visualizations."""
    print("Generating world market charts...")

    # Category-level price charts
    print("  Category price charts...")
    plot_all_category_prices()

    # Category-level supply charts
    print("  Category supply charts...")
    plot_all_category_supply()

    # Category-level sold charts
    print("  Category sold charts...")
    plot_all_category_sold()

    # Supply/demand balance charts
    print("  Supply/demand balance charts...")
    plot_all_supply_demand_balance()

    # Price index charts
    print("  Price index charts...")
    plot_all_price_indices()
    plot_category_price_comparison()

    # Individual commodity charts (price only)
    print("  Individual price charts...")
    plot_all_individual_prices()

    # Individual supply charts
    print("  Individual supply charts...")
    plot_all_individual_supply()

    # Individual sold charts
    print("  Individual sold charts...")
    plot_all_individual_sold()

    # Full analysis charts (combined price/supply/sold)
    print("  Full commodity analysis charts...")
    plot_all_commodity_full()

    print("Done with world market!")


if __name__ == '__main__':
    plot_all()
