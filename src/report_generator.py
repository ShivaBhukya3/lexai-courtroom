"""Generate professional HTML legal case reports."""

import base64
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


REPORT_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', Georgia, serif; background: #fff; color: #1a1a2e; line-height: 1.6; }
  .cover { background: linear-gradient(135deg, #04080f 0%, #0c1221 100%); color: #fff; padding: 80px 60px; min-height: 297mm; display: flex; flex-direction: column; justify-content: center; }
  .cover-logo { font-size: 48px; font-weight: 900; color: #c9a84c; letter-spacing: -2px; margin-bottom: 8px; }
  .cover-tagline { font-size: 16px; color: #9ca3af; margin-bottom: 60px; }
  .cover-case { font-size: 32px; font-weight: 700; color: #fff; margin-bottom: 16px; }
  .cover-meta { font-size: 14px; color: #9ca3af; margin-bottom: 8px; }
  .cover-conf { margin-top: 60px; padding: 12px 20px; border: 1px solid #c9a84c; display: inline-block; font-size: 12px; font-weight: 700; color: #c9a84c; letter-spacing: 3px; }
  .page { padding: 40px 60px; max-width: 900px; margin: 0 auto; page-break-after: always; }
  h1 { font-size: 28px; font-weight: 700; color: #1a1a2e; margin: 30px 0 10px; border-bottom: 3px solid #c9a84c; padding-bottom: 8px; }
  h2 { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 24px 0 8px; }
  h3 { font-size: 16px; font-weight: 600; color: #2c3e50; margin: 16px 0 6px; }
  p { font-size: 13px; color: #374151; margin-bottom: 12px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }
  .kpi { background: #f8f9fa; border-left: 4px solid #c9a84c; padding: 16px; border-radius: 6px; }
  .kpi-val { font-size: 28px; font-weight: 900; color: #1a1a2e; }
  .kpi-label { font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
  .verdict-box { text-align: center; padding: 40px; background: linear-gradient(135deg, #1a1a2e 0%, #2c3e50 100%); border-radius: 12px; color: #fff; margin: 20px 0; }
  .verdict-prob { font-size: 72px; font-weight: 900; letter-spacing: -3px; }
  .verdict-conviction { color: #e02424; }
  .verdict-acquittal { color: #057a55; }
  .verdict-label { font-size: 18px; font-weight: 700; margin-top: 8px; text-transform: uppercase; letter-spacing: 3px; }
  .arg-block { border-radius: 8px; padding: 20px; margin: 12px 0; }
  .arg-prosecution { background: rgba(224,36,36,0.05); border-left: 4px solid #e02424; }
  .arg-defense { background: rgba(5,122,85,0.05); border-left: 4px solid #057a55; }
  .arg-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
  .arg-prosecution .arg-title { color: #e02424; }
  .arg-defense .arg-title { color: #057a55; }
  .cite { background: #fffbeb; border: 1px solid #f59e0b; border-radius: 6px; padding: 10px 14px; margin: 8px 0; font-size: 12px; }
  .cite-name { font-weight: 700; color: #92400e; }
  .cite-principle { color: #6b7280; margin-top: 4px; }
  .evidence-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 12px; }
  .evidence-table th { background: #1a1a2e; color: #fff; padding: 10px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
  .evidence-table td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }
  .evidence-table tr:nth-child(even) td { background: #f9fafb; }
  .badge { font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 100px; display: inline-block; }
  .badge-high { background: #d1fae5; color: #065f46; }
  .badge-med { background: #fef3c7; color: #92400e; }
  .badge-low { background: #fee2e2; color: #991b1b; }
  .timeline-item { display: flex; gap: 16px; padding-bottom: 24px; position: relative; }
  .timeline-item:not(:last-child)::before { content: ''; position: absolute; left: 11px; top: 24px; bottom: 0; width: 2px; background: #c9a84c; opacity: 0.3; }
  .tl-dot { width: 24px; height: 24px; border-radius: 50%; background: #c9a84c; flex-shrink: 0; margin-top: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #000; font-weight: 700; }
  .tl-date { font-size: 11px; font-weight: 700; color: #c9a84c; text-transform: uppercase; letter-spacing: 1px; }
  .tl-event { font-size: 13px; font-weight: 600; color: #1a1a2e; margin-top: 2px; }
  .tl-desc { font-size: 12px; color: #6b7280; margin-top: 2px; }
  .footer { margin-top: 60px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 11px; color: #9ca3af; }
  @media print { .page { page-break-after: always; } }
</style>
"""


class LegalReportGenerator:
    """Generate comprehensive HTML legal case reports."""

    def generate_full_case_report(
        self,
        case_data: dict,
        prosecution_args: dict,
        defense_args: dict,
        verdict_prediction: dict,
        timeline: list[dict] | None = None,
        evidence_list: list[dict] | None = None,
    ) -> str:
        """Generate a complete professional HTML case report."""
        meta = case_data.get("metadata", case_data)
        case_id = meta.get("case_id", "UNKNOWN")
        generated_at = datetime.now().strftime("%d %B %Y, %I:%M %p")

        sections = [
            self._cover_page(meta, case_id, generated_at),
            self._executive_summary(meta),
            self._case_overview(meta, timeline or []),
            self._evidence_section(evidence_list or []),
            self._legal_framework(meta),
            self._prosecution_section(prosecution_args),
            self._defense_section(defense_args),
            self._verdict_section(verdict_prediction),
            self._recommendations_section(verdict_prediction, meta),
        ]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LexAI Case Report — {case_id}</title>
{REPORT_CSS}
</head>
<body>
{"".join(sections)}
<div class="page">
  <div class="footer">
    <p><strong>LexAI — Multimodal Courtroom Intelligence Platform</strong></p>
    <p>Generated on {generated_at} | Powered by RAG + GPT-4V + Whisper + LangChain</p>
    <p>⚠️ This report is AI-generated for legal research purposes only. Verify all information with qualified legal counsel.</p>
  </div>
</div>
</body>
</html>"""

        return html

    def _cover_page(self, meta: dict, case_id: str, generated_at: str) -> str:
        plaintiff = meta.get("plaintiff", meta.get("complainant", {}))
        plaintiff = plaintiff.get("name", "Complainant") if isinstance(plaintiff, dict) else str(plaintiff)
        defendant = meta.get("defendant", meta.get("accused", {}))
        if isinstance(defendant, dict):
            defendant = defendant.get("name", "Accused")

        return f"""
<div class="cover">
  <div class="cover-logo">⚖ LexAI</div>
  <div class="cover-tagline">Multimodal Courtroom Intelligence Platform</div>
  <div class="cover-case">LEGAL CASE REPORT</div>
  <div class="cover-meta">Case ID: <strong>{case_id}</strong></div>
  <div class="cover-meta">Court: {meta.get("court", "N/A")}</div>
  <div class="cover-meta">Case Type: {meta.get("case_type", "")} — {meta.get("sub_type", "")}</div>
  <div class="cover-meta">Status: {meta.get("status", "Active")}</div>
  <div class="cover-meta">Generated: {generated_at}</div>
  <div class="cover-conf">CONFIDENTIAL — ATTORNEY-CLIENT PRIVILEGED</div>
</div>"""

    def _executive_summary(self, meta: dict) -> str:
        charges = meta.get("charges", [])
        key_facts = meta.get("key_facts", [])
        return f"""
<div class="page">
<h1>Executive Summary</h1>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-val">{meta.get("case_type", "Case")[:8]}</div><div class="kpi-label">Case Type</div></div>
  <div class="kpi"><div class="kpi-val">{len(charges)}</div><div class="kpi-label">Charges</div></div>
  <div class="kpi"><div class="kpi-val">{len(meta.get("witnesses", []))}</div><div class="kpi-label">Witnesses</div></div>
  <div class="kpi"><div class="kpi-val">{meta.get("status", "Active")[:10]}</div><div class="kpi-label">Status</div></div>
</div>
<h2>Charges</h2>
<ul>{"".join(f"<li><p>{c}</p></li>" for c in charges)}</ul>
<h2>Key Facts</h2>
<ul>{"".join(f"<li><p>{f}</p></li>" for f in key_facts)}</ul>
</div>"""

    def _case_overview(self, meta: dict, timeline: list[dict]) -> str:
        tl_html = ""
        for i, e in enumerate(timeline[:10], 1):
            tl_html += f"""
<div class="timeline-item">
  <div class="tl-dot">{i}</div>
  <div>
    <div class="tl-date">{e.get("date", "")}</div>
    <div class="tl-event">{e.get("event", "")}</div>
    <div class="tl-desc">{e.get("legal_impact", "")}</div>
  </div>
</div>"""

        return f"""
<div class="page">
<h1>Case Overview & Timeline</h1>
<h2>Case Details</h2>
<p><strong>Case ID:</strong> {meta.get("case_id", "N/A")} &nbsp;|&nbsp; <strong>Court:</strong> {meta.get("court", "N/A")}</p>
<p><strong>Filing Date:</strong> {meta.get("filing_date", "N/A")} &nbsp;|&nbsp; <strong>Next Hearing:</strong> {meta.get("next_hearing", "N/A")}</p>
<h2>Chronological Timeline</h2>
{tl_html or "<p>No timeline data available.</p>"}
</div>"""

    def _evidence_section(self, evidence_list: list[dict]) -> str:
        rows = ""
        for e in evidence_list[:20]:
            strength = e.get("evidence_strength", 5)
            badge_cls = "badge-high" if strength >= 7 else "badge-med" if strength >= 4 else "badge-low"
            rows += f"""
<tr>
  <td>{e.get("file_name", "N/A")}</td>
  <td>{e.get("doc_type", "N/A").upper()}</td>
  <td><span class="badge {badge_cls}">{strength}/10</span></td>
  <td>{str(e.get("summary", e.get("description", "")))[:120]}</td>
</tr>"""

        return f"""
<div class="page">
<h1>Evidence Analysis</h1>
<table class="evidence-table">
<thead><tr><th>Document</th><th>Type</th><th>Strength</th><th>Summary</th></tr></thead>
<tbody>{rows or "<tr><td colspan='4'>No evidence processed yet.</td></tr>"}</tbody>
</table>
</div>"""

    def _legal_framework(self, meta: dict) -> str:
        charges = meta.get("charges", [])
        applicable = meta.get("applicable_law", [])
        all_law = list(set(charges + applicable))
        items = "".join(f"<p>• {law}</p>" for law in all_law[:10])
        return f"""
<div class="page">
<h1>Legal Framework</h1>
<h2>Applicable Law</h2>
{items or "<p>Standard Indian criminal/civil procedure.</p>"}
</div>"""

    def _prosecution_section(self, args: dict) -> str:
        opening = args.get("opening_statement", "")
        closing = args.get("closing_statement", "")
        precedents = args.get("cited_precedents", [])
        cite_html = "".join(
            f'<div class="cite"><div class="cite-name">{p if isinstance(p, str) else p.get("case_name", str(p))}</div></div>'
            for p in precedents[:5]
        )
        return f"""
<div class="page">
<h1>Prosecution Arguments</h1>
<div class="arg-block arg-prosecution">
  <div class="arg-title">Opening Statement</div>
  <p>{opening}</p>
</div>
<div class="arg-block arg-prosecution">
  <div class="arg-title">Closing Statement</div>
  <p>{closing}</p>
</div>
<h2>Cited Precedents</h2>
{cite_html or "<p>No precedents cited.</p>"}
</div>"""

    def _defense_section(self, args: dict) -> str:
        opening = args.get("opening_statement", "")
        closing = args.get("closing_statement", "")
        acquittal = args.get("acquittal_grounds", [])
        grounds_html = "".join(f"<p>• {g}</p>" for g in acquittal[:5])
        return f"""
<div class="page">
<h1>Defense Arguments</h1>
<div class="arg-block arg-defense">
  <div class="arg-title">Opening Statement</div>
  <p>{opening}</p>
</div>
<div class="arg-block arg-defense">
  <div class="arg-title">Closing Statement</div>
  <p>{closing}</p>
</div>
<h2>Grounds for Acquittal</h2>
{grounds_html or "<p>Defense strategy pending.</p>"}
</div>"""

    def _verdict_section(self, prediction: dict) -> str:
        verdict = prediction.get("verdict", "Pending")
        prob = prediction.get("conviction_probability", 0.5)
        prob_pct = f"{prob*100:.1f}%"
        color_cls = "verdict-conviction" if verdict == "Conviction" else "verdict-acquittal"
        factors = prediction.get("key_factors", [])
        factors_html = "".join(f"<p>• {f}</p>" for f in factors)

        return f"""
<div class="page">
<h1>Verdict Prediction</h1>
<div class="verdict-box">
  <div class="verdict-prob {color_cls}">{prob_pct}</div>
  <div class="verdict-label">{verdict} Probability</div>
  <p style="color:#9ca3af;margin-top:12px">Confidence: {prediction.get("confidence_level", "Medium")}</p>
</div>
<h2>Key Factors</h2>
{factors_html or "<p>Run verdict prediction for detailed analysis.</p>"}
<h2>Sentence Estimate</h2>
<p>{prediction.get("sentence_estimate", {}).get("likely", "N/A") if isinstance(prediction.get("sentence_estimate"), dict) else prediction.get("sentence_estimate", "N/A")}</p>
<h2>Bail Recommendation</h2>
<p>{prediction.get("bail_recommendation", "N/A")}</p>
</div>"""

    def _recommendations_section(self, prediction: dict, meta: dict) -> str:
        appeal_grounds = prediction.get("appeal_grounds", [])
        grounds_html = "".join(f"<p>• {g}</p>" for g in appeal_grounds)
        return f"""
<div class="page">
<h1>Strategic Recommendations</h1>
<h2>Immediate Actions</h2>
<p>1. Secure all original evidence documents with proper chain of custody.</p>
<p>2. File bail application if accused is in custody.</p>
<p>3. Obtain certified copies of all revenue/bank records.</p>
<p>4. Brief witnesses and prepare them for examination.</p>
<h2>Appeal Grounds (if needed)</h2>
{grounds_html or "<p>Appeal strategy to be determined post-verdict.</p>"}
<h2>Case Strategy</h2>
<p>Based on AI analysis, the {prediction.get("verdict", "outcome")} prediction carries
{prediction.get("confidence_level", "medium")} confidence. Focus on the key battlegrounds
identified in the argument strength comparison.</p>
</div>"""

    def generate_court_filing_draft(self, case_data: dict, filing_type: str) -> str:
        """Draft common court filings."""
        meta = case_data.get("metadata", case_data)
        templates = {
            "bail_application": self._bail_application_template(meta),
            "written_statement": self._written_statement_template(meta),
        }
        return templates.get(filing_type.lower(), f"Filing type '{filing_type}' not supported.")

    def _bail_application_template(self, meta: dict) -> str:
        accused = meta.get("accused", meta.get("defendant", {}))
        if isinstance(accused, dict):
            accused_name = accused.get("name", "the Accused")
        else:
            accused_name = str(accused)

        return f"""
IN THE COURT OF {meta.get("court", "THE HON'BLE COURT").upper()}

BAIL APPLICATION U/S 437/439 CrPC

IN THE MATTER OF:

FIR/Case No.: {meta.get("case_id", meta.get("fir_number", "N/A"))}
Police Station: {meta.get("police_station", "N/A")}

IN THE MATTER OF:
{accused_name} ... APPLICANT/ACCUSED

VERSUS

State of Maharashtra ... RESPONDENT

BAIL APPLICATION

The Applicant above-named most respectfully submits:

1. That the Applicant has been arrested in connection with the above FIR and is presently in judicial custody.

2. That the allegations against the Applicant are false and frivolous and have been made with mala fide intentions.

3. That the Applicant is a permanent resident and there is no likelihood of the Applicant fleeing justice.

4. That the Applicant undertakes to co-operate with the investigation and shall not tamper with evidence or influence witnesses.

5. That no useful purpose would be served by continued detention of the Applicant.

PRAYER:
It is therefore humbly prayed that this Hon'ble Court may graciously be pleased to:
(a) Release the Applicant on bail on such terms and conditions as this Hon'ble Court may deem fit;
(b) Pass such other and further orders as this Hon'ble Court may deem fit and proper.

Date: {datetime.now().strftime("%d/%m/%Y")}
Place: [City]

APPLICANT/ACCUSED
Through: Advocate
"""

    def _written_statement_template(self, meta: dict) -> str:
        return f"""
IN THE COURT OF {meta.get("court", "THE HON'BLE COURT").upper()}

CIVIL SUIT NO. _____ OF _____

[Plaintiff Name] ... PLAINTIFF
VERSUS
[Defendant Name] ... DEFENDANT

WRITTEN STATEMENT OF THE DEFENDANT

The Defendant above named most respectfully submits as under:

PRELIMINARY OBJECTIONS:
1. The Plaint is not maintainable in law and on facts.
2. The Suit is barred by limitation.
3. The Plaintiff has no cause of action against the Defendant.

ON MERITS:
1. The Defendant denies all the allegations made in the Plaint except those specifically admitted herein.

PRAYER:
The Defendant humbly prays that this Hon'ble Court may be pleased to:
(a) Dismiss the Suit with costs;
(b) Pass such other orders as deemed fit.

Date: {datetime.now().strftime("%d/%m/%Y")}
DEFENDANT
Through Advocate
"""
