#!/usr/bin/env python3
"""
WestMetro ITSM Bulk Importer - Bureaucrat/CRND Service Desk
=============================================================
Server: servicedesk.westmetro.ng
DB: servicedesk.westmetro.ng

Adds missing stages and full route set to ALL request types.

Run:
    cd /opt/odoo/odoo
    sudo -u odoo python3 odoo-bin shell -c /opt/odoo/conf/odoo.conf -d servicedesk.westmetro.ng --no-http < /path/to/itsm_shell_importer_v2.py

Author: WestMetro Limited | www.westmetrong.com
"""

# ============================================================
# STAGE TEMPLATE (matching 3P-API setup)
# ============================================================
# (name, code, sequence, closed, stage_type_id)
# stage_type_id references request_stage_type:
#   1=Draft, 5=Closed(OK), 18=Pending, 19=Escalated, 20=Resolved
#   15=New, 16=Assigned, 17=In Progress, 21=Closed
STAGE_TEMPLATE = [
    ("New",         "new",         5,  False, 15),   # type_id=15 (New)
    ("Assigned",    "assigned",   10,  False, 16),   # type_id=16 (Assigned)
    ("In Progress", "in-progress",11,  False, 17),   # type_id=17 (In Progress)
    ("Pending",     "pending",    12,  False, 18),   # type_id=18 (Pending)
    ("Escalated",   "escalated",  13,  False, 19),   # type_id=19 (Escalated)
    ("Resolved",    "resolved",   14,  True,  20),   # type_id=20 (Resolved), closed=True
    ("Closed",      "close",      15,  True,   5),   # type_id=5  (Closed OK), closed=True
]

# ============================================================
# ROUTE TEMPLATE (9 routes, no New→Closed)
# ============================================================
# (name, from_code, to_code, close, sequence, button_style)
ROUTE_TEMPLATE = [
    ("Assign",              "new",         "assigned",    False, 10, "primary"),
    ("Start Work",          "assigned",    "in-progress", False, 20, "primary"),
    ("Request Info",        "in-progress", "pending",     False, 30, "warning"),
    ("Escalate",            "in-progress", "escalated",   False, 40, "danger"),
    ("Resolve",             "in-progress", "resolved",    False, 50, "success"),
    ("Resume",              "pending",     "in-progress", False, 60, "primary"),
    ("Resolve (Escalated)", "escalated",   "resolved",    False, 70, "success"),
    ("Close",               "resolved",    "close",       True,  80, "default"),
    ("Reopen",              "close",       "new",         False, 90, "warning"),
]

# ============================================================
# STEP 1: GET ALL REQUEST TYPES
# ============================================================
print("\n" + "="*60)
print("  WML ITSM BULK IMPORTER v2")
print("  Bureaucrat/CRND Service Desk")
print("="*60)

all_types = env['request.type'].search([('active', '=', True)])
print(f"\n  Found {len(all_types)} active request types")

# ============================================================
# STEP 2: ADD MISSING STAGES TO EACH TYPE
# ============================================================
print("\n" + "="*60)
print("  IMPORTING STAGES")
print("="*60)

total_stages_created = 0
total_stages_skipped = 0

for rtype in all_types:
    existing_stages = env['request.stage'].search([
        ('request_type_id', '=', rtype.id)
    ])
    existing_codes = {s.code: s for s in existing_stages}

    created_this_type = 0
    for name, code, seq, closed, type_id in STAGE_TEMPLATE:
        if code in existing_codes:
            # Stage exists - check if type_id needs updating
            stage = existing_codes[code]
            updates = {}
            if stage.type_id.id != type_id and type_id:
                updates['type_id'] = type_id
            if stage.closed != closed:
                updates['closed'] = closed
            if stage.sequence != seq:
                updates['sequence'] = seq
            if updates:
                stage.write(updates)
            total_stages_skipped += 1
            continue

        # Create missing stage
        env['request.stage'].create({
            'name': name,
            'code': code,
            'sequence': seq,
            'closed': closed,
            'type_id': type_id,
            'request_type_id': rtype.id,
            'active': True,
        })
        created_this_type += 1
        total_stages_created += 1

    if created_this_type > 0:
        print(f"  ✓ {rtype.code}: +{created_this_type} stages")

env.cr.commit()
print(f"\n  → Created: {total_stages_created} | Existing: {total_stages_skipped}")

# ============================================================
# STEP 3: SET start_stage_id FOR EACH TYPE
# ============================================================
print("\n" + "="*60)
print("  SETTING START STAGES")
print("="*60)

start_count = 0
for rtype in all_types:
    new_stage = env['request.stage'].search([
        ('request_type_id', '=', rtype.id),
        ('code', '=', 'new')
    ], limit=1)
    if new_stage and rtype.start_stage_id.id != new_stage.id:
        rtype.write({'start_stage_id': new_stage.id})
        start_count += 1

env.cr.commit()
print(f"  → Updated {start_count} start stages")

# ============================================================
# STEP 4: REMOVE OLD New→Closed ROUTES & CREATE FULL ROUTES
# ============================================================
print("\n" + "="*60)
print("  IMPORTING ROUTES")
print("="*60)

total_routes_created = 0
total_routes_removed = 0
total_routes_skipped = 0
errors = []

for rtype in all_types:
    # Get all stages for this type keyed by code
    stages = env['request.stage'].search([
        ('request_type_id', '=', rtype.id)
    ])
    stage_map = {s.code: s for s in stages}

    # Verify all required stages exist
    missing = [code for _, code, _, _, _ in STAGE_TEMPLATE if code not in stage_map]
    if missing:
        errors.append(f"  ✗ {rtype.code}: missing stages {missing}")
        continue

    # Remove old direct New→Closed route
    old_routes = env['request.stage.route'].search([
        ('request_type_id', '=', rtype.id),
        ('stage_from_id', '=', stage_map['new'].id),
        ('stage_to_id', '=', stage_map['close'].id),
    ])
    if old_routes:
        old_routes.unlink()
        total_routes_removed += len(old_routes)

    # Get existing routes for this type
    existing_routes = env['request.stage.route'].search([
        ('request_type_id', '=', rtype.id)
    ])
    existing_pairs = {(r.stage_from_id.id, r.stage_to_id.id) for r in existing_routes}

    created_this_type = 0
    for rname, from_code, to_code, close, seq, btn_style in ROUTE_TEMPLATE:
        from_stage = stage_map.get(from_code)
        to_stage = stage_map.get(to_code)

        if not from_stage or not to_stage:
            continue

        # Skip if route already exists
        if (from_stage.id, to_stage.id) in existing_pairs:
            total_routes_skipped += 1
            continue

        env['request.stage.route'].create({
            'name': rname,
            'sequence': seq,
            'stage_from_id': from_stage.id,
            'stage_to_id': to_stage.id,
            'request_type_id': rtype.id,
            'close': close,
            'button_style': btn_style,
            'website_published': True,
        })
        created_this_type += 1
        total_routes_created += 1

    if created_this_type > 0:
        print(f"  ✓ {rtype.code}: +{created_this_type} routes")

env.cr.commit()

if errors:
    print("\n  ERRORS:")
    for e in errors:
        print(e)

print(f"\n  → Created: {total_routes_created} | Removed old: {total_routes_removed} | Existing: {total_routes_skipped}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("  IMPORT COMPLETE")
print("="*60)
print(f"  Request Types processed:  {len(all_types)}")
print(f"  Stages created:           {total_stages_created}")
print(f"  Stages already existed:   {total_stages_skipped}")
print(f"  Routes created:           {total_routes_created}")
print(f"  Old New→Closed removed:   {total_routes_removed}")
print(f"  Routes already existed:   {total_routes_skipped}")
print("="*60)

# Verify totals
final_stages = env['request.stage'].search_count([])
final_routes = env['request.stage.route'].search_count([])
print(f"\n  TOTALS IN DATABASE:")
print(f"  Stages: {final_stages}")
print(f"  Routes: {final_routes}")
print("="*60)
print()
