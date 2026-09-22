"""FastF1 feasibility ingestion. No fitted degradation or causal strategy claims."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd


def quality_audit(frame):
    """Keep explicit exclusion reasons, without full-stint pace thresholds.

    This is retrospective quality control, not a guarantee flags were available
    online. Traffic is unmeasured and not excluded by these filters.
    """
    checks = {
        'missing_lap_or_age': frame[['LapTime', 'TyreLife', 'LapNumber', 'Stint', 'Driver', 'Time']].isna().any(axis=1),
        'nonpositive_lap_or_age': (frame['LapTime'] <= pd.Timedelta(0)) | (frame['TyreLife'] < 1),
        'pit_in_or_out': frame['PitInTime'].notna() | frame['PitOutTime'].notna(),
        'not_green': frame['TrackStatus'].ne('1'),
        'not_dry_compound': ~frame['Compound'].isin(['SOFT', 'MEDIUM', 'HARD']),
        'inaccurate': ~frame['IsAccurate'].eq(True),
        'generated': ~frame['FastF1Generated'].eq(False),
        'first_race_lap': frame['LapNumber'].le(1),
    }
    reasons = pd.DataFrame(checks, index=frame.index).fillna(True)
    result = frame.copy()
    result['eligible'] = ~reasons.any(axis=1)
    result['exclusion_reasons'] = reasons.apply(lambda r: '|'.join(r.index[r]), axis=1)
    return result, {name: int(mask.sum()) for name, mask in reasons.items()}


def main():
    import argparse
    import fastf1
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument('--selection', default='research/pilot-selection.json')
    args = parser.parse_args()
    selection = json.loads((root/args.selection).read_text())
    event_id = f"{selection['year']}-{selection['event'].lower().replace(' ', '-')}"
    cache, raw, processed = (root/'data'/name for name in ('cache', 'raw', 'processed'))
    for path in (cache, raw, processed):
        path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache))
    session = fastf1.get_session(selection['year'], selection['event'], selection['session'])
    session.load(laps=True, telemetry=False, weather=True, messages=False)
    columns = ['Driver', 'LapNumber', 'Stint', 'LapTime', 'Time', 'LapStartTime',
               'Compound', 'TyreLife', 'FreshTyre', 'PitInTime', 'PitOutTime',
               'TrackStatus', 'IsAccurate', 'FastF1Generated']
    frame = pd.DataFrame(session.laps)[columns].copy()
    if frame.empty:
        raise RuntimeError('FastF1 returned no laps; no successful manifest written')
    frame.to_csv(raw/f'{event_id}-laps.csv', index=False)
    pd.DataFrame(session.weather_data).to_csv(raw/f'{event_id}-weather.csv', index=False)
    audited, reasons = quality_audit(frame)
    audited['lap_seconds'] = audited['LapTime'].dt.total_seconds()
    audited['lap_end_session_seconds'] = audited['Time'].dt.total_seconds()
    # FastF1 TyreLife counts the lap just completed, whereas our synthetic age
    # indexes the tyre at the start of the lap. Keep both explicit.
    audited['tyre_age_start'] = audited['TyreLife']-1
    audited.sort_values(['lap_end_session_seconds', 'Driver'], inplace=True)
    audited.to_csv(processed/f'{event_id}-audited.csv', index=False)
    kept = audited[audited['eligible']]
    stints = []
    for (driver, stint), group in kept.groupby(['Driver', 'Stint'], sort=True):
        stints.append(dict(driver=driver, stint=int(stint), compound=str(group['Compound'].iloc[0]),
                           eligible_laps=len(group), first_lap=int(group['LapNumber'].min()),
                           last_lap=int(group['LapNumber'].max()),
                           median_lap_seconds=float(group['lap_seconds'].median())))
    # Display a driver deterministically, not whichever makes the best story.
    display_driver = sorted(kept['Driver'].unique())[0] if len(kept) else None
    display = kept[kept['Driver'] == display_driver]
    points = [dict(lap=int(r.LapNumber), seconds=float(r.lap_seconds),
                   stint=int(r.Stint), compound=r.Compound, age=float(r.tyre_age_start))
              for r in display.itertuples()]
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = dict(selection=selection, retrieved_utc=datetime.now(timezone.utc).isoformat(),
                    fastf1_version=fastf1.__version__, source='FastF1 / F1 timing feeds',
                    raw_sha256=digest(raw/f'{event_id}-laps.csv'),
                    processed_sha256=digest(processed/f'{event_id}-audited.csv'),
                    total_laps=len(frame), eligible_laps=len(kept),
                    drivers=int(frame['Driver'].nunique()), eligible_stints=len(stints),
                    exclusion_counts_overlapping=reasons, stints=stints,
                    display_driver=display_driver, display_laps=points,
                    limitations=['Retrospective quality flags; as-of availability not established',
                                 'Traffic, fuel load, track evolution and warmup not estimated',
                                 'No causal strategy evaluation or fitted degradation',
                                 'Raw source data remains local; redistribution rights not assessed'])
    manifest_name = 'historical-pilot.json' if event_id == '2024-bahrain' else f'{event_id}-manifest.json'
    (root/'results'/manifest_name).write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('stints', 'display_laps')}, indent=2))


if __name__ == '__main__':
    main()
