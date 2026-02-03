#!/usr/bin/env python3
"""
WestMetro ITSM Team Setup - Bureaucrat/CRND Service Desk
==========================================================
Server: servicedesk.westmetro.ng
DB: servicedesk.westmetro.ng

Creates 6 teams and maps all 17 services to the correct team.

Run:
    cd /opt/odoo/odoo
    sudo -u odoo python3 odoo-bin shell -c /opt/odoo/conf/odoo.conf -d servicedesk.westmetro.ng --no-http < /path/to/itsm_teams_v3.py

Author: WestMetro Limited | www.westmetrong.com
"""

# ============================================================
# TEAM DEFINITIONS
# ============================================================
TEAMS = [
    {
        "name": "Product Support",
        "description": "Platform-specific technical issues across all WML products — Taxly, ATRS, Akraa, Vendra, 3P portals. First and second line support for client-facing product incidents.",
    },
    {
        "name": "Integration & ERP",
        "description": "ERP deployment projects, system integration (SAP, Odoo, Sage, Dynamics), data migration, UAT, and go-live support. Specialist team handling complex implementation work.",
    },
    {
        "name": "Connectivity & Infrastructure",
        "description": "Network operations for fibre, microwave, and leased line services. Covers outages, installations, site surveys, maintenance, and performance issues.",
    },
    {
        "name": "Account Management",
        "description": "User provisioning, billing, subscriptions, contracts, password resets, and account-level administration across all services.",
    },
    {
        "name": "Sales & Onboarding",
        "description": "Pre-sales inquiries, demos, pricing, proposals, partnership requests, new client onboarding, training, and general inquiries across all products.",
    },
    {
        "name": "Compliance & Security",
        "description": "Regulatory compliance, audit support, compliance alerts, security reviews, and fiscalization compliance across Akraa, ATRS, and related platforms.",
    },
]

# ============================================================
# SERVICE → TEAM MAPPING
# ============================================================
# Maps generic_service name → team name
SERVICE_TEAM_MAP = {
    # Product Support
    "Taxly eInvoice Direct Integration": "Product Support",
    "Taxly eInvoice Middleware":         "Product Support",
    "Taxly Access Point Onboarding":     "Product Support",
    "Akraa Bulk Upload":                 "Product Support",
    "Akraa":                             "Product Support",
    "Akraa Lite":                        "Product Support",
    "Vendra":                            "Product Support",
    "Third Party Portals":               "Product Support",
    "Support Tools":                     "Product Support",

    # Integration & ERP
    "ERP Deployment":                    "Integration & ERP",
    "ERP Integration":                   "Integration & ERP",

    # Connectivity & Infrastructure
    "Fiber Networks":                    "Connectivity & Infrastructure",
    "Microwave Links":                   "Connectivity & Infrastructure",
    "Leased Lines":                      "Connectivity & Infrastructure",

    # Account Management
    "Account Services":                  "Account Management",

    # Sales & Onboarding
    "General Sales":                     "Sales & Onboarding",

    # ATRS Fiscalization → Compliance (regulatory/fiscal compliance)
    "ATRS Fiscalization":                "Compliance & Security",
}

# ============================================================
# STEP 1: CREATE TEAMS
# ============================================================
print("\n" + "="*60)
print("  WML ITSM TEAM SETUP v3")
print("="*60)

print("\n" + "-"*60)
print("  CREATING TEAMS")
print("-"*60)

# Default leader: Soji (id=6). Reassign per team later in UI.
DEFAULT_LEADER_ID = 6

team_ids = {}
for t in TEAMS:
    rec = env['generic.team'].search([('name', '=', t['name'])], limit=1)
    if not rec:
        rec = env['generic.team'].create({
            'name': t['name'],
            'description': t['description'],
            'active': True,
            'leader_id': DEFAULT_LEADER_ID,
        })
        print(f"  ✓ Created: {t['name']} (id={rec.id})")
    else:
        print(f"  ○ Exists:  {t['name']} (id={rec.id})")
    team_ids[t['name']] = rec.id

env.cr.commit()
print(f"\n  → {len(team_ids)} teams ready")

# ============================================================
# STEP 2: ASSIGN TEAMS TO SERVICES
# ============================================================
print("\n" + "-"*60)
print("  MAPPING SERVICES → TEAMS")
print("-"*60)

mapped = 0
unmapped = []
all_services = env['generic.service'].search([('active', '=', True)])

for svc in all_services:
    team_name = SERVICE_TEAM_MAP.get(svc.name)
    if not team_name:
        unmapped.append(svc.name)
        continue

    tid = team_ids.get(team_name)
    if not tid:
        print(f"  ✗ Team '{team_name}' not found for service '{svc.name}'")
        continue

    if svc.team_id.id != tid:
        svc.write({'team_id': tid})
        print(f"  ✓ {svc.name} → {team_name}")
    else:
        print(f"  ○ {svc.name} → {team_name} (already set)")
    mapped += 1

env.cr.commit()

if unmapped:
    print(f"\n  ⚠ Unmapped services ({len(unmapped)}):")
    for u in unmapped:
        print(f"    - {u}")

print(f"\n  → {mapped} services mapped to teams")

# ============================================================
# STEP 3: CREATE ASSIGNMENT POLICY FOR REQUESTS
# ============================================================
print("\n" + "-"*60)
print("  SETTING UP ASSIGNMENT POLICY")
print("-"*60)

# Find request.request model
req_model = env['ir.model'].search([('model', '=', 'request.request')], limit=1)

# Find team_id field on request.request
team_field = env['ir.model.fields'].search([
    ('model', '=', 'request.request'),
    ('name', '=', 'team_id')
], limit=1)

# Find user_id field on request.request
user_field = env['ir.model.fields'].search([
    ('model', '=', 'request.request'),
    ('name', '=', 'user_id')
], limit=1)

if not req_model or not team_field:
    print("  ✗ Could not find request.request model or team_id field")
else:
    # Check if policy already exists
    policy = env['generic.assign.policy'].search([
        ('name', '=', 'ITSM Team Assignment')
    ], limit=1)

    if not policy:
        policy_vals = {
            'name': 'ITSM Team Assignment',
            'model_id': req_model.id,
            'active': True,
            'assign_team_field_id': team_field.id,
            'description': 'Auto-assigns requests to the team linked to the service. Created by WML ITSM importer.',
        }
        if user_field:
            policy_vals['assign_user_field_id'] = user_field.id

        policy = env['generic.assign.policy'].create(policy_vals)
        print(f"  ✓ Created policy: ITSM Team Assignment (id={policy.id})")

        # Create rule: assign by team with round-robin
        rule = env['generic.assign.policy.rule'].create({
            'name': 'Assign to Service Team (Round Robin)',
            'sequence': 10,
            'active': True,
            'policy_id': policy.id,
            'assign_type': 'team',
            'assign_team_choice_type': 'least_loaded',
            'assign_team_sort_direction': 'asc',
        })
        print(f"  ✓ Created rule: Round Robin by Team (id={rule.id})")
    else:
        print(f"  ○ Policy already exists (id={policy.id})")

env.cr.commit()

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("  SETUP COMPLETE")
print("="*60)
print(f"  Teams created:        {len(team_ids)}")
print(f"  Services mapped:      {mapped}")

# Show final mapping
print(f"\n  TEAM → SERVICE MAPPING:")
for team_name in [t['name'] for t in TEAMS]:
    tid = team_ids[team_name]
    services = env['generic.service'].search([('team_id', '=', tid)])
    svc_names = ', '.join(s.name for s in services) if services else '(none)'
    print(f"    {team_name}:")
    for s in services:
        print(f"      • {s.name}")

print("\n" + "="*60)
print("  NEXT STEPS:")
print("  1. Go to Generic Teams → Add members to each team")
print("  2. Assign a Team Leader for each team")
print("  3. Review the assignment policy under Settings")
print("  4. Test: create a request for a FIBER-* type,")
print("     verify it routes to Connectivity & Infrastructure")
print("="*60)
print()
