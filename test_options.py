#!/usr/bin/env python3
import unittest

from _common import _parse_option_value, parse_options
from run_bench import option_flags


class TestOptionParsing(unittest.TestCase):
    def test_parse_option_value_types(self):
        self.assertIs(_parse_option_value("true"), True)
        self.assertIs(_parse_option_value("false"), False)
        self.assertEqual(_parse_option_value("8192"), 8192)
        self.assertEqual(_parse_option_value("1.0"), 1.0)
        self.assertEqual(_parse_option_value("abc"), "abc")

    def test_parse_options_happy_path(self):
        opts = parse_options([
            "--option=temperature=1.0",
            "--option=top_p=0.95",
            "--option=top_k=20",
        ])
        self.assertEqual(opts, {"temperature": 1.0, "top_p": 0.95, "top_k": 20})

    def test_parse_options_rejects_malformed(self):
        bad_args = [
            "--option=temperature",
            "--option==1.0",
            "--option=temperature=",
            "--option=temperatur=1.0",
            "--option=num_predict=3000",
            "--option=think=true",
        ]
        for arg in bad_args:
            with self.subTest(arg=arg):
                with self.assertRaises(ValueError):
                    parse_options([arg])

    def test_parse_options_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            parse_options(["--option=temperature=0.7", "--option=temperature=1.0"])

    def test_option_flags_round_trip(self):
        cfg = {"think": "high", "num_predict": 6000, "temperature": 1.0, "top_p": 0.95}
        self.assertEqual(
            parse_options(option_flags(cfg)),
            {"temperature": 1.0, "top_p": 0.95},
        )

    def test_option_flags_rejects_unknown_task_key(self):
        with self.assertRaises(ValueError):
            option_flags({"think": "false", "num_predict": 3000, "note": "not an Ollama option"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
