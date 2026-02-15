import requests
import json
import time
import subprocess
import os
import re
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_CHAT_IDS = [int(id) for id in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if id]
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "minecraft")
PROPERTIES_FILE = os.getenv("PROPERTIES_FILE", "/data/server.properties")
BACKUP_SCRIPT = os.getenv("BACKUP_SCRIPT", "./scripts/auto_backup.sh")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# State to track pending broadcasts and chat mode
pending_broadcast = {}
chat_mode_enabled = True # Default ON

COMMANDS_HELP = (
    "🛠 *Commands:*\n"
    "`/add <name>` - Add player\n"
    "`/remove <name>` - Remove player\n"
    "`/kick <name>` - Kick player\n"
    "`/cmd <command>` - Run RCON (Owner) 💻"
)

# English Guide (Translated from Arabic)
GUIDE_TEXT = (
    "📜 *Common Commands Guide (Commander):*\n"
    "Type `/cmd` followed by the command:\n\n"
    "⏰ *Time & Weather:*\n"
    "`time set day` (Day)\n"
    "`weather clear` (Clear)\n\n"
    "👤 *Player Management:*\n"
    "`gamemode creative <name>`\n"
    "`gamemode survival <name>`\n"
    "`tp <player> <target>` (Teleport)\n"
    "`give <name> diamond 64`\n\n"
    "🔨 *Admin:*\n"
    "`op <name>` (Give OP)\n"
    "`deop <name>` (Remove OP)\n"
    "`kick <name>`\n"
    "`ban <name>`\n"
    "`say <message>` (Broadcast)"
)

def rcon_command(cmd_input):
    try:
        if isinstance(cmd_input, list):
            args = cmd_input
        else:
            args = cmd_input.split()

        cmd = ["docker", "exec", "-i", CONTAINER_NAME, "rcon-cli"] + args
        # Add timeout to prevent hanging commands
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "⚠️ Error: RCON Timeout (Server Busy)"
    except Exception as e:
        return f"Error: {e}"

def start_server():
    try:
        subprocess.run(["docker", "start", CONTAINER_NAME], check=True, timeout=10)
        return "✅ Server starting..."
    except Exception as e:
        return f"❌ Error: {e}"

def restart_server():
    try:
        subprocess.run(["docker", "restart", CONTAINER_NAME], check=True, timeout=60)
        return "🔄 Server restarting..."
    except Exception as e:
        return f"❌ Error: {e}"

def stop_server():
    try:
        subprocess.run(["docker", "stop", CONTAINER_NAME], check=True, timeout=20)
        return "🛑 Server stopped."
    except Exception as e:
        return f"❌ Error: {e}"

def run_backup():
    try:
        # Run in background to avoid blocking bot
        if os.path.exists(BACKUP_SCRIPT):
            subprocess.Popen([BACKUP_SCRIPT])
            return "📦 Backup started! You will receive files shortly."
        else:
            return "❌ Backup script not found."
    except Exception as e:
        return f"❌ Error starting backup: {e}"

def get_whitelist_state():
    try:
        with open(PROPERTIES_FILE, "r") as f:
            for line in f:
                if line.strip().startswith("white-list="):
                    state = line.strip().split("=")[1].lower()
                    return state == "true"
    except Exception:
        return None
    return False

def get_server_stats():
    try:
        # Get RAM/CPU usage
        stats = subprocess.check_output(
            ["docker", "stats", CONTAINER_NAME, "--no-stream", "--format", "{{.MemUsage}} / {{.CPUPerc}}"],
            timeout=5
        ).strip().decode()
        return stats
    except:
        return "OFFLINE"

def get_server_status():
    try:
        # Check container status
        box_status = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.Status}}", CONTAINER_NAME],
            timeout=5
        ).strip().decode()
    except:
        return "🔴 *Server is DOWN* (Container not found)"

    if box_status != "running":
         return f"🔴 *Server is {box_status.upper()}*\n📦 Status: Offline"

    # Check whitelist status
    is_wl = get_whitelist_state()
    wl_icon = "🔒" if is_wl else "🔓"
    wl_text = "*ON (Locked)*" if is_wl else "*OFF (Open)*"

    # Stats
    res_usage = get_server_stats()

    # Check player count via RCON
    list_out = rcon_command("list")
    player_text = "Checking..."
    match = re.search(r"There are (\d+) of a max of (\d+) players online", list_out)
    if match:
        count = match.group(1)
        max_p = match.group(2)
        player_text = f"`{count}/{max_p}`"

    status_msg = (
        f"🌍 *Server Status:*\n"
        f"------------------\n"
        f"📦 State: `{box_status.upper()}`\n"
        f"🛡️ Whitelist: {wl_icon} {wl_text}\n"
        f"👥 Players: {player_text}\n"
        f"📊 Usage: `{res_usage}`\n"
    )
    return status_msg

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_online_players_list():
    raw = rcon_command("list")
    # Clean raw output first
    clean_raw = strip_ansi(raw)
    
    if ":" in clean_raw:
        parts = clean_raw.split(":", 1)
        names = parts[1].strip()
        if not names:
            return []
        # Filter out empty strings and clean whitespace
        return [n.strip() for n in names.split(",") if n.strip()]
    return []

def get_online_players_msg():
    players = get_online_players_list()
    if not players:
        return "👥 *Online Players:*\n_No players online._", None
    
    msg = f"👥 *Online Players ({len(players)}):*\nSelect a player to manage:"
    
    # Build keyboard
    keyboard = {"inline_keyboard": []}
    row = []
    for p in players:
        row.append({"text": f"👤 {p}", "callback_data": f"manage:{p}"})
        if len(row) == 2:
           keyboard["inline_keyboard"].append(row)
           row = []
    if row:
        keyboard["inline_keyboard"].append(row)
        
    keyboard["inline_keyboard"].append([{"text": "🔄 Refresh", "callback_data": "online"}])
    return msg, keyboard

def get_player_action_keyboard(player, viewer_id):
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🎮 Survival", "callback_data": f"gm:survival:{player}"},
                {"text": "🎮 Creative", "callback_data": f"gm:creative:{player}"},
                {"text": "👻 Spectator", "callback_data": f"gm:spectator:{player}"}
            ]
        ]
    }
    
    # Owner Only buttons are visible to all but restricted in callback
    keyboard["inline_keyboard"].append([
        {"text": "⚡ Give OP", "callback_data": f"op:{player}"},
        {"text": "🔻 Remove OP", "callback_data": f"deop:{player}"}
    ])
        
    keyboard["inline_keyboard"].append([
        {"text": "🔨 Ban", "callback_data": f"ban:{player}"},
        {"text": "🔓 Unban", "callback_data": f"unban:{player}"}
    ])
    keyboard["inline_keyboard"].append([
         {"text": "🥾 Kick", "callback_data": f"kick:{player}"}
    ])
    keyboard["inline_keyboard"].append([
        {"text": "🔙 Back to Players", "callback_data": "online"}
    ])
    return keyboard

def get_whitelist():
    raw = rcon_command("whitelist list")
    clean_raw = strip_ansi(raw)
    if ":" in clean_raw:
        names = clean_raw.split(":", 1)[1].strip()
        if not names:
             return "📭 *Whitelist is empty.*\nUse `/add <name>` to add players."
        formatted_names = ", ".join([f"`{n.strip()}`" for n in names.split(",") if n.strip()])
        return f"📜 *Whitelisted Players:*\n{formatted_names}"
    return raw

def send_request(method, payload, timeout=10):
    url = BASE_URL + method
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        return resp.json()
    except Exception as e:
        print(f"Request error {method}: {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    send_request("sendMessage", payload)

def broadcast_message(text, reply_markup=None):
    for admin_id in ALLOWED_CHAT_IDS:
        send_message(admin_id, text, reply_markup)

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    send_request("editMessageText", payload)

def answer_callback(callback_id, text):
    send_request("answerCallbackQuery", {"callback_query_id": callback_id, "text": text}, timeout=5)

def get_main_keyboard():
    chat_icon = "🟢" if chat_mode_enabled else "🔴"
    chat_text = "Chat ON" if chat_mode_enabled else "Chat OFF"

    return {
        "inline_keyboard": [
            [
                {"text": "⚡ Start", "callback_data": "start_server"},
                {"text": "🔄 Restart", "callback_data": "restart_server"},
                {"text": "🛑 Stop", "callback_data": "stop_server"}
            ],
            [
                {"text": "🔄 Refresh", "callback_data": "refresh"},
                {"text": "👥 Online", "callback_data": "online"}
            ],
            [
                {"text": "⚙️ Settings", "callback_data": "menu_settings"},
                {"text": "📜 Whitelist", "callback_data": "wl_list"}
            ],
            [
                {"text": "🔒 Lock Server", "callback_data": "wl_on"},
                {"text": "🔓 Unlock Server", "callback_data": "wl_off"}
            ],
            [
                {"text": "📢 Broadcast", "callback_data": "broadcast_mode"},
                 {"text": "📦 Backup", "callback_data": "trigger_backup"}
            ],
            [
                 {"text": f"{chat_icon} {chat_text}", "callback_data": "toggle_chat"},
                 {"text": "🏆 Top Playtime", "callback_data": "show_top"}
            ],
            [
                 {"text": "ℹ️ Help / Guide", "callback_data": "show_help"},
                 {"text": "📋 Copy IP", "callback_data": "get_ip"}
            ]
        ]
    }

def get_public_ip():
    try:
        # Try to get from environment first
        env_ip = os.getenv("SERVER_IP")
        if env_ip:
            return env_ip

        # Fallback to external service
        ip = subprocess.check_output(["curl", "-s", "ifconfig.me"], timeout=5).decode().strip()
        return ip
    except:
        return "Unknown IP"

def get_settings_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "☀️ Day", "callback_data": "set_day"},
                {"text": "🌙 Night", "callback_data": "set_night"},
                {"text": "🌧️ Rain", "callback_data": "set_rain"},
                {"text": "☀️ Clear", "callback_data": "set_clear"}
            ],
            [
                {"text": "👶 Easy", "callback_data": "set_diff:easy"},
                {"text": "😐 Normal", "callback_data": "set_diff:normal"},
                {"text": "💀 Hard", "callback_data": "set_diff:hard"}
            ],
            [
                {"text": "🟢 KeepInv", "callback_data": "keepinv_on"},
                {"text": "🔘 KeepInv", "callback_data": "keepinv_off"}
            ],
            [
                {"text": "🔧 Properties (PvP/Flight...)", "callback_data": "menu_properties"}
            ],
            [
                {"text": "BACK TO MAIN", "callback_data": "menu_main"}
            ]
        ]
    }

def read_property(key):
    try:
        with open(PROPERTIES_FILE, "r") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.strip().split("=")[1]
    except:
        return "N/A"
    return "N/A"

def update_property(key, value):
    try:
        lines = []
        with open(PROPERTIES_FILE, "r") as f:
            lines = f.readlines()
        
        with open(PROPERTIES_FILE, "w") as f:
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                else:
                    f.write(line)
    except Exception as e:
        print(f"Error updating property: {e}")

def get_properties_keyboard():
    # Read current values
    pvp = "🟢" if read_property("pvp") == "true" else "🔴"
    flight = "🟢" if read_property("allow-flight") == "true" else "🔴"
    nether = "🟢" if read_property("allow-nether") == "true" else "🔴"
    
    max_p = read_property("max-players")
    view_d = read_property("view-distance")
    
    return {
        "inline_keyboard": [
            [
                {"text": f"⚔️ PvP: {pvp}", "callback_data": "prop_toggle:pvp"},
                {"text": f"🕊️ Flight: {flight}", "callback_data": "prop_toggle:allow-flight"}
            ],
            [
                {"text": f" Nether: {nether}", "callback_data": "prop_toggle:allow-nether"}
            ],
            [
                {"text": f"👥 Max: {max_p}", "callback_data": "ignore"},
                {"text": "10", "callback_data": "prop_set:max-players:10"},
                {"text": "20", "callback_data": "prop_set:max-players:20"},
                {"text": "50", "callback_data": "prop_set:max-players:50"}
            ],
            [
                {"text": f"👀 View: {view_d}", "callback_data": "ignore"},
                {"text": "6", "callback_data": "prop_set:view-distance:6"},
                {"text": "10", "callback_data": "prop_set:view-distance:10"},
                {"text": "16", "callback_data": "prop_set:view-distance:16"}
            ],
            [
                {"text": "⚠️ Apply Changes (Restart)", "callback_data": "restart_server"}
            ],
            [
                {"text": "🔙 Back", "callback_data": "menu_settings"}
            ]
        ]
    }

def monitor_logs():
    print("Log monitor started...")
    while True:
        try:
            # Check if container is running first
            try:
                state = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME], timeout=5).strip().decode()
                if state != "true":
                    time.sleep(10) # Sleep if stopped
                    continue
            except:
                time.sleep(10)
                continue

            process = subprocess.Popen(
                ["docker", "compose", "-f", "/home/fawi/minecraft/docker-compose.yml", "logs", "-f", "--tail=0", CONTAINER_NAME],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                    
                line = line.strip()
                # Detect JOIN
                if "joined the game" in line:
                    match = re.search(r": (.*?) joined the game", line)
                    if match:
                        player = match.group(1)
                        msg = f"🟢 *Player Joined!*\n👤 `{player}`"
                        broadcast_message(msg)

                # Detect CHAT (Relay to Telegram)
                if "]: <" in line and "> " in line:
                    match = re.search(r": <(.*?)> (.*)", line)
                    if match:
                        player = match.group(1)
                        message = match.group(2)
                        msg = f"💬 *{player}:* {message}"
                        broadcast_message(msg)
                
                # Detect DEATH (Funny Broadcast)
                death_keywords = ["slain by", "shot by", "blew up", "burned to death", "fell from", "drowned", "starved", "suffocated", "withered", "died", "killed by", "hit the ground"]
                if any(k in line for k in death_keywords) and "]: " in line:
                     msg_part = line.split("]: ", 1)[1].strip()
                     if not msg_part.startswith("<"): 
                         title_payload = {"text": msg_part, "color": "yellow", "bold": True}
                         subtitle_payload = {"text": "RIP ☠️", "color": "red"}
                         rcon_command(["title", "@a", "title", json.dumps(title_payload)])
                         rcon_command(["title", "@a", "subtitle", json.dumps(subtitle_payload)])
                         broadcast_message(f"💀 *Death:* {msg_part}")

                # Detect BLOCKED (Whitelist)
                if "You are not white-listed" in line and "Disconnecting" in line:
                    match = re.search(r"Disconnecting (.*?) \(", line)
                    if match:
                        player = match.group(1)
                        kb = {
                            "inline_keyboard": [[
                                {"text": f"✅ Add {player}", "callback_data": f"quick_add:{player}"}
                            ]]
                        }
                        msg = f"🚨 *Blocked Connection!*\n👤 `{player}` tried to join."
                        broadcast_message(msg, kb)
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(5)

def get_playtime_top():
    try:
        stats_dir = "/data/world/stats/" # Updated relative to container path/mount usually
        # But script runs on host. So it needs FULL HOST PATHS.
        # User should configure this in ENV if path differs.
        # For now, defaulting to standard path or env
        stats_dir = os.path.dirname(PROPERTIES_FILE) + "/world/stats/"
        usercache_file = os.path.dirname(PROPERTIES_FILE) + "/usercache.json"
        
        # Load usercache for UUID -> Name
        uuid_map = {}
        if os.path.exists(usercache_file):
            with open(usercache_file, "r") as f:
                data = json.load(f)
                for entry in data:
                    uuid_map[entry["uuid"]] = entry["name"]
        
        # Parse stats
        players = []
        if os.path.exists(stats_dir):
            for filename in os.listdir(stats_dir):
                if filename.endswith(".json"):
                    try:
                        uuid = filename.replace(".json", "")
                        with open(os.path.join(stats_dir, filename), "r") as f:
                            stat_data = json.load(f)
                            # Playtime is in ticks (20 ticks = 1 sec)
                            ticks = stat_data.get("stats", {}).get("minecraft:custom", {}).get("minecraft:play_time", 0)
                            if ticks > 0:
                                name = uuid_map.get(uuid, uuid[:8])
                                hours = ticks / 20 / 3600
                                players.append((name, hours))
                    except:
                        pass
        
        # Sort and format
        players.sort(key=lambda x: x[1], reverse=True)
        top_list = players[:5]
        
        msg = "🏆 *Top Playtime:*\n"
        for i, (name, hours) in enumerate(top_list, 1):
            msg += f"{i}. 👤 *{name}:* `{hours:.1f} hours`\n"
            
        return msg if top_list else "No stats available."
    except Exception as e:
        return f"Error calculating stats: {e}"

def handle_callback(cb):
    global chat_mode_enabled
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    data = cb["data"]
    cb_id = cb["id"]
    
    if chat_id not in ALLOWED_CHAT_IDS:
        answer_callback(cb_id, "Unauthorized")
        return

    text_response = "Done!"
    
    if data == "toggle_chat":
        chat_mode_enabled = not chat_mode_enabled
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        state_text = "Enabled" if chat_mode_enabled else "Disabled"
        answer_callback(cb_id, f"Chat {state_text}")
        return

    if data == "show_top":
        msg = get_playtime_top()
        send_message(chat_id, msg)
        answer_callback(cb_id, "🏆 Top Players")
        return

    if data == "show_help":
        help_text = (
            "ℹ️ *Control Panel Guide:*\n\n"
            "⚡ *Start/Stop/Restart:* Power controls.\n"
            "------------------\n"
            "⚙️ *Settings:* Time ☀️, Weather 🌧️, Difficulty 💀.\n"
            " *Properties:* Edit PvP, Flight, Max Players (Req. Restart).\n"
            "------------------\n"
            " *Players:* Click 'Online' to Manage Players:\n"
            "   • 🎮 Gamemode (Survival/Creative/Spectator)\n"
            "   • 🔨 Ban / Unban\n"
            "   • ⚡ OP / De-OP (Owner Only 🔒)\n"
            "   • 🥾 Kick\n"
            "------------------\n"
            "🔒 *Lock:* Whitelist ON (Only trusted).\n"
            "📜 *Whitelist:* Show allowed players.\n"
            "------------------\n"
            "📦 *Backup:* Send world copy to Telegram.\n"
            "📢 *Broadcast:* Send big title message.\n"
            "💻 */cmd:* Run console commands (Owner).\n"
            "🏆 *Playtime:* /top for ranks."
        )
        answer_callback(cb_id, "Help Guide")
        send_message(chat_id, help_text)
        return

    if data == "show_guide":
        answer_callback(cb_id, "Commands Guide")
        send_message(chat_id, GUIDE_TEXT)
        return

    if data == "get_ip":
        ip = get_public_ip()
        send_message(chat_id, f"🌐 *Server IP:*\n`{ip}`")
        answer_callback(cb_id, "Sent IP")
        return
    
    # Settings Menu Handlers
    if data == "menu_settings":
        edit_message(chat_id, msg_id, "⚙️ *Server Settings:*", get_settings_keyboard())
        return
        
    if data == "menu_main":
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        return
        
    if data == "set_day":
        rcon_command("time set day")
        answer_callback(cb_id, "Time set to Day ☀️")
        return
    if data == "set_night":
        rcon_command("time set night")
        answer_callback(cb_id, "Time set to Night 🌙")
        return
    if data == "set_rain":
        rcon_command("weather rain")
        answer_callback(cb_id, "Weather set to Rain 🌧️")
        return
    if data == "set_clear":
        rcon_command("weather clear")
        answer_callback(cb_id, "Weather set to Clear ☀️")
        return
        
    # Property Editor Handlers
    if data == "menu_properties":
        edit_message(chat_id, msg_id, "🔧 *Server Properties (Req. Restart):*", get_properties_keyboard())
        return

    if data.startswith("prop_toggle:"):
        key = data.split(":")[1]
        current = read_property(key)
        new_val = "false" if current == "true" else "true"
        update_property(key, new_val)
        answer_callback(cb_id, f"Set {key} to {new_val} 📝")
        edit_message(chat_id, msg_id, "🔧 *Server Properties (Req. Restart):*", get_properties_keyboard())
        return

    if data.startswith("prop_set:"):
        _, key, val = data.split(":")
        update_property(key, val)
        answer_callback(cb_id, f"Set {key} to {val} 📝")
        edit_message(chat_id, msg_id, "🔧 *Server Properties (Req. Restart):*", get_properties_keyboard())
        return
        
    if data.startswith("set_diff:"):
        diff = data.split(":")[1]
        rcon_command(f"difficulty {diff}")
        answer_callback(cb_id, f"Difficulty set to {diff.upper()} 💀")
        return
 
    if data == "keepinv_on":
        rcon_command("gamerule keepInventory true")
        answer_callback(cb_id, "KeepInventory ON 🎒")
        return
    if data == "keepinv_off":
        rcon_command("gamerule keepInventory false")
        answer_callback(cb_id, "KeepInventory OFF 🔻")
        return

    if data.startswith("quick_add:"):
        player_name = data.split(":")[1]
        rcon_command(f"whitelist add {player_name}")
        rcon_command("whitelist reload")
        edit_message(chat_id, msg_id, f"✅ *Added {player_name} to whitelist!*\nThey can join now.")
        answer_callback(cb_id, f"Added {player_name}")
        return

    if data == "refresh":
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        text_response = "Refreshed"

    elif data == "start_server":
        msg = start_server()
        answer_callback(cb_id, msg)
        time.sleep(2)
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        return

    elif data == "restart_server":
        edit_message(chat_id, msg_id, "⏳ *Restarting Server...*\nPlease wait (~60s).", get_main_keyboard())
        answer_callback(cb_id, "Restarting...")

        msg = restart_server()
        time.sleep(5) # Wait for restart

        status = get_server_status()
        edit_message(chat_id, msg_id, f"✅ *{msg}*\n\n{status}\n\n{COMMANDS_HELP}", get_main_keyboard())
        return

    elif data == "stop_server":
        kb = {
            "inline_keyboard": [[
                {"text": "✅ Yes, Stop", "callback_data": "confirm_stop"},
                {"text": "❌ Cancel", "callback_data": "cancel_stop"}
            ]]
        }
        edit_message(
            chat_id,
            msg_id,
            "⚠️ *Are you sure you want to STOP the server?*\n"
            "This will kick all players.",
            kb
        )
        answer_callback(cb_id, "Confirmation needed")
        return

    elif data == "confirm_stop":
        msg = stop_server()
        answer_callback(cb_id, msg)
        time.sleep(2)
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        return

    elif data == "cancel_stop":
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        answer_callback(cb_id, "Cancelled")
        return

    elif data == "trigger_backup":
        edit_message(chat_id, msg_id, "⏳ *Starting Backup...*", get_main_keyboard())
        answer_callback(cb_id, "Backup started!")

        msg = run_backup()
        edit_message(chat_id, msg_id, f"{msg}\n\n{get_server_status()}\n\n{COMMANDS_HELP}", get_main_keyboard())
        return
        
    elif data == "online":
        msg, kb = get_online_players_msg()
        if kb:
            try:
                edit_message(chat_id, msg_id, msg, kb)
            except:
                send_message(chat_id, msg, kb)
        else:
             send_message(chat_id, msg)
        return

    # Player Management Handlers
    if data.startswith("manage:"):
        player = data.split(":")[1]
        edit_message(chat_id, msg_id, f"👤 Managing *{player}*:", get_player_action_keyboard(player, chat_id))
        return
        
    if data.startswith("gm:"):
        _, mode, player = data.split(":")
        rcon_command(f"gamemode {mode} {player}")
        answer_callback(cb_id, f"Set {player} to {mode} 🎮")
        return
        
    if data.startswith("op:"):
        if chat_id != OWNER_ID:
            answer_callback(cb_id, "⛔ Only Owner can give OP!")
            return
        player = data.split(":")[1]
        rcon_command(f"op {player}")
        answer_callback(cb_id, f"{player} is now OP ⚡")
        return

    if data.startswith("deop:"):
        if chat_id != OWNER_ID:
            answer_callback(cb_id, "⛔ Only Owner can remove OP!")
            return
        player = data.split(":")[1]
        rcon_command(f"deop {player}")
        answer_callback(cb_id, f"{player} is no longer OP 🔻")
        return
        
    if data.startswith("ban:"):
        player = data.split(":")[1]
        rcon_command(f"ban {player}")
        answer_callback(cb_id, f"{player} BANNED 🔨")
        edit_message(chat_id, msg_id, f"🔨 *{player}* has been BANNED.", get_player_action_keyboard(player, chat_id))
        return

    if data.startswith("unban:"):
        player = data.split(":")[1]
        rcon_command(f"pardon {player}")
        answer_callback(cb_id, f"{player} UNBANNED 🔓")
        edit_message(chat_id, msg_id, f"🔓 *{player}* has been UNBANNED.", get_player_action_keyboard(player, chat_id))
        return
        
    if data.startswith("kick:"):
        player = data.split(":")[1]
        rcon_command(f"kick {player}")
        answer_callback(cb_id, f"{player} Kicked 🥾")
        return
        
    elif data == "wl_list":
        msg = get_whitelist()
        send_message(chat_id, msg)

    elif data == "wl_on":
        rcon_command("whitelist on")
        rcon_command("whitelist reload")
        time.sleep(1) # Wait for file update
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        answer_callback(cb_id, "Locked")
        return

    elif data == "wl_off":
        rcon_command("whitelist off")
        time.sleep(1) # Wait for file update
        status = get_server_status()
        edit_message(chat_id, msg_id, status + "\n" + COMMANDS_HELP, get_main_keyboard())
        answer_callback(cb_id, "Unlocked")
        return
        
    elif data == "broadcast_mode":
        pending_broadcast[chat_id] = True
        send_message(chat_id, "📢 *Broadcast Mode ON*\nType your message now to send it as a screen title to all players.")
        answer_callback(cb_id, "Waiting for input...")
        return

    answer_callback(cb_id, text_response)

def handle_text(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    user_name = msg.get("from", {}).get("first_name", "Admin")
    
    if chat_id not in ALLOWED_CHAT_IDS:
        return
        
    # Check for pending broadcast
    if pending_broadcast.get(chat_id):
        # Send title command
        title_payload = {"text": text, "color": "gold", "bold": True}
        subtitle_payload = {"text": f"From {user_name}", "color": "gray"}

        # Title command: title @a title {"text":"MESSAGE", "color":"gold"}
        rcon_command(["title", "@a", "title", json.dumps(title_payload)])
        rcon_command(["title", "@a", "subtitle", json.dumps(subtitle_payload)])
        
        # Also play sound
        rcon_command("execute at @a run playsound minecraft:entity.experience_orb.pickup master @p ~ ~ ~ 1 1")
        
        send_message(chat_id, f"✅ *Broadcast Sent:*\n{text}")
        pending_broadcast[chat_id] = False
        return

    # Commands
    if text.startswith("/"):
        if text.startswith("/start") or text.startswith("/help") or text.startswith("/panel"):
            status = get_server_status()
            send_message(chat_id, f"👋 *Pico Minecraft Bot*\n\n{status}\n\n{COMMANDS_HELP}", get_main_keyboard())
            return
            
            send_message(chat_id, msg)
            return

        if text.startswith("/cmd "):
            if chat_id != OWNER_ID:
                send_message(chat_id, "⛔ Only Owner can use console commands!")
                return
            
            cmd = text[5:].strip()
            if not cmd:
                send_message(chat_id, "⚠️ Usage: `/cmd <command>`")
                return
                
            output = rcon_command(cmd)
            clean_out = strip_ansi(output)
            if not clean_out.strip():
                clean_out = "✅ Command executed (No output)"
                
            send_message(chat_id, f"💻 *Console Output:*\n`{clean_out}`")
            return

        parts = text.split()
        cmd = parts[0].lower()
        
        if cmd == "/add" and len(parts) > 1:
            player = parts[1]
            out = rcon_command(f"whitelist add {player}")
            rcon_command("whitelist reload")
            send_message(chat_id, f"✅ *Added:* {player}\n`{out}`")
            
        elif cmd == "/remove" and len(parts) > 1:
            player = parts[1]
            out = rcon_command(f"whitelist remove {player}")
            rcon_command("whitelist reload")
            send_message(chat_id, f"❌ *Removed:* {player}\n`{out}`")
            
        elif cmd == "/kick" and len(parts) > 1:
            player = parts[1]
            out = rcon_command(f"kick {player}")
            send_message(chat_id, f"🥾 *Kicked:* {player}\n`{out}`")
    
    else:
        # Chat Relay: Send text to game (Only if chat mode is ON)
        if chat_mode_enabled:
            tellraw_payload = [
                "",
                {"text": f"[{user_name}@Telegram]: ", "color": "aqua"},
                {"text": text, "color": "white"}
            ]
            rcon_command(["tellraw", "@a", json.dumps(tellraw_payload)])

def monitor_resources():
    print("Resource monitor started...")
    last_alert_time = 0
    ALERT_COOLDOWN = 1800 # 30 minutes

    while True:
        try:
            # Check RAM Usage
            try:
                # Get percentage directly: "50.29%"
                stats = subprocess.check_output(
                    ["docker", "stats", CONTAINER_NAME, "--no-stream", "--format", "{{.MemPerc}}"],
                    timeout=5
                ).strip().decode()
                
                # Parse percentage
                mem_perc = float(stats.replace("%", ""))
                
                if mem_perc > 90.0:
                    current_time = time.time()
                    if current_time - last_alert_time > ALERT_COOLDOWN:
                        msg = (
                            f"⚠️ *High RAM Usage Alert!* 📊\n"
                            f"Usage: `{mem_perc}%`\n"
                            f"The server might lag. Consider restarting soon."
                        )
                        broadcast_message(msg)
                        last_alert_time = current_time
                        
            except Exception as e:
                # Container might be stopped or starting
                pass
                
        except Exception as e:
            print(f"Resource Monitor error: {e}")
        
        time.sleep(3600) # Check every hour

def main():
    print("Bot Premium V9 (Chat Toggle + Resource Monitor) started...")
    
    # Log Monitor Thread
    t_log = threading.Thread(target=monitor_logs, daemon=True)
    t_log.start()
    
    # Resource Monitor Thread
    t_res = threading.Thread(target=monitor_resources, daemon=True)
    t_res.start()
    
    last_update_id = None
    
    while True:
        try:
            # Long polling: 30s timeout in payload, 40s network timeout
            updates = send_request("getUpdates", {"offset": last_update_id, "timeout": 30}, timeout=40)
            if updates and "result" in updates:
                for u in updates["result"]:
                    last_update_id = u["update_id"] + 1
                    
                    if "message" in u:
                        handle_text(u["message"])
                    elif "callback_query" in u:
                        handle_callback(u["callback_query"])
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
