"""Command-line entrypoint the ge-content-queue skill calls."""
from __future__ import annotations

import argparse
import sys

from gevideo import queue


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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
