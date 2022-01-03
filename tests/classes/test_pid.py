import unittest
import pytest
import numpy as np
from classes.pid import *
from mech.equipment import current_readings

class TestPID(unittest.TestCase):

    def test_pid_instance_instantiate_without_error(self):

        # test error free-instance
        pid=PID()
        assert True

    def test_pid_tune_valid_output(self):
        
        # test k coefficient tune method for valid tune parameters 
        pid=PID()
        K_t=pid.tune()
        assert isinstance(K_t, np.ndarray) and len(K_t)==3 

    def test_pid_control_var(self):

        # check control_var method adjustedments in right direction
        test_setpoint = [(1, 1),  (2, 1),  (3, 1),  (4, 1), (5, 1)]
        test_process =[(1, 0.5),(2, 0.5),(3, 0.5),(4,0.5),(5,0.5)]
        pid=PID()
        actual = pid.control_var(test_setpoint, test_process, False)
        
        assert actual >= test_process[-1][1]

    def test_simple_control_var_overshoot(self):

        # check simplified control_var method adjustments
        test_setpoint = [(1, 1),  (2, 1),  (3, 1),  (4, 1), (5, 1)]
        test_process =[(1, 0.5),(2, 0.5),(3, 0.5),(4,0.5),(5,0.5)]
        initial_rate = current_readings('rate')
        pid=PID()
        pid.simple_control_var(test_setpoint, test_process)
        adjusted_rate = current_readings('rate')
        
        assert initial_rate < adjusted_rate
        
