from src import conversation_cache as cache


def test_invalidate_by_project():
    cache.set_block("p1", "b", "k1", 1)
    cache.set_block("p2", "b", "k2", 2)
    removed = cache.invalidate(project_id="p1")
    assert removed == 1
    assert cache.get_block("p1", "b", "k1") is None
    assert cache.get_block("p2", "b", "k2") == 2
    cache.invalidate()