"""Deterministic synthetic illustration for defender-edge geometry."""
from __future__ import annotations
import html
from defensive_network_disruption.networks.options import OptionState
from defensive_network_disruption.networks.defender_edges import map_defender_edges


def synthetic_defender_edge_svg() -> str:
    state = OptionState((0, 0), ("A", "B", "C", "D"),
                        ((20, -10), (25, 0), (20, 10), (-10, 5)),
                        ((5, 0), (18, -9), (18, 9), (-7, 4)))
    mapping = map_defender_edges(state)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="650" viewBox="0 0 1200 650">',
             '<rect width="1200" height="650" fill="#f6f7f9"/>',
             '<g font-family="sans-serif" fill="#172a3a">',
             '<text x="35" y="38" font-size="22">SYNTHETIC — GEOMETRIC RELATIONSHIPS, NOT SUPPRESSION</text>']
    for panel, kind in enumerate(("receiver", "segment")):
        ox = 80 + panel * 590
        oy = 275
        def xy(point): return ox + point[0] * 9, oy - point[1] * 9
        parts.append(f'<text x="{ox-30}" y="75" font-size="18">{kind.title()} proximity</text>')
        cx, cy = xy(state.carrier_xy)
        for receiver_index, (rid, point) in enumerate(zip(state.candidate_ids, state.candidate_xy)):
            x, y = xy(point)
            parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#7c98a8" stroke-width="2"/>')
            parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#167d9a"/><text x="{x+8}" y="{y-6}" font-size="13">{html.escape(rid)}</text>')
            rows = mapping.for_receiver(receiver_index)
            for relation in rows:
                if relation.membership(kind, 1) > 0 or relation.membership(kind, 2) > 0:
                    dx, dy = xy(state.defender_xy[relation.defender_index])
                    style = 'stroke="#d24b40" stroke-width="3"' if relation.membership(kind, 1) > 0 else 'stroke="#e59a3a" stroke-width="2" stroke-dasharray="5 4"'
                    target_x, target_y = (x, y) if kind == "receiver" else ((cx+x)/2, (cy+y)/2)
                    parts.append(f'<line x1="{dx}" y1="{dy}" x2="{target_x}" y2="{target_y}" {style} opacity="0.72"/>')
        for index, point in enumerate(state.defender_xy):
            x, y = xy(point)
            parts.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#d24b40"/><text x="{x+9}" y="{y+16}" font-size="12">D{index+1}</text>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="#172a3a"/><text x="{cx-25}" y="{cy+24}" font-size="12">Carrier</text>')
        parts.append(f'<path d="M {ox-30},470 h 90" stroke="#172a3a"/><text x="{ox-30}" y="490" font-size="11">10 metres</text><text x="{ox+110}" y="485" font-size="12">Attack →</text>')
        y0 = 525
        parts.append(f'<text x="{ox-30}" y="{y0}" font-size="12">Edge × defender ranks (1 filled, 2 outlined)</text>')
        for ri, rid in enumerate(state.candidate_ids):
            parts.append(f'<text x="{ox-30}" y="{y0+22+ri*20}" font-size="11">{rid}</text>')
            for di, relation in enumerate(mapping.for_receiver(ri)):
                rank = getattr(relation, f"{kind}_rank")
                fill = '#d24b40' if relation.membership(kind, 1) > 0 else ('none' if relation.membership(kind, 2) > 0 else '#d9dee2')
                stroke = '#e59a3a' if relation.membership(kind, 2) > 0 and relation.membership(kind, 1) == 0 else '#7f8d96'
                parts.append(f'<circle cx="{ox+40+di*42}" cy="{y0+18+ri*20}" r="7" fill="{fill}" stroke="{stroke}"/><text x="{ox+34+di*42}" y="{y0-2}" font-size="10">D{di+1}</text>')
                parts.append(f'<title>{html.escape(rid)} D{di+1} expected rank {rank:g}</title>')
    parts.extend(['<text x="35" y="635" font-size="12">Red = nearest-block relationship; orange outline/dash = second-position membership. Anonymous state-local defenders.</text>', '</g></svg>'])
    return "\n".join(parts) + "\n"
