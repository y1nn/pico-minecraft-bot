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
        print("------------------------------------------")
        print("🚀 You can now run the bot with:")
        print("   python3 scripts/minecraft_bot.py")
        print("------------------------------------------")
    except Exception as e:
        print(f"\n❌ Error saving file: {e}")

if __name__ == "__main__":
    main()
