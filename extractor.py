"""
Economic data extraction from parsed Victoria 2 save files.

This module transforms the raw parsed data structures from parser.py into
structured Python dataclasses that represent Victoria 2's economic model.
It handles the complexity of extracting meaningful economic data from the
deeply nested save file structure.

VICTORIA 2 ECONOMIC MODEL OVERVIEW
==================================

Victoria 2 simulates a detailed 19th-century economic model with:

1. **POPs (Population Units)**: The basic economic actors
   - Each POP has a type (farmer, craftsman, capitalist, etc.)
   - POPs have money, bank savings, and satisfaction levels
   - 13 distinct POP types with different economic roles

2. **Factories**: Industrial production facilities
   - Located in states, employ craftsmen and clerks
   - Track income, spending, and profitability
   - Can be subsidized by the government

3. **RGOs (Resource Gathering Operations)**: Primary resource extraction
   - Located in provinces, employ farmers/labourers
   - Produce raw materials (grain, coal, iron, etc.)

4. **World Market**: Global commodity trading system
   - Tracks prices, supply, and demand for ~50 commodities
   - Countries trade through this market

DATA FLOW
=========

```
Save File (parsed dict)
         │
         ├──> World Market Data ──> WorldMarketData dataclass
         │
         ├──> Province Data ──────> POP extraction ──> PopData dataclass
         │                     └──> RGO extraction ──> RGOData dataclass
         │
         └──> Country Data ───────> Tax/spending extraction
                              └──> State extraction ──> StateData dataclass
                                                   └──> FactoryData dataclass
```

POP TYPES AND ECONOMIC ROLES
============================

| Type        | ID | Economic Role                           |
|-------------|----|-----------------------------------------|
| aristocrats |  0 | Landowners, receive farming output      |
| artisans    |  1 | Independent producers                   |
| bureaucrats |  2 | Government administration               |
| capitalists |  3 | Factory owners, invest in industry      |
| clergymen   |  4 | Religious/educational services          |
| clerks      |5/6 | Factory white-collar workers            |
| craftsmen   |  7 | Factory blue-collar workers             |
| farmers     |  8 | Agricultural workers in RGOs            |
| labourers   |  9 | Manual labor in RGOs                    |
| officers    | 10 | Military leadership                     |
| soldiers    | 11 | Military personnel                      |
| slaves      | 12 | Unfree labor (in slave-holding nations) |

Note: Some POP types have alternate IDs in different contexts (clerks: 5 or 6).

USAGE EXAMPLE
=============

```python
from parser import parse_save_file, iterate_province_sections
from extractor import extract_world_market, extract_country_data, SaveData

# Parse the save file
data = parse_save_file("save.v2")

# Extract world market data
world_market = extract_world_market(data)
print(f"Iron price: {world_market.prices.get('iron', 0)}")

# Build province dictionary for country extraction
provinces = {}
for prov_id, prov_data in iterate_province_sections("save.v2"):
    provinces[prov_id] = prov_data

# Extract country data
eng_data = extract_country_data("ENG", data["ENG"], provinces)
print(f"UK Treasury: {eng_data.treasury}")
print(f"UK Population: {eng_data.pop_data.total_population}")
```

Author: Victoria 2 Economy Analysis Tool Project
"""

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# POP TYPE DEFINITIONS
# =============================================================================

# Mapping from POP type name to numeric ID as used in save files
# Victoria 2 internally uses numeric IDs to reference POP types
POP_TYPES = {
    'aristocrats': 0,   # Landowners - receive portion of RGO output
    'artisans': 1,      # Independent craftsmen - produce goods individually
    'bureaucrats': 2,   # Government workers - provide administrative efficiency
    'capitalists': 3,   # Factory owners - build factories, receive profits
    'clergymen': 4,     # Religious leaders - provide education and reduce militancy
    'clerks': 5,        # Factory clerks - white-collar factory workers
    'craftsmen': 7,     # Factory workers - blue-collar factory workers
    'farmers': 8,       # Agricultural workers - work in farming RGOs
    'labourers': 9,     # Manual laborers - work in non-farming RGOs (mines, etc.)
    'officers': 10,     # Military officers - lead military units
    'soldiers': 11,     # Military soldiers - form military units
    'slaves': 12,       # Slaves - unfree labor in slave-holding nations
}

# Reverse mapping: ID to type name (for parsing save files that use numeric IDs)
POP_TYPE_BY_ID = {v: k for k, v in POP_TYPES.items()}

# Handle alternate IDs that appear in some contexts in the save file
# This is necessary because Victoria 2 sometimes uses different IDs for the same type
POP_TYPE_BY_ID[6] = 'clerks'      # Clerks can appear as either 5 or 6
POP_TYPE_BY_ID[9] = 'labourers'   # Labourers ID confirmation


# =============================================================================
# DATA CLASSES - Economic Data Structures
# =============================================================================

@dataclass
class WorldMarketData:
    """
    World market economic data representing the global commodity market.

    Victoria 2's world market is a central exchange where all countries
    trade commodities. Prices fluctuate based on global supply and demand.

    Attributes:
        prices: Current market prices for each commodity
                Key: commodity name (e.g., "iron", "grain", "fabric")
                Value: price in pounds sterling

        supply: Total quantity supplied to the market by all producers
                Includes factory output, RGO production, and artisan goods

        demand: Total quantity demanded by all consumers
                Includes factory inputs, POP consumption, military needs

        actual_sold: Actual quantity sold (may be less than supply if
                     demand is insufficient)

    Example Commodities:
        Raw materials: iron, coal, sulphur, timber, wool
        Agricultural: grain, cattle, fish, fruit, tea, coffee
        Industrial: steel, cement, fabric, paper, glass
        Consumer: clothes, furniture, luxury_clothes, luxury_furniture
        Military: small_arms, ammunition, artillery, canned_food

    Market Mechanics:
        - Prices rise when demand exceeds supply
        - Prices fall when supply exceeds demand
        - Base prices are defined in game files, actual prices fluctuate
    """
    prices: dict[str, float] = field(default_factory=dict)
    supply: dict[str, float] = field(default_factory=dict)
    demand: dict[str, float] = field(default_factory=dict)
    actual_sold: dict[str, float] = field(default_factory=dict)


@dataclass
class PopData:
    """
    Aggregated POP (population) data for a country or the entire world.

    POPs are the fundamental economic and social units in Victoria 2.
    This dataclass aggregates statistics across all POPs of a given scope.

    Attributes:
        total_population: Sum of all POP sizes (in individual people)
                         Victoria 2 typically has millions of POPs globally

        population_by_type: Population count broken down by POP type
                           Key: POP type name (e.g., "farmers", "craftsmen")
                           Value: population count

        total_money: Sum of all cash holdings across all POPs
                    This is liquid money, not including bank savings

        total_bank_savings: Sum of all bank deposits across all POPs
                           Represents wealth stored in national banks

        money_by_type: Cash holdings broken down by POP type
                      Useful for analyzing wealth distribution

        avg_life_needs: Population-weighted average of life needs satisfaction
                       Range: 0.0 (starving) to 1.0+ (fully satisfied)
                       Life needs include: food, fuel, basic clothing

        avg_everyday_needs: Population-weighted average of everyday needs
                           Range: 0.0 to 1.0+
                           Everyday needs include: services, furniture, etc.

        avg_luxury_needs: Population-weighted average of luxury needs
                         Range: 0.0 to 1.0+
                         Luxury needs include: luxury goods, entertainment

        avg_literacy: Population-weighted average literacy rate
                     Range: 0.0 (illiterate) to 1.0 (fully literate)
                     Affects political awareness and reform desire

        avg_consciousness: Population-weighted political consciousness
                          Range: 0.0 to 10.0
                          Higher values mean more political awareness

        avg_militancy: Population-weighted militancy level
                      Range: 0.0 to 10.0
                      Higher values increase revolt risk

        employed_*: Employment counts for industrial/agricultural work
                   Used for tracking economic activity

    Needs Satisfaction Mechanics:
        - POPs use their money to buy goods fulfilling their needs
        - Unsatisfied needs cause population decline, emigration, militancy
        - Different POP types have different needs profiles
    """
    total_population: int = 0
    population_by_type: dict[str, int] = field(default_factory=dict)
    total_money: float = 0.0
    total_bank_savings: float = 0.0
    money_by_type: dict[str, float] = field(default_factory=dict)
    avg_life_needs: float = 0.0
    avg_everyday_needs: float = 0.0
    avg_luxury_needs: float = 0.0
    avg_literacy: float = 0.0
    avg_consciousness: float = 0.0
    avg_militancy: float = 0.0
    employed_craftsmen: int = 0
    employed_clerks: int = 0
    employed_labourers: int = 0
    employed_farmers: int = 0


@dataclass
class FactoryData:
    """
    Economic data for a single factory.

    Factories are the core of Victoria 2's industrial economy. They
    transform input goods into output goods, employing craftsmen and clerks.

    Attributes:
        name: Factory type identifier (e.g., "steel_factory", "fabric_factory")
              This maps to definitions in the game's production files

        level: Factory level (1-99), determines production capacity
               Each level adds to the factory's throughput and employment

        money: Current cash reserves of the factory
               Used for purchasing inputs and paying wages

        last_income: Revenue from last production cycle
                    Income = output goods sold at market price

        last_spending: Expenditure from last production cycle
                      Spending = input goods + wages

        wages_paid: Total wages paid to workers last cycle
                   Split between craftsmen and clerks based on employment

        unprofitable_days: Number of days the factory has been unprofitable
                          Used for closure decisions; high values risk shutdown

        subsidised: Whether the factory receives government subsidies
                   Subsidized factories can operate at a loss

        employed_craftsmen: Number of craftsmen (blue-collar) workers
        employed_clerks: Number of clerks (white-collar) workers

        produces: Quantity of goods produced in last cycle
                 Depends on level, throughput bonuses, and employment

    Factory Economics:
        Profit = last_income - last_spending
        If unprofitable for 365 days, factory may close
        Capitalist POPs invest in profitable factories
    """
    name: str = ""
    level: int = 0
    money: float = 0.0
    last_income: float = 0.0
    last_spending: float = 0.0
    wages_paid: float = 0.0
    unprofitable_days: int = 0
    subsidised: bool = False
    employed_craftsmen: int = 0
    employed_clerks: int = 0
    produces: float = 0.0


@dataclass
class StateData:
    """
    Economic data for a state (collection of provinces).

    States are the administrative units in Victoria 2 where factories
    can be built. Each country consists of multiple states.

    Attributes:
        provinces: List of province IDs belonging to this state
                  Provinces are the smallest geographic units

        is_colonial: Colonial status (0 = full state, 1+ = colonial)
                    Colonial states have different rules (e.g., can't build
                    certain factories, population treated differently)

        savings: State-level cash reserves (used for factory construction)

        factories: List of all factories in this state
                  Factories are built at state level, not province level

        total_factory_employment: Sum of all factory workers in the state
        total_factory_income: Sum of all factory income in the state

    State Economics:
        - Factory construction happens at state level
        - State populations provide factory workforce
        - Colonial states have reduced industrial capacity
    """
    provinces: list[int] = field(default_factory=list)
    is_colonial: int = 0
    savings: float = 0.0
    factories: list[FactoryData] = field(default_factory=list)
    total_factory_employment: int = 0
    total_factory_income: float = 0.0


@dataclass
class RGOData:
    """
    RGO (Resource Gathering Operation) data for a province.

    RGOs represent primary production in provinces: farming, mining,
    logging, etc. Each province has one RGO type determined by terrain.

    Attributes:
        goods_type: Type of commodity produced (e.g., "grain", "iron", "coal")
                   Determined by province's defined RGO in game files

        last_income: Revenue from last production cycle
                    Income = goods produced * market price

        total_employed: Total workers in the RGO
                       Farmers for agricultural RGOs
                       Labourers for mining/extraction RGOs

    RGO Mechanics:
        - Output depends on province size and RGO efficiency
        - Aristocrats receive a portion of RGO profits
        - Technology and reforms affect RGO throughput
    """
    goods_type: str = ""
    last_income: float = 0.0
    total_employed: int = 0


@dataclass
class CountryData:
    """
    Comprehensive economic data for a single country.

    This dataclass aggregates all economic information for a nation,
    including government finances, population, industry, and agriculture.

    Attributes:
        tag: 3-letter country tag (e.g., "ENG", "FRA", "PRU", "USA")
             This is the unique identifier for the country

        treasury: Current government cash reserves
                 Used for government spending, war costs, investments

        bank_reserves: Money held in the national bank
        bank_money_lent: Money lent out by the national bank

        prestige: National prestige score (affects great power ranking)
        infamy: "Badboy" score - accumulated from unjustified wars
                High infamy can trigger containment wars

        tax_base: Total taxable income in the country
        civilized: Whether the country is "civilized" or "uncivilized"
                  Uncivilized nations have severe penalties

        Tax Rates and Income:
            rich_tax_rate/income: Taxation of aristocrats, capitalists
            middle_tax_rate/income: Taxation of artisans, clerks, bureaucrats
            poor_tax_rate/income: Taxation of farmers, labourers, craftsmen

        Spending:
            education_spending: Education budget (0.0 to 1.0 slider)
            military_spending: Military budget
            social_spending: Social programs (healthcare, pensions)

        pop_data: Aggregated population data (PopData instance)

        states: List of all states owned by this country

        Factory Aggregates:
            total_factory_count: Number of factories
            total_factory_levels: Sum of all factory levels
            total_factory_income: Sum of all factory income
            total_factory_employment: Sum of all factory workers

        RGO Aggregates:
            total_rgo_income: Sum of all RGO income
            total_rgo_employment: Sum of all RGO workers

    Economic Balance:
        Government Revenue = Tax Income + Tariffs + Gold Income
        Government Spending = Administration + Military + Subsidies + Debt
    """
    tag: str = ""
    treasury: float = 0.0
    bank_reserves: float = 0.0
    bank_money_lent: float = 0.0
    prestige: float = 0.0
    infamy: float = 0.0
    tax_base: float = 0.0
    civilized: bool = True

    # Tax data - Victoria 2 has 3-tier taxation system
    rich_tax_rate: float = 0.0       # Slider position (0.0 to 1.0)
    middle_tax_rate: float = 0.0
    poor_tax_rate: float = 0.0
    rich_tax_income: float = 0.0     # Actual tax revenue collected
    middle_tax_income: float = 0.0
    poor_tax_income: float = 0.0

    # Government spending sliders (0.0 to 1.0)
    education_spending: float = 0.0   # Affects literacy growth
    military_spending: float = 0.0    # Affects soldier quality
    social_spending: float = 0.0      # Affects POP needs satisfaction

    # POP data - comprehensive population statistics
    pop_data: PopData = field(default_factory=PopData)

    # States and factories
    states: list[StateData] = field(default_factory=list)
    total_factory_count: int = 0
    total_factory_levels: int = 0
    total_factory_income: float = 0.0
    total_factory_employment: int = 0

    # RGO (Resource Gathering Operation) data
    total_rgo_income: float = 0.0
    total_rgo_employment: int = 0


@dataclass
class SaveData:
    """
    Complete economic data from a save file.

    This is the top-level container holding all extracted data from
    a single save file, representing a snapshot of the game state.

    Attributes:
        date: In-game date in "YYYY.M.D" format (e.g., "1836.1.1")
              Victoria 2 spans 1836-1936

        world_market: Global commodity market data
                     Prices, supply, and demand for all goods

        countries: Dictionary of all country data
                  Key: country tag (e.g., "ENG")
                  Value: CountryData instance

        global_pop_data: World-aggregated population statistics
                        Sum/average of all countries' POP data

    Temporal Analysis:
        By processing multiple save files from different dates,
        you can track economic trends over time:
        - Population growth
        - Industrialization progress
        - Price fluctuations
        - Wealth accumulation
    """
    date: str = ""
    world_market: WorldMarketData = field(default_factory=WorldMarketData)
    countries: dict[str, CountryData] = field(default_factory=dict)
    global_pop_data: PopData = field(default_factory=PopData)


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_world_market(data: dict) -> WorldMarketData:
    """
    Extract world market data from parsed save file.

    The world market data is stored in the 'worldmarket' section of the
    save file and contains global commodity trading information.

    Args:
        data: Complete parsed save file dictionary

    Returns:
        WorldMarketData: Extracted market data with prices, supply, and sales

    Example:
        >>> data = parse_save_file("save.v2")
        >>> market = extract_world_market(data)
        >>> print(f"Iron price: {market.prices.get('iron', 0):.3f}")
        >>> print(f"Iron supply: {market.supply.get('iron', 0):.0f}")

    Save File Structure:
        worldmarket={
            price_pool={ iron=35.000 coal=2.300 ... }
            supply_pool={ iron=1000.000 coal=5000.000 ... }
            actual_sold={ iron=950.000 coal=4800.000 ... }
        }
    """
    result = WorldMarketData()

    # Navigate to the worldmarket section
    wm = data.get('worldmarket', {})
    if isinstance(wm, dict):
        # Extract prices from price_pool
        # Price is in pounds sterling per unit
        prices = wm.get('price_pool', {})
        if isinstance(prices, dict):
            result.prices = {k: float(v) for k, v in prices.items()
                           if isinstance(v, (int, float))}

        # Extract supply from supply_pool
        # Supply is the total quantity available on the market
        supply = wm.get('supply_pool', {})
        if isinstance(supply, dict):
            result.supply = {k: float(v) for k, v in supply.items()
                           if isinstance(v, (int, float))}

        # Extract actual sold quantities
        # This is how much was actually purchased (may be less than supply)
        sold = wm.get('actual_sold', {})
        if isinstance(sold, dict):
            result.actual_sold = {k: float(v) for k, v in sold.items()
                                 if isinstance(v, (int, float))}

    return result


def safe_float(value, default=0.0) -> float:
    """
    Safely convert a value to float with error handling.

    Paradox save files can have unexpected data types or malformed values.
    This function provides robust conversion with fallback to a default.

    Args:
        value: Value to convert (can be int, float, str, or other)
        default: Value to return if conversion fails

    Returns:
        float: Converted value, or default if conversion fails

    Examples:
        >>> safe_float(100)          # 100.0
        >>> safe_float("50.5")       # 50.5
        >>> safe_float("invalid")    # 0.0 (default)
        >>> safe_float(None, -1.0)   # -1.0 (custom default)
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def safe_int(value, default=0) -> int:
    """
    Safely convert a value to int with error handling.

    Similar to safe_float, handles the various data types that can
    appear in save files and provides robust conversion.

    Args:
        value: Value to convert
        default: Value to return if conversion fails

    Returns:
        int: Converted value, or default if conversion fails

    Examples:
        >>> safe_int(100)            # 100
        >>> safe_int(50.7)           # 50 (truncated, not rounded)
        >>> safe_int("25")           # 25
        >>> safe_int("invalid")      # 0 (default)
    """
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)  # Truncate float to int
    if isinstance(value, str):
        try:
            # Handle string floats like "100.0" -> 100
            return int(float(value))
        except ValueError:
            return default
    return default


def extract_pop_from_block(pop_type: str, pop_block: dict) -> dict:
    """
    Extract data from a single POP block in the save file.

    Each POP in a province is stored as a separate block containing
    demographics, wealth, and satisfaction data.

    Args:
        pop_type: Type of POP (e.g., "farmers", "craftsmen")
        pop_block: Parsed dictionary for this POP's data block

    Returns:
        dict: Extracted POP data, or None if invalid input

    Returned Dictionary Keys:
        - type: POP type name
        - size: Number of individuals in this POP unit
        - money: Cash holdings
        - bank: Bank savings
        - life_needs: Life needs satisfaction (0.0-1.0+)
        - everyday_needs: Everyday needs satisfaction
        - luxury_needs: Luxury needs satisfaction
        - literacy: Literacy rate (0.0-1.0)
        - con: Political consciousness (0-10)
        - mil: Militancy (0-10)

    Save File Structure:
        farmers={
            size=50000
            money=1234.567
            bank=500.000
            life_needs=0.850
            everyday_needs=0.600
            luxury_needs=0.200
            literacy=0.150
            con=2.500
            mil=1.200
        }
    """
    if not isinstance(pop_block, dict):
        return None

    return {
        'type': pop_type,
        'size': safe_int(pop_block.get('size', 0)),
        'money': safe_float(pop_block.get('money', 0.0)),
        'bank': safe_float(pop_block.get('bank', 0.0)),
        'life_needs': safe_float(pop_block.get('life_needs', 0.0)),
        'everyday_needs': safe_float(pop_block.get('everyday_needs', 0.0)),
        'luxury_needs': safe_float(pop_block.get('luxury_needs', 0.0)),
        'literacy': safe_float(pop_block.get('literacy', 0.0)),
        'con': safe_float(pop_block.get('con', 0.0)),       # consciousness
        'mil': safe_float(pop_block.get('mil', 0.0)),       # militancy
    }


def extract_factory_data(building_block: dict) -> FactoryData:
    """
    Extract factory data from a state_buildings block.

    Factories are stored in states within the country block. Each factory
    block contains production and employment information.

    Args:
        building_block: Parsed dictionary for a factory's data block

    Returns:
        FactoryData: Extracted factory data

    Employment Extraction:
        Factory employment is stored in a nested structure:
        employment={
            employees={
                { province_pop_id={ type=7 } count=500 }  # craftsmen
                { province_pop_id={ type=5 } count=100 }  # clerks
            }
        }

    Save File Structure:
        state_buildings={
            building="steel_factory"
            level=3
            money=5000.000
            last_income=1200.000
            last_spending=800.000
            pops_paychecks=600.000
            unprofitable_days=0
            subsidised=no
            produces=50.000
            employment={
                employees={
                    { province_pop_id={ type=7 index=0 } count=1500 }
                    { province_pop_id={ type=5 index=0 } count=300 }
                }
            }
        }
    """
    factory = FactoryData()

    # Basic factory information
    factory.name = str(building_block.get('building', ''))
    factory.level = safe_int(building_block.get('level', 0))
    factory.money = safe_float(building_block.get('money', 0.0))

    # Production economics
    factory.last_income = safe_float(building_block.get('last_income', 0.0))
    factory.last_spending = safe_float(building_block.get('last_spending', 0.0))
    factory.wages_paid = safe_float(building_block.get('pops_paychecks', 0.0))
    factory.unprofitable_days = safe_int(building_block.get('unprofitable_days', 0))
    factory.subsidised = building_block.get('subsidised', False)
    factory.produces = safe_float(building_block.get('produces', 0.0))

    # Extract employment data from nested structure
    employment = building_block.get('employment', {})
    if isinstance(employment, dict):
        employees = employment.get('employees', [])
        if isinstance(employees, list):
            for emp in employees:
                if isinstance(emp, dict):
                    # Get the POP type from the province_pop_id reference
                    pop_id = emp.get('province_pop_id', {})
                    if isinstance(pop_id, dict):
                        pop_type_id = safe_int(pop_id.get('type', -1), -1)
                        count = safe_int(emp.get('count', 0))

                        # Categorize by POP type ID
                        if pop_type_id in (5, 6):  # clerks (alternate IDs)
                            factory.employed_clerks += count
                        elif pop_type_id == 7:      # craftsmen
                            factory.employed_craftsmen += count

    return factory


def extract_rgo_data(rgo_block: dict) -> RGOData:
    """
    Extract RGO data from a province's rgo block.

    Each province has one RGO that produces primary commodities
    (agricultural or mining products).

    Args:
        rgo_block: Parsed dictionary for the province's RGO data

    Returns:
        RGOData: Extracted RGO data

    Save File Structure:
        rgo={
            goods_type="grain"
            last_income=500.000
            employment={
                employees={
                    { province_pop_id={ type=8 } count=10000 }  # farmers
                }
            }
        }
    """
    rgo = RGOData()

    # Basic RGO information
    rgo.goods_type = str(rgo_block.get('goods_type', ''))
    rgo.last_income = safe_float(rgo_block.get('last_income', 0.0))

    # Extract employment (similar structure to factories)
    employment = rgo_block.get('employment', {})
    if isinstance(employment, dict):
        employees = employment.get('employees', [])
        if isinstance(employees, list):
            for emp in employees:
                if isinstance(emp, dict):
                    count = safe_int(emp.get('count', 0))
                    rgo.total_employed += count

    return rgo


def extract_state_data(state_block: dict) -> StateData:
    """
    Extract state data including all factories.

    States are collections of provinces that can build factories.
    This function extracts state-level economic information.

    Args:
        state_block: Parsed dictionary for a state's data

    Returns:
        StateData: Extracted state data with factories

    Save File Structure:
        state={
            provinces={ 300 301 302 }
            is_colonial=0
            savings=10000.000
            state_buildings={
                building="fabric_factory"
                level=2
                ...
            }
            state_buildings={
                building="steel_factory"
                level=1
                ...
            }
        }

    Note:
        state_buildings can appear as a single dict (one factory)
        or a list of dicts (multiple factories). This function
        handles both cases.
    """
    state = StateData()

    # Get provinces belonging to this state
    provinces = state_block.get('provinces', [])
    if isinstance(provinces, list):
        state.provinces = [p for p in provinces if isinstance(p, int)]

    # Colonial status (0 = full state, higher = colonial)
    state.is_colonial = state_block.get('is_colonial', 0)
    state.savings = state_block.get('savings', 0.0)

    # Extract factories from state_buildings
    # Handle both single factory (dict) and multiple factories (list)
    buildings = state_block.get('state_buildings', [])
    if isinstance(buildings, dict):
        buildings = [buildings]  # Wrap single factory in list
    elif not isinstance(buildings, list):
        buildings = []

    # Process each factory
    for building in buildings:
        if isinstance(building, dict) and 'building' in building:
            factory = extract_factory_data(building)
            state.factories.append(factory)

            # Aggregate state-level totals
            state.total_factory_employment += (factory.employed_craftsmen +
                                               factory.employed_clerks)
            state.total_factory_income += factory.last_income

    return state


def extract_country_data(tag: str, country_block: dict,
                         provinces: dict[int, dict]) -> CountryData:
    """
    Extract all economic data for a country.

    This is the main extraction function for country-level data. It
    processes government finances, states, factories, and aggregates
    POP data from all owned provinces.

    Args:
        tag: 3-letter country tag (e.g., "ENG", "FRA")
        country_block: Parsed dictionary for this country's data
        provinces: Dictionary of all province data (from iterate_province_sections)
                  Key: province ID, Value: province data dict

    Returns:
        CountryData: Complete economic data for the country

    Processing Steps:
        1. Extract basic country info (treasury, prestige, infamy)
        2. Extract bank data
        3. Extract tax rates and income
        4. Extract spending sliders
        5. Process all states and factories
        6. Identify owned provinces and extract POPs and RGOs
        7. Calculate population-weighted averages

    Example:
        >>> provinces = dict(iterate_province_sections("save.v2"))
        >>> country = extract_country_data("ENG", data["ENG"], provinces)
        >>> print(f"UK Treasury: {country.treasury:,.0f}")
        >>> print(f"UK Population: {country.pop_data.total_population:,}")
    """
    country = CountryData()
    country.tag = tag

    # ==== BASIC COUNTRY DATA ====
    # Treasury is stored as 'money' in the save file
    country.treasury = safe_float(country_block.get('money', 0.0))
    country.prestige = safe_float(country_block.get('prestige', 0.0))
    # Infamy is stored as 'badboy' (historical term for diplomatic reputation)
    country.infamy = safe_float(country_block.get('badboy', 0.0))
    country.tax_base = safe_float(country_block.get('tax_base', 0.0))
    country.civilized = country_block.get('civilized', True)

    # ==== BANK DATA ====
    bank = country_block.get('bank', {})
    if isinstance(bank, dict):
        country.bank_reserves = safe_float(bank.get('money', 0.0))
        country.bank_money_lent = safe_float(bank.get('money_lent', 0.0))

    # ==== TAX DATA ====
    # Victoria 2 has three tax tiers: rich, middle, poor
    # Each has a 'current' rate (slider position) and 'total' income collected
    rich_tax = country_block.get('rich_tax', {})
    if isinstance(rich_tax, dict):
        country.rich_tax_rate = safe_float(rich_tax.get('current', 0.0))
        country.rich_tax_income = safe_float(rich_tax.get('total', 0.0))

    middle_tax = country_block.get('middle_tax', {})
    if isinstance(middle_tax, dict):
        country.middle_tax_rate = safe_float(middle_tax.get('current', 0.0))
        country.middle_tax_income = safe_float(middle_tax.get('total', 0.0))

    poor_tax = country_block.get('poor_tax', {})
    if isinstance(poor_tax, dict):
        country.poor_tax_rate = safe_float(poor_tax.get('current', 0.0))
        country.poor_tax_income = safe_float(poor_tax.get('total', 0.0))

    # ==== SPENDING SLIDERS ====
    # Stored with 'settings' containing the slider position (0.0 to 1.0)
    edu = country_block.get('education_spending', {})
    if isinstance(edu, dict):
        country.education_spending = safe_float(edu.get('settings', 0.0))

    mil = country_block.get('military_spending', {})
    if isinstance(mil, dict):
        country.military_spending = safe_float(mil.get('settings', 0.0))

    social = country_block.get('social_spending', {})
    if isinstance(social, dict):
        country.social_spending = safe_float(social.get('settings', 0.0))

    # ==== STATES AND FACTORIES ====
    # Handle both single state (dict) and multiple states (list)
    states = country_block.get('state', [])
    if isinstance(states, dict):
        states = [states]
    elif not isinstance(states, list):
        states = []

    for state_block in states:
        if isinstance(state_block, dict):
            state = extract_state_data(state_block)
            country.states.append(state)

            # Aggregate country-level factory totals
            country.total_factory_employment += state.total_factory_employment
            country.total_factory_income += state.total_factory_income

            for factory in state.factories:
                country.total_factory_count += 1
                country.total_factory_levels += factory.level

    # ==== PROVINCE DATA (POPs and RGOs) ====
    # Find all provinces owned by this country
    owned_provinces = []
    for prov_id, prov_data in provinces.items():
        if isinstance(prov_data, dict) and prov_data.get('owner') == tag:
            owned_provinces.append((prov_id, prov_data))

    # ==== POP DATA AGGREGATION ====
    # We need to aggregate data from all POPs and calculate weighted averages
    pop_data = PopData()

    # Accumulators for weighted average calculation
    total_weighted_needs = {'life': 0.0, 'everyday': 0.0, 'luxury': 0.0}
    total_weighted_literacy = 0.0
    total_weighted_con = 0.0
    total_weighted_mil = 0.0

    # Process each owned province
    for prov_id, prov_data in owned_provinces:
        # Extract RGO data
        rgo_block = prov_data.get('rgo', {})
        if isinstance(rgo_block, dict):
            rgo = extract_rgo_data(rgo_block)
            country.total_rgo_income += rgo.last_income
            country.total_rgo_employment += rgo.total_employed

        # Extract POP data for each POP type
        for pop_type in POP_TYPES.keys():
            pops = prov_data.get(pop_type, [])

            # Handle single POP (dict) or multiple POPs (list) of same type
            if isinstance(pops, dict):
                pops = [pops]
            elif not isinstance(pops, list):
                continue

            # Process each POP unit of this type
            for pop_block in pops:
                pop = extract_pop_from_block(pop_type, pop_block)
                if pop:
                    size = pop['size']

                    # Aggregate totals
                    pop_data.total_population += size
                    pop_data.population_by_type[pop_type] = (
                        pop_data.population_by_type.get(pop_type, 0) + size
                    )
                    pop_data.total_money += pop['money']
                    pop_data.total_bank_savings += pop['bank']
                    pop_data.money_by_type[pop_type] = (
                        pop_data.money_by_type.get(pop_type, 0.0) + pop['money']
                    )

                    # Accumulate weighted values for averaging
                    # Weight = POP size (bigger POPs count more)
                    total_weighted_needs['life'] += pop['life_needs'] * size
                    total_weighted_needs['everyday'] += pop['everyday_needs'] * size
                    total_weighted_needs['luxury'] += pop['luxury_needs'] * size
                    total_weighted_literacy += pop['literacy'] * size
                    total_weighted_con += pop['con'] * size
                    total_weighted_mil += pop['mil'] * size

    # ==== CALCULATE WEIGHTED AVERAGES ====
    # Divide weighted sums by total population to get averages
    if pop_data.total_population > 0:
        pop_data.avg_life_needs = (total_weighted_needs['life'] /
                                   pop_data.total_population)
        pop_data.avg_everyday_needs = (total_weighted_needs['everyday'] /
                                       pop_data.total_population)
        pop_data.avg_luxury_needs = (total_weighted_needs['luxury'] /
                                     pop_data.total_population)
        pop_data.avg_literacy = total_weighted_literacy / pop_data.total_population
        pop_data.avg_consciousness = total_weighted_con / pop_data.total_population
        pop_data.avg_militancy = total_weighted_mil / pop_data.total_population

    # ==== EMPLOYMENT DATA ====
    # Factory employment comes from factory data, RGO from province data
    pop_data.employed_craftsmen = country.total_factory_employment  # Approximation
    pop_data.employed_labourers = country.total_rgo_employment      # RGO workers

    country.pop_data = pop_data
    return country


def aggregate_global_pop_data(countries: dict[str, CountryData]) -> PopData:
    """
    Aggregate POP data across all countries to get world totals.

    This function sums population and economic data from all countries
    and calculates population-weighted global averages.

    Args:
        countries: Dictionary of all country data
                  Key: country tag, Value: CountryData instance

    Returns:
        PopData: Global aggregated population data

    Calculation Method:
        - Totals: Simple sum across all countries
        - Averages: Weighted by each country's population size
          global_avg = sum(country_avg * country_pop) / total_pop

    Example:
        >>> countries = {"ENG": eng_data, "FRA": fra_data, ...}
        >>> world_pop = aggregate_global_pop_data(countries)
        >>> print(f"World population: {world_pop.total_population:,}")
        >>> print(f"World literacy: {world_pop.avg_literacy:.1%}")
    """
    global_pop = PopData()

    # ==== AGGREGATE TOTALS ====
    for country in countries.values():
        pd = country.pop_data

        # Sum totals
        global_pop.total_population += pd.total_population
        global_pop.total_money += pd.total_money
        global_pop.total_bank_savings += pd.total_bank_savings

        # Sum population by type
        for pop_type, count in pd.population_by_type.items():
            global_pop.population_by_type[pop_type] = (
                global_pop.population_by_type.get(pop_type, 0) + count
            )

        # Sum money by type
        for pop_type, money in pd.money_by_type.items():
            global_pop.money_by_type[pop_type] = (
                global_pop.money_by_type.get(pop_type, 0.0) + money
            )

        # Sum employment
        global_pop.employed_craftsmen += pd.employed_craftsmen
        global_pop.employed_clerks += pd.employed_clerks
        global_pop.employed_labourers += pd.employed_labourers
        global_pop.employed_farmers += pd.employed_farmers

    # ==== CALCULATE WEIGHTED GLOBAL AVERAGES ====
    # Each country's average is weighted by its population
    total_pop = global_pop.total_population
    if total_pop > 0:
        # Sum of (country_average * country_population) for each metric
        weighted_life = sum(c.pop_data.avg_life_needs * c.pop_data.total_population
                          for c in countries.values())
        weighted_everyday = sum(c.pop_data.avg_everyday_needs * c.pop_data.total_population
                               for c in countries.values())
        weighted_luxury = sum(c.pop_data.avg_luxury_needs * c.pop_data.total_population
                             for c in countries.values())
        weighted_literacy = sum(c.pop_data.avg_literacy * c.pop_data.total_population
                               for c in countries.values())
        weighted_con = sum(c.pop_data.avg_consciousness * c.pop_data.total_population
                          for c in countries.values())
        weighted_mil = sum(c.pop_data.avg_militancy * c.pop_data.total_population
                          for c in countries.values())

        # Divide by total population to get weighted average
        global_pop.avg_life_needs = weighted_life / total_pop
        global_pop.avg_everyday_needs = weighted_everyday / total_pop
        global_pop.avg_luxury_needs = weighted_luxury / total_pop
        global_pop.avg_literacy = weighted_literacy / total_pop
        global_pop.avg_consciousness = weighted_con / total_pop
        global_pop.avg_militancy = weighted_mil / total_pop

    return global_pop
