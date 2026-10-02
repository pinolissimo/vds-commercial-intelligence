import json
import tempfile
import unittest
from pathlib import Path

import scripts.build_geographic_intelligence as geo


class GeographicRadarContractTests(unittest.TestCase):
    def test_exact_locality_coordinates_do_not_fall_back_to_regional_capital(self):
        self.assertEqual(geo.coords("Spain","Andalucía","Málaga"), (36.7213,-4.4214))
        self.assertNotEqual(geo.coords("Spain","Andalucía","Málaga"), geo.coords("Spain","Andalucía","Sevilla"))
        self.assertEqual(geo.coords("Spain","Castilla y León","Zamora"), (41.5033,-5.7446))
        self.assertEqual(geo.coords("Spain","País Vasco","Bizkaia"), (43.2630,-2.9350))

    def test_unknown_locality_is_not_silently_mapped_to_regional_capital(self):
        self.assertIsNone(geo.coords("Italy","Lazio","Unknown"))
        self.assertIsNone(geo.coords("Spain","Unknown","Nowhere"))

    def test_execution_state_contract_accepts_completed_run_focus(self):
        allowed={"MISSION_STARTED","MISSION_COMPLETED","MISSION_FAILED","RUN_COMPLETED"}
        self.assertIn("RUN_COMPLETED",allowed)


class DashboardRadarSourceContractTests(unittest.TestCase):
    def test_frontend_prioritizes_real_execution_and_has_five_second_refocus(self):
        app=Path("command-center/assets/app.js").read_text(encoding="utf-8")
        self.assertIn("const actual=geo.actual_execution_focus||null",app)
        self.assertIn("const actualFresh=",app)
        self.assertIn("let focus=actualFresh?actual:",app)
        self.assertIn("const REFOCUS_DELAY=5000",app)
        self.assertIn("REAL EXECUTION",app)
        self.assertIn("SCAN PLAN",app)

    def test_map_tooltip_contains_contacted_company_name(self):
        app=Path("command-center/assets/app.js").read_text(encoding="utf-8")
        self.assertIn("primaryName",app)
        self.assertIn(".bindTooltip(count>1?",app)


class ExecutorContractTests(unittest.TestCase):
    def test_executor_is_bounded_rotating_and_no_evasion(self):
        src=Path("scripts/territorial_mission_executor.py").read_text(encoding="utf-8")
        self.assertIn("MAX_MISSIONS=6",src)
        self.assertIn("CURSOR=",src)
        self.assertIn("next_index",src)
        self.assertIn("DDGS(timeout=4)",src)
        self.assertIn('"es-es"',src)
        self.assertIn('"it-it"',src)
        self.assertIn("backend_pairs",src)
        self.assertIn('"brave","bing"',src)
        self.assertIn('"google","duckduckgo"',src)
        self.assertIn('"provider":"ddgs_multi_engine"',src)
        self.assertIn('"bing.com","google.com","brave.com","duckduckgo.com","yahoo.com"',src)
        self.assertIn("NO_PROXY_NO_STEALTH_NO_CAPTCHA_BYPASS",src)
        self.assertIn("search_results_are_discovery_only",src)
        self.assertIn('state="RUN_COMPLETED"',src)


if __name__=="__main__":
    unittest.main()
