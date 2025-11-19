"""
Simple Test: Send test notifications using real complaints
"""
from app import create_app
from app.models import Complaint, Admin
from app.notifications import notify_status_change

def main():
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("📧 TESTING STATUS CHANGE NOTIFICATIONS")
        print("=" * 70)
        
        # Get a real complaint
        complaint = Complaint.query.filter_by(complaint_id='CMP2025-0003').first()
        
        if not complaint:
            print("\n❌ Complaint CMP2025-0003 not found!")
            print("   Available complaints:")
            for c in Complaint.query.all():
                print(f"   - {c.complaint_id}")
            return
        
        # Get an admin
        admin = Admin.query.first()
        
        if not admin:
            print("\n❌ No admin found!")
            return
        
        print(f"\n✅ Found complaint: {complaint.complaint_id}")
        print(f"   Reporter: {complaint.name} ({complaint.email})")
        print(f"   Current Status: {complaint.status}")
        print(f"   Lab: {complaint.lab.name if complaint.lab else 'No lab'}")
        print(f"\n✅ Using admin: {admin.name}")
        
        # Test 1: Resolved notification
        print("\n" + "-" * 70)
        print("TEST 1: Sending 'Resolved' notification")
        print("-" * 70)
        
        original_status = complaint.status
        original_notes = complaint.resolution_notes
        
        complaint.status = "Resolved"
        complaint.resolution_notes = "Test: Issue has been resolved successfully. All systems are working properly now."
        
        try:
            notify_status_change(complaint, admin)
            print(f"✅ Email sent to: {complaint.email}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Terminated notification  
        print("\n" + "-" * 70)
        print("TEST 2: Sending 'Terminated' notification")
        print("-" * 70)
        
        complaint.status = "Terminated"
        complaint.resolution_notes = "Test: Complaint terminated as the issue could not be reproduced."
        
        try:
            notify_status_change(complaint, admin)
            print(f"✅ Email sent to: {complaint.email}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Restore original values
        complaint.status = original_status
        complaint.resolution_notes = original_notes
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"""
✅ Sent 2 test emails to: {complaint.email}
   1. Resolved notification (with green styling)
   2. Terminated notification (with red styling)

📧 Check the inbox for:
   - Subject: "✅ Complaint Resolved: {complaint.complaint_id}"
   - Subject: "❌ Complaint Terminated: {complaint.complaint_id}"

💡 Both emails include:
   - Complaint details
   - Resolution/termination notes
   - Color-coded status badges
   - Next steps guidance
        """)
        print("=" * 70)

if __name__ == '__main__':
    main()
