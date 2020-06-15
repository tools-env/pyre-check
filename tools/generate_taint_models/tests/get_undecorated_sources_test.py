# Copyright (c) 2016-present, Facebook, Inc.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


import ast
import unittest
from unittest.mock import MagicMock, patch

from ..get_REST_api_sources import RESTApiSourceGenerator
from ..get_undecorated_sources import (
    UndecoratedSourceGenerator,
    __name__ as undecorated_source_name,
)
from ..model import CallableModel, FunctionDefinitionModel
from .test_functions import TestClass, all_functions, testA, testB


class GetUndecoratedSourcesTest(unittest.TestCase):
    @patch.object(RESTApiSourceGenerator, "generate_models")
    @patch(
        "{}.AnnotatedFreeFunctionWithDecoratorGenerator".format(undecorated_source_name)
    )
    def test_compute_models(
        self,
        mock_annotated_decorator: MagicMock,
        mock_RESTapi_decorator_generate_models: MagicMock,
    ) -> None:
        mock_RESTapi_decorator_generate_models.return_value = {
            CallableModel(
                testA,
                arg="TaintSource[UserControlled]",
                vararg="TaintSource[UserControlled]",
                kwarg="TaintSource[UserControlled]",
            ),
            CallableModel(
                testB,
                arg="TaintSource[UserControlled]",
                vararg="TaintSource[UserControlled]",
                kwarg="TaintSource[UserControlled]",
            ),
            CallableModel(
                TestClass().methodA,
                arg="TaintSource[UserControlled]",
                vararg="TaintSource[UserControlled]",
                kwarg="TaintSource[UserControlled]",
            ),
        }
        generator_instance = MagicMock()
        generator_instance.generate_models.return_value = {
            FunctionDefinitionModel(
                # pyre-ignore: Incompatible parameter type [6]
                ast.parse("def testA(): pass").body[0],
                arg="TaintSource[UserControlled]",
                vararg="TaintSource[UserControlled]",
                kwarg="TaintSource[UserControlled]",
                qualifier="tools.pyre.tools.generate_taint_models.tests.test_functions",
            )
        }
        mock_annotated_decorator.side_effect = [generator_instance]

        self.maxDiff = None
        self.assertEqual(
            {
                *map(
                    str,
                    UndecoratedSourceGenerator(
                        source_generator=RESTApiSourceGenerator(
                            django_urls=MagicMock()
                        ),
                        root="/root",
                        decorators_to_filter=[],
                    ).compute_models(all_functions),
                )
            },
            {
                "def tools.pyre.tools.generate_taint_models.tests.test_functions."
                "TestClass.methodA(self: TaintSource[UserControlled], x: "
                "TaintSource[UserControlled]): ...",
                "def tools.pyre.tools.generate_taint_models.tests.test_functions."
                "testB(x: TaintSource[UserControlled]): ...",
            },
        )
