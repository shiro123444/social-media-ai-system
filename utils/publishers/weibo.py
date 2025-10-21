from __future__ import annotations
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from .base import BasePublisher


class WeiboPublisher(BasePublisher):
    def __init__(self, dry_run: bool = True, output_root: str | None = None):
        super().__init__(platform="weibo", dry_run=dry_run, output_root=output_root)
        self.env = Environment(
            loader=FileSystemLoader(str(Path("templates/platform"))),
            autoescape=select_autoescape()
        )
        self.template = self.env.get_template("weibo.md.j2")

    def render(self, content):
        return self.template.render(content=content.content, hashtags=content.hashtags)
