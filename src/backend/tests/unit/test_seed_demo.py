import importlib.util
import sys
from pathlib import Path

from app.db.enums import LocationArea, RecordKind


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "seed_demo.py"
SPEC = importlib.util.spec_from_file_location("seed_demo_under_test", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
seed_demo = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = seed_demo
SPEC.loader.exec_module(seed_demo)

DEMO_CASES = seed_demo.DEMO_CASES
demo_id = seed_demo.demo_id


def test_every_repository_image_has_a_lost_and_found_demo_case() -> None:
    image_names = {case.image_name for case in DEMO_CASES if case.image_name is not None}

    assert image_names == {
        "images.jpeg",
        "毕业证.jpg",
        "电脑.jpg",
        "电脑包.jpg",
        "笔记本.jpg",
        "美乐蒂托特包.jpg",
        "羽毛球拍.jpg",
        "衣服.jpeg",
    }
    for case in DEMO_CASES:
        assert demo_id(f"{case.slug}-{RecordKind.LOST.value.casefold()}") != demo_id(
            f"{case.slug}-{RecordKind.FOUND.value.casefold()}"
        )


def test_umbrella_case_keeps_floor_and_handle_conflicts_but_remains_matchable() -> None:
    umbrella = next(case for case in DEMO_CASES if case.slug == "umbrella-floor-conflict")

    assert umbrella.lost_area is LocationArea.TEACHING_BUILDING
    assert umbrella.found_area is LocationArea.TEACHING_BUILDING
    assert "三楼" in umbrella.lost_location
    assert "二楼" in umbrella.found_location
    assert "直柄" in umbrella.lost_description
    assert "弯柄" in umbrella.found_description
    assert umbrella.score >= 80
    assert set(umbrella.conflicts) == {"FLOOR_CONFLICT", "HANDLE_FEATURE_CONFLICT"}


def test_each_demo_user_can_own_both_record_kinds() -> None:
    owner_kinds: dict[int, set[RecordKind]] = {0: set(), 1: set(), 2: set()}
    for index, _case in enumerate(DEMO_CASES):
        owner_kinds[index % 3].add(RecordKind.LOST)
        owner_kinds[(index + 1) % 3].add(RecordKind.FOUND)

    assert all(kinds == {RecordKind.LOST, RecordKind.FOUND} for kinds in owner_kinds.values())
