from __future__ import annotations
from typing import Dict

from .wechat import WechatPublisher
from .weibo import WeiboPublisher
from .bilibili import BilibiliPublisher


def get_publishers(enabled_platforms: list[str], dry_run: bool = True):
    mapping: Dict[str, object] = {}
    for p in enabled_platforms:
        if p == "wechat":
            mapping[p] = WechatPublisher(dry_run=dry_run)
        elif p == "weibo":
            mapping[p] = WeiboPublisher(dry_run=dry_run)
        elif p == "bilibili":
            mapping[p] = BilibiliPublisher(dry_run=dry_run)
    return mapping
