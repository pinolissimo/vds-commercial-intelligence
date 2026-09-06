import unittest

from scripts.acquisition_performance_optimizer import (
    SOURCE_EXPLORATION_FLOOR,
    adjust_source_multiplier,
    choose_turbo,
)
from scripts.enrich_command_center_funnel import classify_status


class AcquisitionThroughputPolicyTests(unittest.TestCase):
    def test_large_qualified_backlog_enables_turbo_even_when_raw_precision_is_bottleneck(self):
        enabled, reason = choose_turbo("RAW_SOURCE_PRECISION", 89, False)
        self.assertTrue(enabled)
        self.assertEqual(reason, "QUALIFIED_BACKLOG_PRESSURE")

    def test_hysteresis_keeps_turbo_stable_while_backlog_drains(self):
        enabled, reason = choose_turbo("RAW_SOURCE_PRECISION", 12, True)
        self.assertTrue(enabled)
        self.assertEqual(reason, "QUALIFIED_BACKLOG_DRAIN_HYSTERESIS")

    def test_small_backlog_releases_turbo(self):
        enabled, reason = choose_turbo("RAW_SOURCE_PRECISION", 4, True)
        self.assertFalse(enabled)
        self.assertEqual(reason, "NO_TURBO_PRESSURE")

    def test_noisy_source_is_constrained_but_never_disabled(self):
        multiplier = adjust_source_multiplier(1.5, 0.0, 100)
        self.assertGreaterEqual(multiplier, SOURCE_EXPLORATION_FLOOR)
        self.assertLessEqual(multiplier, 0.45)

    def test_high_yield_source_is_not_penalized_by_noisy_source_cap(self):
        multiplier = adjust_source_multiplier(1.2, 0.75, 100)
        self.assertGreater(multiplier, 0.70)

    def test_legacy_ready_is_not_executable(self):
        self.assertEqual(classify_status("READY_FOR_DAILY_OUTREACH_REVIEW"), "LEGACY_ADVISORY")
        self.assertEqual(classify_status("READY_TO_CONTACT"), "EXECUTABLE")
        self.assertEqual(classify_status("READY_TO_CONTACT_MANUAL_ROUTE"), "MANUAL_APPLY")


if __name__ == "__main__":
    unittest.main()
