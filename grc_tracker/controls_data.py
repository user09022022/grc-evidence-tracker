"""Bundled control catalogues.

v0.1 ships a starter set of ISO 27001:2022 Annex A controls spanning all
four themes: Organizational (A.5), People (A.6), Physical (A.7) and
Technological (A.8). Control IDs and titles follow ISO/IEC 27001:2022
Annex A.

v0.2 adds a second catalogue: the SOC 2 Trust Services Criteria common
criteria (CC1-CC9 series, AICPA 2017 Trust Services Criteria). Each
SOC 2 control's theme is its CC category (for example CC6 is "Logical
and Physical Access Controls"). Every control records the framework it
belongs to via its "framework" key.
"""

CONTROLS = [
    # --- Organizational controls (A.5) ---
    {"id": "A.5.1", "framework": "iso27001", "theme": "Organizational",
     "title": "Policies for information security"},
    {"id": "A.5.2", "framework": "iso27001", "theme": "Organizational",
     "title": "Information security roles and responsibilities"},
    {"id": "A.5.7", "framework": "iso27001", "theme": "Organizational",
     "title": "Threat intelligence"},
    {"id": "A.5.19", "framework": "iso27001", "theme": "Organizational",
     "title": "Information security in supplier relationships"},
    {"id": "A.5.24", "framework": "iso27001", "theme": "Organizational",
     "title": "Information security incident management planning and preparation"},
    {"id": "A.5.31", "framework": "iso27001", "theme": "Organizational",
     "title": "Legal, statutory, regulatory and contractual requirements"},
    {"id": "A.5.35", "framework": "iso27001", "theme": "Organizational",
     "title": "Independent review of information security"},
    # --- People controls (A.6) ---
    {"id": "A.6.1", "framework": "iso27001", "theme": "People",
     "title": "Screening"},
    {"id": "A.6.2", "framework": "iso27001", "theme": "People",
     "title": "Terms and conditions of employment"},
    {"id": "A.6.3", "framework": "iso27001", "theme": "People",
     "title": "Information security awareness, education and training"},
    {"id": "A.6.4", "framework": "iso27001", "theme": "People",
     "title": "Disciplinary process"},
    {"id": "A.6.6", "framework": "iso27001", "theme": "People",
     "title": "Confidentiality or non-disclosure agreements"},
    # --- Physical controls (A.7) ---
    {"id": "A.7.1", "framework": "iso27001", "theme": "Physical",
     "title": "Physical security perimeters"},
    {"id": "A.7.2", "framework": "iso27001", "theme": "Physical",
     "title": "Physical entry"},
    {"id": "A.7.4", "framework": "iso27001", "theme": "Physical",
     "title": "Physical security monitoring"},
    {"id": "A.7.8", "framework": "iso27001", "theme": "Physical",
     "title": "Equipment siting and protection"},
    {"id": "A.7.10", "framework": "iso27001", "theme": "Physical",
     "title": "Storage media"},
    {"id": "A.7.13", "framework": "iso27001", "theme": "Physical",
     "title": "Equipment maintenance"},
    # --- Technological controls (A.8) ---
    {"id": "A.8.2", "framework": "iso27001", "theme": "Technological",
     "title": "Privileged access rights"},
    {"id": "A.8.3", "framework": "iso27001", "theme": "Technological",
     "title": "Information access restriction"},
    {"id": "A.8.5", "framework": "iso27001", "theme": "Technological",
     "title": "Secure authentication"},
    {"id": "A.8.9", "framework": "iso27001", "theme": "Technological",
     "title": "Configuration management"},
    {"id": "A.8.13", "framework": "iso27001", "theme": "Technological",
     "title": "Information backup"},
    {"id": "A.8.15", "framework": "iso27001", "theme": "Technological",
     "title": "Logging"},
    {"id": "A.8.24", "framework": "iso27001", "theme": "Technological",
     "title": "Use of cryptography"},
    {"id": "A.8.34", "framework": "iso27001", "theme": "Technological",
     "title": "Protection of information systems during audit testing"},
]

THEMES = ["Organizational", "People", "Physical", "Technological"]


# --- SOC 2 Trust Services Criteria: Common Criteria (CC1-CC9) ---------
# IDs and categories follow the AICPA 2017 Trust Services Criteria.
# Titles are short forms of the criteria text.
SOC2_CONTROLS = [
    # --- CC1: Organization and Management ---
    {"id": "CC1.1", "framework": "soc2", "theme": "Organization and Management",
     "title": "Integrity and ethical values"},
    {"id": "CC1.2", "framework": "soc2", "theme": "Organization and Management",
     "title": "Board independence and oversight of internal control"},
    {"id": "CC1.3", "framework": "soc2", "theme": "Organization and Management",
     "title": "Organizational structure, authority and responsibility"},
    {"id": "CC1.4", "framework": "soc2", "theme": "Organization and Management",
     "title": "Commitment to competence"},
    {"id": "CC1.5", "framework": "soc2", "theme": "Organization and Management",
     "title": "Accountability for internal control responsibilities"},
    # --- CC2: Communication and Information ---
    {"id": "CC2.1", "framework": "soc2", "theme": "Communication and Information",
     "title": "Use of relevant, quality information"},
    {"id": "CC2.2", "framework": "soc2", "theme": "Communication and Information",
     "title": "Internal communication of information"},
    {"id": "CC2.3", "framework": "soc2", "theme": "Communication and Information",
     "title": "Communication with external parties"},
    # --- CC3: Risk Assessment ---
    {"id": "CC3.1", "framework": "soc2", "theme": "Risk Assessment",
     "title": "Specification of objectives"},
    {"id": "CC3.2", "framework": "soc2", "theme": "Risk Assessment",
     "title": "Identification and analysis of risks"},
    {"id": "CC3.3", "framework": "soc2", "theme": "Risk Assessment",
     "title": "Consideration of the potential for fraud"},
    {"id": "CC3.4", "framework": "soc2", "theme": "Risk Assessment",
     "title": "Identification and assessment of significant change"},
    # --- CC4: Monitoring Activities ---
    {"id": "CC4.1", "framework": "soc2", "theme": "Monitoring Activities",
     "title": "Ongoing and separate evaluations"},
    {"id": "CC4.2", "framework": "soc2", "theme": "Monitoring Activities",
     "title": "Evaluation and communication of deficiencies"},
    # --- CC5: Control Activities ---
    {"id": "CC5.1", "framework": "soc2", "theme": "Control Activities",
     "title": "Selection and development of control activities"},
    {"id": "CC5.2", "framework": "soc2", "theme": "Control Activities",
     "title": "Selection and development of general controls over technology"},
    {"id": "CC5.3", "framework": "soc2", "theme": "Control Activities",
     "title": "Deployment of control activities through policies and procedures"},
    # --- CC6: Logical and Physical Access Controls ---
    {"id": "CC6.1", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Logical access security"},
    {"id": "CC6.2", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Authorization of new users"},
    {"id": "CC6.3", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Access authorization, modification and removal"},
    {"id": "CC6.4", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Restriction of physical access"},
    {"id": "CC6.5", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Discontinuation of protections over assets"},
    {"id": "CC6.6", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Protection against external threats"},
    {"id": "CC6.7", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Restriction of information transmission, movement and removal"},
    {"id": "CC6.8", "framework": "soc2", "theme": "Logical and Physical Access Controls",
     "title": "Prevention and detection of unauthorized or malicious software"},
    # --- CC7: System Operations ---
    {"id": "CC7.1", "framework": "soc2", "theme": "System Operations",
     "title": "Detection of changes and unauthorized components"},
    {"id": "CC7.2", "framework": "soc2", "theme": "System Operations",
     "title": "Monitoring of system components and anomalies"},
    {"id": "CC7.3", "framework": "soc2", "theme": "System Operations",
     "title": "Evaluation of security events"},
    {"id": "CC7.4", "framework": "soc2", "theme": "System Operations",
     "title": "Response to security incidents"},
    {"id": "CC7.5", "framework": "soc2", "theme": "System Operations",
     "title": "Recovery from security incidents"},
    # --- CC8: Change Management ---
    {"id": "CC8.1", "framework": "soc2", "theme": "Change Management",
     "title": "Authorized change management"},
    # --- CC9: Risk Mitigation ---
    {"id": "CC9.1", "framework": "soc2", "theme": "Risk Mitigation",
     "title": "Risk mitigation for business disruptions"},
    {"id": "CC9.2", "framework": "soc2", "theme": "Risk Mitigation",
     "title": "Vendor and business partner risk management"},
]

SOC2_THEMES = [
    "Organization and Management",
    "Communication and Information",
    "Risk Assessment",
    "Monitoring Activities",
    "Control Activities",
    "Logical and Physical Access Controls",
    "System Operations",
    "Change Management",
    "Risk Mitigation",
]

FRAMEWORKS = ("iso27001", "soc2")

DEFAULT_FRAMEWORK = "iso27001"

CATALOGUES = {
    "iso27001": CONTROLS,
    "soc2": SOC2_CONTROLS,
}

THEMES_BY_FRAMEWORK = {
    "iso27001": THEMES,
    "soc2": SOC2_THEMES,
}

ALL_CONTROLS = CONTROLS + SOC2_CONTROLS


def controls_for(framework):
    """Return the bundled catalogue for *framework*.

    Raises ValueError for an unknown framework.
    """
    try:
        return CATALOGUES[framework]
    except KeyError:
        raise ValueError(
            f"Unknown framework {framework!r}: "
            f"expected one of {', '.join(FRAMEWORKS)}."
        ) from None


def controls_by_id(framework=None):
    """Return an id -> control mapping.

    With *framework*, only that catalogue is included; without one, all
    catalogues are merged (control ids do not overlap between them).
    """
    if framework is None:
        return {c["id"]: c for c in ALL_CONTROLS}
    return {c["id"]: c for c in controls_for(framework)}


def themes_for(framework):
    """Return the theme/category names for *framework*."""
    controls_for(framework)  # validates the framework name
    return THEMES_BY_FRAMEWORK[framework]


CONTROLS_BY_ID = {c["id"]: c for c in ALL_CONTROLS}

SOC2_CONTROLS_BY_ID = {c["id"]: c for c in SOC2_CONTROLS}
