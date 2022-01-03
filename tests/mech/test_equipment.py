import unittest
import pytest
from datetime import datetime
from mech.equipment import *
from mech.actuator import MOCK_ACTUATOR

class TestCurrentReadings:

    # Set system parmameters 
    MOCK_ACTUATOR['VALVE']=0
    MOCK_ACTUATOR['SCALE']=500
    MOCK_ACTUATOR['PUMP']=0
    MOCK_ACTUATOR['PRESSURE']=1
    MOCK_ACTUATOR['TUNE']=[1,0,0]

    def test_current_readings_data_structure(self):

        # Check that simulated sensor readings are correctly formatted
        actual = current_readings()
        assert isinstance(actual, dict) and len(actual)==5


    def test_current_reading_single_sensor(self):

        # Check that single sensor input returns respective sensor output

        actual = current_readings(sensor='time')
        assert isinstance(actual, datetime)


class TestAttenuatePumpRate:

    def test_attenuate_pump_rate_intermediate_value(self):

        # checks if moderate pump rate is unaffected
        expected_rate = 10 #steps/s
        actual = attenuate_pump_rate(expected_rate)
        actual_val = actual[0]
        assert actual_val == expected_rate


    def test_attenuate_pump_rate_lowerbound(self):

        # Lower boundary stop rate attenuation check
        test_rate = 10 #steps/s
        test_stop_rate = 5 #steps/s 
        actual = attenuate_pump_rate(rate=test_rate,
                                     stop_rate=test_stop_rate)
        actual_val = actual[0]
        expected_rate = 5
        assert  expected_rate == pytest.approx(actual_val)


    def test_attenuate_pump_rate_high_value(self):

        # checks if high pump rate is lowered
        test_rate = 15000 #steps/s
        actual = attenuate_pump_rate(test_rate)
        actual_val = actual[0]
        expected_rate = MAX_PUMP_RATE
        assert actual_val == expected_rate

        
    def test_attenuate_pump_rate_low_value(self):

        # checks if reverse pump rate is stopped
        test_rate = -10 #steps/s
        actual = attenuate_pump_rate(test_rate)
        actual_val = actual[0]
        expected = 0
        assert actual_val == expected

        
    def test_attenuate_pump_rate_overrate_value(self):

        # checks if high pump rate is lowered based on stop_rate
        #  and flag is returned
        test_rate = 10 #steps/s
        test_stop_rate = 5
        actual = attenuate_pump_rate(rate=test_rate, stop_rate=test_stop_rate)
        actual_val = actual[0]
        flag = actual[1]
        expected_0 = 5
        expected_1 = True
        assert actual_val == expected_0 \
          and flag== expected_1


    class TestVessleConditionsGood:

        def test_vessle_conditions_good_valid_output(self):

            # checks if returns boolean
            actual = vessle_conditions_good()
            assert isinstance(actual, bool)


        def test_vessle_conditions_good_returns_False_none(self):

           #returns False for incomplete null functions
           expected = False
           actual = vessle_conditions_good(feedempty=True)
           assert actual == expected










