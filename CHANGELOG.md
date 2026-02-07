# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-07

### Added
- 🎮 **Server Control**: Start, Stop, Restart via Telegram buttons.
- 👥 **Player Management**: Whitelist, Ban, Kick, OP, Gamemode control.
- ⚙️ **Server Settings**: Edit Time, Weather, Difficulty, KeepInventory.
- 🔧 **Properties Editor**: Modify `server.properties` (PvP, Flight, etc.).
- 💾 **Backup System**: Create and send world backups to Telegram.
- 📊 **Status Monitoring**: View online players, CPU, RAM usage.
- 💬 **Chat Relay**: Bi-directional Telegram ↔ Minecraft chat.
- 💀 **Death Broadcasts**: Fun death messages in Telegram.
- 🏆 **Top Playtime**: Leaderboard for player activity.
- 🖥️ **Commander Mode**: `/cmd` for raw RCON commands (Owner only).
- 🐳 **Docker Support**: Run bot in a container.
- ⚙️ **Auto-Service**: Interactive setup script with systemd installation.

### Security
- All secrets loaded from environment variables (`.env`).
- No hardcoded tokens or IDs in source code.
