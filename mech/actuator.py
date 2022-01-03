import time
import numpy as np
from lib.utils import *

"""
Contains actuator functions controlling actual mechanical devices.
Note that these functions are all fictitious, since I can't interface
with system that I can't access.

I took liberties with available actuators to make system more realistic,
adding in pressure reading for safety and control valve (e.g. 8-port)
connecting feed stock resivor and pump with vessle,
which would be needed for priming, pump calibration, and safety autoshutoff.
"""

# fake system
MOCK_ACTUATOR = {'VALVE': 0,
                 'SCALE': 250,
                 'PUMP': 0,
                 'PRESSURE': 1,
                 'TUNE': [1,0,0]}

def pressure():

    """
    pressure - reads current pressure of reaction vessle.
      :return: float returns current pressure of vessle (in atm)
    """

    # add 0.01 atm for every read
    MOCK_ACTUATOR['PRESSURE'] += 0.01
    pressure_reading = MOCK_ACTUATOR['PRESSURE']
    
    return pressure_reading


def pump(rate=None):

    """
    :param rate: var - float: desired pump rate in steps/second
                       chr: 'f' increases pump rate by 5%
                       chr: 's' decreases pump rate by 5%
                       list: list of rate, preset steps
                            e.g. [5, 10] is 5 steps/seconds for 10 steps
                       int - number of steps to complete before stopping
    :return: returns current pump rate (steps/s) if rate=None
             if rate is not None, returns True for success False for error
            

    """

    pump_return = False
    current_rate = MOCK_ACTUATOR['PUMP']

    if rate is not None:
        # moves pump faster
        if rate=='f':

            # Check if too fast
            if abs(current_rate * 1.05) <= MAX_PUMP_RATE:
                MOCK_ACTUATOR['PUMP'] = current_rate * 1.05
                pump_return = True
            else:
               # set to max rate if too fast; return error
               MOCK_ACTUATOR['PUMP'] = MAX_PUMP_RATE
               print('whirrr!') # highly realistic fast pump noise

        # moves pump slower
        if rate=='s':

            # Check if too slow
            if abs(current_rate * 0.95) > MIN_PUMP_RATE:
                MOCK_ACTUATOR['PUMP'] = current_rate * 0.95
                pump_return = True
            else:
                # set to zero if too slow; return error
                MOCK_ACTUATOR['PUMP'] = 0
                print('record scratch noise') # sound of pump grinding to halt

        # moves pump at given rate
        if isinstance(rate, float) or isinstance(rate, int):

            if abs(rate) <= MAX_PUMP_RATE and \
               abs(rate) >= MIN_PUMP_RATE:

                MOCK_ACTUATOR['PUMP'] = rate
                pump_return = True

        # moves pump at given rate for given period of time
        if isinstance(rate, list) and \
           isinstance(rate[0], float) and isinstance(rate[1], int):

            # clean up rates
            if abs(rate[0]) <= MAX_PUMP_RATE and \
               abs(rate[0]) >= MIN_PUMP_RATE:

                # calculate duration of steps
                duration = rate[1] / rate[0]

                MOCK_ACTUATOR['PUMP'] = rate[0]
                
                # Achieve specified steps by
                #  causing program to freeze for duration specified
                duration = round(duration)
                print('Zzz...')
                time.sleep(duration)

                pump_return = True

    else:
        # read current pump rate
        pump_return = MOCK_ACTUATOR['PUMP']

    return pump_return


def scale(tare=False):

    """
    :param tare: bool - if True tares the scale back to zero
    :return: returns current scale reading (in grams) if tare is False
             if tare = True returns True for success False for error
             if tare = False returns current pump rate (steps/s) if rate=None

    """

    scale_return=0
   
    #zero scale
    if tare:
        MOCK_ACTUATOR['SCALE'] = 0
        scale_return = True
    elif tare is False:
        #read scale; decrement by nominal mass each read
         MOCK_ACTUATOR['SCALE'] -= abs(MOCK_ACTUATOR['PUMP'] * NOMINAL_MASS_PER_STEP)
         scale_return = MOCK_ACTUATOR['SCALE']
         
    else:
        # scale malfuncion onomatopoeia 
        print('bzzzt!')

    if scale_return < -1:
        raise Exception('out of feed')

    return scale_return


def valve(position=None):

    """
    valve - sets position of valve and states current position of valve
            valve connects feed resivoir and pump to reactor vessle. 
    :param: position int - 1 = open/online with feed vessle
                           0 = closed - feed goes straight to waste vessle
                           None = states which position valve is in

    :return: returns int 1 or 0 corresponding to position of valve
             returns None if error
    """

    # Read valve position
    if position is None:
        valve_position = MOCK_ACTUATOR['VALVE']

    # open valve
    elif position==1:

        # fake valve read
        MOCK_ACTUATOR['VALVE'] = position

        #return new position
        valve_position = MOCK_ACTUATOR['VALVE']

        # for versimilitude
        print('boop beep') 
        
    #close valve
    elif position==0:
        MOCK_ACTUATOR['VALVE'] = position
        print('beep bloop') # highly realistic pump simulation
        valve_position = MOCK_ACTUATOR['VALVE']

    # invalid input
    else:
        print('confused bloop beep') # confused pump noises
        valve_position = None
    
    return valve_position


def tune():

    """
    Tune control loop - tunes PID coefficients manually
      or algorithmically (e.g. using Ziegler-Nichols method 
   
    :return: list - PID coefficients K=[k_p, k_i, k_d]

      """

    # since this system is fictitious, just make up numbers
    very_sophisticated_tuning_algorithm_results = MOCK_ACTUATOR['TUNE']
    K = np.array(very_sophisticated_tuning_algorithm_results)

    return K

