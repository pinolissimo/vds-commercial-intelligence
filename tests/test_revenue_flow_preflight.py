import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "revenue_flow_preflight.py"
spec = importlib.util.spec_from_file_location("revenue_flow_preflight", SCRIPT)
rf = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(rf)


class RevenueFlowPreflightTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "schema_version": "1.0",
            "event_type": "VERIFIED_EMAIL_SENT",
            "action_type": "FIRST_CONTACT",
            "provider": "HOSTINGER",
            "provider_uid": 295,
            "sent_at": "2026-09-05T10:09:09Z",
            "canonical_identity_key": "org:witapp.it",
            "organization": "Witapp SRL",
            "recipient": "candidature@witapp.it",
            "subject": "Candidatura — Web Specialist",
            "workstream": "VDS_LINKEDIN_JOB_HUNTER",
            "attachments": 0,
            "bcc_owner": True,
            "state": "VERIFIED_EMAIL_SENT",
        }

    def test_repair_adds_missing_identity_to_all_three_derived_caches(self):
        suppression = {"scan": {"highest_uid_seen": 294}, "contacted_domains": []}
        sent_index = {"messages": []}
        org_index = {"contacted": []}

        suppression, sent_index, org_index, changes = rf.reconcile(
            [self.event], suppression, sent_index, org_index
        )

        self.assertIn("witapp.it", suppression["contacted_domains"])
        self.assertEqual(295, suppression["scan"]["highest_uid_seen"])
        self.assertEqual([295], [m["provider_uid"] for m in sent_index["messages"]])
        self.assertEqual(
            ["org:witapp.it"],
            [o["canonical_identity_key"] for o in org_index["contacted"]],
        )
        self.assertEqual(["witapp.it"], changes["suppression_domains_added"])
        self.assertEqual([295], changes["sent_uids_added"])
        self.assertEqual(["org:witapp.it"], changes["organization_keys_added"])

    def test_repair_is_idempotent(self):
        suppression = {"scan": {"highest_uid_seen": 294}, "contacted_domains": []}
        sent_index = {"messages": []}
        org_index = {"contacted": []}

        suppression, sent_index, org_index, _ = rf.reconcile(
            [self.event], suppression, sent_index, org_index
        )
        _, _, _, second_changes = rf.reconcile(
            [self.event], suppression, sent_index, org_index
        )

        self.assertEqual([], second_changes["suppression_domains_added"])
        self.assertEqual([], second_changes["sent_uids_added"])
        self.assertEqual([], second_changes["organization_keys_added"])

    def test_only_verified_first_contacts_enter_repair_source(self):
        continuation = dict(self.event, provider_uid=296, action_type="REPLY_CONTINUATION")
        internal = dict(self.event, provider_uid=297, action_type="INTERNAL_NOTIFICATION")
        contacts = rf.durable_first_contacts([self.event, continuation, internal])
        self.assertEqual([295], [x["provider_uid"] for x in contacts])

    def test_nonzero_discovery_file_is_not_treated_as_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "discovery.json"
            path.write_text(json.dumps({"signals": [{"id": 1}, {"id": 2}]}), encoding="utf-8")
            health = rf.discovery_health(path)
            self.assertTrue(health["json_valid"])
            self.assertGreater(health["byte_size"], 0)
            self.assertEqual(2, health["signal_count"])

    def test_zero_byte_discovery_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "discovery.json"
            path.write_bytes(b"")
            with self.assertRaises(rf.PreflightError):
                rf.discovery_health(path)


if __name__ == "__main__":
    unittest.main()
