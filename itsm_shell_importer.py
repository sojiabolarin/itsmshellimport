#!/usr/bin/env python3
"""
WestMetro ITSM Bulk Importer - Odoo Shell Version
===================================================
Run directly on your Odoo server. No XML-RPC, no network.

Server: servicedesk.westmetro.ng

Run:
    cd /opt/odoo/odoo
    python3 odoo-bin shell -c /opt/odoo/odoo.conf -d servicedesk.westmetro.ng --no-http < /opt/odoo/itsm_shell_importer.py

Author: WestMetro Limited | www.westmetrong.com
"""

# ============================================================
# SECURITY GROUPS
# ============================================================
print("\n" + "="*60)
print("  IMPORTING SECURITY GROUPS")
print("="*60)

cat = env['ir.module.category'].search([('name', 'ilike', 'Helpdesk')], limit=1)
cat_id = cat.id if cat else False

GROUPS = [
    "L1 Support", "L2 Support", "L3 Support / Specialist",
    "Service Desk", "Change Manager", "CAB Member",
    "Problem Manager", "IT Security", "IAM Team",
    "IT Asset Manager", "IT Operations", "IT Onboarding Team",
    "Fulfillment Team", "Request Approver", "Data Owner",
]

group_ids = {}
for g in GROUPS:
    rec = env['res.groups'].search([('name', '=', g)], limit=1)
    if not rec:
        rec = env['res.groups'].create({'name': g, 'category_id': cat_id})
    group_ids[g] = rec.id
    print(f"  ✓ {g}")

print(f"  → {len(group_ids)} groups ready")
env.cr.commit()

# ============================================================
# HELPDESK TEAMS
# ============================================================
print("\n" + "="*60)
print("  IMPORTING HELPDESK TEAMS")
print("="*60)

TEAMS = [
    {"name": "Incident Management", "use_sla": True, "use_rating": True, "use_website_helpdesk_form": True, "assign_method": "balanced"},
    {"name": "Service Request", "use_sla": True, "use_rating": True, "use_website_helpdesk_form": True, "assign_method": "balanced"},
    {"name": "Change Management", "use_sla": True, "use_rating": False, "assign_method": "manual"},
    {"name": "Problem Management", "use_sla": True, "use_rating": False, "assign_method": "manual"},
    {"name": "Asset Request", "use_sla": True, "use_rating": True, "use_website_helpdesk_form": True, "assign_method": "balanced"},
    {"name": "Access Request", "use_sla": True, "use_rating": True, "use_website_helpdesk_form": True, "assign_method": "balanced"},
    {"name": "General Inquiry", "use_sla": True, "use_rating": True, "use_website_helpdesk_form": True, "assign_method": "balanced"},
    {"name": "Onboarding Request", "use_sla": True, "use_rating": True, "assign_method": "manual"},
    {"name": "Offboarding Request", "use_sla": True, "use_rating": False, "assign_method": "manual"},
    {"name": "Maintenance Request", "use_sla": True, "use_rating": False, "assign_method": "manual"},
]

team_ids = {}
for t in TEAMS:
    rec = env['helpdesk.team'].search([('name', '=', t['name'])], limit=1)
    if not rec:
        rec = env['helpdesk.team'].create(t)
    team_ids[t['name']] = rec.id
    print(f"  ✓ {t['name']} (id={rec.id})")

print(f"  → {len(team_ids)} teams ready")
env.cr.commit()

# ============================================================
# STAGES
# ============================================================
print("\n" + "="*60)
print("  IMPORTING STAGES")
print("="*60)

STAGES = {
    "Incident Management": [
        ("New", 10, False, False),
        ("Assigned", 20, False, False),
        ("In Progress", 30, False, False),
        ("Pending", 40, False, False),
        ("Escalated", 50, False, False),
        ("Resolved", 60, False, False),
        ("Closed", 70, True, True),
    ],
    "Service Request": [
        ("New", 10, False, False),
        ("Pending Approval", 15, False, False),
        ("Assigned", 20, False, False),
        ("In Progress", 30, False, False),
        ("Pending", 40, False, False),
        ("Resolved", 60, False, False),
        ("Closed", 70, True, True),
        ("Rejected", 75, True, True),
    ],
    "Change Management": [
        ("Draft", 5, False, False),
        ("Submitted for Review", 10, False, False),
        ("Approved - Scheduled", 20, False, False),
        ("Implementation", 30, False, False),
        ("Paused", 40, False, False),
        ("Emergency Stop", 50, False, False),
        ("Verification", 60, False, False),
        ("Closed - Successful", 70, True, True),
        ("Closed - Failed", 75, True, True),
        ("Rejected by CAB", 80, True, True),
    ],
    "Problem Management": [
        ("Identified", 10, False, False),
        ("Under Investigation", 20, False, False),
        ("Root Cause Analysis", 30, False, False),
        ("Pending Vendor", 40, False, False),
        ("Escalated to Vendor", 50, False, False),
        ("Workaround Available", 55, False, False),
        ("Root Cause Fixed", 60, False, False),
        ("Closed", 70, True, True),
    ],
    "Asset Request": [
        ("New", 10, False, False),
        ("Manager Approval", 15, False, False),
        ("IT Approved", 20, False, False),
        ("Provisioning", 30, False, False),
        ("Pending Stock", 40, False, False),
        ("Ready for Delivery", 60, False, False),
        ("Delivered", 70, True, True),
        ("Rejected", 75, True, True),
    ],
    "Access Request": [
        ("New", 10, False, False),
        ("Data Owner Approval", 15, False, False),
        ("Security Review", 20, False, False),
        ("Provisioning Access", 30, False, False),
        ("Access Granted", 60, False, False),
        ("Confirmed", 70, True, True),
        ("Rejected", 75, True, True),
    ],
    "General Inquiry": [
        ("New", 10, False, False),
        ("Assigned", 20, False, False),
        ("In Progress", 30, False, False),
        ("Awaiting Clarification", 40, False, False),
        ("Escalated to Expert", 50, False, False),
        ("Answered", 60, False, False),
        ("Closed", 70, True, True),
    ],
    "Onboarding Request": [
        ("Initiated", 10, False, False),
        ("Tasks Assigned", 20, False, False),
        ("Preparing", 30, False, False),
        ("Pending Dependencies", 40, False, False),
        ("Ready for Day 1", 60, False, False),
        ("Completed", 70, True, True),
    ],
    "Offboarding Request": [
        ("Initiated", 10, False, False),
        ("Tasks Assigned", 20, False, False),
        ("Data Backup", 25, False, False),
        ("Access Revocation", 30, False, False),
        ("Asset Collection", 40, False, False),
        ("Audit Complete", 60, False, False),
        ("Archived", 70, True, True),
    ],
    "Maintenance Request": [
        ("Scheduled", 10, False, False),
        ("Approved", 20, False, False),
        ("In Progress", 30, False, False),
        ("Issue Encountered", 50, False, False),
        ("Verification", 60, False, False),
        ("Completed", 70, True, True),
    ],
}

stage_ids = {}  # (team_name, stage_name) -> id
total_stages = 0

for team_name, stages in STAGES.items():
    tid = team_ids.get(team_name)
    if not tid:
        print(f"  ✗ Team '{team_name}' not found, skipping")
        continue

    print(f"\n  [{team_name}]")
    for name, seq, fold, is_close in stages:
        rec = env['helpdesk.stage'].search([
            ('name', '=', name),
            ('team_ids', 'in', [tid])
        ], limit=1)
        if not rec:
            rec = env['helpdesk.stage'].create({
                'name': name,
                'sequence': seq,
                'fold': fold,
                'is_close': is_close,
                'team_ids': [(4, tid)],
            })
        stage_ids[(team_name, name)] = rec.id
        total_stages += 1
        tag = " [CLOSE]" if is_close else ""
        print(f"    ✓ {name} (seq={seq}){tag}")

print(f"\n  → {total_stages} stages imported")
env.cr.commit()

# ============================================================
# TICKET TYPES
# ============================================================
print("\n" + "="*60)
print("  IMPORTING TICKET TYPES")
print("="*60)

TICKET_TYPES = [
    "Hardware Issue", "Software Issue", "Network/Connectivity",
    "Email/Collaboration", "Printer/Peripheral", "Access/Login Issue",
    "Performance Issue", "Security Incident", "Data/File Issue", "Other Incident",
    "New User Setup", "Software Installation", "Hardware Request",
    "Access Request", "Email/Distribution List", "Training Request",
    "Report Request", "Move/Add/Change", "Other Service Request",
    "Standard Change", "Normal Change", "Emergency Change",
    "Infrastructure Change", "Application Change", "Security Change",
    "System Access", "Application Access", "Network/VPN Access",
    "Physical Access (Badge)", "Admin/Elevated Access", "External/Vendor Access",
    "Laptop", "Desktop", "Monitor", "Mobile Device",
    "Peripheral (Keyboard, Mouse, etc.)", "Software License",
    "Asset Replacement", "Asset Return",
    "How-To Question", "Policy Question", "Status Inquiry",
    "Feedback/Suggestion", "General Question",
    "Scheduled Maintenance", "Preventive Maintenance", "Patch/Update",
    "Backup/Recovery Test", "Infrastructure Maintenance",
]

tt_count = 0
for tt in TICKET_TYPES:
    rec = env['helpdesk.ticket.type'].search([('name', '=', tt)], limit=1)
    if not rec:
        env['helpdesk.ticket.type'].create({'name': tt})
    tt_count += 1

print(f"  → {tt_count} ticket types imported")
env.cr.commit()

# ============================================================
# SLA POLICIES
# ============================================================
print("\n" + "="*60)
print("  IMPORTING SLA POLICIES")
print("="*60)

SLAS = {
    "Incident Management": [
        ("INC Critical - First Response", "3", "Assigned", 0.25, 0),
        ("INC Critical - Resolution", "3", "Resolved", 4, 0),
        ("INC High - First Response", "2", "Assigned", 1, 0),
        ("INC High - Resolution", "2", "Resolved", 8, 0),
        ("INC Medium - First Response", "1", "Assigned", 4, 0),
        ("INC Medium - Resolution", "1", "Resolved", 0, 1),
        ("INC Low - First Response", "0", "Assigned", 8, 0),
        ("INC Low - Resolution", "0", "Resolved", 0, 3),
    ],
    "Service Request": [
        ("SR High - Fulfillment", "2", "Resolved", 0, 2),
        ("SR Medium - Fulfillment", "1", "Resolved", 0, 5),
        ("SR Low - Fulfillment", "0", "Resolved", 0, 10),
    ],
    "Access Request": [
        ("ACC High - Provisioning", "2", "Access Granted", 4, 0),
        ("ACC Medium - Provisioning", "1", "Access Granted", 0, 1),
        ("ACC Low - Provisioning", "0", "Access Granted", 0, 3),
    ],
    "Asset Request": [
        ("AST High - Delivery", "2", "Ready for Delivery", 0, 3),
        ("AST Medium - Delivery", "1", "Ready for Delivery", 0, 5),
        ("AST Low - Delivery", "0", "Ready for Delivery", 0, 10),
    ],
    "General Inquiry": [
        ("INQ - First Response", "0", "Assigned", 4, 0),
        ("INQ - Answer Provided", "0", "Answered", 0, 2),
    ],
    "Onboarding Request": [
        ("ONB - Ready Before Start Date", "0", "Ready for Day 1", 0, 3),
    ],
    "Offboarding Request": [
        ("OFF - Complete by Last Day", "0", "Audit Complete", 0, 1),
    ],
    "Maintenance Request": [
        ("MNT - Within Scheduled Window", "0", "Verification", 0, 1),
    ],
    "Change Management": [
        ("CHG - CAB Review", "0", "Approved - Scheduled", 0, 5),
    ],
    "Problem Management": [
        ("PRB - Investigation Start", "0", "Under Investigation", 0, 2),
        ("PRB - Workaround/Resolution", "0", "Workaround Available", 0, 14),
    ],
}

sla_count = 0
for team_name, slas in SLAS.items():
    tid = team_ids.get(team_name)
    if not tid:
        continue
    print(f"\n  [{team_name}]")
    for sla_name, priority, target_stage, hours, days in slas:
        sid = stage_ids.get((team_name, target_stage))
        if not sid:
            print(f"    ✗ Stage '{target_stage}' not found")
            continue
        rec = env['helpdesk.sla'].search([('name', '=', sla_name), ('team_id', '=', tid)], limit=1)
        if not rec:
            env['helpdesk.sla'].create({
                'name': sla_name,
                'team_id': tid,
                'priority': priority,
                'stage_id': sid,
                'time': hours,
                'time_days': days,
            })
        sla_count += 1
        t = f"{hours}h" if hours else f"{days}d"
        print(f"    ✓ {sla_name} → {target_stage} ({t})")

print(f"\n  → {sla_count} SLA policies imported")
env.cr.commit()

# ============================================================
# ROUTES (AUTOMATED ACTIONS)
# ============================================================
print("\n" + "="*60)
print("  IMPORTING ROUTES (AUTOMATED ACTIONS)")
print("="*60)

model_rec = env['ir.model'].search([('model', '=', 'helpdesk.ticket')], limit=1)
model_id = model_rec.id

write_date_field = env['ir.model.fields'].search([
    ('model', '=', 'helpdesk.ticket'),
    ('name', '=', 'write_date')
], limit=1)
write_date_id = write_date_field.id

def get_stage(team, name):
    return stage_ids.get((team, name), False)

def create_route(name, team_name, trigger, code, from_stage=None, to_stage=None, target_stage=None, close_stage=None, days=None):
    """Create a single automation route."""
    tid = team_ids[team_name]

    existing = env['base.automation'].search([('name', '=', name)], limit=1)
    if existing:
        print(f"    ○ {name} (exists)")
        return

    vals = {
        'name': name,
        'model_id': model_id,
        'state': 'code',
        'active': True,
        'code': code.strip(),
    }

    if trigger == 'on_create':
        vals['trigger'] = 'on_create'
        vals['filter_domain'] = "[('team_id', '=', %d)]" % tid

    elif trigger == 'on_write':
        fs = get_stage(team_name, from_stage)
        ts = get_stage(team_name, to_stage)
        if not fs or not ts:
            print(f"    ✗ {name} - stage not found (from={from_stage}, to={to_stage})")
            return
        vals['trigger'] = 'on_write'
        vals['filter_domain'] = "[('team_id', '=', %d), ('stage_id', '=', %d)]" % (tid, ts)
        vals['filter_pre_domain'] = "[('stage_id', '=', %d)]" % fs

    elif trigger == 'on_time':
        ts = get_stage(team_name, target_stage)
        cs = get_stage(team_name, close_stage)
        if not ts or not cs:
            print(f"    ✗ {name} - stage not found")
            return
        vals['trigger'] = 'on_time'
        vals['trg_date_id'] = write_date_id
        vals['trg_date_range'] = days
        vals['trg_date_range_type'] = 'day'
        vals['filter_domain'] = "[('team_id', '=', %d), ('stage_id', '=', %d)]" % (tid, ts)
        vals['code'] = code.strip().replace('{CLOSE_STAGE_ID}', str(cs))

    try:
        env['base.automation'].create(vals)
        if trigger == 'on_write':
            print(f"    ✓ {name}  ({from_stage} → {to_stage})")
        elif trigger == 'on_time':
            print(f"    ✓ {name}  (After {days}d)")
        else:
            print(f"    ✓ {name}  (On Create)")
    except Exception as e:
        print(f"    ✗ {name} - ERROR: {e}")


# ---- INCIDENT MANAGEMENT ----
tn = "Incident Management"
print(f"\n  [{tn}]")

create_route("INC: Auto-Acknowledge", tn, "on_create", """
if record.partner_id and record.partner_id.email:
    record.message_post(body='Your incident has been received and logged. A technician will be assigned shortly.', message_type='notification', partner_ids=[record.partner_id.id])
record.message_post(body='Incident received and triaged automatically.')
""")

create_route("INC: Notify on Assignment", tn, "on_write", """
if record.user_id:
    record.message_post(body='Ticket assigned to %s.' % record.user_id.name, partner_ids=[record.user_id.partner_id.id])
""", from_stage="New", to_stage="Assigned")

create_route("INC: Start Work", tn, "on_write", """
record.message_post(body='Work started on this incident.')
if record.partner_id:
    record.message_post(body='A technician is now working on your issue.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Assigned", to_stage="In Progress")

create_route("INC: Pause SLA on Pending", tn, "on_write", """
record.message_post(body='Ticket on hold - awaiting information from requester. SLA timer paused.')
if record.partner_id:
    record.message_post(body='We need additional information to proceed. Please reply with the requested details.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="In Progress", to_stage="Pending")

create_route("INC: Manual Escalation", tn, "on_write", """
record.message_post(body='Ticket escalated to L2 Support.')
if record.partner_id:
    record.message_post(body='Your ticket has been escalated to our senior support team.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="In Progress", to_stage="Escalated")

create_route("INC: Resolve from In Progress", tn, "on_write", """
record.message_post(body='Incident resolved. Awaiting user confirmation.')
if record.partner_id:
    record.message_post(body='Your incident has been resolved. Please confirm. If no response in 5 days, this ticket will auto-close.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="In Progress", to_stage="Resolved")

create_route("INC: Resolve from Escalated", tn, "on_write", """
record.message_post(body='Escalated incident resolved. Awaiting confirmation.')
if record.partner_id:
    record.message_post(body='Your escalated incident has been resolved. Please confirm.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Escalated", to_stage="Resolved")

create_route("INC: Manual Close", tn, "on_write", """
record.message_post(body='Incident closed.')
if record.partner_id:
    record.message_post(body='Your incident has been closed. Thank you for contacting IT Support.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Resolved", to_stage="Closed")

create_route("INC: Auto-Close After 5 Days", tn, "on_time", """
closed_stage = env['helpdesk.stage'].browse({CLOSE_STAGE_ID})
for ticket in records:
    ticket.write({'stage_id': closed_stage.id})
    ticket.message_post(body='Incident auto-closed after 5 days with no response.')
""", target_stage="Resolved", close_stage="Closed", days=5)

create_route("INC: Reopen Ticket", tn, "on_write", """
record.message_post(body='Incident reopened.')
if record.user_id:
    record.message_post(body='This ticket has been reopened.', partner_ids=[record.user_id.partner_id.id])
""", from_stage="Closed", to_stage="In Progress")

env.cr.commit()

# ---- SERVICE REQUEST ----
tn = "Service Request"
print(f"\n  [{tn}]")

create_route("SR: Auto-Acknowledge", tn, "on_create", """
record.message_post(body='Service request received. Your request is being processed.')
""")

create_route("SR: Send for Approval", tn, "on_write", """
record.message_post(body='Request sent for approval.')
""", from_stage="New", to_stage="Pending Approval")

create_route("SR: Approved", tn, "on_write", """
record.message_post(body='Request approved. Fulfillment started.')
if record.partner_id:
    record.message_post(body='Your service request has been approved.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Pending Approval", to_stage="Assigned")

create_route("SR: Rejected", tn, "on_write", """
record.message_post(body='Request rejected.')
if record.partner_id:
    record.message_post(body='Your service request could not be approved. Please contact your manager.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Pending Approval", to_stage="Rejected")

create_route("SR: Resolved", tn, "on_write", """
record.message_post(body='Service request fulfilled.')
if record.partner_id:
    record.message_post(body='Your service request has been completed. Please confirm.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="In Progress", to_stage="Resolved")

create_route("SR: Auto-Close After 3 Days", tn, "on_time", """
closed_stage = env['helpdesk.stage'].browse({CLOSE_STAGE_ID})
for ticket in records:
    ticket.write({'stage_id': closed_stage.id})
    ticket.message_post(body='Request auto-closed after 3 days with no response.')
""", target_stage="Resolved", close_stage="Closed", days=3)

env.cr.commit()

# ---- CHANGE MANAGEMENT ----
tn = "Change Management"
print(f"\n  [{tn}]")

create_route("CHG: Submit for Review", tn, "on_write", """
record.message_post(body='Change request submitted for CAB review.')
""", from_stage="Draft", to_stage="Submitted for Review")

create_route("CHG: CAB Approved", tn, "on_write", """
record.message_post(body='Change approved by CAB. Schedule implementation window.')
if record.partner_id:
    record.message_post(body='Your change request has been approved.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Submitted for Review", to_stage="Approved - Scheduled")

create_route("CHG: CAB Rejected", tn, "on_write", """
record.message_post(body='Change rejected by CAB.')
if record.partner_id:
    record.message_post(body='Your change request was not approved.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Submitted for Review", to_stage="Rejected by CAB")

create_route("CHG: Start Implementation", tn, "on_write", """
record.message_post(body='Implementation started.')
""", from_stage="Approved - Scheduled", to_stage="Implementation")

create_route("CHG: Emergency Stop", tn, "on_write", """
record.message_post(body='EMERGENCY STOP triggered! Immediate attention required. Rollback may be necessary.')
""", from_stage="Implementation", to_stage="Emergency Stop")

create_route("CHG: Verification", tn, "on_write", """
record.message_post(body='Implementation complete. Running verification checks.')
""", from_stage="Implementation", to_stage="Verification")

create_route("CHG: Closed Successful", tn, "on_write", """
record.message_post(body='Change completed successfully.')
""", from_stage="Verification", to_stage="Closed - Successful")

create_route("CHG: Closed Failed", tn, "on_write", """
record.message_post(body='Change failed. Rollback completed.')
""", from_stage="Emergency Stop", to_stage="Closed - Failed")

env.cr.commit()

# ---- PROBLEM MANAGEMENT ----
tn = "Problem Management"
print(f"\n  [{tn}]")

create_route("PRB: Assign Investigation", tn, "on_write", """
record.message_post(body='Problem assigned for investigation.')
""", from_stage="Identified", to_stage="Under Investigation")

create_route("PRB: Start RCA", tn, "on_write", """
record.message_post(body='Root cause analysis started.')
""", from_stage="Under Investigation", to_stage="Root Cause Analysis")

create_route("PRB: Workaround Found", tn, "on_write", """
record.message_post(body='Workaround documented. Consider publishing to Knowledge Base.')
""", from_stage="Root Cause Analysis", to_stage="Workaround Available")

create_route("PRB: Escalate to Vendor", tn, "on_write", """
record.message_post(body='Problem escalated to vendor for resolution.')
""", from_stage="Root Cause Analysis", to_stage="Escalated to Vendor")

create_route("PRB: Root Cause Fixed", tn, "on_write", """
record.message_post(body='Root cause fixed. Permanent solution deployed.')
""", from_stage="Root Cause Analysis", to_stage="Root Cause Fixed")

create_route("PRB: Close", tn, "on_write", """
record.message_post(body='Problem closed. Fix verified in production.')
""", from_stage="Root Cause Fixed", to_stage="Closed")

env.cr.commit()

# ---- ASSET REQUEST ----
tn = "Asset Request"
print(f"\n  [{tn}]")

create_route("AST: Auto-Acknowledge", tn, "on_create", """
record.message_post(body='Asset request received. Checking entitlement and availability.')
""")

create_route("AST: Manager Approved", tn, "on_write", """
record.message_post(body='Manager approved. IT reviewing availability.')
""", from_stage="Manager Approval", to_stage="IT Approved")

create_route("AST: Pending Stock", tn, "on_write", """
record.message_post(body='Asset out of stock. Procurement request created.')
if record.partner_id:
    record.message_post(body='Your requested asset is currently out of stock. You will be notified when available.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Provisioning", to_stage="Pending Stock")

create_route("AST: Ready for Delivery", tn, "on_write", """
record.message_post(body='Asset ready for delivery.')
if record.partner_id:
    record.message_post(body='Your asset is ready for pickup/delivery.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Provisioning", to_stage="Ready for Delivery")

create_route("AST: Delivered", tn, "on_write", """
record.message_post(body='Asset delivered and signed off.')
""", from_stage="Ready for Delivery", to_stage="Delivered")

env.cr.commit()

# ---- ACCESS REQUEST ----
tn = "Access Request"
print(f"\n  [{tn}]")

create_route("ACC: Data Owner Approval", tn, "on_write", """
record.message_post(body='Access request sent to data owner for approval.')
""", from_stage="New", to_stage="Data Owner Approval")

create_route("ACC: Security Review", tn, "on_write", """
record.message_post(body='Security review in progress.')
""", from_stage="Data Owner Approval", to_stage="Security Review")

create_route("ACC: Provisioning", tn, "on_write", """
record.message_post(body='All approvals obtained. Provisioning access.')
""", from_stage="Security Review", to_stage="Provisioning Access")

create_route("ACC: Access Granted", tn, "on_write", """
record.message_post(body='Access granted.')
if record.partner_id:
    record.message_post(body='Your access has been provisioned. Please verify it is working.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Provisioning Access", to_stage="Access Granted")

create_route("ACC: Rejected", tn, "on_write", """
record.message_post(body='Access request rejected.')
if record.partner_id:
    record.message_post(body='Your access request could not be approved.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="Security Review", to_stage="Rejected")

create_route("ACC: Auto-Confirm After 3 Days", tn, "on_time", """
closed_stage = env['helpdesk.stage'].browse({CLOSE_STAGE_ID})
for ticket in records:
    ticket.write({'stage_id': closed_stage.id})
    ticket.message_post(body='Access auto-confirmed after 3 days.')
""", target_stage="Access Granted", close_stage="Confirmed", days=3)

env.cr.commit()

# ---- GENERAL INQUIRY ----
tn = "General Inquiry"
print(f"\n  [{tn}]")

create_route("INQ: Auto-Acknowledge", tn, "on_create", """
record.message_post(body='Thank you for your inquiry. A team member will respond shortly.')
""")

create_route("INQ: Escalate to Expert", tn, "on_write", """
record.message_post(body='Inquiry escalated to subject matter expert.')
""", from_stage="In Progress", to_stage="Escalated to Expert")

create_route("INQ: Answered", tn, "on_write", """
record.message_post(body='Inquiry answered.')
if record.partner_id:
    record.message_post(body='Your inquiry has been answered. Please let us know if you need anything else.', message_type='notification', partner_ids=[record.partner_id.id])
""", from_stage="In Progress", to_stage="Answered")

create_route("INQ: Auto-Close After 5 Days", tn, "on_time", """
closed_stage = env['helpdesk.stage'].browse({CLOSE_STAGE_ID})
for ticket in records:
    ticket.write({'stage_id': closed_stage.id})
    ticket.message_post(body='Inquiry auto-closed after 5 days.')
""", target_stage="Answered", close_stage="Closed", days=5)

env.cr.commit()

# ---- ONBOARDING ----
tn = "Onboarding Request"
print(f"\n  [{tn}]")

create_route("ONB: Generate Checklist", tn, "on_create", """
checklist = 'Onboarding Checklist:\\n- Create AD/Email account\\n- Provision laptop/workstation\\n- Configure required software\\n- Set up phone/extension\\n- Create badge/access card\\n- Assign to security groups\\n- Schedule Day 1 orientation\\n- Prepare welcome documentation'
record.message_post(body=checklist)
""")

create_route("ONB: Ready for Day 1", tn, "on_write", """
record.message_post(body='All onboarding tasks complete. Ready for new hire Day 1 handover.')
""", from_stage="Preparing", to_stage="Ready for Day 1")

env.cr.commit()

# ---- OFFBOARDING ----
tn = "Offboarding Request"
print(f"\n  [{tn}]")

create_route("OFF: Generate Revocation Checklist", tn, "on_create", """
checklist = 'Offboarding Security Checklist:\\n- Backup mailbox and files\\n- Disable AD account\\n- Revoke VPN access\\n- Disable badge/physical access\\n- Remove from security groups\\n- Collect laptop/equipment\\n- Collect mobile devices\\n- Transfer shared resources\\n- Archive account\\n- Final security audit'
record.message_post(body=checklist)
""")

create_route("OFF: Audit Complete", tn, "on_write", """
record.message_post(body='Offboarding complete. Final security audit required before archiving.')
""", from_stage="Asset Collection", to_stage="Audit Complete")

env.cr.commit()

# ---- MAINTENANCE ----
tn = "Maintenance Request"
print(f"\n  [{tn}]")

create_route("MNT: Approved", tn, "on_write", """
record.message_post(body='Maintenance window approved. User notifications should be sent.')
""", from_stage="Scheduled", to_stage="Approved")

create_route("MNT: Issue Alert", tn, "on_write", """
record.message_post(body='Issue encountered during maintenance! Assess impact and consider extending window or aborting.')
""", from_stage="In Progress", to_stage="Issue Encountered")

create_route("MNT: All-Clear", tn, "on_write", """
record.message_post(body='Maintenance completed successfully. All systems operational.')
""", from_stage="Verification", to_stage="Completed")

env.cr.commit()

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("  IMPORT COMPLETE")
print("="*60)
print(f"  Security Groups:  {len(group_ids)}")
print(f"  Teams:            {len(team_ids)}")
print(f"  Stages:           {total_stages}")
print(f"  Ticket Types:     {tt_count}")
print(f"  SLA Policies:     {sla_count}")
print(f"  Routes:           Check Settings → Technical → Automations")
print("="*60)
print("\n  NEXT STEPS:")
print("  1. Helpdesk → Configuration → Teams → Assign members")
print("  2. Settings → Users → Groups → Assign ITSM roles")
print("  3. Helpdesk → Configuration → SLA → Adjust times")
print("  4. Settings → Technical → Automations → Verify routes")
print()
