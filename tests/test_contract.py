def test_contract_source_present():
    from pathlib import Path
    source=Path('contracts/checkpoint_graph.py').read_text()
    assert 'class MarketSentinel' in source
    assert 'def sample' in source
    assert 'run_nondet_unsafe' in source
