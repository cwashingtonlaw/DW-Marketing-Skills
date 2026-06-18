"""Approval-notification message building and Google Chat webhook delivery."""
from __future__ import annotations


def build_approval_message(item: dict) -> dict:
    verdict = item.get("compliance_verdict")
    if isinstance(verdict, dict):
        vtext = verdict.get("verdict", "?")
    else:
        vtext = verdict if verdict else "(none)"

    date = item.get("date", "")
    title = item.get("title", "(untitled)")
    subject = f"[GE Video] Approve {date}: {title}"
    body = "\n".join([
        f"Daily video ready for approval — {date}",
        f"Title: {title}",
        f"Status: {item.get('status')}",
        f"Compliance: {vtext}",
        f"Video: {item.get('video_path')}",
        "",
        'To publish: run "approve today\'s video" (or reject to send to HOLD).',
        "",
        "Manual posts (no tool can automate these): "
        "Facebook personal, Instagram personal, Snapchat.",
    ])
    return {"subject": subject, "body": body}


import json
import urllib.request


class _UrllibPoster:
    def post(self, url: str, payload: dict) -> int:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req) as resp:
            return resp.status


def post_chat_webhook(webhook_url: str, text: str, http=None) -> int:
    http = http or _UrllibPoster()
    return http.post(webhook_url, {"text": text})
