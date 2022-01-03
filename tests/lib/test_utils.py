import unittest
import pytest
from datetime import datetime, timedelta
import numpy as np
from lib.utils import *

class TestConvertRate:

    def test_conver_rate_mLmin_to_stepsec(self):

        # check pump rate unit conversion accuracy
        actual = convert_rate(60, units_den=['min','sec']) 
        expected = 5
        assert actual == pytest.approx(expected)

    def test_conver_rate_acc(self):

        # check pump increase rate conversion accuracy
        actual = convert_rate(360,
                              units_num = ['v', 'v'],
                              units_den=['min^2', 'sec^2'])
        expected = 0.1
        assert actual == pytest.approx(expected)

    def test_conver_rate_identity(self):

        # check pump doesn't change for same units
        actual = convert_rate(1,
                              units_num = ['v', 'v'],
                              units_den=['hour', 'hour'])
        expected = 1
        assert actual == pytest.approx(expected)



"""
class TestClusterPoints:

    test_input = {'points': None,
                       'epsilon': 1}

    def test_cluster_points_one_big_cluster(self):

        # check cluster function for one cluster
        test_points = np.array([[0, 0.5, 1, 1.5, 2],
                                [0, 1, 0, 1, 0]])
        TestClusterPoints.test_input['points'] = test_points
        expected = np.array([[1],
                             [0.4]])
        actual = cluster_points(TestClusterPoints.test_input['points'],
                                TestClusterPoints.test_input['epsilon'])
        assert actual == pytest.approx(expected)
                             
    def test_cluster_points_two_clusters(self):

        # check cluster function for two clusters
        test_points = np.array([[0, 0.5, 1.5, 2, 2.5],
                                [0, 2,   1,   9, 3]])
        TestClusterPoints.test_input['points'] = test_points
        expected = np.array([[0.25, 2],
                             [1,    4.33]])
        actual = cluster_points(TestClusterPoints.test_input['points'],
                                TestClusterPoints.test_input['epsilon'])
        assert actual == pytest.approx(expected)
"""


class TestIntegral:

     def test_integral_flat_slope(self):

        # check that rectangle has expected area
        test_points_t = [i/10 for i in range(0,11)]
        test_points = list(zip(test_points_t, [1]*11))
        expected = 1
        actual = integral(test_points)

        assert actual == pytest.approx(expected)

     def test_integral_leftbound_quartercircle(self):

        # check that left bound param works
        test_points_y = [np.sqrt(1-(i/10)**2) for i in range(-10, 11)]
        test_points_t = list([i/10 for i in range(-10,11)])
        test_points = list(zip(test_points_t, test_points_y))

        expected = 0.785
        actual = integral(test_points, segment_start=10)
        np.testing.assert_approx_equal(expected, actual, significant=2)
       
     def test_integral_rightbound_quartercircle(self):

        # check that right bound param works
        test_points_y = [np.sqrt(1-(i/10)**2) for i in range(-10, 11)]
        test_points_t = list([i/10 for i in range(-10,11)])
        test_points = list(zip(test_points_t, test_points_y))
                                
        expected = 0.785
        actual = integral(test_points, segment_end=11)
        np.testing.assert_approx_equal(expected, actual, significant=2)
    

class TestDerivative:

    def test_derivative_unitsquare_endpoint(self):

        # check flat line has slope 0
        test_points_t = [i/10 for i in range(0,11)]
        test_points = list(zip(test_points_t, [1]*11))
        expected = 0
        actual = derivative(test_points)
        assert actual == pytest.approx(expected)

    def test_derivative_unitline_endpoint(self):

        # check unit line has slope 1
        test_points_t = [i/10 for i in range(0,11)]
        test_points = list(zip(test_points_t, test_points_t))

        expected = 1
        actual = derivative(test_points)
        assert actual == pytest.approx(expected)

    def test_derivative_absolute_times(self):

        # check if time input works
        t = [datetime.now() + timedelta(seconds=5*i) for i in range(0,5)]
        y = list(range(0,5))
        test_points = list(zip(t,y))
        expected = 0.2
        actual = derivative(test_points)
        assert actual == pytest.approx(expected)

        

    def test_derivative_relative_times(self):

        # check if time input works
        test_points = [(timedelta(seconds=5*i), i) for i in range(0,5)]
        expected = 0.2
        actual = derivative(test_points)
        assert actual == pytest.approx(expected)



    def test_derivative_unitquadratic_midpoint(self):

        # Check that boundary point w/ 0 avg yields slope of 0
        test_points_y = [(i/10)**2 for i in range(-10, 11)]
        test_points_t = [i/10 for i in range(-10, 11)]
        test_points = list(zip(test_points_t, test_points_y))
        expected = 0
        actual = derivative(test_points, t_0=0)
        assert actual == pytest.approx(expected)

    def test_derivative_unitquadratic_nonboundary(self):

        # Check that boundary point w/ 0 avg yields slope of 0
        test_points_y = [(i/10)**2 for i in range(-10, 11)]
        test_points_t = [i/10 for i in range(-10, 11)]
        test_points = list(zip(test_points_t, test_points_y))
        expected = 0.1
        actual = derivative(test_points, t_0=0.05)
        assert actual == pytest.approx(expected)


        
    def test_derivative_single_point(self):

        # Check that single point returns no derivative
        test_points = [(1,1)]
        actual = derivative(test_points)
        assert actual is None

