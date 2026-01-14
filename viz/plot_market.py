"""
Visualizations for world market data.
"""

import matplotlib.pyplot as plt
import numpy as np

from utils import (
    load_json,
    parse_date,
    setup_style,
    format_date_axis,
    save_chart,
    get_commodity_color,
)


# Commodity categories
RAW_RESOURCES = ['coal', 'iron', 'timber', 'cotton', 'wool', 'grain', 'cattle']
INDUSTRIAL_GOODS = ['steel', 'cement', 'machine_parts', 'fabric', 'lumber', 'glass', 'fertilizer']
CONSUMER_GOODS = ['regular_clothes', 'luxury_clothes', 'furniture', 'luxury_furniture', 'liquor', 'wine']
MILITARY_GOODS = ['ammunition', 'small_arms', 'artillery', 'canned_food', 'clipper_convoy', 'steamer_convoy']
LUXURY_RESOURCES = ['silk', 'dye', 'tea', 'coffee', 'opium', 'tobacco', 'tropical_wood']


def plot_commodity_prices(commodities: list[str], title: str, filename: str):
    """Plot prices for a list of commodities."""
    setup_style()
    data = load_json('world_market_prices.json')

    dates = [parse_date(d['date']) for d in data]

    fig, ax = plt.subplots(figsize=(14, 7))

    for commodity in commodities:
        if commodity in data[0]:
            values = [d.get(commodity, 0) for d in data]
            color = get_commodity_color(commodity)
            ax.plot(dates, values, label=commodity.replace('_', ' ').title(),
                   linewidth=1.5, color=color if color != '#888888' else None)

    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel('Price (£)')

    format_date_axis(ax, dates)
    ax.legend(loc='best', ncol=2)

    save_chart(filename)
    print(f'Saved: {filename}.png')


def plot_raw_resource_prices():
    """Plot raw resource prices."""
    plot_commodity_prices(RAW_RESOURCES, 'Raw Resource Prices', 'market_raw_resources')


def plot_industrial_prices():
    """Plot industrial goods prices."""
    plot_commodity_prices(INDUSTRIAL_GOODS, 'Industrial Goods Prices', 'market_industrial')


def plot_consumer_prices():
    """Plot consumer goods prices."""
    plot_commodity_prices(CONSUMER_GOODS, 'Consumer Goods Prices', 'market_consumer')


def plot_military_prices():
    """Plot military goods prices."""
    plot_commodity_prices(MILITARY_GOODS, 'Military Goods Prices', 'market_military')


def plot_luxury_prices():
    """Plot luxury resource prices."""
    plot_commodity_prices(LUXURY_RESOURCES, 'Luxury Resource Prices', 'market_luxury')


def plot_price_indices():
    """Plot composite price indices for different categories."""
    setup_style()
    data = load_json('world_market_prices.json')

    dates = [parse_date(d['date']) for d in data]

    # Calculate average price index for each category (normalized to first date)
    def calc_index(commodities):
        index = []
        base_prices = {}
        for commodity in commodities:
            if commodity in data[0]:
                base_prices[commodity] = data[0][commodity]

        for d in data:
            total = 0
            count = 0
            for commodity in commodities:
                if commodity in d and commodity in base_prices and base_prices[commodity] > 0:
                    total += d[commodity] / base_prices[commodity]
                    count += 1
            index.append((total / count * 100) if count > 0 else 100)
        return index

    raw_index = calc_index(RAW_RESOURCES)
    industrial_index = calc_index(INDUSTRIAL_GOODS)
    consumer_index = calc_index(CONSUMER_GOODS)
    military_index = calc_index(MILITARY_GOODS)

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(dates, raw_index, label='Raw Resources', linewidth=2, color='#2E86AB')
    ax.plot(dates, industrial_index, label='Industrial Goods', linewidth=2, color='#A23B72')
    ax.plot(dates, consumer_index, label='Consumer Goods', linewidth=2, color='#F18F01')
    ax.plot(dates, military_index, label='Military Goods', linewidth=2, color='#C73E1D')

    ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Baseline (100)')

    ax.set_title('Price Indices by Category (Base Year = 100)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Price Index')

    format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('market_price_indices')
    print('Saved: market_price_indices.png')


def plot_price_volatility():
    """Plot rolling volatility of key commodities."""
    setup_style()
    data = load_json('world_market_prices.json')

    dates = [parse_date(d['date']) for d in data]

    # Key commodities to track
    commodities = ['coal', 'iron', 'grain', 'cotton', 'steel']

    # Calculate rolling standard deviation (12-month window)
    window = 12

    fig, ax = plt.subplots(figsize=(14, 7))

    for commodity in commodities:
        if commodity not in data[0]:
            continue

        prices = [d.get(commodity, 0) for d in data]
        volatility = []

        for i in range(len(prices)):
            if i < window:
                volatility.append(np.nan)
            else:
                window_prices = prices[i-window:i]
                mean = np.mean(window_prices)
                if mean > 0:
                    std = np.std(window_prices)
                    volatility.append(std / mean * 100)  # Coefficient of variation
                else:
                    volatility.append(np.nan)

        color = get_commodity_color(commodity)
        ax.plot(dates, volatility, label=commodity.title(),
               linewidth=1.5, color=color if color != '#888888' else None)

    ax.set_title('Price Volatility (12-Month Rolling CV%)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Coefficient of Variation (%)')

    format_date_axis(ax, dates)
    ax.legend(loc='best')

    save_chart('market_volatility')
    print('Saved: market_volatility.png')


def plot_single_commodity(commodity: str):
    """Plot detailed view of a single commodity."""
    setup_style()
    data = load_json('world_market_prices.json')

    if commodity not in data[0]:
        print(f'Commodity {commodity} not found in data')
        return

    dates = [parse_date(d['date']) for d in data]
    prices = [d.get(commodity, 0) for d in data]

    fig, ax = plt.subplots()

    ax.plot(dates, prices, color='#2E86AB', linewidth=2)
    ax.fill_between(dates, prices, alpha=0.3, color='#2E86AB')

    # Add trend line
    x_numeric = np.arange(len(dates))
    z = np.polyfit(x_numeric, prices, 1)
    p = np.poly1d(z)
    ax.plot(dates, p(x_numeric), '--', color='#E63946', alpha=0.8, label='Trend')

    ax.set_title(f'{commodity.replace("_", " ").title()} Price Over Time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Price (£)')

    format_date_axis(ax, dates)
    ax.legend()

    save_chart(f'market_{commodity}')
    print(f'Saved: market_{commodity}.png')


def plot_all():
    """Generate all market visualizations."""
    print("Generating world market charts...")
    plot_raw_resource_prices()
    plot_industrial_prices()
    plot_consumer_prices()
    plot_military_prices()
    plot_luxury_prices()
    plot_price_indices()
    plot_price_volatility()

    # Individual commodity charts for key goods
    for commodity in ['coal', 'iron', 'steel', 'grain', 'cotton']:
        plot_single_commodity(commodity)

    print("Done!")


if __name__ == '__main__':
    plot_all()
