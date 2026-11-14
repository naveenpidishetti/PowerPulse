"""
Script to generate a comprehensive, professional PDF documentation
for the PowerPulse Smart Electricity Consumption Prediction & Anomaly Detection System.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for total page count and professional headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages after first page)
        if self._pageNumber > 1:
            self.drawString(54, 750, "PowerPulse — Smart Electricity Prediction & Anomaly Detection System")
            self.drawRightString(612 - 54, 750, "Technical Architecture & Feature Guide")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.drawString(54, 32, "PowerPulse Project Documentation • AI Energy Intelligence")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.restoreState()


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom color palette
    c_primary = colors.HexColor("#0f172a")     # Deep Slate
    c_blue = colors.HexColor("#1e40af")        # Brand Blue
    c_cyan = colors.HexColor("#0284c7")        # Accent Cyan
    c_dark = colors.HexColor("#1e293b")        # Text Dark
    c_muted = colors.HexColor("#64748b")       # Text Muted
    c_light_bg = colors.HexColor("#f8fafc")    # Card / Row Bg
    c_border = colors.HexColor("#e2e8f0")      # Border Grey
    c_accent = colors.HexColor("#f59e0b")      # Amber Accent
    c_danger = colors.HexColor("#dc2626")      # Danger Red
    c_success = colors.HexColor("#16a34a")     # Success Green

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_blue,
        spaceAfter=12,
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=c_muted,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_blue,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6,
    )
    body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=13,
        textColor=c_dark,
        leftIndent=12,
        spaceAfter=4,
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=c_dark,
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=c_dark,
    )
    callout_text = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.8,
        leading=13,
        textColor=c_primary,
    )

    story = []

    # ---------------------------------------------------------
    # COVER / HEADER BANNER
    # ---------------------------------------------------------
    banner_table_data = [
        [
            Paragraph("<b>POWERPULSE ⚡</b>", ParagraphStyle("Logo", fontName="Helvetica-Bold", fontSize=18, textColor=c_accent)),
            Paragraph(f"<b>System Guide & Feature Manual</b><br/>Published: {datetime.now().strftime('%B %Y')}", ParagraphStyle("RightHdr", fontName="Helvetica", fontSize=9, textColor=colors.whitesmoke, alignment=2))
        ]
    ]
    t_banner = Table(banner_table_data, colWidths=[250, 254])
    t_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_primary),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("CORNERPAD", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Smart Electricity Consumption Prediction & Anomaly Detection", title_style))
    story.append(Paragraph("A Comprehensive Guide to Architecture, Machine Learning Pipelines, and Platform Features", subtitle_style))
    
    meta_box = [
        [
            Paragraph("<b>Framework:</b> Django 5.2 (Python 3.12+)", meta_style),
            Paragraph("<b>ML Library:</b> Scikit-Learn & Pandas", meta_style),
            Paragraph("<b>Target Audience:</b> Auditors, Engineers & Evaluators", meta_style),
        ],
        [
            Paragraph("<b>Database:</b> SQLite (Zero Config)", meta_style),
            Paragraph("<b>Charts:</b> Chart.js Interactive Engine", meta_style),
            Paragraph("<b>Document Version:</b> 1.0 (Production Release)", meta_style),
        ]
    ]
    t_meta = Table(meta_box, colWidths=[168, 168, 168])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # 1. EXECUTIVE SUMMARY
    # ---------------------------------------------------------
    story.append(Paragraph("1. Executive Summary & Problem Statement", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "Modern facilities and residential compounds struggle with unpredictable energy bills, unflagged hardware malfunctions, "
        "and delayed leak detection. Typical energy audits occur weeks after a billing cycle closes, long after consumption spikes "
        "have caused financial loss. <b>PowerPulse</b> solves this by providing continuous, automated intelligence:",
        body_style
    ))
    story.append(Paragraph("• <b>Proactive Anomaly Detection:</b> Unsupervised Isolation Forests and statistical bounds automatically identify consumption surges the day they occur.", bullet_style))
    story.append(Paragraph("• <b>Machine Learning Load Forecasting:</b> Multi-variable auto-regressive regression accurately predicts upcoming daily electricity usage across 7 to 30 day horizons.", bullet_style))
    story.append(Paragraph("• <b>Meter Reading & CSV Ingestion:</b> Simple manual loggers and bulk CSV parsers eliminate friction when importing historical facility data.", bullet_style))
    story.append(Paragraph("• <b>Utility Bill Audit:</b> Automated effective rate monitoring (cost-per-unit) flags utility rate hikes and tariff drift.", bullet_style))
    story.append(Paragraph("• <b>Instant Audit Reporting:</b> One-click ReportLab PDF generation exports boardroom-ready executive audits on demand.", bullet_style))
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 2. SYSTEM ARCHITECTURE
    # ---------------------------------------------------------
    story.append(Paragraph("2. System Architecture & Tech Stack", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "PowerPulse is engineered as a clean, decoupled 4-tier web application built upon the robust Django Model-Template-View (MTV) pattern:",
        body_style
    ))

    arch_data = [
        [Paragraph("Layer", table_header), Paragraph("Technology", table_header), Paragraph("Key Responsibilities & Components", table_header)],
        [
            Paragraph("<b>Presentation</b>", table_cell_bold),
            Paragraph("Bootstrap 5<br/>Chart.js<br/>Bootstrap Icons", table_cell),
            Paragraph("Responsive desktop/mobile layouts, interactive daily consumption timelines, anomaly scatter plots, and intuitive audit forms.", table_cell),
        ],
        [
            Paragraph("<b>Application Logic</b>", table_cell_bold),
            Paragraph("Django 5.2<br/>Python 3.12+", table_cell),
            Paragraph("URL dispatching, session authentication, CSV parsing, delta calculations, authorization guards, and business rule validation.", table_cell),
        ],
        [
            Paragraph("<b>Machine Learning</b>", table_cell_bold),
            Paragraph("Scikit-Learn<br/>Pandas & NumPy", table_cell),
            Paragraph("Random Forest & Ridge Regressor forecasting, feature engineering (lags, rolling statistics, calendar indicators), Isolation Forest anomaly detection.", table_cell),
        ],
        [
            Paragraph("<b>Persistence & DB</b>", table_cell_bold),
            Paragraph("SQLite 3<br/>Django ORM", table_cell),
            Paragraph("Stores meter readings, anomaly alert logs, time-series predictions, user accounts, and billing statements with zero setup overhead.", table_cell),
        ],
        [
            Paragraph("<b>Reporting</b>", table_cell_bold),
            Paragraph("ReportLab 5.1", table_cell),
            Paragraph("Dynamic multi-page PDF document generation compiling executive summaries, KPI tables, anomaly tables, and forecast projections.", table_cell),
        ],
    ]
    t_arch = Table(arch_data, colWidths=[90, 105, 309])
    t_arch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [c_light_bg, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 14))

    # Page break to start detailed features cleanly on Page 2
    story.append(PageBreak())

    # ---------------------------------------------------------
    # 3. DETAILED PLATFORM FEATURES
    # ---------------------------------------------------------
    story.append(Paragraph("3. Core Platform Features & Capabilities", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("3.1 Interactive Energy Intelligence Dashboard", h2_style))
    story.append(Paragraph(
        "Upon authentication, the user lands on an executive dashboard that synthesizes all historical readings into actionable metrics:",
        body_style
    ))
    story.append(Paragraph("• <b>30-Day Scorecards:</b> Aggregates cumulative energy usage (kWh), total estimated spend (₹), average daily consumption, and the single-day peak surge.", bullet_style))
    story.append(Paragraph("• <b>Consumption Timeline:</b> Chart.js interactive graph visualizing consumption trends over the previous 30 to 60 days.", bullet_style))
    story.append(Paragraph("• <b>Immediate Alert Banner:</b> Surfaces unreviewed anomaly alerts right at the top of the screen so equipment malfunctions are noticed instantly.", bullet_style))
    story.append(Paragraph("• <b>Upcoming Forecast Preview:</b> Displays predicted consumption for the upcoming week based on the latest trained model.", bullet_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.2 Machine Learning Load Forecasting Engine (ml/predictor.py)", h2_style))
    story.append(Paragraph(
        "PowerPulse incorporates an advanced auto-regressive regression pipeline that accurately projects future electricity loads. "
        "Unlike simplistic moving averages, the predictor incorporates comprehensive calendar and sequential time-series indicators:",
        body_style
    ))

    ml_feat_data = [
        [Paragraph("Feature Group", table_header), Paragraph("Engineered Variables", table_header), Paragraph("Behavioral & Predictive Significance", table_header)],
        [
            Paragraph("<b>Temporal / Calendar</b>", table_cell_bold),
            Paragraph("<code>day_of_week</code><br/><code>day_of_month</code><br/><code>month</code><br/><code>is_weekend</code>", table_cell),
            Paragraph("Captures human activity cycles: weekend usage jumps vs weekday baseline, monthly billing periods, and seasonal temperature shifts.", table_cell),
        ],
        [
            Paragraph("<b>Auto-Regressive Lags</b>", table_cell_bold),
            Paragraph("<code>lag_1</code> (Yesterday)<br/><code>lag_2</code> (2 days prior)<br/><code>lag_7</code> (Same day prior week)", table_cell),
            Paragraph("Preserves temporal autocorrelation. The 7-day lag directly correlates weekly cyclical operations (e.g., Monday to Monday patterns).", table_cell),
        ],
        [
            Paragraph("<b>Rolling Statistics</b>", table_cell_bold),
            Paragraph("<code>rolling_7_mean</code>", table_cell),
            Paragraph("Smooths high-frequency noise and reflects macro trends in household or facility equipment utilization.", table_cell),
        ],
    ]
    t_ml_feat = Table(ml_feat_data, colWidths=[100, 130, 274])
    t_ml_feat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_blue),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [c_light_bg, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_ml_feat)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Model Selection & Multi-Step Recursive Forecasting:</b> Users can select between <b>Random Forest Regressor</b> "
        "(capturing non-linear interactions and threshold dynamics) and <b>Ridge Regression</b> (L2 regularized linear baseline). "
        "For multi-day forecasts (7, 14, or 30 days), the engine applies an iterative recursive strategy where each step's prediction "
        "feeds into subsequent lag and rolling calculations. Model accuracy is validated live with <b>RMSE</b> and <b>MAE</b> scorecards.",
        body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.3 Dual-Layer Surge & Anomaly Detection (ml/anomaly_detector.py)", h2_style))
    story.append(Paragraph(
        "A critical innovation in PowerPulse is its dual-layer unsupervised anomaly detection system, designed to catch surges "
        "and leaks without requiring manual threshold adjustments:",
        body_style
    ))
    story.append(Paragraph("• <b>Layer 1 — Scikit-Learn Isolation Forest:</b> Employs recursive tree partitioning to isolate data points that deviate from multidimensional clusters (contamination parameter set to 0.05).", bullet_style))
    story.append(Paragraph("• <b>Layer 2 — Statistical Dispersion (2.5σ & IQR):</b> Evaluates the reading against rolling mean and standard deviation. Any observation beyond 2.5 standard deviations or Interquartile Range boundaries is isolated.", bullet_style))
    story.append(Paragraph("• <b>Automated Diagnostic Attribution:</b> The engine analyzes the deviation ratio and assigns human-readable explanations (e.g., <i>'Severe consumption surge: 96.2 kWh (2.9x user average)'</i> or <i>'Atypical weekend drop: facility unoccupied'</i>).", bullet_style))
    story.append(Paragraph("• <b>Historical Anomaly Scatter Plot:</b> Overlays detected anomaly points onto the user's historical trendline in high-visibility red markers for rapid root-cause inspection.", bullet_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.4 Meter Reading Management & Flexible CSV Ingestion", h2_style))
    story.append(Paragraph(
        "Users can log readings manually or ingest extensive multi-month datasets in seconds:",
        body_style
    ))
    story.append(Paragraph("• <b>Automatic Delta Calculation:</b> Users enter cumulative meter readouts; the system computes <code>Current - Previous = Net Consumption kWh</code> and applies the active unit tariff automatically.", bullet_style))
    story.append(Paragraph("• <b>Robust CSV Ingestion:</b> Supports flexible column aliases (<code>date</code>, <code>reading_date</code>, <code>kwh</code>, <code>units</code>, <code>tariff</code>, <code>building_name</code>) and parses multiple international date formats (<code>YYYY-MM-DD</code> and <code>DD-MM-YYYY</code>).", bullet_style))
    story.append(Paragraph("• <b>Downloadable Sample CSV:</b> One-click template generation produces ready-to-test CSV files for instant evaluation.", bullet_style))
    story.append(Spacer(1, 14))

    # Page break to start section 4
    story.append(PageBreak())

    # ---------------------------------------------------------
    # 3.5 & 3.6 OTHER FEATURES & WORKFLOW
    # ---------------------------------------------------------
    story.append(Paragraph("3.5 Utility Bill Auditing & Rate Inflation Tracking", h2_style))
    story.append(Paragraph(
        "Utility providers frequently adjust seasonal tariffs, fuel surcharges, and peak-hour rate blocks. "
        "PowerPulse's <b>Monthly Utility Bill</b> module records official utility statements and calculates effective cost per unit:",
        body_style
    ))
    story.append(Paragraph(
        "$$\\text{Effective Cost Per Unit} = \\frac{\\text{Total Monthly Bill (₹)}}{\\text{Billed Units Consumed (kWh)}}$$",
        body_style
    ))
    story.append(Paragraph(
        "This metric enables facility managers to distinguish between genuine energy consumption increases and utility rate inflation.",
        body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.6 Executive PDF Audit Export", h2_style))
    story.append(Paragraph(
        "The system includes a ReportLab-powered PDF generator that assembles an audit document complete with executive KPI tables, "
        "7-day ML forecasts with RMSE/MAE metrics, and itemized anomaly logs. Ideal for energy managers submitting reports to management.",
        body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.7 One-Click Instant Demo Experience", h2_style))
    story.append(Paragraph(
        "To allow evaluators and interviewers to explore all features instantly without registering or preparing data, "
        "PowerPulse features an <b>Instant Demo</b> button. With a single click, it sets up an authenticated demo session, seeds 90 days "
        "of realistic daily consumption (featuring weekend cycles, seasonal baselines, and injected equipment anomalies), seeds 3 utility bills, "
        "and automatically trains the forecasting model and anomaly detector.",
        body_style
    ))
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # 4. HOW THE SYSTEM WORKS (END-TO-END PIPELINE)
    # ---------------------------------------------------------
    story.append(Paragraph("4. End-to-End Operational Workflow", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "The diagram below outlines how raw meter readings flow through the PowerPulse processing pipeline into actionable intelligence:",
        body_style
    ))

    flow_data = [
        [Paragraph("Step", table_header), Paragraph("Pipeline Stage", table_header), Paragraph("System Operation & Logic Flow", table_header)],
        [
            Paragraph("<b>1</b>", table_cell_bold),
            Paragraph("<b>Data Ingestion</b>", table_cell_bold),
            Paragraph("Meter reading submitted via web form or batch CSV upload. System validates chronological consistency and computes net kWh.", table_cell),
        ],
        [
            Paragraph("<b>2</b>", table_cell_bold),
            Paragraph("<b>Validation & Costing</b>", table_cell_bold),
            Paragraph("ORM model triggers <code>clean()</code> to verify <code>current_reading >= previous_reading</code>. Multiplies kWh by tariff to determine cost.", table_cell),
        ],
        [
            Paragraph("<b>3</b>", table_cell_bold),
            Paragraph("<b>Anomaly Scanning</b>", table_cell_bold),
            Paragraph("Triggered immediately upon saving. Builds distribution matrix; Isolation Forest & 2.5σ tests flag outliers; logs <code>AnomalyAlert</code>.", table_cell),
        ],
        [
            Paragraph("<b>4</b>", table_cell_bold),
            Paragraph("<b>Feature Engineering</b>", table_cell_bold),
            Paragraph("Transforms sequential readings into Pandas DataFrame. Derives calendar features, lag_1, lag_2, lag_7, and rolling 7-day average.", table_cell),
        ],
        [
            Paragraph("<b>5</b>", table_cell_bold),
            Paragraph("<b>ML Training & Forecast</b>", table_cell_bold),
            Paragraph("Trains Random Forest / Ridge Regressor. Generates recursive multi-day forecast; records RMSE/MAE metrics to <code>PredictionRecord</code>.", table_cell),
        ],
        [
            Paragraph("<b>6</b>", table_cell_bold),
            Paragraph("<b>Visualization & Export</b>", table_cell_bold),
            Paragraph("Renders interactive Chart.js graphs on dashboard. Generates printable ReportLab PDF report upon user download request.", table_cell),
        ],
    ]
    t_flow = Table(flow_data, colWidths=[35, 120, 349])
    t_flow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [c_light_bg, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 14))

    # Page break to start database schema and execution guide on Page 4
    story.append(PageBreak())

    # ---------------------------------------------------------
    # 5. DATABASE SCHEMA
    # ---------------------------------------------------------
    story.append(Paragraph("5. Database Schema & Data Models", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "PowerPulse maintains clean relational data integrity through four core Django ORM models:",
        body_style
    ))

    schema_data = [
        [Paragraph("Model Name", table_header), Paragraph("Key Fields & Types", table_header), Paragraph("Business Rules & Constraints", table_header)],
        [
            Paragraph("<b>ElectricityReading</b>", table_cell_bold),
            Paragraph("<code>user</code> (FK)<br/><code>reading_date</code> (Date)<br/><code>previous_reading</code> (Dec)<br/><code>current_reading</code> (Dec)<br/><code>consumption_kwh</code> (Dec)<br/><code>tariff_per_unit</code> (Dec)<br/><code>estimated_cost</code> (Dec)<br/><code>source</code> (Manual/CSV/Demo)", table_cell),
            Paragraph("Unique per user + date. Validates current >= previous. Automatically computes consumption and estimated cost during <code>save()</code>.", table_cell),
        ],
        [
            Paragraph("<b>MonthlyElectricityBill</b>", table_cell_bold),
            Paragraph("<code>user</code> (FK)<br/><code>billing_month</code> (Date)<br/><code>units_consumed</code> (Dec)<br/><code>bill_amount</code> (Dec)<br/><code>cost_per_unit</code> (Dec)", table_cell),
            Paragraph("Normalized to 1st of each month. Computes <code>cost_per_unit</code> to detect utility tariff inflation over time.", table_cell),
        ],
        [
            Paragraph("<b>AnomalyAlert</b>", table_cell_bold),
            Paragraph("<code>user</code> (FK)<br/><code>reading</code> (FK)<br/><code>reading_date</code> (Date)<br/><code>consumption_kwh</code> (Dec)<br/><code>anomaly_score</code> (Float)<br/><code>reason</code> (VarChar)", table_cell),
            Paragraph("Created by ML anomaly detector when reading exceeds 2.5σ or Isolation Forest threshold. Stores human-readable diagnostic attribution.", table_cell),
        ],
        [
            Paragraph("<b>PredictionRecord</b>", table_cell_bold),
            Paragraph("<code>user</code> (FK)<br/><code>target_date</code> (Date)<br/><code>predicted_kwh</code> (Dec)<br/><code>model_name</code> (VarChar)<br/><code>model_rmse</code> (Float)<br/><code>model_mae</code> (Float)", table_cell),
            Paragraph("Stores multi-day forward projections alongside benchmark accuracy metrics for audit comparison against actual consumption.", table_cell),
        ],
    ]
    t_schema = Table(schema_data, colWidths=[120, 160, 224])
    t_schema.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [c_light_bg, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_schema)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # 6. LOCAL SETUP & RUNNING GUIDE
    # ---------------------------------------------------------
    story.append(Paragraph("6. Platform Setup & Execution Reference", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceBefore=2, spaceAfter=8))

    setup_table_data = [
        [Paragraph("Step / Action", table_header), Paragraph("Commands / Script", table_header), Paragraph("Notes & Expected Output", table_header)],
        [
            Paragraph("<b>One-Click Launch</b>", table_cell_bold),
            Paragraph("<code>.\\start_server.ps1</code><br/><i>or</i> <code>start_server.bat</code>", table_cell),
            Paragraph("Launches development server on <code>http://127.0.0.1:8000/</code>.", table_cell),
        ],
        [
            Paragraph("<b>Automated Test Suite</b>", table_cell_bold),
            Paragraph("<code>python manage.py test</code>", table_cell),
            Paragraph("Executes 18 comprehensive tests across models, auth, CSV, ML, anomalies, and PDF generation.", table_cell),
        ],
        [
            Paragraph("<b>Default Credentials</b>", table_cell_bold),
            Paragraph("<b>Username:</b> <code>admin</code><br/><b>Password:</b> <code>admin123</code>", table_cell),
            Paragraph("Full superuser access to Django admin portal (<code>/admin/</code>) and energy dashboards.", table_cell),
        ],
        [
            Paragraph("<b>Instant Live Demo</b>", table_cell_bold),
            Paragraph("Click <b>'Instant Demo'</b> on navbar or landing page", table_cell),
            Paragraph("Auto-authenticates and seeds 90 days of synthetic energy data with anomalies and trained ML forecast.", table_cell),
        ],
    ]
    t_setup = Table(setup_table_data, colWidths=[120, 170, 214])
    t_setup.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_blue),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [c_light_bg, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_setup)
    story.append(Spacer(1, 14))

    # Summary box
    summary_box_data = [
        [
            Paragraph(
                "<b>PowerPulse Project Summary:</b> PowerPulse provides a complete energy analytics solution combining "
                "enterprise web engineering with applied machine learning. With modular Django apps, automated time-series regression, "
                "unsupervised anomaly detection, and executive reporting, the system turns raw kilowatt-hour data into proactive cost savings.",
                callout_text
            )
        ]
    ]
    t_sum_box = Table(summary_box_data, colWidths=[504])
    t_sum_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 1, c_blue),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_sum_box)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Documentation PDF generated successfully at: {output_path}")

if __name__ == "__main__":
    out1 = Path("PowerPulse_Project_Documentation.pdf").resolve()
    build_pdf(out1)
    
    # Also place a copy in parent folder for easy discovery
    parent_out = Path("..") / "PowerPulse_Project_Documentation.pdf"
    try:
        build_pdf(parent_out.resolve())
    except Exception as e:
        print(f"Parent build note: {e}")
