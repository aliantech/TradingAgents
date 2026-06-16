from app.realtime.publisher_factory import create_market_data_publisher


class FakeRedis:
    instances = []

    @classmethod
    def from_url(cls, url: str):
        instance = cls()
        instance.url = url
        cls.instances.append(instance)
        return instance


def test_publisher_factory_returns_none_when_disabled():
    publisher = create_market_data_publisher(enabled=False, redis_url="redis://localhost:6379/0")

    assert publisher is None


def test_publisher_factory_creates_redis_publisher_when_enabled():
    FakeRedis.instances.clear()

    publisher = create_market_data_publisher(
        enabled=True,
        redis_url="redis://localhost:6379/0",
        redis_cls=FakeRedis,
        ttl_seconds=30,
    )

    assert publisher is not None
    assert FakeRedis.instances[0].url == "redis://localhost:6379/0"
    assert publisher.ttl_seconds == 30
