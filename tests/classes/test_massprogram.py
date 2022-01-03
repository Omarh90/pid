import unittest
import pytest
from classes.massprogram import MassProgram
from mech.actuator import pump

class TestMassProgram(unittest.TestCase):

    test_recipe = {1:{'feed_type':'timed',
                      'start_parameters': {'rate': 1},#mL/min
                      'stop_parameters': {'stop_type':'time',
                                          'stop_value': 0.1} #min
                      },
                   2: {'feed_type':'linear',
                      'start_parameters':{'inc_rate': 0.1}, #mL/min^2
                      'stop_parameters':{'stop_type':'rate',
                                         'stop_value': 1} #mL/min
                      }
                   }

    def test_massprogram_iteration(self):

        # check that MassProgram is iterable
        mp = MassProgram(TestMassProgram.test_recipe)
        with pytest.raises(StopIteration):
            while True:
                next(mp)


    def test_massprogram_pump(self):

        # check pump method works
        mp = MassProgram(TestMassProgram.test_recipe)
        mp.pump(5, input_units=['s','sec'])
        current_reading_st_sec=pump()/60
        expected = current_reading_st_sec
        assert 5 == pytest.approx(expected)



    def test_massprogram_pump_exceeded_rate(self):

        # check pump method works
        current_reading_st_sec=pump()/60
        expected = current_reading_st_sec
        mp = MassProgram(TestMassProgram.test_recipe)
        mp.pump(5000, input_units=['s','sec'])
        expected = current_reading_st_sec
        assert expected == pytest.approx(expected)




    def test_massprogram_get_stage(self):

        # test get parameter
        expected = TestMassProgram.test_recipe[1]
        mp = MassProgram(TestMassProgram.test_recipe)
        ms_1=mp.get_stage(1)
        assert ms_1.feed_type == expected['feed_type'] and \
        ms_1.start_parameters == expected['start_parameters'] and \
        ms_1.stop_parameters == expected['stop_parameters']
