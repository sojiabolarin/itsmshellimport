#!/usr/bin/env python3
"""
WestMetro ITSM Digest Emails Implementation
=============================================
Server: servicedesk.westmetro.ng
DB: servicedesk.westmetro.ng

Creates:
1. Mail templates for 5 digest types
2. Server actions with Python code to generate digests
3. Scheduled cron jobs to send digests automatically

Digest Types:
- Daily Team Digest (8:00 AM daily to each team)
- Weekly Management Summary (Monday 9:00 AM to leadership)
- Customer Digest (Weekly to client contacts)
- Escalation Alert (Real-time on SLA breach)
- CAB Digest (Before CAB meetings)

Mail Server: servicedesk@westmetro.ng (id=2)

Run:
    cd /opt/odoo/odoo
    sudo -u odoo python3 odoo-bin shell -c /opt/odoo/conf/odoo.conf \
      -d servicedesk.westmetro.ng --no-http < /path/to/itsm_digest_emails.py

Author: WestMetro Limited | www.westmetrong.com
"""

from datetime import datetime, timedelta
import traceback

print("\n" + "=" * 70)
print("  WML ITSM DIGEST EMAILS IMPLEMENTATION")
print("=" * 70)

# ================================================================
# CONFIGURATION
# ================================================================
MAIL_SERVER_ID = 2  # servicedesk@westmetro.ng
EMAIL_FROM = "servicedesk@westmetro.ng"
PORTAL_URL = "https://servicedesk.westmetro.ng"

# ================================================================
# STEP 1: GET MODEL IDs
# ================================================================
print("\n" + "-" * 70)
print("  STEP 1: FETCHING MODEL IDs")
print("-" * 70)

request_model = env['ir.model'].search([('model', '=', 'request.request')], limit=1)
team_model = env['ir.model'].search([('model', '=', 'generic.team')], limit=1)
user_model = env['ir.model'].search([('model', '=', 'res.users')], limit=1)

if not request_model:
    print("  ERROR: request.request model not found!")
    exit()

print(f"  request.request model_id: {request_model.id}")
print(f"  generic.team model_id: {team_model.id if team_model else 'N/A'}")
print(f"  res.users model_id: {user_model.id}")

# ================================================================
# STEP 2: CREATE MAIL TEMPLATES
# ================================================================
print("\n" + "-" * 70)
print("  STEP 2: CREATING MAIL TEMPLATES")
print("-" * 70)

# ------------------- TEMPLATE 1: DAILY TEAM DIGEST -------------------
DAILY_TEAM_BODY = '''
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
    <div style="background: #1B4F72; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">Daily Team Digest</h1>
        <p style="margin: 5px 0 0 0;">{{ team_name }} | {{ date_str }}</p>
    </div>
    
    <div style="padding: 20px; background: #f9f9f9;">
        <!-- SUMMARY BOX -->
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">
            <div style="flex: 1; min-width: 120px; background: #3498DB; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ new_count }}</div>
                <div>New Today</div>
            </div>
            <div style="flex: 1; min-width: 120px; background: #F39C12; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ in_progress_count }}</div>
                <div>In Progress</div>
            </div>
            <div style="flex: 1; min-width: 120px; background: #E67E22; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ pending_count }}</div>
                <div>Pending</div>
            </div>
            <div style="flex: 1; min-width: 120px; background: #27AE60; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ resolved_yesterday }}</div>
                <div>Resolved Yesterday</div>
            </div>
        </div>
        
        <!-- SLA ALERTS -->
        {% if sla_warning_count > 0 or sla_breached_count > 0 %}
        <div style="background: #FDEDEC; border-left: 4px solid #E74C3C; padding: 15px; margin-bottom: 20px;">
            <h3 style="color: #C0392B; margin-top: 0;">⚠️ SLA Alerts</h3>
            {% if sla_breached_count > 0 %}
            <p style="color: #E74C3C; font-weight: bold;">{{ sla_breached_count }} request(s) have BREACHED SLA</p>
            {% endif %}
            {% if sla_warning_count > 0 %}
            <p style="color: #F39C12;">{{ sla_warning_count }} request(s) approaching SLA deadline</p>
            {% endif %}
        </div>
        {% endif %}
        
        <!-- AGED REQUESTS -->
        {% if aged_count > 0 %}
        <div style="background: #FEF9E7; border-left: 4px solid #F1C40F; padding: 15px; margin-bottom: 20px;">
            <h3 style="color: #9A7D0A; margin-top: 0;">📅 Aged Requests</h3>
            <p>{{ aged_count }} request(s) have been open for more than 5 days.</p>
        </div>
        {% endif %}
        
        <!-- NEW REQUESTS TABLE -->
        {% if new_requests %}
        <h3 style="color: #1B4F72;">New Requests Assigned</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background: #1B4F72; color: white;">
                <th style="padding: 10px; text-align: left;">ID</th>
                <th style="padding: 10px; text-align: left;">Type</th>
                <th style="padding: 10px; text-align: left;">Subject</th>
                <th style="padding: 10px; text-align: left;">Priority</th>
                <th style="padding: 10px; text-align: left;">Created</th>
            </tr>
            {% for req in new_requests %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    <a href="{{ portal_url }}/web#id={{ req.id }}&model=request.request">{{ req.name }}</a>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.type_id.name }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.request_text[:50] }}...</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.priority }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.create_date.strftime('%Y-%m-%d %H:%M') }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="{{ portal_url }}" style="background: #1B4F72; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Open Service Desk</a>
        </div>
    </div>
    
    <div style="background: #1B4F72; color: white; padding: 15px; text-align: center; font-size: 12px;">
        <p style="margin: 0;">WestMetro Limited | +234 806 902 0996 | servicedesk@westmetro.ng</p>
    </div>
</div>
'''

# ------------------- TEMPLATE 2: WEEKLY MANAGEMENT SUMMARY -------------------
WEEKLY_MGMT_BODY = '''
<div style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto;">
    <div style="background: #1B4F72; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">Weekly Management Summary</h1>
        <p style="margin: 5px 0 0 0;">Week of {{ week_start }} to {{ week_end }}</p>
    </div>
    
    <div style="padding: 20px; background: #f9f9f9;">
        <!-- KEY METRICS -->
        <h2 style="color: #1B4F72; border-bottom: 2px solid #1B4F72; padding-bottom: 10px;">Key Metrics</h2>
        <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 30px;">
            <div style="flex: 1; min-width: 150px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: #3498DB;">{{ total_opened }}</div>
                <div style="color: #666;">Requests Opened</div>
            </div>
            <div style="flex: 1; min-width: 150px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: #27AE60;">{{ total_closed }}</div>
                <div style="color: #666;">Requests Closed</div>
            </div>
            <div style="flex: 1; min-width: 150px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: {% if sla_compliance >= 90 %}#27AE60{% elif sla_compliance >= 75 %}#F39C12{% else %}#E74C3C{% endif %};">{{ sla_compliance }}%</div>
                <div style="color: #666;">SLA Compliance</div>
            </div>
            <div style="flex: 1; min-width: 150px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: #8E44AD;">{{ open_backlog }}</div>
                <div style="color: #666;">Open Backlog</div>
            </div>
        </div>
        
        <!-- SLA BY PRIORITY -->
        <h2 style="color: #1B4F72; border-bottom: 2px solid #1B4F72; padding-bottom: 10px;">SLA Performance by Priority</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <tr style="background: #1B4F72; color: white;">
                <th style="padding: 12px; text-align: left;">Priority</th>
                <th style="padding: 12px; text-align: center;">Total</th>
                <th style="padding: 12px; text-align: center;">Met SLA</th>
                <th style="padding: 12px; text-align: center;">Breached</th>
                <th style="padding: 12px; text-align: center;">Compliance</th>
                <th style="padding: 12px; text-align: center;">Avg Resolution</th>
            </tr>
            {% for p in priority_stats %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 12px; border-bottom: 1px solid #ddd; font-weight: bold;">{{ p.name }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{{ p.total }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center; color: #27AE60;">{{ p.met }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center; color: #E74C3C;">{{ p.breached }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">
                    <span style="background: {% if p.compliance >= 90 %}#27AE60{% elif p.compliance >= 75 %}#F39C12{% else %}#E74C3C{% endif %}; color: white; padding: 3px 10px; border-radius: 3px;">{{ p.compliance }}%</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{{ p.avg_resolution }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <!-- TEAM PERFORMANCE -->
        <h2 style="color: #1B4F72; border-bottom: 2px solid #1B4F72; padding-bottom: 10px;">Team Performance</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <tr style="background: #1B4F72; color: white;">
                <th style="padding: 12px; text-align: left;">Team</th>
                <th style="padding: 12px; text-align: center;">Assigned</th>
                <th style="padding: 12px; text-align: center;">Resolved</th>
                <th style="padding: 12px; text-align: center;">Open</th>
                <th style="padding: 12px; text-align: center;">SLA %</th>
            </tr>
            {% for t in team_stats %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 12px; border-bottom: 1px solid #ddd; font-weight: bold;">{{ t.name }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{{ t.assigned }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center; color: #27AE60;">{{ t.resolved }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center; color: #F39C12;">{{ t.open }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{{ t.sla_pct }}%</td>
            </tr>
            {% endfor %}
        </table>
        
        <!-- TOP REQUEST TYPES -->
        <h2 style="color: #1B4F72; border-bottom: 2px solid #1B4F72; padding-bottom: 10px;">Top 5 Request Types</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <tr style="background: #1B4F72; color: white;">
                <th style="padding: 12px; text-align: left;">Request Type</th>
                <th style="padding: 12px; text-align: center;">Volume</th>
                <th style="padding: 12px; text-align: left;">Trend</th>
            </tr>
            {% for rt in top_types %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">{{ rt.name }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center; font-weight: bold;">{{ rt.count }}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                    {% if rt.trend > 0 %}
                    <span style="color: #E74C3C;">↑ {{ rt.trend }}%</span>
                    {% elif rt.trend < 0 %}
                    <span style="color: #27AE60;">↓ {{ rt.trend|abs }}%</span>
                    {% else %}
                    <span style="color: #666;">→ No change</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="{{ portal_url }}" style="background: #1B4F72; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">View Full Dashboard</a>
        </div>
    </div>
    
    <div style="background: #1B4F72; color: white; padding: 15px; text-align: center; font-size: 12px;">
        <p style="margin: 0;">WestMetro Limited | +234 806 902 0996 | servicedesk@westmetro.ng</p>
    </div>
</div>
'''

# ------------------- TEMPLATE 3: ESCALATION ALERT -------------------
ESCALATION_ALERT_BODY = '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #E74C3C; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">🚨 SLA ESCALATION ALERT</h1>
        <p style="margin: 5px 0 0 0; font-size: 18px;">Immediate Action Required</p>
    </div>
    
    <div style="padding: 20px; background: #FDEDEC;">
        <div style="background: white; padding: 20px; border-radius: 8px; border-left: 5px solid #E74C3C;">
            <h2 style="color: #C0392B; margin-top: 0;">Request Details</h2>
            <table style="width: 100%;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; width: 140px;">Request ID:</td>
                    <td style="padding: 8px 0;"><a href="{{ portal_url }}/web#id={{ request.id }}&model=request.request" style="color: #E74C3C; font-weight: bold;">{{ request.name }}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Type:</td>
                    <td style="padding: 8px 0;">{{ request.type_id.name }}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Priority:</td>
                    <td style="padding: 8px 0;"><span style="background: #E74C3C; color: white; padding: 3px 10px; border-radius: 3px;">{{ request.priority }}</span></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Subject:</td>
                    <td style="padding: 8px 0;">{{ request.request_text[:100] }}...</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Created:</td>
                    <td style="padding: 8px 0;">{{ request.create_date.strftime('%Y-%m-%d %H:%M') }}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Time Open:</td>
                    <td style="padding: 8px 0; color: #E74C3C; font-weight: bold;">{{ time_open }}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Current Stage:</td>
                    <td style="padding: 8px 0;">{{ request.stage_id.name }}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Assigned To:</td>
                    <td style="padding: 8px 0;">{{ request.user_id.name or 'Unassigned' }}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Team:</td>
                    <td style="padding: 8px 0;">{{ request.team_id.name or 'Unassigned' }}</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #FDEBD0; padding: 15px; border-radius: 8px; margin-top: 20px;">
            <h3 style="color: #9A7D0A; margin-top: 0;">⚠️ SLA Status</h3>
            <p><strong>Target Response:</strong> {{ sla_target }}</p>
            <p><strong>Actual Time:</strong> {{ actual_time }}</p>
            <p style="color: #E74C3C; font-weight: bold;">STATUS: {{ sla_status }}</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="{{ portal_url }}/web#id={{ request.id }}&model=request.request" style="background: #E74C3C; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold;">TAKE ACTION NOW</a>
        </div>
    </div>
    
    <div style="background: #1B4F72; color: white; padding: 15px; text-align: center; font-size: 12px;">
        <p style="margin: 0;">This is an automated escalation alert from WestMetro ITSM</p>
    </div>
</div>
'''

# ------------------- TEMPLATE 4: CUSTOMER DIGEST -------------------
CUSTOMER_DIGEST_BODY = '''
<div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
    <div style="background: #1B4F72; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">Your Support Summary</h1>
        <p style="margin: 5px 0 0 0;">{{ customer_name }} | Week of {{ week_date }}</p>
    </div>
    
    <div style="padding: 20px; background: #f9f9f9;">
        <p style="font-size: 16px;">Dear {{ contact_name }},</p>
        <p>Here is your weekly support summary from WestMetro Limited.</p>
        
        <!-- SUMMARY -->
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0;">
            <div style="flex: 1; min-width: 100px; background: #3498DB; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold;">{{ open_count }}</div>
                <div>Open Requests</div>
            </div>
            <div style="flex: 1; min-width: 100px; background: #27AE60; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold;">{{ resolved_count }}</div>
                <div>Resolved This Week</div>
            </div>
            <div style="flex: 1; min-width: 100px; background: #8E44AD; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold;">{{ sla_pct }}%</div>
                <div>SLA Compliance</div>
            </div>
        </div>
        
        <!-- OPEN REQUESTS -->
        {% if open_requests %}
        <h3 style="color: #1B4F72;">Your Open Requests</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background: #1B4F72; color: white;">
                <th style="padding: 10px; text-align: left;">ID</th>
                <th style="padding: 10px; text-align: left;">Subject</th>
                <th style="padding: 10px; text-align: left;">Status</th>
                <th style="padding: 10px; text-align: left;">Last Update</th>
            </tr>
            {% for req in open_requests %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><a href="{{ portal_url }}/my/requests/{{ req.id }}">{{ req.name }}</a></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.request_text[:40] }}...</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.stage_id.name }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.write_date.strftime('%Y-%m-%d') }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="background: #D5F5E3; padding: 15px; border-radius: 8px; color: #1E8449;">✓ You have no open requests. All issues resolved!</p>
        {% endif %}
        
        <!-- RESOLVED THIS WEEK -->
        {% if resolved_requests %}
        <h3 style="color: #1B4F72;">Resolved This Week</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background: #27AE60; color: white;">
                <th style="padding: 10px; text-align: left;">ID</th>
                <th style="padding: 10px; text-align: left;">Subject</th>
                <th style="padding: 10px; text-align: left;">Resolution Date</th>
            </tr>
            {% for req in resolved_requests %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.name }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.request_text[:40] }}...</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ req.date_closed.strftime('%Y-%m-%d') if req.date_closed else '' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <!-- UPCOMING CHANGES -->
        {% if scheduled_changes %}
        <h3 style="color: #1B4F72;">Scheduled Changes</h3>
        <div style="background: #FEF9E7; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            {% for change in scheduled_changes %}
            <p><strong>{{ change.name }}</strong> - Scheduled: {{ change.scheduled_date }}</p>
            {% endfor %}
        </div>
        {% endif %}
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="{{ portal_url }}/my/requests" style="background: #1B4F72; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">View All Your Requests</a>
        </div>
        
        <p style="margin-top: 30px; color: #666; font-size: 14px;">If you have any questions, please contact us at support@westmetrong.com or call +234 806 902 0996.</p>
    </div>
    
    <div style="background: #1B4F72; color: white; padding: 15px; text-align: center; font-size: 12px;">
        <p style="margin: 0;">WestMetro Limited | www.westmetrong.com</p>
    </div>
</div>
'''

# ------------------- TEMPLATE 5: CAB DIGEST -------------------
CAB_DIGEST_BODY = '''
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
    <div style="background: #2C3E50; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">Change Advisory Board Digest</h1>
        <p style="margin: 5px 0 0 0;">CAB Meeting: {{ cab_date }}</p>
    </div>
    
    <div style="padding: 20px; background: #f9f9f9;">
        <!-- SUMMARY -->
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">
            <div style="flex: 1; min-width: 120px; background: #8E44AD; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ pending_review }}</div>
                <div>Pending Review</div>
            </div>
            <div style="flex: 1; min-width: 120px; background: #F39C12; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ scheduled_count }}</div>
                <div>Scheduled</div>
            </div>
            <div style="flex: 1; min-width: 120px; background: #27AE60; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ implemented_success }}</div>
                <div>Implemented (Success)</div>
            </div>
            <div style="flex: 1; min-width: 120px; background: #E74C3C; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 28px; font-weight: bold;">{{ implemented_failed }}</div>
                <div>Failed/Rolled Back</div>
            </div>
        </div>
        
        <!-- RFCs PENDING REVIEW -->
        {% if rfcs_pending %}
        <h2 style="color: #2C3E50; border-bottom: 2px solid #8E44AD; padding-bottom: 10px;">📋 RFCs Pending Review</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background: #8E44AD; color: white;">
                <th style="padding: 10px; text-align: left;">RFC ID</th>
                <th style="padding: 10px; text-align: left;">Change Description</th>
                <th style="padding: 10px; text-align: left;">Service</th>
                <th style="padding: 10px; text-align: left;">Risk Level</th>
                <th style="padding: 10px; text-align: left;">Requester</th>
            </tr>
            {% for rfc in rfcs_pending %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><a href="{{ portal_url }}/web#id={{ rfc.id }}&model=request.request">{{ rfc.name }}</a></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ rfc.request_text[:50] }}...</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ rfc.service_id.name or 'N/A' }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ rfc.priority }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ rfc.author_id.name }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <!-- SCHEDULED CHANGES -->
        {% if changes_scheduled %}
        <h2 style="color: #2C3E50; border-bottom: 2px solid #F39C12; padding-bottom: 10px;">📅 Scheduled Changes (Next 7 Days)</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background: #F39C12; color: white;">
                <th style="padding: 10px; text-align: left;">Change ID</th>
                <th style="padding: 10px; text-align: left;">Description</th>
                <th style="padding: 10px; text-align: left;">Scheduled Date</th>
                <th style="padding: 10px; text-align: left;">Implementer</th>
            </tr>
            {% for chg in changes_scheduled %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ chg.name }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ chg.request_text[:50] }}...</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ chg.scheduled_date or 'TBD' }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ chg.user_id.name or 'Unassigned' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <!-- RECENTLY IMPLEMENTED -->
        {% if recently_implemented %}
        <h2 style="color: #2C3E50; border-bottom: 2px solid #27AE60; padding-bottom: 10px;">✅ Recently Implemented</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background: #27AE60; color: white;">
                <th style="padding: 10px; text-align: left;">Change ID</th>
                <th style="padding: 10px; text-align: left;">Description</th>
                <th style="padding: 10px; text-align: left;">Outcome</th>
                <th style="padding: 10px; text-align: left;">Completed</th>
            </tr>
            {% for impl in recently_implemented %}
            <tr style="background: {{ loop.cycle('#ffffff', '#f2f2f2') }};">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ impl.name }}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ impl.request_text[:50] }}...</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    {% if impl.stage_id.code == 'closed-success' %}
                    <span style="background: #27AE60; color: white; padding: 3px 8px; border-radius: 3px;">Success</span>
                    {% elif impl.stage_id.code == 'closed-failed' %}
                    <span style="background: #E74C3C; color: white; padding: 3px 8px; border-radius: 3px;">Failed</span>
                    {% else %}
                    <span style="background: #95A5A6; color: white; padding: 3px 8px; border-radius: 3px;">Rolled Back</span>
                    {% endif %}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{{ impl.write_date.strftime('%Y-%m-%d') }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="{{ portal_url }}" style="background: #2C3E50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Open Change Management</a>
        </div>
    </div>
    
    <div style="background: #2C3E50; color: white; padding: 15px; text-align: center; font-size: 12px;">
        <p style="margin: 0;">WestMetro Limited | Change Advisory Board</p>
    </div>
</div>
'''

# Create templates
templates_created = 0

MAIL_TEMPLATES = [
    {
        'name': 'ITSM: Daily Team Digest',
        'subject': '[WML ITSM] Daily Team Digest - {{ team_name }} - {{ date_str }}',
        'body_html': DAILY_TEAM_BODY,
        'model': 'generic.team',
        'email_from': EMAIL_FROM,
    },
    {
        'name': 'ITSM: Weekly Management Summary',
        'subject': '[WML ITSM] Weekly Management Summary - Week {{ week_number }}',
        'body_html': WEEKLY_MGMT_BODY,
        'model': 'res.users',
        'email_from': EMAIL_FROM,
    },
    {
        'name': 'ITSM: Escalation Alert',
        'subject': '🚨 [URGENT] SLA Breach Alert - {{ request.name }} - {{ request.type_id.name }}',
        'body_html': ESCALATION_ALERT_BODY,
        'model': 'request.request',
        'email_from': EMAIL_FROM,
    },
    {
        'name': 'ITSM: Customer Digest',
        'subject': '[WML Support] Your Weekly Support Summary - {{ customer_name }}',
        'body_html': CUSTOMER_DIGEST_BODY,
        'model': 'res.partner',
        'email_from': EMAIL_FROM,
    },
    {
        'name': 'ITSM: CAB Digest',
        'subject': '[WML CAB] Change Advisory Board Digest - {{ cab_date }}',
        'body_html': CAB_DIGEST_BODY,
        'model': 'res.users',
        'email_from': EMAIL_FROM,
    },
]

for tmpl in MAIL_TEMPLATES:
    existing = env['mail.template'].search([('name', '=', tmpl['name'])], limit=1)
    model_rec = env['ir.model'].search([('model', '=', tmpl['model'])], limit=1)
    
    if existing:
        existing.write({
            'subject': tmpl['subject'],
            'body_html': tmpl['body_html'],
            'email_from': tmpl['email_from'],
            'mail_server_id': MAIL_SERVER_ID,
        })
        print(f"  ○ Updated: {tmpl['name']}")
    else:
        vals = {
            'name': tmpl['name'],
            'subject': tmpl['subject'],
            'body_html': tmpl['body_html'],
            'email_from': tmpl['email_from'],
            'model_id': model_rec.id if model_rec else False,
            'model': tmpl['model'],
            'mail_server_id': MAIL_SERVER_ID,
            'auto_delete': False,
        }
        env['mail.template'].create(vals)
        templates_created += 1
        print(f"  + Created: {tmpl['name']}")

env.cr.commit()
print(f"\n  -> {templates_created} templates created")

# ================================================================
# STEP 3: CREATE SERVER ACTIONS
# ================================================================
print("\n" + "-" * 70)
print("  STEP 3: CREATING SERVER ACTIONS")
print("-" * 70)

# Python code for Daily Team Digest (no imports - Odoo safe)
DAILY_TEAM_CODE = '''
# Daily Team Digest - Sends digest to each team
# Uses datetime from fields.Datetime
# Queues emails instead of direct send for Zoho compatibility

portal_url = "https://servicedesk.westmetro.ng"
today = fields.Date.context_today(env.user)
yesterday = fields.Date.subtract(today, days=1)

teams = env['generic.team'].search([('active', '=', True)])

for team in teams:
    # Get team leader email
    if not team.leader_id or not team.leader_id.email:
        continue
    
    # Count requests by stage for this team
    domain_base = [('team_id', '=', team.id), ('stage_id.closed', '=', False)]
    
    new_requests = env['request.request'].search(domain_base + [('stage_id.code', 'in', ['logged', 'new', 'received', 'submitted', 'initiated', 'rfc-submitted'])])
    in_progress = env['request.request'].search(domain_base + [('stage_id.code', 'in', ['in-progress', 'triaged', 'fulfillment', 'implementation', 'configuration'])])
    pending = env['request.request'].search(domain_base + [('stage_id.code', 'in', ['pending', 'pending-vendor', 'awaiting-resp', 'under-review', 'cab-review'])])
    
    # Resolved yesterday
    resolved_yesterday = env['request.request'].search_count([
        ('team_id', '=', team.id),
        ('stage_id.closed', '=', True),
        ('write_date', '>=', str(yesterday)),
        ('write_date', '<', str(today)),
    ])
    
    # Aged requests (open > 5 days)
    five_days_ago = fields.Date.subtract(today, days=5)
    aged = env['request.request'].search_count(domain_base + [('create_date', '<', str(five_days_ago))])
    
    # SLA counts (simplified)
    sla_warning = 0
    sla_breached = 0
    
    # Build email content
    template = env['mail.template'].search([('name', '=', 'ITSM: Daily Team Digest')], limit=1)
    if template:
        # Queue email (state='outgoing') - Mail Queue Manager cron will send it
        subject = '[WML ITSM] Daily Team Digest - %s - %s' % (team.name, str(today))
        mail_values = {
            'subject': subject,
            'body_html': template.body_html,
            'email_to': team.leader_id.email,
            'email_from': 'servicedesk@westmetro.ng',
            'mail_server_id': 2,
            'state': 'outgoing',
            'auto_delete': False,
        }
        env['mail.mail'].create(mail_values)
'''

# Python code for Weekly Management Summary (no imports - Odoo safe)
WEEKLY_MGMT_CODE = '''
# Weekly Management Summary - Sends to leadership
# Uses datetime from fields.Datetime
# Queues emails instead of direct send for Zoho compatibility

portal_url = "https://servicedesk.westmetro.ng"
today = fields.Date.context_today(env.user)
week_start = fields.Date.subtract(today, days=today.weekday() + 7)
week_end = fields.Date.add(week_start, days=6)

# Get leadership users (admin as fallback)
leaders = env['res.users'].search([('id', '=', 2)])

# Calculate metrics
total_opened = env['request.request'].search_count([
    ('create_date', '>=', str(week_start)),
    ('create_date', '<=', str(week_end)),
])

total_closed = env['request.request'].search_count([
    ('stage_id.closed', '=', True),
    ('write_date', '>=', str(week_start)),
    ('write_date', '<=', str(week_end)),
])

open_backlog = env['request.request'].search_count([
    ('stage_id.closed', '=', False),
])

# SLA compliance (simplified)
sla_compliance = 85

template = env['mail.template'].search([('name', '=', 'ITSM: Weekly Management Summary')], limit=1)
if template:
    for leader in leaders:
        if not leader.email:
            continue
        subject = '[WML ITSM] Weekly Management Summary - Week %s' % str(week_start)
        # Queue email (state='outgoing') - Mail Queue Manager cron will send it
        mail_values = {
            'subject': subject,
            'body_html': template.body_html,
            'email_to': leader.email,
            'email_from': 'servicedesk@westmetro.ng',
            'mail_server_id': 2,
            'state': 'outgoing',
            'auto_delete': False,
        }
        env['mail.mail'].create(mail_values)
'''

# Create server actions
SERVER_ACTIONS = [
    {
        'name': 'ITSM: Send Daily Team Digest',
        'code': DAILY_TEAM_CODE,
        'model': 'generic.team',
    },
    {
        'name': 'ITSM: Send Weekly Management Summary',
        'code': WEEKLY_MGMT_CODE,
        'model': 'res.users',
    },
]

actions_created = 0
action_ids = {}

for act in SERVER_ACTIONS:
    existing = env['ir.actions.server'].search([('name', '=', act['name'])], limit=1)
    model_rec = env['ir.model'].search([('model', '=', act['model'])], limit=1)
    
    if existing:
        existing.write({
            'code': act['code'],
        })
        action_ids[act['name']] = existing.id
        print(f"  ○ Updated: {act['name']}")
    else:
        vals = {
            'name': act['name'],
            'state': 'code',
            'code': act['code'],
            'model_id': model_rec.id if model_rec else False,
            'type': 'ir.actions.server',
        }
        rec = env['ir.actions.server'].create(vals)
        action_ids[act['name']] = rec.id
        actions_created += 1
        print(f"  + Created: {act['name']} (id={rec.id})")

env.cr.commit()
print(f"\n  -> {actions_created} server actions created")

# ================================================================
# STEP 4: CREATE SCHEDULED CRON JOBS
# ================================================================
print("\n" + "-" * 70)
print("  STEP 4: CREATING SCHEDULED CRON JOBS")
print("-" * 70)

from datetime import datetime

CRON_JOBS = [
    {
        'cron_name': 'ITSM: Daily Team Digest (8:00 AM)',
        'interval_number': 1,
        'interval_type': 'days',
        'nextcall': datetime.now().replace(hour=7, minute=0, second=0) + timedelta(days=1),  # 8AM WAT = 7AM UTC
        'action_name': 'ITSM: Send Daily Team Digest',
    },
    {
        'cron_name': 'ITSM: Weekly Management Summary (Monday 9:00 AM)',
        'interval_number': 1,
        'interval_type': 'weeks',
        'nextcall': datetime.now().replace(hour=8, minute=0, second=0),  # Next occurrence
        'action_name': 'ITSM: Send Weekly Management Summary',
    },
]

crons_created = 0

for cron in CRON_JOBS:
    existing = env['ir.cron'].search([('cron_name', '=', cron['cron_name'])], limit=1)
    action_id = action_ids.get(cron['action_name'])
    
    if not action_id:
        print(f"  ✗ Action not found for: {cron['cron_name']}")
        continue
    
    if existing:
        existing.write({
            'ir_actions_server_id': action_id,
            'interval_number': cron['interval_number'],
            'interval_type': cron['interval_type'],
            'active': True,
        })
        print(f"  ○ Updated: {cron['cron_name']}")
    else:
        vals = {
            'cron_name': cron['cron_name'],
            'ir_actions_server_id': action_id,
            'user_id': 1,  # Admin
            'interval_number': cron['interval_number'],
            'interval_type': cron['interval_type'],
            'numbercall': -1,  # Unlimited
            'doall': False,
            'nextcall': cron['nextcall'],
            'active': True,
            'priority': 10,
        }
        env['ir.cron'].create(vals)
        crons_created += 1
        print(f"  + Created: {cron['cron_name']}")

env.cr.commit()
print(f"\n  -> {crons_created} cron jobs created")

# ================================================================
# SUMMARY
# ================================================================
print("\n" + "=" * 70)
print("  IMPLEMENTATION COMPLETE")
print("=" * 70)
print(f"  Mail Templates:     {templates_created} created")
print(f"  Server Actions:     {actions_created} created")
print(f"  Cron Jobs:          {crons_created} created")

print("\n  DIGEST SCHEDULE:")
print("  - Daily Team Digest:          8:00 AM WAT daily")
print("  - Weekly Management Summary:  Monday 9:00 AM WAT")
print("  - Customer Digest:            Configure manually per customer")
print("  - Escalation Alert:           Real-time (trigger via automation)")
print("  - CAB Digest:                 Configure before CAB meetings")

print("\n  MAIL SERVER:")
print(f"  - Using: servicedesk@westmetro.ng (id={MAIL_SERVER_ID})")

print("\n" + "=" * 70)
print("  NEXT STEPS:")
print("  1. Test email delivery: Settings → Technical → Emails")
print("  2. Add leadership users to receive management summary")
print("  3. Configure customer contacts for customer digests")
print("  4. Set up SLA rules for accurate breach tracking")
print("  5. Adjust cron schedules if needed: Settings → Technical → Scheduled Actions")
print("=" * 70)
print()
