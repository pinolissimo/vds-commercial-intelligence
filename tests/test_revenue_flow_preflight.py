import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
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


    def test_fresh_provider_mirror_is_accepted_and_searchable(self):
        outbound = {"events": [{
            "provider_uid": 736,
            "state": "VERIFIED_EMAIL_SENT",
            "recipient": "hello@example.com",
            "canonical_identity_key": "org:example.com",
        }]}
        observation = {
            "sent_observed": True,
            "inbox_observed": True,
            "latest_sent_uid": 736,
            "observed_at": "2026-10-04T14:34:49Z",
        }
        status = {
            "status": "OK",
            "auth_status": "VALID",
            "latest_sent_uid": 736,
            "checked_at": "2026-10-04T14:34:49Z",
        }
        health = rf.provider_snapshot_health(
            outbound, observation, status,
            now=datetime(2026, 10, 4, 14, 40, tzinfo=timezone.utc),
        )
        self.assertEqual("HEALTHY", health["status"])
        matches = rf.provider_sent_matches(
            outbound,
            recipient="hello@example.com",
            canonical_organization_key="org:example.com",
            corporate_domain="example.com",
        )
        self.assertTrue(matches["exact_recipient_match"])
        self.assertTrue(matches["organization_or_domain_match"])
        self.assertEqual([736], matches["exact_provider_uids"])

    def test_stale_provider_mirror_fails_closed(self):
        outbound = {"events": [{
            "provider_uid": 736,
            "state": "VERIFIED_EMAIL_SENT",
            "recipient": "hello@example.com",
            "canonical_identity_key": "org:example.com",
        }]}
        observation = {
            "sent_observed": True,
            "inbox_observed": True,
            "latest_sent_uid": 736,
            "observed_at": "2026-10-04T14:00:00Z",
        }
        status = {
            "status": "OK",
            "auth_status": "VALID",
            "latest_sent_uid": 736,
            "checked_at": "2026-10-04T14:00:00Z",
        }
        with self.assertRaises(rf.PreflightError):
            rf.provider_snapshot_health(
                outbound, observation, status,
                now=datetime(2026, 10, 4, 14, 40, tzinfo=timezone.utc),
            )

    def test_provider_watermark_mismatch_fails_closed(self):
        outbound = {"events": [{
            "provider_uid": 735,
            "state": "VERIFIED_EMAIL_SENT",
            "recipient": "hello@example.com",
            "canonical_identity_key": "org:example.com",
        }]}
        observation = {
            "sent_observed": True,
            "inbox_observed": True,
            "latest_sent_uid": 736,
            "observed_at": "2026-10-04T14:34:49Z",
        }
        status = {
            "status": "OK",
            "auth_status": "VALID",
            "latest_sent_uid": 736,
            "checked_at": "2026-10-04T14:34:49Z",
        }
        with self.assertRaises(rf.PreflightError):
            rf.provider_snapshot_health(
                outbound, observation, status,
                now=datetime(2026, 10, 4, 14, 40, tzinfo=timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
