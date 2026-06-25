#!/usr/bin/env python3
import json
import sys
from pathlib import Path


CLASSIC_REFERENCE = r'''def rainwater_classic(height):
    left = 0
    right = len(height) - 1
    left_max = 0
    right_max = 0
    total = 0
    while left < right:
        if height[left] <= height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                total += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                total += right_max - height[right]
            right -= 1
    return total
'''


TASKS = [
    {
        "func": "rainwater_classic",
        "prompt_pl": "Napisz funkcje Python rainwater_classic(height) zwracajaca ilosc wody uwiezionej miedzy slupkami po deszczu. height to lista nieujemnych liczb calkowitych, kazdy slupek ma szerokosc 1, a uklad NIE jest kolowy: woda moze wyplynac poza lewy albo prawy koniec. Zwroc liczbe calkowita. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function rainwater_classic(height) returning the amount of water trapped between bars after rain. height is a list of non-negative integers, each bar has width 1, and the layout is NOT circular: water can leak past the left or right end. Return an integer. Return ONLY code in a ```python``` block.",
        "reference": CLASSIC_REFERENCE,
        "tests": [
            [[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], 6],
            [[[4, 2, 0, 3, 2, 5]], 9],
            [[[1, 1]], 0],
            [[[5, 4, 1, 2]], 1],
            [[[]], 0],
            [[[3]], 0],
            [[[2, 0, 2]], 2],
            [[[3, 0, 1, 3, 0, 5]], 8],
            [[[2, 1, 0, 1, 3]], 4],
            [[[4, 0, 4, 0, 4]], 8],
        ],
        "twists": ["baseline LeetCode 42 control; non-circular bars of width 1"],
    },
    {
        "func": "rainwater_v1",
        "prompt_pl": "Napisz funkcje Python rainwater_v1(height) zwracajaca ilosc wody uwiezionej miedzy slupkami po deszczu. height to lista nieujemnych liczb calkowitych. Uklad jest KOLOWY: ostatni slupek i pierwszy slupek sa sasiadami, wiec woda moze byc tez uwieziona przez przejscie przez koniec listy. Nie ma zewnetrznego brzegu, przez ktory woda wyplywa. Rownowaznie: przetnij okrag w jednym z najwyzszych slupkow i potraktuj ten najwyzszy slupek jako oba konce rozwinietej linii. Kazdy slupek ma szerokosc 1. Dla mniej niz 2 slupkow zwroc 0. Zwroc liczbe calkowita. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function rainwater_v1(height) returning the amount of water trapped between bars after rain. height is a list of non-negative integers. The layout is CIRCULAR: the last bar and first bar are adjacent, so water can also be trapped across the end of the list. There is no outside edge where water leaks away. Equivalently: cut the circle at one of the tallest bars and treat that tallest bar as both ends of the unrolled line. Each bar has width 1. For fewer than 2 bars return 0. Return an integer. Return ONLY code in a ```python``` block.",
        "reference": r'''def rainwater_v1(height):
    if len(height) < 2:
        return 0
    top = max(height)
    return sum(top - h for h in height)
''',
        "tests": [
            [[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], 22],
            [[[4, 2, 0, 3, 2, 5]], 14],
            [[[1, 1]], 0],
            [[[5]], 0],
            [[[2, 0, 2]], 2],
            [[[5, 0, 0]], 10],
            [[[3, 1, 2]], 3],
            [[[4, 0, 4, 0, 4]], 8],
            [[[0, 0, 0]], 0],
            [[[1, 0]], 1],
            [[[2, 1, 0, 1, 3]], 8],
        ],
        "twists": ["circular layout: first and last bars are adjacent; no leaking edge"],
    },
    {
        "func": "rainwater_v2",
        "prompt_pl": "Napisz funkcje Python rainwater_v2(height, t) zwracajaca ilosc wody uwiezionej miedzy slupkami po deszczu. height to lista nieujemnych liczb calkowitych, t to grubosc kazdego slupka i liczba calkowita >= 1. Uklad jest KOLOWY: ostatni slupek i pierwszy slupek sa sasiadami, bez zewnetrznego brzegu, przez ktory woda wyplywa. Kazdy slupek ma szerokosc t jednostek, a kazda przerwa miedzy sasiednimi slupkami ma szerokosc 1 jednostki i wysokosc gruntu 0. Dla mniej niz 2 slupkow zwroc 0. Rownowaznie poziom wody w zamknietym okregu dochodzi do wysokosci najwyzszego slupka; policz wode nad slupkami oraz w przerwach. Zwroc liczbe calkowita. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function rainwater_v2(height, t) returning the amount of water trapped between bars after rain. height is a list of non-negative integers, and t is the thickness of each bar, an integer >= 1. The layout is CIRCULAR: the last bar and first bar are adjacent, with no outside edge where water leaks away. Each bar has width t units, and each gap between adjacent bars has width 1 unit and ground height 0. For fewer than 2 bars return 0. Equivalently, the water level in the closed circle reaches the height of the tallest bar; count water above bars and inside gaps. Return an integer. Return ONLY code in a ```python``` block.",
        "reference": r'''def rainwater_v2(height, t):
    n = len(height)
    if n < 2:
        return 0
    top = max(height)
    over_bars = sum((top - h) * t for h in height)
    in_gaps = n * top
    return over_bars + in_gaps
''',
        "tests": [
            [[[2, 0, 2], 2], 10],
            [[[5, 0, 0], 1], 25],
            [[[3, 1, 2], 3], 18],
            [[[1, 1], 4], 2],
            [[[0, 0, 0], 5], 0],
            [[[4, 0, 4, 0, 4], 2], 36],
            [[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], 1], 58],
            [[[4, 2, 0, 3, 2, 5], 2], 58],
            [[[5], 3], 0],
            [[[1, 0], 2], 4],
            [[[2, 1, 0, 1, 3], 1], 23],
        ],
        "twists": ["circular layout", "bar thickness t; each circular gap has width 1 and ground height 0"],
    },
    {
        "func": "rainwater_v3",
        "prompt_pl": "Napisz funkcje Python rainwater_v3(height, t, e) zwracajaca pare (total_water, num_pockets_evaporated). height to lista nieujemnych liczb calkowitych, t to grubosc kazdego slupka i liczba calkowita >= 1, e to prog parowania i liczba calkowita >= 0. Uklad NIE jest kolowy: woda moze wyplynac poza lewy albo prawy koniec. Kazdy slupek ma szerokosc t jednostek, a kazda przerwa miedzy kolejnymi slupkami ma szerokosc 1 jednostki i wysokosc gruntu 0. Najpierw policz zwykle uwieziona wode na tej niekolowej linii, traktujac slupki i przerwy jako kolejne odcinki o podanych szerokosciach. Kieszen wody to maksymalny spojny odcinek fizycznej linii, na ktorym glebokosc wody jest dodatnia. Jezeli szerokosc takiej kieszeni jest <= e, cala kieszen paruje i daje 0 do total_water; zwieksz num_pockets_evaporated o 1. Szersze kieszenie zachowuja cala objetosc. Zwroc krotke dwoch liczb calkowitych. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function rainwater_v3(height, t, e) returning a pair (total_water, num_pockets_evaporated). height is a list of non-negative integers, t is each bar's thickness and an integer >= 1, and e is the evaporation threshold and an integer >= 0. The layout is NOT circular: water can leak past the left or right end. Each bar has width t units, and each gap between consecutive bars has width 1 unit and ground height 0. First compute ordinary trapped water on this non-circular line, treating bars and gaps as consecutive segments with the given widths. A water pocket is a maximal connected interval of the physical line where water depth is positive. If such a pocket has width <= e, the whole pocket evaporates and contributes 0 to total_water; increase num_pockets_evaporated by 1. Wider pockets keep their entire volume. Return a tuple of two integers. Return ONLY code in a ```python``` block.",
        "reference": r'''def rainwater_v3(height, t, e):
    if len(height) < 2:
        return (0, 0)

    segments = []
    for i, h in enumerate(height):
        segments.append((h, t))
        if i != len(height) - 1:
            segments.append((0, 1))

    n = len(segments)
    left = [0] * n
    right = [0] * n
    high = 0
    for i, (h, _) in enumerate(segments):
        left[i] = high
        if h > high:
            high = h
    high = 0
    for i in range(n - 1, -1, -1):
        h, _ = segments[i]
        right[i] = high
        if h > high:
            high = h

    water = []
    for i, (h, width) in enumerate(segments):
        level = min(left[i], right[i])
        depth = level - h
        water.append(depth * width if depth > 0 else 0)

    total = 0
    evaporated = 0
    i = 0
    while i < n:
        if water[i] == 0:
            i += 1
            continue
        pocket_width = 0
        pocket_volume = 0
        while i < n and water[i] > 0:
            pocket_width += segments[i][1]
            pocket_volume += water[i]
            i += 1
        if pocket_width <= e:
            evaporated += 1
        else:
            total += pocket_volume
    return (total, evaporated)
''',
        "tests": [
            [[[3, 0, 3], 2, 3], [12, 0]],
            [[[3, 0, 3], 2, 4], [0, 1]],
            [[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], 1, 2], [20, 2]],
            [[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], 1, 20], [0, 5]],
            [[[4, 2, 0, 3, 2, 5], 2, 3], [38, 0]],
            [[[4, 2, 0, 3, 2, 5], 2, 20], [0, 1]],
            [[[5, 4, 1, 2], 3, 4], [7, 1]],
            [[[5, 4, 1, 2], 3, 10], [0, 2]],
            [[[4, 0, 4, 0, 4], 1, 2], [24, 0]],
            [[[4, 0, 4, 0, 4], 1, 3], [0, 2]],
            [[[1, 1], 5, 1], [0, 1]],
            [[[3, 0, 1, 0, 3], 2, 5], [28, 0]],
        ],
        "twists": ["non-circular layout", "bar thickness t and width-1 gaps", "pockets of physical width <= e evaporate", "returns (total_water, num_pockets_evaporated)"],
    },
]


HAND_CHECKS = {
    "rainwater_v1": [
        ([[5, 0, 0]], 10, "closed ring: two zero bars fill to height 5"),
        ([[3, 1, 2]], 3, "max height 3, deficits 0+2+1"),
        ([[2, 1, 0, 1, 3]], 8, "max height 3, deficits 1+2+3+2+0"),
    ],
    "rainwater_v2": [
        ([[2, 0, 2], 2], 10, "center bar volume 2*2 plus three gaps of height 2"),
        ([[5, 0, 0], 1], 25, "two low bars fill 10, three gaps fill 15"),
        ([[3, 1, 2], 3], 18, "bar deficits 3 units wide give 9, three gaps give 9"),
    ],
    "rainwater_v3": [
        ([[3, 0, 3], 2, 3], [12, 0], "one pocket width 4 and volume 12 survives"),
        ([[3, 0, 3], 2, 4], [0, 1], "same width-4 pocket evaporates"),
        ([[4, 0, 4, 0, 4], 1, 3], [0, 2], "two width-3 pockets evaporate"),
    ],
}


def load_func(source, name):
    namespace = {}
    exec(source, namespace)
    return namespace[name]


def normalize(value):
    if isinstance(value, tuple):
        return list(value)
    return value


def run_tests(task):
    fn = load_func(task["reference"], task["func"])
    for args, expected in task["tests"]:
        got = normalize(fn(*args))
        assert got == expected, f"{task['func']}({args}) -> {got}, expected {expected}"


def classic_bites(task):
    fn = load_func(CLASSIC_REFERENCE, "rainwater_classic")
    failures = 0
    for args, expected in task["tests"]:
        try:
            got = normalize(fn(*args))
        except Exception:
            failures += 1
            continue
        if got != expected:
            failures += 1
    assert failures > 0, f"classic unexpectedly passed all tests for {task['func']}"
    return failures


def assert_ascii_polish():
    required_suffix = "Zwroc TYLKO kod w bloku ```python```."
    for task in TASKS:
        prompt = task["prompt_pl"]
        assert prompt.endswith(required_suffix), f"{task['func']} Polish prompt suffix mismatch"
        assert prompt.isascii(), f"{task['func']} Polish prompt contains non-ASCII"
        assert task["prompt_en"].endswith("Return ONLY code in a ```python``` block."), task["func"]


def assert_hand_checks():
    by_name = {task["func"]: task for task in TASKS}
    for name, checks in HAND_CHECKS.items():
        fn = load_func(by_name[name]["reference"], name)
        for args, expected, reason in checks:
            got = normalize(fn(*args))
            assert got == expected, f"hand-check mismatch for {name}: {reason}; got {got}, expected {expected}"


def write_candidates():
    out = {
        "family": "rainwater",
        "base_problem": "Trapping Rain Water (LeetCode 42)",
        "tasks": TASKS,
    }
    path = Path(__file__).with_name("mutated_candidates.json")
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"WROTE {path}")


def main():
    assert_ascii_polish()
    assert_hand_checks()
    for task in TASKS:
        run_tests(task)
        print(f"PASS {task['func']} reference ({len(task['tests'])} tests)")
    for task in TASKS[1:]:
        failures = classic_bites(task)
        print(f"CLASSIC-BITES {task['func']} ({failures}/{len(task['tests'])} failures)")
    print("SUMMARY all references pass and every mutated task defeats the classic reference")
    if "--write-json" in sys.argv:
        write_candidates()


if __name__ == "__main__":
    main()
