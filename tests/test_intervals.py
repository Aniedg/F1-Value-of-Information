import unittest
from pitvoi.intervals import apply_intervals,interval_metrics


def rows(values):
    return [dict(driver='AAA',lap=i+1,predicted=100,variance=1,observed=v) for i,v in enumerate(values)]


class IntervalTests(unittest.TestCase):
    def test_current_and_future_target_cannot_change_width(self):
        a=apply_intervals(rows([100,104,100]),[1]*201,prior_mass=1)
        b=apply_intervals(rows([100,500,800]),[1]*201,prior_mass=1)
        self.assertEqual(a[1]['lower'],b[1]['lower'])
        self.assertEqual(a[1]['upper'],b[1]['upper'])
        self.assertEqual(a[:2],apply_intervals(rows([100,104]),[1]*201,prior_mass=1))

    def test_past_errors_expand_width_and_drivers_are_isolated(self):
        a=apply_intervals(rows([105,105,100]),[1]*201,prior_mass=1)
        self.assertGreater(a[2]['upper']-a[2]['lower'],a[0]['upper']-a[0]['lower'])
        extra=[dict(r,driver='BBB') for r in rows([100,100,100])]
        b=apply_intervals(rows([105,105,100])+extra,[1]*201,prior_mass=1)
        self.assertEqual(b[3]['upper'],101)

    def test_interval_score_penalises_width_and_misses(self):
        metrics=interval_metrics([dict(observed=3,predicted=0,lower=-1,upper=1)])
        self.assertEqual(metrics['interval_score'],42)
        self.assertEqual(metrics['coverage90'],0)


if __name__=='__main__':unittest.main()
