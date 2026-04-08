"""
Gwinnett County Magistrate Court — local filing context for drafting / review.

Sources (official, as of integration): https://www.gwinnettcourts.com/magistrate/civil-filing-forms
Cross-check forms and fees before filing; courts update PDFs periodically.
"""

from __future__ import annotations

import re

from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING

# Civil clerk line published on dismissal / forms pages (verify if you call).
GWINNETT_MAGISTRATE_CIVIL_CLERK_PHONE = "770-822-8100"

# Hub for civil filing — answers, counterclaims, certificates of service, etc.
GWINNETT_MAGISTRATE_CIVIL_FORMS_URL = "https://www.gwinnettcourts.com/magistrate/civil-filing-forms"

# Injected before USER MESSAGE when Gwinnett Magistrate civil drafting is detected.
GWINNETT_MAGISTRATE_DRAFTING_BLOCK = f"""
GWINNETT COUNTY MAGISTRATE COURT — LOCAL FILING SKELETON (civil claims / answers / counterclaims)

Use this for **structure and local practice pointers** only. The user must verify every requirement with current
court rules, fees, and PDFs. Official forms index: {GWINNETT_MAGISTRATE_CIVIL_FORMS_URL}

**Caption (typical)** — adapt party names and case number from the summons / clerk file:
STATE OF GEORGIA
COUNTY OF GWINNETT
MAGISTRATE COURT OF GWINNETT COUNTY

[Plaintiff name(s)] )
                                   ) Civil Action
vs.                                    ) Case No. ___________
[Defendant name(s)] )

**Answer / counterclaim (align with court’s MAG 10-13)** — Gwinnett publishes **MAG 10-13 Answer and Counterclaim of Defendant**.
An answer should admit or deny the plaintiff’s allegations; list defenses; a counterclaim states the defendant’s claims against the plaintiff.
The court’s form page explains: filing must be **with the clerk** within **30 days** of service unless waiver extends time under **O.C.G.A. § 9-11-4** (the page describes **60 days** from notice when a waiver applies — user must match their summons/waiver facts).

**Certificate of service** — For amendments, answers, and counterclaims after service, Gwinnett typically expects a **MAG 10-04 Certificate of Service** when serving by mail, as described on the forms page (serve opposing party and file with the clerk).

**Party / business naming** — See **MAG 10-09** on listing the correct party or entity (sole prop, corporation, insurance direct actions, etc.).

**Clerk contact (civil)** — {GWINNETT_MAGISTRATE_CIVIL_CLERK_PHONE} (confirm on the court site before relying).

**State Court / transfer** — When jurisdiction exceeds magistrate limits (e.g. counterclaim amount), confirm **transfer** and **e-filing** requirements with the clerk’s current instructions on the county site; mandatory e-filing rules can differ once a case is in State/Superior Court.

**Do not** invent local rules beyond this block; if the vault lacks a statute, do not fabricate O.C.G.A. text — point the user to the official form PDFs and a Georgia-licensed attorney for deadlines and strategy.
""".strip()


# County name alone is not enough — require a civil/magistrate filing cue.
_CIVIL_FILING_CUE = re.compile(
    r"\b("
    r"magistrate|statement\s+of\s+claim|answer|counterclaim|plaintiff|defendant|"
    r"summons|mag\s*10|dispossessory|certificate\s+of\s+service|civil\s+action|"
    r"small\s+claims|landlord|tenant|eviction|garnishment"
    r")\b",
    re.I,
)


def _combined_text(message: str, profile: dict[str, str]) -> str:
    parts = [message or ""]
    for v in profile.values():
        parts.append(str(v))
    return " ".join(parts)


def gwinnett_magistrate_drafting_relevant(message: str, profile: dict[str, str]) -> bool:
    """
    True when the user is likely working on Gwinnett Magistrate civil practice
    (not merely mentioning Georgia generally).
    """
    blob = _combined_text(message, profile).lower()
    if "gwinnett" not in blob:
        return False
    return bool(_CIVIL_FILING_CUE.search(blob))


def should_inject_gwinnett_magistrate_template(
    message: str,
    profile: dict[str, str],
    *,
    document_mode: bool,
    task_hint: str | None,
    audit_mode: bool = False,
) -> bool:
    """Inject local template when Gwinnett Magistrate civil drafting/review is in scope."""
    if not gwinnett_magistrate_drafting_relevant(message, profile):
        return False
    if document_mode or audit_mode:
        return True
    if task_hint == CHAT_TASK_STRENGTHEN_FILING:
        return True
    return False
