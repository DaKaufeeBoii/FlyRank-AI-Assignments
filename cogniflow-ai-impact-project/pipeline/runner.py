"""
Batch pipeline runner and executive dashboard generator.
"""
import json
import os
import sys
from pathlib import Path

from pipeline.schemas import BatchImpactReport, SeverityLevel
from pipeline.triage_engine import analyze_incident

DATA_PATH = Path("data/sample_incidents.json")
OUTPUT_DIR = Path("output")
OUTPUT_JSON = OUTPUT_DIR / "triage_report.json"
OUTPUT_HTML = OUTPUT_DIR / "dashboard.html"

def run_pipeline() -> BatchImpactReport:
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Input incidents dataset not found at {DATA_PATH}")
        
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        incidents = json.load(f)
        
    results = []
    sev_counts = {SeverityLevel.SEV1: 0, SeverityLevel.SEV2: 0, SeverityLevel.SEV3: 0, SeverityLevel.INFO: 0}
    total_latency_ms = 0.0
    
    for inc in incidents:
        res = analyze_incident(inc)
        results.append(res)
        sev_counts[res.severity] += 1
        total_latency_ms += res.processing_time_ms
        
    total_count = len(results)
    avg_latency = total_latency_ms / max(1, total_count)
    
    # ROI Economics
    # Baseline manual triage: 45 minutes (0.75 hours) per incident
    # AI pipeline triage: ~0.02 hours (human verification of drafted brief)
    # Average engineer cost: $80/hr
    # Annual volume estimate for mid-sized SaaS: 800 incidents/year
    manual_hours = total_count * 0.75
    ai_hours = total_count * 0.05
    hours_saved_batch = manual_hours - ai_hours
    
    annual_incidents = 800
    annual_hours_saved = annual_incidents * (0.75 - 0.05)
    annual_roi = annual_hours_saved * 80.0  # $44,800 annual engineering savings
    
    report = BatchImpactReport(
        total_incidents_processed=total_count,
        sev1_count=sev_counts[SeverityLevel.SEV1],
        sev2_count=sev_counts[SeverityLevel.SEV2],
        sev3_count=sev_counts[SeverityLevel.SEV3],
        info_count=sev_counts[SeverityLevel.INFO],
        average_processing_time_ms=round(avg_latency, 2),
        manual_hours_baseline=round(manual_hours, 2),
        ai_hours_spent=round(ai_hours, 2),
        hours_saved=round(hours_saved_batch, 2),
        annual_roi_projected_usd=round(annual_roi, 2),
        results=results
    )
    
    # Save JSON report
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
        
    # Render Standalone HTML Dashboard
    render_dashboard(report)
    
    print("\n" + "=" * 65)
    print("   COGNIFLOW INCIDENT TRIAGE & IMPACT PIPELINE RUN COMPLETE")
    print("=" * 65)
    print(f"Total Incidents Processed : {report.total_incidents_processed}")
    print(f"SEV-1 Outages Triaged    : {report.sev1_count}")
    print(f"SEV-2 Major Incidents    : {report.sev2_count}")
    print(f"Average Pipeline Latency : {report.average_processing_time_ms} ms")
    print(f"Manual Triage Baseline   : {report.manual_hours_baseline} hours")
    print(f"CogniFlow Triage Time    : {report.ai_hours_spent} hours")
    print(f"Hours Saved This Batch   : {report.hours_saved} hours")
    print(f"Projected Annual ROI     : ${report.annual_roi_projected_usd:,.2f} USD")
    print(f"Artifact Saved (JSON)    : {OUTPUT_JSON}")
    print(f"Artifact Saved (HTML)    : {OUTPUT_HTML}")
    print("=" * 65 + "\n")
    
    return report

def render_dashboard(r: BatchImpactReport):
    rows_html = ""
    for item in r.results:
        badge_color = {
            "SEV-1": "#ef4444",
            "SEV-2": "#f97316",
            "SEV-3": "#eab308",
            "INFO": "#3b82f6"
        }.get(item.severity.value, "#6b7280")
        
        rows_html += f"""
        <tr>
            <td style="font-weight:600;">{item.incident_id}</td>
            <td><code>{item.service}</code></td>
            <td><span style="background:{badge_color}; color:#fff; padding:3px 8px; border-radius:4px; font-size:12px; font-weight:700;">{item.severity.value}</span></td>
            <td>{item.root_cause_summary}</td>
            <td style="color:#059669; font-weight:600;">{item.sla_response_minutes} min</td>
            <td><small>{item.external_customer_update}</small></td>
            <td>{item.processing_time_ms} ms</td>
        </tr>
        """
        
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CogniFlow — Incident Triage & ROI Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 30px; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 20px; }}
  h1 {{ margin: 0; font-size: 26px; color: #38bdf8; }}
  .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
  .card {{ background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; }}
  .card-val {{ font-size: 28px; font-weight: 700; color: #f8fafc; margin-top: 5px; }}
  .card-sub {{ font-size: 13px; color: #94a3b8; }}
  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; border: 1px solid #334155; }}
  th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }}
  th {{ background: #0f172a; color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em; }}
  tr:hover {{ background: #334155; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>CogniFlow Incident Intelligence</h1>
      <p style="color:#94a3b8; margin:5px 0 0 0;">General AI Fluency Capstone Project — Sai Tarun Reddy</p>
    </div>
    <div style="text-align:right;">
      <span style="background:#0284c7; color:#fff; padding:6px 14px; border-radius:20px; font-size:13px; font-weight:600;">Status: Operational</span>
    </div>
  </div>

  <div class="metrics-grid">
    <div class="card">
      <div class="card-sub">Incidents Triaged</div>
      <div class="card-val">{r.total_incidents_processed}</div>
      <div class="card-sub">{r.sev1_count} Critical SEV-1 | {r.sev2_count} SEV-2</div>
    </div>
    <div class="card">
      <div class="card-sub">Avg AI Triage Latency</div>
      <div class="card-val" style="color:#38bdf8;">{r.average_processing_time_ms} ms</div>
      <div class="card-sub">vs 45 min manual baseline</div>
    </div>
    <div class="card">
      <div class="card-sub">Time Saved (Batch)</div>
      <div class="card-val" style="color:#4ade80;">{r.hours_saved} hrs</div>
      <div class="card-sub">93.3% reduction in triage toil</div>
    </div>
    <div class="card">
      <div class="card-sub">Projected Annual ROI</div>
      <div class="card-val" style="color:#fbbf24;">${r.annual_roi_projected_usd:,.0f}</div>
      <div class="card-sub">Based on 800 annual incidents</div>
    </div>
  </div>

  <h2 style="font-size:18px; margin: 30px 0 15px 0;">Triaged Incidents & Automated Communications</h2>
  <table>
    <thead>
      <tr>
        <th>Incident</th>
        <th>Service</th>
        <th>Severity</th>
        <th>Root Cause Summary</th>
        <th>SLA Window</th>
        <th>External Status Draft</th>
        <th>Latency</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    run_pipeline()
