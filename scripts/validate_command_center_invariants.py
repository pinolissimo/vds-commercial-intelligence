#!/usr/bin/env python3
"""Fail closed when Command Center projections violate core invariants."""
import json
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
API=ROOT/'api'/'v1'
MADRID=ZoneInfo('Europe/Madrid')

def load(name):
    return json.loads((API/name).read_text(encoding='utf-8'))

def eid(x):
    uid=x.get('provider_uid')
    if isinstance(uid,int): return f'provider:{uid}'
    ext=x.get('external_id') or x.get('gmail_message_id')
    if ext: return f"{x.get('source','external')}:{ext}"
    return None

def parse_dt(value):
    if not isinstance(value,str) or not value: return None
    try:
        if value.endswith('Z'): value=value[:-1]+'+00:00'
        dt=datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=MADRID)
    except ValueError:
        return None

def in_active_window(x,date_str):
    dt=parse_dt(x.get('sent_at_local') or x.get('sent_at'))
    if not dt: return False
    local=dt.astimezone(MADRID)
    return str(local.date())==date_str and time(9,0)<=local.time().replace(tzinfo=None)<time(19,0)

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

    date_str=today.get('date')
    active=[x for x in today.get('sent') or [] if in_active_window(x,date_str)]
    active_first=[x for x in active if x.get('action_type','FIRST_CONTACT')=='FIRST_CONTACT']
    elapsed=float((dash.get('today') or {}).get('active_window_elapsed_hours') or 0)
    expected_rate=round(len(active)/elapsed,2) if elapsed else 0.0
    expected_first_rate=round(len(active_first)/elapsed,2) if elapsed else 0.0
    assert today.get('active_window_sent_count')==len(active), 'active-window sent count drift'
    assert today.get('active_window_first_contact_count')==len(active_first), 'active-window first-contact count drift'
    assert today.get('messages_per_active_hour')==expected_rate, 'throughput includes events outside 09:00-19:00'
    assert today.get('first_contacts_per_active_hour')==expected_first_rate, 'first-contact throughput includes events outside 09:00-19:00'
    assert (dash.get('today') or {}).get('messages_per_active_hour')==expected_rate, 'dashboard throughput drift'
    assert outbound.get('messages_per_active_hour')==expected_rate, 'outbound throughput drift'

    assert health.get('provider_observed_at'), 'missing provider observation timestamp'
    print(f"Invariant suite PASS: {len(ids)} unique outbound identities; {today.get('sent_count',0)} sent today; {len(active)} inside active window")
if __name__=='__main__': main()