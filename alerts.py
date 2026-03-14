"""
Alerts — send email notifications when checks fail.
Uses Resend API (100 free emails/day).
"""

import os
import logging
from datetime import datetime, timezone

import httpx

from checker import CheckResult

logger = logging.getLogger("shipwatcher.alerts")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "ShipWatcher <onboarding@resend.dev>")


def _build_email_body(failures: list[CheckResult], total: int) -> str:
    """Build a clean HTML email body."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = total - len(failures)

    rows = ""
    for f in failures:
        rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #333;">{f.project_name}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #333;">{f.check_type}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #333; color: #ef4444;">{f.error}</td>
        </tr>"""

    return f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #e5e5e5; padding: 24px; border-radius: 8px;">
        <h1 style="font-size: 20px; margin: 0 0 4px 0;">ShipWatcher Alert</h1>
        <p style="color: #888; margin: 0 0 20px 0;">{now}</p>

        <div style="background: #1a1a1a; border-radius: 6px; padding: 16px; margin-bottom: 20px;">
            <span style="font-size: 24px; color: #ef4444; font-weight: bold;">{len(failures)}</span>
            <span style="color: #888;"> check(s) failed out of {total}</span>
        </div>

        <table style="width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 6px;">
            <thead>
                <tr style="border-bottom: 2px solid #333;">
                    <th style="padding: 10px 12px; text-align: left; color: #888;">Project</th>
                    <th style="padding: 10px 12px; text-align: left; color: #888;">Check</th>
                    <th style="padding: 10px 12px; text-align: left; color: #888;">Error</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        <p style="color: #888; font-size: 13px; margin-top: 20px;">
            {passed}/{total} checks passed.
            <a href="https://shipwatcher.onrender.com" style="color: #6366f1;">Open dashboard</a>
        </p>
    </div>
    """


async def send_alert(failures: list[CheckResult], total: int):
    """Send an alert email via Resend."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email alert")
        return

    if not ALERT_EMAIL:
        logger.warning("ALERT_EMAIL not set — skipping email alert")
        return

    subject = f"🔴 ShipWatcher: {len(failures)} check(s) failed"
    html_body = _build_email_body(failures, total)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": FROM_EMAIL,
                    "to": [ALERT_EMAIL],
                    "subject": subject,
                    "html": html_body,
                },
                timeout=10,
            )

        if resp.status_code == 200:
            logger.info(f"Alert email sent to {ALERT_EMAIL}")
        else:
            logger.error(f"Resend API error: {resp.status_code} — {resp.text}")

    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
