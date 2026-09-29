"""Draw a traced run as a flow chart: what ran in parallel, what ran in series, per lane.

Reads a workspace's `index.json` (written by `trace.py build`) and, if they exist, its
`findings/U<nn>.md` files. Writes `flow.html`: one self-contained page, no scripts, no
network.

The chart reads top to bottom:

  rows     waves: the agents one spawner started in one message, so they ran in parallel.
           Waves follow each other in time, so going down a column is running in series.
  columns  lanes: what a unit worked on (its `Section:` input, else the first `a/b` name in
           its description), so a column is one section's whole history: every agent that
           touched it, how many runs and review rounds it took, and how each review ended.
  bands    full-width rows where the driver stopped to ask the user, or the user typed.

A review is any unit whose return carries `Verdict:`; its box is coloured by the verdict and
shows its critical and warning counts. A unit with a findings file gets a badge with its
ERROR count. Everything here is read from index.json, so re-running `trace.py flow` after an
audit adds the badges without rebuilding the trace.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

PALETTE = ["#4e79a7", "#f28e2b", "#59a14f", "#b07aa1", "#76b7b2", "#edc948", "#ff9da7", "#9c755f"]
VERDICT = {  # label, css class
    "approve": ("✓ approve", "ok"),
    "request changes": ("✗ changes", "bad"),
    "reject": ("✗ reject", "bad"),
    "spec-change": ("↺ spec-change", "warn"),
    "blocked": ("⏸ blocked", "idle"),
    "defer": ("→ defer", "idle"),
}
RESULT = {"done": "ok", "blocked": "idle", "stopped": "idle", "failed": "bad",
          "spec-change": "warn", "design-gap": "warn"}

LEFT, CW, BH, GAP, HEAD, BAND = 150, 178, 54, 6, 64, 34


def ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def minutes(a: str, b: str) -> int | None:
    x, y = ts(a), ts(b)
    return round((y - x).total_seconds() / 60) if x and y else None


def audit_errors(out: Path, unit: str) -> int | None:
    f = out / "findings" / f"{unit}.md"
    if not f.exists():
        return None
    return len(re.findall(r"^## F\d+ · ERROR", f.read_text(encoding="utf-8"), re.M))


# ---------------------------------------------------------------- model


def model(index: dict, out: Path | None = None) -> dict:
    units = index["units"]
    for u in units:
        u["lane"] = u.get("lane") or "(other)"
        u["mins"] = minutes(u["first_ts"], u["last_ts"])
        u["audit"] = audit_errors(out, u["unit"]) if out else None

    waves: dict[str, list[dict]] = {}
    for u in units:
        waves.setdefault(u.get("wave_key") or u["unit"], []).append(u)
    wave_list = sorted(waves.values(), key=lambda us: min(u["first_ts"] for u in us))
    for n, us in enumerate(wave_list, 1):
        for u in us:
            u["wave"] = n

    # Columns follow the widest wave (usually the plan's own order: the designers of every
    # section in one message), then every other lane where it first appears.
    widest = max(wave_list, key=lambda us: len({u["lane"] for u in us}), default=[])
    lanes: list[str] = []
    for u in [*widest, *(u for us in wave_list for u in us)]:
        if u["lane"] not in lanes:
            lanes.append(u["lane"])
    if "(other)" in lanes:
        lanes.remove("(other)")
        lanes.append("(other)")

    roles: list[str] = []
    for u in units:
        if u["role"] not in roles:
            roles.append(u["role"])

    lane_info = {}
    for lane in lanes:
        mine = [u for u in units if u["lane"] == lane]
        reviews = [u for u in mine if u.get("verdict")]
        rounds = max([u["round"] for u in reviews if u.get("round")] or [0])
        by_role: dict[str, int] = {}
        for u in mine:
            by_role[u["role"]] = by_role.get(u["role"], 0) + 1
        lane_info[lane] = {"runs": len(mine), "by_role": by_role, "rounds": rounds, "reviews": reviews,
                           "last": reviews[-1]["verdict"] if reviews else None}

    rows: list[dict] = []
    pending = sorted(index.get("interventions", []), key=lambda i: i["ts"])
    for n, us in enumerate(wave_list, 1):
        start = min(u["first_ts"] for u in us)
        while pending and pending[0]["ts"] < start:
            rows.append({"band": pending.pop(0)})
        rows.append({"wave": n, "units": us, "start": start, "end": max(u["last_ts"] for u in us),
                     "spawner": us[0]["spawner"]})
    rows.extend({"band": b} for b in pending)
    return {"rows": rows, "lanes": lanes, "roles": roles, "lane_info": lane_info, "waves": len(wave_list)}


# ---------------------------------------------------------------- text, for run.md


def text(index: dict) -> list[str]:
    m = model(json.loads(json.dumps(index)))
    par = [r for r in m["rows"] if "wave" in r and len(r["units"]) > 1]
    lines = [
        "## Flow",
        "",
        f"{m['waves']} waves; {len(par)} ran agents in parallel (widest: "
        f"{max([len(r['units']) for r in par] or [1])}). `∥` is a parallel wave, `→` a single agent. "
        "The chart is `flow.html`.",
        "",
    ]
    for r in m["rows"]:
        if "band" in r:
            b = r["band"]
            lines.append(f"- **{'asked the user' if b['kind'] == 'asked' else 'user said'}** "
                         f"({b['step']}): {b['text'][:160]}" + (f" → {b['answer'][:120]}" if b["answer"] else ""))
            continue
        us = r["units"]
        when = r["start"][11:16]
        dur = minutes(r["start"], r["end"])
        mark = f"∥ {len(us)}" if len(us) > 1 else "→"
        who = "; ".join(
            f"{u['unit']} {u['role']} {u['lane']}"
            + (f" [{u['verdict']}{', ' + str(u['critical']) + ' crit' if u.get('critical') else ''}]" if u.get("verdict")
               else f" [{u['result']}]" if u.get("result") and u["result"] != "done" else "")
            for u in us)
        by = "" if r["spawner"] == "driver" else f" (by {r['spawner']})"
        lines.append(f"- `W{r['wave']}` {when} · {dur if dur is not None else '?'}m · {mark}{by} — {who}")
    lines += ["", "| Lane | Runs | By role | Review rounds | Reviews, in order |", "|---|---|---|---|---|"]
    for lane in m["lanes"]:
        li = m["lane_info"][lane]
        roles = ", ".join(f"{k} {v}" for k, v in li["by_role"].items())
        revs = " → ".join(f"{u['unit']} {u['verdict']}" + (f" ({u['critical']}C)" if u.get("critical") else "")
                          for u in li["reviews"]) or "—"
        lines.append(f"| {lane} | {li['runs']} | {roles} | {li['rounds'] or '—'} | {revs} |")
    return lines + [""]


# ---------------------------------------------------------------- html


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fit(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def sublabel(u: dict) -> str:
    """The description minus the role word and the lane, so the box says what is left."""
    d = u["description"]
    for w in (u["lane"], u["role"]):
        d = re.sub(re.escape(w), " ", d, flags=re.I)
    d = re.sub(rf"(?<![\w-]){re.escape(u['lane'].split('/')[-1])}(?![\w-])", " ", d, flags=re.I)
    d = re.sub(r"^\s*(design|implement|review|probe|intent tests|tests?)\b", " ", d, flags=re.I)
    d = re.sub(r"\s+(for|of|to|on)\s*$", " ", d, flags=re.I)
    return re.sub(r"\s{2,}", " ", d).strip(" -—·")


def box(u: dict, x: float, y: float, w: float, color: str) -> str:
    title = (f"{u['unit']} · {u['type']}\n{u['description']}\n"
             f"{u['mins'] if u['mins'] is not None else '?'} min · {u['tool_calls']} tools · "
             f"{u['errors']} errors · {u['hook_blocks']} hook blocks\n"
             f"commits: {', '.join(u['commits']) or 'none'}\n"
             f"returned: {u['return_first_line'] or '(still running)'}")
    parts = [f'<g class="unit"><title>{esc(title)}</title>',
             f'<rect x="{x}" y="{y}" width="{w}" height="{BH}" rx="6" class="box"/>',
             f'<rect x="{x}" y="{y}" width="5" height="{BH}" rx="2" fill="{color}"/>',
             f'<text x="{x + 11}" y="{y + 16}" class="role">{esc(u["role"])}</text>',
             f'<text x="{x + w - 6}" y="{y + 16}" class="uid" text-anchor="end">{u["unit"]}</text>']
    sub = sublabel(u)
    if sub:
        parts.append(f'<text x="{x + 11}" y="{y + 30}" class="sub">{esc(fit(sub, 26))}</text>')
    if u.get("verdict"):
        label, cls = VERDICT.get(u["verdict"], (u["verdict"], "idle"))
        counts = []
        if u.get("critical"):
            counts.append(f"{u['critical']}C")
        if u.get("warning") is not None:
            counts.append(f"{u['warning']}W")
        parts.append(f'<text x="{x + 11}" y="{y + 45}" class="badge {cls}">{esc(label)}</text>')
        if counts:
            parts.append(f'<text x="{x + w - 6}" y="{y + 45}" class="meta {"bad" if u.get("critical") else ""}" '
                         f'text-anchor="end">{" ".join(counts)}</text>')
    else:
        res = u.get("result") or ("running" if not u.get("finished") else "returned")
        cls = RESULT.get(res, "idle")
        meta = f"{u['mins']}m" if u["mins"] is not None else ""
        if u["hook_blocks"]:
            meta += f" · {u['hook_blocks']}⛔"
        parts.append(f'<text x="{x + 11}" y="{y + 45}" class="badge {cls}">{esc(res)}</text>')
        parts.append(f'<text x="{x + w - 6}" y="{y + 45}" class="meta" text-anchor="end">{esc(meta)}</text>')
    if u.get("audit") is not None:
        cls = "bad" if u["audit"] else "ok"
        parts.append(f'<circle cx="{x + w - 2}" cy="{y + 2}" r="9" class="audit {cls}"/>'
                     f'<text x="{x + w - 2}" y="{y + 6}" class="auditn" text-anchor="middle">'
                     f'{u["audit"] if u["audit"] else "✓"}</text>')
    parts.append("</g>")
    return "".join(parts)


def svg(m: dict) -> str:
    """Four SVGs in a CSS grid, so the lane headers stick to the top and the wave labels to
    the left while the body scrolls under them."""
    lanes, rows = m["lanes"], m["rows"]
    color = {r: PALETTE[i % len(PALETTE)] for i, r in enumerate(m["roles"])}
    width = CW * len(lanes) + 10
    y = 0
    body: list[str] = []
    side: list[str] = []
    last_box: dict[str, tuple[float, float]] = {}  # lane -> (x center, bottom y) of its latest box
    links: list[str] = []

    for r in rows:
        if "band" in r:
            b = r["band"]
            who = "asked you" if b["kind"] == "asked" else "you said"
            label = f"{who} ({b['step']}): {b['text']}"
            if b["answer"]:
                label += f"  →  {b['answer']}"
            body.append(f'<g><title>{esc(label)}</title><rect x="0" y="{y}" width="{width}" height="{BAND - 6}" '
                        f'class="band"/><text x="8" y="{y + 18}" class="bandt">'
                        f'{esc(fit(label, int((width - 30) / 6.4)))}</text></g>')
            side.append(f'<rect x="4" y="{y}" width="{LEFT - 4}" height="{BAND - 6}" class="band"/>'
                        f'<text x="10" y="{y + 18}" class="bandt"><tspan class="wave">'
                        f'{"❓ asked you" if b["kind"] == "asked" else "💬 you said"}</tspan></text>')
            y += BAND
            continue
        us = r["units"]
        per_lane: dict[str, list[dict]] = {}
        for u in us:
            per_lane.setdefault(u["lane"], []).append(u)
        height = max(len(v) for v in per_lane.values()) * (BH + GAP) + GAP
        par = len(us) > 1
        shade = "rowp" if par else "rows"
        body.append(f'<rect x="0" y="{y}" width="{width}" height="{height}" class="{shade}"/>')
        side.append(f'<rect x="0" y="{y}" width="{LEFT}" height="{height}" class="{shade}"/>')
        dur = minutes(r["start"], r["end"])
        by = "" if r["spawner"] == "driver" else f" · by {r['spawner']}"
        side.append(f'<text x="10" y="{y + 18}" class="wave">W{r["wave"]} '
                    f'<tspan class="{"par" if par else "ser"}">{"∥ " + str(len(us)) if par else "→ 1"}</tspan></text>'
                    f'<text x="10" y="{y + 34}" class="wmeta">{r["start"][11:16]} · '
                    f'{dur if dur is not None else "?"} min{esc(by)}</text>')
        for lane, lus in per_lane.items():
            x = lanes.index(lane) * CW + 6
            cx = x + (CW - 12) / 2
            for k, u in enumerate(lus):
                by_ = y + GAP + k * (BH + GAP)
                if k == 0 and lane in last_box:
                    px, py = last_box[lane]
                    links.append(f'<line x1="{px}" y1="{py}" x2="{cx}" y2="{by_ - 1}" class="link" '
                                 f'marker-end="url(#arrow)"/>')
                body.append(box(u, x, by_, CW - 12, color[u["role"]]))
            last_box[lane] = (cx, y + GAP + (len(lus) - 1) * (BH + GAP) + BH)
        y += height
    height = y + 10

    heads, grid = [], []
    for i, lane in enumerate(lanes):
        li = m["lane_info"][lane]
        x = i * CW + CW / 2
        tail = f"{li['runs']} runs"
        if li["rounds"]:
            tail += f" · {li['rounds']} review round{'s' if li['rounds'] > 1 else ''}"
        last = VERDICT.get(li["last"], (li["last"] or "", "idle")) if li["last"] else None
        heads.append(f'<text x="{x}" y="22" class="lane" text-anchor="middle">{esc(fit(lane, 24))}</text>'
                     f'<text x="{x}" y="38" class="lmeta" text-anchor="middle">{esc(tail)}</text>'
                     + (f'<text x="{x}" y="54" class="badge {last[1]}" text-anchor="middle">last review: '
                        f'{esc(last[0])}</text>' if last else ""))
        grid.append(f'<line x1="{i * CW}" y1="0" x2="{i * CW}" y2="{height}" class="grid"/>')

    def one(w, h, inner, cls, defs=""):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
                f'class="{cls}">{defs}{inner}</svg>')

    arrow = ('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
             'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrowhead"/></marker></defs>')
    return (f'<div class="chart" style="grid-template-columns:{LEFT}px {width}px">'
            f'<div class="corner">{one(LEFT, HEAD, "", "bg")}</div>'
            f'<div class="colhead">{one(width, HEAD, "".join(heads), "bg")}</div>'
            f'<div class="rowhead">{one(LEFT, height, "".join(side), "bg")}</div>'
            f'<div>{one(width, height, "".join(grid) + "".join(body) + "".join(links), "", arrow)}</div>'
            "</div>")


CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1f;--muted:#6b6b70;--line:#d9d9de;--box:#fff;--rowp:#eef3fb;--band:#fff4d6;
--ok:#2e7d32;--bad:#c62828;--warn:#b26a00;--idle:#6b6b70}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17171a;--fg:#ececf0;--muted:#9a9aa3;
--line:#34343a;--box:#222227;--rowp:#1d2433;--band:#3a3015;--ok:#6fcf73;--bad:#ff6b6b;--warn:#f0b35a;--idle:#9a9aa3}}
:root[data-theme="dark"]{--bg:#17171a;--fg:#ececf0;--muted:#9a9aa3;--line:#34343a;--box:#222227;--rowp:#1d2433;
--band:#3a3015;--ok:#6fcf73;--bad:#ff6b6b;--warn:#f0b35a;--idle:#9a9aa3}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 -apple-system,system-ui,sans-serif}
h1{font-size:18px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 8px}.sub{color:var(--muted)}
table{border-collapse:collapse;margin:4px 0 8px}td,th{border-bottom:1px solid var(--line);padding:4px 10px;text-align:left;
vertical-align:top}th{color:var(--muted);font-weight:600}.chips span{display:inline-block;margin:0 4px 2px 0}
.legend span{margin-right:14px;white-space:nowrap}.sw{display:inline-block;width:10px;height:10px;border-radius:2px;
margin-right:4px;vertical-align:-1px}.scroll{overflow:auto;max-height:88vh;border:1px solid var(--line);border-radius:8px}
.chart{display:grid;width:max-content}.chart>div{line-height:0}.corner{position:sticky;top:0;left:0;z-index:3}
.colhead{position:sticky;top:0;z-index:2}.rowhead{position:sticky;left:0;z-index:2}
svg.bg{background:var(--bg)}.colhead svg{border-bottom:1px solid var(--line)}.rowhead svg{border-right:1px solid var(--line)}
.ok{color:var(--ok);fill:var(--ok)}.bad{color:var(--bad);fill:var(--bad)}.warn{color:var(--warn);fill:var(--warn)}
.idle{color:var(--idle);fill:var(--idle)}
svg text{fill:var(--fg);font-family:-apple-system,system-ui,sans-serif}
.box{fill:var(--box);stroke:var(--line)}.unit:hover .box{stroke:var(--fg)}
.role{font-size:12px;font-weight:600}.uid,.wmeta,.lmeta,.meta{font-size:10px;fill:var(--muted)}
.sub{font-size:10.5px;fill:var(--muted)}.badge{font-size:11px;font-weight:600}
.meta.bad{fill:var(--bad);font-weight:600}.lane{font-size:13px;font-weight:700}.wave{font-size:13px;font-weight:700}
.par{fill:#4e79a7}.ser{fill:var(--muted)}.rowp{fill:var(--rowp)}.rows{fill:transparent}.band{fill:var(--band)}
.bandt{font-size:11.5px}.grid{stroke:var(--line)}.link{stroke:var(--muted);stroke-width:1.2;opacity:.55}
.arrowhead{fill:var(--muted)}.audit{stroke:var(--box);stroke-width:2}.auditn{font-size:10px;font-weight:700;fill:#fff}
"""


def write_html(out: Path) -> Path:
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    m = model(index, out)
    units = index["units"]
    par = [r for r in m["rows"] if "wave" in r and len(r["units"]) > 1]
    commands = ", ".join(s["command"] for s in index["segments"]) or "(no command of the plugin)"
    reviews = [u for u in units if u.get("verdict")]
    flagged = [u for u in reviews if u["verdict"] != "approve" or u.get("critical")]
    audited = [u for u in units if u.get("audit") is not None]

    legend = "".join(f'<span><i class="sw" style="background:{PALETTE[i % len(PALETTE)]}"></i>{esc(r)}</span>'
                     for i, r in enumerate(m["roles"]))
    lane_rows = []
    for lane in m["lanes"]:
        li = m["lane_info"][lane]
        chips = "".join(
            f'<span class="{VERDICT.get(u["verdict"], ("", "idle"))[1]}">'
            f'{esc(u["unit"])} r{u.get("round") or "?"} {esc(VERDICT.get(u["verdict"], (u["verdict"],))[0])}'
            f'{" " + str(u["critical"]) + "C" if u.get("critical") else ""}</span>' for u in li["reviews"]) or "—"
        roles = ", ".join(f"{esc(k)} {v}" for k, v in li["by_role"].items())
        lane_rows.append(f"<tr><td><b>{esc(lane)}</b></td><td>{li['runs']}</td><td>{roles}</td>"
                         f"<td>{li['rounds'] or '—'}</td><td class='chips'>{chips}</td></tr>")
    flagged_rows = "".join(
        f"<tr><td>{esc(u['unit'])}</td><td>{esc(u['lane'])}</td><td>{esc(u['description'])}</td>"
        f"<td class='{VERDICT.get(u['verdict'], ('', 'idle'))[1]}'>{esc(u['verdict'])}</td>"
        f"<td>{u.get('critical') if u.get('critical') is not None else '—'}</td>"
        f"<td>{u.get('warning') if u.get('warning') is not None else '—'}</td></tr>" for u in flagged)
    audit_note = (f"{len(audited)} audited; the badge on a box is its audit ERROR count (✓ none)."
                  if audited else "No unit audited yet; run `trace.py flow` after an audit to add badges.")

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Run flow</title><style>{CSS}</style></head>
<body>
<h1>{esc(index['plugin'])} {esc(index.get('version') or '')} · {esc(commands)}</h1>
<div class="sub">session {esc(index['session'][:8])} · {esc(index.get('project') or '')} · {esc(index.get('branch') or '')}
 · {esc(index['first_ts'][:16].replace('T', ' '))} → {esc(index['last_ts'][:16].replace('T', ' '))} UTC</div>
<p>{len(units)} agents in {m['waves']} waves. {len(par)} waves ran agents in parallel (widest:
{max([len(r['units']) for r in par] or [1])}); the rest ran one agent at a time.
{len(index.get('interventions', []))} stops for you. {audit_note}</p>

<h2>Per section</h2>
<table><tr><th>Section</th><th>Runs</th><th>By role</th><th>Review rounds</th><th>Reviews, in order</th></tr>
{''.join(lane_rows)}</table>

<h2>Reviews that found issues</h2>
{"<table><tr><th>Unit</th><th>Section</th><th>Review</th><th>Verdict</th><th>Critical</th><th>Warning</th></tr>"
 + flagged_rows + "</table>" if flagged else "<p>None: every review approved with no critical finding.</p>"}

<h2>Flow</h2>
<p class="legend">Down is time. A shaded row is one wave of agents started together, so they ran in parallel;
an unshaded row ran one agent alone. Each column is one section's history, arrows joining its runs in order.
Hover a box for its duration, tools, commits and return. {legend}</p>
<div class="scroll">{svg(m)}</div>
</body></html>"""
    path = out / "flow.html"
    path.write_text(page, encoding="utf-8")
    return path
