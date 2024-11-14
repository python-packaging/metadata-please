"""
Reads static values from setup.py when they are simple enough.

With the goal of just getting dependencies, and returning a clear error if we don't understand, this has a simpler

This only reads ~50% of current setup.py, vs dowsing which is more like 80%.

I experimented with a more complex version of this in
[dowsing](https://github.com/python-packaging/dowsing/) with a goal of 100%
coverage of open source
"""

import ast
from typing import Any, Dict, List, Optional


# Copied from orig-index
class ShortCircuitingVisitor(ast.NodeVisitor):
    """
    This visitor behaves more like libcst.CSTVisitor in that a visit_ method
    can return true or false to specify whether children get visited, and the
    visiting of children is not the responsibility of the visit_ method.
    """

    def visit(self, node: ast.AST) -> None:
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        rv = visitor(node)
        if rv:
            self.visit_children(node)

    def visit_children(self, node: ast.AST) -> None:
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)

    def generic_visit(self, node: ast.AST) -> bool:
        return True


class QualifiedNameSaver(ShortCircuitingVisitor):
    """Similar to LibCST's QualifiedNameProvider except simpler and wronger"""

    def __init__(self) -> None:
        super().__init__()
        self.qualified_name_prefixes: Dict[str, str] = {}

    def qualified_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return self.qualified_name(node.value) + "." + node.attr
        elif isinstance(node, ast.Expr):
            return self.qualified_name(node.value)
        elif isinstance(node, ast.Name):
            new = self.qualified_name_prefixes.get(node.id)
            if new:
                return new
            return f"<locals>.{node.id}"
        else:
            raise ValueError(f"Complex expression: {type(node)}")

    def visit_Import(self, node: ast.Import) -> None:
        # .names
        #     alias = (identifier name, identifier? asname)
        for a in node.names:
            self.qualified_name_prefixes[a.asname or a.name] = a.name

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # .identifier / .level
        # .names
        #     alias = (identifier name, identifier? asname)
        if node.module:
            prefix = f"{node.module}."
        else:
            prefix = "." * node.level

        for a in node.names:
            self.qualified_name_prefixes[a.asname or a.name] = prefix + a.name


class Unknown:
    pass


UNKNOWN = Unknown()


class SetupFindingVisitor(QualifiedNameSaver):
    def __init__(self) -> None:
        super().__init__()
        self.setup_call_args: Optional[Dict[str, Any]] = None
        self.setup_call_kwargs: Optional[bool] = None
        self.stack: List[ast.AST] = []

    def locate_assignment_value(self, body: List[ast.AST], name: ast.Name) -> Any:
        for node in body:
            if isinstance(node, ast.Assign):
                if node.targets == [name]:
                    return node.value
        return UNKNOWN

    def visit(self, node: ast.AST) -> Any:
        self.stack.append(node)
        try:
            return super().visit(node)
        finally:
            self.stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        # .func (expr, can just be name)
        # .args
        # .keywords
        try:
            qn = self.qualified_name(node.func)
        except ValueError:
            return
        if qn in ("setuptools.setup", "distutils.setup"):
            self.setup_call_args = d = {}
            self.setup_call_kwargs = False
            # Positional args are rarely used
            for k in node.keywords:
                if not k.arg:
                    self.setup_call_kwargs = True
                else:
                    try:
                        if isinstance(k.value, ast.Name):
                            print(self.stack)
                            for p in self.stack[::-1]:
                                if hasattr(p, "body"):
                                    v = self.locate_assignment_value(p.body, k.value)
                                    if v is not UNKNOWN:
                                        d[k.arg] = ast.literal_eval(v)
                                        break
                            else:
                                raise ValueError("XXX")
                        else:
                            d[k.arg] = ast.literal_eval(k.value)
                    except ValueError:  # malformed node or string...
                        d[k.arg] = UNKNOWN


if __name__ == "__main__":
    import sys
    from pathlib import Path

    mod = ast.parse(Path(sys.argv[1]).read_bytes())
    v = SetupFindingVisitor()
    v.visit(mod)
    print(v.setup_call_args)
