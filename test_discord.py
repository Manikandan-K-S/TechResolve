"""
Test Discord webhook notifications for TechResolve

This script tests Discord webhook integration by sending test notifications
for all three main events: complaint creation, assignment, and status change.
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Complaint, Admin, Lab
from app.notifications import send_discord_notification, get_discord_webhook_for_lab
from datetime import datetime
import os

def test_discord_webhooks():
    """Test Discord webhook functionality with sample data"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("🔔 TESTING DISCORD WEBHOOK NOTIFICATIONS")
        print("="*70)
        
        # Get labs with Discord webhooks
        labs = Lab.query.all()
        print(f"\n📊 Found {len(labs)} labs in database:")
        
        labs_with_webhooks = []
        for lab in labs:
            webhook_url = get_discord_webhook_for_lab(lab.name)
            webhook_status = "✅ Configured" if webhook_url else "❌ Not configured"
            print(f"   - {lab.name}: {webhook_status}")
            if webhook_url:
                labs_with_webhooks.append((lab, webhook_url))
        
        if not labs_with_webhooks:
            print("\n" + "="*70)
            print("⚠️  NO DISCORD WEBHOOKS CONFIGURED")
            print("="*70)
            print("\n📝 To configure Discord webhooks:")
            print("   1. Create a Discord channel for notifications")
            print("   2. Go to Channel Settings > Integrations > Webhooks")
            print("   3. Create a new webhook and copy the URL")
            print("   4. Add the webhook URL to your .env file")
            print("\n💡 .env File Example:")
            print("   DISCORD_CC_LAB_WEBHOOK=https://discord.com/api/webhooks/...")
            print("   DISCORD_ISL_WEBHOOK=https://discord.com/api/webhooks/...")
            print("   DISCORD_IBM_LAB_WEBHOOK=https://discord.com/api/webhooks/...")
            print("\n📝 Format: DISCORD_{LAB_NAME}_WEBHOOK (uppercase, spaces to underscores)")
            print("   Examples:")
            print("   - 'CC Lab' → DISCORD_CC_LAB_WEBHOOK")
            print("   - 'ISL' → DISCORD_ISL_WEBHOOK")
            print("   - 'Hardware Lab' → DISCORD_HARDWARE_LAB_WEBHOOK")
            print("\n" + "="*70)
            return
        
        print(f"\n✅ Found {len(labs_with_webhooks)} lab(s) with Discord webhooks configured")
        print("\n" + "-"*70)
        
        # Get a sample complaint for testing
        complaint = Complaint.query.first()
        admin = Admin.query.filter_by(is_active=True).first()
        
        if not complaint:
            print("❌ No complaints found in database. Please create a complaint first.")
            return
        
        if not admin:
            print("❌ No active admins found in database.")
            return
        
        print(f"\nUsing sample complaint: {complaint.complaint_id}")
        print(f"Using sample admin: {admin.name}")
        
        # Test each webhook
        for lab, webhook_url in labs_with_webhooks:
            print(f"\n" + "="*70)
            print(f"🧪 TESTING WEBHOOK FOR: {lab.name}")
            print("="*70)
            
            # Test 1: New Complaint Notification
            print("\n📝 Test 1: New Complaint Notification")
            print("-" * 50)
            discord_data = {
                "content": "🆕 **New Complaint Received** (TEST MESSAGE)",
                "title": f"Complaint {complaint.complaint_id}",
                "description": f"A new technical complaint has been submitted and requires attention.",
                "color": 3447003,  # Blue color
                "fields": [
                    {"name": "📋 Complaint ID", "value": complaint.complaint_id, "inline": True},
                    {"name": "👤 Reporter", "value": complaint.name, "inline": True},
                    {"name": "📧 Email", "value": complaint.email, "inline": True},
                    {"name": "🔬 Lab", "value": lab.name, "inline": True},
                    {"name": "📁 Category", "value": complaint.category, "inline": True},
                    {"name": "⚠️ Priority", "value": complaint.priority or 'Low', "inline": True},
                    {"name": "📊 Status", "value": f"⏳ {complaint.status}", "inline": True},
                    {"name": "📝 Description", "value": "This is a test notification from TechResolve system.", "inline": False}
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            send_discord_notification(webhook_url, discord_data)
            
            # Test 2: Assignment Notification
            print("\n👤 Test 2: Assignment Notification")
            print("-" * 50)
            discord_data = {
                "content": f"👤 **Admin Assignment Update** (TEST MESSAGE)",
                "title": f"Complaint {complaint.complaint_id} Assigned",
                "description": f"**{admin.name}** has been assigned to handle this complaint.",
                "color": 10181046,  # Purple color
                "fields": [
                    {"name": "📋 Complaint ID", "value": complaint.complaint_id, "inline": True},
                    {"name": "👤 Assigned To", "value": admin.name, "inline": True},
                    {"name": "👨‍💼 Assigned By", "value": "Test System", "inline": True},
                    {"name": "👥 Reporter", "value": complaint.name, "inline": True},
                    {"name": "🔬 Lab", "value": lab.name, "inline": True},
                    {"name": "📁 Category", "value": complaint.category, "inline": True},
                    {"name": "📊 Status", "value": complaint.status, "inline": True},
                    {"name": "⚠️ Priority", "value": complaint.priority or 'Low', "inline": True}
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            send_discord_notification(webhook_url, discord_data)
            
            # Test 3: Resolved Status Notification
            print("\n✅ Test 3: Resolved Status Notification")
            print("-" * 50)
            discord_data = {
                "content": f"✅ **Status Update - Resolved** (TEST MESSAGE)",
                "title": f"Complaint {complaint.complaint_id} Updated",
                "description": f"Status changed to **Resolved** by {admin.name}",
                "color": 3066993,  # Green color
                "fields": [
                    {"name": "📋 Complaint ID", "value": complaint.complaint_id, "inline": True},
                    {"name": "📊 New Status", "value": "✅ **Resolved**", "inline": True},
                    {"name": "👨‍💼 Updated By", "value": admin.name, "inline": True},
                    {"name": "👤 Reporter", "value": complaint.name, "inline": True},
                    {"name": "🔬 Lab", "value": lab.name, "inline": True},
                    {"name": "📁 Category", "value": complaint.category, "inline": True},
                    {"name": "📝 Notes", "value": "Test: The issue has been successfully resolved. This is a test notification.", "inline": False}
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            send_discord_notification(webhook_url, discord_data)
            
            # Test 4: Terminated Status Notification
            print("\n❌ Test 4: Terminated Status Notification")
            print("-" * 50)
            discord_data = {
                "content": f"❌ **Status Update - Terminated** (TEST MESSAGE)",
                "title": f"Complaint {complaint.complaint_id} Updated",
                "description": f"Status changed to **Terminated** by {admin.name}",
                "color": 15158332,  # Red color
                "fields": [
                    {"name": "📋 Complaint ID", "value": complaint.complaint_id, "inline": True},
                    {"name": "📊 New Status", "value": "❌ **Terminated**", "inline": True},
                    {"name": "👨‍💼 Updated By", "value": admin.name, "inline": True},
                    {"name": "👤 Reporter", "value": complaint.name, "inline": True},
                    {"name": "🔬 Lab", "value": lab.name, "inline": True},
                    {"name": "📁 Category", "value": complaint.category, "inline": True},
                    {"name": "📝 Notes", "value": "Test: Unable to reproduce the issue. This is a test notification.", "inline": False}
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            send_discord_notification(webhook_url, discord_data)
        
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"\n✅ Tested {len(labs_with_webhooks)} Discord webhook(s)")
        print(f"✅ Sent 4 test notifications per webhook")
        print(f"✅ Total notifications sent: {len(labs_with_webhooks) * 4}")
        print("\n💡 Check your Discord channel(s) to verify the notifications")
        print("\n📝 All test messages are marked with '(TEST MESSAGE)' label")
        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    test_discord_webhooks()
