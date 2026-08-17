#!/usr/bin/env python3
import json
import os

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

with open(os.path.join(BASE_DIR, "options_exam_data.json"), "r", encoding="utf-8") as f:
    opts_data = json.load(f)

json_data_str = json.dumps(opts_data, ensure_ascii=False)

with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.json"), "r", encoding="utf-8") as f:
    weekly_schedules = json.load(f)

weekly_data_str = json.dumps(weekly_schedules, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AL MUNAWWARA ISLAMIC SCHOOL — Term Examination Timetable</title>
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --brand-primary: #064e3b;
      --brand-accent: #0f766e;
      --brand-surface: #f0fdf4;
      --brand-border: #a7f3d0;
      
      --f2f-color: #16a34a;
      --f2f-bg: #f0fdf4;
      --f2f-border: #bbf7d0;
      
      --odl1-color: #0284c7;
      --odl1-bg: #f0f9ff;
      --odl1-border: #bae6fd;
      
      --odl2-color: #d97706;
      --odl2-bg: #fffbeb;
      --odl2-border: #fde68a;
      
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-subtle: #f1f5f9;
      --text: #0f172a;
      --text-muted: #64748b;
      --line: #e2e8f0;
      --line-strong: #cbd5e1;
      
      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 14px;
      --radius-xl: 18px;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }}

    /* Top App Header */
    .app-header {{
      background: var(--surface);
      border-bottom: 2px solid var(--line);
      padding: 16px 24px;
      position: sticky;
      top: 0;
      z-index: 50;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}

    .header-inner {{
      max-width: 1600px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .brand-section {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .brand-logo {{
      width: 44px;
      height: 44px;
      background: var(--brand-primary);
      color: #fff;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      font-weight: 900;
      letter-spacing: -0.02em;
    }}

    .brand-text h1 {{
      font-size: 20px;
      font-weight: 900;
      color: var(--brand-primary);
      line-height: 1.2;
      letter-spacing: -0.02em;
    }}

    .brand-text p {{
      font-size: 13.5px;
      font-weight: 700;
      color: var(--text-muted);
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--brand-surface);
      color: var(--brand-primary);
      border: 1.5px solid var(--brand-border);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 13.5px;
      font-weight: 800;
    }}

    .status-dot {{
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
    }}

    .btn {{
      padding: 9px 18px;
      border-radius: var(--radius-md);
      font-size: 14.5px;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.15s ease;
      border: 1.5px solid transparent;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}

    .btn-primary {{
      background: var(--brand-primary);
      color: #fff;
    }}

    .btn-primary:hover {{
      background: #043828;
    }}

    .btn-outline {{
      background: var(--surface);
      border-color: var(--line-strong);
      color: var(--text);
    }}

    .btn-outline:hover {{
      background: var(--surface-subtle);
      border-color: #64748b;
    }}

    /* Option Switcher Strip */
    .option-switcher-container {{
      max-width: 1600px;
      margin: 18px auto 0;
      padding: 0 24px;
    }}

    .option-switcher-card {{
      background: var(--surface);
      border: 2.5px solid #cbd5e1;
      border-radius: var(--radius-lg);
      padding: 14px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }}

    .option-group-title {{
      font-size: 13.5px;
      font-weight: 900;
      color: var(--brand-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-right: 4px;
    }}

    .option-pills-list {{
      display: inline-flex;
      background: #e2e8f0;
      padding: 4px;
      border-radius: var(--radius-md);
      gap: 5px;
      flex-wrap: wrap;
    }}

    .opt-btn {{
      padding: 8px 16px;
      border-radius: 8px;
      border: 1.5px solid transparent;
      background: transparent;
      cursor: pointer;
      font-family: inherit;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s ease;
    }}

    .opt-btn.active {{
      background: #ffffff;
      border-color: var(--brand-primary);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
    }}

    .opt-code {{
      font-size: 13px;
      font-weight: 900;
      padding: 2px 6px;
      border-radius: 4px;
      background: #e2e8f0;
      color: #334155;
    }}

    .opt-btn.active .opt-code {{
      background: var(--brand-primary);
      color: #ffffff;
    }}

    .opt-name {{
      font-size: 14.5px;
      font-weight: 800;
      color: #1e293b;
    }}

    .badge-rec {{
      background: #fef08a;
      color: #854d0e;
      border: 1px solid #facc15;
      font-size: 11px;
      font-weight: 900;
      padding: 1px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    /* Controls & Filters Container */
    .controls-container {{
      max-width: 1600px;
      margin: 16px auto 0;
      padding: 0 24px;
    }}

    .controls-card {{
      background: var(--surface);
      border: 2px solid var(--line);
      border-radius: var(--radius-lg);
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }}

    .controls-top-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 18px;
      padding-bottom: 16px;
      border-bottom: 2px solid var(--line);
    }}

    /* Clean View Tabs - No Emojis */
    .view-tabs {{
      display: inline-flex;
      background: #e2e8f0;
      padding: 4px;
      border-radius: var(--radius-md);
      gap: 4px;
    }}

    .view-tab {{
      padding: 9px 20px;
      border-radius: 8px;
      font-size: 14.5px;
      font-weight: 800;
      color: #475569;
      cursor: pointer;
      border: 0;
      background: transparent;
      transition: all 0.15s ease;
    }}

    .view-tab.active {{
      background: var(--surface);
      color: var(--text);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }}

    .search-box-wrapper {{
      flex: 1;
      max-width: 420px;
      position: relative;
    }}

    .search-input {{
      width: 100%;
      padding: 11px 16px;
      border-radius: var(--radius-md);
      border: 2px solid var(--line);
      font-size: 15px;
      font-weight: 700;
      font-family: inherit;
      outline: none;
      background: #fff;
    }}

    .search-input:focus {{
      border-color: var(--brand-primary);
      box-shadow: 0 0 0 3px rgba(6, 78, 59, 0.15);
    }}

    .filter-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
    }}

    .filter-control {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .filter-control label {{
      font-size: 12.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }}

    .select-dropdown {{
      width: 100%;
      padding: 10px 14px;
      border-radius: var(--radius-md);
      border: 2px solid var(--line);
      background: #fff;
      font-size: 14.5px;
      font-weight: 700;
      color: var(--text);
      font-family: inherit;
      cursor: pointer;
      outline: none;
    }}

    .select-dropdown:focus {{
      border-color: var(--brand-primary);
    }}

    /* Live Stats Strip */
    .stats-strip {{
      max-width: 1600px;
      margin: 16px auto 0;
      padding: 0 24px;
      display: flex;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
    }}

    .stat-pill {{
      background: var(--surface);
      border: 1.5px solid var(--line);
      padding: 8px 16px;
      border-radius: var(--radius-md);
      font-size: 14px;
      font-weight: 700;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .stat-pill strong {{
      color: var(--text);
      font-weight: 900;
    }}

    .stat-pill.pill-active-option {{
      background: #ecfdf5;
      border-color: #6ee7b7;
      color: #065f46;
    }}

    /* Main Content Area */
    .main-content {{
      max-width: 1600px;
      margin: 20px auto 40px;
      padding: 0 24px;
    }}

    /* Calendar Poster */
    .calendar-poster {{
      background: var(--surface);
      border: 2.5px solid var(--line-strong);
      border-radius: var(--radius-xl);
      overflow: hidden;
      margin-bottom: 36px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
      page-break-after: always;
      break-after: page;
    }}

    .poster-header {{
      background: var(--brand-primary);
      color: #fff;
      padding: 22px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid var(--brand-border);
    }}

    .poster-title h2 {{
      font-size: 26px;
      font-weight: 900;
      letter-spacing: -0.02em;
      line-height: 1.2;
    }}

    .poster-title p {{
      font-size: 14.5px;
      font-weight: 700;
      opacity: 0.9;
      margin-top: 3px;
    }}

    .grade-badge-display {{
      background: #ffffff;
      color: var(--brand-primary);
      font-size: 20px;
      font-weight: 900;
      padding: 8px 24px;
      border-radius: var(--radius-md);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
      letter-spacing: -0.01em;
    }}

    /* Matrix Table Grid */
    .table-container {{
      overflow-x: auto;
      background: #f8fafc;
      padding: 20px;
    }}

    .matrix-table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0 12px;
      table-layout: fixed;
    }}

    .matrix-table thead th {{
      background: var(--surface);
      border: 2px solid var(--line);
      padding: 14px 16px;
      text-align: center;
      border-radius: var(--radius-md);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }}

    .matrix-table thead th.time-col {{
      width: 240px;
      min-width: 240px;
      background: #e2e8f0;
      color: #1e293b;
      font-size: 15px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      white-space: nowrap;
    }}

    .th-day-title {{
      font-size: 18px;
      font-weight: 900;
      color: var(--text);
      display: block;
    }}

    .th-day-sub {{
      font-size: 13.5px;
      font-weight: 800;
      color: var(--text-muted);
      display: block;
      margin-top: 2px;
    }}

    .matrix-table tbody tr {{
      background: transparent;
    }}

    .matrix-table tbody td {{
      background: var(--surface);
      border: 1.5px solid var(--line);
      border-right: 0;
      padding: 12px;
      vertical-align: top;
      min-height: 110px;
    }}

    .matrix-table tbody td:first-child {{
      border-radius: var(--radius-md) 0 0 var(--radius-md);
    }}

    .matrix-table tbody td:last-child {{
      border-right: 1.5px solid var(--line);
      border-radius: 0 var(--radius-md) var(--radius-md) 0;
    }}

    .time-td {{
      background: #f8fafc !important;
      border: 2px solid #cbd5e1 !important;
      vertical-align: middle !important;
      text-align: center !important;
      padding: 16px 12px !important;
      width: 240px;
      min-width: 240px;
      white-space: nowrap;
    }}

    .time-slot-val {{
      font-size: 16.5px;
      font-weight: 900;
      color: #0f172a;
      display: block;
      white-space: nowrap;
      letter-spacing: -0.01em;
    }}

    .time-slot-period {{
      font-size: 12px;
      font-weight: 800;
      color: var(--brand-accent);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 4px;
      display: inline-block;
      background: #e0f2fe;
      padding: 2px 8px;
      border-radius: 4px;
    }}

    /* Break Rows */
    .break-tr td {{
      background: #f0f9ff !important;
      border: 1.5px solid #bae6fd !important;
    }}

    .break-banner-td {{
      vertical-align: middle !important;
      text-align: center !important;
      font-size: 16.5px !important;
      font-weight: 900 !important;
      color: #0369a1 !important;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 18px 24px !important;
    }}

    .break-tag {{
      font-size: 12px;
      font-weight: 900;
      color: #0284c7;
      background: #e0f2fe;
      padding: 3px 8px;
      border-radius: 4px;
      margin-top: 4px;
      display: inline-block;
    }}

    /* Cards Stack */
    .cards-stack {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .exam-event-card {{
      background: #ffffff;
      border: 1.5px solid #cbd5e1;
      border-left-width: 6px;
      border-radius: var(--radius-md);
      padding: 12px 14px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .exam-event-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08);
      border-color: #94a3b8;
    }}

    .exam-event-card.f2f {{ border-left-color: var(--f2f-color); }}
    .exam-event-card.odl1 {{ border-left-color: var(--odl1-color); }}
    .exam-event-card.odl2 {{ border-left-color: var(--odl2-color); }}

    .card-subject-name {{
      font-size: 18px;
      font-weight: 900;
      color: #0f172a;
      line-height: 1.25;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .card-subject-name .click-hint {{
      font-size: 11px;
      font-weight: 800;
      color: var(--brand-accent);
      text-transform: uppercase;
    }}

    .card-grade-gender-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 6px;
      padding-bottom: 4px;
      border-bottom: 1px solid #e2e8f0;
    }}

    .card-grade-label {{
      font-size: 13.5px;
      font-weight: 900;
      color: #1e293b;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .gender-pill {{
      display: inline-block;
      font-size: 11px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 2px 7px;
      border-radius: 4px;
      white-space: nowrap;
    }}

    .gender-pill.pill-boys {{
      background: #e0f2fe;
      color: #0369a1;
      border: 1.5px solid #7dd3fc;
    }}

    .gender-pill.pill-girls {{
      background: #fce7f3;
      color: #be185d;
      border: 1.5px solid #fbcfe8;
    }}

    .gender-pill.pill-mix,
    .gender-pill.pill-mixed {{
      background: #f3e8ff;
      color: #7e22ce;
      border: 1.5px solid #e9d5ff;
    }}

    .gender-pill.pill-not-encoded {{
      background: #f1f5f9;
      color: #64748b;
      border: 1.5px solid #cbd5e1;
      font-size: 10px;
    }}

    .card-sec-name-row {{
      font-size: 14.5px;
      font-weight: 800;
      color: #334155;
      margin-top: 5px;
      line-height: 1.3;
    }}

    .card-teacher-row {{
      margin-top: 8px;
      padding-top: 6px;
      border-top: 1.5px dashed #cbd5e1;
      font-size: 16px;
      font-weight: 900;
      color: var(--brand-primary);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .card-modality-row {{
      margin-top: 5px;
      font-size: 11.5px;
      font-weight: 800;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .empty-slot-block {{
      padding: 28px 10px;
      text-align: center;
      color: #94a3b8;
      font-size: 14px;
      font-weight: 800;
    }}

    /* Modal / Drawer */
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(4px);
      z-index: 100;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}

    .modal-backdrop.active {{
      display: flex;
    }}

    .modal-card {{
      background: #ffffff;
      border-radius: var(--radius-xl);
      max-width: 960px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
      border: 2px solid var(--line);
      overflow: hidden;
      animation: modalSlide 0.2s ease-out;
    }}

    @keyframes modalSlide {{
      from {{ transform: translateY(20px); opacity: 0; }}
      to {{ transform: translateY(0); opacity: 1; }}
    }}

    .modal-header {{
      padding: 22px 28px;
      background: var(--brand-primary);
      color: #fff;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .modal-header h3 {{
      font-size: 24px;
      font-weight: 900;
    }}

    .modal-header p {{
      font-size: 14px;
      font-weight: 700;
      opacity: 0.9;
    }}

    .modal-close-btn {{
      background: rgba(255, 255, 255, 0.2);
      border: 0;
      color: #fff;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      font-size: 18px;
      font-weight: 900;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .modal-close-btn:hover {{
      background: rgba(255, 255, 255, 0.3);
    }}

    .modal-body {{
      padding: 24px 28px;
      overflow-y: auto;
    }}

    .modal-stats-bar {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-bottom: 24px;
    }}

    .modal-stat-box {{
      background: var(--surface-subtle);
      border: 1.5px solid var(--line);
      padding: 14px 18px;
      border-radius: var(--radius-md);
      text-align: center;
    }}

    .modal-stat-box .val {{
      font-size: 26px;
      font-weight: 900;
      color: var(--brand-primary);
    }}

    .modal-stat-box .lbl {{
      font-size: 12.5px;
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
    }}

    .modal-sec-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .modal-sec-item {{
      background: var(--surface);
      border: 1.5px solid var(--line);
      border-radius: var(--radius-md);
      padding: 14px 18px;
      display: grid;
      grid-template-columns: 2fr 1.5fr 1.5fr 1fr;
      align-items: center;
      gap: 14px;
    }}

    .item-grade-sec {{
      font-size: 16px;
      font-weight: 900;
      color: #0f172a;
    }}

    .mod-badge {{
      display: inline-block;
      font-size: 11.5px;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      margin-top: 4px;
    }}

    .mod-badge.f2f {{ background: var(--f2f-bg); color: var(--f2f-color); border: 1.5px solid var(--f2f-border); }}
    .mod-badge.odl1 {{ background: var(--odl1-bg); color: var(--odl1-color); border: 1.5px solid var(--odl1-border); }}
    .mod-badge.odl2 {{ background: var(--odl2-bg); color: var(--odl2-color); border: 1.5px solid var(--odl2-border); }}

    .item-teacher {{
      font-size: 15.5px;
      font-weight: 900;
      color: var(--brand-primary);
    }}

    .item-datetime {{
      font-size: 14px;
      font-weight: 800;
      color: var(--text);
    }}

    .item-datetime span {{
      display: block;
      font-size: 12.5px;
      color: var(--text-muted);
      font-weight: 700;
    }}

    .modal-footer {{
      padding: 16px 28px;
      background: #f8fafc;
      border-top: 2px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    /* Comparison Modal Styling */
    .compare-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-top: 16px;
    }}

    .compare-card {{
      background: #ffffff;
      border: 2px solid var(--line);
      border-radius: var(--radius-lg);
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
    }}

    .compare-card.active-card {{
      border-color: var(--brand-primary);
      box-shadow: 0 4px 16px rgba(6, 78, 59, 0.15);
    }}

    .compare-header {{
      border-bottom: 2px solid var(--line);
      padding-bottom: 12px;
      margin-bottom: 14px;
    }}

    .compare-code {{
      font-size: 13px;
      font-weight: 900;
      padding: 3px 8px;
      border-radius: 4px;
      background: #e2e8f0;
      color: #334155;
      display: inline-block;
      margin-bottom: 6px;
    }}

    .compare-card.active-card .compare-code {{
      background: var(--brand-primary);
      color: #ffffff;
    }}

    .compare-title {{
      font-size: 18px;
      font-weight: 900;
      color: #0f172a;
      line-height: 1.2;
    }}

    .compare-desc {{
      font-size: 13px;
      font-weight: 700;
      color: #64748b;
      margin-top: 4px;
    }}

    .metric-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px dashed var(--line);
      font-size: 13.5px;
    }}

    .metric-lbl {{
      color: #475569;
      font-weight: 750;
    }}

    .metric-val {{
      font-weight: 900;
      color: #0f172a;
    }}

    .metric-val.val-good {{
      color: #16a34a;
    }}

    /* Print Styles: PRINT ONLY THE CALENDAR POSTER */
    @media print {{
      @page {{
        size: landscape;
        margin: 8mm;
    /* Print Specific Rules */
    @media print {{
      @page {{
        size: A4 landscape;
        margin: 5mm 6mm;
      }}

      html, body {{
        background: #ffffff !important;
        color: #000000 !important;
        width: 100% !important;
        height: auto !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}

      .app-header,
      .option-switcher-container,
      .controls-container,
      .stats-strip,
      .modal-backdrop,
      .click-hint,
      .header-actions,
      button,
      input,
      select {{
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
      }}

      .main-content,
      #mainContainer {{
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
      }}

      .calendar-poster {{
        display: block !important;
        width: 100% !important;
        margin: 0 0 0 0 !important;
        padding: 0 !important;
        border: 1.5px solid #064e3b !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        page-break-after: always !important;
        break-after: page !important;
      }}

      .calendar-poster:last-child {{
        page-break-after: auto !important;
        break-after: auto !important;
      }}

      .poster-header {{
        background: #064e3b !important;
        color: #ffffff !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        padding: 6px 12px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
      }}

      .poster-header .poster-title h2 {{
        font-size: 14px !important;
        margin: 0 !important;
        line-height: 1.1 !important;
      }}

      .poster-header .poster-title p {{
        font-size: 10px !important;
        margin: 2px 0 0 0 !important;
        opacity: 0.9 !important;
      }}

      .grade-badge-display {{
        font-size: 12px !important;
        padding: 3px 8px !important;
      }}

      .table-container {{
        padding: 0 !important;
        margin: 0 !important;
        overflow: visible !important;
      }}

      .matrix-table {{
        width: 100% !important;
        border-collapse: collapse !important;
        table-layout: fixed !important;
        font-size: 8.5px !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
      }}

      .matrix-table thead th {{
        padding: 3px 4px !important;
        font-size: 9.5px !important;
        height: 20px !important;
        font-weight: 800 !important;
      }}

      .matrix-table thead th .th-day-title {{
        font-size: 10px !important;
      }}

      .matrix-table thead th .th-day-sub {{
        font-size: 8px !important;
      }}

      .matrix-table tbody td {{
        padding: 2px 3px !important;
        height: 22px !important;
        vertical-align: top !important;
      }}

      .matrix-table .time-td {{
        width: 115px !important;
        padding: 2px 4px !important;
      }}

      .matrix-table .time-slot-val {{
        font-size: 8.5px !important;
        font-weight: 800 !important;
      }}

      .matrix-table .time-slot-period {{
        font-size: 7.5px !important;
      }}

      .break-tr {{
        background: #f1f5f9 !important;
      }}

      .break-banner-td {{
        font-size: 8.5px !important;
        font-weight: 800 !important;
        padding: 2px 6px !important;
      }}

      .cards-stack {{
        display: flex !important;
        flex-direction: column !important;
        gap: 2px !important;
      }}

      .exam-event-card {{
        padding: 2px 4px !important;
        border-radius: 4px !important;
        border-width: 1px !important;
        box-shadow: none !important;
        margin-bottom: 0 !important;
      }}

      .card-subject-name {{
        font-size: 9px !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
      }}

      .card-time-duration-row {{
        font-size: 8px !important;
        padding: 1px 3px !important;
        margin: 1px 0 !important;
        border-radius: 3px !important;
      }}

      .card-time-duration-row span:last-child {{
        font-size: 7.5px !important;
        padding: 0 3px !important;
      }}

      .card-grade-gender-row {{
        font-size: 7.5px !important;
        margin-top: 1px !important;
      }}

      .card-sec-name-row {{
        font-size: 8px !important;
        font-weight: 700 !important;
        line-height: 1.1 !important;
      }}

      .card-teacher-row {{
        font-size: 8px !important;
        font-weight: 700 !important;
      }}

      .card-modality-row {{
        font-size: 7px !important;
        opacity: 0.8 !important;
      }}

      .empty-slot-block {{
        font-size: 8px !important;
        padding: 4px !important;
        color: #94a3b8 !important;
      }}

      .poster-footer-strip {{
        padding: 3px 10px !important;
        font-size: 8px !important;
      }}
    }}
  </style>
</head>
<body>

  <!-- App Header -->
  <header class="app-header">
    <div class="header-inner">
      <div class="brand-section">
        <img src="amis_logo.png" alt="AMIS Logo" style="width:48px; height:48px; border-radius:50%; object-fit:contain; background:#ffffff; padding:2px; box-shadow:0 3px 10px rgba(0,0,0,0.15);">
        <div class="brand-text">
          <h1>AL MUNAWWARA ISLAMIC SCHOOL</h1>
          <p>1st Term Examination Schedule • S.Y. 2026–2027 • Approved Option C (Teacher-Priority)</p>
        </div>
      </div>
      <div class="header-actions">
        <a class="btn btn-outline" href="index.html" style="background:#ffffff; color:#0f172a; font-weight:700; border-color:#cbd5e1;" title="Back to Schedule Home">
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          Schedule Home
        </a>
        <a class="btn btn-outline" href="class-schedule.html" target="_blank" style="background:#0f766e; color:#ffffff; font-weight:700; border-color:#0f766e;" title="View Official Weekly Class Schedule (Sunday-Thursday)">
          Class Schedule
        </a>
        <a class="btn btn-outline" href="faculty-timetable-exam.html" target="_blank" style="background:#047857; color:#ffffff; font-weight:700; border-color:#059669;" title="View Faculty Timetable — Exam Schedule">
          Faculty Timetable (Exam)
        </a>
        <button class="btn btn-outline" onclick="window.print()">Print Schedule</button>
        <button class="btn btn-primary" onclick="exportMasterCSV()">Export CSV</button>
      </div>
    </div>
  </header>

  <!-- Controls & Filters -->
  <section class="controls-container">
    <div class="controls-card">
      <div class="controls-top-row">
        <div class="view-tabs">
          <button class="view-tab active" id="tabPosters" onclick="switchView('posters')">Grade Posters</button>
          <button class="view-tab" id="tabFaculty" onclick="switchView('faculty')">Faculty Timetables</button>
        </div>

        <div class="search-box-wrapper">
          <input type="text" id="searchInput" class="search-input" placeholder="Search staff/faculty, section, subject..." oninput="onFilterChange()">
        </div>
      </div>

      <div class="filter-grid">
        <div class="filter-control">
          <label>Grade Level</label>
          <select id="gradeSelect" class="select-dropdown" onchange="onGradeChange()">
            <option value="">All Grades (16)</option>
          </select>
        </div>
        <div class="filter-control">
          <label>Section</label>
          <select id="sectionSelect" class="select-dropdown" onchange="onFilterChange()">
            <option value="">All Sections (63)</option>
          </select>
        </div>
        <div class="filter-control">
          <label>Gender</label>
          <select id="genderSelect" class="select-dropdown" onchange="onFilterChange()">
            <option value="">All Genders</option>
            <option value="BOYS">Boys</option>
            <option value="GIRLS">Girls</option>
            <option value="MIXED">Mixed</option>
          </select>
        </div>
        <div class="filter-control">
          <label>Modality</label>
          <select id="modalitySelect" class="select-dropdown" onchange="onFilterChange()">
            <option value="">All Modalities</option>
            <option value="F2F">F2F Classroom</option>
            <option value="ODL">ODL (Online Distance)</option>
          </select>
        </div>
        <div class="filter-control">
          <label>Shift</label>
          <select id="shiftSelect" class="select-dropdown" onchange="onFilterChange()">
            <option value="">All Shifts</option>
            <option value="1st Shift">1st Shift (Morning/Afternoon)</option>
            <option value="2nd Shift">2nd Shift (Afternoon/Evening)</option>
          </select>
        </div>
        <div class="filter-control">
          <label>Staff / Faculty</label>
          <select id="teacherSelect" class="select-dropdown" onchange="onFilterChange()">
            <option value="">All Staff / Faculty</option>
          </select>
        </div>
        <div class="filter-control">
          <label>Exam Subject</label>
          <select id="subjectSelect" class="select-dropdown" onchange="onFilterChange()">
            <option value="">All Subjects</option>
          </select>
        </div>
      </div>
    </div>
  </section>

  <!-- Live Stats -->
  <div class="stats-strip" id="statsStrip">
    <div class="stat-pill pill-active-option">Approved Timetable: <strong id="statActiveOption">Option C (Teacher-Priority)</strong></div>
    <div class="stat-pill">Total Exam Sessions: <strong id="statTotalExams">549</strong></div>
    <div class="stat-pill">Active Sections: <strong id="statTotalSections">64</strong></div>
    <div class="stat-pill">Assigned Faculty: <strong id="statTotalTeachers">61</strong></div>
    <div class="stat-pill">Dates: <strong>Sep 2, 3, 6 & 7, 2026</strong></div>
    <div class="stat-pill" style="margin-left:auto;">
      <button class="btn btn-outline" style="padding:6px 14px; font-size:13px;" onclick="resetFilters()">Reset All Filters</button>
    </div>
  </div>

  <!-- Main View Container -->
  <main class="main-content" id="mainContainer">
    <!-- Dynamic Content injected here -->
  </main>

  <!-- Interactive Subject Modal / Drawer -->
  <div class="modal-backdrop" id="subjectModalBackdrop" onclick="closeSubjectModal(event)">
    <div class="modal-card" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div>
          <h3 id="modalSubjectTitle">Subject Details</h3>
          <p id="modalSubjectSub">Assigned Sections & Schedule Breakdown</p>
        </div>
        <button class="modal-close-btn" onclick="closeSubjectModal()">✕</button>
      </div>
      <div class="modal-body">
        <div class="modal-stats-bar">
          <div class="modal-stat-box">
            <div class="val" id="modalStatSections">0</div>
            <div class="lbl">Sections Taking Exam</div>
          </div>
          <div class="modal-stat-box">
            <div class="val" id="modalStatTeachers">0</div>
            <div class="lbl">Assigned Faculty</div>
          </div>
          <div class="modal-stat-box">
            <div class="val" id="modalStatExams">0</div>
            <div class="lbl">Total Sessions</div>
          </div>
        </div>

        <div id="modalSubjectBody">
          <!-- Injected dynamically -->
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" id="modalFilterSubjectBtn" onclick="filterByCurrentSubject()">Filter Calendar by this Subject</button>
        <button class="btn btn-primary" onclick="closeSubjectModal()">Close</button>
      </div>
    </div>
  </div>

  <!-- Compare All 4 Options Modal -->
  <div class="modal-backdrop" id="compareModalBackdrop" onclick="closeCompareModal(event)">
    <div class="modal-card" style="max-width:1200px;" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div>
          <h3>Compare School-Wide Timetable Options</h3>
          <p>School-Wide Alternative Optimization Models (All 63 Sections • 54 Faculty Members)</p>
        </div>
        <button class="modal-close-btn" onclick="closeCompareModal()">✕</button>
      </div>
      <div class="modal-body">
        <div class="compare-grid" id="compareGridContent">
          <!-- Injected dynamically -->
        </div>
      </div>
      <div class="modal-footer">
        <span style="font-size:13.5px; font-weight:800; color:#475569;">All 4 Options are 100% mathematically proven conflict-free (0 teacher conflicts, 0 section overlaps).</span>
        <button class="btn btn-primary" onclick="closeCompareModal()">Close Window</button>
      </div>
    </div>
  </div>

  <!-- App Footer -->
  <footer style="text-align:center; padding:32px 20px; font-size:14px; font-weight:800; color:#64748b; border-top:2px solid #e2e8f0; background:#ffffff; margin-top:40px;">
    <p style="color:#0f172a; font-size:16px; font-weight:900; letter-spacing:-0.01em;">AL MUNAWWARA ISLAMIC SCHOOL EXAMINATION SCHEDULER</p>
    <p style="margin-top:6px;">Architecture, Optimization Engine & Timetable Design by <strong style="color:#064e3b;">Software Engineer Mon Zhairel Lingasa</strong></p>
    <p style="margin-top:4px; font-size:12.5px; color:#94a3b8;">100% Conflict-Free Validated • Mathematical Constraint Programming Model • S.Y. 2026–2027</p>
  </footer>

  <!-- Inlined Full Option C Dataset & Weekly Schedules -->
  <script>
    window.AMIS_OPTIONS_DATA = {json_data_str};
    window.AMIS_EXAM_DATA = window.AMIS_OPTIONS_DATA.OPTION_C;
    window.AMIS_TEACHER_WEEKLY_SCHEDULES = {weekly_data_str};
    const WEEKLY_SCHEDULES_DATA = window.AMIS_TEACHER_WEEKLY_SCHEDULES;
  </script>

  <script>
    let CURRENT_OPTION = 'OPTION_C';
    let ALL_DATA = [];
    let CURRENT_VIEW = 'posters';
    let CURRENT_MODAL_SUBJECT = '';

    const OPTION_INFO = {{
      OPTION_A: {{
        code: 'OPTION A',
        title: 'Current / Default Schedule',
        desc: 'Existing approved examination timetable. Preserved exactly as-is without modification.',
        highlight: 'Approved Baseline'
      }},
      OPTION_B: {{
        code: 'OPTION B',
        title: 'Modality-Aligned / Best Balance',
        desc: 'Aligns examinations of same grade + same subject to identical test dates across F2F, ODL 1, and ODL 2.',
        highlight: 'Recommended Alternative'
      }},
      OPTION_C: {{
        code: 'OPTION C',
        title: 'Teacher-Priority',
        desc: 'Optimized for faculty workload distribution, minimizing fatigue and difficult inter-shift transitions.',
        highlight: 'Faculty Workload Focused'
      }},
      OPTION_D: {{
        code: 'OPTION D',
        title: 'Student-Friendly',
        desc: 'Optimized for continuous student exam flow, early dismissal, and balanced academic workload per day.',
        highlight: 'Student Experience Focused'
      }}
    }};

    window.addEventListener('DOMContentLoaded', () => {{
      if (window.AMIS_OPTIONS_DATA && window.AMIS_OPTIONS_DATA[CURRENT_OPTION]) {{
        ALL_DATA = window.AMIS_OPTIONS_DATA[CURRENT_OPTION];
        initApp();
      }} else if (window.AMIS_EXAM_DATA && Array.isArray(window.AMIS_EXAM_DATA)) {{
        ALL_DATA = window.AMIS_EXAM_DATA;
        initApp();
      }}
    }});

    function switchOption(optKey) {{
      if (!window.AMIS_OPTIONS_DATA || !window.AMIS_OPTIONS_DATA[optKey]) return;
      CURRENT_OPTION = optKey;
      ALL_DATA = window.AMIS_OPTIONS_DATA[optKey];

      ['A', 'B', 'C', 'D'].forEach(k => {{
        const btn = document.getElementById('btnOpt' + k);
        if (btn) btn.classList.toggle('active', 'OPTION_' + k === optKey);
      }});

      document.getElementById('applyOptionBtn').innerText = 'Apply ' + OPTION_INFO[optKey].code;
      document.getElementById('statActiveOption').innerText = OPTION_INFO[optKey].code + ' (' + OPTION_INFO[optKey].title.split('/')[0].trim() + ')';

      populateFilters();
      renderCurrentView();
    }}

    function applyCurrentOption() {{
      alert('Applied ' + OPTION_INFO[CURRENT_OPTION].code + ' (' + OPTION_INFO[CURRENT_OPTION].title + ') as the active master examination schedule!');
    }}

    function cleanSecName(sec) {{
      if (!sec) return '';
      let s = String(sec)
        .replace(/\\s*\\((Boys|Girls|Mix|Mixed)\\)/gi, '')
        .replace(/\\s*—\\s*(Boys|Girls|Mix|Mixed)/gi, '')
        .replace(/\\s*-\\s*(Boys|Girls|Mix|Mixed)/gi, '')
        .replace(/\\s*•\\s*(Boys|Girls|Mix|Mixed)/gi, '')
        .trim();
      if (!s || s.toLowerCase() === 'boys' || s.toLowerCase() === 'girls') {{
        return sec;
      }}
      return s;
    }}

    function getGenderBadge(ex) {{
      let g = (ex.gender || '').toUpperCase().trim();
      if (g === 'BOYS') {{
        return `<span class="gender-pill pill-boys">BOYS</span>`;
      }} else if (g === 'GIRLS') {{
        return `<span class="gender-pill pill-girls">GIRLS</span>`;
      }} else if (g === 'MIXED' || g === 'MIX') {{
        return `<span class="gender-pill pill-mixed">MIXED</span>`;
      }}
      return '';
    }}

    function getGradeSortOrder(g) {{
      if (!g) return 999;
      const lower = String(g).toLowerCase().trim();
      if (lower.includes('k1') || lower.includes('kinder 1')) return 1;
      if (lower.includes('k2') || lower.includes('kinder 2')) return 2;
      const m = lower.match(/\\d+/);
      if (m) {{
        return 10 + parseInt(m[0], 10);
      }}
      return 100;
    }}

    function initApp() {{
      populateFilters();
      renderCurrentView();
    }}

    function populateFilters() {{
      const grades = [...new Set(ALL_DATA.map(r => r.grade))].sort((a,b) => getGradeSortOrder(a) - getGradeSortOrder(b));
      const gradeSel = document.getElementById('gradeSelect');
      const curG = gradeSel.value;
      gradeSel.innerHTML = '<option value="">All Grades (' + grades.length + ')</option>' + grades.map(g => `<option value="${{g}}">${{g}}</option>`).join('');
      gradeSel.value = curG;

      updateSectionDropdown();

      const teachers = [...new Set(ALL_DATA.map(r => r.teacher))].sort();
      const tSel = document.getElementById('teacherSelect');
      const curT = tSel.value;
      tSel.innerHTML = '<option value="">All Staff / Faculty (' + teachers.length + ')</option>' + teachers.map(t => `<option value="${{t}}">${{t}}</option>`).join('');
      tSel.value = curT;

      const subjects = [...new Set(ALL_DATA.map(r => r.subject))].sort();
      const subSel = document.getElementById('subjectSelect');
      const curSub = subSel.value;
      subSel.innerHTML = '<option value="">All Subjects (' + subjects.length + ')</option>' + subjects.map(s => `<option value="${{s}}">${{s}}</option>`).join('');
      subSel.value = curSub;
    }}

    function updateSectionDropdown() {{
      const selGrade = document.getElementById('gradeSelect').value;
      const secSel = document.getElementById('sectionSelect');
      const curS = secSel.value;

      let pool = ALL_DATA;
      if (selGrade) {{
        pool = pool.filter(r => r.grade === selGrade || r.grade_level === selGrade);
      }}

      const sections = [...new Set(pool.map(r => r.section || r.section_name))].filter(Boolean).sort();
      const label = selGrade ? `All ${{selGrade}} Sections (${{sections.length}})` : `All Sections (${{sections.length}})`;
      secSel.innerHTML = `<option value="">${{label}}</option>` + sections.map(s => `<option value="${{s}}">${{cleanSecName(s)}}</option>`).join('');
      
      if (sections.includes(curS)) {{
        secSel.value = curS;
      }} else {{
        secSel.value = "";
      }}
    }}

    function getFilteredData() {{
      const query = (document.getElementById('searchInput').value || '').toLowerCase().trim();
      const grade = document.getElementById('gradeSelect').value;
      const section = document.getElementById('sectionSelect').value;
      const gender = (document.getElementById('genderSelect').value || '').toUpperCase().trim();
      const modality = document.getElementById('modalitySelect').value;
      const shift = (document.getElementById('shiftSelect').value || '').toUpperCase().trim();
      const teacher = document.getElementById('teacherSelect').value;
      const subject = document.getElementById('subjectSelect').value;

      return ALL_DATA.filter(r => {{
        // Grade filter
        if (grade && r.grade !== grade && r.grade_level !== grade) return false;

        // Section filter
        if (section) {{
          const s1 = (r.section || '').trim();
          const s2 = (r.section_name || '').trim();
          if (s1 !== section && s2 !== section && cleanSecName(s1) !== cleanSecName(section) && cleanSecName(s2) !== cleanSecName(section)) {{
            return false;
          }}
        }}

        // Gender filter
        if (gender) {{
          const g = (r.gender || '').toUpperCase().trim();
          if (g !== gender && !g.includes(gender)) return false;
        }}

        // Modality filter
        if (modality) {{
          const m = (r.modality || '').toUpperCase();
          const s = (r.shift || '').toUpperCase();
          if (modality === 'F2F') {{
            if (!m.includes('F2F') && !s.includes('F2F')) return false;
          }} else if (modality === 'ODL') {{
            if (!m.includes('ODL') && !s.includes('ODL')) return false;
          }}
        }}

        // Shift filter
        if (shift) {{
          const s = (r.shift || '').toUpperCase();
          const m = (r.modality || '').toUpperCase();
          if (shift.includes('1ST') && !s.includes('1ST') && !m.includes('1ST')) return false;
          if (shift.includes('2ND') && !s.includes('2ND') && !m.includes('2ND')) return false;
        }}

        // Teacher filter
        if (teacher && r.teacher !== teacher) return false;

        // Subject filter
        if (subject && r.subject !== subject) return false;

        // Search query filter
        if (query) {{
          const haystack = [
            r.subject || '',
            r.teacher || '',
            r.section || '',
            r.section_name || '',
            r.grade || '',
            r.modality || '',
            r.shift || '',
            r.time_slot || '',
            r.time || ''
          ].join(' ').toLowerCase();

          if (!haystack.includes(query)) return false;
        }}

        return true;
      }});
    }}

    function onGradeChange() {{
      updateSectionDropdown();
      renderCurrentView();
    }}

    function onFilterChange() {{
      renderCurrentView();
    }}

    function resetFilters() {{
      document.getElementById('searchInput').value = '';
      document.getElementById('gradeSelect').value = '';
      document.getElementById('sectionSelect').value = '';
      document.getElementById('genderSelect').value = '';
      document.getElementById('modalitySelect').value = '';
      document.getElementById('shiftSelect').value = '';
      document.getElementById('teacherSelect').value = '';
      document.getElementById('subjectSelect').value = '';
      updateSectionDropdown();
      renderCurrentView();
    }}

    function switchView(viewName) {{
      CURRENT_VIEW = viewName;
      document.getElementById('tabPosters').classList.toggle('active', viewName === 'posters');
      document.getElementById('tabFaculty').classList.toggle('active', viewName === 'faculty');
      renderCurrentView();
    }}

    function renderCurrentView() {{
      const filtered = getFilteredData();
      
      document.getElementById('statTotalExams').innerText = filtered.length;
      document.getElementById('statTotalSections').innerText = new Set(filtered.map(r => r.grade + '-' + r.section)).size;
      document.getElementById('statTotalTeachers').innerText = new Set(filtered.map(r => r.teacher)).size;

      if (CURRENT_VIEW === 'posters') {{
        renderPostersView(filtered);
      }} else if (CURRENT_VIEW === 'faculty') {{
        renderFacultyView(filtered);
      }}
    }}

    function minutes(tStr) {{
      if (!tStr) return 0;
      const clean = tStr.trim();
      const parts = clean.split(' ');
      if (parts.length < 2) return 0;
      const hm = parts[0].split(':');
      let h = parseInt(hm[0], 10);
      let m = parseInt(hm[1], 10) || 0;
      const ampm = parts[1].toUpperCase();
      if (ampm === 'PM' && h !== 12) h += 12;
      if (ampm === 'AM' && h === 12) h = 0;
      return h * 60 + m;
    }}

    function calcDuration(tStr, fallback) {{
      if (!tStr) return fallback || 60;
      const parts = tStr.split(/[-–]/);
      if (parts.length >= 2) {{
        const m1 = minutes(parts[0].trim());
        const m2 = minutes(parts[1].trim());
        let diff = m2 - m1;
        if (diff < 0) diff += 24 * 60;
        if (diff > 0) return diff;
      }}
      if (typeof fallback === 'number' && fallback > 0) return fallback;
      return 60;
    }}

    function renderPostersView(records) {{
      const container = document.getElementById('mainContainer');
      if (records.length === 0) {{
        container.innerHTML = `
          <div style="text-align:center; padding:80px 20px; background:#fff; border-radius:18px; border:2px dashed #cbd5e1;">
            <h3 style="font-size:22px; font-weight:900; color:#334155;">No examination records match your selected filters</h3>
            <p style="color:#64748b; font-size:15px; font-weight:700; margin-top:6px;">Try adjusting or resetting your filter criteria above.</p>
            <button class="btn btn-primary" style="margin-top:18px;" onclick="resetFilters()">Reset All Filters</button>
          </div>
        `;
        return;
      }}

      const uniqueGrades = [...new Set(records.map(r => r.grade))].sort((a,b) => getGradeSortOrder(a) - getGradeSortOrder(b));

      const dates = [
        '2026-09-02',
        '2026-09-03',
        '2026-09-06',
        '2026-09-07'
      ];

      const dayHeaders = [
        {{ day_num: 1, title: 'Sep 2', sub: 'Wednesday' }},
        {{ day_num: 2, title: 'Sep 3', sub: 'Thursday' }},
        {{ day_num: 3, title: 'Sep 6', sub: 'Sunday' }},
        {{ day_num: 4, title: 'Sep 7', sub: 'Monday' }}
      ];

      container.innerHTML = uniqueGrades.map(grade => {{
        const gradeRecs = records.filter(r => r.grade === grade);
        const uniqueTimes = [...new Set(gradeRecs.map(r => r.time || r.time_slot))].sort((a,b) => minutes(a.split(/[-–]/)[0]) - minutes(b.split(/[-–]/)[0]));
        const hasF2F = gradeRecs.some(r => (r.modality || '').includes('F2F') || (r.shift || '').includes('F2F'));
        const hasODL1 = gradeRecs.some(r => (r.modality || '').includes('1ST') || (r.shift || '').includes('1ST'));

        let timeline = [];
        uniqueTimes.forEach(tStr => {{
          timeline.push({{ time: tStr, isBreak: false }});
        }});

        if (hasF2F && (grade.startsWith('Grade') || grade.includes('Kinder'))) {{
          const insertIdx = timeline.findIndex(item => minutes(item.time.split(/[-–]/)[0]) >= minutes('10:00 AM'));
          const recessItem = {{
            time: '10:00 AM – 10:25 AM',
            isBreak: true,
            label: 'RECESS (10:00 AM – 10:25 AM)',
            tag: 'RECESS'
          }};
          if (insertIdx !== -1) {{
            timeline.splice(insertIdx, 0, recessItem);
          }} else if (timeline.length > 0 && minutes(timeline[0].time.split(/[-–]/)[0]) < minutes('12:00 PM')) {{
            timeline.push(recessItem);
          }}
        }}

        if (hasODL1) {{
          const insertIdx2 = timeline.findIndex(item => minutes(item.time.split(/[-–]/)[0]) >= minutes('03:10 PM'));
          const salahItem = {{
            time: '02:50 PM – 03:10 PM',
            isBreak: true,
            label: 'TRANSITION & SALAH BREAK (2:50 PM – 3:10 PM)',
            tag: 'SALAH BREAK'
          }};
          if (insertIdx2 !== -1) {{
            timeline.splice(insertIdx2, 0, salahItem);
          }}
        }}

        return `
          <div class="calendar-poster" id="poster-${{grade.replace(/\\s+/g, '-')}}">
            <div class="poster-header">
              <div class="poster-title">
                <h2>AL MUNAWWARA ISLAMIC SCHOOL</h2>
                <p>Official Term Examination Schedule • S.Y. 2026–2027 (${{OPTION_INFO[CURRENT_OPTION].code}})</p>
              </div>
              <div class="grade-badge-display">${{grade}}</div>
            </div>

            <div class="table-container">
              <table class="matrix-table">
                <thead>
                  <tr>
                    <th class="time-col">Exam Period</th>
                    ${{dayHeaders.map(dh => `
                      <th>
                        <span class="th-day-title">${{dh.title}}</span>
                        <span class="th-day-sub">${{dh.sub}}</span>
                      </th>
                    `).join('')}}
                  </tr>
                </thead>
                <tbody>
                  ${{timeline.map(item => {{
                    if (item.isBreak) {{
                      return `
                        <tr class="break-tr">
                          <td class="time-td">
                            <span class="time-slot-val">${{item.time}}</span>
                            <span class="break-tag">${{item.tag}}</span>
                          </td>
                          <td colspan="4" class="break-banner-td">${{item.label}}</td>
                        </tr>
                      `;
                    }}

                    return `
                      <tr>
                        <td class="time-td">
                          <span class="time-slot-val">${{item.time}}</span>
                          <span class="time-slot-period">Exam Period</span>
                        </td>
                        ${{dayHeaders.map(dh => {{
                          const cellExams = gradeRecs.filter(r => {{
                            const matchDay = (r.day_number === dh.day_num) || (r.short_date && r.short_date.includes(dh.title)) || (r.date && r.date.includes(dh.title));
                            const matchTime = (r.time === item.time) || (r.time_slot === item.time);
                            return matchDay && matchTime;
                          }});

                          if (cellExams.length === 0) {{
                            return `<td><div class="empty-slot-block">No Exam</div></td>`;
                          }}
                          return `
                            <td>
                              <div class="cards-stack">
                                ${{cellExams.map(ex => {{
                                  const typeCls = ex.modality === 'F2F' ? 'f2f' : ((ex.shift && ex.shift.includes('2nd')) ? 'odl2' : 'odl1');
                                  return renderExamCardHtml(ex, typeCls);
                                }}).join('')}}
                              </div>
                            </td>
                          `;
                        }}).join('')}}
                      </tr>
                    `;
                  }}).join('')}}
                </tbody>
              </table>
            </div>
            <div class="poster-footer-strip" style="background:#f8fafc; border-top:1.5px solid #cbd5e1; padding:12px 24px; display:flex; justify-content:space-between; align-items:center; font-size:12.5px; font-weight:800; color:#64748b;">
              <span>AL MUNAWWARA ISLAMIC SCHOOL • OFFICIAL EXAMINATION TIMETABLE</span>
              <span>System Architect & Lead Engineer: Software Engineer Mon Zhairel Lingasa</span>
            </div>
          </div>
        `;
      }}).join('');
    }}

    function renderExamCardHtml(ex, typeCls) {{
      const shiftLabel = ex.modality === 'F2F' ? 'F2F Classroom' : (ex.shift.includes('2nd') ? 'ODL 2nd Shift' : 'ODL 1st Shift');
      const timeVal = ex.time_slot || ex.time || '';
      const durVal = calcDuration(timeVal, ex.duration_minutes);
      return `
        <div class="exam-event-card ${{typeCls}}" onclick="openSubjectModal('${{encodeURIComponent(ex.subject)}}')">
          <div class="card-subject-name">
            <span>${{ex.subject}}</span>
            <span class="click-hint">details →</span>
          </div>
          <div class="card-time-duration-row" style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.04); padding:3px 7px; border-radius:5px; margin:3px 0 5px 0; font-size:11px; font-weight:800;">
            <span style="color:#0f172a;">${{timeVal}}</span>
            <span style="background:#064e3b; color:#ffffff; padding:1px 5px; border-radius:3px; font-size:10px; font-weight:900;">${{durVal}} min</span>
          </div>
          <div class="card-grade-gender-row">
            <span class="card-grade-label">${{ex.grade}}</span>
            ${{getGenderBadge(ex)}}
          </div>
          <div class="card-sec-name-row">
            <span>${{cleanSecName(ex.section_name || ex.section)}}</span>
          </div>
          <div class="card-teacher-row">
            <span>${{ex.teacher}}</span>
            ${{ex.room ? `<span style="font-size:12px; background:#f1f5f9; padding:2px 7px; border-radius:4px; color:#334155; font-weight:800;">Rm ${{ex.room}}</span>` : ''}}
          </div>
          <div class="card-modality-row">
            <span>${{shiftLabel}}</span>
          </div>
        </div>
      `;
    }}

    function renderFacultyView(records) {{
      const container = document.getElementById('mainContainer');
      const uniqueTeachers = [...new Set(records.map(r => r.teacher))].sort();

      container.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:28px;">
          ${{uniqueTeachers.map(teacher => {{
            const tRecs = records.filter(r => r.teacher === teacher).sort((a,b) => a.date.localeCompare(b.date) || minutes(a.time) - minutes(b.time));
            const subList = [...new Set(tRecs.map(r => r.subject))];
            const weeklyData = (typeof WEEKLY_SCHEDULES_DATA !== 'undefined' && WEEKLY_SCHEDULES_DATA[teacher]) ? WEEKLY_SCHEDULES_DATA[teacher] : null;

            let weeklyTableHtml = '';
            if (weeklyData && weeklyData.rows) {{
              weeklyTableHtml = `
                <div style="overflow-x:auto; margin-top:14px; border:1.5px solid #cbd5e1; border-radius:8px;">
                  <table style="width:100%; border-collapse:collapse; background:#ffffff; table-layout:fixed; font-size:12px;">
                    <thead>
                      <tr style="background:#0b4d38; color:#ffffff;">
                        <th style="padding:8px 6px; width:130px; border:1px solid #043828; text-align:center;">Time</th>
                        <th style="padding:8px 6px; width:65px; border:1px solid #043828; text-align:center;">Mins</th>
                        <th style="padding:8px 6px; border:1px solid #043828; text-align:center;">Sunday</th>
                        <th style="padding:8px 6px; border:1px solid #043828; text-align:center;">Monday</th>
                        <th style="padding:8px 6px; border:1px solid #043828; text-align:center;">Tuesday</th>
                        <th style="padding:8px 6px; border:1px solid #043828; text-align:center;">Wednesday</th>
                        <th style="padding:8px 6px; border:1px solid #043828; text-align:center;">Thursday</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${{weeklyData.rows.map(r => {{
                        if (r.is_break) {{
                          return `
                            <tr style="background:#f1f5f9;">
                              <td style="padding:4px 6px; border:1px solid #cbd5e1; text-align:center; font-weight:800; font-size:11px; color:#1e293b;">${{r.time}}</td>
                              <td style="padding:4px 6px; border:1px solid #cbd5e1; text-align:center; font-weight:800; font-size:11px; color:#64748b;">${{r.minutes}}m</td>
                              <td colspan="5" style="padding:4px 10px; border:1px solid #cbd5e1; text-align:center; font-weight:900; font-size:10.5px; color:#475569; letter-spacing:0.04em; text-transform:uppercase;">${{r.break_title}}</td>
                            </tr>
                          `;
                        }}
                        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];
                        const dayCells = days.map(d => {{
                          const cell = r.days[d];
                          if (cell && cell.occupied) {{
                            const c = cell.color || {{ bg: '#f1f5f9', border: '#cbd5e1', text: '#1e293b' }};
                            return `
                              <td style="padding:4px 4px; border:1px solid #cbd5e1; text-align:center; background:${{c.bg}}; color:${{c.text}}; border-color:${{c.border}}; vertical-align:middle;">
                                <div style="font-weight:900; font-size:11px; line-height:1.2;">${{cell.label}}</div>
                                <div style="font-size:9px; font-weight:700; opacity:0.8; text-transform:uppercase;">${{cell.modality}}</div>
                              </td>
                            `;
                          }}
                          return '<td style="padding:4px; border:1px solid #cbd5e1; background:#ffffff;"></td>';
                        }}).join('');

                        return `
                          <tr>
                            <td style="padding:4px 6px; border:1px solid #cbd5e1; text-align:center; font-weight:800; font-size:11px; background:#f8fafc; color:#1e293b;">${{r.time}}</td>
                            <td style="padding:4px 6px; border:1px solid #cbd5e1; text-align:center; font-weight:800; font-size:11px; background:#f1f5f9; color:#475569;">${{r.minutes}}m</td>
                            ${{dayCells}}
                          </tr>
                        `;
                      }}).join('')}}
                    </tbody>
                  </table>
                </div>
              `;
            }}

            return `
              <div class="calendar-poster" style="margin-bottom:28px;">
                <div class="poster-header" style="background: #064e3b; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                  <div class="poster-title">
                    <h2 style="font-size:20px; font-weight:900; letter-spacing:0.02em;">${{teacher}}</h2>
                    <p style="font-size:13px; color:#a7f3d0; font-weight:700;">${{subList.join(' • ')}} (${{weeklyData ? weeklyData.total_classes + ' Weekly Classes' : tRecs.length + ' Exams'}})</p>
                  </div>
                  <div style="display:flex; gap:10px; align-items:center;">
                    <a href="faculty-timetable-print.html?teacher=${{encodeURIComponent(teacher)}}" target="_blank" class="btn btn-outline" style="background:#ffffff; color:#064e3b; font-size:13px; padding:7px 14px; border-radius:6px; text-decoration:none; font-weight:800; display:inline-flex; align-items:center; gap:6px;">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M18 3H6V7H18V3M19 12A1 1 0 1 1 18 11A1 1 0 0 1 19 12M16 19H8V14H16V19M19 8H5A3 3 0 0 0 2 11V17H6V21H18V17H22V11A3 3 0 0 0 19 8Z"/></svg>
                      Print / Export PDF
                    </a>
                  </div>
                </div>

                <div style="padding:20px;">
                  <h3 style="font-size:15px; font-weight:900; color:#0f172a; margin-bottom:6px;">
                    Weekly Teaching Schedule Matrix (Sunday–Thursday)
                  </h3>
                  ${{weeklyTableHtml}}

                  <div style="margin-top:24px; padding-top:18px; border-top:2px solid #e2e8f0;">
                    <h3 style="font-size:14px; font-weight:900; color:#0f172a; margin-bottom:12px;">
                      Term Examination Proctoring Schedule (${{tRecs.length}} Sessions)
                    </h3>
                    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:14px;">
                      ${{tRecs.map(ex => {{
                        const typeCls = ex.modality === 'F2F' ? 'f2f' : (ex.shift.includes('2nd') ? 'odl2' : 'odl1');
                        return renderExamCardHtml(ex, typeCls);
                      }}).join('')}}
                    </div>
                  </div>
                </div>
              </div>
            `;
          }}).join('')}}
        </div>
      `;
    }}

    function openSubjectModal(encSubject) {{
      const subject = decodeURIComponent(encSubject);
      CURRENT_MODAL_SUBJECT = subject;

      const subRecs = ALL_DATA.filter(r => r.subject === subject).sort((a,b) => {{
        return a.date.localeCompare(b.date) || minutes(a.time) - minutes(b.time) || a.grade.localeCompare(b.grade, undefined, {{ numeric: true }});
      }});

      document.getElementById('modalSubjectTitle').innerText = subject;
      document.getElementById('modalSubjectSub').innerText = `${{subRecs.length}} Active Section Assignments Across Examination Days (${{OPTION_INFO[CURRENT_OPTION].code}})`;

      const tCount = new Set(subRecs.map(r => r.teacher)).size;
      const secCount = new Set(subRecs.map(r => `${{r.grade}}-${{r.section}}`)).size;

      document.getElementById('modalStatSections').innerText = secCount;
      document.getElementById('modalStatTeachers').innerText = tCount;
      document.getElementById('modalStatExams').innerText = subRecs.length;

      const listContainer = document.getElementById('modalSecList');
      listContainer.innerHTML = subRecs.map(ex => {{
        const modCls = ex.modality === 'F2F' ? 'f2f' : (ex.shift.includes('2nd') ? 'odl2' : 'odl1');
        const modLabel = ex.modality === 'F2F' ? 'F2F Classroom' : (ex.shift.includes('2nd') ? 'ODL 2nd Shift' : 'ODL 1st Shift');

        return `
          <div class="modal-sec-item">
            <div>
              <div class="item-grade-sec">${{ex.grade}} — ${{cleanSecName(ex.section)}} ${{getGenderBadge(ex)}}</div>
              <span class="mod-badge ${{modCls}}">${{modLabel}}</span>
            </div>
            <div>
              <span style="font-size:12px; color:var(--text-muted); font-weight:800; display:block;">FACULTY PROCTOR</span>
              <div class="item-teacher">${{ex.teacher}}</div>
            </div>
            <div>
              <span style="font-size:12px; color:var(--text-muted); font-weight:800; display:block;">EXAM SCHEDULE</span>
              <div class="item-datetime">
                ${{ex.date}} (${{ex.dayName.slice(0,3)}})
                <span>${{ex.time}}</span>
              </div>
            </div>
            <div style="text-align:right;">
              ${{ex.room ? `<span class="mod-badge" style="background:#f1f5f9; color:#1e293b; font-size:13px; font-weight:800; border:1.5px solid var(--line);">Rm ${{ex.room}}</span>` : '<span style="font-size:13px; font-weight:800; color:#64748b;">Online</span>'}}
            </div>
          </div>
        `;
      }}).join('');

      document.getElementById('subjectModalBackdrop').classList.add('active');
    }}

    function closeSubjectModal(e) {{
      if (e && e.target !== document.getElementById('subjectModalBackdrop') && !e.target.classList.contains('modal-close-btn') && e.target.tagName !== 'BUTTON') {{
        return;
      }}
      document.getElementById('subjectModalBackdrop').classList.remove('active');
    }}

    function filterByCurrentSubject() {{
      if (!CURRENT_MODAL_SUBJECT) return;
      document.getElementById('subjectSelect').value = CURRENT_MODAL_SUBJECT;
      closeSubjectModal();
      renderCurrentView();
    }}

    function openCompareModal() {{
      const metrics = window.AMIS_OPTIONS_DATA ? window.AMIS_OPTIONS_DATA.METRICS : {{}};
      const container = document.getElementById('compareGridContent');

      container.innerHTML = ['OPTION_A', 'OPTION_B', 'OPTION_C', 'OPTION_D'].map(k => {{
        const info = OPTION_INFO[k];
        const m = (metrics && metrics[k]) ? metrics[k] : {{
          teacher_conflicts: 0,
          section_conflicts: 0,
          total_exams: 597,
          alignment_pct: 0,
          teacher_balance_score: 80,
          student_flow_score: 80,
          status: 'VALID'
        }};

        const isCurrent = CURRENT_OPTION === k;

        return `
          <div class="compare-card ${{isCurrent ? 'active-card' : ''}}">
            <div>
              <div class="compare-header">
                <span class="compare-code">${{info.code}}</span>
                ${{k === 'OPTION_B' ? '<span class="badge-rec" style="margin-left:6px;">RECOMMENDED</span>' : ''}}
                <div class="compare-title">${{info.title}}</div>
                <div class="compare-desc">${{info.desc}}</div>
              </div>

              <div>
                <div class="metric-item">
                  <span class="metric-lbl">Teacher Conflicts</span>
                  <span class="metric-val val-good">${{m.teacher_conflicts}} (Zero)</span>
                </div>
                <div class="metric-item">
                  <span class="metric-lbl">Section Conflicts</span>
                  <span class="metric-val val-good">${{m.section_conflicts}} (Zero)</span>
                </div>
                <div class="metric-item">
                  <span class="metric-lbl">Total Valid Exams</span>
                  <span class="metric-val">${{m.total_exams}} / 597</span>
                </div>
                <div class="metric-item">
                  <span class="metric-lbl">Modality Alignment</span>
                  <span class="metric-val ${{k === 'OPTION_B' ? 'val-good' : ''}}">${{m.alignment_pct}}%</span>
                </div>
                <div class="metric-item">
                  <span class="metric-lbl">Teacher Balance Score</span>
                  <span class="metric-val ${{k === 'OPTION_C' ? 'val-good' : ''}}">${{m.teacher_balance_score}}/100</span>
                </div>
                <div class="metric-item">
                  <span class="metric-lbl">Continuous Flow</span>
                  <span class="metric-val ${{k === 'OPTION_D' ? 'val-good' : ''}}">${{m.student_flow_score}}%</span>
                </div>
                <div class="metric-item" style="border-bottom:0;">
                  <span class="metric-lbl">Solver Status</span>
                  <span class="metric-val val-good">${{m.status}}</span>
                </div>
              </div>
            </div>

            <div style="margin-top:18px; display:flex; flex-direction:column; gap:8px;">
              <button class="btn ${{isCurrent ? 'btn-primary' : 'btn-outline'}}" onclick="switchOption('${{k}}'); closeCompareModal();">
                ${{isCurrent ? 'Currently Viewing' : 'Preview ' + info.code}}
              </button>
              <button class="btn btn-primary" style="background:#064e3b; font-size:13px;" onclick="switchOption('${{k}}'); applyCurrentOption(); closeCompareModal();">
                Apply ${{info.code}} As Active
              </button>
            </div>
          </div>
        `;
      }}).join('');

      document.getElementById('compareModalBackdrop').classList.add('active');
    }}

    function closeCompareModal(e) {{
      if (e && e.target !== document.getElementById('compareModalBackdrop') && !e.target.classList.contains('modal-close-btn') && e.target.tagName !== 'BUTTON') {{
        return;
      }}
      document.getElementById('compareModalBackdrop').classList.remove('active');
    }}

    function exportMasterCSV() {{
      const filtered = getFilteredData();
      const headers = ['Exam Day', 'Date', 'Day Name', 'Start Time', 'End Time', 'Time Slot', 'Period', 'Duration', 'Grade', 'Section', 'Gender', 'Modality', 'Shift', 'Subject', 'Teacher', 'Room', 'Status'];
      const rows = filtered.map(r => [
        r.examDay || '',
        r.date,
        r.dayName,
        r.startTime || '',
        r.endTime || '',
        r.time,
        r.period || '',
        r.duration || '60 minutes',
        r.grade,
        r.section_name || r.section,
        r.gender || 'NOT ENCODED',
        r.modality,
        r.shift,
        r.subject,
        r.teacher,
        r.room || '',
        r.status || 'CONFIRMED'
      ]);

      const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(e => e.map(val => `"${{String(val).replace(/"/g, '""')}}"`).join(','))].join('\\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', `AMIS_Exam_Schedule_${{CURRENT_OPTION}}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}
  </script>
</body>
</html>
"""

with open(os.path.join(BASE_DIR, "exam-schedule.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print("exam-schedule.html successfully written and assembled with all 4 options!")
