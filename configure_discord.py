"""
Configure Discord Webhooks for Labs

This script helps you easily configure Discord webhook URLs for each lab in the database.
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Lab

def configure_webhooks():
    """Interactive script to configure Discord webhooks for labs"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("🔧 DISCORD WEBHOOK CONFIGURATION")
        print("="*70)
        
        labs = Lab.query.all()
        
        if not labs:
            print("\n❌ No labs found in database!")
            return
        
        print(f"\n📊 Found {len(labs)} lab(s) in database:\n")
        
        for i, lab in enumerate(labs, 1):
            current_webhook = lab.discord_webhook or "Not configured"
            status = "✅" if lab.discord_webhook and lab.discord_webhook.strip() else "❌"
            print(f"{status} {i}. {lab.name}")
            if lab.discord_webhook:
                # Mask webhook URL for security
                masked = lab.discord_webhook[:50] + "..." if len(lab.discord_webhook) > 50 else lab.discord_webhook
                print(f"   Current webhook: {masked}")
        
        print("\n" + "-"*70)
        print("\n💡 How to get a Discord Webhook URL:")
        print("   1. Open your Discord server")
        print("   2. Right-click on the channel you want notifications in")
        print("   3. Select 'Edit Channel' > 'Integrations' > 'Webhooks'")
        print("   4. Click 'New Webhook' or use an existing one")
        print("   5. Copy the Webhook URL")
        print("\n" + "-"*70)
        
        while True:
            print("\n📝 Options:")
            print("   [1-9] - Configure webhook for a specific lab")
            print("   [list] - Show all labs again")
            print("   [test] - Test configured webhooks")
            print("   [clear] - Clear a webhook URL")
            print("   [exit] - Exit configuration")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'exit':
                print("\n✅ Configuration saved. Goodbye!")
                break
            
            elif choice == 'list':
                print("\n📊 Labs:")
                for i, lab in enumerate(labs, 1):
                    status = "✅" if lab.discord_webhook and lab.discord_webhook.strip() else "❌"
                    print(f"{status} {i}. {lab.name}")
            
            elif choice == 'test':
                print("\n🧪 Running webhook tests...")
                os.system('python test_discord.py')
            
            elif choice == 'clear':
                try:
                    lab_num = int(input("\nEnter lab number to clear webhook: "))
                    if 1 <= lab_num <= len(labs):
                        lab = labs[lab_num - 1]
                        lab.discord_webhook = None
                        db.session.commit()
                        print(f"\n✅ Webhook cleared for {lab.name}")
                    else:
                        print("\n❌ Invalid lab number!")
                except ValueError:
                    print("\n❌ Please enter a valid number!")
            
            elif choice.isdigit():
                lab_num = int(choice)
                if 1 <= lab_num <= len(labs):
                    lab = labs[lab_num - 1]
                    print(f"\n📝 Configuring webhook for: {lab.name}")
                    
                    if lab.discord_webhook:
                        print(f"   Current webhook: {lab.discord_webhook[:50]}...")
                        update = input("   Update existing webhook? (y/n): ").strip().lower()
                        if update != 'y':
                            continue
                    
                    webhook_url = input("\n   Enter Discord Webhook URL (or 'cancel'): ").strip()
                    
                    if webhook_url.lower() == 'cancel':
                        print("   ❌ Cancelled")
                        continue
                    
                    if not webhook_url.startswith('https://discord.com/api/webhooks/'):
                        print("\n   ⚠️  Warning: This doesn't look like a Discord webhook URL")
                        confirm = input("   Continue anyway? (y/n): ").strip().lower()
                        if confirm != 'y':
                            continue
                    
                    lab.discord_webhook = webhook_url
                    db.session.commit()
                    print(f"\n   ✅ Webhook configured for {lab.name}")
                    print(f"   💡 Run 'test' option to verify it works")
                else:
                    print("\n❌ Invalid lab number!")
            
            else:
                print("\n❌ Invalid choice!")


if __name__ == '__main__':
    configure_webhooks()
