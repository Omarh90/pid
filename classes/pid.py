from mech.actuator import tune, pump
from lib.utils import *
from lib.utils import integral, derivative

#TODO: fix buggy control loop logic

class PID:

    """
    PID class. Tunes PID coefficients, and calculates u(t)
      using either PID coefficients, or simple negative feedback control loop.

    """

    def __init__(self, K=DEFAULT_K):

        self.K = K #3-membered list: proportional integral and derivative K's
        self.current_u = 0       #u(t_0)
        self.rate_error = list() #e(t)
        self.sensor_data = list()
        self.derivatives = list() # de(t)/dt
        self.derivative= 0
        self.total_int=0 #cumulative integral

     #Confirm sensor_data and measured_data lists auto-update

    def tune(self):

        # Tune system to calculate PID parameters

        self.K = tune()

        return self.K

    def control_var(self, setpoint, process, continuous=True):

        """
        control_var - provides adjusted pumprate based on u(t),
           where u(t) = k_p*e(t) + k_i*e(t) + k_d*e(t),
           with e(t) being the error between the set point and measured point
            (e.g. pump rate set by pump() vs. scale mass-transfer rate),
            and k_p, k_i, k_d being PID coefficients from system tuning

        :param setpoint: list of tups [(t_i, x_i)] - expected setpoint values
        :param process: list of tups [(t_i, x_i)]  - measured setpoint values
        :return: set_rate0 modified set rate based on u(t)
        """

        # get most recent values
        setrate_0 = setpoint[-1:][0][1] 
        processrate_0 = process[-1:][0][1]

        # calculate error between scale-measured grams/s pump rate (in steps/s)
        #   vs. pump sensor speed rate(steps/s)
        rate_error_0 = setrate_0 - processrate_0
        self.rate_error.append((setpoint[-1:][0][0],
                                rate_error_0))

        if continuous:
        # process update every second
            
            if len(self.rate_error) >= 2:
                # Calculate integral & derivative of most recent points.
                # Add integral to previous sum to avoid recalculating points
                self.total_int +=integral(self.rate_error[-2:])
                self.current_derivative = derivative(self.rate_error[-2:])
                
                # Calculate PID control variable
                u_0 =  rate_error_0*self.K[0] + \
                       self.current_derivative * self.K[1] + \
                       self.total_int * self.K[2]

                # Update current u(t) value
                self.current_u = u_0

                # update pump rate according to u_i value
                setrate_0+=u_0 #?Not sure how to use u_0 here - is it additive?

        else:
            # batch process error corrections
            setpoint_arr = np.array(setpoint)
            process_arr = np.array(process)
            error_arr = setpoint_arr[:,1] - process_arr[:,1]
        
            error_ls = list(zip(setpoint_arr[:,0],error_arr))

            if len(error_ls) >= 2:
                # Calculate integral & derivative of entire data set
                inte = integral(error_ls)
                d_0 = derivative(error_ls)
                u_0 = rate_error_0 * self.K[0] + \
                        d_0 * self.K[1] + \
                        inte * self.K[2]

                # Update current u(t) value
                self.current_u = u_0
                
                # update pump rate according to u_i value
                setrate_0+=u_0 #?Not sure how to use u_0 here - is it additive?

        return setrate_0


    def simple_control_var(self, setpoint, process):

        """
         rudmentary cascade adjusment of pump rate:
           - increases pump rate by 5% if e<0
           - decreases by 5% if e>0

        param setpoint: list of tups [(t_i, x_i)] - expected setpoint values
        param process: list of tups [(t_i, x_i)]  - measured setpoint values
        """ 

        rate_error_i = setpoint[-1:][0][1] - process[-1:][0][1]
        t_f = setpoint[-1:][0][0]
        self.rate_error.append((t_f, rate_error_i))

        if rate_error_i > 0:
            # increase pump if too slow                     
            pump('f')

        elif rate_error_i < 0:
            # decrease pump if too fast
            pump('s')
