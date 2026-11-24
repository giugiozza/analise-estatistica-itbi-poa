import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, footer {visibility: hidden;}
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
        [data-testid="stSidebar"] {background: #EDF1F5; border-right: 1px solid #E2E8F0;}
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF; border: 1px solid #D1D9E2; border-radius: 10px;
        }
        .kpi-title {color:#64748B; font-size:.82rem; font-weight:600; margin-bottom:.35rem;}
        .kpi-value {color:#0F172A; font-size:1.55rem; font-weight:700; line-height:1.1;}
        .muted {color:#64748B; font-size:.78rem;}
        .badge-reject, .badge-no-reject, .badge-gray {
            display:inline-block; padding:3px 8px; border-radius:999px; font-size:.75rem;
            font-weight:600;
        }
        .badge-reject {background:#DBEAFE; color:#1D4ED8;}
        .badge-no-reject {background:#EEF2F6; color:#475569;}
        .badge-gray {background:#EEF2F6; color:#64748B;}
        .hypothesis {background:#EEF2F6; border-radius:6px; padding:9px 12px; text-align:center;
            color:#334155; font-size:.9rem; line-height:1.45; margin:.4rem 0 .7rem;}
        .hypothesis-row {display:flex; justify-content:center; align-items:baseline; gap:.45rem;
            flex-wrap:wrap;}
        .hypothesis-row + .hypothesis-row {margin-top:5px;}
        .hypothesis-row strong {white-space:nowrap;}
        .market-reading {color:#475569; font-size:.82rem; line-height:1.45; margin:.25rem 0 .75rem;}
        .scope-note {display:block; color:#64748B; font-size:.74rem; margin-top:3px;}
        .not-check {color:#64748B; font-weight:600;}
        .itbi-table {width:100%; border-collapse:collapse; font-size:.86rem;}
        .itbi-table th {background:#EEF2F6; color:#334155; text-align:right; padding:9px;}
        .itbi-table th:first-child, .itbi-table td:first-child {text-align:left;}
        .itbi-table td {border-bottom:1px solid #E2E8F0; padding:9px; text-align:right;}
        .itbi-table tr:last-child td {border-bottom:0;}
        .check {color:#15803D; font-weight:700;}
        [data-testid="stPopover"] button {
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            background: #FFFFFF;
            color: #1849C6;
            font-size: 0.82rem;
            min-height: 38px;
            justify-content: flex-start;
        }
        [data-testid="stPopover"] button:hover {
            border-color: #1849C6;
            background: #F8FAFC;
        }
        [data-testid="stVerticalBlock"] [data-testid="stBaseButton-secondary"] {
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            color: #1849C6;
            background: #FFFFFF;
            font-size: 0.82rem;
            min-height: 38px;
            text-align: left;
        }
        [role="dialog"] {
            max-width: 720px;
            border-radius: 12px;
        }
        [role="dialog"] [data-testid="stMarkdownContainer"] {
            font-size: 0.95rem;
            line-height: 1.55;
        }
        [data-baseweb="tab"] {
            font-size: 0.95rem;
            font-weight: 600;
            color: #64748B;
        }
        [aria-selected="true"][data-baseweb="tab"] {
            color: #1849C6;
            border-bottom: 3px solid #1849C6;
        }
        [data-testid="stButton"] button,
        [data-testid="stDownloadButton"] button {
            transition: border-color 120ms ease, background-color 120ms ease, color 120ms ease;
        }
        [data-testid="stButton"] button:hover,
        [data-testid="stDownloadButton"] button:hover {
            border-color: #1849C6;
            background: #F8FAFC;
        }
        [data-testid="stButton"] button:focus-visible,
        [data-testid="stDownloadButton"] button:focus-visible,
        [data-testid="stSelectbox"] div:focus-within,
        [data-testid="stSlider"] div:focus-within {
            outline: 3px solid rgba(24,73,198,0.22);
            outline-offset: 2px;
        }
        [data-testid="stMetricLabel"] {
            color: #475569;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #0F172A;
        }
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_True_0),
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_True_1),
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_True_2),
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_True_3),
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_False_0),
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_False_1),
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_False_2),
        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.st-key-kpi_False_3) {
            height: 160px;
        }
        .st-key-kpi_True_0,
        .st-key-kpi_True_1,
        .st-key-kpi_True_2,
        .st-key-kpi_True_3,
        .st-key-kpi_False_0,
        .st-key-kpi_False_1,
        .st-key-kpi_False_2,
        .st-key-kpi_False_3 {
            min-height: 160px;
        }
        [class*="st-key-metric_info_"] button {
            border: 0 !important;
            background: transparent !important;
            color: #1849C6 !important;
            box-shadow: none !important;
            outline: none !important;
            min-height: 32px !important;
            height: 32px !important;
            padding: 0 !important;
        }
        [class*="st-key-metric_info_"] button:hover,
        [class*="st-key-metric_info_"] button:focus-visible {
            border: 0 !important;
            background: transparent !important;
            color: #0F172A !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .st-key-panel_population button,
        .st-key-panel_sample button,
        .st-key-panel_inference button {
            min-height: 136px !important;
            height: 136px !important;
            max-height: 136px !important;
            white-space: normal !important;
            text-align: center !important;
            display: block !important;
            border: 1px solid #D1D9E2 !important;
            border-radius: 10px !important;
            padding: 14px 24px !important;
            line-height: 1.35 !important;
            box-sizing: border-box !important;
            color: #64748B !important;
            background: #FFFFFF !important;
        }
        .st-key-panel_population button[kind="primary"],
        .st-key-panel_sample button[kind="primary"],
        .st-key-panel_inference button[kind="primary"] {
            color: #FFFFFF !important;
            background: #1849C6 !important;
            border-color: #1849C6 !important;
        }
        .st-key-panel_population button p:first-child,
        .st-key-panel_sample button p:first-child,
        .st-key-panel_inference button p:first-child {
            margin: 0 0 10px 0;
            text-align: center;
            font-size: 1rem;
            font-weight: 700;
            color: inherit !important;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
        }
        .st-key-panel_population button p:last-child,
        .st-key-panel_sample button p:last-child,
        .st-key-panel_inference button p:last-child {
            margin: 0;
            text-align: center !important;
            font-size: 0.88rem;
            font-weight: 400;
            line-height: 1.35;
            color: #64748B;
            width: 100%;
            max-width: 100%;
            margin-left: auto;
            margin-right: auto;
            box-sizing: border-box;
            overflow-wrap: anywhere;
        }
        .st-key-panel_population button[kind="primary"] p:last-child,
        .st-key-panel_sample button[kind="primary"] p:last-child,
        .st-key-panel_inference button[kind="primary"] p:last-child {
            color: rgba(255,255,255,0.86) !important;
        }
        .st-key-panel_population button[kind="primary"]:hover,
        .st-key-panel_sample button[kind="primary"]:hover,
        .st-key-panel_inference button[kind="primary"]:hover,
        .st-key-panel_population button[kind="primary"]:focus-visible,
        .st-key-panel_sample button[kind="primary"]:focus-visible,
        .st-key-panel_inference button[kind="primary"]:focus-visible {
            color: #FFFFFF !important;
            background: #1849C6 !important;
            border-color: #0F172A !important;
        }
        .st-key-panel_population button[kind="secondary"]:hover,
        .st-key-panel_sample button[kind="secondary"]:hover,
        .st-key-panel_inference button[kind="secondary"]:hover,
        .st-key-panel_population button[kind="secondary"]:focus-visible,
        .st-key-panel_sample button[kind="secondary"]:focus-visible,
        .st-key-panel_inference button[kind="secondary"]:focus-visible {
            color: #1849C6 !important;
            background: #F8FAFC !important;
            border-color: #1849C6 !important;
        }
        @media (max-width: 900px) {
            .block-container {padding-left: 1rem; padding-right: 1rem;}
            [data-testid="stHorizontalBlock"] {flex-wrap: wrap;}
            [data-testid="column"] {width: 100% !important; flex: 1 1 100% !important;}
            [data-baseweb="tab"] {font-size: 0.82rem; padding-left: 8px; padding-right: 8px;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
