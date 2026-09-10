def test_contract_source_present():
    from pathlib import Path
    assert 'class CheckpointGraph' in Path('contracts/checkpoint_graph.py').read_text()
