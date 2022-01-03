import unittest
import pytest
import numpy as np
from copy import deepcopy
from datetime import datetime
from classes.recipe_coefficients import MassSegment
from lib.utils import convert_rate
from datetime import datetime, timedelta

class TestMassSegment(unittest.TestCase):
    
    test_recipe = {1:{'feed_type':'timed',
                      'start_parameters': {'rate': 60},#mL/min
                      'stop_parameters': {'stop_type':'time',
                                          'stop_value': 0.1} #min
                      },
                   2:{'feed_type':'linear',
                      'start_parameters':{'inc_rate': 180}, #mL/min^2
                      'stop_parameters':{'stop_type':'rate',
                                         'stop_value': 6} #mL/min
                      },
                   3:{'feed_type':'bolus',
                      'start_parameters':{},
                      'stop_parameters':{'stop_type':'mass',
                                         'stop_value': 1}  #g
                      }
                   }
    
    test_conditions = {'time':datetime.now(),
                       'rate': 10, #g/s aka 50 step/s
                       'rate_mL_min': 300, #mL/min
                       'rate_s_sec':50, #steps/s
                       'mass':1}

    def test_bolus_coefficients(self):

        # Test bolus coefficient method for accuracy
        bolus_recipe = TestMassSegment.test_recipe[3]
        ms_b = MassSegment(bolus_recipe,
                           3,
                           bolus_recipe['feed_type'],
                           bolus_recipe['start_parameters'],
                           bolus_recipe['stop_parameters'])
        actual_coefficients = ms_b.calculate_bolus(TestMassSegment.test_conditions)
        expected_coefficients = np.array([0, 2]) #default pump rate in g/s
        expected_stop_value = 0
        assert actual_coefficients == pytest.approx(expected_coefficients) \
          and expected_stop_value == ms_b.stop_value


    def test_timed_coefficients(self):

        # Test timed coefficient method for accuracy
        timed_recipe = TestMassSegment.test_recipe[1]
        ms_t = MassSegment(timed_recipe,
                           1,
                           timed_recipe['feed_type'],
                           timed_recipe['start_parameters'],
                           timed_recipe['stop_parameters'])

        actual_coefficients = ms_t.calculate_timed(TestMassSegment.test_conditions)
        expected_coefficients = np.array([0, 1]) #g/s
        expected_stop_value = datetime.now() + timedelta(seconds=6)
        approximately_zero = expected_stop_value - ms_t.stop_value
        assert actual_coefficients == pytest.approx(expected_coefficients) \
          and 2 > abs(approximately_zero.seconds)

    
    def test_linear_coefficients(self):

        # Test linear coefficient method for accuracy
        linear_recipe = TestMassSegment.test_recipe[2]
        ms_lin = MassSegment(linear_recipe,
                             2,
                             linear_recipe['feed_type'],
                             linear_recipe['start_parameters'],
                             linear_recipe['stop_parameters'])
        actual_coefficients = ms_lin.calculate_linear(TestMassSegment.test_conditions)
        expected_coefficients = np.array([0.05, 2]) #180 mL/min^2, and default pump rate
        expected_stop_value = convert_rate(linear_recipe['stop_parameters']['stop_value'],
                                           units_num=['v', 'm'], units_den=['min', 'sec'])
        #convert stop val of 6 mL/min to 0.1 #g/s
        assert actual_coefficients == pytest.approx(expected_coefficients) \
          and expected_stop_value == pytest.approx(ms_lin.stop_value)
