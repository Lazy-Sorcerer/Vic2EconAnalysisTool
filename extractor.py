"""
Economic data extraction from parsed Victoria 2 save files.
"""

from dataclasses import dataclass, field
from typing import Any


# POP type mapping
POP_TYPES = {
    'aristocrats': 0,
    'artisans': 1,
    'bureaucrats': 2,
    'capitalists': 3,
    'clergymen': 4,
    'clerks': 5,
    'craftsmen': 7,
    'farmers': 8,
    'labourers': 9,
    'officers': 10,
    'soldiers': 11,
    'slaves': 12,
}

POP_TYPE_BY_ID = {v: k for k, v in POP_TYPES.items()}
# Handle alternate IDs
POP_TYPE_BY_ID[6] = 'clerks'
POP_TYPE_BY_ID[9] = 'labourers'


@dataclass
class WorldMarketData:
    """World market economic data."""
    prices: dict[str, float] = field(default_factory=dict)
    supply: dict[str, float] = field(default_factory=dict)
    demand: dict[str, float] = field(default_factory=dict)
    actual_sold: dict[str, float] = field(default_factory=dict)


@dataclass
class PopData:
    """Aggregated POP data for a country."""
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
    """Factory economic data."""
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
    """State economic data."""
    provinces: list[int] = field(default_factory=list)
    is_colonial: int = 0
    savings: float = 0.0
    factories: list[FactoryData] = field(default_factory=list)
    total_factory_employment: int = 0
    total_factory_income: float = 0.0


@dataclass
class RGOData:
    """RGO data for a province."""
    goods_type: str = ""
    last_income: float = 0.0
    total_employed: int = 0


@dataclass
class CountryData:
    """Economic data for a country."""
    tag: str = ""
    treasury: float = 0.0
    bank_reserves: float = 0.0
    bank_money_lent: float = 0.0
    prestige: float = 0.0
    infamy: float = 0.0
    tax_base: float = 0.0
    civilized: bool = True

    # Tax data
    rich_tax_rate: float = 0.0
    middle_tax_rate: float = 0.0
    poor_tax_rate: float = 0.0
    rich_tax_income: float = 0.0
    middle_tax_income: float = 0.0
    poor_tax_income: float = 0.0

    # Spending
    education_spending: float = 0.0
    military_spending: float = 0.0
    social_spending: float = 0.0

    # POP data
    pop_data: PopData = field(default_factory=PopData)

    # States and factories
    states: list[StateData] = field(default_factory=list)
    total_factory_count: int = 0
    total_factory_levels: int = 0
    total_factory_income: float = 0.0
    total_factory_employment: int = 0

    # RGO data
    total_rgo_income: float = 0.0
    total_rgo_employment: int = 0


@dataclass
class SaveData:
    """All economic data from a save file."""
    date: str = ""
    world_market: WorldMarketData = field(default_factory=WorldMarketData)
    countries: dict[str, CountryData] = field(default_factory=dict)
    global_pop_data: PopData = field(default_factory=PopData)


def extract_world_market(data: dict) -> WorldMarketData:
    """Extract world market data."""
    result = WorldMarketData()

    wm = data.get('worldmarket', {})
    if isinstance(wm, dict):
        # Prices
        prices = wm.get('price_pool', {})
        if isinstance(prices, dict):
            result.prices = {k: float(v) for k, v in prices.items() if isinstance(v, (int, float))}

        # Supply
        supply = wm.get('supply_pool', {})
        if isinstance(supply, dict):
            result.supply = {k: float(v) for k, v in supply.items() if isinstance(v, (int, float))}

        # Actual sold
        sold = wm.get('actual_sold', {})
        if isinstance(sold, dict):
            result.actual_sold = {k: float(v) for k, v in sold.items() if isinstance(v, (int, float))}

    return result


def extract_pop_from_block(pop_type: str, pop_block: dict) -> dict:
    """Extract data from a single POP block."""
    if not isinstance(pop_block, dict):
        return None

    return {
        'type': pop_type,
        'size': pop_block.get('size', 0),
        'money': pop_block.get('money', 0.0),
        'bank': pop_block.get('bank', 0.0),
        'life_needs': pop_block.get('life_needs', 0.0),
        'everyday_needs': pop_block.get('everyday_needs', 0.0),
        'luxury_needs': pop_block.get('luxury_needs', 0.0),
        'literacy': pop_block.get('literacy', 0.0),
        'con': pop_block.get('con', 0.0),
        'mil': pop_block.get('mil', 0.0),
    }


def extract_factory_data(building_block: dict) -> FactoryData:
    """Extract factory data from a state_buildings block."""
    factory = FactoryData()

    factory.name = building_block.get('building', '')
    factory.level = building_block.get('level', 0)
    factory.money = building_block.get('money', 0.0)
    factory.last_income = building_block.get('last_income', 0.0)
    factory.last_spending = building_block.get('last_spending', 0.0)
    factory.wages_paid = building_block.get('pops_paychecks', 0.0)
    factory.unprofitable_days = building_block.get('unprofitable_days', 0)
    factory.subsidised = building_block.get('subsidised', False)
    factory.produces = building_block.get('produces', 0.0)

    # Extract employment
    employment = building_block.get('employment', {})
    if isinstance(employment, dict):
        employees = employment.get('employees', [])
        if isinstance(employees, list):
            for emp in employees:
                if isinstance(emp, dict):
                    pop_id = emp.get('province_pop_id', {})
                    if isinstance(pop_id, dict):
                        pop_type_id = pop_id.get('type', -1)
                        count = emp.get('count', 0)
                        if pop_type_id in (5, 6):  # clerks
                            factory.employed_clerks += count
                        elif pop_type_id == 7:  # craftsmen
                            factory.employed_craftsmen += count

    return factory


def extract_rgo_data(rgo_block: dict) -> RGOData:
    """Extract RGO data from a province's rgo block."""
    rgo = RGOData()

    rgo.goods_type = rgo_block.get('goods_type', '')
    rgo.last_income = rgo_block.get('last_income', 0.0)

    # Extract employment
    employment = rgo_block.get('employment', {})
    if isinstance(employment, dict):
        employees = employment.get('employees', [])
        if isinstance(employees, list):
            for emp in employees:
                if isinstance(emp, dict):
                    count = emp.get('count', 0)
                    rgo.total_employed += count

    return rgo


def extract_state_data(state_block: dict) -> StateData:
    """Extract state data including factories."""
    state = StateData()

    provinces = state_block.get('provinces', [])
    if isinstance(provinces, list):
        state.provinces = [p for p in provinces if isinstance(p, int)]

    state.is_colonial = state_block.get('is_colonial', 0)
    state.savings = state_block.get('savings', 0.0)

    # Extract factories
    buildings = state_block.get('state_buildings', [])
    if isinstance(buildings, dict):
        buildings = [buildings]
    elif not isinstance(buildings, list):
        buildings = []

    for building in buildings:
        if isinstance(building, dict) and 'building' in building:
            factory = extract_factory_data(building)
            state.factories.append(factory)
            state.total_factory_employment += factory.employed_craftsmen + factory.employed_clerks
            state.total_factory_income += factory.last_income

    return state


def extract_country_data(tag: str, country_block: dict, provinces: dict[int, dict]) -> CountryData:
    """Extract all economic data for a country."""
    country = CountryData()
    country.tag = tag

    # Basic data
    country.treasury = country_block.get('money', 0.0)
    country.prestige = country_block.get('prestige', 0.0)
    country.infamy = country_block.get('badboy', 0.0)
    country.tax_base = country_block.get('tax_base', 0.0)
    country.civilized = country_block.get('civilized', True)

    # Bank data
    bank = country_block.get('bank', {})
    if isinstance(bank, dict):
        country.bank_reserves = bank.get('money', 0.0)
        country.bank_money_lent = bank.get('money_lent', 0.0)

    # Tax data
    rich_tax = country_block.get('rich_tax', {})
    if isinstance(rich_tax, dict):
        country.rich_tax_rate = rich_tax.get('current', 0.0)
        country.rich_tax_income = rich_tax.get('total', 0.0)

    middle_tax = country_block.get('middle_tax', {})
    if isinstance(middle_tax, dict):
        country.middle_tax_rate = middle_tax.get('current', 0.0)
        country.middle_tax_income = middle_tax.get('total', 0.0)

    poor_tax = country_block.get('poor_tax', {})
    if isinstance(poor_tax, dict):
        country.poor_tax_rate = poor_tax.get('current', 0.0)
        country.poor_tax_income = poor_tax.get('total', 0.0)

    # Spending
    edu = country_block.get('education_spending', {})
    if isinstance(edu, dict):
        country.education_spending = edu.get('settings', 0.0)

    mil = country_block.get('military_spending', {})
    if isinstance(mil, dict):
        country.military_spending = mil.get('settings', 0.0)

    social = country_block.get('social_spending', {})
    if isinstance(social, dict):
        country.social_spending = social.get('settings', 0.0)

    # States and factories
    states = country_block.get('state', [])
    if isinstance(states, dict):
        states = [states]
    elif not isinstance(states, list):
        states = []

    for state_block in states:
        if isinstance(state_block, dict):
            state = extract_state_data(state_block)
            country.states.append(state)
            country.total_factory_employment += state.total_factory_employment
            country.total_factory_income += state.total_factory_income
            for factory in state.factories:
                country.total_factory_count += 1
                country.total_factory_levels += factory.level

    # Process owned provinces for POPs and RGOs
    owned_provinces = []
    for prov_id, prov_data in provinces.items():
        if isinstance(prov_data, dict) and prov_data.get('owner') == tag:
            owned_provinces.append((prov_id, prov_data))

    # Extract POP data from provinces
    pop_data = PopData()
    total_weighted_needs = {'life': 0.0, 'everyday': 0.0, 'luxury': 0.0}
    total_weighted_literacy = 0.0
    total_weighted_con = 0.0
    total_weighted_mil = 0.0

    for prov_id, prov_data in owned_provinces:
        # RGO data
        rgo_block = prov_data.get('rgo', {})
        if isinstance(rgo_block, dict):
            rgo = extract_rgo_data(rgo_block)
            country.total_rgo_income += rgo.last_income
            country.total_rgo_employment += rgo.total_employed

        # POP data
        for pop_type in POP_TYPES.keys():
            pops = prov_data.get(pop_type, [])
            if isinstance(pops, dict):
                pops = [pops]
            elif not isinstance(pops, list):
                continue

            for pop_block in pops:
                pop = extract_pop_from_block(pop_type, pop_block)
                if pop:
                    size = pop['size']
                    pop_data.total_population += size
                    pop_data.population_by_type[pop_type] = pop_data.population_by_type.get(pop_type, 0) + size
                    pop_data.total_money += pop['money']
                    pop_data.total_bank_savings += pop['bank']
                    pop_data.money_by_type[pop_type] = pop_data.money_by_type.get(pop_type, 0.0) + pop['money']

                    # Weighted averages
                    total_weighted_needs['life'] += pop['life_needs'] * size
                    total_weighted_needs['everyday'] += pop['everyday_needs'] * size
                    total_weighted_needs['luxury'] += pop['luxury_needs'] * size
                    total_weighted_literacy += pop['literacy'] * size
                    total_weighted_con += pop['con'] * size
                    total_weighted_mil += pop['mil'] * size

    # Calculate averages
    if pop_data.total_population > 0:
        pop_data.avg_life_needs = total_weighted_needs['life'] / pop_data.total_population
        pop_data.avg_everyday_needs = total_weighted_needs['everyday'] / pop_data.total_population
        pop_data.avg_luxury_needs = total_weighted_needs['luxury'] / pop_data.total_population
        pop_data.avg_literacy = total_weighted_literacy / pop_data.total_population
        pop_data.avg_consciousness = total_weighted_con / pop_data.total_population
        pop_data.avg_militancy = total_weighted_mil / pop_data.total_population

    # Calculate employment from factory data
    pop_data.employed_craftsmen = country.total_factory_employment  # Approximation
    pop_data.employed_labourers = country.total_rgo_employment  # RGO employment

    country.pop_data = pop_data
    return country


def aggregate_global_pop_data(countries: dict[str, CountryData]) -> PopData:
    """Aggregate POP data across all countries."""
    global_pop = PopData()

    for country in countries.values():
        pd = country.pop_data
        global_pop.total_population += pd.total_population
        global_pop.total_money += pd.total_money
        global_pop.total_bank_savings += pd.total_bank_savings

        for pop_type, count in pd.population_by_type.items():
            global_pop.population_by_type[pop_type] = global_pop.population_by_type.get(pop_type, 0) + count

        for pop_type, money in pd.money_by_type.items():
            global_pop.money_by_type[pop_type] = global_pop.money_by_type.get(pop_type, 0.0) + money

        global_pop.employed_craftsmen += pd.employed_craftsmen
        global_pop.employed_clerks += pd.employed_clerks
        global_pop.employed_labourers += pd.employed_labourers
        global_pop.employed_farmers += pd.employed_farmers

    # Weighted averages need population weights from each country
    total_pop = global_pop.total_population
    if total_pop > 0:
        weighted_life = sum(c.pop_data.avg_life_needs * c.pop_data.total_population for c in countries.values())
        weighted_everyday = sum(c.pop_data.avg_everyday_needs * c.pop_data.total_population for c in countries.values())
        weighted_luxury = sum(c.pop_data.avg_luxury_needs * c.pop_data.total_population for c in countries.values())
        weighted_literacy = sum(c.pop_data.avg_literacy * c.pop_data.total_population for c in countries.values())
        weighted_con = sum(c.pop_data.avg_consciousness * c.pop_data.total_population for c in countries.values())
        weighted_mil = sum(c.pop_data.avg_militancy * c.pop_data.total_population for c in countries.values())

        global_pop.avg_life_needs = weighted_life / total_pop
        global_pop.avg_everyday_needs = weighted_everyday / total_pop
        global_pop.avg_luxury_needs = weighted_luxury / total_pop
        global_pop.avg_literacy = weighted_literacy / total_pop
        global_pop.avg_consciousness = weighted_con / total_pop
        global_pop.avg_militancy = weighted_mil / total_pop

    return global_pop
