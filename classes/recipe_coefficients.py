from mech.actuator import pump, valve, pressure
from lib.utils import *
import numpy as np
from datetime import datetime, timedelta

class MassSegment:

    """
    Mass Segment class defines parameters for individual stage of recipe
     and builds runtime coefficients for pump rate 
    """

    def __init__(self, recipe, stage, feed_type,
                 start_parameters, stop_parameters):

        # Exhaustive recipe parameters
        self.recipe = recipe
        
        # fill in basic parameters
        self.feed_type = feed_type
        self.stage = stage
        self.start_parameters = start_parameters
        self.stop_parameters = stop_parameters
        self.stop_type = stop_parameters['stop_type']
        self.stop_value = None # define w/ correct units in coefficients
        
        # link stages
        self.last = None
        self.next = None
        
        # runtime vars fill out while recipe runs
        self.t0_recipe = None # time at start of stage
        self.m0_recipe = None # scale reading at start of stage
        self.r0_recipe = None # pump rate at start of stage (units g/s)

        self.t0_stage = None # time at start of stage
        self.m0_stage = None # scale reading at start of stage
        self.r0_stage = None # pump rate at start of stage (units g/s)

        # Instantiate linear recipe parameters
        self.inc_rate = 0 # increase rate
        self.is_lowerbound = False # in cases where rate < 0

        # coefficients fill out from calculate methods
        self.coefficients = None


    def calculate_bolus(self, initial_conditions):

        # retrieve last stage's end parameters
        ms_last = self.last
        
        # Set stage start parameters
        self.t0_stage=initial_conditions['time']
        self.r0_stage=initial_conditions['rate']
        self.m0_stage=initial_conditions['mass']

        if ms_last is None:
            # Set recipe initial parameters if first stage
            self.m0_recipe = self.m0_stage
            self.t0_recipe = self.t0_stage
            self.r0_stage = convert_rate(DEFAULT_PUMP_RATE, # rate=0 if first stage
                                         units_num=['s','m'])
            self.r0_recipe = self.r0_stage

        # calculate absolute mass from net mass (grams)
        net_mass = self.stop_parameters['stop_value']
        target_mass = self.m0_stage - net_mass
        self.stop_value = target_mass        
        self.is_lowerbound = True # subtractive scale

        # y = mx + b, where m = pump rate increase, b = start rate
        #  time in relative seconds from start of segment
        #  
        self.coefficients = np.array([0, self.r0_stage])

        # Calculate nominal mass/s and mL/s rates for quality control
        # ...

        return self.coefficients


    def calculate_timed(self, initial_conditions):

        # retrieve last stage's end parameters
        ms_last = self.last

        # Convert rate to g/s
        rate_mL_min= self.start_parameters['rate']
        start_rate = convert_rate(rate_mL_min,
                                  ['v','m'],
                                  ['min', 'sec']) 

        # Set stage start parameters
        self.t0_stage = initial_conditions['time']
        self.r0_stage = start_rate
        self.m0_stage = initial_conditions['mass']

        if ms_last is None:
            
            # Set recipe initial parameters if first stage
            self.t0_recipe = self.t0_stage
            self.r0_recipe = self.r0_stage
            self.m0_recipe = self.m0_stage

        # calculate stop parameters based on initial conditions
        duration_min = self.stop_parameters['stop_value']
        self.stop_value = self.t0_stage + timedelta(minutes=duration_min)
 
        # y = mx + b, where m = pump rate increase, b = start rate
        #  time in relative seconds from start of segment
        #  
        self.coefficients = np.array([0, self.r0_stage])

        # Calculate nominal mass/s and mL/s rates for quality control
        # ...

        return self.coefficients


    def calculate_linear(self, initial_conditions=None):

        ms_last = self.last

        # Set stage start parameters
        self.t0_stage = initial_conditions['time']
        self.r0_stage = initial_conditions['rate']
        self.m0_stage = initial_conditions['mass']

        if ms_last is None:
            # Set recipe initial parameters if first stage
            self.t0_recipe = self.t0_stage
            self.r0_stage = convert_rate(DEFAULT_PUMP_RATE, # rate=0 if first stage
                                         units_num=['s','m'])
            self.r0_recipe = self.r0_stage
            self.m0_recipe = self.m0_stage

        # convert acceleration term into g/s^2
        inc_rate_mL_min2 = self.start_parameters['inc_rate']
        self.inc_rate = convert_rate(inc_rate_mL_min2,
                                       ['v', 'm'],
                                       ['min^2', 'sec^2'])
        # convert stop parameter to g/s
        end_rate_mL_min = self.stop_parameters['stop_value']
        self.stop_value = convert_rate(end_rate_mL_min,
                                        ['v','m'],
                                        ['min', 'sec'])

        # y = mx + b, where m = pump rate increase, b = start rate
        #  time in relative seconds from start of segment
        #  
        self.coefficients = np.array([self.inc_rate, self.r0_stage])

        # determine if stop value is lower boundary
        if self.coefficients[0] < 0:
            self.is_lowerbound = True
        elif self.coefficients[0] > 0:
            self.is_lowerbound = False
        else:
            pass

        # Calculate nominal mass/s and mL/s rates for quality control
        # ...

        return self.coefficients
