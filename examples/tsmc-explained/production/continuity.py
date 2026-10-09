"""Articulation helpers and short-window diagnostics, independent of genre presets.

Use connected bass only when the arrangement calls for legato. Intentional rests
remain an artistic choice; micro-dynamics measurements are not listening tests.
"""
import itertools
import math
import numpy as np
import instruments as ins


def tail_end(harmony, pitch, gate_end, desired_end):
    """Allow natural release across compatible harmony, not arbitrary new chords."""
    end = desired_end
    for chord in harmony:
        if chord['start'] < desired_end and chord['end'] > gate_end + 1e-7:
            pcs = chord['pcs'] | {chord['root'] % 12}
            if pitch % 12 not in pcs:
                end = min(end, max(gate_end, chord['start']))
    return end


def voice_lead(voices, previous=None):
    """Keep pitch classes, avoid adjacent semitones, and minimize voice movement."""
    choices = [[n for n in range(50, 77) if n % 12 == pc] for pc in sorted({n % 12 for n in voices})]
    preferred = previous or sorted(voices)
    candidates = set(tuple(sorted(notes)) for notes in itertools.product(*choices))
    def cost(notes):
        movement = sum(min(abs(n-p) for p in preferred) for n in notes)
        movement += sum(min(abs(p-n) for n in notes) for p in preferred)
        crowding = sum(18 for a,b in zip(notes, notes[1:]) if b-a < 2)
        return movement + crowding + .08 * (notes[-1]-notes[0]), notes
    return list(min(candidates, key=cost))


def sustained_pad(score, gain=.12):
    """Tie shared notes instead of restarting the entire pad at each bar."""
    score.stems['pad'].fill(0)
    score.events[:] = [e for e in score.events if e['stem'] != 'pad']
    phrases, live, previous = [], {}, None
    for chord in score.harmony:
        notes = voice_lead(chord['voices'], previous)
        chord['pad_voices'] = notes
        previous = notes
        for pitch in list(live):
            if pitch not in notes:
                phrases.append(live.pop(pitch))
        for pitch in notes:
            if pitch in live:
                live[pitch]['end'] = chord['end']
            else:
                live[pitch] = {'pitch':pitch, 'start':chord['start'], 'end':chord['end']}
    phrases.extend(live.values())
    for phrase in phrases:
        start, end, pitch = phrase['start'], phrase['end'], phrase['pitch']
        length = end-start
        t = np.arange(round(length*score.sr))/score.sr + start
        sound = np.zeros((len(t),2), np.float64)
        for c,cents in enumerate([-1.5,1.5]):
            f = ins.hz(pitch)*2**(cents/1200)
            for h,w in [(1,.50),(2,.13),(3,.035)]:
                sound[:,c] += w*np.sin(2*math.pi*h*f*t + h*.17)
            sound[:,c] = ins.soften(sound[:,c], min(.045,length/4), min(.065,length/4))
        sound *= (.96+.04*np.sin(2*math.pi*.17*t))[:,None]
        score.note('pad',start,length,pitch,gain,sound=sound,boundary=score.duration,velocity=55)


def connected_bass(score, identity):
    """Tied note gates and a phase-continuous mono oscillator; no per-note reset."""
    original = sorted([e for e in score.events if e['stem']=='bass'], key=lambda e:e['time'])
    score.events[:] = [e for e in score.events if e['stem']!='bass' and not (identity=='drum-and-bass' and e['stem']=='chords')]
    frequency = np.full(score.n, ins.hz(score.harmony[0]['root']), np.float64)
    amplitude = np.zeros(score.n, np.float32)
    gain = {'future-bass':.39,'drum-and-bass':.38,'uk-garage':.36,'dub-techno':.32}.get(identity,.36)
    for chord in score.harmony:
        if chord['role'] not in ('groove','build','drop'):
            continue
        notes = [dict(e) for e in original if chord['start']-1e-7 <= e['time'] < chord['end']-1e-7]
        if not notes or notes[0]['time'] > chord['start']+1e-7:
            notes.insert(0, {'time':chord['start'],'note':chord['root'],'velocity':75})
        for i,event in enumerate(notes):
            start = event['time']
            end = notes[i+1]['time'] if i+1 < len(notes) else chord['end']
            k, j = round(start*score.sr), round(end*score.sr)
            amplitude[k:j] = gain*(.88+.12*np.exp(-np.arange(j-k)/score.sr*3))
            recorded = {'stem':'bass','time':start,'duration':end-start,'sounding_duration':end-start,
                        'note':event['note'],'velocity':event['velocity'],'articulation':'legato'}
            score.events.append(recorded)
            if identity=='drum-and-bass':
                score.events.append({**recorded,'stem':'chords'})
    bass_events=sorted([e for e in score.events if e['stem']=='bass'],key=lambda e:e['time'])
    for i,event in enumerate(bass_events):
        k=round(event['time']*score.sr)
        j=round(bass_events[i+1]['time']*score.sr) if i+1<len(bass_events) else score.n
        frequency[k:j]=ins.hz(event['note'])
    # Smooth gain on entry/exit without dipping between tied notes.
    from scipy.signal import lfilter
    pole = math.exp(-1/(score.sr*.012))
    amplitude = lfilter([1-pole],[1,-pole],amplitude).astype(np.float32)
    phase = 2*math.pi*np.cumsum(frequency)/score.sr
    mono = (np.sin(phase)+.10*np.sin(phase*2))*amplitude*.67
    score.stems['bass'] = np.column_stack([mono,mono]).astype(np.float32)/math.sqrt(2)
    if identity=='drum-and-bass':
        t=np.arange(score.n)/score.sr
        mid=sum(np.sin(phase*h*2**(cents/1200))*(.12/h)/np.sqrt(1+(h*frequency/1600)**4)
                for cents in [-6,6] for h in range(2,10))
        mid=np.tanh(mid*1.7)*(.90+.10*np.sin(2*math.pi*1.1*t))*amplitude
        score.stems['chords']=np.column_stack([mid,mid]).astype(np.float32)


def room(score, wet=.10):
    """Low-level filtered early reflections, leaving mono bass and kick dry."""
    source=sum(score.stems[name] for name in ['keys','pad','chords','lead'])
    source=ins.filt(ins.filt(source,260),4200,'lowpass')
    reflections=np.zeros_like(source)
    times=[.029,.043,.061,.083,.113,.157,.211,.277,.359,.449,.557]
    for i,seconds in enumerate(times):
        k=round(seconds*score.sr)
        if k>=score.n: continue
        reflections[k:] += source[:-k,::(-1 if i%2 else 1)]*(wet*math.exp(-seconds*5)/3)
    score.stems['effects'] += reflections


def micro_dynamics(sound, sr, sections):
    """10ms windows expose inter-beat holes hidden by a one-second RMS check."""
    width=max(1,round(sr*.010))
    count=len(sound)//width
    rms=np.sqrt(np.mean(np.asarray(sound[:count*width],np.float64).reshape(count,width,-1)**2,axis=(1,2)))
    result=[]
    for section in sections:
        if section['role'] not in ('groove','build','drop'): continue
        start=int((section['start']+.25)*sr/width)
        end=min(count,int((section['end']-.20)*sr/width))
        values=rms[start:end]
        if not len(values): continue
        q10,q95=np.quantile(values,[.1,.95])
        low=values < max(q95*.02,1e-8)
        run=longest=0
        for value in low:
            run=run+1 if value else 0
            longest=max(longest,run)
        result.append({'start':section['start'],'end':section['end'],'role':section['role'],
                       'p10_to_p95_db':round(float(20*np.log10(max(q10,1e-12)/max(q95,1e-12))),2),
                       'longest_deep_trough_ms':round(longest*width/sr*1000),
                       'deep_trough_fraction':round(float(np.mean(low)),5)})
    return {'window_ms':10,'deep_trough_threshold_db_below_p95':round(20*math.log10(.02),2),
            'regions':result,'interpretation':'Review with arrangement intent. These values do not certify listening quality.'}


def apply_continuity(score):
    """Arrangement changes are opt-in; retaining release never requires a new bed."""
    options = score.cfg['music'].get('continuity', {})
    if not isinstance(options, dict):
        raise ValueError('music.continuity must be an object')
    tie = options.get('tie_pad', False)
    wet = options.get('room_wet', 0.)
    if not isinstance(tie, bool):
        raise ValueError('music.continuity.tie_pad must be true or false')
    if isinstance(wet, bool) or not isinstance(wet, (int, float)) or not math.isfinite(wet) or not 0 <= wet <= .5:
        raise ValueError('music.continuity.room_wet must be within 0–0.5')
    if tie:
        sustained_pad(score, .11)
    if wet:
        room(score, wet)
