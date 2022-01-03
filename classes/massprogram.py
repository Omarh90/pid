



from classes.recipe_coefficients import MassSegment
from classes.pid import PID
from mech.equipment import *
from mech.actuator import pump, valve, pressure


class MassProgram:

    """
    Defines recipe object in terms of mass transfer rate of individuals stages
    """
     
    def __init__(self, recipe):

        # Instantiate recipe
        self.recipe = dict()
        # dict = {1:{feed_type: linear
        #            start_parameters:{inc_rate:1}
        #            stop_parameters:{stop_type:rate
        #                             stop_value:5}

        # list of mass_segment composing recipe
        self.massprogram = list()
        #[ms_1, ms_2]
        self.ms = None #current mass segment

        # Current recipe stage parameters
        self.feed_type = None #(e.g. bolus, linear, timed)
        self.stop_type = None #(e.g. mass, rate, time)
        self.stop_value = None #(e.g. 5g,  1g/s, 5min)
        self.coeff = None      # pump rate equation coefficients for current step
        self.is_lowerbound = None # indicates if stop_value is lower boundary

        # Initial parameters of recipe
        self.current_stage = 0
        self.t0_recipe = None # initial time
        self.m0_recipe = None # initial mass
        self.r0_recipe = None # initial pump rate
        ms_last = None # loop var

        # number of stages
        self.len_stages = len(recipe)
        
        # Populate recipe with newly-generated recipe stage
        for stage, segment in recipe.items():
            
            ms_i = MassSegment(recipe,
                               stage,
                               segment['feed_type'],
                               segment['start_parameters'],
                               segment['stop_parameters']
                               ) #todo: stop parameter units

            # Link latest recipe stages with first/last attributes
            if ms_last:
                
                ms_i.last = ms_last #self.massprogram[-1]
                ms_last = ms_i.last
                ms_last.next = ms_i
 
            # Add recipe stage to recipe
            self.massprogram.append(ms_i)

            # store last ms_i for next loop
            ms_last = ms_i


    def __next__(self):

        if self.current_stage < len(self.massprogram):
            self.ms = self.massprogram[self.current_stage]
        else:
            raise StopIteration

        # Increment stage var
        self.current_stage += 1

        # Update MassProgram Class global variables with current stage vars
        self.feed_type = self.ms.feed_type
        self.stop_type = self.ms.stop_type

        # get stage start conditions
        current_data = current_readings(rate_units=['m','sec'])

        # Calculate run parameters based on current system run conditions
        if self.ms.feed_type=='bolus':
            coeff = self.ms.calculate_bolus(current_data)
            self.stop_type = 'mass'
        elif self.ms.feed_type=='timed':
            coeff = self.ms.calculate_timed(current_data)
            self.stop_type = 'time'
        elif self.ms.feed_type=='linear':
            coeff = self.ms.calculate_linear(current_data)
            self.stop_type = 'rate'

        # update current stage coefficients
        self.coeff = coeff
        self.stop_value = self.ms.stop_value
        self.is_lowerbound = self.ms.is_lowerbound

    def __iter__(self):

        return self

    def pump(self, rate, input_units=['m', 'sec'], add_to_rate=False, pid=[False,False,False]):

        """
        pump - layer between pump() and recipe to prevent equipment problems
          takes pump rate specified, and compares it to recipe and pump eng limits
          and pid error constant, then readjusts pump rate accordingly.
        :param rate:
        param input_units: list - pump rate units - first entry is numerator, 2nd is denominator
                'm' = mass (g), 's' = steps, 'v'=volume, 'sec'=seconds, 'min'=minute
        """

        #Insantiate PID object
        _pid=PID()


        # convert stop_rate to same units
        if self.stop_type=='rate':
            stop_value_st = convert_rate(rate=self.stop_value, #g/s => steps/s
                                         units_num=['m', 's'])
        else:
            stop_value_st = None

        # if control correction factor specified
        if np.any(pid):

            # multiply rate increase by proportionality pid constant
            #  to preemptively offset error in rate adjustment
            rate*= _pid.K[pid] # Not sure if this is valid use of k_p coefficient
            rate=sum(rate)

        # add calculated pump rate increase to current emperical rate
        if add_to_rate:
            rate+=add_to_rate

        # standardize pump rate units to steps/sec
        rate_st = convert_rate(rate, #input[0]/input[1] =>steps/s
                               [input_units[0], 's'],
                               [input_units[1], 'sec'])

        # Adjust rate value according to engineering and recipe controls
        adj_rate_st = attenuate_pump_rate(rate_st,
                                          stop_value_st,
                                          self.is_lowerbound)

        # Unpack pump rate attenuation return value
        adj_rate_st,  pump_limit_exceeded = adj_rate_st # Cleaned up pump rate

        # convert new rate to steps/min
        adj_rate_st_min = convert_rate(rate=adj_rate_st,
                                       units_num = ['s', 's'],
                                       units_den=['sec', 'min'])

        # update pump rate according to (corrected) mass program
        pump_return=pump(adj_rate_st_min)

        return pump_limit_exceeded

        
    def get_stage(self, n):
    
        ms = self.massprogram[n-1]
        
        return ms


    def set_stage(self, ms, n=None):    

        # If adding new stage
        if n is None or n==self.len_stages+1:

            # If n not set, append new massprogram to end of recipe list
            self.massprogram.append(ms)
            self.recipe[n] = ms.recipe
            self.len_stages += 1

            # link to last mass_segments with next/last attributes
            if n >= 2:
                ms.last = self.massprogram[n-2]
                ms_last = ms.last
                ms_last.next = ms

        # If replacing current stage
        elif self.len_stages <= n:
            self.massprogram[n-1] = ms
            self.recipe[n] = ms.recipe
            self.len_stages += 1

            # link next mass_segments with next/last attributes
            if n < self.len_stages:
                ms.next = self.massprogram[n]
                ms_next = ms.next
                ms_next.last = ms

            # link prev mass_segments with next/last attributes
            if n >= 2:
                ms.last = self.massprogram[n-2]
                ms_last = ms.last
                ms_last.next = ms


