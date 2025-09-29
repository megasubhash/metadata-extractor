import builtins
from datasource.factory import DataSourceFactory


def test_factory_github():
    cfg = {"type": "github", "owner": "o", "repo": "r"}
    strat = DataSourceFactory.get_strategy(cfg)
    from datasource.github.strategy import GitHubStrategy
    assert isinstance(strat, GitHubStrategy)


def test_factory_redis():
    cfg = {"type": "redis", "host": "localhost", "port": 6379, "db": 0}
    strat = DataSourceFactory.get_strategy(cfg)
    from datasource.redis.strategy import RedisStrategy
    assert isinstance(strat, RedisStrategy)
