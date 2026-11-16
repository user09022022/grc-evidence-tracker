"""Bundled control catalogue.

v0.1 ships a starter set of ISO 27001:2022 Annex A controls spanning all
four themes: Organizational (A.5), People (A.6), Physical (A.7) and
Technological (A.8). Control IDs and titles follow ISO/IEC 27001:2022
Annex A.
"""

CONTROLS = [
    # --- Organizational controls (A.5) ---
    {"id": "A.5.1", "theme": "Organizational",
     "title": "Policies for information security"},
    {"id": "A.5.2", "theme": "Organizational",
     "title": "Information security roles and responsibilities"},
    {"id": "A.5.7", "theme": "Organizational",
     "title": "Threat intelligence"},
    {"id": "A.5.19", "theme": "Organizational",
     "title": "Information security in supplier relationships"},
    {"id": "A.5.24", "theme": "Organizational",
     "title": "Information security incident management planning and preparation"},
    {"id": "A.5.31", "theme": "Organizational",
     "title": "Legal, statutory, regulatory and contractual requirements"},
    {"id": "A.5.35", "theme": "Organizational",
     "title": "Independent review of information security"},
    # --- People controls (A.6) ---
    {"id": "A.6.1", "theme": "People",
     "title": "Screening"},
    {"id": "A.6.2", "theme": "People",
     "title": "Terms and conditions of employment"},
    {"id": "A.6.3", "theme": "People",
     "title": "Information security awareness, education and training"},
    {"id": "A.6.4", "theme": "People",
     "title": "Disciplinary process"},
    {"id": "A.6.6", "theme": "People",
     "title": "Confidentiality or non-disclosure agreements"},
    # --- Physical controls (A.7) ---
    {"id": "A.7.1", "theme": "Physical",
     "title": "Physical security perimeters"},
    {"id": "A.7.2", "theme": "Physical",
     "title": "Physical entry"},
    {"id": "A.7.4", "theme": "Physical",
     "title": "Physical security monitoring"},
    {"id": "A.7.8", "theme": "Physical",
     "title": "Equipment siting and protection"},
    {"id": "A.7.10", "theme": "Physical",
     "title": "Storage media"},
    {"id": "A.7.13", "theme": "Physical",
     "title": "Equipment maintenance"},
    # --- Technological controls (A.8) ---
    {"id": "A.8.2", "theme": "Technological",
     "title": "Privileged access rights"},
    {"id": "A.8.3", "theme": "Technological",
     "title": "Information access restriction"},
    {"id": "A.8.5", "theme": "Technological",
     "title": "Secure authentication"},
    {"id": "A.8.9", "theme": "Technological",
     "title": "Configuration management"},
    {"id": "A.8.13", "theme": "Technological",
     "title": "Information backup"},
    {"id": "A.8.15", "theme": "Technological",
     "title": "Logging"},
    {"id": "A.8.24", "theme": "Technological",
     "title": "Use of cryptography"},
    {"id": "A.8.34", "theme": "Technological",
     "title": "Protection of information systems during audit testing"},
]

CONTROLS_BY_ID = {c["id"]: c for c in CONTROLS}

THEMES = ["Organizational", "People", "Physical", "Technological"]
