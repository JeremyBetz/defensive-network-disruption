"""One frozen synthetic illustration, never an empirical renderer."""
import html
from defensive_network_disruption.networks.options import OptionState, evaluate_options


def synthetic_options_svg(models):
    state = OptionState((0, 0), ("A", "B", "C", "D"),
                        ((12, 8), (22, 0), (10, -12), (30, 15)),
                        ((8, 3), (16, -2), (24, 10)))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="510" viewBox="0 0 1000 510">',
             '<rect width="1000" height="510" fill="#f5f7fb"/>',
             '<g font-family="sans-serif" fill="#142739">',
             '<text x="28" y="32" font-size="20">SYNTHETIC — carrier-centred model-implied option shares</text>']
    for col, name in enumerate(("m0", "m1")):
        net = evaluate_options(state, model=models[name])
        ox = 70 + 500 * col
        def xy(p):
            return ox + 10 * p[0], 245 - 10 * p[1]
        parts.append(f'<text x="{ox-35}" y="65" font-size="17">{name.upper()} — {"attacking geometry" if name=="m0" else "defense-conditioned geometry"}</text>')
        a, b = xy(state.carrier_xy)
        for e, pos in zip(net.edges, state.candidate_xy):
            x, y = xy(pos)
            parts.extend([f'<line x1="{a}" y1="{b}" x2="{x}" y2="{y}" stroke="#167d9a" stroke-width="{0.5+8*e.option_share:.6f}"/>',
                          f'<circle cx="{x}" cy="{y}" r="5" fill="#167d9a"/>',
                          f'<text x="{x+8}" y="{y-5}" font-size="12">{html.escape(e.receiver_id)} {e.option_share:.1%}</text>'])
        for pos in state.defender_xy:
            x,y=xy(pos)
            parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#bd583e"/>')
        parts.extend([f'<circle cx="{a}" cy="{b}" r="6" fill="#142739"/>',
                      f'<text x="{a-40}" y="{b+20}" font-size="12">Carrier</text>',
                      f'<text x="{ox}" y="400" font-size="13">Top share {net.summary["top_one_share"]:.1%} · Effective options {net.summary["effective_option_count"]:.2f}</text>',
                      f'<path d="M {ox},430 h 100" stroke="#142739"/><text x="{ox}" y="450" font-size="11">10 metres</text>',
                      f'<text x="{ox+150}" y="445" font-size="12">Attack →</text>'])
    parts.extend(['<text x="28" y="485" font-size="12">Width = 0.5 + 8 × share. Orange: defenders. Shares are not availability or pass-success probabilities.</text>', '</g></svg>'])
    return "\n".join(parts) + "\n"
