"""Explanation-quality transfer plots from existing evaluated answers only."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/roboboat-transfer-accuracy-2026-10-02'


def capsule_entry(p):
    key = str(Path(p).resolve().relative_to(ROOT))
    capsule = json.loads((OUT / 'evaluated-source-capsule.json').read_text())
    entry = capsule['sources'][key]
    canonical = json.dumps(entry['value'], sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(canonical).hexdigest() == entry['canonical_projection_sha256']
    return entry


def bind(p):
    p = Path(p).resolve()
    if not p.exists():
        return capsule_entry(p)['original_binding']
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def read(p):
    if not Path(p).exists():
        return capsule_entry(p)['value']
    return json.loads(Path(p).read_text())


def save(fig, name):
    fig.get_layout_engine().set(rect=(0, .07, 1, .93))
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=200, metadata={'Date': None} if ext == 'svg' else {})


def cards(ax, quotes, title):
    from matplotlib.patches import FancyBboxPatch
    ax.axis('off'); ax.set_title(title, loc='left', fontsize=11)
    for i, (label, quote) in enumerate(quotes):
        y = .71 - i * .30
        ax.add_patch(FancyBboxPatch((.02, y), .96, .26, boxstyle='round,pad=0.01',
                    facecolor=('#edf2f5', '#e4eef5', '#dceee8')[i], edgecolor='#bdcbd1', transform=ax.transAxes))
        ax.text(.05, y + .20, label, weight='bold', fontsize=10, transform=ax.transAxes)
        ax.text(.05, y + .15, textwrap.fill('“' + quote + '”', 67), va='top',
                fontsize=9, linespacing=1.25, transform=ax.transAxes)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none',
                         'svg.hashsalt': 'marine-transfer-accuracy-v1'})
    OUT.mkdir(exist_ok=True)
    old_path = ROOT / 'artifacts/roboboat-terminal-v3/development-results-final.json'
    contact_path = ROOT / 'artifacts/roboboat-contact-policy-support-v2/development-results-v2.json'
    old = read(old_path); contact = read(contact_path)
    old_rows = [r for r in old['rows'] if r['method'] == 'B4']
    rows = [r for r in contact['rows'] if r['method'] == 'B4']
    sources = [bind(old_path), bind(contact_path), bind(__file__)]
    finals = []
    for r in old_rows:
        candidates = [ROOT / f'artifacts/roboboat-terminal-{v}/comparison/annotations/{r["opaque_response_id"]}/final.json'
                      for v in ('v1', 'v3')]
        keys = json.loads((OUT / 'evaluated-source-capsule.json').read_text())['sources']
        final = next(p for p in candidates if p.exists() or str(p.relative_to(ROOT)) in keys)
        assert bind(final)['sha256'] == r['final_sha256']
        sources.append(bind(final)); finals.append(read(final))
    for r in rows:
        answer = ROOT / r['answer_path']
        final = ROOT / f'artifacts/roboboat-contact-policy-support-v2/annotations/{r["support_packet_id"]}/final.json'
        assert bind(answer)['sha256'] == r['answer_file_sha256']
        assert bind(final)['sha256'] == r['final_sha256']
        sources.extend([bind(answer), bind(final)])
        assert r['pass_A'] == r['pass_B'] == r['final']
    summary = {
        'schema': 'roboboat-explanation-transfer-results/v1',
        'method_scope': 'Historical B4: deterministic marine evidence-contract renderer; not a new scored full-framework/LLM result.',
        'failure_bank': {'recordings': len({r['batch'] for r in old_rows}), 'approach_clusters': 3,
                         'answers': len(old_rows), 'successful_answers': sum(r['answer_success'] for r in old_rows),
                         'all_claims_supported_answers': sum(r['all_claims_supported'] for r in old_rows),
                         'required_units_covered': sum(r['required_units_covered'] for r in old_rows),
                         'required_units_total': sum(r['required_units_n'] for r in old_rows),
                         'limitations_preserved_answers': sum(r['limitations_preserved'] for r in old_rows),
                         'annotation_scope': 'Original project sentence-level inventory; later incomplete atomic reassessment not substituted.'},
        'contact_replay_bank': {'recordings': len({r['episode'] for r in rows}), 'answers': len(rows),
                               'successful_answers': sum(r['final']['strict_extended_success'] for r in rows),
                               'supported_reviewed_claim_instances': sum(r['final']['claim_label_counts'].get('SUPPORTED_BY_VISIBLE_EVIDENCE', 0) for r in rows),
                               'reviewed_claim_instances': sum(r['final']['claims_n'] for r in rows),
                               'required_units_covered': sum(r['final']['common_units_communicated'] for r in rows),
                               'required_units_total': sum(r['final']['common_units_n'] for r in rows),
                               'positive_sampled_compliance_communicated': sum(r['final']['partial_compliance_communicated'] is True for r in rows),
                               'positive_sampled_compliance_answerable': sum(r['partial_information_answerable'] for r in rows),
                               'limits_preserved_answers': sum(all(r['final']['whole_answer_limits_preserved'].values()) for r in rows)},
        'scope': 'Separate inspected development banks, all B4 rows retained. Claim/unit/evidence-level counts add no independent configuration N. Model-assessed, not human validated. No matched land-marine performance estimate or superiority inference.',
        'sources': sources}
    assert summary['failure_bank']['answers'] == 15 and summary['failure_bank']['required_units_covered'] == 60
    assert summary['contact_replay_bank']['reviewed_claim_instances'] == 116

    # An explanation-quality matrix, rather than a navigation-success chart.
    fig, ax = plt.subplots(figsize=(10, 3.8), layout='constrained')
    ax.set(xlim=(-.05, 3), ylim=(-.15, 2.45)); ax.axis('off')
    ax.set_title('Marine explanation accuracy across removal-only evidence levels', loc='left', fontsize=13)
    from matplotlib.patches import FancyBboxPatch
    for j, label in enumerate(('L0: status only', 'L1: adjacent measurement', 'L2: sampled interval')):
        ax.text(j + .5, 2.12, label, ha='center', fontsize=10, weight='bold')
    for i, episode in enumerate(('boat-terminal-settling-001', 'boat-terminal-settling-002')):
        for j in range(3):
            row = next(r for r in rows if r['episode'] == episode and r['level'] == f'L{j}')
            result = row['final']; n = result['claims_n']; y = 1.05 - i
            ax.add_patch(FancyBboxPatch((j + .04, y), .92, .82, boxstyle='round,pad=0.01',
                                       facecolor='#dceee8', edgecolor='#b2c9be'))
            ax.text(j + .50, y + .60, ('Known route' if i == 0 else 'Direct route'), ha='center', fontsize=9)
            ax.text(j + .50, y + .36, f'{n}/{n} reviewed claims supported', ha='center', fontsize=10, weight='bold')
            ax.text(j + .50, y + .14, '4/4 required units; limits preserved', ha='center', fontsize=9)
    fig.text(.04, .015, 'Six inspected answers; two existing recordings. Automated support review, not population accuracy or a comparison effect.', fontsize=9)
    save(fig, 'marine-explanation-quality'); plt.close(fig)

    # Judged positive example: the explanation retains unknown full completion
    # while reporting useful observed compliance. The late crossing is out of dwell.
    episode = 'boat-terminal-settling-001'
    chosen = [next(r for r in rows if r['episode'] == episode and r['level'] == f'L{i}') for i in range(3)]
    batch = ROOT / 'artifacts/roboboat-contact-policy-comparison-v2/batches' / chosen[0]['response_id'].rsplit('-L', 1)[0]
    packet_path = batch / 'method_packets/L2.json'; packet = read(packet_path)
    fixture_path = ROOT / f'artifacts/roboboat-terminal-settling-v1/captures/{episode}/fixture-summary.json'
    fixture = read(fixture_path)
    raw = [r for r in fixture['trajectory'] if r['phase'] == 'post_result']
    assert len(raw) == len(packet['post_result'])
    assert all(all(a[k] == b[k] for k in ('x', 'y', 'yaw', 'simSeconds')) for a, b in zip(raw, packet['post_result']))
    task = packet['task']; times = [r['simSeconds'] for r in raw]; start = times[0]; end = start + task['dwell_s']
    errors = [math.dist((r['x'], r['y']), (task['goal']['x'], task['goal']['y'])) for r in raw]
    speeds = [math.hypot(r['bodySurge'], r['bodySway']) for r in raw]
    in_dwell = [i for i, t in enumerate(times) if t <= end]
    assert len(in_dwell) == 251 and max(errors[i] for i in in_dwell) < .4 and max(speeds[i] for i in in_dwell) < .05
    crossing = next(i for i, e in enumerate(errors) if e > .4)
    assert times[crossing] > end
    answer_texts = [read(ROOT / r['answer_path'])['answer'] for r in chosen]
    quotes = [
        ('L0: calibrated withholding', 'Physical docking completion is unestablished by the available evidence.'),
        ('L1: supported specificity', 'The result-adjacent observation had position error 0.1893 m and measured speed 0.0146 m/s.'),
        ('L2: useful positive information', 'All 251 observed samples in the declared 248.420270–253.420270 s dwell met the position, heading, translational-speed, yaw-rate and hull-containment requirements (maximum sample gap 0.0200 s).')]
    assert all(q in text for (_, q), text in zip(quotes, answer_texts))
    fig = plt.figure(figsize=(11.8, 5.1), layout='constrained'); gs = fig.add_gridspec(2, 2, width_ratios=(1, 1.3))
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[1, 0]); text_ax = fig.add_subplot(gs[:, 1])
    for ax, vals, bound, ylabel in ((ax1, errors, .4, 'Position error (m)'), (ax2, speeds, .05, 'Measured speed (m/s)')):
        ax.axvspan(0, 5, color='#dceaf4'); ax.plot([t - start for t in times], vals, color='#175c82', linewidth=1.5)
        ax.axhline(bound, color='#a63732', linestyle='--', linewidth=1)
        ax.set_ylabel(ylabel); ax.spines[['top', 'right']].set_visible(False)
    ax1.set_title('Observed compliance is useful evidence', loc='left', fontsize=11)
    ax1.scatter(times[crossing] - start, errors[crossing], color='#a63732', s=25, zorder=4)
    ax1.annotate('Later crossing outside dwell', (times[crossing] - start, errors[crossing]),
                 xytext=(.12, .9), textcoords='axes fraction', fontsize=8,
                 arrowprops={'arrowstyle': '->', 'color': '#a63732'})
    ax2.set_xlabel('Simulator seconds after first post-result observation')
    cards(text_ax, quotes, 'Actual evaluated answer excerpts')
    fig.text(.03, .005, 'Shading: fixed five-second dwell. Full completion stays unknown because contact is unavailable; samples do not prove continuous compliance.', fontsize=8)
    save(fig, 'marine-positive-evidence-ladder'); plt.close(fig)
    sources.extend([bind(packet_path), bind(fixture_path)])

    # Judged negative example: a within-dwell witness changes the answer, not cause.
    case = 'boat-terminal-pilot-004-render-successor-v3'
    base = ROOT / 'artifacts/roboboat-terminal-v3'
    packet_path = base / f'batches/{case}/method_packets/L2.json'; packet = read(packet_path)
    fixture_path = base / f'captures/{case}/fixture-summary.json'; fixture = read(fixture_path)
    raw = [r for r in fixture['trajectory'] if r['phase'] == 'post_result']; times = [r['simSeconds'] for r in raw]
    assert len(raw) == len(packet['post_result'])
    assert all(all(a[k] == b[k] for k in ('x', 'y', 'yaw', 'simSeconds')) for a, b in zip(raw, packet['post_result']))
    rates = [abs(r['bodyYawRate']) for r in raw]; start = times[0]; bound = packet['task']['yaw_rate_tolerance_radps']
    first = next(i for i, v in enumerate(rates) if v > bound and times[i] <= start + 5)
    texts = [read(base / f'comparison/{case}/L{i}/B4.json')['answer'] for i in range(3)]
    quotes = [
        ('L0: reported status is insufficient', 'Physical docking completion is unestablished by the available evidence.'),
        ('L1: accurate adjacent observation', 'The result-adjacent observation had position error 0.0945 m and measured speed 0.0175 m/s.'),
        ('L2: supported violation diagnosis', 'The specified docking dwell failed: at observed time 189.103 s, measured absolute yaw rate was 0.0516 rad/s, exceeding the 0.0500 rad/s bound.')]
    assert all(q in text for (_, q), text in zip(quotes, texts))
    assert all(r['answer_success'] and r['limitations_preserved'] for r in old_rows if r['batch'] == case)
    fig = plt.figure(figsize=(11.8, 4.4), layout='constrained'); gs = fig.add_gridspec(1, 2, width_ratios=(1, 1.3))
    ax = fig.add_subplot(gs[0]); text_ax = fig.add_subplot(gs[1])
    ax.axvspan(0, 5, color='#dceaf4', label='Declared dwell')
    ax.plot([t - start for t in times], rates, color='#175c82', linewidth=1.5, label='Measured yaw rate')
    ax.axhline(bound, color='#a63732', linestyle='--', linewidth=1, label='Requirement (0.05 rad/s)')
    ax.scatter(times[first] - start, rates[first], color='#a63732', s=35, zorder=4)
    ax.annotate('First within-dwell violation', (times[first] - start, rates[first]),
                xytext=(.25, .86), textcoords='axes fraction', fontsize=8,
                arrowprops={'arrowstyle': '->', 'color': '#a63732'})
    ax.set(xlabel='Simulator seconds after first post-result observation', ylabel='Absolute measured yaw rate (rad/s)',
           title='A witness supports a stronger explanation')
    ax.legend(fontsize=8, frameon=False, loc='upper right', bbox_to_anchor=(1, .79)); ax.spines[['top', 'right']].set_visible(False)
    cards(text_ax, quotes, 'Actual evaluated answer excerpts')
    fig.text(.03, .005, 'Same physical record at L0–L2. The explanation diagnoses an observed requirement violation while leaving the physical cause unidentified.', fontsize=8)
    save(fig, 'marine-violation-evidence-ladder'); plt.close(fig)
    sources.extend([bind(packet_path), bind(fixture_path)])
    sources.extend(bind(base / f'comparison/{case}/L{i}/B4.json') for i in range(3))
    summary['sources'] = sources
    summary['figure_checks'] = {'all_displayed_quotes_verbatim': True, 'raw_packet_coordinates_match': True,
                              'known_route_dwell_251_samples': True, 'known_route_later_crossing_outside_dwell': True,
                              'direct_route_violation_inside_dwell': True, 'final_annotation_hashes_checked': True}
    (OUT / 'explanation-transfer-results.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('failure_bank', 'contact_replay_bank', 'figure_checks')}, indent=2))


if __name__ == '__main__':
    main()
