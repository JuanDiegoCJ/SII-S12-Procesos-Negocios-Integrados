"""Generador de diagramas BPMN 2.0.

A partir de una descripción en Python (piscinas, carriles, nodos y flujos)
produce dos salidas coherentes entre sí:
  * un archivo .bpmn (XML BPMN 2.0 con información de diagrama, BPMN DI),
    importable en Bizagi Modeler, Camunda Modeler o bpmn.io;
  * una imagen .svg con la misma disposición.
"""
from xml.sax.saxutils import escape
import textwrap

TASK_W, TASK_H = 106, 66
EV = 36
GW = 46
POOL_LABEL = 30
LANE_LABEL = 30
PAD_X = 24
FONT = "Caladea, Cambria, Georgia, serif"

TASKS = {"task", "userTask", "serviceTask", "sendTask", "receiveTask", "manualTask", "subProcess"}
EVENTS = {"start", "startMsg", "startTimer", "end", "endMsg", "interMsgCatch", "interMsgThrow", "interTimer"}
GATEWAYS = {"xor", "and", "or"}


class Diagram:
    def __init__(self, ident, name, colw=122, laneh=118, bbh=54, pool_gap=44):
        self.id, self.name = ident, name
        self.colw, self.laneh, self.bbh, self.pool_gap = colw, laneh, bbh, pool_gap
        self.pools, self.nodes, self.flows, self.msgs = [], {}, [], []
        self.ncols = 0

    # ---------- descripción ----------
    def pool(self, pid, name, lanes=None, blackbox=False, laneh=None):
        self.pools.append(dict(id=pid, name=name, lanes=lanes or [], bb=blackbox,
                               laneh=laneh or self.laneh))

    def node(self, nid, kind, name, lane, col, dy=0, label="below"):
        self.nodes[nid] = dict(id=nid, kind=kind, name=name, lane=lane, col=col, dy=dy, label=label)
        self.ncols = max(self.ncols, col + 0.95)

    def flow(self, src, tgt, label="", route=None, via=None, lpos=None):
        self.flows.append(dict(src=src, tgt=tgt, label=label, route=route, via=via, lpos=lpos))

    def msg(self, src, tgt, label="", dx=0, lpos=None):
        self.msgs.append(dict(src=src, tgt=tgt, label=label, dx=dx, lpos=lpos))

    # ---------- geometría ----------
    def layout(self):
        width = int(POOL_LABEL + LANE_LABEL + 2 * PAD_X + self.ncols * self.colw)
        self.W = width
        y = 0
        self.lane_geo, self.pool_geo = {}, {}
        for p in self.pools:
            if p["bb"]:
                self.pool_geo[p["id"]] = (0, y, width, self.bbh)
                y += self.bbh + self.pool_gap
                continue
            h = len(p["lanes"]) * p["laneh"]
            self.pool_geo[p["id"]] = (0, y, width, h)
            ly = y
            for lid, _ in p["lanes"]:
                self.lane_geo[lid] = (POOL_LABEL, ly, width - POOL_LABEL, p["laneh"], p["id"])
                ly += p["laneh"]
            y += h + self.pool_gap
        self.H = y - self.pool_gap
        for n in self.nodes.values():
            lx, ly, lw, lh, pid = self.lane_geo[n["lane"]]
            cx = POOL_LABEL + LANE_LABEL + PAD_X + n["col"] * self.colw + self.colw / 2
            cy = ly + lh / 2 + n["dy"]
            w, h = self.size(n["kind"])
            n.update(cx=cx, cy=cy, w=w, h=h, x=cx - w / 2, y=cy - h / 2, pool=pid)

    @staticmethod
    def size(kind):
        if kind in TASKS:
            return TASK_W, TASK_H
        if kind in GATEWAYS:
            return GW, GW
        return EV, EV

    def edge_points(self, f):
        s, t = self.nodes[f["src"]], self.nodes[f["tgt"]]
        route = f["route"]
        if f["via"] is not None:  # retorno por encima o por debajo
            vy = f["via"]
            if isinstance(vy, str):
                parts = vy.split(":")
                lx, ly, lw, lh, _ = self.lane_geo[parts[0]]
                off = float(parts[2]) if len(parts) > 2 else 12
                vy = ly + lh - off if parts[1] == "bottom" else ly + off
            sy = s["y"] + s["h"] if vy > s["cy"] else s["y"]
            ty = t["y"] + t["h"] if vy > t["cy"] else t["y"]
            return [(s["cx"], sy), (s["cx"], vy), (t["cx"], vy), (t["cx"], ty)]
        if abs(s["cy"] - t["cy"]) < 1:
            if t["cx"] > s["cx"]:
                return [(s["x"] + s["w"], s["cy"]), (t["x"], t["cy"])]
            return [(s["x"], s["cy"]), (t["x"] + t["w"], t["cy"])]
        if abs(s["cx"] - t["cx"]) < 1:
            down = t["cy"] > s["cy"]
            return [(s["cx"], s["y"] + (s["h"] if down else 0)),
                    (t["cx"], t["y"] + (0 if down else t["h"]))]
        down = t["cy"] > s["cy"]
        if route is None:
            route = "vh" if s["kind"] in GATEWAYS else "hv"
        if route == "hv":
            sx = s["x"] + s["w"] if t["cx"] > s["cx"] else s["x"]
            return [(sx, s["cy"]), (t["cx"], s["cy"]),
                    (t["cx"], t["y"] + (0 if down else t["h"]))]
        if route == "vh":
            return [(s["cx"], s["y"] + (s["h"] if down else 0)), (s["cx"], t["cy"]),
                    (t["x"] if t["cx"] > s["cx"] else t["x"] + t["w"], t["cy"])]
        if route == "hvh":
            xm = (s["x"] + s["w"] + t["x"]) / 2
            return [(s["x"] + s["w"], s["cy"]), (xm, s["cy"]), (xm, t["cy"]), (t["x"], t["cy"])]
        raise ValueError(route)

    def msg_points(self, m):
        def end(ref, other_y):
            if ref in self.nodes:
                n = self.nodes[ref]
                return n["cx"], (n["y"] + n["h"] if other_y > n["cy"] else n["y"]), n["cy"]
            px, py, pw, ph = self.pool_geo[ref]
            return None, (py + ph if other_y > py + ph / 2 else py), py + ph / 2

        def cy(ref):
            if ref in self.nodes:
                return self.nodes[ref]["cy"]
            px, py, pw, ph = self.pool_geo[ref]
            return py + ph / 2

        sx, sy, _ = end(m["src"], cy(m["tgt"]))
        tx, ty, _ = end(m["tgt"], cy(m["src"]))
        x = (sx if sx is not None else tx) + m["dx"]
        return [(x, sy), (x, ty)]

    # ---------- SVG ----------
    def svg(self, scale=1.0):
        self.layout()
        m = 6
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-m} {-m} {self.W + 2*m} {self.H + 2*m}" '
               f'width="{(self.W + 2*m) * scale:.0f}" height="{(self.H + 2*m) * scale:.0f}" '
               f'font-family="{FONT}" font-size="10.5">',
               '<defs>'
               '<marker id="arr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
               '<path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker>'
               '<marker id="arro" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
               '<path d="M0,0 L10,5 L0,10 z" fill="#fff" stroke="#555"/></marker>'
               '<marker id="circ" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6">'
               '<circle cx="5" cy="5" r="4" fill="#fff" stroke="#555"/></marker>'
               '</defs>']
        for p in self.pools:
            x, y, w, h = self.pool_geo[p["id"]]
            fill = "#EEF1F6" if p["bb"] else "#FFFFFF"
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#3A3A3A" stroke-width="1.3"/>')
            if p["bb"]:
                out.append(f'<text x="{w/2:.1f}" y="{y + h/2 + 4:.1f}" text-anchor="middle" font-size="13" '
                           f'font-weight="bold" fill="#333">{escape(p["name"])}</text>')
                continue
            out.append(f'<line x1="{POOL_LABEL}" y1="{y}" x2="{POOL_LABEL}" y2="{y+h}" stroke="#3A3A3A" stroke-width="1.3"/>')
            out.append(self._vtext(POOL_LABEL / 2, y + h / 2, p["name"], h - 6, bold=True, size=11))
            for i, (lid, lname) in enumerate(p["lanes"]):
                lx, ly, lw, lh, _ = self.lane_geo[lid]
                if i:
                    out.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+lw}" y2="{ly}" stroke="#777" stroke-width="0.9"/>')
                out.append(f'<line x1="{lx+LANE_LABEL}" y1="{ly}" x2="{lx+LANE_LABEL}" y2="{ly+lh}" stroke="#777" stroke-width="0.9"/>')
                out.append(f'<rect x="{lx+0.6}" y="{ly+0.6}" width="{LANE_LABEL-1.2}" height="{lh-1.2}" fill="#F3F5F9"/>')
                out.append(self._vtext(lx + LANE_LABEL / 2, ly + lh / 2, lname, lh - 4, size=11.5))
        for f in self.flows:
            pts = self.edge_points(f)
            d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
            out.append(f'<path d="{d}" fill="none" stroke="#333" stroke-width="1.1" marker-end="url(#arr)"/>')
            if f["label"]:
                (x0, y0), (x1, y1) = pts[0], pts[1]
                if f["lpos"]:
                    lx, ly = x0 + f["lpos"][0], y0 + f["lpos"][1]
                elif abs(x1 - x0) > abs(y1 - y0):
                    lx, ly = x0 + 6, y0 - 5
                else:
                    lx, ly = x0 + 5, y0 + (13 if y1 > y0 else -6)
                out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="11.5" font-style="italic" fill="#222">{escape(f["label"])}</text>')
        for mm in self.msgs:
            pts = self.msg_points(mm)
            d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
            out.append(f'<path d="{d}" fill="none" stroke="#555" stroke-width="1" stroke-dasharray="5,3" '
                       f'marker-start="url(#circ)" marker-end="url(#arro)"/>')
            if mm["label"]:
                (x0, y0), (x1, y1) = pts
                lx = x0 + 5 + (mm["lpos"][0] if mm["lpos"] else 0)
                ly = (y0 + y1) / 2 + (mm["lpos"][1] if mm["lpos"] else 0)
                lines = textwrap.wrap(mm["label"], 15, break_long_words=False)
                for i, ln in enumerate(lines):
                    out.append(f'<text x="{lx:.1f}" y="{ly + i*12 - (len(lines)-1)*6:.1f}" font-size="11" '
                               f'fill="#444" font-style="italic">{escape(ln)}</text>')
        for n in self.nodes.values():
            out.append(self._node_svg(n))
        out.append("</svg>")
        return "\n".join(out)

    def _vtext(self, cx, cy, text, avail, bold=False, size=10):
        lines = textwrap.wrap(text, max(8, int(avail / (size * 0.5))), break_long_words=False)
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate(-90)">']
        for i, ln in enumerate(lines):
            yy = (i - (len(lines) - 1) / 2) * (size + 1.5) + size * 0.35
            g.append(f'<text x="0" y="{yy:.1f}" text-anchor="middle" font-size="{size}" '
                     f'{"font-weight=\"bold\"" if bold else ""}>{escape(ln)}</text>')
        g.append("</g>")
        return "".join(g)

    def _node_svg(self, n):
        k, x, y, w, h, cx, cy = n["kind"], n["x"], n["y"], n["w"], n["h"], n["cx"], n["cy"]
        s = []
        if k in TASKS:
            s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#F4F7FC" stroke="#1F3864" stroke-width="1.2"/>')
            s.append(self._icon(k, x + 4, y + 4))
            if k == "subProcess":
                s.append(f'<rect x="{cx-7}" y="{y+h-15}" width="14" height="14" fill="#fff" stroke="#333" stroke-width="1"/>'
                         f'<path d="M{cx-4},{y+h-8} h8 M{cx},{y+h-12} v8" stroke="#333" stroke-width="1.3"/>')
            icon = k not in ("task", "subProcess", "manualTask")
            lines = textwrap.wrap(n["name"], 15 if icon else 16, break_long_words=False)
            top = cy - (len(lines) - 1) * 6.8 + 4.3 - (6 if k == "subProcess" else 0) + (6 if icon and len(lines) == 3 else 0) + (5.5 if icon and len(lines) >= 4 else 0) + (4 if icon and len(lines) == 2 else 0)
            for i, ln in enumerate(lines):
                s.append(f'<text x="{cx}" y="{top + i*(12.6 if icon and len(lines) >= 4 else 13.6):.1f}" text-anchor="middle" font-size="12">{escape(ln)}</text>')
            return "".join(s)
        if k in EVENTS:
            r = EV / 2
            if k.startswith("start"):
                s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#EAF6EC" stroke="#2E7D32" stroke-width="1.5"/>')
            elif k.startswith("end"):
                s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FCEBEB" stroke="#A61B1B" stroke-width="3.2"/>')
            else:
                s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFF8E6" stroke="#8A6D1F" stroke-width="1.3"/>'
                         f'<circle cx="{cx}" cy="{cy}" r="{r-3.5}" fill="none" stroke="#8A6D1F" stroke-width="1.1"/>')
            if "Msg" in k:
                filled = k in ("endMsg", "interMsgThrow")
                s.append(self._envelope(cx, cy, 15, 10.5, filled))
            if "Timer" in k:
                s.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="#fff" stroke="#333" stroke-width="1"/>'
                         f'<path d="M{cx},{cy-7} L{cx},{cy} L{cx+5},{cy+3}" stroke="#333" fill="none" stroke-width="1.1"/>')
        if k in GATEWAYS:
            s.append(f'<path d="M{cx},{y} L{x+w},{cy} L{cx},{y+h} L{x},{cy} z" fill="#FFF7E0" stroke="#9C7A14" stroke-width="1.3"/>')
            if k == "xor":
                s.append(f'<path d="M{cx-7},{cy-7} L{cx+7},{cy+7} M{cx+7},{cy-7} L{cx-7},{cy+7}" stroke="#333" stroke-width="2.6"/>')
            elif k == "and":
                s.append(f'<path d="M{cx},{cy-10} L{cx},{cy+10} M{cx-10},{cy} L{cx+10},{cy}" stroke="#333" stroke-width="2.6"/>')
            else:
                s.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="#333" stroke-width="2.2"/>')
        if n["name"]:
            lines = textwrap.wrap(n["name"], 15, break_long_words=False)
            base = y + h + 13 if n["label"] == "below" else y - 6 - (len(lines) - 1) * 12
            for i, ln in enumerate(lines):
                s.append(f'<text x="{cx}" y="{base + i*12.8:.1f}" text-anchor="middle" font-size="11.5">{escape(ln)}</text>')
        return "".join(s)

    @staticmethod
    def _envelope(cx, cy, w, h, filled):
        x, y = cx - w / 2, cy - h / 2
        fill, line = ("#333", "#fff") if filled else ("#fff", "#333")
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#333" stroke-width="1"/>'
                f'<path d="M{x},{y} L{cx},{cy+1} L{x+w},{y}" fill="none" stroke="{line}" stroke-width="1"/>')

    def _icon(self, k, x, y):
        if k == "serviceTask":
            return (f'<circle cx="{x+7}" cy="{y+7}" r="5.5" fill="none" stroke="#333" stroke-width="2.2" stroke-dasharray="2.2,1.6"/>'
                    f'<circle cx="{x+7}" cy="{y+7}" r="2.2" fill="none" stroke="#333" stroke-width="1"/>')
        if k == "userTask":
            return (f'<circle cx="{x+7}" cy="{y+4.5}" r="3.2" fill="#fff" stroke="#333" stroke-width="1"/>'
                    f'<path d="M{x+1},{y+14} Q{x+1},{y+8} {x+7},{y+8} Q{x+13},{y+8} {x+13},{y+14} z" fill="#fff" stroke="#333" stroke-width="1"/>')
        if k in ("sendTask", "receiveTask"):
            return self._envelope(x + 8, y + 6, 13, 9, k == "sendTask")
        return ""

    # ---------- BPMN XML ----------
    def bpmn(self):
        self.layout()
        tag = {"task": "task", "userTask": "userTask", "serviceTask": "serviceTask", "sendTask": "sendTask",
               "receiveTask": "receiveTask", "manualTask": "manualTask", "subProcess": "subProcess",
               "start": "startEvent", "startMsg": "startEvent", "startTimer": "startEvent",
               "end": "endEvent", "endMsg": "endEvent", "interMsgCatch": "intermediateCatchEvent",
               "interMsgThrow": "intermediateThrowEvent", "interTimer": "intermediateCatchEvent",
               "xor": "exclusiveGateway", "and": "parallelGateway", "or": "inclusiveGateway"}
        flows = [dict(f, fid=f"Flow_{self.id}_{i+1}") for i, f in enumerate(self.flows)]
        msgs = [dict(m, mid=f"MsgFlow_{self.id}_{i+1}") for i, m in enumerate(self.msgs)]
        inc, outg = {}, {}
        for f in flows:
            outg.setdefault(f["src"], []).append(f["fid"])
            inc.setdefault(f["tgt"], []).append(f["fid"])
        x = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
             'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
             'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
             'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
             'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             f'id="Definitions_{self.id}" targetNamespace="http://upao.edu.pe/sii/s12" '
             'exporter="bpmn_gen.py" exporterVersion="1.0">']
        x.append(f'  <bpmn:collaboration id="Collab_{self.id}">')
        for p in self.pools:
            pr = "" if p["bb"] else f' processRef="Process_{p["id"]}"'
            x.append(f'    <bpmn:participant id="Part_{p["id"]}" name="{escape(p["name"])}"{pr}/>')
        for m in msgs:
            def ref(r):
                return r if r in self.nodes else f"Part_{r}"
            x.append(f'    <bpmn:messageFlow id="{m["mid"]}" name="{escape(m["label"])}" '
                     f'sourceRef="{ref(m["src"])}" targetRef="{ref(m["tgt"])}"/>')
        x.append("  </bpmn:collaboration>")
        for p in self.pools:
            if p["bb"]:
                continue
            x.append(f'  <bpmn:process id="Process_{p["id"]}" name="{escape(p["name"])}" isExecutable="false">')
            x.append(f'    <bpmn:laneSet id="LaneSet_{p["id"]}">')
            for lid, lname in p["lanes"]:
                x.append(f'      <bpmn:lane id="Lane_{lid}" name="{escape(lname)}">')
                for n in self.nodes.values():
                    if n["lane"] == lid:
                        x.append(f'        <bpmn:flowNodeRef>{n["id"]}</bpmn:flowNodeRef>')
                x.append("      </bpmn:lane>")
            x.append("    </bpmn:laneSet>")
            for n in self.nodes.values():
                if n["pool"] != p["id"]:
                    continue
                t = tag[n["kind"]]
                attrs = f'id="{n["id"]}" name="{escape(n["name"])}"'
                if n["kind"] in GATEWAYS:
                    d = "Diverging" if len(outg.get(n["id"], [])) > 1 else "Converging"
                    attrs += f' gatewayDirection="{d}"'
                body = [f"      <bpmn:incoming>{i}</bpmn:incoming>" for i in inc.get(n["id"], [])]
                body += [f"      <bpmn:outgoing>{o}</bpmn:outgoing>" for o in outg.get(n["id"], [])]
                if "Msg" in n["kind"]:
                    body.append(f'      <bpmn:messageEventDefinition id="MED_{n["id"]}"/>')
                if "Timer" in n["kind"]:
                    body.append(f'      <bpmn:timerEventDefinition id="TED_{n["id"]}"/>')
                x.append(f"    <bpmn:{t} {attrs}>")
                x.extend(body)
                x.append(f"    </bpmn:{t}>")
            for f in flows:
                if self.nodes[f["src"]]["pool"] == p["id"]:
                    x.append(f'    <bpmn:sequenceFlow id="{f["fid"]}" name="{escape(f["label"])}" '
                             f'sourceRef="{f["src"]}" targetRef="{f["tgt"]}"/>')
            x.append("  </bpmn:process>")
        # DI
        x.append(f'  <bpmndi:BPMNDiagram id="Diagram_{self.id}" name="{escape(self.name)}">')
        x.append(f'    <bpmndi:BPMNPlane id="Plane_{self.id}" bpmnElement="Collab_{self.id}">')

        def b(xx, yy, ww, hh):
            return f'<dc:Bounds x="{xx:.0f}" y="{yy:.0f}" width="{ww:.0f}" height="{hh:.0f}"/>'
        for p in self.pools:
            px, py, pw, ph = self.pool_geo[p["id"]]
            x.append(f'      <bpmndi:BPMNShape id="Part_{p["id"]}_di" bpmnElement="Part_{p["id"]}" isHorizontal="true">{b(px, py, pw, ph)}</bpmndi:BPMNShape>')
            for lid, _ in p["lanes"]:
                lx, ly, lw, lh, _ = self.lane_geo[lid]
                x.append(f'      <bpmndi:BPMNShape id="Lane_{lid}_di" bpmnElement="Lane_{lid}" isHorizontal="true">{b(lx, ly, lw, lh)}</bpmndi:BPMNShape>')
        for n in self.nodes.values():
            extra = ""
            if n["kind"] in GATEWAYS:
                extra = ' isMarkerVisible="true"'
            if n["kind"] == "subProcess":
                extra = ' isExpanded="false"'
            lab = ""
            if n["kind"] not in TASKS and n["name"]:
                lab = f'<bpmndi:BPMNLabel>{b(n["cx"] - 55, n["y"] + n["h"] + 2, 110, 28)}</bpmndi:BPMNLabel>'
            x.append(f'      <bpmndi:BPMNShape id="{n["id"]}_di" bpmnElement="{n["id"]}"{extra}>{b(n["x"], n["y"], n["w"], n["h"])}{lab}</bpmndi:BPMNShape>')
        for f in flows:
            wps = "".join(f'<di:waypoint x="{px:.0f}" y="{py:.0f}"/>' for px, py in self.edge_points(f))
            x.append(f'      <bpmndi:BPMNEdge id="{f["fid"]}_di" bpmnElement="{f["fid"]}">{wps}</bpmndi:BPMNEdge>')
        for m in msgs:
            wps = "".join(f'<di:waypoint x="{px:.0f}" y="{py:.0f}"/>' for px, py in self.msg_points(m))
            x.append(f'      <bpmndi:BPMNEdge id="{m["mid"]}_di" bpmnElement="{m["mid"]}">{wps}</bpmndi:BPMNEdge>')
        x.append("    </bpmndi:BPMNPlane>")
        x.append("  </bpmndi:BPMNDiagram>")
        x.append("</bpmn:definitions>")
        return "\n".join(x)

    def save(self, folder_bpmn, folder_svg):
        import os
        os.makedirs(folder_bpmn, exist_ok=True)
        os.makedirs(folder_svg, exist_ok=True)
        with open(os.path.join(folder_bpmn, f"{self.id}.bpmn"), "w", encoding="utf-8") as fh:
            fh.write(self.bpmn())
        with open(os.path.join(folder_svg, f"{self.id}.svg"), "w", encoding="utf-8") as fh:
            fh.write(self.svg())
