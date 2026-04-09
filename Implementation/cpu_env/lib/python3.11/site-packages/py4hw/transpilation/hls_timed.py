# -*- coding: utf-8 -*-
"""
Created on Sun Jul 13 06:51:58 2025

@author: 2016570
"""
import ast
import textwrap
import inspect
import copy
from typing import Dict, Any

class YieldFromInliner(ast.NodeTransformer):
    def __init__(self, cls_node):
        self.cls_node = cls_node
        self.inlinable_methods = {}
        self.calls_to_inline = [] # This is primarily for debugging/information in Phase 1
        self.methods_to_remove = set()
        self._phase1_collect_info()
        self.current_function_stack = []

    def _phase1_collect_info(self):
        # print("\n--- Phase 1: Collecting Information ---")
        for node in self.cls_node.body:
            if isinstance(node, ast.FunctionDef):
                self.inlinable_methods[node.name] = node
                # print(f'  Collecting method: {node.name}')

        call_collector = CallSiteCollector(self.inlinable_methods.keys())
        call_collector.visit(self.cls_node)
        self.calls_to_inline = call_collector.collected_calls
        # print(f'  Identified {len(self.calls_to_inline)} potential inlining candidates.')

    def _phase2_apply_inlining(self):
        # print("\n--- Phase 2: Applying Inlining and Removing Functions ---")
        transformed_cls_node = self.visit(self.cls_node) # This kicks off the transformation

        new_class_body = []
        removed_count = 0
        for node in transformed_cls_node.body:
            if isinstance(node, ast.FunctionDef) and node.name in self.methods_to_remove:
                # print(f"  Removing inlined function definition: {node.name}")
                removed_count += 1
                continue
            new_class_body.append(node)
        transformed_cls_node.body = new_class_body
        # print(f"  Removed {removed_count} function definitions.")

        return transformed_cls_node

    def visit_FunctionDef(self, node):
        self.current_function_stack.append(node.name)
        # It's important to process the body recursively here to ensure nested inlines
        # The generic_visit calls visit for each child.
        # However, for function body, we need to manage it to ensure newly inserted
        # statements are also processed.
        
        # We need to manually iterate and visit statements in the body,
        # handling lists returned by visit for inlining.
        new_body = []
        for stmt in node.body:
            transformed_stmt = self.visit(stmt) # Visit each statement
            if isinstance(transformed_stmt, list):
                # If a statement was inlined into multiple statements, extend the list
                new_body.extend(transformed_stmt)
            elif transformed_stmt is not None: # Don't add if node was removed (returned None)
                new_body.append(transformed_stmt)
        node.body = new_body
        
        self.current_function_stack.pop()
        return node

    def visit_Expr(self, node):
        # First, ensure nested expressions are visited
        node = self.generic_visit(node)

        if isinstance(node.value, ast.YieldFrom):
            call = node.value.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                if isinstance(call.func.value, ast.Name) and call.func.value.id == 'self':
                    method_name = call.func.attr
                    if method_name in self.inlinable_methods:
                        if self.current_function_stack and method_name == self.current_function_stack[-1]:
                            raise RecursionError(f"Refusing to inline recursive call to {method_name}")

                        method_node = self.inlinable_methods[method_name]
                        
                        # Deep copy the body of the method being inlined.
                        # Then, RECURSIVELY VISIT EACH STATEMENT IN THE INLINED BODY.
                        # This is the crucial change for nested inlining.
                        transformed_inlined_body = []
                        for stmt in method_node.body:
                            # Visit the statement to handle any further inlining *within* it
                            visited_stmt = self.visit(copy.deepcopy(stmt))
                            if isinstance(visited_stmt, list):
                                transformed_inlined_body.extend(visited_stmt)
                            elif visited_stmt is not None:
                                transformed_inlined_body.append(visited_stmt)

                        # print(f"  Inlining '{method_name}' into '{self.current_function_stack[-1]}'")
                        self.methods_to_remove.add(method_name)
                        return transformed_inlined_body
        return node

    def visit_Return(self, node):
        # This is a placeholder. Real inlining would need to convert
        # 'return value' from an inlined generator into the final value
        # of the 'yield from' expression, which is complex.
        # For simple inlining, you might remove it or transform to 'pass'.
        return self.generic_visit(node)



class YieldStateTransformer(ast.NodeTransformer):
    def __init__(self):
        self.yield_counter = 1

    def visit_ClassDef(self, node):
        # Visit all methods first
        self.generic_visit(node)

        # Check if __init__ method exists
        init_found = False
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                init_found = True
                # Insert self.state = 0 at the beginning of __init__
                assign_stmt = ast.parse("self.state = 0").body[0]
                stmt.body.insert(0, assign_stmt)
                break

        # If __init__ not found, create one with self.state = 0
        if not init_found:
            init_func = ast.FunctionDef(
                name="__init__",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg='self')],
                    vararg=None, kwonlyargs=[], kw_defaults=[],
                    kwarg=None, defaults=[]
                ),
                body=[ast.parse("self.state = 0").body[0]],
                decorator_list=[]
            )
            node.body.insert(0, init_func)

        return node

    def visit_FunctionDef(self, node):
        # Only transform the "run" method
        if node.name == "run":
            self.generic_visit(node)
        return node

    def visit_Yield(self, node):
        # Replace each yield with: self.state = N
        state_assign = ast.Assign(
            targets=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='state', ctx=ast.Store())],
            value=ast.Constant(value=self.yield_counter)
        )
        self.yield_counter += 1
        return state_assign




class CallSiteCollector(ast.NodeVisitor):
    # (No changes needed for CallSiteCollector for this particular fix)
    def __init__(self, inlinable_method_names):
        self.inlinable_method_names = inlinable_method_names
        self.collected_calls = []
        self.current_function_stack = []

    def visit_FunctionDef(self, node):
        self.current_function_stack.append(node.name)
        self.generic_visit(node)
        self.current_function_stack.pop()

    def visit_YieldFrom(self, node):
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
            if isinstance(call.func.value, ast.Name) and call.func.value.id == 'self':
                method_name = call.func.attr
                if method_name in self.inlinable_method_names:
                    if self.current_function_stack:
                        calling_function = self.current_function_stack[-1]
                        self.collected_calls.append((calling_function, method_name, call))
        self.generic_visit(node)


class KeepInitAndClockTransformer(ast.NodeTransformer):
    def visit_ClassDef(self, node):
        # Keep only methods named '__init__' or 'clock'
        node.body = [
            item for item in node.body
            if not isinstance(item, ast.FunctionDef)
            or item.name in ('__init__', 'clock')
        ]
        self.generic_visit(node)
        return node
    
class IOWireDirectoryDetector(ast.NodeVisitor):
    def __init__(self):
        self.input_dir = None
        self.output_dir = None

    def visit_FunctionDef(self, node):
        if node.name != '__init__':
            return  # Only inspect __init__
        for stmt in node.body:
            if isinstance(stmt, ast.For):
                self._process_for_loop(stmt)

    def _process_for_loop(self, node):
        # Check if loop iterates over something like: <dict>.keys()
        if (
            isinstance(node.iter, ast.Call) and
            isinstance(node.iter.func, ast.Attribute) and
            node.iter.func.attr == 'keys' and
            isinstance(node.iter.func.value, ast.Name)
        ):
            dict_var = node.iter.func.value.id  # the dict being iterated over
            for inner_stmt in node.body:
                # Check for: self.addIn(...) or self.addOut(...)
                if isinstance(inner_stmt, ast.Expr):
                    call = inner_stmt.value
                    if (
                        isinstance(call, ast.Call) and
                        isinstance(call.func, ast.Attribute) and
                        isinstance(call.func.value, ast.Name) and
                        call.func.value.id == 'self'
                    ):
                        method = call.func.attr
                        if method == 'addIn' and self.input_dir is None:
                            self.input_dir = dict_var
                        elif method == 'addOut' and self.output_dir is None:
                            self.output_dir = dict_var


class ReplacePrintByPass(ast.NodeTransformer):
        
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        #print('checking call', attr)
        if (attr == 'print'):
            # remove prints
            return ast.Pass()
        
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node


import ast
from typing import Any, Dict, Tuple

# ---------- Helper ----------
def dotted_name_from_attribute(node: ast.Attribute) -> str | None:
    """Return dotted name like 'ALU.OP_INC' or 'pkg.mod.Class.CONST'."""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return '.'.join(reversed(parts))
    return None

class ClassConstantCollector(ast.NodeVisitor):
    def __init__(self, namespace):
        self.constants = {}
        self.current_class = None
        self.namespace = namespace

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Collect class-level constants (case 1)"""
        self.current_class = node.name
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        try:
                            value = ast.literal_eval(item.value)
                            self.constants[f"self.{target.id}"] = value
                        except (ValueError, SyntaxError):
                            pass
        self.generic_visit(node)  # Continue visiting child nodes

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Collect external class constants (case 2)"""
        if isinstance(node.value, ast.Name):
            # Pattern: OtherClass.CONST
            print('Attribute', f"{node.value.id}.{node.attr}")
            try:
                value = eval(f"{node.value.id}.{node.attr}", self.namespace)
                self.constants[f"{node.value.id}.{node.attr}"] = value
            except :
                print('error')
                pass
        elif (isinstance(node.value, ast.Attribute) and 
              isinstance(node.value.value, ast.Name) and 
              node.value.value.id == 'self'):
            # Pattern: self.CONST (already handled in visit_ClassDef)
            pass
        self.generic_visit(node)
        
# ---------- Transformer with eval fallback ----------
class StaticAttributeInliner(ast.NodeTransformer):
    def __init__(
        self,
        ast_constants: Dict[str, Any],
        runtime_namespace: Dict[str, Any],
        allowed_types: Tuple[type, ...] = (int, float, str, bool, tuple)
    ):
        self.constants = dict(ast_constants)
        self.runtime_namespace = runtime_namespace
        self.allowed_types = allowed_types
        self._current_class = None
        self._in_bases = False  # Flag to track if visiting bases

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self._current_class
        self._current_class = node.name

        # First visit bases with flag set
        self._in_bases = True
        for i, base in enumerate(node.bases):
            node.bases[i] = self.visit(base)
        self._in_bases = False

        # Then visit the rest of the body normally
        node.body = [self.visit(stmt) for stmt in node.body]

        self._current_class = prev_class
        return node

    def visit_Attribute(self, node: ast.Attribute):
        # When inside base classes, do not replace anything
        if self._in_bases:
            return self.generic_visit(node)

        self.generic_visit(node)

        # Case 1: self.CONST inside current class
        if isinstance(node.value, ast.Name) and node.value.id == "self" and self._current_class:
            key = f"{self._current_class}.{node.attr}"
            if key in self.constants:
                return ast.copy_location(ast.Constant(value=self.constants[key]), node)

        # Case 2: Class.CONST or module.Class.CONST
        dotted = dotted_name_from_attribute(node)
        if dotted:
            if dotted in self.constants:
                return ast.copy_location(ast.Constant(value=self.constants[dotted]), node)

            parts = dotted.split('.')
            if len(parts) >= 2:
                last_two = '.'.join(parts[-2:])
                if last_two in self.constants:
                    return ast.copy_location(ast.Constant(value=self.constants[last_two]), node)

            try:
                val = eval(dotted, self.runtime_namespace)
                if isinstance(val, self.allowed_types):
                    self.constants[dotted] = val
                    if len(parts) >= 2:
                        self.constants[last_two] = val
                    return ast.copy_location(ast.Constant(value=val), node)
            except Exception:
                pass

        return node


def replaceConstants(tree:ast.AST, clazz):
    # Execute source to create namespace
    module = inspect.getmodule(clazz)
    src = inspect.getsource(module)
    namespace = {}
    
    print(src[0:1000])
    exec(src, namespace)
    
    collector = ClassConstantCollector(namespace)
    collector.visit(tree)

    print('Collected constants', collector.constants)
    transformer = StaticAttributeInliner(collector.constants, globals())
    new_tree = transformer.visit(tree)

    return new_tree

class ScopedSelfAliasRewriter(ast.NodeTransformer):
    def __init__(self):
        self.current_aliases = {}

    def visit_FunctionDef(self, node):
        saved_aliases = self.current_aliases
        self.current_aliases = {}

        node = self.generic_visit(node)

        # Remove alias assignments like a = self.<something>
        new_body = []
        for stmt in node.body:
            if (isinstance(stmt, ast.Assign) and
                len(stmt.targets) == 1 and
                isinstance(stmt.targets[0], ast.Name) and
                self._is_self_expr(stmt.value)):
                continue  # skip alias
            new_body.append(stmt)

        self.current_aliases = saved_aliases
        node.body = new_body
        return node

    def visit_Assign(self, node):
        if (
            len(node.targets) == 1 and
            isinstance(node.targets[0], ast.Name) and
            self._is_self_expr(node.value)
        ):
            alias_name = node.targets[0].id
            self.current_aliases[alias_name] = copy.deepcopy(node.value)
            return None  # remove assignment
        return self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.current_aliases:
            return copy.deepcopy(self.current_aliases[node.id])
        return node

    def _is_self_expr(self, expr):
        """
        Returns True if expr starts from `self`, e.g., self.foo.bar()['x'].baz
        """
        while isinstance(expr, (ast.Attribute, ast.Subscript, ast.Call)):
            if isinstance(expr, ast.Call):
                expr = expr.func
            elif isinstance(expr, ast.Subscript):
                expr = expr.value
            else:  # ast.Attribute
                expr = expr.value
        return isinstance(expr, ast.Name) and expr.id == 'self'



class IODictKeyCollector(ast.NodeVisitor):
    def __init__(self, input_dir_name, output_dir_name, method_name):
        self.input_dir_name = input_dir_name
        self.output_dir_name = output_dir_name
        self.method_name = method_name
        self.input_keys = set()
        self.output_keys = set()

    def visit_FunctionDef(self, node):
        print('checking function ', node.name ,  self.method_name)
        if node.name != self.method_name:
            return
        self.generic_visit(node)

    def visit_Subscript(self, node):
        # Check if we're subscript-ing an attribute like self.status["key"]
        import astunparse
        #print('Checking subscript', astunparse.unparse(node), type(node.value))
        target = node.value
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            if target.value.id == 'self':
                dict_name = target.attr  # e.g., 'status' or 'control'

                # Handle dict["key"] where key is a constant string
                if isinstance(node.slice, ast.Constant):  # Python 3.9+
                    key = node.slice.value
                elif isinstance(node.slice, ast.Index) and isinstance(node.slice.value, ast.Constant):  # pre-3.9
                    key = node.slice.value.value
                else:
                    key = None

                if isinstance(key, str):
                    if dict_name == self.input_dir_name:
                        self.input_keys.add(key)
                    elif dict_name == self.output_dir_name:
                        self.output_keys.add(key)
        self.generic_visit(node)





import itertools

class SSARewriter(ast.NodeTransformer):
    def __init__(self):
        self.counter = itertools.count()
        self.versions = {}  # variable → latest version name
        self.rename_map = {}  # current loads → latest version name

    def visit_Assign(self, node):
        # Only handle simple single-target assignments
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            orig_name = node.targets[0].id

            # Visit RHS first, so it uses the *old* version
            node.value = self.visit(node.value)

            # Then create new version for LHS
            new_name = f"{orig_name}_{next(self.counter)}"
            self.versions[orig_name] = new_name
            self.rename_map[orig_name] = new_name
            node.targets[0].id = new_name
            return node

        return self.generic_visit(node)

    def visit_Name(self, node):
        # For loads, rewrite to latest version
        if isinstance(node.ctx, ast.Load) and node.id in self.rename_map:
            node.id = self.rename_map[node.id]
        return node


class RemoveUnusedAssignments(ast.NodeTransformer):
    def __init__(self):
        self.changed = False
        
    def visit_FunctionDef(self, node):
        self.generic_visit(node)  # process children first

        assigned_vars = set()
        used_vars = set()

        # Collect assignments and uses throughout the entire function
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    for t in ast.walk(target):
                        if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store):
                            assigned_vars.add(t.id)
            elif isinstance(stmt, ast.AnnAssign):
                target = stmt.target
                if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
                    assigned_vars.add(target.id)
            elif isinstance(stmt, ast.Name) and isinstance(stmt.ctx, ast.Load):
                used_vars.add(stmt.id)

        unused_vars = assigned_vars - used_vars
        
        if (len(unused_vars) > 0):
            self.changed = True
            print('ununsed', unused_vars)

        # Now filter out assignments to only-unused variables
        def is_unused_assignment(stmt):
            def extract_names(target):
                if isinstance(target, ast.Name):
                    return [target.id]
                elif isinstance(target, ast.Tuple):
                    return [id for elt in target.elts for id in extract_names(elt)]
                return []
        
            if isinstance(stmt, ast.Assign):
                all_names = []
                for t in stmt.targets:
                    all_names.extend(extract_names(t))
                return all_names and all(name in unused_vars for name in all_names)
        
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name):
                    return stmt.target.id in unused_vars
        
            return False


        class AssignmentCleaner(ast.NodeTransformer):
            def visit_Assign(self, stmt):
                return ast.Pass() if is_unused_assignment(stmt) else stmt

            def visit_AnnAssign(self, stmt):
                return ast.Pass() if is_unused_assignment(stmt) else stmt

        node.body = [AssignmentCleaner().visit(stmt) for stmt in node.body]
        return node


class RemoveIrrelevantConditions(ast.NodeTransformer):
    def visit_If(self, node):
        self.generic_visit(node)  # first transform inside the body

        ret = False
        
        if len(node.body) == 0:
            ret = True
        elif len(node.body) == 1:
            if (isinstance(node.body[0], ast.Pass)):
                ret = True
            elif (isinstance(node.body[0], ast.Expr)) and (isinstance(node.body[0].value, ast.Pass)):
                ret = True
        
        if len(node.orelse) != 0:
            # how could this ever change ?
            ret = False

        if ret :
            return None  

        return node


class ExpandInitLoopTransformer(ast.NodeTransformer):
    def __init__(self, input_dir, output_dir, input_keys, output_keys):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.all_keys = input_keys.union(output_keys)

    def visit_FunctionDef(self, node):
        if node.name == '__init__':
            # Rewrite constructor loops
            new_body = []
            for stmt in node.body:
                if self._is_status_loop(stmt):
                    new_body.extend(self._generate_input_assignments())
                elif self._is_control_loop(stmt):
                    new_body.extend(self._generate_output_assignments())
                else:
                    new_body.append(stmt)
            node.body = new_body
        else:
            # Rewrite Subscript accesses elsewhere (like in clock)
            self.generic_visit(node)
        return node

    def visit_Subscript(self, node):
        # Only replace self.status["key"] or self.control["key"]
        if (
            isinstance(node.value, ast.Attribute) and
            isinstance(node.value.value, ast.Name) and
            node.value.value.id == 'self' and
            node.value.attr in {self.input_dir, self.output_dir}
        ):
            key = None
            if isinstance(node.slice, ast.Constant):  # Python 3.9+
                key = node.slice.value
            elif isinstance(node.slice, ast.Index) and isinstance(node.slice.value, ast.Constant):  # <3.9
                key = node.slice.value.value
            if isinstance(key, str) and key in self.all_keys:
                return ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=key, ctx=node.ctx)
        return self.generic_visit(node)

    def _is_status_loop(self, node):
        return (
            isinstance(node, ast.For) and
            isinstance(node.iter, ast.Call) and
            isinstance(node.iter.func, ast.Attribute) and
            node.iter.func.attr == 'keys' and
            isinstance(node.iter.func.value, ast.Name) and
            node.iter.func.value.id == self.input_dir
        )

    def _is_control_loop(self, node):
        return (
            isinstance(node, ast.For) and
            isinstance(node.iter, ast.Call) and
            isinstance(node.iter.func, ast.Attribute) and
            node.iter.func.attr == 'keys' and
            isinstance(node.iter.func.value, ast.Name) and
            node.iter.func.value.id == self.output_dir
        )

    def _generate_input_assignments(self):
        return [
            ast.Assign(
                targets=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=key, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='addIn', ctx=ast.Load()),
                    args=[
                        ast.Constant(value=key),
                        ast.Subscript(
                            value=ast.Name(id=self.input_dir, ctx=ast.Load()),
                            slice=ast.Constant(value=key),
                            ctx=ast.Load()
                        )
                    ],
                    keywords=[]
                )
            )
            for key in sorted(self.input_keys)
        ]

    def _generate_output_assignments(self):
        return [
            ast.Assign(
                targets=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=key, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='addOut', ctx=ast.Load()),
                    args=[
                        ast.Constant(value=key),
                        ast.Subscript(
                            value=ast.Name(id=self.output_dir, ctx=ast.Load()),
                            slice=ast.Constant(value=key),
                            ctx=ast.Load()
                        )
                    ],
                    keywords=[]
                )
            )
            for key in sorted(self.output_keys)
        ]



def getClassTree(cls: type) -> ast.AST:
    """
    Transforms a generator-based class's 'run' method into a state machine 'clock' method.

    Args:
        cls: The class object to transform.

    Returns:
        The AST of the class
    """
    if not isinstance(cls, type):
        raise TypeError("Expected a class object")

    try:
        source = inspect.getsource(cls)
    except Exception as e:
        raise ValueError(f"Could not retrieve source for {cls.__name__}: {e}")

    source = textwrap.dedent(source)
    tree = ast.parse(source)
    
    class_node = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls.__name__), None)
    if class_node is None:
        raise ValueError(f"Class {cls.__name__} not found in AST.")


    return class_node

# --- Helper function to apply the transformer ---
def transform_generator_to_fsm(class_node: ast.AST) -> ast.AST:

    #print(astunparse.unparse(class_node))

    transformer = GeneratorToFSMTransformer()
    tree = transformer.visit(class_node)

    #for i, node in enumerate(tree.body):
    #    if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
    #        tree.body[i] = transformed_class_node
    #        break

    ast.fix_missing_locations(tree)
    
    return tree
    #return astunparse.unparse(tree)


def removeUnusedAssignments(tree: ast.AST) -> ast.AST:
    tr = RemoveUnusedAssignments()
    doRun = True
    while doRun:
        tr.changed = False 
        tree = tr.visit(tree)
        doRun = tr.changed

    return tree

def inline_yield_from(class_node: ast.AST) -> ast.AST:
   

    # Phase 1: Initialize the transformer, which collects information
    transformer = YieldFromInliner(class_node)

    # Phase 2: Apply the transformations and remove the inlined functions
    # The _phase2_apply_inlining method itself performs the visit operation internally
    tree = transformer._phase2_apply_inlining()

    # Replace the original class_node in the tree with the transformed one
    #for i, node in enumerate(tree.body):
    #    if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
    #        tree.body[i] = transformed_class_node
    #        break

    # Fix line numbers and other metadata in the AST
    ast.fix_missing_locations(tree)

    # Convert back to code
    #return astunparse.unparse(tree)
    return tree

def yield_to_state(class_node: ast.AST) -> ast.AST:
    tr = YieldStateTransformer()
    tree = tr.visit(class_node)
    ast.fix_missing_locations(tree)
    return tree



class ReplaceIfElseTreeByMatchCase(ast.NodeTransformer):
    """Transforms if/elif chains on the same variable into a match/case AST."""

    def visit_If(self, node):
        match_node = self.try_match_if_chain(node)
        if match_node:
            return match_node
        return self.generic_visit(node)

    def try_match_if_chain(self, node):
        var_expr = None
        case_list = []
        default_body = None
        cur = node

        while True:
            # Must be a Compare node
            if not isinstance(cur.test, ast.Compare):
                return None
            cmp = cur.test

            # Check '==' and single comparator
            if len(cmp.ops) != 1 or not isinstance(cmp.ops[0], ast.Eq):
                return None
            if len(cmp.comparators) != 1:
                return None

            lhs = cmp.left
            rhs = cmp.comparators[0]

            # First branch: store the variable expression
            if var_expr is None:
                var_expr = lhs
            elif ast.dump(var_expr) != ast.dump(lhs):
                return None  # expression differs

            # Create a MatchValue pattern
            pattern = ast.MatchValue(value=rhs)
            case_list.append(ast.match_case(pattern=pattern, guard=None, body=cur.body))

            # Go to elif
            if len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]
            else:
                if cur.orelse:
                    default_body = cur.orelse
                break

        if len(case_list) >= 2:
            if default_body:
                case_list.append(
                    ast.match_case(
                        pattern=ast.MatchAs(name=None),  # case _
                        guard=None,
                        body=default_body
                    )
                )
            return ast.Match(subject=var_expr, cases=case_list)

        return None
