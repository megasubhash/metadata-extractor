import builtins
from datasource.factory import DataSourceFactory


def test_factory_postgres():
    cfg = {"type": "postgres", "host": "h", "port": 5432, "database": "d", "user": "u", "password": "p"}
    strat = DataSourceFactory.get_strategy(cfg)
    from datasource.postgres_strategy import PostgresStrategy
    assert isinstance(strat, PostgresStrategy)


def test_factory_github():
    cfg = {"type": "github", "owner": "o", "repo": "r"}
    strat = DataSourceFactory.get_strategy(cfg)
    from datasource.github_strategy import GitHubStrategy
    assert isinstance(strat, GitHubStrategy)
