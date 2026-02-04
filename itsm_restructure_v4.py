#!/usr/bin/env python3
"""
WestMetro ITSM Restructuring v4 - ITIL-Aligned Workflows
============================================================
Server: servicedesk.westmetro.ng
DB: servicedesk.westmetro.ng

This script:
1. Creates new stage types for all workflow templates
2. Adds Change Management category + request types per service
3. Deletes ALL existing stages and routes for every request type
4. Creates workflow-specific stages (with unique colors) and routes
5. Sets start_stage_id for each type

5 Workflow Templates:
  - Incident Management (technical support)
  - Service Request / Fulfillment
  - Change Management (ITIL CAB)
  - Onboarding / Project
  - Sales / Pre-Sales / Inquiry

Run:
    cd /opt/odoo/odoo
    sudo -u odoo python3 odoo-bin shell -c /opt/odoo/conf/odoo.conf \
      -d servicedesk.westmetro.ng --no-http < /path/to/itsm_restructure_v4.py

Author: WestMetro Limited | www.westmetrong.com
"""

import traceback

print("\n" + "=" * 70)
print("  WML ITSM RESTRUCTURING v4 - ITIL-ALIGNED WORKFLOWS")
print("  This will replace ALL existing stages and routes.")
print("=" * 70)

# ================================================================
# STEP 1: CREATE NEW STAGE TYPES
# ================================================================
print("\n" + "-" * 70)
print("  STEP 1: CREATING STAGE TYPES")
print("-" * 70)

STAGE_TYPES = [
    # Incident Management
    ("Logged",              "LOGGED"),
    ("Triaged",             "TRIAGED"),
    # In Progress (17), Escalated (19), Resolved (20), Closed (21) exist
    ("Pending Vendor",      "PENDING-VENDOR"),

    # Service Request
    ("Submitted",           "SUBMITTED"),
    ("Under Review",        "UNDER-REVIEW"),
    ("Approved",            "APPROVED"),
    ("Rejected",            "REJECTED"),
    ("Fulfillment",         "FULFILLMENT"),
    ("Fulfilled",           "FULFILLED"),

    # Change Management
    ("RFC Submitted",       "RFC-SUBMITTED"),
    ("Change Assessment",   "CHANGE-ASSESS"),
    ("CAB Review",          "CAB-REVIEW"),
    ("Scheduled",           "SCHEDULED"),
    ("Implementation",      "IMPLEMENTATION"),
    ("Verification",        "VERIFICATION"),
    ("Closed - Success",    "CLOSED-SUCCESS"),
    ("Closed - Failed",     "CLOSED-FAILED"),
    ("Rolled Back",         "ROLLED-BACK"),

    # Onboarding
    ("Initiated",           "INITIATED"),
    ("Requirements Gathering", "REQ-GATHERING"),
    ("Configuration",       "CONFIGURATION"),
    ("Data Migration",      "DATA-MIGRATION"),
    ("UAT",                 "UAT"),
    ("Training",            "TRAINING"),
    ("Go-Live",             "GO-LIVE"),
    ("Post Go-Live Review", "POST-GOLIVE"),
    ("Completed",           "COMPLETED"),

    # Sales
    ("Received",            "RECEIVED"),
    ("Qualified",           "QUALIFIED"),
    ("Proposal Sent",       "PROPOSAL-SENT"),
    ("Awaiting Response",   "AWAITING-RESP"),
    ("Won",                 "WON"),
    ("Lost",                "LOST"),
]

stage_type_map = {}

# Load existing stage types
for st in env['request.stage.type'].search([]):
    stage_type_map[st.code] = st.id

# Create missing ones
created_st = 0
for name, code in STAGE_TYPES:
    if code not in stage_type_map:
        rec = env['request.stage.type'].create({
            'name': name,
            'code': code,
            'active': True,
        })
        stage_type_map[code] = rec.id
        created_st += 1
        print(f"  + Stage Type: {name} ({code}) id={rec.id}")
    else:
        print(f"  o Exists: {name} ({code})")

env.cr.commit()
print(f"\n  -> Created {created_st} new stage types")

# Also map existing ones we need
for st in env['request.stage.type'].search([]):
    stage_type_map[st.code] = st.id

# ================================================================
# STEP 2: ADD CHANGE MANAGEMENT CATEGORY
# ================================================================
print("\n" + "-" * 70)
print("  STEP 2: ADDING CHANGE MANAGEMENT CATEGORY")
print("-" * 70)

cat_change = env['request.category'].search([('code', '=', 'CAT-CHANGE')], limit=1)
if not cat_change:
    cat_change = env['request.category'].create({
        'name': 'Change Management',
        'code': 'CAT-CHANGE',
        'active': True,
        'sequence': 10,
        'description': 'ITIL Change Management - RFC submission, CAB review, and controlled implementation of changes.',
    })
    print(f"  + Created: Change Management (CAT-CHANGE) id={cat_change.id}")
else:
    print(f"  o Exists: Change Management id={cat_change.id}")

env.cr.commit()

# ================================================================
# STEP 3: CREATE CHANGE MANAGEMENT REQUEST TYPES PER SERVICE
# ================================================================
print("\n" + "-" * 70)
print("  STEP 3: CREATING CHANGE MANAGEMENT REQUEST TYPES")
print("-" * 70)

# Service code prefix -> Change type definition
CHANGE_TYPES = [
    ("Taxly Change Request",              "TAXLY-CHANGE",    "Change request for Taxly eInvoice platform"),
    ("ATRS Change Request",               "ATRS-CHANGE",     "Change request for ATRS Fiscalization system"),
    ("Akraa Change Request",              "AKRAA-CHANGE",    "Change request for Akraa compliance platform"),
    ("Akraa Lite Change Request",         "AKRLITE-CHANGE",  "Change request for Akraa Lite"),
    ("Akraa Bulk Upload Change Request",  "AKRBULK-CHANGE",  "Change request for Akraa Bulk Upload"),
    ("Vendra Change Request",             "VENDRA-CHANGE",   "Change request for Vendra procurement platform"),
    ("3P Portal Change Request",          "3P-CHANGE",       "Change request for Third Party Portals"),
    ("ERP Deployment Change Request",     "ERPDEP-CHANGE",   "Change request for ERP Deployment projects"),
    ("ERP Integration Change Request",    "ERPINT-CHANGE",   "Change request for ERP Integration services"),
    ("Fiber Network Change Request",      "FIBER-CHANGE",    "Change request for Fiber Network infrastructure"),
    ("Microwave Link Change Request",     "MICRO-CHANGE",    "Change request for Microwave Link infrastructure"),
    ("Leased Line Change Request",        "LEASED-CHANGE",   "Change request for Leased Line infrastructure"),
    ("Account Services Change Request",   "ACCT-CHANGE",     "Change request for Account Services"),
    ("General Change Request",            "GEN-CHANGE",      "General change request not specific to a service"),
]

change_type_ids = []
for name, code, desc in CHANGE_TYPES:
    existing = env['request.type'].search([('code', '=', code)], limit=1)
    if not existing:
        rec = env['request.type'].create({
            'name': name,
            'code': code,
            'active': True,
            'description': desc,
        })
        change_type_ids.append(rec.id)
        print(f"  + Created: {name} ({code}) id={rec.id}")
    else:
        change_type_ids.append(existing.id)
        print(f"  o Exists: {name} ({code}) id={existing.id}")

env.cr.commit()

# ================================================================
# STEP 4: CLASSIFY ALL REQUEST TYPES INTO WORKFLOW TEMPLATES
# ================================================================
print("\n" + "-" * 70)
print("  STEP 4: CLASSIFYING REQUEST TYPES")
print("-" * 70)

# Suffix-based classification rules
# Order matters: first match wins

INCIDENT_SUFFIXES = [
    '-SUBMIT', '-VALID', '-CSID', '-API', '-REPORT', '-ACCESS', '-DEVICE',
    '-COMPLY', '-TECH', '-UPLOAD', '-FORMAT', '-DELAY', '-ALERT',
    '-REG', '-DASH', '-DOC', '-VENDOR', '-PO', '-MATCH', '-WF',
    '-SYNC', '-LOGIN', '-CLIENT', '-OUTAGE', '-CONNECT', '-HARDWARE',
    '-PERF', '-PWD', '-PAYMENT',
]

SERVICE_REQUEST_SUFFIXES = [
    '-FEATURE', '-UPGRADE', '-DOWNGRADE', '-CONFIG', '-TEMPLATE',
    '-ADDUSER', '-REMOVEUSER', '-ROLECHANGE', '-BILLING', '-INVOICE',
    '-AMEND', '-RENEWAL', '-INSTALL', '-SURVEY', '-MAINT',
    '-ESCALATE', '-CANCEL',
]

CHANGE_SUFFIXES = ['-CHANGE']

ONBOARD_SUFFIXES = [
    '-ONBOARD', '-GOLIVE', '-POSTLIVE', '-REQ', '-DATAMIG',
    '-INTEG', '-UAT',
]

SALES_SUFFIXES = [
    '-QUERY', '-PRICING', '-DEMO', '-PROPOSAL', '-PARTNER',
    '-FEEDBACK', '-INFO', '-TRAIN', '-ADMINTRAIN',
]

# Special cases for types that don't match suffix rules
SPECIAL_OVERRIDES = {
    'api-key': 'service_request',
    'ERPDEP-CONFIG': 'onboarding',
    'ERPDEP-GOLIVE': 'onboarding',
    'ERPDEP-POSTLIVE': 'onboarding',
    'ERPDEP-REQ': 'onboarding',
    'ERPDEP-DATAMIG': 'onboarding',
    'ERPDEP-INTEG': 'onboarding',
    'ERPDEP-UAT': 'onboarding',
    'ERPINT-NEW': 'onboarding',
    'AKRAA-AUDIT': 'incident',
    'FIBER-MAINT': 'service_request',
}


def classify_type(code):
    """Classify a request type code into a workflow template."""
    if code in SPECIAL_OVERRIDES:
        return SPECIAL_OVERRIDES[code]

    upper = code.upper()

    for suffix in CHANGE_SUFFIXES:
        if upper.endswith(suffix):
            return 'change'

    for suffix in ONBOARD_SUFFIXES:
        if upper.endswith(suffix):
            return 'onboarding'

    for suffix in SALES_SUFFIXES:
        if upper.endswith(suffix):
            return 'sales'

    for suffix in SERVICE_REQUEST_SUFFIXES:
        if upper.endswith(suffix):
            return 'service_request'

    for suffix in INCIDENT_SUFFIXES:
        if upper.endswith(suffix):
            return 'incident'

    # Default: incident
    return 'incident'


# Build classification map
all_types = env['request.type'].search([('active', '=', True)])
classification = {}
counts = {'incident': 0, 'service_request': 0, 'change': 0, 'onboarding': 0, 'sales': 0}

for rt in all_types:
    wf = classify_type(rt.code)
    classification[rt.id] = wf
    counts[wf] += 1

print(f"\n  Classification summary:")
for wf, count in counts.items():
    print(f"    {wf}: {count} types")
print(f"    Total: {sum(counts.values())} types")


# ================================================================
# STEP 5: DEFINE WORKFLOW TEMPLATES
# ================================================================
# Each template: list of (name, code, sequence, closed, stage_type_code, bg_color, label_color)

WHITE_LABEL = "rgba(255,255,255,1)"

WORKFLOWS = {
    'incident': {
        'stages': [
            ("Logged",         "logged",         5,  False, "LOGGED",         "#3498DB", WHITE_LABEL),
            ("Triaged",        "triaged",       10,  False, "TRIAGED",        "#2E86C1", WHITE_LABEL),
            ("In Progress",    "in-progress",   15,  False, "INPROGRESS",     "#F39C12", WHITE_LABEL),
            ("Pending Vendor", "pending-vendor", 20,  False, "PENDING-VENDOR", "#E67E22", WHITE_LABEL),
            ("Escalated",      "escalated",     25,  False, "ESCALATED",      "#E74C3C", WHITE_LABEL),
            ("Resolved",       "resolved",      30,  True,  "RESOLVED",       "#27AE60", WHITE_LABEL),
            ("Closed",         "closed",        35,  True,  "CLOSED",         "#7F8C8D", WHITE_LABEL),
        ],
        'routes': [
            ("Triage",                 "logged",        "triaged",       False, 10, "primary"),
            ("Start Work",             "triaged",       "in-progress",   False, 20, "primary"),
            ("Await Vendor",           "in-progress",   "pending-vendor",False, 30, "warning"),
            ("Escalate",               "in-progress",   "escalated",     False, 40, "danger"),
            ("Resolve",                "in-progress",   "resolved",      False, 50, "success"),
            ("Vendor Responded",       "pending-vendor","in-progress",   False, 60, "primary"),
            ("Resolve (Escalated)",    "escalated",     "resolved",      False, 70, "success"),
            ("De-escalate",            "escalated",     "in-progress",   False, 75, "primary"),
            ("Close",                  "resolved",      "closed",        True,  80, "default"),
            ("Reopen",                 "closed",        "logged",        False, 90, "warning"),
        ],
    },
    'service_request': {
        'stages': [
            ("Submitted",     "submitted",     5,  False, "SUBMITTED",    "#3498DB", WHITE_LABEL),
            ("Under Review",  "under-review",  10, False, "UNDER-REVIEW", "#8E44AD", WHITE_LABEL),
            ("Approved",      "approved",      15, False, "APPROVED",     "#27AE60", WHITE_LABEL),
            ("Rejected",      "rejected",      20, True,  "REJECTED",     "#E74C3C", WHITE_LABEL),
            ("Fulfillment",   "fulfillment",   25, False, "FULFILLMENT",  "#F39C12", WHITE_LABEL),
            ("Fulfilled",     "fulfilled",     30, True,  "FULFILLED",    "#2ECC71", WHITE_LABEL),
            ("Closed",        "closed",        35, True,  "CLOSED",       "#7F8C8D", WHITE_LABEL),
        ],
        'routes': [
            ("Review",                 "submitted",    "under-review",  False, 10, "primary"),
            ("Approve",                "under-review", "approved",      False, 20, "success"),
            ("Reject",                 "under-review", "rejected",      False, 30, "danger"),
            ("Begin Fulfillment",      "approved",     "fulfillment",   False, 40, "primary"),
            ("Mark Fulfilled",         "fulfillment",  "fulfilled",     False, 50, "success"),
            ("Close",                  "fulfilled",    "closed",        True,  60, "default"),
            ("Reopen",                 "closed",       "submitted",     False, 70, "warning"),
            ("Reconsider",             "rejected",     "under-review",  False, 80, "warning"),
        ],
    },
    'change': {
        'stages': [
            ("RFC Submitted",      "rfc-submitted",    5,  False, "RFC-SUBMITTED",   "#3498DB", WHITE_LABEL),
            ("Change Assessment",  "change-assess",   10,  False, "CHANGE-ASSESS",   "#8E44AD", WHITE_LABEL),
            ("CAB Review",         "cab-review",      15,  False, "CAB-REVIEW",      "#2C3E50", WHITE_LABEL),
            ("Approved",           "approved",        20,  False, "APPROVED",         "#27AE60", WHITE_LABEL),
            ("Rejected",           "rejected",        25,  True,  "REJECTED",         "#C0392B", WHITE_LABEL),
            ("Scheduled",          "scheduled",       30,  False, "SCHEDULED",        "#F39C12", WHITE_LABEL),
            ("Implementation",     "implementation",  35,  False, "IMPLEMENTATION",   "#E67E22", WHITE_LABEL),
            ("Verification",       "verification",    40,  False, "VERIFICATION",     "#16A085", WHITE_LABEL),
            ("Closed - Success",   "closed-success",  45,  True,  "CLOSED-SUCCESS",   "#2ECC71", WHITE_LABEL),
            ("Closed - Failed",    "closed-failed",   50,  True,  "CLOSED-FAILED",    "#E74C3C", WHITE_LABEL),
            ("Rolled Back",        "rolled-back",     55,  True,  "ROLLED-BACK",      "#95A5A6", WHITE_LABEL),
        ],
        'routes': [
            ("Assess Change",          "rfc-submitted",  "change-assess",  False, 10, "primary"),
            ("Submit to CAB",          "change-assess",  "cab-review",     False, 20, "primary"),
            ("CAB Approve",            "cab-review",     "approved",       False, 30, "success"),
            ("CAB Reject",             "cab-review",     "rejected",       False, 40, "danger"),
            ("Schedule Change",        "approved",       "scheduled",      False, 50, "primary"),
            ("Begin Implementation",   "scheduled",      "implementation", False, 60, "warning"),
            ("Verify Change",          "implementation", "verification",   False, 70, "primary"),
            ("Rollback",               "implementation", "rolled-back",    False, 75, "danger"),
            ("Close - Success",        "verification",   "closed-success", True,  80, "success"),
            ("Close - Failed",         "verification",   "closed-failed",  True,  85, "danger"),
            ("Reopen as New RFC",      "closed-success", "rfc-submitted",  False, 90, "warning"),
            ("Reopen as New RFC",      "closed-failed",  "rfc-submitted",  False, 91, "warning"),
            ("Reconsider",             "rejected",       "change-assess",  False, 95, "warning"),
        ],
    },
    'onboarding': {
        'stages': [
            ("Initiated",               "initiated",      5,  False, "INITIATED",      "#3498DB", WHITE_LABEL),
            ("Requirements Gathering",  "req-gathering",  10,  False, "REQ-GATHERING",  "#8E44AD", WHITE_LABEL),
            ("Configuration",           "configuration",  15,  False, "CONFIGURATION",  "#F39C12", WHITE_LABEL),
            ("Data Migration",          "data-migration", 20,  False, "DATA-MIGRATION", "#E67E22", WHITE_LABEL),
            ("UAT",                     "uat",            25,  False, "UAT",            "#D35400", WHITE_LABEL),
            ("Training",                "training",       30,  False, "TRAINING",       "#16A085", WHITE_LABEL),
            ("Go-Live",                 "go-live",        35,  False, "GO-LIVE",        "#27AE60", WHITE_LABEL),
            ("Post Go-Live Review",     "post-golive",    40,  False, "POST-GOLIVE",    "#2ECC71", WHITE_LABEL),
            ("Completed",               "completed",      45,  True,  "COMPLETED",      "#7F8C8D", WHITE_LABEL),
        ],
        'routes': [
            ("Gather Requirements",     "initiated",      "req-gathering",  False, 10, "primary"),
            ("Begin Configuration",     "req-gathering",  "configuration",  False, 20, "primary"),
            ("Start Data Migration",    "configuration",  "data-migration", False, 30, "primary"),
            ("Begin UAT",               "data-migration", "uat",            False, 40, "primary"),
            ("Start Training",          "uat",            "training",       False, 50, "primary"),
            ("Go Live",                 "training",       "go-live",        False, 60, "success"),
            ("Post Go-Live Review",     "go-live",        "post-golive",    False, 70, "primary"),
            ("Complete",                "post-golive",    "completed",      True,  80, "success"),
            # Back routes
            ("Revise Requirements",     "configuration",  "req-gathering",  False, 85, "warning"),
            ("Rework Configuration",    "uat",            "configuration",  False, 86, "warning"),
            ("Additional Training",     "go-live",        "training",       False, 87, "warning"),
            # Skip to complete from any active stage
            ("Early Completion",        "req-gathering",  "completed",      True,  90, "default"),
            ("Early Completion",        "configuration",  "completed",      True,  91, "default"),
            ("Early Completion",        "data-migration", "completed",      True,  92, "default"),
            ("Early Completion",        "uat",            "completed",      True,  93, "default"),
            ("Early Completion",        "training",       "completed",      True,  94, "default"),
            # Reopen
            ("Reopen",                  "completed",      "initiated",      False, 99, "warning"),
        ],
    },
    'sales': {
        'stages': [
            ("Received",           "received",        5,  False, "RECEIVED",       "#3498DB", WHITE_LABEL),
            ("Qualified",          "qualified",       10,  False, "QUALIFIED",      "#8E44AD", WHITE_LABEL),
            ("In Progress",        "in-progress",     15,  False, "INPROGRESS",     "#F39C12", WHITE_LABEL),
            ("Proposal Sent",      "proposal-sent",   20,  False, "PROPOSAL-SENT",  "#E67E22", WHITE_LABEL),
            ("Awaiting Response",  "awaiting-resp",   25,  False, "AWAITING-RESP",  "#D4AC0D", WHITE_LABEL),
            ("Won",                "won",             30,  True,  "WON",            "#27AE60", WHITE_LABEL),
            ("Lost",               "lost",            35,  True,  "LOST",           "#E74C3C", WHITE_LABEL),
            ("Closed",             "closed",          40,  True,  "CLOSED",         "#7F8C8D", WHITE_LABEL),
        ],
        'routes': [
            ("Qualify",                "received",       "qualified",      False, 10, "primary"),
            ("Start Work",            "qualified",      "in-progress",    False, 20, "primary"),
            ("Send Proposal",         "in-progress",    "proposal-sent",  False, 30, "primary"),
            ("Awaiting Response",     "proposal-sent",  "awaiting-resp",  False, 40, "warning"),
            ("Mark Won",              "awaiting-resp",  "won",            False, 50, "success"),
            ("Mark Lost",             "awaiting-resp",  "lost",           False, 60, "danger"),
            ("Close (Won)",           "won",            "closed",         True,  70, "default"),
            ("Close (Lost)",          "lost",           "closed",         True,  80, "default"),
            ("Reopen",                "closed",         "received",       False, 90, "warning"),
            # Direct close from any stage
            ("Direct Win",            "in-progress",    "won",            False, 91, "success"),
            ("Direct Loss",           "in-progress",    "lost",           False, 92, "danger"),
            ("Revise Proposal",       "awaiting-resp",  "in-progress",   False, 93, "warning"),
        ],
    },
}

# ================================================================
# STEP 6: DELETE ALL EXISTING STAGES AND ROUTES, RECREATE
# ================================================================
print("\n" + "-" * 70)
print("  STEP 6: REPLACING STAGES AND ROUTES")
print("-" * 70)

total_deleted_routes = 0
total_deleted_stages = 0
total_created_stages = 0
total_created_routes = 0
errors = []

for rt in all_types:
    wf_name = classification[rt.id]
    wf = WORKFLOWS[wf_name]

    try:
        # Delete existing routes for this type
        old_routes = env['request.stage.route'].search([('request_type_id', '=', rt.id)])
        if old_routes:
            total_deleted_routes += len(old_routes)
            old_routes.unlink()

        # Delete existing stages for this type
        old_stages = env['request.stage'].search([('request_type_id', '=', rt.id)])
        if old_stages:
            total_deleted_stages += len(old_stages)
            old_stages.unlink()

        env.cr.commit()

        # Create new stages
        stage_map = {}
        for sname, scode, seq, closed, st_code, bg, lbl in wf['stages']:
            st_id = stage_type_map.get(st_code)
            vals = {
                'name': sname,
                'code': scode,
                'sequence': seq,
                'closed': closed,
                'request_type_id': rt.id,
                'active': True,
                'bg_color': bg,
                'label_color': lbl,
                'use_custom_colors': True,
            }
            if st_id:
                vals['type_id'] = st_id
            stage = env['request.stage'].create(vals)
            stage_map[scode] = stage.id
            total_created_stages += 1

        env.cr.commit()

        # Set start stage
        first_code = wf['stages'][0][1]
        rt.write({'start_stage_id': stage_map[first_code]})

        # Create routes
        for rname, from_code, to_code, close, seq, btn in wf['routes']:
            from_id = stage_map.get(from_code)
            to_id = stage_map.get(to_code)
            if not from_id or not to_id:
                continue
            env['request.stage.route'].create({
                'name': rname,
                'sequence': seq,
                'stage_from_id': from_id,
                'stage_to_id': to_id,
                'request_type_id': rt.id,
                'close': close,
                'button_style': btn,
                'website_published': True,
            })
            total_created_routes += 1

        env.cr.commit()
        print(f"  ✓ {rt.code} -> {wf_name} ({len(wf['stages'])} stages, {len(wf['routes'])} routes)")

    except Exception as e:
        env.cr.rollback()
        errors.append(f"  ✗ {rt.code}: {str(e)}")
        print(f"  ✗ {rt.code}: {str(e)}")
        traceback.print_exc()

# ================================================================
# SUMMARY
# ================================================================
print("\n" + "=" * 70)
print("  RESTRUCTURING COMPLETE")
print("=" * 70)
print(f"  Request Types processed:  {len(all_types)}")
print(f"  Stages deleted:           {total_deleted_stages}")
print(f"  Stages created:           {total_created_stages}")
print(f"  Routes deleted:           {total_deleted_routes}")
print(f"  Routes created:           {total_created_routes}")
print(f"  Change Management types:  {len(change_type_ids)}")

if errors:
    print(f"\n  ERRORS ({len(errors)}):")
    for e in errors:
        print(e)

# Verify totals
final_stages = env['request.stage'].search_count([])
final_routes = env['request.stage.route'].search_count([])
print(f"\n  FINAL TOTALS:")
print(f"  Stages in DB: {final_stages}")
print(f"  Routes in DB: {final_routes}")

print(f"\n  WORKFLOW DISTRIBUTION:")
for wf_name, count in counts.items():
    wf = WORKFLOWS[wf_name]
    print(f"    {wf_name}: {count} types x {len(wf['stages'])} stages x {len(wf['routes'])} routes")

print("\n" + "=" * 70)
print("  NEXT STEPS:")
print("  1. Verify in UI: servicedesk.westmetro.ng")
print("  2. Test each workflow template with a sample request")
print("  3. Assign team members and configure SLAs")
print("  4. Update training materials with new workflows")
print("=" * 70)
print()
