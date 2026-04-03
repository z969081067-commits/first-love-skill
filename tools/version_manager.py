#!/usr/bin/env python3
"""版本存档与回滚管理器

Usage:
    python3 version_manager.py --action <backup|rollback|list> --slug <slug> --base-dir <path> [--version <v>]
"""

import argparse
import os
import sys
import shutil
import json
from datetime import datetime


def backup(base_dir: str, slug: str):
    """备份当前版本"""
    skill_dir = os.path.join(base_dir, slug)
    versions_dir = os.path.join(skill_dir, 'versions')
    meta_path = os.path.join(skill_dir, 'meta.json')
    
    if not os.path.exists(meta_path):
        print(f"错误：meta.json 不存在", file=sys.stderr)
        sys.exit(1)
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    current_version = meta.get('version', 'v0')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{current_version}_{timestamp}"
    backup_dir = os.path.join(versions_dir, backup_name)
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # 备份核心文件
    for fname in ['memory.md', 'persona.md', 'SKILL.md', 'meta.json']:
        src = os.path.join(skill_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(backup_dir, fname))
    
    print(f"已备份版本 {backup_name} 到 {backup_dir}")
    return backup_name


def resolve_version_dir(versions_dir: str, version: str) -> tuple[str, str]:
    """解析回滚目标目录。

    规则：
    1. 目录名完全匹配时，优先使用完全匹配。
    2. 否则匹配以 `{version}_` 开头的快照目录。
    3. 多个候选时，按目录名倒序选择最新快照。
    """
    if not os.path.isdir(versions_dir):
        raise FileNotFoundError("没有历史版本。")

    version_names = [
        name for name in os.listdir(versions_dir)
        if os.path.isdir(os.path.join(versions_dir, name))
    ]
    if not version_names:
        raise FileNotFoundError("没有历史版本。")

    if version in version_names:
        return version, os.path.join(versions_dir, version)

    candidates = sorted(
        [name for name in version_names if name.startswith(f"{version}_")],
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"找不到版本 {version}")

    selected = candidates[0]
    return selected, os.path.join(versions_dir, selected)


def rollback(base_dir: str, slug: str, version: str):
    """回滚到指定版本"""
    skill_dir = os.path.join(base_dir, slug)
    versions_dir = os.path.join(skill_dir, 'versions')

    try:
        resolved_version, target_dir = resolve_version_dir(versions_dir, version)
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        list_versions(base_dir, slug)
        sys.exit(1)

    # 先备份当前版本
    backup(base_dir, slug)

    # 恢复文件
    for fname in ['memory.md', 'persona.md', 'SKILL.md', 'meta.json']:
        src = os.path.join(target_dir, fname)
        dst = os.path.join(skill_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    print(f"已回滚到版本 {resolved_version}")


def list_versions(base_dir: str, slug: str):
    """列出所有版本"""
    versions_dir = os.path.join(base_dir, slug, 'versions')
    
    if not os.path.isdir(versions_dir):
        print("没有历史版本。")
        return
    
    versions = sorted(os.listdir(versions_dir), reverse=True)
    if not versions:
        print("没有历史版本。")
        return
    
    print(f"历史版本（共 {len(versions)} 个）：\n")
    for v in versions:
        print(f"  {v}")


def main():
    parser = argparse.ArgumentParser(description='版本管理器')
    parser.add_argument('--action', required=True, choices=['backup', 'rollback', 'list'])
    parser.add_argument('--slug', required=True, help='初恋代号')
    parser.add_argument('--base-dir', default='./first_loves', help='基础目录')
    parser.add_argument('--version', help='回滚目标版本')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        backup(args.base_dir, args.slug)
    elif args.action == 'rollback':
        if not args.version:
            print("错误：rollback 需要 --version 参数", file=sys.stderr)
            sys.exit(1)
        rollback(args.base_dir, args.slug, args.version)
    elif args.action == 'list':
        list_versions(args.base_dir, args.slug)


if __name__ == '__main__':
    main()
