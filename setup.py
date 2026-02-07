import os

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("❌ This field is required.")

def main():
    print("\n🤖 Welcome to Pico Minecraft Bot Setup! 🤖")
    print("------------------------------------------")
    print("This script will help you configure your bot easily.\n")

    # 1. Get Bot Token
    print("1️⃣  Get your Bot Token from @BotFather on Telegram.")
    bot_token = get_input("Enter Bot Token")

    # 2. Get Admin IDs
    print("\n2️⃣  Enter your Telegram User ID (get it from @userinfobot).")
    owner_id = get_input("Enter Owner ID")
    allowed_ids = get_input("Enter Allowed Chat IDs (comma separated, e.g. 123,456)", default=owner_id)

    # 3. Docker Container
    print("\n3️⃣  Enter the name of your Minecraft Docker container.")
    container_name = get_input("Container Name", default="minecraft")

    # 4. Paths
    print("\n4️⃣  Paths (Press Enter to use defaults if unsure).")
    # Try to guess default paths based on typical setups or user's current valid ones roughly
    default_props = "/home/user/minecraft/data/server.properties"
    default_backup = "/home/user/minecraft/scripts/auto_backup.sh"
    
    props_file = get_input("Path to server.properties", default=default_props)
    backup_script = get_input("Path to backup script", default=default_backup)

    # Generate content
    env_content = f"""# Telegram Bot Token
BOT_TOKEN={bot_token}

# Allowed Chat IDs (Comma separated)
ALLOWED_CHAT_IDS={allowed_ids}

# Owner ID (For sensitive commands like OP)
OWNER_ID={owner_id}

# Docker Container Name
CONTAINER_NAME={container_name}

# Paths
PROPERTIES_FILE={props_file}
BACKUP_SCRIPT={backup_script}
"""

    # Write file
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("\n✅ Configuration saved to '.env'!")
    except Exception as e:
        print(f"\n❌ Error saving file: {e}")
        return

    # 5. Service Installation (Optional)
    print("\n------------------------------------------")
    print("⚙️  Service Setup (Linux Only)")
    install_svc = get_input("Do you want to install this bot as a Background Service? (y/n)", default="y")
    
    if install_svc.lower() == "y":
        service_path = "/etc/systemd/system/minecraft-bot.service"
        current_dir = os.getcwd()
        python_exec = os.popen("which python3").read().strip()
        user = os.getenv("USER")

        service_content = f"""[Unit]
Description=Pico Minecraft Bot
After=network.target docker.service

[Service]
User={user}
WorkingDirectory={current_dir}
ExecStart={python_exec} {current_dir}/scripts/minecraft_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
        print(f"\nAttempting to create service at {service_path}...")
        try:
            # Try writing directly (needs sudo)
            if os.access("/etc/systemd/system", os.W_OK):
                with open(service_path, "w") as f:
                    f.write(service_content)
                print("✅ Service file created!")
                os.system("systemctl daemon-reload")
                os.system("systemctl enable --now minecraft-bot")
                print("🚀 Service STARTED and ENABLED! The bot is running.")
            else:
                # Fallback: Create a temporary file and ask user to copy
                with open("minecraft-bot.service", "w") as f:
                    f.write(service_content)
                print("⚠️  Permission denied (Run with sudo to auto-install).")
                print("📝 I created 'minecraft-bot.service' locally for you.")
                print("\n👉 Run these commands to finish:")
                print(f"sudo mv minecraft-bot.service {service_path}")
                print("sudo systemctl enable --now minecraft-bot")
        except Exception as e:
            print(f"❌ Error creating service: {e}")

    print("------------------------------------------")
    print("🎉 Setup Complete!")

if __name__ == "__main__":
    main()
