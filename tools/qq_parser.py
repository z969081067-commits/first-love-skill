#!/usr/bin/env python3
"""QQ 聊天记录解析器."""

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from chat_analysis import (
    analyze_messages,
    build_event,
    parse_timestamp,
    read_text_file,
    write_markdown_report,
)


QQ_MESSAGE_PATTERN = re.compile(r"^(\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\s+(.+?)(?:\((.*?)\))?\s*$")


def parse_qq_text_content(
    content: str,
    target_name: str,
    *,
    source_format: str,
    target_aliases: Optional[str] = None,
    self_name: Optional[str] = None,
) -> list:
    messages = []
    current_msg = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip("\n")
        match = QQ_MESSAGE_PATTERN.match(line)
        if match:
            if current_msg:
                messages.append(current_msg)
            timestamp, sender, _qq_number = match.groups()
            current_msg = {
                "timestamp": parse_timestamp(timestamp),
                "sender": sender.strip(),
                "content": "",
            }
        elif current_msg and line.strip() and not line.startswith("==="):
            if current_msg["content"]:
                current_msg["content"] += "\n"
            current_msg["content"] += line

    if current_msg:
        messages.append(current_msg)

    events = []
    for msg in messages:
        event = build_event(
            msg["timestamp"],
            msg["sender"],
            msg["content"],
            target_name,
            source_format,
            target_aliases=target_aliases,
            self_name=self_name,
        )
        if event:
            events.append(event)
    return events


def parse_qq_txt(file_path: str, target_name: str, *, target_aliases: Optional[str], self_name: Optional[str]) -> list:
    content = read_text_file(file_path)
    return parse_qq_text_content(
        content,
        target_name,
        source_format="qq_txt",
        target_aliases=target_aliases,
        self_name=self_name,
    )


def parse_qq_mht(file_path: str, target_name: str, *, target_aliases: Optional[str], self_name: Optional[str]) -> list:
    content = read_text_file(file_path)
    content = re.sub(r"<script.*?</script>", "", content, flags=re.I | re.S)
    content = re.sub(r"<style.*?</style>", "", content, flags=re.I | re.S)
    content = re.sub(r"<br\s*/?>", "\n", content, flags=re.I)
    content = re.sub(r"</?(div|p|tr|li|table|tbody|td|th|section|article)[^>]*>", "\n", content, flags=re.I)
    content = re.sub(r"<[^>]+>", "", content)
    content = html.unescape(content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    events = parse_qq_text_content(
        content,
        target_name,
        source_format="qq_mht",
        target_aliases=target_aliases,
        self_name=self_name,
    )
    if events:
        return events
    fallback = build_event(
        None,
        target_name,
        content,
        target_name,
        "qq_mht",
        target_aliases=target_aliases,
        self_name=self_name,
        explicit_sender_role="target",
        evidence_strength="medium",
    )
    return [fallback] if fallback else []


def main() -> None:
    parser = argparse.ArgumentParser(description="QQ 聊天记录解析器")
    parser.add_argument("--file", required=True, help="输入文件路径")
    parser.add_argument("--target", required=True, help="初恋的名字/昵称")
    parser.add_argument("--target-aliases", help="ta 的别名，使用逗号分隔")
    parser.add_argument("--self-name", help="你在聊天记录中的名字/备注")
    parser.add_argument("--output", required=True, help="Markdown 报告输出路径")
    parser.add_argument("--json-output", help="额外输出结构化 JSON 分析结果")
    parser.add_argument("--session-gap-minutes", type=int, default=180, help="划分会话的间隔阈值（分钟）")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    ext = Path(args.file).suffix.lower()
    if ext in {".mht", ".mhtml"}:
        detected_format = "qq_mht"
        events = parse_qq_mht(args.file, args.target, target_aliases=args.target_aliases, self_name=args.self_name)
    else:
        detected_format = "qq_txt"
        events = parse_qq_txt(args.file, args.target, target_aliases=args.target_aliases, self_name=args.self_name)

    if not events:
        print("警告：未解析到有效消息。", file=sys.stderr)
        sys.exit(1)

    result = analyze_messages(events, args.target, args.session_gap_minutes, platform="qq")
    write_markdown_report(result, args.file, detected_format, args.output, title="QQ 聊天记录分析")

    if args.json_output:
        os.makedirs(os.path.dirname(args.json_output) or ".", exist_ok=True)
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分析完成，报告已写入 {args.output}")
    if args.json_output:
        print(f"结构化结果已写入 {args.json_output}")


if __name__ == "__main__":
    main()
