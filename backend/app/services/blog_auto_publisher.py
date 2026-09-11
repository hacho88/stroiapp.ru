import asyncio
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class BlogAutoPublisher:
    """Background task that auto-publishes 1-2 blog articles per day."""

    def __init__(self) -> None:
        self._running = False
        self._last_run = None
        self._last_publish_date = None
        self._published_today = 0
        self.max_per_day = 2

    def status(self) -> dict:
        return {
            "running": self._running,
            "last_run": self._last_run if isinstance(self._last_run, str) else (self._last_run.isoformat() if self._last_run else None),
            "published_today": self._published_today,
            "max_per_day": self.max_per_day,
            "last_publish_date": self._last_publish_date,
        }

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        logger.info("BlogAutoPublisher started — %d articles/day", self.max_per_day)
        while self._running:
            try:
                await self._tick()
            except Exception as exc:
                logger.error("BlogAutoPublisher error: %s", exc)
            await asyncio.sleep(3600)

    async def stop(self) -> None:
        self._running = False

    async def _tick(self) -> None:
        now = datetime.now(timezone(timedelta(hours=3)))
        today = now.strftime("%Y-%m-%d")

        if self._last_publish_date != today:
            self._last_publish_date = today
            self._published_today = 0

        if self._published_today >= self.max_per_day:
            return

        if now.hour < 9 or now.hour > 22:
            return

        self._last_run = now.isoformat()

        from app.api.routes.content_factory import (
            generate_articles,
            publish_article,
            _check_daily_limit,
        )

        while self._published_today < self.max_per_day and _check_daily_limit():
            try:
                gen = await generate_articles({"count": 1})
                if gen.get("generated"):
                    pub = await publish_article({"article_id": gen["generated"][0]["id"]})
                    if pub.get("status") == "published":
                        self._published_today += 1
                        logger.info("BlogAutoPublisher: published '%s'", pub.get("title", ""))
                    elif pub.get("status") == "limit_reached":
                        break
                    else:
                        logger.warning("BlogAutoPublisher: publish failed — %s", pub)
                        break
                else:
                    logger.warning("BlogAutoPublisher: generation returned no articles")
                    break
                await asyncio.sleep(5)
            except Exception as exc:
                logger.error("BlogAutoPublisher publish error: %s", exc)
                break


_blog_auto_publisher: BlogAutoPublisher | None = None


def get_blog_auto_publisher() -> BlogAutoPublisher:
    global _blog_auto_publisher
    if _blog_auto_publisher is None:
        _blog_auto_publisher = BlogAutoPublisher()
    return _blog_auto_publisher
