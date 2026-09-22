import unittest
from pitvoi.gaussian import LapScenario,LapSolver
from pitvoi.waiting_condition import decompose

class WaitingConditionTests(unittest.TestCase):
    def test_bellman_decomposition_and_action_equivalence(self):
        for noise in [.5,1.5,4.]:
            for loss in [8,18,32]:
                solver=LapSolver(LapScenario(noise_sd=noise,pit_loss=loss),grid_size=801,quadrature=81)
                for t in range(8):
                    for p in [0,.2,.5,.8,1]:
                        d=decompose(solver,t,p)
                        self.assertAlmostEqual(d['learning_benefit'],d['next_observation_benefit']+d['later_learning_benefit'],places=10)
                        # Quadrature/interpolation can weakly violate exact concavity.
                        self.assertGreaterEqual(d['next_observation_benefit'],-1e-5)
                        self.assertGreaterEqual(d['later_learning_benefit'],-1e-5)
                        if abs(d['adaptive_wait_advantage'])>1e-8:
                            self.assertEqual(d['adaptive_pits'],d['adaptive_wait_advantage']<0)

    def test_last_lap_has_no_information_value(self):
        solver=LapSolver(LapScenario())
        self.assertEqual(decompose(solver,7)['learning_benefit'],0)
