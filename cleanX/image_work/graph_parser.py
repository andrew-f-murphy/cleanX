# -*- coding: utf-8 -*-

import ast
import importlib

from collections import namedtuple, Counter

from lark import Lark, Transformer, v_args


class MissingDefinition(LookupError):

    def __init__(self, missing):
        super().__init__('Missing definition for {}'.format(missing))


class DuplicateVariables(ValueError):

    def __init__(self, duplicates):
        super().__init__('Found duplicate variables: {}'.format(duplicates))


StepCall = namedtuple('StepCall', 'definition,options,variables')
PipelineDef = namedtuple('PipelineDef', 'steps,goal')


cleanx_grammar = """
    ?start: pipeline -> create_pipeline
    ?pipeline: "pipeline" "(" definitions steps goal ")" -> pipeline
    ?definitions: "definitions" "(" dassign+ ")" -> definitions
    ?steps: "steps" "(" sassign+ ")" -> steps
    ?goal: "goal" "(" step ")" -> goal
    ?dassign: var "=" src -> dassign
    ?var: NAME
    ?src: module ":" def -> src
    ?module: NAME ("." NAME)*
    ?def: NAME
    ?sassign: var+ "=" step -> sassign
    ?step: var options? "(" var* ")" -> step
    ?options: "[" oassign+ "]" -> options
    ?oassign: var "=" val -> oassign
    ?val: number
        | string
        | boolean
        | null
        | list
    ?number: NUMBER -> number
    ?string: STRING -> string
    ?null: "null" -> null
    ?boolean: /true|false/ -> boolean
    ?list: "(" val* ")"
    COMMENT: /#.*$/

    %import common.ESCAPED_STRING -> STRING
    %import common.SIGNED_NUMBER -> NUMBER
    %import common.CNAME -> NAME
    %import common.WS
    %ignore COMMENT
    %ignore WS
"""


@v_args(inline=True)
class Parser(Transformer):
    '''
    Example:

    ::

        pipeline(
            definitions(
                dir = cleanX.source:Dir
                glob = cleanX.source:Glob
                acquire = cleanX.steps:Acquire
                or = cleanX.steps:Or
                crop = cleanX.steps:Crop
            )
            steps(
                source1 = dir[path = "/foo/bar"]()
                source2 = glob[pattern = "/foo/*.jpg"]()

                out1 out2 out3 = acquire[arg1 = "foo" arg2 = 42](
                    source1 source2
                )
                out4 = or[arg1 = true](out1 out2)
                out5 = crop(out3 out4)
            )
            goal(
                save[path = "/foo/bar"](out5)
            )
        )
    '''

    def __init__(self):
        self.lark = Lark(
            cleanx_grammar,
            parser='lalr',
            transformer=self,
        )
        self._definitions = {}
        self._variables = {}

    def parse(self, stream):
        return self.lark.parse(stream).children[0]

    def number(self, n):
        return ast.literal_eval(n)

    def string(self, s):
        return ast.literal_eval(s)

    def null(self):
        return None

    def boolean(self, b):
        return b == 'true'

    def src(self, module, definition):
        mod = importlib.import_module('.'.join(module.children))
        return getattr(mod, definition)

    def dassign(self, name, definition):
        self._definitions[str(name)] = definition
        return definition

    def oassign(self, name, value):
        return str(name), value

    def options(self, *raw):
        return dict(raw)

    def step(self, *args):
        try:
            definition = self._definitions[args[0]]
        except KeyError:
            raise MissingDefinition(args[0])
        args = args[1:]
        if args and (type(args[0]) is dict):
            options = args[0]
            args = args[1:]
        else:
            options = {}
        if args:
            variables = tuple(str(s) for s in args)
        else:
            variables = ()
        # TODO(wvxvw): Here we could validate optional arguments to
        # steps.
        return StepCall(definition, options, variables)

    def sassign(self, *args):
        variables = tuple(str(s) for s in args[:-1])
        duplicates = []
        for var, count in Counter(variables).most_common():
            if count == 1:
                break
            duplicates.append(var)

        for v in variables:
            if v in self._variables:
                duplicates.append(v)
        if duplicates:
            raise DuplicateVariables(duplicates)
        for v in variables:
            self._variables[v] = args[-1]
        return args[-1]

    def pipeline(self, *args):
        # TODO(wvxvw): Here we could check for unused definitions, but
        # it's not very important for now.
        return PipelineDef(self._variables, args[-1].children[0])
