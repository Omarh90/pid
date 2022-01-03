from mech.actuator import *
from lib.utils import *
from datetime import datetime


"""
Defines functions to control, calibrate, and monitor actuators.
One layer up from direct actuator functions

"""

def current_readings(sensor=None, rate_units=['s', 'sec']):    

    """
    current_readings -  provides current state of system.
      scale mass (g), pump rate (steps/s), time (__), pressure (atm)

    :param sensor: specifies which sensor to read
         must be one of ['mass', 'rate', 'time', 'pressure', 'valve']
         if None, returns all readings as dict
    :return: dict of readings if sensor=None,
             else returns float
    """

    current_data = dict()
    
    sensors = {'mass': scale,
               'rate': lambda: pump()/60, #(60 for min->s)
               'time': datetime.now,
               'pressure': pressure,
               'valve': valve}
    
    for s, actuator in sensors.items():
        current_data[s] = actuator()

    if sensor:
        # provide measured value single sensor specfied
        if sensor in sensors.keys():
             current_data = sensors[sensor]()
        else:
            # invalid sensor specified; raise error/report in log
            current_data = None

    # if steps/second not desired pump rate units, convert accordingly:
    if (rate_units != ['s', 'sec'] and sensor is None) \
        or (rate_units != ['s', 'sec'] and sensor == 'rate'):

        # unpack pump rate
        if sensor:
            rate_0 = current_data
        else:
            rate_0 = current_data['rate']

        # convert pump rate from steps/sec
        rate = convert_rate(rate_0, ['s', rate_units[0]], ['sec',rate_units[1]])
        
        # repack pump rate
        if sensor:
            current_data = rate
        else:
            current_data['rate'] = rate

    return current_data


def attenuate_pump_rate(rate, stop_rate=None, is_lowerbound=False):

    """
    attenuate_pump_rate - checks if pump adjustment will exceed engineering limits
       or recipe stage boundaries. Attenuates rate by reducing to boundary value.
    :param rate: int - current pump rate in steps/s
    :param stop_rate: int - recipe end rate for pump in steps/s
    :param is_lowerbound" bool - indicates rate decreasing e.g. lower bound threshold
    :return: 2-list
      :rate: float cleaned up rate value
      :rate_limit_hit: bool - Indicates attenuation so stage not stuck in infinite loop trying to reach
        out of bounds stop value
    """

    # Indicates if stop_value exceeded
    rate_limit_hit = False

    # Clean up pump rate if zero (e.g.stopped) or negative (e.g. pumping in reverse)
    if rate < MIN_PUMP_RATE:

        if rate < 0:
            #if in reverse, stop pump
            rate=0
        else:

            # if non-negative but lower than minimum readjust to nominal rate
            rate = MIN_PUMP_RATE
        rate_limit_hit = True
        
        #raise mass recipe discrepency error and note in log
        #...

    # Reduce pump rate if exceeds mechanical pump speed threshold
    if rate > MAX_PUMP_RATE:

        rate = MAX_PUMP_RATE
        rate_limit_hit = True

        #raise mass recipe discrepency error and note in log
        #...


    if stop_rate:
        # If new rate exceeds stop rate, go with max rate
        #  (or if negative rate and min)
        if (rate > stop_rate \
             and not is_lowerbound) or \
           (rate < stop_rate \
            and is_lowerbound):

            # replace rate with stop value
            rate = stop_rate
            rate_limit_hit = True

    rate_j = [rate, rate_limit_hit]

    return rate_j



def pump_calibration():

    """
    Calibrate constant to calculate pump mass/step ratio
      using range of pump speeds to for feed solution viscocity 
    """
    #...
    
    return step_constant

def max_pressure(bioreactor_type=DEFAULT_REACTOR_MODEL):

    """
    max_pressure - returns maximum pressure (atm) safely allowed by vessle

    :return: maximum safe pressure for given reactor.
      
    """

    bioreactor_specs = {'ficticfeed100':{'p_max':100}}

    specs = bioreactor_specs[bioreactor_type]
    p_max  = specs['p_max']

    return p_max


def pump_prime(prime_duration=5):
    """
     Fill dead volume of pump with glucose feedstock
      by running pump at max rate offline for set number of seconds (prime_duration)

    :param prime_duration: int time (seconds) to run pump at max speed
    :return: None
    """

    #  Priming program will depend on type of pump:
    #    peristaltic: high speed until stock starts losing weight. Continue for remainder of tubing
    #    diaphragm: high speed for several seconds.
    #    syringe: Fill to capacaity of pump.
    
    valve(0)
    pump(MAX_PUMP_RATE)
    sleep(prime_duration)
    pump(0)
    valve(1)

    return None



def is_feedempty(sensor_data):

    """
    Checks if glucose feed ran out.
      If scale stops decreasing while pump is going, attempts prime
      monitors if scale starts going down.
    """

    # take derivative of scale readings wrt time

    # compare to pump readings

    # if pump rate >> 0 and scale == 0 then prime

        # check scale again

        # if scale still unchanging, return True

    
    pass


def check_feed_contamination(sensor_data):

    """
    Checks if outgassing or foam from over-pressured vessle
    is traveling up feedstock tubing and contaminating glucose container

    """

    pass


def compare_scale_pump_pressure(sensor_data):

    """
    Checks if mass scale change, pump rate, and pressure data make physical sense
    Comparing rates of change with eachother at given times
    """

    pass


def vessle_conditions_good( maxpressure=True,
                            sensor_consistency=False,
                            feedempty=False,
                            contamination=False,
                            sensor_readings=None):


    """
    Checks multiple experimental conditions and egnineering controls at once
    Returns True if all pass, False if any fail
    """

    # Instantate list
    checks = []

    # Check if max pressure exceeded
    if maxpressure:
        goodpressure = pressure() < max_pressure()
        checks.append(goodpressure)

    # Check if atm, pump, and mass rate of changes are in agreement w/ eachother
    if sensor_consistency:
        consistent = compare_scale_pump_pressure(sensor_readings)
        checks.append(consistent)

    # Check if feedstock ran out
    if feedempty:
        feed = is_feedempty(sensor_readings)
        checks.append(feed)

    # Check if feedstock has evidence of contamination
    if contamination:
        contam = check_feed_contamination(sensor_readings)
        checks.append(contam)

    return all(checks)
