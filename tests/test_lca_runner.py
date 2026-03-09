# Test for LCA runner
def test_run_lca():
    from ltt_core.lca_runner import run_lca
    result = run_lca({"test": 1}, ("test",))
    assert "score" in result