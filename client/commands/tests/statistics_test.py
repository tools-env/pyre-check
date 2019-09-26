# Copyright (c) 2016-present, Facebook, Inc.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

import textwrap
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Dict

from libcst import Module, parse_module

from ... import commands  # noqa
from ..statistics import AnnotationCountCollector, FixmeCountCollector, _find_paths
from .command_test import mock_arguments


class StatisticsTest(unittest.TestCase):
    def test_find_targets(self) -> None:
        arguments = mock_arguments()
        arguments.filter_paths = []
        arguments.local_configuration = "example/path/client"
        self.assertEqual(
            _find_paths(arguments.local_configuration, arguments.filter_paths),
            [Path("example/path/client")],
        )

        arguments.local_configuration = "example/path/client/.pyre_configuration.local"
        self.assertEqual(
            _find_paths(arguments.local_configuration, arguments.filter_paths),
            [Path("example/path/client")],
        )

        arguments.filter_paths = ["a.py", "b.py"]
        self.assertEqual(
            _find_paths(arguments.local_configuration, arguments.filter_paths),
            [Path("example/path/client/a.py"), Path("example/path/client/b.py")],
        )


class AnnotationCountCollectorTest(unittest.TestCase):
    @staticmethod
    def format_files(source: str) -> Module:
        return parse_module(textwrap.dedent(source.rstrip()))

    def assert_counts(self, source: str, expected: Dict[str, int]) -> None:
        source_module = self.format_files(source)
        collector = AnnotationCountCollector()
        source_module.visit(collector)
        self.assertEqual(collector.build_json(), expected)

    def test_annotate_functions(self) -> None:
        self.assert_counts(
            """
            def foo(x) -> int:
                pass
            """,
            {
                "annotated_return_count": 1,
                "annotated_globals_count": 0,
                "annotated_parameter_count": 0,
                "return_count": 1,
                "globals_count": 0,
                "parameter_count": 1,
            },
        )

        self.assert_counts(
            """
            def bar(x: int, y):
                pass
            """,
            {
                "annotated_return_count": 0,
                "annotated_globals_count": 0,
                "annotated_parameter_count": 1,
                "return_count": 1,
                "globals_count": 0,
                "parameter_count": 2,
            },
        )

        self.assert_counts(
            """
            a = foo()
            b: int = bar()
            """,
            {
                "annotated_return_count": 0,
                "annotated_globals_count": 1,
                "annotated_parameter_count": 0,
                "return_count": 0,
                "globals_count": 2,
                "parameter_count": 0,
            },
        )


class FixmeCountCollectorTest(unittest.TestCase):
    @staticmethod
    def format_files(source: str) -> Module:
        return parse_module(textwrap.dedent(source.rstrip()))

    def assert_counts(self, source: str, expected: Dict[str, int]) -> None:
        source_module = self.format_files(source)
        collector = FixmeCountCollector(defaultdict(int))
        source_module.visit(collector)
        self.assertEqual(collector.build_json(), expected)

    def test_annotate_functions(self) -> None:
        self.assert_counts("# pyre-fixme[2]: Example Error Message", {"2": 1})
        self.assert_counts(
            "# pyre-fixme[3]: Example Error Message \n\n\n # pyre-fixme[34]: Example",
            {"3": 1, "34": 1},
        )
        self.assert_counts(
            "# pyre-fixme[2]: Example Error Message\n\n\n# pyre-fixme[2]: message",
            {"2": 2},
        )
