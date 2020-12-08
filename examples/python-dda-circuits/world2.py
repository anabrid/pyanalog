#!/usr/bin/env python3

from dda import dda
from dda.sympy import from_sympy
import sympy
from collections import namedtuple

# Based on https://github.com/zykls/whynot/blob/master/whynot/simulators/world2/

birth_rate = 0.04
death_rate = 0.028
effective_capital_investment_ratio = 1.0
natural_resources_usage = 1.0
land_area = 135e6
population_density = 26.5
food_coefficient = 1.0
food_normal = 1.0
capital_investment_agriculture = 0.3
capital_investment_generation = 0.05
capital_investment_discard = 0.025
pollution_standard = 3.6e9
pollution = 1.0
intervention_time = 1970
capital_investment_in_agriculture_frac_adj_time = 15.0
quality_of_life_standard = 1.0

#: Time to initialize the simulation (in years).
start_time = 1900
#: Time to end the simulation (in years).
end_time = 2100
#: Time (in years) elapsed on each update of the discrete dynamics.
delta_t = 0.2

## These are the tabulated functions

class Tabulated():
    instance_counter = 0
    def __init__(self,x,y):
        self.x, self.y = x,y
        Tabulated.instance_counter += 1 # because we don't know the actual name
        self.symb = sympy.Function("Table%d" % Tabulated.instance_counter)
        self.symb.table = self # back-reference from sympy context
    def __call__(self, x):
        # Calling within symbolic sympy context yields in a delayed
        # execution which allows us 
        return self.symb(x)
    
BIRTH_RATE_FROM_MATERIAL = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [1.2, 1.0, 0.85, 0.75, 0.7, 0.7])
BIRTH_RATE_FROM_CROWDING = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [1.05, 1.0, 0.9, 0.7, 0.6, 0.55])
BIRTH_RATE_FROM_FOOD = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0], [0.0, 1.0, 1.6, 1.9, 2.0])
BIRTH_RATE_FROM_POLLUTION = Tabulated([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0], [1.02, 0.9, 0.7, 0.4, 0.25, 0.15, 0.1])
DEATH_RATE_FROM_MATERIAL = Tabulated([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0], [3.0, 1.8, 1.0, 0.8, 0.7, 0.6, 0.53, 0.5, 0.5, 0.5, 0.5])
DEATH_RATE_FROM_POLLUTION = Tabulated([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0], [0.92, 1.3, 2.0, 3.2, 4.8, 6.8,9.2])
DEATH_RATE_FROM_FOOD = Tabulated([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0], [30.0, 3.0, 2.0, 1.4, 1.0, 0.7, 0.6, 0.5, 0.5],)
DEATH_RATE_FROM_CROWDING = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [0.9, 1.0, 1.2, 1.5, 1.9, 3.0])
FOOD_FROM_CROWDING = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [2.4, 1.0, 0.6, 0.4, 0.3, 0.2])
FOOD_POTENTIAL_FROM_CAPITAL_INVESTMENT = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0], [0.5, 1.0, 1.4, 1.7, 1.9, 2.05, 2.2])
CAPITAL_INVESTMENT_MULTIPLIER_TABLE = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [0.1, 1.0, 1.8, 2.4, 2.8, 3.0])
FOOD_FROM_POLLUTION = Tabulated([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0], [1.02, 0.9, 0.65, 0.35, 0.2, 0.1, 0.05])
POLLUTION_FROM_CAPITAL = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [0.05, 1.0, 3.5, 5.4, 7.4, 8.0])
POLLUTION_ABSORPTION_TIME_TABLE = Tabulated([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0], [0.6, 2.5, 5.0, 8.0, 11.5, 15.5, 20.0])
CAPITAL_FRACTION_INDICATE_BY_FOOD_RATIO_TABLE = Tabulated([0.0, 0.5, 1.0, 1.5, 2.0], [1.0, 0.6, 0.3, 0.15, 0.1])
QUALITY_OF_LIFE_FROM_MATERIAL = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], [0.2, 1.0, 1.7, 2.3, 2.7, 2.9])
QUALITY_OF_LIFE_FROM_CROWDING = Tabulated([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],[2.0, 1.3, 1.0, 0.75, 0.55, 0.45, 0.38, 0.3, 0.25, 0.22, 0.2])
QUALITY_OF_LIFE_FROM_FOOD = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0], [0.0, 1.0, 1.8, 2.4, 2.7])
QUALITY_OF_LIFE_FROM_POLLUTION = Tabulated([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0], [1.04, 0.85, 0.6, 0.3, 0.15, 0.05, 0.02])
NATURAL_RESOURCE_EXTRACTION = Tabulated([0.0, 0.25, 0.5, 0.75, 1.0], [0.0, 0.15, 0.5, 0.85, 1.0])
NATURAL_RESOURCES_FROM_MATERIAL = Tabulated([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],[0.0, 1.0, 1.8, 2.4, 2.9, 3.3, 3.6, 3.8, 3.9, 3.95, 4.0])
CAPITAL_INVESTMENT_FROM_QUALITY = Tabulated([0.0, 0.5, 1.0, 1.5, 2.0], [0.7, 0.8, 1.0, 1.5, 2.0])


### These are the state variables initial values

ic_population = 1.65e9
#: Stock of natural resources
ic_natural_resources = 3.6e9 * 250
#: Total capital investment stock
ic_capital_investment = 0.4e9
#: Pollution stock
ic_pollution = 0.2e9
#: Fraction of capital investment in agriculture
ic_capital_investment_in_agriculture = 0.2

#: Initial natural resources
# Since this does not change over time, we don't treat it as
# an eveolution quantity but as a constant.
initial_natural_resources = 3.6e9 * 250


### These are the five actual state variables as sympy variables

state_variables = sympy.symbols("s:5")

# unpack:
(
    population,
    natural_resources,
    capital_investment,
    pollution,
    capital_investment_in_agriculture,
) = state_variables

### These are intermediate variables required for computation of the new state.
### They are sympy expressions.

capital_investment_ratio = capital_investment / population
crowding_ratio = population / (land_area * population_density)
pollution_ratio = pollution / pollution_standard

capital_investment_ratio_in_agriculture = (
    capital_investment_ratio
    * capital_investment_in_agriculture
    / capital_investment_agriculture
)

capital_investment_food_potential = FOOD_POTENTIAL_FROM_CAPITAL_INVESTMENT(
    capital_investment_ratio_in_agriculture)

food_ratio = (
    capital_investment_food_potential
    * FOOD_FROM_CROWDING(crowding_ratio)  # crowding multiplier
    * FOOD_FROM_POLLUTION(pollution_ratio)  # pollution multiplier
    * food_coefficient
    / food_normal
)

standard_of_living = (
    (
        capital_investment_ratio
        * NATURAL_RESOURCE_EXTRACTION(
            natural_resources
            / initial_natural_resources  # fraction of natural resources remaining
        )  # natural resources extraction multiplier
        * (1.0 - capital_investment_in_agriculture)
        / (1.0 - capital_investment_agriculture)
    )  # effective capital investment ratio
    / effective_capital_investment_ratio
)

death_rate_per_year = (
    death_rate
    * DEATH_RATE_FROM_MATERIAL(standard_of_living)  # material multiplier
    * DEATH_RATE_FROM_POLLUTION(pollution_ratio)  # pollution multiplier
    * DEATH_RATE_FROM_FOOD(food_ratio)  # food multiplier
    * DEATH_RATE_FROM_CROWDING(crowding_ratio)  # crowding multiplier
)

birth_rate_per_year = (
    birth_rate
    * BIRTH_RATE_FROM_MATERIAL(standard_of_living)  # material multiplier
    * BIRTH_RATE_FROM_POLLUTION(pollution_ratio)  # pollution multiplier
    * BIRTH_RATE_FROM_FOOD(food_ratio)  # food multiplier
    * BIRTH_RATE_FROM_CROWDING(crowding_ratio)  # crowding multiplier
)

natural_resources_usage_rate = (
    population
    * natural_resources_usage
    * NATURAL_RESOURCES_FROM_MATERIAL(
        standard_of_living
    )  # material multiplier
)
capital_investment_rate = (
    population
    * CAPITAL_INVESTMENT_MULTIPLIER_TABLE(standard_of_living)  # material multiplier
    * capital_investment_generation
) - capital_investment * capital_investment_discard

pollution_generation = (
    population
    * POLLUTION_FROM_CAPITAL(capital_investment_ratio)  # capital multiplier
    * pollution
)

pollution_absorption = (
    pollution
    / POLLUTION_ABSORPTION_TIME_TABLE(pollution_ratio)  # absorption time
)

pollution_rate = pollution_generation - pollution_absorption


### These are the dynamics

# Population
delta_population = (birth_rate_per_year - death_rate_per_year) * population

# Natural resources (negative since this is usage)
delta_natural_resources = -natural_resources_usage_rate

# Capital_investment
delta_capital_investment = capital_investment_rate

# Pollution
delta_pollution = pollution_rate

# Investment in agriculture
delta_capital_investment_in_agriculture = (
    CAPITAL_FRACTION_INDICATE_BY_FOOD_RATIO_TABLE(food_ratio)
    * CAPITAL_INVESTMENT_FROM_QUALITY(
        (
            QUALITY_OF_LIFE_FROM_MATERIAL(standard_of_living)
            / QUALITY_OF_LIFE_FROM_FOOD(food_ratio)
        )  # life quality ratio
    )  # capital investment from quality ratio
    - capital_investment_in_agriculture
) / capital_investment_in_agriculture_frac_adj_time
        
### Actual evolution

population = dda.int(delta_population, delta_t, ic_pollution)
natural_resources = dda.int(delta_natural_resources, delta_t, ic_natural_resources)
capital_investment = dda.int(delta_capital_investment, delta_t, ic_capital_investment)
pollution = dda.int(delta_pollution, delta_t, ic_pollution)
capital_investment_in_agriculture = dda.int(delta_capital_investment_in_agriculture,
                                            delta_t, ic_capital_investment_in_agriculture)


### This is a derived quantity of interest from the solution:
### The quality of life measure

qol = (
        quality_of_life_standard
        * QUALITY_OF_LIFE_FROM_MATERIAL(
            standard_of_living
        )  # material multiplier
        * QUALITY_OF_LIFE_FROM_CROWDING(crowding_ratio)  # crowding multiplier
        * QUALITY_OF_LIFE_FROM_FOOD(food_ratio)  # food multiplier
        * QUALITY_OF_LIFE_FROM_POLLUTION(pollution_ratio)  # pollution multiplier
    )
