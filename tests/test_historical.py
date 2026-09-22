import unittest
import pandas as pd
from pitvoi.historical import quality_audit


class HistoricalTests(unittest.TestCase):
    def test_quality_reasons_and_prefix_invariance(self):
        row = dict(Driver='AAA', LapTime=pd.Timedelta(seconds=90), TyreLife=4,
                   LapNumber=5, Stint=1, Time=pd.Timedelta(seconds=450),
                   PitInTime=pd.NaT, PitOutTime=pd.NaT, TrackStatus='1',
                   Compound='MEDIUM', IsAccurate=True, FastF1Generated=False)
        frame = pd.DataFrame([row, {**row, 'LapNumber': 6, 'TrackStatus': '14'},
                              {**row, 'LapNumber': 7, 'PitInTime': pd.Timedelta(seconds=620)}])
        audited, counts = quality_audit(frame)
        self.assertEqual(audited['eligible'].tolist(), [True, False, False])
        self.assertEqual(counts['not_green'], 1)
        prefix, _ = quality_audit(frame.iloc[:1])
        self.assertEqual(prefix['eligible'].tolist(), audited['eligible'].iloc[:1].tolist())


if __name__ == '__main__':
    unittest.main()
