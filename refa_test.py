from lib2to3.fixer_base import BaseFix
from lib2to3.refactor import RefactoringTool
from lib2to3.pytree import Node, Leaf
from lib2to3.pgen2 import token


class TestFixer(BaseFix):
    PATTERN = """
    classdef<any*>
    """

    def transform(self, node, results):
        node.children.extend([Leaf(token.INDENT, '    '), Leaf(token.COMMENT, 'b = 32')])


class Refa(RefactoringTool):
    def get_fixers(self):
        return ([], [TestFixer(self.options, self.fixer_log)])


rf = Refa([])

print(rf.refactor_string(
    """
class Blah:
    a = 12
    def b(self):
        print("c")
    """, 'a'))
