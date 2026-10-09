"""A conservative simultaneous-interval profile, separate from key membership."""

DISSONANT_CLASSES = {1: 'minor second / major seventh',
                    2: 'major second / minor seventh',
                    6: 'tritone',
                    10: 'minor seventh / major second',
                    11: 'major seventh / minor second'}


def overlapping_dissonances(events):
    """Inspect simultaneous pitched parts, including tracked synthesis releases.

    This symbolic check cannot infer untracked sample/FX tails, loudness, detune
    or perceived roughness. Perfect fourths inside triad inversions are allowed.
    """
    pitched = sorted((event for event in events
                      if event.get('stem') != 'drums' and 'note' in event),
                     key=lambda event: event['time'])
    active, conflicts = [], []
    for event in pitched:
        start = event['time']
        end = start + event.get('sounding_duration', event['duration'])
        active = [(other, stop) for other, stop in active if stop > start + 1/48000]
        for other, stop in active:
            overlap_end = min(end, stop)
            if overlap_end <= start + 1/48000:
                continue
            distance = abs(event['note'] - other['note'])
            interval = distance % 12
            if interval in DISSONANT_CLASSES:
                conflicts.append({'start': start, 'end': overlap_end,
                    'stems': [other['stem'], event['stem']],
                    'notes': [other['note'], event['note']],
                    'semitones': distance, 'interval_class': interval,
                    'interval': DISSONANT_CLASSES[interval]})
        active.append((event, end))
    return conflicts


def check_profile(events, music):
    profile = music.get('harmonic_profile', 'consonant')
    if profile not in ('consonant', 'intentional-tension'):
        raise ValueError('music.harmonic_profile must be consonant or intentional-tension')
    conflicts = overlapping_dissonances(events)
    if profile == 'consonant' and conflicts:
        first = conflicts[0]
        raise ValueError(f"Consonant profile found {first['interval']} at {first['start']:.3f}s "
                         f"between {first['notes']}; revise the voicing, overlap or phrase.")
    return {'profile': profile, 'tracked_overlap_conflicts': conflicts,
            'tension_intent': music.get('tension_intent'),
            'limits': 'Symbolic intervals do not certify comfortable timbre. '
                      'Sampled release and FX tails still require audio review.'}
