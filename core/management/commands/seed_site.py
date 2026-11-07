"""Build the whole Ostia Management site tree from scratch.

Re-runnable: everything under the Wagtail root is removed and rebuilt, so the
command is the single source of truth for the launch content.

    python manage.py seed_site
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Page, Site

from wagtail.images.models import Image

from core.models import (
    Certificate,
    ContactFormField,
    ContactPage,
    ServiceIndexPage,
    ServicePage,
    SiteSettings,
    StandardPage,
    VerifyPage,
)
from home.models import HomePage

# --------------------------------------------------------------------------
# Small helpers so the content below reads as data rather than plumbing.
# --------------------------------------------------------------------------


def img(title):
    """Look a photograph up by title; returns None when import_photos has not run."""
    return Image.objects.filter(title=title).first()


def hero(**kwargs):
    return ("hero", kwargs)


def marquee(items, speed="medium"):
    return ("marquee", {"items": items, "speed": speed})


def stats(items, tone="tint", **kwargs):
    kwargs.update({"items": [{"value": v, "label": l} for v, l in items], "tone": tone})
    return ("stats", kwargs)


def feature(**kwargs):
    kwargs.setdefault("tone", "white")
    return ("feature", kwargs)


def cards(card_list, style="plain", tone="paper", **kwargs):
    kwargs.update({"cards": card_list, "style": style, "tone": tone})
    return ("cards", kwargs)


def process(steps, style="steps", tone="tint", **kwargs):
    kwargs.update({"steps": steps, "style": style, "tone": tone})
    return ("process", kwargs)


def chips(chip_list, tone="paper", **kwargs):
    kwargs.update({"chips": chip_list, "tone": tone})
    return ("chips", kwargs)


def certificates(items, tone="tint", **kwargs):
    kwargs.update({"items": items, "tone": tone})
    return ("certificates", kwargs)


def testimonials(items, tone="ink", **kwargs):
    kwargs.update({"items": items, "tone": tone})
    return ("testimonials", kwargs)


def faq(items, tone="paper", **kwargs):
    kwargs.update({"items": [{"question": q, "answer": a} for q, a in items], "tone": tone})
    return ("faq", kwargs)


def document(**kwargs):
    return ("document", kwargs)


def cta(heading, text, label="Get in touch", url="/contact/", secondary=None):
    value = {"heading": heading, "text": text, "button": {"label": label, "url": url}}
    if secondary:
        value["secondary"] = {"label": secondary[0], "url": secondary[1]}
    return ("cta", value)


def text_block(body, tone="paper", **kwargs):
    kwargs.update({"body": body, "tone": tone})
    return ("text", kwargs)


def standards_showcase(limit=8, featured_only=True, tone="tint", **kwargs):
    kwargs.update({"limit": limit, "featured_only": featured_only, "tone": tone})
    return ("standards", kwargs)


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------

STANDARDS = [
    {
        "code": "ISO 9001:2015",
        "slug": "iso-9001-2015",
        "system_name": "Quality Management System",
        "category": "quality",
        "accent": "violet",
        "accredited": True,
        "featured": True,
        "summary": (
            "The world's most widely adopted quality management standard. It helps organisations "
            "deliver consistently, satisfy customers and improve year on year."
        ),
        "overview": (
            "<p>ISO 9001:2015 sets out the requirements for a Quality Management System (QMS). It gives an "
            "organisation a structured framework for managing its processes, meeting customer and regulatory "
            "requirements, and improving performance over time.</p>"
            "<p>The standard is built on a risk-based approach and the principle of continual improvement. It "
            "applies to organisations of every size and in every sector &mdash; manufacturing, construction, "
            "professional services, logistics and the public sector alike.</p>"
            "<p>ISO writes the standards but does not certify against them. Certification is carried out by "
            "independent certification bodies such as Ostia Management, which assess your management system "
            "against the published requirements and issue a certificate when it conforms.</p>"
            "<p>Certification demonstrates a genuine commitment to quality, customer focus and continual "
            "improvement &mdash; and it is increasingly a condition of entry to tenders and supply chains.</p>"
        ),
        "benefits": [
            "Consistent products and services that meet customer expectations",
            "Clear process ownership and fewer costly reworks",
            "Risk-based thinking built into day-to-day decisions",
            "Stronger position in tenders and approved supplier lists",
            "A measurable framework for continual improvement",
            "Greater confidence among customers, regulators and investors",
        ],
    },
    {
        "code": "ISO 14001:2015",
        "slug": "iso-14001-2015",
        "system_name": "Environmental Management System",
        "category": "environment",
        "accent": "mint",
        "accredited": True,
        "featured": True,
        "summary": (
            "A practical framework for managing environmental responsibilities, reducing impact and "
            "meeting the obligations your business is held to."
        ),
        "overview": (
            "<p>ISO 14001:2015 specifies the requirements for an Environmental Management System (EMS). It "
            "helps an organisation identify its environmental aspects and impacts, keep track of its compliance "
            "obligations, and manage them systematically rather than reactively.</p>"
            "<p>The standard covers the full life cycle perspective &mdash; from raw materials and energy use "
            "through to waste, emissions and end-of-life. It asks leadership to set objectives, allocate "
            "resources and review performance against them.</p>"
            "<p>Certification by an independent body gives customers, regulators and investors objective "
            "evidence that environmental commitments are being managed, not merely announced.</p>"
        ),
        "benefits": [
            "A clear register of environmental aspects, impacts and legal obligations",
            "Lower energy, water and raw material consumption",
            "Reduced waste-handling and disposal costs",
            "Credible evidence for ESG and sustainability reporting",
            "Fewer compliance incidents and regulatory surprises",
            "Recognition in tenders that carry environmental criteria",
        ],
    },
    {
        "code": "ISO 45001:2018",
        "slug": "iso-45001-2018",
        "system_name": "Occupational Health & Safety Management System",
        "category": "health-safety",
        "accent": "coral",
        "accredited": True,
        "featured": True,
        "summary": (
            "The international standard for occupational health and safety — built around hazard "
            "control, worker participation and the prevention of harm."
        ),
        "overview": (
            "<p>ISO 45001:2018 sets out the requirements for an Occupational Health and Safety Management "
            "System (OH&amp;SMS). It replaced OHSAS 18001 and brings health and safety into the same high-level "
            "structure as ISO 9001 and ISO 14001, so the three integrate cleanly.</p>"
            "<p>The standard puts emphasis on leadership accountability, the active participation of workers, "
            "and the systematic identification of hazards before they cause harm. It covers everyone who works "
            "under the organisation's control, including contractors and temporary staff.</p>"
            "<p>Certification provides independent assurance that your arrangements for protecting people are "
            "designed, operated and reviewed properly.</p>"
        ),
        "benefits": [
            "Fewer workplace incidents, injuries and lost days",
            "Hazards identified and controlled before harm occurs",
            "Demonstrable compliance with health and safety law",
            "Genuine worker consultation and participation",
            "Lower insurance exposure and claims history",
            "A safety culture that clients and contractors can see",
        ],
    },
    {
        "code": "ISO 27001:2022",
        "slug": "iso-27001-2022",
        "system_name": "Information Security Management System",
        "category": "security",
        "accent": "sky",
        "accredited": False,
        "featured": True,
        "summary": (
            "The benchmark for information security. Protect confidentiality, integrity and availability "
            "with controls chosen on the basis of real risk."
        ),
        "overview": (
            "<p>ISO/IEC 27001:2022 specifies the requirements for an Information Security Management System "
            "(ISMS). It takes a risk-led approach: you identify the information assets that matter, assess the "
            "threats to them, and select controls from Annex A that treat those risks proportionately.</p>"
            "<p>The 2022 revision reorganised the Annex A controls into four themes &mdash; organisational, "
            "people, physical and technological &mdash; and introduced controls covering threat intelligence, "
            "cloud services, data masking and secure coding.</p>"
            "<p>For organisations handling client data, operating in regulated sectors or selling into "
            "enterprise procurement, ISO 27001 certification has become the expected baseline.</p>"
        ),
        "benefits": [
            "A risk assessment that reflects your actual threat landscape",
            "Controls selected and justified through a Statement of Applicability",
            "Stronger answers to client security questionnaires and audits",
            "Supports obligations under UK GDPR and sector regulation",
            "Tested incident response and business continuity arrangements",
            "A recognised credential in enterprise and public sector tenders",
        ],
    },
    {
        "code": "ISO 22000:2018",
        "slug": "iso-22000-2018",
        "system_name": "Food Safety Management System",
        "category": "food-medical",
        "accent": "amber",
        "accredited": True,
        "featured": True,
        "summary": (
            "Food safety management across the whole chain, combining HACCP principles with a management "
            "system that regulators and retailers recognise."
        ),
        "overview": (
            "<p>ISO 22000:2018 specifies the requirements for a Food Safety Management System (FSMS). It "
            "applies to every organisation in the food chain &mdash; growers, processors, packaging suppliers, "
            "transport, storage, retail and food service.</p>"
            "<p>The standard brings together interactive communication, system management, prerequisite "
            "programmes and HACCP principles. It asks you to analyse hazards, establish control measures and "
            "verify that they work in practice.</p>"
            "<p>Certification gives retailers, regulators and consumers independent assurance that food safety "
            "is controlled systematically from end to end.</p>"
        ),
        "benefits": [
            "Hazard analysis and control measures validated against HACCP principles",
            "Prerequisite programmes documented and verified",
            "Traceability and recall arrangements that have been tested",
            "Recognised by retailers and across international food supply chains",
            "Fewer product safety incidents and withdrawals",
            "Integrates with ISO 9001 and other management systems",
        ],
    },
    {
        "code": "ISO 13485:2016",
        "slug": "iso-13485-2016",
        "system_name": "Medical Devices Quality Management System",
        "category": "food-medical",
        "accent": "violet",
        "accredited": False,
        "featured": True,
        "summary": (
            "The quality management standard for medical devices, aligned to the regulatory expectations "
            "that govern the sector throughout the product life cycle."
        ),
        "overview": (
            "<p>ISO 13485:2016 sets out quality management system requirements for organisations involved in "
            "the design, production, installation and servicing of medical devices, and for suppliers of "
            "related services.</p>"
            "<p>Unlike ISO 9001, the emphasis falls on regulatory compliance, risk management across the "
            "product life cycle, design controls, traceability, and documented processes that can withstand "
            "regulatory scrutiny. Continual improvement is framed around maintaining effectiveness and meeting "
            "regulatory requirements.</p>"
            "<p>Certification supports market access and demonstrates control over the processes that regulators "
            "examine most closely.</p>"
        ),
        "benefits": [
            "Design and development controls that stand up to regulatory review",
            "Risk management applied across the full product life cycle",
            "Full traceability of devices, components and records",
            "Validated processes, software and sterile barrier systems",
            "Structured complaint handling and vigilance reporting",
            "Supports access to regulated international markets",
        ],
    },
    {
        "code": "ISO 37001:2016",
        "slug": "iso-37001-2016",
        "system_name": "Anti-Bribery Management System",
        "category": "governance",
        "accent": "coral",
        "accredited": True,
        "featured": True,
        "summary": (
            "An anti-bribery management system that evidences reasonable procedures and a genuine "
            "commitment to ethical business conduct."
        ),
        "overview": (
            "<p>ISO 37001:2016 specifies requirements for an Anti-Bribery Management System (ABMS). It covers "
            "bribery by the organisation, by its personnel and by its business associates &mdash; whether "
            "offered, solicited or accepted, directly or indirectly.</p>"
            "<p>The standard requires a bribery risk assessment, due diligence on projects and business "
            "associates, financial and commercial controls, gifts and hospitality rules, confidential reporting "
            "channels, and a compliance function with real authority.</p>"
            "<p>Certification offers independent evidence that proportionate procedures are in place &mdash; "
            "relevant to organisations exposed to the UK Bribery Act 2010 and comparable legislation.</p>"
        ),
        "benefits": [
            "A documented bribery risk assessment across operations and markets",
            "Due diligence applied to agents, partners and suppliers",
            "Clear gifts, hospitality and donations controls",
            "Confidential reporting channels with anti-retaliation protection",
            "Evidence of proportionate procedures for regulators and boards",
            "Reduced exposure to legal, financial and reputational damage",
        ],
    },
    {
        "code": "ISO 50001:2018",
        "slug": "iso-50001-2018",
        "system_name": "Energy Management System",
        "category": "energy-assets",
        "accent": "mint",
        "accredited": True,
        "featured": True,
        "summary": (
            "A disciplined approach to energy performance: measure it, set a baseline, improve it and "
            "prove the improvement."
        ),
        "overview": (
            "<p>ISO 50001:2018 specifies the requirements for an Energy Management System (EnMS). It gives "
            "organisations a framework for improving energy performance in a way that can be measured and "
            "demonstrated rather than estimated.</p>"
            "<p>The standard requires an energy review, an energy baseline, energy performance indicators and "
            "objectives, alongside controls over design and procurement decisions that lock in consumption for "
            "years.</p>"
            "<p>Certification supports cost reduction and carbon targets, and in the UK can contribute to "
            "compliance routes such as ESOS.</p>"
        ),
        "benefits": [
            "A measured energy baseline and meaningful performance indicators",
            "Significant energy uses identified and brought under control",
            "Lower energy spend and reduced exposure to price volatility",
            "Evidence for carbon reduction and net-zero reporting",
            "Energy efficiency built into procurement and design decisions",
            "Supports ESOS and similar regulatory schemes",
        ],
    },
]

COMPLIANCE_SCHEMES = [
    ("ISO 22301", "iso-22301-certification", "governance", "Business Continuity Management System",
     "Prepare for disruption, keep critical activities running and recover within agreed timeframes."),
    ("ISO 20000-1", "iso-20000-1-certification", "security", "IT Service Management System",
     "Deliver and improve IT services with defined service levels, change control and incident management."),
    ("ISO 31000", "iso-31000-certification", "governance", "Risk Management Guidelines",
     "Embed a consistent approach to identifying, evaluating and treating risk across the organisation."),
    ("ISO 41001:2018", "iso-41001-certification", "energy-assets", "Facility Management System",
     "Manage facilities and workplace services to a defined standard of performance and cost."),
    ("ISO 55001", "iso-55001-certification", "energy-assets", "Asset Management System",
     "Get value from physical assets across their whole life cycle, from acquisition to disposal."),
    ("ISO 39001", "iso-39001-certification", "health-safety", "Road Traffic Safety Management System",
     "Reduce death and serious injury arising from road traffic in your operations and supply chain."),
    ("ISO 20121", "iso-20121-certification", "environment", "Event Sustainability Management System",
     "Plan and deliver events with their social, economic and environmental impacts under control."),
    ("ISO 14046", "iso-14046-certification", "environment", "Water Footprint Assessment",
     "Assess and report the water footprint of products, processes and organisations."),
    ("ISO 18788:2015", "iso-18788-certification", "governance", "Security Operations Management System",
     "Manage private security operations with respect for human rights and the rule of law."),
    ("ISO 10001", "iso-10001-certification", "quality", "Customer Satisfaction Codes of Conduct",
     "Set and keep public commitments on customer conduct that raise satisfaction and trust."),
    ("ISO 10002", "iso-10002-certification", "quality", "Complaints Handling",
     "Handle customer complaints fairly, quickly and in a way that feeds back into improvement."),
    ("ISO 10006", "iso-10006-certification", "quality", "Quality Management in Projects",
     "Apply quality management principles to project processes from initiation through to closure."),
    ("ISO 10015", "iso-10015-certification", "quality", "Competence and Training",
     "Plan, deliver and evaluate training so competence requirements are genuinely met."),
    ("ISO 15000-1", "iso-15000-1-certification", "security", "Electronic Business (ebXML)",
     "Adopt recognised specifications for electronic business messaging and collaboration."),
    ("ISO 21500", "iso-21500-certification", "governance", "Project Management Guidance",
     "Bring a common vocabulary and process model to project delivery across the organisation."),
    ("HACCP", "haccp-certification", "food-medical", "Hazard Analysis & Critical Control Points",
     "The foundation of food safety: identify hazards, set critical limits and control them."),
    ("GMP", "gmp-certification", "food-medical", "Good Manufacturing Practice",
     "Manufacture food, pharmaceutical and cosmetic products under controlled, hygienic conditions."),
    ("HSEMS", "hsems-certification", "health-safety", "Health, Safety & Environment Management",
     "An integrated HSE management system for operations where the three are managed together."),
    ("HCMS", "hcms-certification", "health-safety", "Healthcare Management System",
     "Structure clinical and non-clinical processes around patient safety and service quality."),
    ("Green Building", "green-building-certification", "environment", "Sustainable Building Assessment",
     "Assess buildings against energy, water, materials and indoor environment criteria."),
    ("GOST", "gost-certification", "product", "GOST R Conformity Certification",
     "Conformity certification required for products entering a number of regional markets."),
    ("GS Mark", "gs-mark-certification", "product", "Geprüfte Sicherheit Product Safety",
     "The voluntary German safety mark recognised across European consumer markets."),
    ("FCC", "fcc-certification", "product", "Electromagnetic Compliance",
     "Demonstrate that electronic products meet electromagnetic interference requirements."),
    ("RoHS", "rohs-certification", "product", "Restriction of Hazardous Substances",
     "Evidence that electrical and electronic equipment meets restricted substance limits."),
]

CERT_PROCESS_STEPS = [
    {
        "meta": "Step 1",
        "title": "Application and scope review",
        "text": (
            "You tell us the standard, the activities to be certified, your sites and your headcount. We "
            "review the application, confirm we hold the competence for your sector, calculate the audit "
            "duration and send you a written quotation and programme."
        ),
    },
    {
        "meta": "Step 2",
        "title": "Stage 1 audit",
        "text": (
            "A readiness review. We examine your documented system, confirm the scope and site arrangements, "
            "evaluate your internal audit and management review, and agree what must be in place before "
            "Stage 2. You receive a written report with any areas of concern."
        ),
    },
    {
        "meta": "Step 3",
        "title": "Stage 2 audit",
        "text": (
            "The full assessment of implementation and effectiveness, carried out at your premises. We sample "
            "activities, interview people at every level and gather objective evidence against each clause of "
            "the standard. Findings are raised and classified before we leave site."
        ),
    },
    {
        "meta": "Step 4",
        "title": "Certification decision",
        "text": (
            "The audit file passes to a competent reviewer who took no part in the audit. That independence is "
            "a requirement of ISO/IEC 17021-1:2015 and it is not negotiable. Where the decision is positive, "
            "your certificate is issued with a three-year validity."
        ),
    },
    {
        "meta": "Step 5",
        "title": "Surveillance audits",
        "text": (
            "We return in years one and two to confirm that the system remains implemented and effective, and "
            "that it has kept pace with changes to your business, your obligations and your risks."
        ),
    },
    {
        "meta": "Step 6",
        "title": "Recertification",
        "text": (
            "Before the three-year cycle closes we carry out a recertification audit covering the whole "
            "system, including its performance over the cycle. A fresh certificate is issued and the next "
            "cycle begins."
        ),
    },
]

# Same steps for the cycle diagram, labelled by where they fall in the cycle.
CERT_CYCLE_PHASES = ["Initial certification"] * 4 + ["Years 1 and 2", "Year 3"]
CERT_CYCLE_STEPS = [
    {**step, "meta": phase} for step, phase in zip(CERT_PROCESS_STEPS, CERT_CYCLE_PHASES)
]


# --------------------------------------------------------------------------
# Page builders
# --------------------------------------------------------------------------


def home_body():
    return [
        hero(
            eyebrow="UAF accredited · ISO/IEC 17021-1:2015",
            heading="Certification your market can {word}",
            rotating_words=["trust.", "verify.", "rely on.", "check."],
            intro=(
                "Ostia Management is an independent certification body. We audit and certify management "
                "systems against more than thirty international standards — impartially, competently "
                "and without commercial pressure on the outcome."
            ),
            primary_cta={"label": "Apply for certification", "url": "/contact/"},
            secondary_cta={"label": "Explore schemes", "url": "/services/"},
            highlights=[
                "Accredited by the United Accreditation Foundation",
                "CAB ID 107",
                "UK registered under the Companies Act 2006",
            ],
            image=img("team-meeting"),
        ),
        marquee(
            [
                "ISO 9001", "ISO 14001", "ISO 45001", "ISO 27001", "ISO 22000", "ISO 13485",
                "ISO 37001", "ISO 50001", "ISO 22301", "HACCP", "GMP", "RoHS", "GS Mark",
            ],
            speed="medium",
        ),
        stats(
            [
                ("30+", "Standards and schemes covered"),
                ("6", "Schemes in our UAF accredited scope"),
                ("2", "International offices"),
                ("100%", "Decisions made independently"),
            ],
            tone="tint",
            eyebrow="By the numbers",
            heading="A certification body built for scale",
        ),
        feature(
            eyebrow="Who we are",
            heading="Independent by constitution, not by claim",
            body=(
                "<p>Ostia Management Limited is an independent certification body established in the United "
                "Kingdom and registered under the Companies Act 2006. We operate in accordance with "
                "ISO/IEC 17021-1:2015, the international standard for bodies providing audit and certification "
                "of management systems.</p>"
                "<p>We serve manufacturers, suppliers and service providers across the private and public "
                "sectors, in quality, environment, occupational health and safety, information security, food "
                "safety, medical devices, energy management and anti-bribery.</p>"
            ),
            points=[
                "Accredited by the United Accreditation Foundation, an IAF MLA signatory",
                "Certification decisions taken by reviewers who did not audit",
                "Auditors assigned on sector competence, never on availability alone",
                "Fees never contingent on the outcome of an audit",
            ],
            cta={"label": "About Ostia Management", "url": "/about/"},
            tone="paper",
            image=img("audit"),
        ),
        feature(
            eyebrow="Why organisations choose us",
            heading="Audits that tell you something you did not already know",
            intro=(
                "An audit is only worth the disruption if it surfaces something real. Ours are planned "
                "around your operation and staffed by people who have worked in it."
            ),
            points=[
                "Auditors assigned on sector competence, not availability",
                "Audit duration calculated from IAF mandatory documents",
                "Findings classified consistently, so a major always means the same thing",
                "Integrated audits across several standards in one visit",
                "Written quotation for the full three-year cycle, up front",
            ],
            cta={"label": "See how certification runs", "url": "/certification/"},
            tone="paper",
            reverse=True,
            image=img("factory"),
        ),
        standards_showcase(
            limit=8,
            featured_only=True,
            tone="tint",
            eyebrow="Certification schemes",
            heading="Standards we certify",
            intro=(
                "Eight core management system standards, backed by more than twenty further compliance "
                "schemes. Every one is audited by assessors qualified in your sector."
            ),
        ),
        process(
            CERT_CYCLE_STEPS,
            style="cycle",
            tone="paper",
            eyebrow="How it works",
            heading="Six steps from application to recertification",
            intro=(
                "Every step follows ISO/IEC 17021-1:2015. Before each audit, we confirm who will audit you "
                "and what they will review. Afterwards, we explain what happens next."
            ),
        ),
        certificates(
            [
                {
                    "number": "OML-00012-Q",
                    "standard": "ISO 9001:2015",
                    "holder": "Specimen Holding Ltd.",
                    "issued": "14 Mar 2024",
                    "expires": "13 Mar 2027",
                    "scope": "Design, manufacture and supply of precision engineered components.",
                },
                {
                    "number": "OML-00041-E",
                    "standard": "ISO 14001:2015",
                    "holder": "Specimen Holding Ltd.",
                    "issued": "02 May 2024",
                    "expires": "01 May 2027",
                    "scope": "Environmental management of manufacturing and distribution operations.",
                },
                {
                    "number": "OML-00029-S",
                    "standard": "ISO 45001:2018",
                    "holder": "Specimen Holding Ltd.",
                    "issued": "19 Jun 2024",
                    "expires": "18 Jun 2027",
                    "scope": "Occupational health and safety management across all operational sites.",
                },
            ],
            tone="tint",
            eyebrow="Specimen certificates",
            heading="What you receive",
            intro=(
                "Every certificate carries a unique number, the certified scope and the accreditation mark. "
                "Anyone can check its status on our verification page."
            ),
        ),
        cards(
            [
                {
                    "icon": "⚖",
                    "badge": "Impartiality",
                    "title": "Free from commercial influence",
                    "text": (
                        "Management is committed to carrying out all certification activity impartially and "
                        "without bias. Staff, auditors, contractors and committee members work free of "
                        "commercial, financial or other pressure that could compromise that. Conflicts of "
                        "interest are identified, evaluated and managed."
                    ),
                    "url": "/about/impartiality-policy/",
                },
                {
                    "icon": "\U0001F393",
                    "badge": "Competence",
                    "title": "Auditors qualified in your sector",
                    "text": (
                        "Audit teams are selected against defined competence criteria for the standard, the "
                        "technical area and the sector. Competence is monitored and recorded."
                    ),
                },
                {
                    "icon": "\U0001F4E3",
                    "badge": "Appeals",
                    "title": "A route to challenge us",
                    "text": (
                        "Complaints and appeals about our rules, policies, procedures, decisions or operations "
                        "are handled fairly, impartially, consistently and on time."
                    ),
                    "url": "/certification/appeals-and-complaints/",
                },
                {
                    "icon": "\U0001F50E",
                    "badge": "Transparency",
                    "title": "Published and checkable",
                    "text": (
                        "Our scope, policies and certification conditions are public, and the status of any "
                        "certificate we have issued can be verified by anyone."
                    ),
                    "url": "/verify/",
                },
                {
                    "icon": "\U0001F512",
                    "badge": "Confidentiality",
                    "title": "Your information stays yours",
                    "text": (
                        "Information obtained during audits is treated as confidential, except where "
                        "disclosure is required by law or by our accreditation body."
                    ),
                },
                {
                    "icon": "\U0001F3C5",
                    "badge": "Accreditation",
                    "title": "Independently overseen",
                    "text": (
                        "We are accredited by the United Accreditation Foundation, an IAF MLA signatory, and "
                        "are assessed against ISO/IEC 17021-1:2015."
                    ),
                    "url": "/accreditation/",
                },
            ],
            style="panel",
            tone="paper",
            eyebrow="Our commitments",
            heading="What you are entitled to expect",
        ),
        testimonials(
            [
                {
                    "quote": (
                        "The Stage 1 report was the most useful document we received all year. It told us "
                        "exactly where we stood, with no padding and no surprises at Stage 2."
                    ),
                    "name": "Operations Director",
                    "organisation": "Precision manufacturing, West Midlands",
                    "rating": 5,
                },
                {
                    "quote": (
                        "Our auditor had actually worked in food processing. The questions were the right "
                        "ones and the findings were ones we could act on."
                    ),
                    "name": "Technical Manager",
                    "organisation": "Food production group",
                    "rating": 5,
                },
                {
                    "quote": (
                        "Three standards, one integrated audit programme, one set of dates. It saved us "
                        "weeks of disruption compared with the arrangement we had before."
                    ),
                    "name": "Head of Compliance",
                    "organisation": "Facilities services provider",
                    "rating": 5,
                },
            ],
            tone="ink",
            eyebrow="Client experience",
            heading="What certified organisations tell us",
        ),
        faq(
            [
                (
                    "How long does certification take?",
                    "For a single-site organisation, eight to twelve weeks from application to certificate is "
                    "typical. The time is driven by how ready your system is at Stage 1 and how quickly any "
                    "findings are closed out, rather than by our availability.",
                ),
                (
                    "What does certification cost?",
                    "Audit duration is calculated from your headcount, the number of sites and the complexity "
                    "and risk of your activities, following IAF mandatory documents. We quote the full "
                    "three-year cycle in writing up front, so there are no later surprises.",
                ),
                (
                    "How long is a certificate valid?",
                    "Three years, subject to successful surveillance audits in years one and two. A "
                    "recertification audit before the end of the cycle starts the next three-year period.",
                ),
                (
                    "Can you certify more than one standard at the same time?",
                    "Yes. Integrated audits across ISO 9001, ISO 14001 and ISO 45001 are common and reduce "
                    "both cost and disruption, because shared clauses are audited once.",
                ),
                (
                    "Can we transfer an existing certificate to Ostia Management?",
                    "Yes, where the existing certificate is accredited and in good standing. We review the "
                    "current certificate, the last audit reports and any open findings, then agree a transfer "
                    "date that preserves your existing cycle.",
                ),
                (
                    "Does ISO issue the certificate?",
                    "No. ISO publishes the standards but does not carry out certification. Assessment and "
                    "certification are performed by independent certification bodies such as Ostia Management.",
                ),
            ],
            tone="paper",
            eyebrow="Questions",
            heading="Frequently asked",
        ),
        cta(
            "Ready to start your certification journey?",
            "Talk to our team about the right scheme for your business. We will tell you honestly what is "
            "involved, what it will cost and how long it will take.",
            label="Get in touch",
            url="/contact/",
            secondary=("Verify a certificate", "/verify/"),
        ),
    ]


def build_service(index, data):
    # Photos are titled after the standard family, e.g. iso-9001-2015 -> iso-9001.
    photo = img("-".join(data["slug"].split("-")[:2])) or img("office")
    page = ServicePage(
        title=f"{data['code']} Certification",
        image=photo,
        slug=data["slug"],
        code=data["code"],
        category=data["category"],
        system_name=data["system_name"],
        accent=data["accent"],
        accredited=data["accredited"],
        featured=data["featured"],
        summary=data["summary"],
        overview=data["overview"],
        benefits="\n".join(data["benefits"]),
        show_in_menus=data["featured"],
        body=[
            feature(
                eyebrow="Working with us",
                heading="Why certify with Ostia Management",
                body=(
                    "<p>ISO publishes standards; it does not certify against them. That work is done by "
                    "independent certification bodies. Ostia Management is established in the United Kingdom "
                    "and serves clients internationally, covering first-time certification, transfers from "
                    "another body, and the extension of an existing management system to new standards or "
                    "sites.</p>"
                ),
                points=[
                    "UK established, operating internationally",
                    "Auditors experienced in your technical sector",
                    "A transparent process with written quotations up front",
                    "Impartiality protected by structure, not by promise",
                    "Accredited against ISO/IEC 17021-1:2015",
                    "Integrated audits across multiple standards",
                ],
                cta={"label": "Make an enquiry", "url": "/contact/"},
                tone="paper",
                reverse=True,
            ),
            process(
                CERT_PROCESS_STEPS[:4],
                style="track",
                tone="tint",
                eyebrow="The route to certification",
                heading=f"How {data['code']} certification runs",
            ),
            cta(
                "Ready to start your certification journey?",
                f"Tell us your scope and sites and we will send a {data['code']} quotation and audit "
                "programme for the full three-year cycle.",
                label="Get in touch",
                url="/contact/",
            ),
        ],
    )
    index.add_child(instance=page)
    page.save_revision().publish()
    return page


COMPLIANCE_PHOTOS = ["workspace", "engineer-lab", "server", "training-room", "whiteboard"]


def build_compliance(index, code, slug, category, system_name, summary, order=0):
    page = ServicePage(
        title=f"{code} Certification",
        image=img(COMPLIANCE_PHOTOS[order % len(COMPLIANCE_PHOTOS)]),
        slug=slug,
        code=code,
        category=category,
        system_name=system_name,
        accent="violet",
        accredited=False,
        featured=False,
        summary=summary,
        overview=(
            f"<p>{summary}</p>"
            f"<p>Ostia Management assesses and certifies organisations against {code} as part of our wider "
            "compliance portfolio. Audits are conducted by assessors competent in the relevant technical "
            "area, and certification decisions are taken independently of the audit team.</p>"
            "<p>Where this scheme sits outside our accredited scope, we say so plainly. The audit discipline "
            "is the same; the accreditation mark that appears on the certificate differs.</p>"
        ),
        benefits=(
            "Independent assessment against the published scheme requirements\n"
            "Assessors competent in the relevant technical area\n"
            "A written report with findings you can act on\n"
            "Certification decisions taken independently of the audit team\n"
            "Can be combined with your existing management system audits"
        ),
        body=[
            cta(
                f"Interested in {code}?",
                "Tell us about your scope and we will confirm whether this scheme is the right fit, and what "
                "assessment would involve.",
                label="Make an enquiry",
                url="/contact/",
            )
        ],
    )
    index.add_child(instance=page)
    page.save_revision().publish()
    return page


class Command(BaseCommand):
    help = "Delete and rebuild the Ostia Management site tree."

    @transaction.atomic
    def handle(self, *args, **options):
        root = Page.objects.get(depth=1)

        # Clear everything below the Wagtail root so the command can be re-run.
        for child in root.get_children():
            child.delete()
        Certificate.objects.all().delete()

        home = HomePage(title="Home", slug="home", body=home_body(), show_in_menus=False)
        root.add_child(instance=home)
        home.save_revision().publish()

        site = Site.objects.first()
        if site:
            site.root_page = home
            site.site_name = "Ostia Management"
            site.hostname = site.hostname or "localhost"
            site.save()
        else:
            Site.objects.create(hostname="localhost", port=80, root_page=home, is_default_site=True)

        self._settings(site)
        self._accreditation(home)
        about = self._about(home)
        self._about_children(about)
        services = self._services(home)
        self._compliance(home)
        certification = self._certification(home)
        self._certification_children(certification)
        self._verify(home)
        self._contact(home)
        self._certificates()

        self.stdout.write(self.style.SUCCESS(f"Seeded {Page.objects.live().count()} live pages."))

    # -- settings ---------------------------------------------------------

    def _settings(self, site):
        settings_obj = SiteSettings.objects.first() or SiteSettings()
        settings_obj.phone = "+44 (0)1580 123 456"
        settings_obj.email = "info@ostiamanagement.co.uk"
        settings_obj.address = "Unit 1 Vinehall Business Centre, Robertsbridge, England, TN32 5JW"
        settings_obj.second_office = "Cairo, Egypt"
        settings_obj.opening_hours = "Monday to Friday, 09:00 - 17:30 GMT"
        settings_obj.client_login_url = "https://app.ostiamanagement.co.uk/"
        settings_obj.auditor_login_url = "https://app.ostiamanagement.co.uk/auditor-login"
        settings_obj.linkedin_url = "https://www.linkedin.com/"
        settings_obj.facebook_url = "https://www.facebook.com/"
        settings_obj.youtube_url = "https://www.youtube.com/"
        settings_obj.footer_blurb = (
            "Ostia Management is an independent UK certification body providing audit and certification of "
            "management systems in accordance with ISO/IEC 17021-1:2015."
        )
        settings_obj.legal_line = "Accredited by the United Accreditation Foundation · CAB ID 107"
        settings_obj.save()

    # -- pages ------------------------------------------------------------

    def _accreditation(self, home):
        page = StandardPage(
            title="Accreditation",
            slug="accreditation",
            show_in_menus=True,
            header_image=img("office"),
            eyebrow="Independently overseen",
            intro=(
                "Ostia Management is independently accredited by the United Accreditation Foundation, an IAF "
                "MLA signatory body, for management system certification under ISO/IEC 17021-1:2015."
            ),
            body=[
                feature(
                    eyebrow="United Accreditation Foundation",
                    heading="Accredited, and checkable",
                    body=(
                        "<p>Accreditation is the mechanism by which a certification body is itself audited. "
                        "It is what separates a certificate that carries weight from a printed document.</p>"
                        "<p>Ostia Management holds accreditation from the United Accreditation Foundation "
                        "(UAF) under CAB ID 107. UAF is a signatory to the IAF Multilateral Recognition "
                        "Arrangement, which means certificates issued within our accredited scope are "
                        "recognised internationally.</p>"
                        "<p>Our accreditation can be confirmed directly in the UAF directory. We encourage "
                        "clients and their customers to check it.</p>"
                    ),
                    points=[
                        "CAB ID 107 in the UAF directory",
                        "Assessed against ISO/IEC 17021-1:2015",
                        "IAF MLA recognition for accredited schemes",
                        "UK registered under the Companies Act 2006",
                    ],
                    tone="paper",
                ),
                cards(
                    [
                        {"badge": "ISO 9001:2015", "title": "Quality management", "icon": "✔"},
                        {"badge": "ISO 14001:2015", "title": "Environmental management", "icon": "\U0001F331"},
                        {"badge": "ISO 45001:2018", "title": "Occupational health and safety", "icon": "⛑"},
                        {"badge": "ISO 22000:2018", "title": "Food safety management", "icon": "\U0001F957"},
                        {"badge": "ISO 37001:2016", "title": "Anti-bribery management", "icon": "⚖"},
                        {"badge": "ISO 50001:2018", "title": "Energy management", "icon": "⚡"},
                    ],
                    style="plain",
                    tone="tint",
                    eyebrow="Accredited scope",
                    heading="Schemes covered by our UAF accreditation",
                    intro=(
                        "These six standards sit inside the accredited scope. We also certify further "
                        "schemes outside it, and we always tell you which is which before you commit."
                    ),
                ),
                text_block(
                    "<h2>Schemes outside the accredited scope</h2>"
                    "<p>We also provide certification against ISO/IEC 27001:2022 and ISO 13485:2016, and "
                    "against more than twenty further compliance schemes including HACCP, GMP, RoHS, GS Mark "
                    "and FCC.</p>"
                    "<p>These are audited to the same discipline by assessors competent in the relevant "
                    "technical area, with the same independent certification decision. They are not, however, "
                    "covered by our UAF accreditation, and certificates issued under them do not carry the "
                    "accreditation mark. We state this clearly at quotation stage so that you can judge "
                    "whether the scheme meets your customers' requirements.</p>",
                    tone="paper",
                    eyebrow="Full transparency",
                ),
                cta(
                    "Need certification that your customers will recognise?",
                    "Tell us who is asking for the certificate and why. We will tell you which scheme and "
                    "which accreditation route actually satisfies that requirement.",
                ),
            ],
        )
        home.add_child(instance=page)
        page.save_revision().publish()
        return page

    def _about(self, home):
        page = StandardPage(
            title="About Us",
            slug="about",
            show_in_menus=True,
            header_image=img("team"),
            eyebrow="Driving quality transformation",
            intro=(
                "An independent certification body established in the United Kingdom, operating under "
                "ISO/IEC 17021-1:2015 and serving clients across the private and public sectors."
            ),
            body=[
                feature(
                    eyebrow="Our purpose",
                    heading="Trusted, impartial, internationally recognised",
                    body=(
                        "<p>Our purpose is to drive quality transformation through trusted, impartial and "
                        "internationally recognised certification services.</p>"
                        "<p>We support continual improvement, regulatory compliance and sustainable growth. "
                        "We help organisations improve performance, manage risk, build the confidence of their "
                        "stakeholders, and implement recognised management system standards in a way that is "
                        "practical and cost-effective.</p>"
                        "<p>Ostia Management Limited is registered under the UK Companies Act 2006 and "
                        "provides management system certification to manufacturers, suppliers and service "
                        "providers across many sectors and regions, alongside related training and assurance "
                        "services.</p>"
                    ),
                    points=[
                        "Quality, environmental and occupational health and safety management",
                        "Information security, food safety and medical devices",
                        "Energy management and anti-bribery management",
                        "Private and public sector clients in the UK and internationally",
                    ],
                    tone="paper",
                ),
                stats(
                    [
                        ("30+", "Standards and schemes"),
                        ("6", "UAF accredited schemes"),
                        ("2", "International offices"),
                        ("2006", "Registered under the Companies Act"),
                    ],
                    tone="tint",
                ),
                cards(
                    [
                        {
                            "icon": "⚖",
                            "badge": "Independence",
                            "title": "Structurally impartial",
                            "text": (
                                "We do not consult on the systems we audit. Certification decisions are taken "
                                "by competent reviewers who played no part in the audit."
                            ),
                        },
                        {
                            "icon": "\U0001F393",
                            "badge": "Competence",
                            "title": "The right auditor",
                            "text": (
                                "Audit teams are selected against defined competence criteria for the "
                                "standard, the technical area and the sector. Competence is monitored."
                            ),
                        },
                        {
                            "icon": "\U0001F91D",
                            "badge": "Client focus",
                            "title": "Practical and proportionate",
                            "text": (
                                "Audits are planned around your operation, not around a template. Findings "
                                "are written so that they can actually be acted on."
                            ),
                        },
                        {
                            "icon": "\U0001F501",
                            "badge": "Improvement",
                            "title": "Continual by habit",
                            "text": (
                                "We apply to ourselves the discipline we audit in others: measure, review, "
                                "improve, and evidence the improvement."
                            ),
                        },
                    ],
                    style="plain",
                    tone="tint",
                    eyebrow="What guides us",
                    heading="The principles we work to",
                ),
                cta(
                    "Want to know whether we are the right body for you?",
                    "Ask us directly. If a different certification body is a better fit for your scheme or "
                    "your market, we will say so.",
                ),
            ],
        )
        home.add_child(instance=page)
        page.save_revision().publish()
        return page

    def _about_children(self, about):
        pages = [
            StandardPage(
                title="Vision & Mission",
                slug="vision-mission",
                show_in_menus=True,
                eyebrow="Our purpose",
                intro="Driving quality transformation through trusted certification services.",
                body=[
                    text_block(
                        "<h2>Our vision</h2>"
                        "<p>To drive quality transformation through trusted certification services, and to be "
                        "the certification body that organisations choose when the certificate has to mean "
                        "something.</p>"
                        "<h2>Our mission</h2>"
                        "<p>To drive quality transformation through trusted, impartial and internationally "
                        "recognised certification services.</p>"
                        "<p>We support continual improvement, regulatory compliance and sustainable growth. We "
                        "help organisations improve performance, manage risk, build stakeholder confidence and "
                        "implement recognised management system standards.</p>"
                        "<h2>What we commit to</h2>"
                        "<ul>"
                        "<li>Helping clients meet the requirements of the standards they adopt</li>"
                        "<li>Improving efficiency, governance and operational control</li>"
                        "<li>Demonstrating commitment to quality, safety, security and environmental "
                        "responsibility</li>"
                        "<li>Upholding ethical practice in everything we certify and everything we do</li>"
                        "</ul>",
                        tone="paper",
                    ),
                    chips(
                        [
                            "Impartiality", "Independence", "Professionalism", "Client focus",
                            "Practicality", "Cost-effectiveness", "Continual improvement", "Integrity",
                        ],
                        tone="tint",
                        eyebrow="Our values",
                        heading="Eight words we are prepared to be held to",
                    ),
                    cta(
                        "Ready to start your certification journey?",
                        "Talk to our team about the right scheme for your business.",
                    ),
                ],
            ),
            StandardPage(
                title="Impartiality Policy",
                slug="impartiality-policy",
                show_in_menus=True,
                eyebrow="Our principles",
                intro="Independent, impartial and free from commercial influence.",
                body=[
                    text_block(
                        "<h2>Our commitment</h2>"
                        "<p>The management of Ostia Management is committed to carrying out all certification "
                        "activities impartially, objectively and without bias.</p>"
                        "<p>Staff, auditors, contractors and committee members are required to work free of "
                        "commercial, financial or other pressures that could compromise impartiality. No part "
                        "of anyone's remuneration depends on the outcome of an audit or a certification "
                        "decision.</p>"
                        "<p>We protect the integrity, independence and credibility of our certification work "
                        "by identifying, evaluating and managing potential conflicts of interest on an ongoing "
                        "basis.</p>"
                        "<h2>How impartiality is protected in practice</h2>"
                        "<ul>"
                        "<li>We do not provide management system consultancy to organisations we certify</li>"
                        "<li>We do not provide internal audits to organisations we certify</li>"
                        "<li>Certification decisions are taken by competent personnel who took no part in the "
                        "audit</li>"
                        "<li>Relationships with clients, including those of our personnel, are declared and "
                        "assessed for risk to impartiality</li>"
                        "<li>Auditor assignments are rotated so that no single auditor has indefinite "
                        "responsibility for one client</li>"
                        "<li>An impartiality committee with external representation reviews our arrangements "
                        "and has the authority to act independently</li>"
                        "<li>Threats to impartiality are logged, evaluated and eliminated or reduced to an "
                        "acceptable level, and the response is documented</li>"
                        "</ul>"
                        "<p>Where a threat cannot be reduced to an acceptable level, we decline the work. That "
                        "has a cost, and we accept it.</p>",
                        tone="paper",
                    ),
                    document(
                        title="Annex F - Impartiality Policy",
                        description=(
                            "The complete impartiality policy, including the role and authority of the "
                            "impartiality committee."
                        ),
                        pages="2 pages",
                        eyebrow="Full document",
                    ),
                ],
            ),
            StandardPage(
                title="Quality Policy",
                slug="quality-policy",
                show_in_menus=True,
                eyebrow="Our standard for ourselves",
                intro=(
                    "The discipline we audit in others is the discipline we hold ourselves to."
                ),
                body=[
                    text_block(
                        "<h2>Our quality policy</h2>"
                        "<p>Ostia Management is committed to delivering certification services that are "
                        "accurate, consistent, impartial and valuable to the organisations we assess.</p>"
                        "<p>We operate a management system that meets the requirements of ISO/IEC "
                        "17021-1:2015 and the requirements of our accreditation body. We review it, measure "
                        "it, and improve it.</p>"
                        "<h2>How we deliver on it</h2>"
                        "<ul>"
                        "<li>Audit teams are appointed only where competence against defined criteria has "
                        "been demonstrated and recorded</li>"
                        "<li>Audit duration is calculated in line with IAF mandatory documents, not "
                        "negotiated down to win work</li>"
                        "<li>Reports are factual, evidence-based and issued within agreed timescales</li>"
                        "<li>Findings are classified consistently, so that a major non-conformity means the "
                        "same thing for every client</li>"
                        "<li>Client feedback, complaints and appeals are analysed for trends and feed into "
                        "management review</li>"
                        "<li>Internal audits and management reviews are carried out on a planned cycle</li>"
                        "<li>Objectives for quality are set, measured and reported at every management "
                        "review</li>"
                        "</ul>"
                        "<p>This policy is communicated to all personnel and contractors, reviewed annually, "
                        "and available to any interested party on request.</p>",
                        tone="paper",
                    ),
                    cta(
                        "Questions about how we work?",
                        "We are happy to walk you through our process, our competence criteria and our "
                        "accreditation before you commit to anything.",
                    ),
                ],
            ),
            StandardPage(
                title="Management System Process",
                slug="management-system-process",
                show_in_menus=True,
                eyebrow="How we operate",
                intro=(
                    "Our accredited management system certification process, conducted in accordance with "
                    "ISO/IEC 17021-1:2015."
                ),
                body=[
                    text_block(
                        "<p>The certification process operated by Ostia Management is conducted in accordance "
                        "with the requirements of ISO/IEC 17021-1:2015. It covers application review, Stage 1 "
                        "and Stage 2 audits, an independent certification decision, surveillance audits and "
                        "recertification.</p>",
                        tone="paper",
                    ),
                    process(
                        CERT_PROCESS_STEPS,
                        style="steps",
                        tone="tint",
                        eyebrow="The full cycle",
                        heading="Six stages, three years",
                    ),
                    document(
                        title="Accredited Management System Process",
                        description=(
                            "The complete process document covering application review through to "
                            "recertification, including audit planning, reporting and decision-making."
                        ),
                        pages="14 pages",
                        eyebrow="Full document",
                    ),
                    cta(
                        "Ready to start your certification journey?",
                        "Talk to our team about the right scheme for your business.",
                    ),
                ],
            ),
        ]
        for page in pages:
            about.add_child(instance=page)
            page.save_revision().publish()

    def _services(self, home):
        index = ServiceIndexPage(
            title="Services",
            slug="services",
            show_in_menus=True,
            header_image=img("consultancy"),
            eyebrow="Management system certification",
            intro=(
                "Eight core management system standards, audited by assessors qualified in your sector and "
                "decided independently of the audit team."
            ),
            body=[
                cta(
                    "Not sure which standard you need?",
                    "Tell us who is asking for the certificate and what they need to see. We will point you "
                    "to the scheme that actually answers it.",
                )
            ],
        )
        home.add_child(instance=index)
        index.save_revision().publish()

        for data in STANDARDS:
            build_service(index, data)
        return index

    def _compliance(self, home):
        index = ServiceIndexPage(
            title="Compliance",
            slug="compliance",
            show_in_menus=True,
            header_image=img("engineer-lab"),
            eyebrow="Wider compliance portfolio",
            intro=(
                "More than twenty further schemes, from business continuity and asset management to product "
                "marks and food safety programmes."
            ),
            body=[
                text_block(
                    "<h2>Accredited and non-accredited schemes</h2>"
                    "<p>The schemes on this page sit outside our UAF accredited scope. They are audited to "
                    "the same discipline, by assessors competent in the relevant technical area, with the "
                    "same independent certification decision — but certificates issued under them do not "
                    "carry the accreditation mark.</p>"
                    "<p>We tell you which is which at quotation stage, every time.</p>",
                    tone="paper",
                ),
                cta(
                    "Looking for a scheme that is not listed?",
                    "Our portfolio covers more than thirty standards. Ask us — if we cannot certify it, "
                    "we will tell you who can.",
                ),
            ],
        )
        home.add_child(instance=index)
        index.save_revision().publish()

        for order, (code, slug, category, system_name, summary) in enumerate(COMPLIANCE_SCHEMES):
            build_compliance(index, code, slug, category, system_name, summary, order)
        return index

    def _certification(self, home):
        page = StandardPage(
            title="Certification Process",
            slug="certification",
            show_in_menus=True,
            header_image=img("audit"),
            eyebrow="From application to recertification",
            intro=(
                "The steps in our accredited certification process, and the conditions that apply once a "
                "certificate has been issued."
            ),
            body=[
                process(
                    CERT_PROCESS_STEPS,
                    style="steps",
                    tone="paper",
                    eyebrow="The process",
                    heading="Six stages, conducted under ISO/IEC 17021-1:2015",
                ),
                document(
                    title="Annex E - Certification Process",
                    description="A single-page summary of the certification process for circulation.",
                    pages="1 page",
                    eyebrow="Full document",
                ),
                cta(
                    "Ready to start your certification journey?",
                    "Talk to our team about the right scheme for your business.",
                ),
            ],
        )
        home.add_child(instance=page)
        page.save_revision().publish()
        return page

    def _certification_children(self, parent):
        pages = [
            StandardPage(
                title="Conditions for Certification",
                slug="conditions-for-certification",
                show_in_menus=True,
                eyebrow="Your obligations",
                intro=(
                    "Certified organisations shall comply with all applicable certification scheme "
                    "requirements."
                ),
                body=[
                    text_block(
                        "<h2>What certified organisations must do</h2>"
                        "<p>Certified organisations shall comply with all applicable certification scheme "
                        "requirements. This includes:</p>"
                        "<ul>"
                        "<li>Maintaining continuous conformity with the certified management system "
                        "standard</li>"
                        "<li>Complying with the rules for the use of certification marks</li>"
                        "<li>Informing Ostia Management promptly of significant changes that could affect "
                        "certification &mdash; including changes of ownership, legal status, scope, key "
                        "personnel, sites, processes or the management system itself</li>"
                        "<li>Making arrangements for surveillance and recertification audits to be conducted "
                        "when they are due</li>"
                        "<li>Providing access to records, personnel, sites and — where required — "
                        "to observers and accreditation body assessors</li>"
                        "<li>Keeping records of complaints received and of the action taken on them</li>"
                        "<li>Not using certification in a way that brings Ostia Management or the "
                        "certification scheme into disrepute</li>"
                        "</ul>"
                        "<h2>Suspension and withdrawal</h2>"
                        "<p>Failure to comply with these requirements may result in suspension or withdrawal "
                        "of certification.</p>"
                        "<p>Certification may be suspended where, for example, a surveillance audit is "
                        "refused or repeatedly postponed, major non-conformities are not closed within the "
                        "agreed period, or the certification mark is misused. During suspension the "
                        "certificate is invalid and must not be referred to.</p>"
                        "<p>Where the grounds for suspension are not resolved within the period we set, "
                        "certification is withdrawn and the organisation is removed from the register of "
                        "certified clients. Certificates and all marketing material referring to the "
                        "certification must then be withdrawn from use.</p>"
                        "<p>Certification may also be reduced in scope, where only part of the certified "
                        "activity no longer meets the requirements.</p>",
                        tone="paper",
                    ),
                    document(
                        title="General Conditions for System Certification",
                        description=(
                            "The full contractual conditions governing the grant, maintenance, suspension, "
                            "reduction and withdrawal of certification."
                        ),
                        pages="10 pages",
                        eyebrow="Full document",
                    ),
                ],
            ),
            StandardPage(
                title="Use of Logo",
                slug="use-of-logo",
                show_in_menus=True,
                eyebrow="Certification marks",
                intro=(
                    "How the Ostia Management certification mark and accreditation symbols may be used."
                ),
                body=[
                    text_block(
                        "<h2>Authorised use</h2>"
                        "<p>Organisations certified by Ostia Management are authorised to use the Ostia "
                        "Management certification mark on promotional and marketing materials, including the "
                        "applicable accreditation symbols, provided such use complies with our certification "
                        "scheme and logo usage requirements.</p>"
                        "<p>The certification marks must be used in a manner that accurately reflects the "
                        "scope and status of certification, and must not mislead in any way.</p>"
                        "<h2>Rules that apply</h2>"
                        "<ul>"
                        "<li>The mark may be used only by the certified legal entity, for the certified "
                        "scope, and only while the certificate is valid</li>"
                        "<li>The mark must not be applied to a product, to product packaging, or to anything "
                        "that could be read as product conformity &mdash; management system certification is "
                        "not product certification</li>"
                        "<li>The mark must not appear on laboratory test, calibration or inspection "
                        "reports</li>"
                        "<li>The mark must be reproduced in full, legibly, without alteration to its "
                        "proportions, elements or colours</li>"
                        "<li>Statements about certification must not imply that the certificate covers "
                        "activities, sites or standards outside the certified scope</li>"
                        "<li>Accreditation symbols may be used only where the scheme falls within our "
                        "accredited scope, and only alongside our certification mark</li>"
                        "<li>On suspension or withdrawal, all use of the mark and all references to "
                        "certification must cease immediately</li>"
                        "</ul>"
                        "<h2>Misuse</h2>"
                        "<p>Misuse, misrepresentation or unauthorised use of the certification mark or of "
                        "accreditation symbols may result in corrective action, suspension or withdrawal of "
                        "certification, and where necessary in legal action and publication of the "
                        "transgression.</p>",
                        tone="paper",
                    ),
                    document(
                        title="Annex D - Rules & Regulations for Logo",
                        description=(
                            "Artwork, minimum sizes, clear space and worked examples of correct and "
                            "incorrect use."
                        ),
                        pages="3 pages",
                        eyebrow="Full document",
                    ),
                ],
            ),
            StandardPage(
                title="Appeals & Complaints",
                slug="appeals-and-complaints",
                show_in_menus=True,
                eyebrow="Your right to challenge us",
                intro=(
                    "Complaints and appeals are handled in a fair, impartial, timely and consistent manner."
                ),
                body=[
                    text_block(
                        "<h2>Who may raise one</h2>"
                        "<p>This procedure covers complaints and appeals from clients, certified "
                        "organisations or other interested parties concerning the rules, policies, "
                        "procedures, certification decisions or other operations of Ostia Management.</p>"
                        "<p>An <strong>appeal</strong> is a request to reconsider a decision we have taken "
                        "&mdash; for example a non-conformity raised at audit, or a decision to suspend or "
                        "withdraw certification. A <strong>complaint</strong> is an expression of "
                        "dissatisfaction with our services, our personnel, or the conduct of a certified "
                        "organisation.</p>"
                        "<p>Complaints and appeals are handled in a fair, impartial, timely and consistent "
                        "manner. Submitting one will never, in itself, result in any discriminatory action.</p>",
                        tone="paper",
                    ),
                    process(
                        [
                            {
                                "meta": "Within 2 working days",
                                "title": "Acknowledgement",
                                "text": (
                                    "We confirm receipt in writing, record the matter in the complaints and "
                                    "appeals register, and tell you who is handling it."
                                ),
                            },
                            {
                                "meta": "Within 5 working days",
                                "title": "Validation",
                                "text": (
                                    "We confirm whether the matter relates to certification activities for "
                                    "which we are responsible, and gather the information needed to "
                                    "investigate it."
                                ),
                            },
                            {
                                "meta": "Within 30 days",
                                "title": "Independent investigation",
                                "text": (
                                    "The investigation is carried out by personnel who were not involved in "
                                    "the subject of the complaint or appeal. Where the matter concerns an "
                                    "audit, that excludes the audit team."
                                ),
                            },
                            {
                                "meta": "Decision",
                                "title": "Outcome and notification",
                                "text": (
                                    "The decision is made or reviewed by someone independent of the original "
                                    "decision, communicated to you formally in writing, and accompanied by "
                                    "the reasons for it."
                                ),
                            },
                            {
                                "meta": "Closure",
                                "title": "Correction and improvement",
                                "text": (
                                    "Any correction and corrective action is determined and recorded. Trends "
                                    "are analysed and reported to management review so the same issue does "
                                    "not recur."
                                ),
                            },
                            {
                                "meta": "If still unresolved",
                                "title": "Escalation",
                                "text": (
                                    "If you remain dissatisfied, the matter may be escalated to our "
                                    "impartiality committee and, beyond that, to our accreditation body, the "
                                    "United Accreditation Foundation."
                                ),
                            },
                        ],
                        style="steps",
                        tone="tint",
                        eyebrow="The procedure",
                        heading="How a complaint or appeal is handled",
                    ),
                    text_block(
                        "<h2>How to submit</h2>"
                        "<p>Send your complaint or appeal in writing, by email or by post, stating what "
                        "happened, when, who was involved, what outcome you are seeking, and your contact "
                        "details. Appeals against a certification decision should be submitted within 30 days "
                        "of being notified of that decision.</p>"
                        "<p>Email: <a href=\"mailto:info@ostiamanagement.co.uk\">info@ostiamanagement.co.uk</a></p>"
                        "<p>Post: Unit 1 Vinehall Business Centre, Robertsbridge, England, TN32 5JW</p>",
                        tone="paper",
                    ),
                    document(
                        title="MSP-04 - Complaints & Appeals Procedure",
                        description=(
                            "The full procedure, including responsibilities, timescales, records and "
                            "escalation routes."
                        ),
                        pages="3 pages",
                        eyebrow="Full document",
                    ),
                ],
            ),
        ]
        for page in pages:
            parent.add_child(instance=page)
            page.save_revision().publish()

    def _verify(self, home):
        page = VerifyPage(
            title="Verify",
            slug="verify",
            show_in_menus=True,
            header_image=img("workspace"),
            eyebrow="Certificate check",
            intro=(
                "Check the status of any certificate issued by Ostia Management. Enter the certificate "
                "number exactly as it appears on the document."
            ),
            help_text_above_form="Try OML-00012-Q to see how a valid certificate is reported.",
            body=[
                text_block(
                    "<h2>Why verification matters</h2>"
                    "<p>A certificate is only worth what it can be checked against. Anyone &mdash; a "
                    "customer, a regulator, a procurement team or a member of the public &mdash; can confirm "
                    "here whether a certificate we issued is valid, suspended, withdrawn or expired.</p>"
                    "<p>If the number you have been given returns no result, treat that as significant and "
                    "contact us. We will confirm the position in writing.</p>"
                    "<p>Our own accreditation can be confirmed independently in the United Accreditation "
                    "Foundation directory under CAB ID 107.</p>",
                    tone="paper",
                ),
                cta(
                    "Something does not look right?",
                    "If you believe a certification mark is being misused, tell us. We investigate every "
                    "report and we act on the ones that are founded.",
                    label="Report a concern",
                    url="/contact/",
                ),
            ],
        )
        home.add_child(instance=page)
        page.save_revision().publish()
        return page

    def _contact(self, home):
        page = ContactPage(
            title="Contact",
            slug="contact",
            show_in_menus=True,
            header_image=img("training-room"),
            eyebrow="Get in touch",
            intro=(
                "Tell us the standard, your scope and how many sites you operate, and we will come back "
                "with a quotation and a proposed audit programme."
            ),
            from_address="website@ostiamanagement.co.uk",
            to_address="info@ostiamanagement.co.uk",
            subject="Website enquiry",
            thank_you_text=(
                "<p>Thank you for your enquiry. A member of the certification team will respond within one "
                "working day.</p>"
                "<p>If your enquiry is urgent, call us on +44 (0)1580 123 456.</p>"
            ),
            body=[
                faq(
                    [
                        (
                            "What should I include in my enquiry?",
                            "The standard or standards you are interested in, a short description of the "
                            "activities to be certified, the number of sites and their locations, and your "
                            "total headcount including contractors. That is enough for us to quote.",
                        ),
                        (
                            "How quickly will I get a quotation?",
                            "Usually within one working day. If the scope is complex or spans several sites "
                            "or countries, we may call you first to make sure we have understood it.",
                        ),
                        (
                            "Do you charge for an initial conversation?",
                            "No. Discussing which scheme fits your situation costs nothing and carries no "
                            "obligation.",
                        ),
                        (
                            "Can you audit outside the UK?",
                            "Yes. We operate internationally from our UK and regional offices, and we assign "
                            "auditors with the relevant language and sector competence.",
                        ),
                    ],
                    tone="paper",
                    eyebrow="Before you write",
                    heading="Common questions",
                ),
            ],
        )
        home.add_child(instance=page)

        fields = [
            ("Your name", "singleline", True, "", ""),
            ("Organisation", "singleline", True, "", ""),
            ("Email address", "email", True, "", ""),
            ("Telephone", "singleline", False, "", ""),
            (
                "Standard of interest",
                "dropdown",
                True,
                "",
                "ISO 9001:2015,ISO 14001:2015,ISO 45001:2018,ISO 27001:2022,ISO 22000:2018,"
                "ISO 13485:2016,ISO 37001:2016,ISO 50001:2018,Another scheme,Not sure yet",
            ),
            ("Number of employees", "singleline", False, "Including contractors and part-time staff", ""),
            ("Number of sites", "singleline", False, "", ""),
            (
                "Tell us about your enquiry",
                "multiline",
                True,
                "Describe the activities to be certified and any deadline you are working to.",
                "",
            ),
        ]
        for order, (label, field_type, required, help_text, choices) in enumerate(fields):
            ContactFormField.objects.create(
                page=page,
                sort_order=order,
                label=label,
                field_type=field_type,
                required=required,
                help_text=help_text,
                choices=choices,
            )

        page.save_revision().publish()
        return page

    def _certificates(self):
        rows = [
            ("OML-00012-Q", "Specimen Holding Ltd.", "ISO 9001:2015",
             "Design, manufacture and supply of precision engineered components.",
             "Unit 4 Brookfield Industrial Estate, Rotherham, S60 1AB",
             date(2024, 3, 14), date(2027, 3, 13), "active"),
            ("OML-00041-E", "Specimen Holding Ltd.", "ISO 14001:2015",
             "Environmental management of manufacturing and distribution operations.",
             "Unit 4 Brookfield Industrial Estate, Rotherham, S60 1AB",
             date(2024, 5, 2), date(2027, 5, 1), "active"),
            ("OML-00029-S", "Specimen Holding Ltd.", "ISO 45001:2018",
             "Occupational health and safety management across all operational sites.",
             "Unit 4 Brookfield Industrial Estate, Rotherham, S60 1AB",
             date(2024, 6, 19), date(2027, 6, 18), "active"),
            ("OML-00077-I", "Northgate Data Services Ltd.", "ISO/IEC 27001:2022",
             "Provision of managed hosting and data processing services.",
             "12 Carlisle Court, Leeds, LS1 4HT",
             date(2023, 11, 8), date(2026, 11, 7), "active"),
            ("OML-00103-F", "Harbour Foods Group Ltd.", "ISO 22000:2018",
             "Processing, packing and cold storage of chilled ready meals.",
             "Dockside Way, Hull, HU9 1PQ",
             date(2024, 1, 22), date(2027, 1, 21), "suspended"),
        ]
        for number, holder, standard, scope, site_address, issued, expires, status in rows:
            Certificate.objects.create(
                number=number,
                holder=holder,
                standard=standard,
                scope=scope,
                site_address=site_address,
                issued=issued,
                expires=expires,
                status=status,
            )
