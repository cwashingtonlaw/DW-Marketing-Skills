"""Command-line entrypoint the ge-content-queue skill calls."""
from __future__ import annotations

import argparse
import sys
from datetime import date, time
from pathlib import Path
from zoneinfo import ZoneInfo

from gevideo import queue
from gevideo import heygen
from gevideo import youtube
from gevideo.config import load_config
from gevideo.secrets import get_secret
from gevideo.slots import compute_publish_at, to_rfc3339


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gevideo")
    parser.add_argument("--data-dir", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("backlog-add")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--notes", default="")

    p_prom = sub.add_parser("backlog-promote")
    p_prom.add_argument("--id", required=True)

    sub.add_parser("backlog-list")
    sub.add_parser("queue-status")

    p_app = sub.add_parser("approve")
    p_app.add_argument("--date", required=True)

    p_rej = sub.add_parser("reject")
    p_rej.add_argument("--date", required=True)

    p_gen = sub.add_parser("heygen-generate")
    p_gen.add_argument("--date", required=True)
    p_gen.add_argument("--script-file", required=True)
    p_gen.add_argument("--config", required=True)

    _yt_token = str(Path.home() / ".config/ge-video/youtube_token.json")
    _yt_secret = str(Path.home() / ".config/ge-video/youtube_client_secret.json")
    p_sched = sub.add_parser("youtube-schedule")
    p_sched.add_argument("--date", required=True)
    p_sched.add_argument("--config", required=True)
    p_sched.add_argument("--publish-from", default=None)
    p_sched.add_argument("--token-file", default=_yt_token)
    p_sched.add_argument("--client-secret", default=_yt_secret)

    p_daily = sub.add_parser("daily-start")
    p_daily.add_argument("--date", default=None)

    args = parser.parse_args(argv)
    data_dir = args.data_dir

    if args.command == "backlog-add":
        backlog = queue.load_backlog(data_dir)
        item = queue.add_topic(backlog, title=args.title, notes=args.notes)
        queue.save_backlog(data_dir, backlog)
        print(f"added topic {item['id']}: {item['title']} (proposed)")
        return 0

    if args.command == "backlog-promote":
        backlog = queue.load_backlog(data_dir)
        try:
            queue.promote_topic(backlog, args.id)
        except KeyError:
            print(f"no topic with id {args.id}", file=sys.stderr)
            return 1
        queue.save_backlog(data_dir, backlog)
        print(f"promoted {args.id} -> ready")
        return 0

    if args.command == "backlog-list":
        for item in queue.load_backlog(data_dir):
            print(f"{item['id']}  {item['status']:9}  {item['title']}")
        return 0

    if args.command == "queue-status":
        backlog = queue.load_backlog(data_dir)
        print(f"ready topics: {queue.count_ready(backlog)}")
        return 0

    if args.command in ("approve", "reject"):
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        target = "approved" if args.command == "approve" else "hold"
        try:
            queue.set_status(item, target)
        except queue.InvalidTransition as exc:
            print(f"cannot {args.command}: {exc}", file=sys.stderr)
            return 1
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> {target}")
        return 0

    if args.command == "heygen-generate":
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        cfg = load_config(args.config)
        script = Path(args.script_file).read_text()
        api_key = get_secret("HEYGEN_API_KEY")
        client = heygen.HeyGenClient(api_key)
        dest = Path(data_dir) / "pipeline" / args.date / "video.mp4"
        result = heygen.generate_to_file(
            client, script=script, avatar_id=cfg.avatar_id,
            voice_id=cfg.voice_id, title=item["title"], dest_path=dest)
        item["video_path"] = str(dest)
        item["metadata"]["heygen_video_id"] = result["video_id"]
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> rendered {result['video_id']} -> {dest}")
        return 0

    if args.command == "youtube-schedule":
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        if item["status"] != "approved":
            print(f"item {args.date} is {item['status']}, not approved",
                  file=sys.stderr)
            return 1
        if not item.get("video_path"):
            print(f"item {args.date} has no video_path", file=sys.stderr)
            return 1

        cfg = load_config(args.config)
        used = queue.scheduled_publish_dates(data_dir)
        from_date = (date.fromisoformat(args.publish_from)
                     if args.publish_from else date.today())
        hh, mm = (int(x) for x in cfg.publish_time.split(":"))
        slot = compute_publish_at(used, from_date, time(hh, mm), cfg.timezone)
        publish_at = to_rfc3339(slot)
        publish_date = slot.astimezone(ZoneInfo(cfg.timezone)).date().isoformat()

        meta = item.get("metadata", {})
        uploader = youtube.make_default_uploader(
            token_file=args.token_file, client_secret=args.client_secret)
        video_id = youtube.schedule_upload(
            uploader, file_path=item["video_path"],
            title=meta.get("title", item["title"]),
            description=meta.get("description", ""),
            tags=meta.get("tags", []),
            publish_at=publish_at,
            category_id=meta.get("category_id", youtube.DEFAULT_CATEGORY_ID))

        queue.set_status(item, "scheduled")
        item["youtube_video_id"] = video_id
        item["publish_at"] = publish_at
        item["publish_date"] = publish_date
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> scheduled {video_id} to publish {publish_at}")
        return 0

    if args.command == "daily-start":
        target_date = args.date or date.today().isoformat()
        existing = queue.load_pipeline_item(data_dir, target_date)
        if existing is not None:
            print(f"{target_date} already started: {existing['title']} "
                  f"({existing['status']})")
            return 0
        backlog = queue.load_backlog(data_dir)
        topic = queue.consume_next_ready(backlog)
        if topic is None:
            print("backlog empty: no ready topic. Run ge-ideate to refill.",
                  file=sys.stderr)
            return 2
        queue.save_backlog(data_dir, backlog)
        item = queue.create_pipeline_item(target_date, topic)
        queue.save_pipeline_item(data_dir, item)
        print(f"{target_date} started: {topic['title']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
