from flask_mail import Message
from flask import current_app
from .extensions import mail
import requests
import os

# --------------------------
# Get Discord Webhook URL for Lab
# --------------------------
def get_discord_webhook_for_lab(lab_name):
    """
    Get Discord webhook URL from environment variables based on lab name.
    Format: DISCORD_{LAB_NAME}_WEBHOOK (uppercase, spaces replaced with underscores)
    
    Examples:
    - "CC Lab" → DISCORD_CC_LAB_WEBHOOK
    - "ISL" → DISCORD_ISL_WEBHOOK
    - "IBM Lab" → DISCORD_IBM_LAB_WEBHOOK
    """
    if not lab_name:
        return None
    
    # Convert lab name to environment variable format
    # "CC Lab" -> "CC_LAB", "IBM Lab" -> "IBM_LAB"
    env_key = f"DISCORD_{lab_name.upper().replace(' ', '_')}_WEBHOOK"
    
    webhook_url = os.getenv(env_key)
    
    if not webhook_url or not webhook_url.strip():
        # Fallback: Try without spaces (CC Lab -> DISCORD_CC_WEBHOOK)
        env_key_alt = f"DISCORD_{lab_name.upper().replace(' ', '')}_WEBHOOK"
        webhook_url = os.getenv(env_key_alt)
    
    return webhook_url if webhook_url and webhook_url.strip() else None

# --------------------------
# Send Email
# --------------------------
def send_email(to, subject, body):
    """
    Send email via Flask-Mail
    :param to: recipient email or list
    :param subject: email subject
    :param body: email body (HTML or plain text)
    """
    if not isinstance(to, list):
        to = [to]

    # Get sender from config, use a fallback if not set
    sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
    
    if not sender:
        print("Error: No email sender configured. Set EMAIL_USER in .env file")
        return

    msg = Message(
        subject=subject,
        recipients=to,
        html=body,
        sender=sender
    )
    try:
        mail.send(msg)
        print(f"✅ Email sent successfully to: {to}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

# --------------------------
# Send Discord Notification
# --------------------------
def send_discord_notification(webhook_url, embed_data):
    """
    Send rich embed notification to Discord webhook.
    :param webhook_url: Discord webhook URL
    :param embed_data: Dictionary with embed data (title, description, color, fields, etc.)
    """
    if not webhook_url or not webhook_url.strip():
        print("⚠️ No Discord webhook URL provided - skipping Discord notification")
        return

    # Create Discord embed
    embed = {
        "title": embed_data.get("title", "TechResolve Notification"),
        "description": embed_data.get("description", ""),
        "color": embed_data.get("color", 5814783),  # Default blue color
        "fields": embed_data.get("fields", []),
        "footer": {
            "text": "TechResolve - PSG College of Technology"
        },
        "timestamp": embed_data.get("timestamp")
    }
    
    # Add thumbnail if provided
    if "thumbnail" in embed_data:
        embed["thumbnail"] = {"url": embed_data["thumbnail"]}

    payload = {
        "embeds": [embed]
    }
    
    # Add content text if provided
    if "content" in embed_data:
        payload["content"] = embed_data["content"]

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            print(f"✅ Discord notification sent successfully")
        else:
            print(f"❌ Failed to send Discord notification: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        print(f"⏱️ Discord notification timeout - webhook may be slow or invalid")
    except Exception as exc:
        print(f"❌ Error sending Discord notification: {exc}")

# --------------------------
# Combined Notification Function
# --------------------------
def notify_complaint_creation(complaint):
    """Notify user and lab channel about a new complaint."""
    subject = f"✅ Complaint Received: {complaint.complaint_id}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9fafb;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="background-color: #4f46e5; padding: 20px; text-align: center;">
                <h2 style="color: white; margin: 0;">TechResolve - Complaint Registered</h2>
            </div>
            <div style="padding: 30px;">
                <p style="font-size: 16px; color: #374151;">Hello <strong>{complaint.name}</strong>,</p>
                <p style="font-size: 14px; color: #6b7280;">Your complaint has been successfully registered in our system.</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="color: #1f2937; margin-top: 0; font-size: 16px;">Complaint Details:</h3>
                    <table style="width: 100%; font-size: 14px;">
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280; width: 40%;"><strong>Complaint ID:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;"><strong style="color: #4f46e5;">{complaint.complaint_id}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Lab:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.lab.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Category:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.category}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Status:</strong></td>
                            <td style="padding: 8px 0;"><span style="background-color: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 12px; font-size: 12px;">{complaint.status}</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Priority:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.priority or 'Low'}</td>
                        </tr>
                    </table>
                </div>
                
                <p style="font-size: 14px; color: #6b7280;">We will keep you updated on the progress via email notifications.</p>
                
                <div style="background-color: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 13px; color: #1e40af;">
                        <strong>💡 Track Your Complaint:</strong><br>
                        Use your Complaint ID <strong>{complaint.complaint_id}</strong> or email address to track the status anytime.
                    </p>
                </div>
            </div>
            <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #6b7280; margin: 0;">
                    TechResolve - Technical Complaint Management System<br>
                    PSG College of Technology
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(complaint.email, subject, body)

    # Send Discord notification to lab admins (not to user)
    webhook_url = get_discord_webhook_for_lab(complaint.lab.name)
    if webhook_url:
        discord_data = {
            "content": "🆕 **New Complaint Received**",
            "title": f"Complaint {complaint.complaint_id}",
            "description": f"A new technical complaint has been submitted and requires attention.",
            "color": 3447003,  # Blue color
            "fields": [
                {"name": "📋 Complaint ID", "value": complaint.complaint_id, "inline": True},
                {"name": "👤 Reporter", "value": complaint.name, "inline": True},
                {"name": "📧 Email", "value": complaint.email, "inline": True},
                {"name": "🔬 Lab", "value": complaint.lab.name, "inline": True},
                {"name": "📁 Category", "value": complaint.category, "inline": True},
                {"name": "⚠️ Priority", "value": complaint.priority or 'Low', "inline": True},
                {"name": "📊 Status", "value": f"⏳ {complaint.status}", "inline": True},
                {"name": "📝 Description", "value": complaint.description[:500] + ("..." if len(complaint.description) > 500 else ""), "inline": False}
            ],
            "timestamp": complaint.created_at.isoformat()
        }
        send_discord_notification(webhook_url, discord_data)


def notify_assignment(complaint, assigned_admin, actor):
    """Alert assigned admin when a complaint is tagged to them."""
    if not assigned_admin:
        return

    subject = f"🔔 Complaint Assigned: {complaint.complaint_id}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9fafb;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="background-color: #7c3aed; padding: 20px; text-align: center;">
                <h2 style="color: white; margin: 0;">New Complaint Assignment</h2>
            </div>
            <div style="padding: 30px;">
                <p style="font-size: 16px; color: #374151;">Hello <strong>{assigned_admin.name}</strong>,</p>
                <p style="font-size: 14px; color: #6b7280;">You have been assigned to a new complaint. Please review and take action.</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="color: #1f2937; margin-top: 0; font-size: 16px;">Complaint Information:</h3>
                    <table style="width: 100%; font-size: 14px;">
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280; width: 40%;"><strong>Complaint ID:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;"><strong style="color: #7c3aed;">{complaint.complaint_id}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Reporter:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Email:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Lab:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.lab.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Category:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.category}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Status:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.status}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Priority:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.priority or 'Low'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Assigned By:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{actor.name if actor else 'System'}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 13px; color: #9a3412;">
                        <strong>⚡ Action Required:</strong><br>
                        Please login to the admin dashboard to review and update this complaint.
                    </p>
                </div>
                
                <p style="font-size: 13px; color: #6b7280;"><strong>Description:</strong><br>{complaint.description}</p>
            </div>
            <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #6b7280; margin: 0;">
                    TechResolve - Technical Complaint Management System<br>
                    PSG College of Technology
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(assigned_admin.email, subject, body)

    # Send Discord notification to lab admins about the assignment
    webhook_url = get_discord_webhook_for_lab(complaint.lab.name)
    if webhook_url:
        discord_data = {
            "content": f"👤 **Admin Assignment Update**",
            "title": f"Complaint {complaint.complaint_id} Assigned",
            "description": f"**{assigned_admin.name}** has been assigned to handle this complaint.",
            "color": 10181046,  # Purple color
            "fields": [
                {"name": "📋 Complaint ID", "value": complaint.complaint_id, "inline": True},
                {"name": "👤 Assigned To", "value": assigned_admin.name, "inline": True},
                {"name": "👨‍💼 Assigned By", "value": actor.name if actor else 'System', "inline": True},
                {"name": "👥 Reporter", "value": complaint.name, "inline": True},
                {"name": "🔬 Lab", "value": complaint.lab.name, "inline": True},
                {"name": "📁 Category", "value": complaint.category, "inline": True},
                {"name": "📊 Status", "value": complaint.status, "inline": True},
                {"name": "⚠️ Priority", "value": complaint.priority or 'Low', "inline": True}
            ],
            "timestamp": complaint.updated_at.isoformat() if complaint.updated_at else complaint.created_at.isoformat()
        }
        send_discord_notification(webhook_url, discord_data)


def notify_status_change(complaint, actor):
    """Notify reporter when status changes."""
    # Determine status color and icon
    status_colors = {
        'Pending': {'bg': '#fef3c7', 'text': '#92400e', 'icon': '⏳'},
        'In Progress': {'bg': '#dbeafe', 'text': '#1e40af', 'icon': '🔄'},
        'Resolved': {'bg': '#d1fae5', 'text': '#065f46', 'icon': '✅'},
        'Terminated': {'bg': '#fee2e2', 'text': '#991b1b', 'icon': '❌'}
    }
    
    status_info = status_colors.get(complaint.status, {'bg': '#f3f4f6', 'text': '#374151', 'icon': '📋'})
    status_icon = status_info['icon']
    
    # Special messages for Resolved and Terminated
    if complaint.status == 'Resolved':
        subject = f"✅ Complaint Resolved: {complaint.complaint_id}"
        status_message = "Great news! Your complaint has been resolved."
        action_note = "If you're satisfied with the resolution, no further action is needed. If the issue persists, please submit a new complaint."
    elif complaint.status == 'Terminated':
        subject = f"❌ Complaint Terminated: {complaint.complaint_id}"
        status_message = "Your complaint has been terminated."
        action_note = "If you believe this was closed in error or need further assistance, please contact the admin or submit a new complaint."
    elif complaint.status == 'In Progress':
        subject = f"🔄 Complaint In Progress: {complaint.complaint_id}"
        status_message = "Your complaint is now being worked on."
        action_note = "An admin is actively working on resolving your issue. You'll be notified of any further updates."
    else:
        subject = f"{status_icon} Complaint Update: {complaint.complaint_id}"
        status_message = f"Your complaint status has been updated to {complaint.status}."
        action_note = "You will receive further notifications as the status changes."
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9fafb;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="background-color: {'#10b981' if complaint.status == 'Resolved' else '#ef4444' if complaint.status == 'Terminated' else '#3b82f6'}; padding: 20px; text-align: center;">
                <h2 style="color: white; margin: 0;">{status_icon} Complaint Status Update</h2>
            </div>
            <div style="padding: 30px;">
                <p style="font-size: 16px; color: #374151;">Hello <strong>{complaint.name}</strong>,</p>
                <p style="font-size: 14px; color: #6b7280;">{status_message}</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="color: #1f2937; margin-top: 0; font-size: 16px;">Complaint Details:</h3>
                    <table style="width: 100%; font-size: 14px;">
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280; width: 40%;"><strong>Complaint ID:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;"><strong style="color: #4f46e5;">{complaint.complaint_id}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Lab:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.lab.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Category:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{complaint.category}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>New Status:</strong></td>
                            <td style="padding: 8px 0;">
                                <span style="background-color: {status_info['bg']}; color: {status_info['text']}; padding: 6px 16px; border-radius: 12px; font-size: 13px; font-weight: bold;">
                                    {status_icon} {complaint.status}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;"><strong>Updated By:</strong></td>
                            <td style="padding: 8px 0; color: #1f2937;">{actor.name if actor else 'System'}</td>
                        </tr>
                    </table>
                </div>
                
                {f'''<div style="background-color: #f0fdf4; border: 2px solid #10b981; border-radius: 6px; padding: 20px; margin: 20px 0;">
                    <h4 style="color: #065f46; margin-top: 0; font-size: 15px;">📝 Resolution Notes:</h4>
                    <p style="color: #166534; font-size: 14px; margin: 0; white-space: pre-wrap;">{complaint.resolution_notes}</p>
                </div>''' if complaint.resolution_notes else f'<div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;"><p style="margin: 0; font-size: 13px; color: #78350f;"><strong>ℹ️ Note:</strong> No additional notes provided.</p></div>'}
                
                <div style="background-color: {'#ecfdf5' if complaint.status == 'Resolved' else '#fef2f2' if complaint.status == 'Terminated' else '#eff6ff'}; border-left: 4px solid {'#10b981' if complaint.status == 'Resolved' else '#ef4444' if complaint.status == 'Terminated' else '#3b82f6'}; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 13px; color: {'#065f46' if complaint.status == 'Resolved' else '#991b1b' if complaint.status == 'Terminated' else '#1e40af'};">
                        <strong>💡 What's Next?</strong><br>
                        {action_note}
                    </p>
                </div>
            </div>
            <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #6b7280; margin: 0;">
                    TechResolve - Technical Complaint Management System<br>
                    PSG College of Technology
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(complaint.email, subject, body)

    # Send Discord notification to lab admins about status change
    webhook_url = get_discord_webhook_for_lab(complaint.lab.name)
    if webhook_url:
        # Determine Discord color based on status
        discord_colors = {
            'Pending': 16776960,      # Yellow
            'In Progress': 3447003,   # Blue
            'Resolved': 3066993,      # Green
            'Terminated': 15158332    # Red
        }
        
        discord_color = discord_colors.get(complaint.status, 9807270)  # Default gray
        
        discord_fields = [
            {"name": "📋 Complaint ID", "value": complaint.complaint_id, "inline": True},
            {"name": "📊 New Status", "value": f"{status_icon} **{complaint.status}**", "inline": True},
            {"name": "👨‍💼 Updated By", "value": actor.name if actor else 'System', "inline": True},
            {"name": "👤 Reporter", "value": complaint.name, "inline": True},
            {"name": "🔬 Lab", "value": complaint.lab.name, "inline": True},
            {"name": "� Category", "value": complaint.category, "inline": True}
        ]
        
        # Add resolution notes if available
        if complaint.resolution_notes:
            notes_preview = complaint.resolution_notes[:500] + ("..." if len(complaint.resolution_notes) > 500 else "")
            discord_fields.append({"name": "📝 Notes", "value": notes_preview, "inline": False})
        
        discord_data = {
            "content": f"{status_icon} **Status Update - {complaint.status}**",
            "title": f"Complaint {complaint.complaint_id} Updated",
            "description": f"Status changed to **{complaint.status}** by {actor.name if actor else 'System'}",
            "color": discord_color,
            "fields": discord_fields,
            "timestamp": complaint.updated_at.isoformat() if complaint.updated_at else complaint.created_at.isoformat()
        }
        send_discord_notification(webhook_url, discord_data)
