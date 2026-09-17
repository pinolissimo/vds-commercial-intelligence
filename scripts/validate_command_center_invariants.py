#!/usr/bin/env python3
"""Fail closed when Command Center projections violate core invariants."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
API=ROOT/'api'/'v1'

def load(name):
    return json.loads((API/name).read_text(encoding='utf-8'))

def eid(x):
    uid=x.get('provider_uid')
    if isinstance(uid,int): return f'provider:{uid}'
    ext=x.get('external_id') or x.get('gmail_message_id')
    if ext: return f"{x.get('source','external')}:{ext}"
    return None

def main():
    today=load('today.json'); dash=load('dashboard.json'); outbound=load('outbound.json'); health=load('health.json')
    msgs=outbound.get('messages') or []
    ids=[eid(x) for x in msgs if eid(x)]
    assert len(ids)==len(set(ids)), 'duplicate outbound event identity'
    assert today.get('sent_count',0)>=today.get('first_contact_count',0)>=0
    assert (dash.get('today') or {}).get('sent')==today.get('sent_count'), 'dashboard/today sent drift'
    assert (dash.get('today') or {}).get('first_contacts_sent')==today.get('first_contact_count'), 'dashboard/today first-contact drift'
    assert (dash.get('headline') or {}).get('sent_today')==today.get('sent_count'), 'headline sent drift'
    assert outbound.get('today_count')==today.get('sent_count'), 'outbound/today count drift'
    assert outbound.get('today_first_contact_count')==today.get('first_contact_count'), 'outbound first-contact drift'
    for x in today.get('sent') or []:
        assert eid(x), 'today outbound without stable identity'
        assert x.get('state')=='VERIFIED_EMAIL_SENT', 'today contains non-verified outbound'
        assert x.get('count_as_successful_outbound') is not False, 'today contains excluded outbound'
    assert health.get('provider_observed_at'), 'missing provider observation timestamp'
    print(f"Invariant suite PASS: {len(ids)} unique outbound identities; {today.get('sent_count',0)} sent today")
if __name__=='__main__': main()
