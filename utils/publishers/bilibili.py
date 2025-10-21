from __future__ import annotations
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from .base import BasePublisher


class BilibiliPublisher(BasePublisher):
    def __init__(self, dry_run: bool = True, output_root: str | None = None):
        super().__init__(platform="bilibili", dry_run=dry_run, output_root=output_root)
        self.env = Environment(
            loader=FileSystemLoader(str(Path("templates/platform"))),
            autoescape=select_autoescape()
        )
        self.template = self.env.get_template("bilibili.md.j2")

    def render(self, content):
        # 需要 metadata.scenes: [{time, visual, text}]
        return self.template.render(
            title=content.title or "",
            metadata=content.metadata or {},
            hashtags=content.hashtags or [],
            cover_suggestions=(content.metadata or {}).get("cover_suggestions", "")
        )
