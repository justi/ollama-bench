#!/usr/bin/env python3
import json
import sys
from pathlib import Path


CLASSIC_RAINWATER = r'''def rainwater_v1(height):
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
        "func": "rainwater_v1",
        "prompt_pl": "Napisz funkcje Python rainwater_v1(height) zwracajaca ilosc wody uwiezionej miedzy slupkami po deszczu. height to lista nieujemnych liczb calkowitych. Uklad jest kolowy tylko w tym sensie, ze mozna przeciac go w pierwszym wystapieniu najwyzszego slupka, przesunac ten slupek na poczatek listy, a potem policzyc zwykla niekolowa wode na tak obroconej liscie, bez duplikowania slupka na koncu. Kazdy slupek ma szerokosc 1. Dla mniej niz 2 slupkow zwroc 0. Zwroc liczbe calkowita. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function rainwater_v1(height) returning the amount of water trapped between bars after rain. height is a list of non-negative integers. The layout is circular only in this precise sense: cut it at the first occurrence of a tallest bar, rotate that bar to the start of the list, then compute ordinary non-circular trapped water on that rotated list, without duplicating the bar at the end. Each bar has width 1. For fewer than 2 bars return 0. Return an integer. Return ONLY code in a ```python``` block.",
        "reference": r'''def rainwater_v1(height):
    if len(height) < 2:
        return 0
    start = height.index(max(height))
    rotated = height[start:] + height[:start]
    left = 0
    right = len(rotated) - 1
    left_max = 0
    right_max = 0
    total = 0
    while left < right:
        if rotated[left] <= rotated[right]:
            if rotated[left] >= left_max:
                left_max = rotated[left]
            else:
                total += left_max - rotated[left]
            left += 1
        else:
            if rotated[right] >= right_max:
                right_max = rotated[right]
            else:
                total += right_max - rotated[right]
            right -= 1
    return total
''',
        "tests": [
            [[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], 8],
            [[[4, 2, 0, 3, 2, 5]], 4],
            [[[1, 1]], 0],
            [[[5]], 0],
            [[[2, 0, 2]], 2],
            [[[5, 0, 0]], 0],
            [[[3, 1, 2]], 1],
            [[[4, 0, 4, 0, 4]], 8],
            [[[0, 0, 0]], 0],
            [[[1, 0]], 0],
            [[[2, 1, 0, 1, 3]], 1],
            [[[1, 3, 0, 1, 2]], 3],
        ],
        "twists": [
            "circular input is normalized by cutting at the first tallest bar",
            "ordinary non-circular trapping is applied after rotation",
            "the cut bar is not duplicated as both ends",
        ],
    },
    {
        "func": "binary_search_rank",
        "prompt_pl": "Napisz funkcje Python binary_search_rank(nums, target). nums jest posortowana niemalejaco i moze zawierac duplikaty. Zwroc ile ROZNYCH wartosci w nums jest mniejszych albo rownych target, czyli indeks wstawienia target za ostatnia nie wieksza wartoscia po skasowaniu duplikatow. Jezeli nums jest pusta, zwroc 0. Zwroc liczbe calkowita. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function binary_search_rank(nums, target). nums is sorted in nondecreasing order and may contain duplicates. Return how many DISTINCT values in nums are less than or equal to target, i.e. the insertion index of target after the last not-greater value after duplicates are collapsed. If nums is empty, return 0. Return an integer. Return ONLY code in a ```python``` block.",
        "reference": r'''def binary_search_rank(nums, target):
    count = 0
    prev = None
    seen = False
    for value in nums:
        if not seen or value != prev:
            if value <= target:
                count += 1
            else:
                break
            prev = value
            seen = True
    return count
''',
        "tests": [
            [[[], 4], 0],
            [[[1, 1, 1], 1], 1],
            [[[1, 1, 1], 0], 0],
            [[[1, 2, 2, 2, 5], 2], 2],
            [[[1, 2, 2, 2, 5], 3], 2],
            [[[-5, -5, -2, 0, 0, 7], -3], 1],
            [[[-5, -5, -2, 0, 0, 7], 7], 4],
            [[[2, 4, 4, 6, 8], 5], 2],
            [[[2, 4, 4, 6, 8], 9], 4],
            [[[0, 0, 1, 1, 2, 3, 3], 1], 2],
        ],
        "twists": [
            "return an insertion rank, not a found index",
            "collapse duplicate values before counting",
            "use last-not-greater semantics for absent targets",
        ],
    },
    {
        "func": "two_sum_all_1based",
        "prompt_pl": "Napisz funkcje Python two_sum_all_1based(nums, target). Zwroc wszystkie pary indeksow [i, j] takie, ze i < j, nums[i-1] + nums[j-1] == target, a indeksy sa 1-based. Wynik posortuj leksykograficznie rosnaco. Jezeli nie ma par, zwroc pusta liste. Nie usuwaj par tylko dlatego, ze maja te same wartosci; rozne indeksy to rozne pary. Zwroc liste list. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function two_sum_all_1based(nums, target). Return every index pair [i, j] such that i < j, nums[i-1] + nums[j-1] == target, and indices are 1-based. Sort the result in increasing lexicographic order. If there are no pairs, return an empty list. Do not remove pairs just because they have the same values; different indices are different pairs. Return a list of lists. Return ONLY code in a ```python``` block.",
        "reference": r'''def two_sum_all_1based(nums, target):
    pairs = []
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                pairs.append([i + 1, j + 1])
    return pairs
''',
        "tests": [
            [[[], 5], []],
            [[[2, 7, 11, 15], 9], [[1, 2]]],
            [[[3, 3, 3], 6], [[1, 2], [1, 3], [2, 3]]],
            [[[1, 2, 3, 4, 5], 6], [[1, 5], [2, 4]]],
            [[[0, 0, 0, 1], 0], [[1, 2], [1, 3], [2, 3]]],
            [[[-1, 1, 2, -2, 3], 0], [[1, 2], [3, 4]]],
            [[[5, -1, 6, 0, 1], 5], [[1, 4], [2, 3]]],
            [[[1, 1, 2, 2, 3, 3], 4], [[1, 5], [1, 6], [2, 5], [2, 6], [3, 4]]],
            [[[10], 10], []],
            [[[4, 4, 4, 4], 8], [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]],
        ],
        "twists": [
            "return all matching index pairs, not just one pair",
            "indices are 1-based",
            "duplicate values still create distinct index pairs",
        ],
    },
    {
        "func": "merge_half_open_strict",
        "prompt_pl": "Napisz funkcje Python merge_half_open_strict(intervals). intervals to lista przedzialow [start, end] opisujacych polotwarte zakresy [start, end). Jezeli start > end, najpierw zamien konce. Przedzialy o zerowej dlugosci, gdzie start == end, usun z wyniku. Scal tylko przedzialy, ktore nachodza na siebie dodatnia dlugoscia; przedzialy dotykajace sie w punkcie, np. [1,3) i [3,5), NIE sa scalane. Wynik zwroc jako liste [start, end] posortowana rosnaco. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function merge_half_open_strict(intervals). intervals is a list of [start, end] intervals representing half-open ranges [start, end). If start > end, swap the endpoints first. Remove zero-length intervals where start == end. Merge only intervals that overlap with positive length; intervals that merely touch at one point, such as [1,3) and [3,5), are NOT merged. Return the result as a list of [start, end] sorted in increasing order. Return ONLY code in a ```python``` block.",
        "reference": r'''def merge_half_open_strict(intervals):
    normalized = []
    for start, end in intervals:
        if start > end:
            start, end = end, start
        if start != end:
            normalized.append([start, end])
    normalized.sort()
    merged = []
    for start, end in normalized:
        if not merged or start >= merged[-1][1]:
            merged.append([start, end])
        else:
            if end > merged[-1][1]:
                merged[-1][1] = end
    return merged
''',
        "tests": [
            [[[]], []],
            [[[[1, 3], [3, 5]]], [[1, 3], [3, 5]]],
            [[[[1, 4], [2, 5]]], [[1, 5]]],
            [[[[5, 1], [2, 3], [3, 3]]], [[1, 5]]],
            [[[[0, 2], [2, 4], [1, 3]]], [[0, 4]]],
            [[[[1, 1], [2, 2], [3, 4]]], [[3, 4]]],
            [[[[-2, 0], [0, 2], [-1, 1]]], [[-2, 2]]],
            [[[[10, 12], [6, 8], [8, 10]]], [[6, 8], [8, 10], [10, 12]]],
            [[[[4, 6], [1, 2], [2, 4], [3, 5]]], [[1, 2], [2, 6]]],
            [[[[7, 3], [5, 9], [9, 11]]], [[3, 9], [9, 11]]],
        ],
        "twists": [
            "intervals are half-open",
            "touching intervals do not merge",
            "reversed endpoints are normalized and zero-length intervals are dropped",
        ],
    },
    {
        "func": "valid_parens_escape",
        "prompt_pl": "Napisz funkcje Python valid_parens_escape(s). Sprawdz, czy nawiasy (), [] i {} sa poprawnie zagniezdzone. Znak backslash \\\\ ucieka nastepny znak: uciekniety znak nie jest traktowany jako nawias, nawet jesli nim jest. Sam backslash na koncu lancucha jest zwyklym znakiem bez znaczenia. Wszystkie inne znaki ignoruj. Zwroc True albo False. Zwroc TYLKO kod w bloku ```python```.",
        "prompt_en": "Write a Python function valid_parens_escape(s). Check whether the brackets (), [] and {} are correctly nested. A backslash \\\\ escapes the next character: the escaped character is not treated as a bracket even if it is one. A lone backslash at the end of the string is just an ordinary irrelevant character. Ignore all other characters. Return True or False. Return ONLY code in a ```python``` block.",
        "reference": r'''def valid_parens_escape(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    opens = set(pairs.values())
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '\\':
            i += 2
            continue
        if ch in opens:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
        i += 1
    return not stack
''',
        "tests": [
            [[""], True],
            [["()[]{}"], True],
            [["([{}])"], True],
            [["([)]"], False],
            [["\\("], True],
            [["(\\))"], True],
            [["(\\)]"], False],
            [["abc{[x](y)}"], True],
            [["abc{[x](y)}]"], False],
            [["{\\}\\}"], False],
            [["["], False],
            [["\\"], True],
        ],
        "twists": [
            "supports three bracket types",
            "backslash escapes the next character",
            "non-bracket characters are ignored",
        ],
    },
]


NAIVE_REFERENCES = {
    "rainwater_v1": CLASSIC_RAINWATER,
    "binary_search_rank": r'''def binary_search_rank(nums, target):
    lo = 0
    hi = len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
    "two_sum_all_1based": r'''def two_sum_all_1based(nums, target):
    seen = {}
    for i, value in enumerate(nums):
        need = target - value
        if need in seen:
            return [seen[need], i]
        seen[value] = i
    return []
''',
    "merge_half_open_strict": r'''def merge_half_open_strict(intervals):
    intervals = sorted([item[:] for item in intervals])
    out = []
    for start, end in intervals:
        if not out or start > out[-1][1]:
            out.append([start, end])
        else:
            out[-1][1] = max(out[-1][1], end)
    return out
''',
    "valid_parens_escape": r'''def valid_parens_escape(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack
''',
}


ADJUDICATION_LINES = [
    "ADJUDICATION rainwater_v1:",
    "  input [0,1,0,2,1,0,1,3,2,1,2,1]",
    "  global-max closed-ring fill gives 22",
    "  ordinary non-circular classic gives 6",
    "  rotate at first tallest bar and run ordinary linear trapping gives 8",
    "  max over all possible seams would give 11",
    "  verdict: old v1 was ambiguous; v2 fixes it by explicitly using the 8-rule",
]


HAND_CHECKS = {
    "rainwater_v1": [
        ([[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], 8, "rotate at 3 -> [3,2,1,2,1,0,1,0,2,1,0,1]"),
        ([[5, 0, 0]], 0, "cut at 5 leaves no right wall for the two zero bars"),
        ([[4, 0, 4, 0, 4]], 8, "both zero bars sit between height-4 walls after the cut"),
    ],
    "binary_search_rank": [
        ([[1, 2, 2, 2, 5], 3], 2, "distinct values <= 3 are 1 and 2"),
        ([[-5, -5, -2, 0, 0, 7], -3], 1, "only -5 is not greater than -3 after collapsing"),
    ],
    "two_sum_all_1based": [
        ([[3, 3, 3], 6], [[1, 2], [1, 3], [2, 3]], "all three index pairs are distinct"),
        ([[1, 1, 2, 2, 3, 3], 4], [[1, 5], [1, 6], [2, 5], [2, 6], [3, 4]], "four 1+3 pairs and one 2+2 pair"),
    ],
    "merge_half_open_strict": [
        ([[[1, 3], [3, 5]]], [[1, 3], [3, 5]], "half-open touching intervals remain separate"),
        ([[[5, 1], [2, 3], [3, 3]]], [[1, 5]], "reversed interval normalizes; zero-length interval drops"),
    ],
    "valid_parens_escape": [
        (["(\\))"], True, "escaped close paren is ignored, final close paren matches"),
        (["(\\)]"], False, "escaped close paren is ignored, ] cannot close ("),
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


def naive_bites(task):
    fn = load_func(NAIVE_REFERENCES[task["func"]], task["func"])
    failures = 0
    examples = []
    for args, expected in task["tests"]:
        try:
            got = normalize(fn(*args))
        except Exception as exc:
            failures += 1
            if len(examples) < 2:
                examples.append(f"{args} raised {type(exc).__name__}")
            continue
        if got != expected:
            failures += 1
            if len(examples) < 2:
                examples.append(f"{args} -> {got}, expected {expected}")
    assert failures > 0, f"naive solution unexpectedly passed all tests for {task['func']}"
    return failures, examples


def assert_prompts():
    pl_suffix = "Zwroc TYLKO kod w bloku ```python```."
    en_suffix = "Return ONLY code in a ```python``` block."
    for task in TASKS:
        assert task["prompt_pl"].isascii(), f"{task['func']} Polish prompt contains non-ASCII"
        assert task["prompt_pl"].endswith(pl_suffix), f"{task['func']} Polish prompt suffix mismatch"
        assert task["prompt_en"].endswith(en_suffix), f"{task['func']} English prompt suffix mismatch"


def assert_hand_checks():
    by_name = {task["func"]: task for task in TASKS}
    for name, checks in HAND_CHECKS.items():
        fn = load_func(by_name[name]["reference"], name)
        for args, expected, reason in checks:
            got = normalize(fn(*args))
            assert got == expected, f"hand-check mismatch for {name}: {reason}; got {got}, expected {expected}"


def assert_adjudication_values():
    height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]

    def trap(values):
        total = 0
        for i, h in enumerate(values):
            left = max(values[: i + 1])
            right = max(values[i:])
            total += max(0, min(left, right) - h)
        return total

    closed = max(height) * len(height) - sum(height)
    rotated_start = height.index(max(height))
    rotated = height[rotated_start:] + height[:rotated_start]
    seam_max = max(trap(height[i:] + height[:i]) for i in range(len(height)))
    assert closed == 22
    assert trap(height) == 6
    assert trap(rotated) == 8
    assert seam_max == 11


def write_candidates():
    out = {
        "family": "mutated_v2",
        "base": "Corrected rainwater plus mutated variants of memorized coding problems",
        "tasks": TASKS,
    }
    path = Path(__file__).with_name("mutated_candidates_v2.json")
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"WROTE {path}")


def main():
    assert_prompts()
    assert_adjudication_values()
    assert_hand_checks()
    if "--write-json" in sys.argv:
        write_candidates()
    for line in ADJUDICATION_LINES:
        print(line)
    for task in TASKS:
        run_tests(task)
        print(f"PASS {task['func']} reference ({len(task['tests'])} tests)")
    for task in TASKS:
        failures, examples = naive_bites(task)
        joined = "; ".join(examples)
        print(f"NAIVE-BITES {task['func']} ({failures}/{len(task['tests'])} failures): {joined}")
    print("SUMMARY all references pass and every task defeats its naive memorized baseline")


if __name__ == "__main__":
    main()
