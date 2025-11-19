"""
Test Email Functionality
Run this script to test email sending and send test emails to all admins
"""
from app import create_app
from app.models import Admin, Lab
from app.notifications import send_email
from flask import current_app

def test_email_config():
    """Test email configuration"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("📧 EMAIL CONFIGURATION TEST")
        print("=" * 60)
        
        # Check configuration
        print(f"\n✓ MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}")
        print(f"✓ MAIL_PORT: {current_app.config.get('MAIL_PORT')}")
        print(f"✓ MAIL_USE_TLS: {current_app.config.get('MAIL_USE_TLS')}")
        print(f"✓ MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}")
        print(f"✓ MAIL_PASSWORD: {'*' * len(current_app.config.get('MAIL_PASSWORD', '')) if current_app.config.get('MAIL_PASSWORD') else 'NOT SET'}")
        print(f"✓ MAIL_DEFAULT_SENDER: {current_app.config.get('MAIL_DEFAULT_SENDER')}")
        
        if not current_app.config.get('MAIL_USERNAME'):
            print("\n❌ ERROR: MAIL_USERNAME is not set!")
            print("   Please check your .env file for EMAIL_USER")
            return False
        
        if not current_app.config.get('MAIL_PASSWORD'):
            print("\n❌ ERROR: MAIL_PASSWORD is not set!")
            print("   Please check your .env file for EMAIL_PASS")
            return False
        
        print("\n✅ Configuration looks good!")
        return True

def send_test_to_user():
    """Send a test email to the configured email address"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("📨 SENDING TEST EMAIL TO SENDER")
        print("=" * 60)
        
        sender_email = current_app.config.get('MAIL_USERNAME')
        if not sender_email:
            print("❌ No sender email configured!")
            return
        
        try:
            send_email(
                to=sender_email,
                subject="TechResolve - Test Email",
                body="""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #4f46e5;">✅ Email Configuration Successful!</h2>
                    <p>This is a test email from TechResolve complaint management system.</p>
                    <p>If you're seeing this, your email configuration is working correctly!</p>
                    <hr style="border: 1px solid #e5e7eb; margin: 20px 0;">
                    <p style="color: #6b7280; font-size: 14px;">
                        <strong>Configuration Details:</strong><br>
                        MAIL_SERVER: {}<br>
                        MAIL_PORT: {}<br>
                        MAIL_USE_TLS: {}<br>
                        SENDER: {}
                    </p>
                </body>
                </html>
                """.format(
                    current_app.config.get('MAIL_SERVER'),
                    current_app.config.get('MAIL_PORT'),
                    current_app.config.get('MAIL_USE_TLS'),
                    sender_email
                )
            )
            print(f"\n✅ Test email sent to: {sender_email}")
            print("   Check your inbox!")
        except Exception as e:
            print(f"\n❌ Failed to send test email: {e}")

def send_test_to_all_admins():
    """Send test email to all admins in the database"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("👥 SENDING TEST EMAILS TO ALL ADMINS")
        print("=" * 60)
        
        admins = Admin.query.all()
        
        if not admins:
            print("\n⚠️  No admins found in database!")
            print("   Please create admin accounts first.")
            return
        
        print(f"\nFound {len(admins)} admin(s):")
        for i, admin in enumerate(admins, 1):
            print(f"  {i}. {admin.name} ({admin.email})")
        
        print("\n📤 Sending test emails...\n")
        
        success_count = 0
        failed_count = 0
        
        for admin in admins:
            try:
                send_email(
                    to=admin.email,
                    subject="TechResolve - Admin Account Notification Test",
                    body=f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2 style="color: #4f46e5;">👋 Hello {admin.name}!</h2>
                        <p>This is a test email to verify your admin email notifications are working correctly.</p>
                        
                        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #1f2937; margin-top: 0;">Your Admin Account Details:</h3>
                            <p style="margin: 5px 0;"><strong>Name:</strong> {admin.name}</p>
                            <p style="margin: 5px 0;"><strong>Email:</strong> {admin.email}</p>
                            <p style="margin: 5px 0;"><strong>Role:</strong> {admin.role}</p>
                            <p style="margin: 5px 0;"><strong>Account Created:</strong> {admin.created_at.strftime('%B %d, %Y')}</p>
                        </div>
                        
                        <p>You will receive email notifications when:</p>
                        <ul>
                            <li>A complaint is assigned to you</li>
                            <li>Complaint status changes (if enabled in settings)</li>
                            <li>Important system updates</li>
                        </ul>
                        
                        <hr style="border: 1px solid #e5e7eb; margin: 20px 0;">
                        <p style="color: #6b7280; font-size: 14px;">
                            If you did not expect this email, please contact the system administrator.
                        </p>
                    </body>
                    </html>
                    """
                )
                print(f"  ✅ Sent to: {admin.name} ({admin.email})")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Failed to send to {admin.name} ({admin.email}): {e}")
                failed_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 SUMMARY: {success_count} successful, {failed_count} failed")
        print("=" * 60)

def get_all_labs():
    """Display all labs with their Discord webhooks"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("🔬 LABORATORY CONFIGURATION")
        print("=" * 60)
        
        labs = Lab.query.all()
        
        if not labs:
            print("\n⚠️  No labs found in database!")
            return
        
        print(f"\nFound {len(labs)} lab(s):")
        for i, lab in enumerate(labs, 1):
            webhook_status = "✅ Configured" if lab.discord_webhook else "❌ Not configured"
            print(f"\n  {i}. {lab.name}")
            print(f"     Discord Webhook: {webhook_status}")
            if lab.discord_webhook:
                print(f"     URL: {lab.discord_webhook[:50]}...")

def main():
    """Main test function"""
    print("\n🚀 TechResolve Email Test Utility")
    print("=" * 60)
    
    # Step 1: Check configuration
    if not test_email_config():
        print("\n⚠️  Please fix configuration issues before proceeding.")
        return
    
    # Step 2: Send test to sender
    print("\n" + "=" * 60)
    print("Step 1: Sending test email to sender address...")
    send_test_to_user()
    
    # Step 3: Send test to all admins
    print("\n" + "=" * 60)
    print("Step 2: Sending test emails to all admins...")
    send_test_to_all_admins()
    
    # Step 4: Show lab configuration
    get_all_labs()
    
    print("\n✅ Email test complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
