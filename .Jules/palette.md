## 2024-04-12 - [Stop Server Confirmation]
**Learning:** Destructive actions like stopping a server must have a confirmation step to prevent accidental clicks. This is especially true on mobile interfaces where touch targets are small and accidental taps are common.
**Action:** Always add a confirmation step for critical actions like stopping a server or banning a player.

## 2024-04-12 - [UX Polish Pack]
**Learning:**
*   **Loading States:** For long-running operations (Backups/Restarts), showing an immediate "⏳ Processing..." message prevents user confusion about whether the command was received.
*   **Visual Consistency:** Using standard emojis (🟢/🔴) for toggles makes state clear at a glance, better than text labels like "ON/OFF".
*   **Empty States:** An empty list (like Whitelist) is an opportunity to guide the user on what to do next (e.g., "Add players via /add").
**Action:** Implement immediate feedback for all async commands and use consistent visual indicators for boolean states.
