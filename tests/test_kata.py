from pathlib import Path

import pytest

from sparql_kata.kata import KataError, load_kata

KATAS = Path(__file__).parent.parent / "katas"


@pytest.mark.parametrize("name", ["optional-01", "distinct-01", "join-01"])
def test_example_katas_load(name):
    kata = load_kata(KATAS / f"{name}.yaml")
    assert kata.id == name
    assert kata.datasets[0].label == "visible" and not kata.datasets[0].hidden
    assert all(d.hidden for d in kata.datasets[1:])


def test_unknown_key_is_rejected(tmp_path):
    (tmp_path / "d.ttl").write_text("")
    kata_file = tmp_path / "k.yaml"
    kata_file.write_text(
        "id: k\nprompt: p\nreference: SELECT * {}\n"
        "datasets: {visible: d.ttl}\n"
        "grading: {order_sensitve: true}\n"  # typo on purpose
    )
    with pytest.raises(KataError, match="order_sensitve"):
        load_kata(kata_file)


def test_missing_dataset_file(tmp_path):
    kata_file = tmp_path / "k.yaml"
    kata_file.write_text("id: k\nprompt: p\nreference: SELECT * {}\ndatasets: {visible: nope.ttl}\n")
    with pytest.raises(KataError, match="not found"):
        load_kata(kata_file)
