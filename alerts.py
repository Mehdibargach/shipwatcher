"""
Alerts — send email notifications.
- Alert email: when checks fail (immediate)
- Daily digest: summary every morning (all checks, pass or fail)
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


async def _send_email(subject: str, html_body: str):
    """Send an email via Resend API."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email")
        return
    if not ALERT_EMAIL:
        logger.warning("ALERT_EMAIL not set — skipping email")
        return

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
            logger.info(f"Email sent to {ALERT_EMAIL}: {subject}")
        else:
            logger.error(f"Resend API error: {resp.status_code} — {resp.text}")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def _build_alert_body(failures: list[CheckResult], total: int) -> str:
    """Build HTML body for alert emails (failures only)."""
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


def _build_digest_body(all_results: list[CheckResult]) -> str:
    """Build HTML body for daily digest (all checks)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(1 for r in all_results if r.success)
    failed = len(all_results) - passed
    all_good = failed == 0

    # Status banner
    if all_good:
        banner_color = "#22c55e"
        banner_text = f"All good — {passed}/{len(all_results)} checks passed"
        emoji = "✅"
    else:
        banner_color = "#ef4444"
        banner_text = f"{failed} check(s) failed out of {len(all_results)}"
        emoji = "🔴"

    # Build rows for ALL projects
    rows = ""
    for r in all_results:
        if r.success:
            status = f'<span style="color: #22c55e;">✓ {r.latency_ms}ms</span>'
        else:
            status = f'<span style="color: #ef4444;">✗ {r.error}</span>'

        rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #333;">{r.project_name}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #333;">{r.check_type}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #333;">{status}</td>
        </tr>"""

    return f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #e5e5e5; padding: 24px; border-radius: 8px;">
        <h1 style="font-size: 20px; margin: 0 0 4px 0;">ShipWatcher Daily Digest</h1>
        <p style="color: #888; margin: 0 0 20px 0;">{now}</p>

        <div style="background: #1a1a1a; border-radius: 6px; padding: 16px; margin-bottom: 20px;">
            <span style="font-size: 24px; color: {banner_color}; font-weight: bold;">{emoji}</span>
            <span style="color: #e5e5e5;"> {banner_text}</span>
        </div>

        <table style="width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 6px;">
            <thead>
                <tr style="border-bottom: 2px solid #333;">
                    <th style="padding: 10px 12px; text-align: left; color: #888;">Project</th>
                    <th style="padding: 10px 12px; text-align: left; color: #888;">Check</th>
                    <th style="padding: 10px 12px; text-align: left; color: #888;">Status</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        <p style="color: #888; font-size: 13px; margin-top: 20px;">
            <a href="https://shipwatcher.onrender.com" style="color: #6366f1;">Open dashboard</a>
        </p>
    </div>
    """


async def send_alert(failures: list[CheckResult], total: int):
    """Send an alert email (failures only)."""
    subject = f"🔴 ShipWatcher: {len(failures)} check(s) failed"
    html_body = _build_alert_body(failures, total)
    await _send_email(subject, html_body)


async def send_daily_digest(all_results: list[CheckResult]):
    """Send a daily digest email (all checks, pass or fail)."""
    passed = sum(1 for r in all_results if r.success)
    failed = len(all_results) - passed

    if failed == 0:
        subject = f"✅ ShipWatcher: {passed}/{len(all_results)} checks passed"
    else:
        subject = f"🔴 ShipWatcher: {failed}/{len(all_results)} checks failed"

    html_body = _build_digest_body(all_results)
    await _send_email(subject, html_body)
