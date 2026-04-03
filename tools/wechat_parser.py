#!/usr/bin/env python3
"""Enhanced WeChat parser."""

import argparse
import csv
import html
import json
import os
import re
import sqlite3
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


TIMESTAMP_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+)$")


def detect_format(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".json":
        return "liuhen"
    if ext == ".csv":
        return "wechatmsg_csv"
    if ext in {".html", ".htm"}:
        return "wechatmsg_html"
    if ext in {".db", ".sqlite"}:
        return "pywxdump"
    if ext == ".txt":
        first_chunk = read_text_file(file_path)[:3000]
        if any(TIMESTAMP_PATTERN.match(line.strip()) for line in first_chunk.splitlines() if line.strip()):
            return "wechatmsg_txt"
        return "plaintext"
    return "plaintext"


def parse_wechatmsg_txt(
    file_path: str,
    target_name: str,
    source_format: str,
    *,
    target_aliases: Optional[str] = None,
    self_name: Optional[str] = None,
) -> list:
    messages = []
    current_timestamp = None
    current_sender = ""
    current_lines: list[str] = []

    for raw_line in read_text_file(file_path).splitlines():
        line = raw_line.rstrip("\n")
        match = TIMESTAMP_PATTERN.match(line)
        if match:
            if current_sender and current_lines:
                event = build_event(
                    current_timestamp,
                    current_sender,
                    "\n".join(current_lines),
                    target_name,
                    source_format,
                    target_aliases=target_aliases,
                    self_name=self_name,
                )
                if event:
                    messages.append(event)
            current_timestamp = parse_timestamp(match.group(1))
            current_sender = match.group(2)
            current_lines = []
            continue
        if current_sender and line.strip():
            current_lines.append(line)

    if current_sender and current_lines:
        event = build_event(
            current_timestamp,
            current_sender,
            "\n".join(current_lines),
            target_name,
            source_format,
            target_aliases=target_aliases,
            self_name=self_name,
        )
        if event:
            messages.append(event)
    return messages


def parse_liuhen_json(file_path: str, target_name: str, *, target_aliases: Optional[str], self_name: Optional[str]) -> list:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = data if isinstance(data, list) else data.get("messages") or data.get("data") or data.get("records") or []
    events = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        timestamp = parse_timestamp(row.get("time") or row.get("timestamp") or row.get("msgTime") or row.get("create_time"))
        sender = row.get("sender") or row.get("nickname") or row.get("from") or row.get("talker") or row.get("display_name") or ""
        content = row.get("content") or row.get("message") or row.get("text") or row.get("strContent") or ""
        explicit_sender_role = None
        if row.get("isSender") in (1, "1", True, "true"):
            explicit_sender_role = "user"
        event = build_event(
            timestamp,
            str(sender),
            str(content),
            target_name,
            "liuhen",
            target_aliases=target_aliases,
            self_name=self_name,
            explicit_sender_role=explicit_sender_role,
        )
        if event:
            events.append(event)
    return events


def parse_plaintext(file_path: str, target_name: str, *, target_aliases: Optional[str], self_name: Optional[str]) -> list:
    content = read_text_file(file_path)
    event = build_event(
        None,
        target_name,
        content,
        target_name,
        "plaintext",
        target_aliases=target_aliases,
        self_name=self_name,
        explicit_sender_role="target",
        evidence_strength="medium",
    )
    return [event] if event else []


def parse_wechatmsg_html(file_path: str, target_name: str, *, target_aliases: Optional[str], self_name: Optional[str]) -> list:
    content = read_text_file(file_path)
    content = re.sub(r"<script.*?</script>", "", content, flags=re.I | re.S)
    content = re.sub(r"<style.*?</style>", "", content, flags=re.I | re.S)
    content = re.sub(r"<br\s*/?>", "\n", content, flags=re.I)
    content = re.sub(r"</?(div|p|tr|li|table|tbody|td|th|section|article)[^>]*>", "\n", content, flags=re.I)
    content = re.sub(r"<[^>]+>", "", content)
    content = html.unescape(content)
    content = re.sub(r"\n{3,}", "\n\n", content)

    temp_path = f"{file_path}.plain.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)
    try:
        parsed = parse_wechatmsg_txt(
            temp_path,
            target_name,
            "wechatmsg_html",
            target_aliases=target_aliases,
            self_name=self_name,
        )
        return parsed or parse_plaintext(temp_path, target_name, target_aliases=target_aliases, self_name=self_name)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def parse_wechatmsg_csv(file_path: str, target_name: str, *, target_aliases: Optional[str], self_name: Optional[str]) -> list:
    events = []
    content = read_text_file(file_path)
    dialect = csv.excel
    try:
        dialect = csv.Sniffer().sniff(content[:2048])
    except csv.Error:
        pass

    reader = csv.DictReader(content.splitlines(), dialect=dialect)
    field_map = {name.lower(): name for name in (reader.fieldnames or [])}

    def pick(row: dict[str, str], *keys: str) -> str:
        for key in keys:
            actual = field_map.get(key.lower())
            if actual and row.get(actual):
                return row[actual]
        return ""

    for row in reader:
        timestamp = parse_timestamp(pick(row, "time", "timestamp", "createTime", "msgTime", "date"))
        sender = pick(row, "sender", "talker", "nickname", "from", "name")
        content_text = pick(row, "content", "message", "text", "strContent", "body")
        explicit_sender_role = None
        is_sender = pick(row, "isSender", "issender", "des")
        if str(is_sender).strip().lower() in {"1", "true", "yes"}:
            explicit_sender_role = "user"
        event = build_event(
            timestamp,
            sender,
            content_text,
            target_name,
            "wechatmsg_csv",
            target_aliases=target_aliases,
            self_name=self_name,
            explicit_sender_role=explicit_sender_role,
        )
        if event:
            events.append(event)
    return events


def parse_pywxdump_sqlite(file_path: str, target_name: str, *, target_aliases: Optional[str], self_name: Optional[str]) -> list:
    conn = sqlite3.connect(file_path)
    conn.row_factory = sqlite3.Row
    try:
        tables = [
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if not str(row["name"]).startswith("sqlite_")
        ]
        best_table = None
        best_score = -1
        best_columns: set[str] = set()

        for table in tables:
            columns = {str(col["name"]).lower() for col in conn.execute(f"PRAGMA table_info('{table}')")}
            score = 0
            if {"strcontent", "content", "message", "text"} & columns:
                score += 4
            if {"createtime", "timestamp", "time"} & columns:
                score += 3
            if {"issender", "sender", "talker", "des"} & columns:
                score += 2
            if score > best_score:
                best_score = score
                best_table = table
                best_columns = columns

        if not best_table or best_score < 4:
            return []

        def choose(*candidates: str) -> Optional[str]:
            for candidate in candidates:
                if candidate.lower() in best_columns:
                    return candidate
            return None

        time_col = choose("createTime", "CreateTime", "timestamp", "time")
        content_col = choose("StrContent", "content", "message", "text", "body")
        sender_col = choose("sender", "talker", "nickname", "fromUser")
        is_sender_col = choose("IsSender", "isSender", "issender", "Des", "des")
        if not time_col or not content_col:
            return []

        selected_cols = [time_col, content_col]
        if sender_col:
            selected_cols.append(sender_col)
        if is_sender_col and is_sender_col not in selected_cols:
            selected_cols.append(is_sender_col)

        query = f"SELECT {', '.join(selected_cols)} FROM '{best_table}'"
        rows = conn.execute(query).fetchmany(5000)
        events = []
        for row in rows:
            timestamp = parse_timestamp(row[time_col])
            content = row[content_col]
            sender = ""
            explicit_sender_role = None
            if sender_col and row[sender_col]:
                sender = str(row[sender_col])
            elif is_sender_col is not None:
                is_sender = str(row[is_sender_col]).strip().lower() in {"1", "true", "yes"}
                explicit_sender_role = "user" if is_sender else "target"
            event = build_event(
                timestamp,
                sender,
                str(content or ""),
                target_name,
                "pywxdump",
                target_aliases=target_aliases,
                self_name=self_name,
                explicit_sender_role=explicit_sender_role,
            )
            if event:
                events.append(event)
        return events
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="微信聊天记录解析器")
    parser.add_argument("--file", required=True, help="输入文件路径")
    parser.add_argument("--target", required=True, help="初恋的名字/昵称")
    parser.add_argument("--target-aliases", help="ta 的别名，使用逗号分隔")
    parser.add_argument("--self-name", help="你在聊天记录中的名字/备注")
    parser.add_argument("--output", required=True, help="Markdown 报告输出路径")
    parser.add_argument(
        "--format",
        default="auto",
        help="文件格式 (auto/wechatmsg_txt/liuhen/pywxdump/plaintext/wechatmsg_html/wechatmsg_csv)",
    )
    parser.add_argument("--json-output", help="额外输出结构化 JSON 分析结果")
    parser.add_argument("--session-gap-minutes", type=int, default=180, help="划分会话的间隔阈值（分钟）")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    detected_format = args.format
    if detected_format == "auto":
        detected_format = detect_format(args.file)
        print(f"自动检测格式：{detected_format}")

    parsers = {
        "wechatmsg_txt": lambda p, t: parse_wechatmsg_txt(p, t, "wechatmsg_txt", target_aliases=args.target_aliases, self_name=args.self_name),
        "liuhen": lambda p, t: parse_liuhen_json(p, t, target_aliases=args.target_aliases, self_name=args.self_name),
        "plaintext": lambda p, t: parse_plaintext(p, t, target_aliases=args.target_aliases, self_name=args.self_name),
        "wechatmsg_html": lambda p, t: parse_wechatmsg_html(p, t, target_aliases=args.target_aliases, self_name=args.self_name),
        "wechatmsg_csv": lambda p, t: parse_wechatmsg_csv(p, t, target_aliases=args.target_aliases, self_name=args.self_name),
        "pywxdump": lambda p, t: parse_pywxdump_sqlite(p, t, target_aliases=args.target_aliases, self_name=args.self_name),
    }

    parse_func = parsers.get(detected_format, parsers["plaintext"])
    events = parse_func(args.file, args.target)
    if not events:
        print("警告：未解析到有效消息，退回纯文本模式。")
        events = parse_plaintext(args.file, args.target, target_aliases=args.target_aliases, self_name=args.self_name)
        detected_format = "plaintext"

    result = analyze_messages(events, args.target, args.session_gap_minutes, platform="wechat")
    write_markdown_report(result, args.file, detected_format, args.output, title="微信聊天记录分析")

    if args.json_output:
        os.makedirs(os.path.dirname(args.json_output) or ".", exist_ok=True)
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分析完成，报告已写入 {args.output}")
    if args.json_output:
        print(f"结构化结果已写入 {args.json_output}")


if __name__ == "__main__":
    main()
