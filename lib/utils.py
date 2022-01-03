import numpy as np
from copy import deepcopy
from datetime import datetime, timedelta

# System default values
VESSLE_PRESSURE_LIMIT = 5 #atm
GLUCOSE_SOLN_DENSITY = 1 #g/mL
NOMINAL_MASS_PER_STEP = 0.2 #g/step
NOMINAL_VOL_PER_STEP = 0.2 #mL/step
DEFAULT_PUMP_RATE = 10 #steps/sec
MAX_PUMP_RATE = 12000 #steps/sec
MIN_PUMP_RATE = 0.1 #steps/sec
PID_ADJUSTMENT_INCREMENT = 1 #second
DEFAULT_K = np.array([1,0,0]) # default pid tune parameters
DEFAULT_REACTOR_MODEL = 'ficticfeed100'

def convert_rate(rate, units_num = ['v', 's'], units_den = None,
                  step_constant=NOMINAL_VOL_PER_STEP,
                  density=GLUCOSE_SOLN_DENSITY):

    """
    pump step to gram conversion

    :param rate: float - rate to be converted

    :param units_num: list - conversion units input/output (numerator).
                       First position is input, second output.
                        'v' indicates volume rate (mL/s)
                        's' indicates step rate (steps/s)
                        'm' indicates mass rate (mass/s)
    :param units_den: list - conversion units for denominator (e.g. time)
                       First position is input, second is output.
                        'sec' is seconds
                        'min' is minutes
                        'hour' is hours
                        'sec^2' is seconds squared, for acceleration rate conv.
                        'min^2' is minutes squared, for acc rate conv

    :step_constant: float - volume transferred per pump step (mL per step)

    :density: float - density of solution being pumped (g/mL)

    :return: float - pump rate in desired units
    """

    # factors used if density or step -> vol conversions take place
    step_factor = 1
    density_factor = 1
    time_factor = 1

    # if numerator value is to be converted
    if units_num:

        # determine whether to multiply or divide by step_constant
        if units_num[0]=='s' and units_num[1]!='s':
            step_factor = step_constant
        if units_num[1]=='s' and units_num[0]!='s':
            step_factor = 1/step_constant

        # determine whether to multiply or divide by density
        if units_num[0]=='m' and units_num[1]!='m':
            denisty_factor = 1/density
        if units_num[1]=='m' and units_num[0]!='m':
            density_factor = density

    # convert time units if present
    if units_den:

        # determine relative scale of time units
        timescale = list()
        for u in units_den:

            # Convert from hour <-> min <-> sec rates
            if u=='sec' and ('min' in set(units_den) or \
                             'hour' in set(units_den)):
                timescale.append(1)
            elif u=='min' and ('sec' in set(units_den) or \
                             'hour' in set(units_den)):
                timescale.append(2)
            elif u=='hour'and ('sec' in set(units_den) or \
                             'min' in set(units_den)):
                timescale.append(3)
                
            # acceleration unit conversion rates
            elif u=='sec^2' and 'min^2' in units_den:
                timescale.append(2) 
            elif u=='min^2' and 'sec^2' in units_den:
                timescale.append(4)
        # if timescale none
        if not timescale:
            timescale=[1,1]
        # calculate conversion rate for given units
        t_exp = timescale[1] - timescale[0]
        time_factor = 60**t_exp

    # multiply given rate by conversion factors
    converted_rate = rate * step_factor * density_factor * time_factor

    return converted_rate



def integral(points, segment_start=None, segment_end=None, abs_t=True):
    
    """
    discrete integral - trapezoidal method

    :param points: list of ordered tuples e.g. [(t_i, y_i)]

    :param segment_start: start index position of start of segment to be integrated

    :param segment_end: end index position of end of segment to be integrated

    :param abs_t: bool if True adds absolute value of negative t values to summand i
    """

    # Convert to array, sort by first index
    points_arr = np.array(points)
    points_arr[np.argsort(points_arr[:,0])]

    if segment_end:
        segment_end+=1

    # If absolute times listed in dt, convert to relative time (in seconds) 
    if isinstance(points_arr[0,0], datetime):

        # Convert datetime objects into time relative to first point (in sec)
        relative_time = points_arr[:,0] - points_arr[0,0]
        relative_time = np.array(relative_time)
        ts = np.array(list(map(lambda t: t.seconds, relative_time)))

    # if relative timedeltas, convert to seconds
    elif isinstance(points_arr[0,0], timedelta):
        ts=np.array(list(map(lambda t: t.seconds, points_arr[:,0])))    

    else:
        # otherwise, no cleanup necessary
        ts = points_arr[:,0]

    # Calculate delta values of points
    dt = np.diff(ts)
    t_seg = ts[segment_start:segment_end]
    y_seg = points_arr[segment_start:segment_end,1]
    
    if not abs_t:
        
        # negative t values possible
        integral_trap = np.trapz(y_seg, t_seg)
        
    else:
        #absolute values of t values

        # separate negative from positive t axis segments
        positive_t_index = np.where(t_seg >= 0)
        negative_t_index = np.where(t_seg < 0)
        
        # positive integral
        integral_pos = np.trapz(y_seg[positive_t_index],
                                t_seg[positive_t_index])
        # negative integral
        integral_neg = np.trapz(y_seg[negative_t_index],
                                t_seg[negative_t_index])

        # absolute value of integral
        integral_trap = integral_pos + abs(integral_neg)

    return integral_trap 


def derivative(points, t_0=None):

    """
    discrete derivative - calculates differenial quotient between closest points

    :param points_tup: list of ordered tuples e.g. [(t_i, y_i)]

    :param t_0: float position of tangent. If none, returns slope of last segment

    :return: diff_x_0 float - Difference quotient for specified time interval (or last listed time interval)
    """

    # Instantiate return
    diff_x_t0 = None
    
    # Convert to array, sort by first index
    points_arr = np.array(points)
    points_arr[np.argsort(points_arr[:,0])]

    # proceed if there are enough points to calculate differential
    if points_arr.shape[0] >= 2:

        # If absolute times listed in dt, convert to relative time (in seconds) 
        if isinstance(points_arr[0,0], datetime):

            # Convert datetime objects into time relative to first point (in sec)
            relative_time = points_arr[:,0] - points_arr[0,0]
            relative_time = np.array(relative_time)
            ts = np.array(list(map(lambda t: t.seconds, relative_time)))

        # if relative timedeltas, convert to seconds
        elif isinstance(points_arr[0,0], timedelta):
            ts=np.array(list(map(lambda t: t.seconds, points_arr[:,0])))    

        else:
            # otherwise, no cleanup necessary
            ts = points_arr[:,0]
            
        # Calculate delta values of points
        dt = np.diff(ts)
        dy = np.diff(points_arr[:,1])
        # proceed if there are enough still enough points to calculate differential
        if dt.size and dy.size:

            # take differenital quoient, excepting zero denominators    
            differential_delta = [dy[i]/dt[i] if dt[i] else np.NaN \
                                  for i in range(dy.size)]

            if t_0 is None:

                # Return most recent derivative segment if time not specified
                diff_x_t0 = differential_delta[-1:][0]

            else:

                # If t_0 is specified, select tangent corresponding to
                #   corresponding time interval for t_0 from differential_delta list

                # Assign left boundary to corresponding time interval of slope
                differential_delta = np.array(list(zip(points_arr[1:, 0], differential_delta)))
                
                if t_0 <= points_arr[-1, 0] and\
                   t_0 >= points_arr[0,0]:
                   # confirm t is within range

                    if t_0 not in points_arr[:,0]:

                        # If t_0 is not a boundary value, simply select corrresponding time interval

                        # Increment through points until t_i is closest left boundary to t_0
                        i=0
                        t_i = points_arr[0,0]
                        while t_0 > t_i:
                            # cycle through derivaive values until t_0 segment
                            t_i = differential_delta[i, 0]
                            d_i = differential_delta[i, 1]
                            i+=1

                        # dervative of closet left-most boundary is t_0's correpsonding tangent
                        diff_x_t0 = d_i

                    elif t_0 < points_arr[-1, 0]:

                        # If t_0 is intermediate boundary value, take average of two adjacent tangents

                        # Retrieve index of corresponding left boundary 
                        i = np.where(points_arr[:,0]==t_0)[0][0]

                        # If start of series, return single adjacent boundary (right tangent doesn't exist)
                        if i==0:
                             diff_x_t0 = differential_delta[0,1]

                        # If intermediate boundary value, return average
                        elif isinstance(i, int) or \
                             isinstance(i, np.int64):

                            diff_x_t0 = (differential_delta[i-1,1] + differential_delta[i,1])/2
                    else:
                        # by process of elimination t_0 = points_arr[-1,0]
                        
                        # return last element
                        diff_x_t0 = differential_delta[-1,1]

                else:
                    # raise error/record in log and return None; t_0 > t_max or < t_min; 
                    pass
                    
        else:
            # If diff data set is empty, derivative is undefined.
            pass

    else:

        # If data set only contains one point, derivative is undefined.
        pass

    return diff_x_t0
