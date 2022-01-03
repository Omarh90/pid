from lib.utils import *
from mech.equipment import *
from mech.actuator import pump, valve, pressure
from classes.pid import PID
from classes.massprogram import MassProgram
from datetime import datetime, timedelta
import time


def main(recipe, verbose=False):

    """
    Main - runs recipe dictionary on fictitious feedstock vessel
    :param recipe: dict: dictionary specifying feed recipe with following syntax:
     recipe = {
              1:{
                   'feed_type':'timed',
                   'start_parameters': {'rate': 10},#pump rate in mL/min
                   'stop_parameters': {'stop_type':'time',
                                       'stop_value': 0.3} duration in minutes
                       },
              2:{
                    'feed_type':'bolus',
                    'start_parameters':{},
                    'stop_parameters':{'stop_type':'mass',
                                       'stop_value': 5} target mass in grams
                       },
              3:{
                    'feed_type':'linear',
                    'start_parameters':{'inc_rate': 10}, acceleration in mL/min^2
                    'stop_parameters':{'stop_type':'rate',
                                       'stop_value': 20} stop rate in mL/min
                       }
             }
    :return None:

    
    """


    try:

        # Instantiate sensor stores
        sensor_data = {'scale':[], 'pump':[], 'pressure':[]}
        pressure_check = pressure() #initial pressure (atm)
        sensor_data['pressure'].append((datetime.now(), pressure_check))

        # Bool monitoring of experimental conditions
        #rate_limit_hit = False
        pump_limit_exceeded = False # max/min pump rate hit during recipe. Ends current recipe stage.
        rate_meas = None # pump rate determined by scale change per time
        next_rate = None # pump rate determined by mass program
        add_to_rate =False # add to current pump rate or replace rate

        # Instantiate massprogram objects (e.g. mass-defined recipe)
        mp = MassProgram(recipe)
        pid=PID() #insantiate PID object
        measured_data = {'pump':[], # rate of change determined emperically from scale mass/s
                         'pressure':[]} #rate of change of pressure wrt time
        rate_epsilon =  [] # e(t) of pump rates for pid measurement

        # generate run coefficients for first stage of recipe 
        next(mp)
        if verbose:
            print("First stage of recipe has started. Recipe type: {}".format(mp.feed_type))

        # get pump start rate
        next_rate = mp.coeff[1] #pump rate in g/s
        # open valve
        valve(1)
        # start pump
        pump_limit_exceeded = mp.pump(next_rate) #use mp.pump for better control?

        # PID controlled glucose feed loop (w/ 1 second increment)

        while mp.current_stage <= mp.len_stages \
               and vessle_conditions_good():
            # check if recipe done & if experiment and eng controls acceptable

            # instantiate list index
            i = mp.current_stage - 1

            # read sensors
            current_data = current_readings()
            pressure_check = current_data['pressure']

            # print status
            if verbose:

                #define units for formatting
                print_units = {'mass':'g', 'rate':' steps/sec', 'pressure': ' atm', 'valve': ''}

                print_data = dict()
                # format data for print
                for k, v in current_data.items():
                    if k != 'time' and k != 'valve':
                        print_data[k] = str(round(v ,2)) + print_units[k]
                    elif k=='valve':
                        print_data[k] = (lambda x: ' open' if 1 else 'close')(v)
                txt="current sensors data as of {}:"
                now=datetime.now().strftime("%H:%M:%S")
                print(txt.format(now))
                print(print_data)
         
            # Store sensor readings
            sensor_data['pressure'].append((datetime.now(),
                                            pressure_check)) #atm
            sensor_data['scale'].append((datetime.now(), # time, relative (s)
                                         current_data['mass'])) #mass, relative (g)
            sensor_data['pump'].append((datetime.now(), #time, relative (s)
                                        current_data['rate']))  #pump rate in steps/second
            
            # if recipe type is linear, readjust pump rate accordingly
            if mp.stop_type == 'rate':

                # convert pump rate and readjust value if physically feasible
                
                # adjust pump rate according to recipe if linear
                # (according to relative increase; e.g. what to add to current rate)
                #  rate_i_calc => calculated rate from recipe


                
                del_t = mp.massprogram[i].t0_stage - current_data['time']

                del_t = current_data['time'] - mp.massprogram[i].t0_stage
                      
                add_to_rate = mp.coeff[0]*del_t.seconds  #+ mp.coeff[1] #g/s
                              

                # Update next_rate pump setting in correct units
                next_rate_st = current_data['rate']
                next_rate = convert_rate(next_rate_st, ['s', 'm']) #steps/s => g/s

                # PID controller ineffective without emperically-based tuning parameters
                ## increment pump rate and attenuate wrt engineering controls
                #pump_limit_exceeded = mp.pump(next_rate, ['m', 'sec'],
                #                              add_to_rate=add_to_rate,
                #                              pid=[1,0,0])
                # add to rate
                next_rate+=add_to_rate

            # check if stop target value was hit for given stage       
            if (current_data[mp.stop_type] >= mp.stop_value and not mp.is_lowerbound) or \
                (current_data[mp.stop_type] <= mp.stop_value and mp.is_lowerbound): # or pump_limit_exceeded DISABLED:
                 # check if pump rate is decreasing or pump stop rate hit
                
                # go to next stage in recipe
                if verbose:
                    print("completed stage {}: {} portion of recipe".format(mp.current_stage, mp.feed_type))
                next(mp)

                # update list index
                i = mp.current_stage - 1

                #except StopIteration:
                #    pass
                # Reset loop vars
                pump_limit_exceeded = False
                add_to_rate = False

                # update pump rate to new recipe stage rate if type=timed
                if mp.feed_type == 'timed':

                    # Retrieve constant coefficient (e.g. b in y=mx+b)
                    next_rate = mp.coeff[1]
                    # Attenuate recipe value
                    pump_limit_exceeded = mp.pump(next_rate,
                                                  ['m', 'sec'], #g/sec
                                                  pid =[1,0,0]) 

            # emperically-determined pump rate based on measured mass change of scale per unit time
            rate_meas = derivative(sensor_data['scale'][-2:]) #just need last two points

            
            # if derivative exists
            if rate_meas:
                
                # make units consistent with comparison values
                rate_meas_st = -1*convert_rate(rate=rate_meas, units_num=['m', 's'])

                # store scale-measured pump rate
                measured_data['pump'].append((sensor_data['scale'][-1:][0][0], #time
                                              rate_meas_st))

                if len(measured_data['pump']) > 3:

                   # PID ineffecive without emperical data. Using simplified cascade (mp.simple_control_var)
                   ## determine PID correction based on error rate          
                   ##next_rate = pid.control_var(measured_data['pump'],
                   #                         sensor_data['pump'])

                   # determine PID correction based on error rate          
                   pid.simple_control_var(measured_data['pump'],
                                            sensor_data['pump'])
                   next_rate = pump()/60
                   
            # update pump rate; check if pump engineering limit exceeded
            pump_limit_exceeded = mp.pump(next_rate, ['s', 'm'])
                                                                                
            # repeat scale read, pump rate adjustments, PID adjustment             
            # and pressure reads once every second (or other # of seconds specified)
            time.sleep(PID_ADJUSTMENT_INCREMENT)                                        


        pressure_check = pressure()
        sensor_data['pressure'].append((datetime.now(), pressure_check))

    except StopIteration:

        if verbose:
            print("feed recipe complete")

    except Exception:

        if verbose:
            print("System Error: check your glucose feed")

    finally:

        # End feed
        valve(0)
        pump(0)



if __name__ == '__main__':

    # demo recipe
    recipe_dict = {1:{
                      'feed_type':'timed',
                      'start_parameters': {'rate': 10},#mL/min
                      'stop_parameters': {'stop_type':'time',
                                          'stop_value': 0.3}#min
                       },
                   2:{
                      'feed_type':'bolus',
                      'start_parameters':{},
                      'stop_parameters':{'stop_type':'mass',
                                         'stop_value': 15} #g
                       },
                   3:{
                      'feed_type':'linear',
                      'start_parameters':{'inc_rate': -1}, #mL/min^2
                      'stop_parameters':{'stop_type':'rate',
                                         'stop_value': 0} #mL/min
                       }
                    }
    main(recipe_dict, verbose=True)
