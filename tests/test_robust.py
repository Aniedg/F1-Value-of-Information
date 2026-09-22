import unittest
import numpy as np
import pandas as pd
from pitvoi.robust import RobustConfig,replay_robust,weighted_quantile


def frame(values,ages=None):
    return pd.DataFrame([dict(Driver='AAA',Stint=1,LapNumber=i+1,tyre_age_start=a,
        lap_seconds=v,Compound='HARD') for i,(v,a) in enumerate(zip(values,ages or list(range(len(values)))) )])


class RobustTests(unittest.TestCase):
    def test_first_unusual_lap_does_not_create_false_trend(self):
        rows=replay_robust(frame([138,100,100,100,100]),RobustConfig())
        self.assertAlmostEqual(rows[0]['predicted'],100)
        self.assertLess(abs(rows[1]['predicted']-100),.01)

    def test_current_and_future_values_do_not_change_prediction(self):
        a=replay_robust(frame([100,101,100,99,102]),RobustConfig())
        b=replay_robust(frame([100,101,100,500,800]),RobustConfig())
        self.assertEqual(a[0]['predicted'],b[0]['predicted'])
        self.assertEqual(a[0]['variance'],b[0]['variance'])
        self.assertEqual(a[:1],replay_robust(frame([100,101,100,99]),RobustConfig()))

    def test_gap_reset_uses_prior_observation(self):
        a=replay_robust(frame([100,101,102,105],[0,1,2,8]),RobustConfig())
        self.assertTrue(a[0]['gap_reset'])
        self.assertEqual(a[0]['predicted'],102)

    def test_clipped_update_limits_outlier_effect(self):
        values=[100,100,100,150,100]
        clipped=replay_robust(frame(values),RobustConfig(clip=2.5))
        plain=replay_robust(frame(values),RobustConfig(clip=1e6))
        self.assertLess(abs(clipped[-1]['predicted']-100),abs(plain[-1]['predicted']-100))

    def test_weighted_quantile(self):
        self.assertEqual(weighted_quantile([1,2,10],[.1,.1,.8],.5),10)


if __name__=='__main__':unittest.main()
