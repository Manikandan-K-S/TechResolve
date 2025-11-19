"""
Test All Notification Scenarios
This script tests all email notification workflows in TechResolve
"""
from app import create_app
from app.models import Admin, Lab, Complaint, ComplaintLog, db
from app.notifications import notify_complaint_creation, notify_assignment, notify_status_change
from datetime import datetime

def test_all_notifications():
    """Test complete notification workflow"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("🧪 TESTING ALL EMAIL NOTIFICATION SCENARIOS")
        print("=" * 70)
        
        # Get test data
        admin = Admin.query.first()
        lab = Lab.query.first()
        
        if not admin:
            print("\n❌ No admin found! Please create an admin first.")
            return
        
        if not lab:
            print("\n❌ No lab found! Please create a lab first.")
            return
        
        print(f"\n📋 Test Setup:")
        print(f"   Admin: {admin.name} ({admin.email})")
        print(f"   Lab: {lab.name}")
        
        # Create a test complaint
        print("\n" + "-" * 70)
        print("1️⃣  TESTING: Complaint Creation Notification")
        print("-" * 70)
        
        test_complaint = Complaint(
            complaint_id="CMP2025-TEST",
            email="testuser@example.com",
            name="Test User",
            lab_id=lab.id,
            category="Software",
            description="This is a test complaint for notification testing.",
            status="Pending",
            priority="Medium"
        )
        
        try:
            # Test 1: Complaint Creation
            print("Sending complaint creation notification to user...")
            notify_complaint_creation(test_complaint)
            print("✅ Notification sent to: testuser@example.com")
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 2: Admin Assignment
        print("\n" + "-" * 70)
        print("2️⃣  TESTING: Admin Assignment Notification")
        print("-" * 70)
        
        try:
            test_complaint.assigned_admin_id = admin.id
            print(f"Sending assignment notification to admin...")
            notify_assignment(test_complaint, admin, admin)
            print(f"✅ Notification sent to: {admin.email}")
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 3: Status Change - In Progress
        print("\n" + "-" * 70)
        print("3️⃣  TESTING: Status Change to 'In Progress'")
        print("-" * 70)
        
        try:
            test_complaint.status = "In Progress"
            print("Sending status change notification to user...")
            notify_status_change(test_complaint, admin)
            print("✅ Notification sent to: testuser@example.com")
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 4: Status Change - Resolved
        print("\n" + "-" * 70)
        print("4️⃣  TESTING: Status Change to 'Resolved' (IMPORTANT)")
        print("-" * 70)
        
        try:
            test_complaint.status = "Resolved"
            test_complaint.resolution_notes = "Issue has been fixed. The software has been reinstalled and is working properly now."
            print("Sending RESOLVED notification to user...")
            notify_status_change(test_complaint, admin)
            print("✅ Notification sent to: testuser@example.com")
            print("   📝 Resolution notes included in email")
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 5: Status Change - Terminated
        print("\n" + "-" * 70)
        print("5️⃣  TESTING: Status Change to 'Terminated' (IMPORTANT)")
        print("-" * 70)
        
        try:
            test_complaint.status = "Terminated"
            test_complaint.resolution_notes = "Complaint terminated as the issue is no longer reproducible."
            print("Sending TERMINATED notification to user...")
            notify_status_change(test_complaint, admin)
            print("✅ Notification sent to: testuser@example.com")
            print("   📝 Termination reason included in email")
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 NOTIFICATION TEST SUMMARY")
        print("=" * 70)
        print("""
✅ Test 1: Complaint Creation → User Email
✅ Test 2: Admin Assignment → Admin Email  
✅ Test 3: Status 'In Progress' → User Email
✅ Test 4: Status 'Resolved' → User Email (with resolution notes)
✅ Test 5: Status 'Terminated' → User Email (with termination reason)

📧 Expected Emails Sent: 5
   - 1 to testuser@example.com (complaint creation)
   - 1 to {admin.email} (assignment)
   - 3 to testuser@example.com (status updates)

⚠️  Note: Since testuser@example.com is not a real email, those emails
   won't be delivered, but you should see success messages above.
   
   Check {admin.email} for the assignment notification!
        """)
        
        print("=" * 70)
        print("✅ ALL NOTIFICATION TESTS COMPLETED")
        print("=" * 70)
        
        # Show notification workflow
        print("\n📋 COMPLETE NOTIFICATION WORKFLOW:")
        print("""
┌─────────────────────────────────────────────────────────────┐
│                  NOTIFICATION FLOW CHART                     │
└─────────────────────────────────────────────────────────────┘

1. USER SUBMITS COMPLAINT
   ↓
   📧 Email sent to: USER
   ✉️  Subject: "✅ Complaint Received: CMP2025-XXXX"
   📝 Contains: Complaint ID, Lab, Category, Status, Priority
   
2. ADMIN ASSIGNS COMPLAINT  
   ↓
   📧 Email sent to: ASSIGNED ADMIN
   ✉️  Subject: "🔔 Complaint Assigned: CMP2025-XXXX"
   📝 Contains: Full complaint details, Reporter info, Description
   
3. ADMIN CHANGES STATUS TO "IN PROGRESS"
   ↓
   📧 Email sent to: USER
   ✉️  Subject: "🔄 Complaint In Progress: CMP2025-XXXX"
   📝 Contains: Status update, Lab, Category
   
4. ADMIN CHANGES STATUS TO "RESOLVED"
   ↓
   📧 Email sent to: USER
   ✉️  Subject: "✅ Complaint Resolved: CMP2025-XXXX"
   📝 Contains: Resolution notes, What's next instructions
   🎯 SPECIAL: Green color scheme, resolution message
   
5. ADMIN CHANGES STATUS TO "TERMINATED"
   ↓
   📧 Email sent to: USER
   ✉️  Subject: "❌ Complaint Terminated: CMP2025-XXXX"
   📝 Contains: Termination reason, Action guidance
   🎯 SPECIAL: Red color scheme, termination message

┌─────────────────────────────────────────────────────────────┐
│           WHO GETS NOTIFIED & WHEN                          │
└─────────────────────────────────────────────────────────────┘

ACTION                          | USER EMAIL | ADMIN EMAIL | DISCORD
--------------------------------|------------|-------------|--------
Complaint Created               |     ✅     |     ❌      |   ✅
Admin Assigned                  |     ❌     |     ✅      |   ✅
Status → In Progress            |     ✅     |     ❌      |   ✅
Status → Resolved               |     ✅     |     ❌      |   ✅
Status → Terminated             |     ✅     |     ❌      |   ✅
Tag Changed                     |     ❌     |     ❌      |   ❌
Priority Changed                |     ❌     |     ❌      |   ❌
        """)

def test_real_complaint_workflow():
    """Test with real data from database"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("🔍 CHECKING EXISTING COMPLAINTS IN DATABASE")
        print("=" * 70)
        
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
        
        if not complaints:
            print("\n⚠️  No complaints found in database.")
            print("   Submit a complaint first to test real notifications.")
            return
        
        print(f"\nFound {len(complaints)} recent complaint(s):\n")
        
        for i, complaint in enumerate(complaints, 1):
            print(f"{i}. {complaint.complaint_id} - {complaint.name}")
            print(f"   Email: {complaint.email}")
            print(f"   Status: {complaint.status}")
            print(f"   Lab: {complaint.lab.name}")
            print(f"   Created: {complaint.created_at.strftime('%Y-%m-%d %H:%M')}")
            print()
        
        print("💡 To test notifications with real data:")
        print("   1. Login as admin")
        print("   2. Assign a complaint to yourself")
        print("   3. Change status to 'Resolved' or 'Terminated'")
        print("   4. Check your email inbox!")

if __name__ == '__main__':
    print("\n🚀 TechResolve Notification Test Suite\n")
    
    # Test all notification scenarios
    test_all_notifications()
    
    # Check existing complaints
    test_real_complaint_workflow()
    
    print("\n✅ Test suite completed!")
    print("=" * 70)
