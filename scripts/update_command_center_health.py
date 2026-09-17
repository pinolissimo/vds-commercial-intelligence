#!/usr/bin/env python3
"""Compute Command Center health from provider observation + projection reconciliation.

Commercial event age is never a health signal. A quiet day may legitimately contain
zero events. Health instead requires a recent successful provider poll plus successful
projection reconciliation, preventing both false dashes and false zeroes.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
API=ROOT/'api'/'v1'
STATE=ROOT/'state'
MADRID=ZoneInfo('Europe/Madrid')
PROVIDER_OBSERVATION_MAX_AGE_HOURS=1.5

def load_path(path: Path)->dict:
    try:
        v=json.loads(path.read_text(encoding='utf-8'))
        return v if isinstance(v,dict) else {}
    except Exception:
        return {}

def load(name:str)->dict: return load_path(API/name)
def save(name:str,payload:dict)->None: (API/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def parse_dt(value):
    if not isinstance(value,str) or not value: return None
    try:
        if value.endswith('Z'): value=value[:-1]+'+00:00'
        dt=datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=MADRID)
    except ValueError: return None

def age_hours(value,now_utc):
    dt=parse_dt(value)
    if not dt: return None
    return max(0.0,(now_utc-dt.astimezone(timezone.utc)).total_seconds()/3600)

def main()->int:
    health,today,dashboard=load('health.json'),load('today.json'),load('dashboard.json')
    observation=load_path(STATE/'provider-observation.json')
    now=datetime.now(timezone.utc)
    reconciled_at=now.isoformat(timespec='seconds').replace('+00:00','Z')
    observed_at=observation.get('observed_at')
    observed_age=age_hours(observed_at,now)
    observation_fresh=observed_age is not None and observed_age<=PROVIDER_OBSERVATION_MAX_AGE_HOURS
    sent_observed=observation.get('sent_observed') is True
    inbox_observed=observation.get('inbox_observed') is True

    outbound_last=today.get('provider_live_overlay_updated_at') or dashboard.get('provider_live_overlay_updated_at') or (dashboard.get('provider_live_overlay') or {}).get('updated_at')
    inbound_last=today.get('provider_inbound_overlay_updated_at') or dashboard.get('provider_inbound_overlay_updated_at')
    outbound_sources=today.get('provider_live_sources',dashboard.get('provider_live_sources',0)) or 0
    inbound_sources=today.get('provider_inbound_sources',dashboard.get('provider_inbound_sources',0)) or 0

    projection_outbound_ok=outbound_sources>0
    projection_inbound_ok=inbound_sources>0
    outbound_ok=observation_fresh and sent_observed and projection_outbound_ok
    inbound_ok=observation_fresh and inbox_observed and projection_inbound_ok

    health.update({
      'schema_version':'2.1','reconciled_at':reconciled_at,
      'provider_observed_at':observed_at,'provider_observation_age_hours':round(observed_age,2) if observed_age is not None else None,
      'provider_observation_max_age_hours':PROVIDER_OBSERVATION_MAX_AGE_HOURS,'provider_observation_fresh':observation_fresh,
      'latest_provider_sent_uid':observation.get('latest_sent_uid'),'provider_live_overlay_updated_at':outbound_last,
      'provider_inbound_overlay_updated_at':inbound_last,'outbound_last_event_at':outbound_last,'inbound_last_event_at':inbound_last,
      'provider_live_sources':outbound_sources,'provider_inbound_sources':inbound_sources,
      'provider_live_pending_sources':today.get('provider_live_pending_sources',dashboard.get('provider_live_pending_sources',0)),
      'provider_inbound_pending_sources':today.get('provider_inbound_pending_sources',dashboard.get('provider_inbound_pending_sources',0)),
      'outbound_reconciled':outbound_ok,'inbound_reconciled':inbound_ok,'outbound_source_fresh':outbound_ok,'reply_source_fresh':inbound_ok,
      'provider_live_fresh':outbound_ok,'provider_inbound_fresh':inbound_ok})
    if outbound_ok and inbound_ok:
        health['status']='OK'; health['status_reason']='PROVIDER_OBSERVED_AND_PROJECTIONS_RECONCILED'
    elif not observation_fresh:
        health['status']='DEGRADED'; health['status_reason']='PROVIDER_OBSERVATION_STALE_OR_MISSING'
    elif not outbound_ok and not inbound_ok:
        health['status']='DEGRADED'; health['status_reason']='OUTBOUND_AND_INBOUND_RECONCILIATION_UNAVAILABLE'
    elif not outbound_ok:
        health['status']='DEGRADED'; health['status_reason']='OUTBOUND_RECONCILIATION_UNAVAILABLE'
    else:
        health['status']='DEGRADED'; health['status_reason']='INBOUND_RECONCILIATION_UNAVAILABLE'
    source_health={'schema_version':'2.1','reconciled_at':reconciled_at,'provider_observed_at':observed_at,
      'provider_observation_fresh':observation_fresh,'outbound_last_event_at':outbound_last,'inbound_last_event_at':inbound_last,
      'outbound_reconciled':outbound_ok,'inbound_reconciled':inbound_ok,'outbound_source_fresh':outbound_ok,'reply_source_fresh':inbound_ok}
    today['source_health']=dict(source_health); dashboard['source_health']=dict(source_health)
    save('health.json',health); save('today.json',today); save('dashboard.json',dashboard)
    print(json.dumps({'status':health['status'],'reason':health['status_reason'],**source_health}))
    return 0
if __name__=='__main__': raise SystemExit(main())
