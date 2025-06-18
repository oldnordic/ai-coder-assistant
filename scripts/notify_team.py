"""
notify_team.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

#!/usr/bin/env python3
"""
notify_team.py - Send scan results to Slack or Discord
"""
import sys
import json
import requests
from typing import Dict, Any, Optional
import os

def notify_slack(message: str, webhook_url: Optional[str] = None):
    """Send message to Slack via webhook."""
    webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("Error: SLACK_WEBHOOK_URL environment variable not set")
        return False
    
    payload = {
        "text": message,
        "username": "AI Coder Assistant",
        "icon_emoji": ":robot_face:"
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Message sent to Slack (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Failed to send to Slack: {e}")
        return False

def notify_discord(message: str, webhook_url: Optional[str] = None):
    """Send message to Discord via webhook."""
    webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set")
        return False
    
    payload = {
        "content": message,
        "username": "AI Coder Assistant",
        "avatar_url": "https://github.com/your-repo/ai-coder-assistant/raw/main/icon.png"
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Message sent to Discord (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Failed to send to Discord: {e}")
        return False

def notify_teams(message: str, webhook_url: Optional[str] = None):
    """Send message to Microsoft Teams via webhook."""
    webhook_url = webhook_url or os.getenv('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        print("Error: TEAMS_WEBHOOK_URL environment variable not set")
        return False
    
    # Teams uses a different payload format
    payload = {
        "text": message,
        "title": "AI Coder Assistant",
        "themeColor": "0078D4"  # Microsoft blue
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Message sent to Teams (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Failed to send to Teams: {e}")
        return False

def format_scan_results(results_file: str) -> str:
    """Format scan results for notification."""
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        if not results:
            return "✅ Code scan completed - No issues found!"
        
        total_issues = len(results)
        critical_count = len([r for r in results if r.get('severity') == 'critical'])
        high_count = len([r for r in results if r.get('severity') == 'high'])
        
        message = f"🔍 Code scan completed - Found {total_issues} issues\n"
        message += f"🚨 Critical: {critical_count}\n"
        message += f"⚠️ High: {high_count}\n"
        
        if critical_count > 0:
            message += "\n🚨 **CRITICAL ISSUES:**\n"
            for result in results[:3]:  # Show first 3 critical issues
                if result.get('severity') == 'critical':
                    message += f"• {result.get('file_path', 'Unknown')}:{result.get('line_number', 'Unknown')} - {result.get('description', 'No description')}\n"
        
        return message
        
    except Exception as e:
        return f"❌ Error reading scan results: {e}"

def main():
    if len(sys.argv) < 3:
        print("Usage: notify_team.py <slack|discord|teams> <message|results_file>")
        print("\nExamples:")
        print("  notify_team.py slack 'Hello from AI Coder Assistant!'")
        print("  notify_team.py discord scan_results.json")
        print("  notify_team.py teams scan_results.json")
        print("\nEnvironment variables:")
        print("  SLACK_WEBHOOK_URL - Slack webhook URL")
        print("  DISCORD_WEBHOOK_URL - Discord webhook URL")
        print("  TEAMS_WEBHOOK_URL - Microsoft Teams webhook URL")
        sys.exit(1)
    
    channel = sys.argv[1]
    message_or_file = sys.argv[2]
    
    # Check if it's a file path
    if message_or_file.endswith('.json') and os.path.exists(message_or_file):
        message = format_scan_results(message_or_file)
    else:
        message = message_or_file
    
    success = False
    if channel == 'slack':
        success = notify_slack(message)
    elif channel == 'discord':
        success = notify_discord(message)
    elif channel == 'teams':
        success = notify_teams(message)
    else:
        print(f"Unknown channel: {channel}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 