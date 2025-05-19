# test_ast_dumper.py
import unittest
import ast

from src.sources import dump_python_ast


class TestDumpPythonAST(unittest.TestCase):

    def assert_ast_dump_equals(self, source_code, expected_dump_str):
        """Helper method to compare AST dump output, ignoring potential minor whitespace differences at line ends."""
        actual_dump = dump_python_ast(source_code)
        # Normalize newlines and strip trailing whitespace from each line for robust comparison
        normalized_actual = "\n".join(line.rstrip() for line in actual_dump.splitlines())
        normalized_expected = "\n".join(line.rstrip() for line in expected_dump_str.splitlines())
        self.assertEqual(normalized_actual, normalized_expected)

    def test_empty_string(self):
        """Test with an empty string input."""
        source_code = ""
        expected_ast = ast.dump(ast.parse(source_code), indent=4)
        self.assert_ast_dump_equals(source_code, expected_ast)

    def test_simple_assignment(self):
        """Test a simple assignment statement."""
        source_code = "x = 10"
        # Generate the expected AST string using ast.parse and ast.dump directly
        # This ensures the test is based on the current Python version's ast.dump behavior
        tree = ast.parse(source_code)
        expected_ast = ast.dump(tree, indent=4)
        self.assert_ast_dump_equals(source_code, expected_ast)

    def test_function_definition(self):
        """Test a simple function definition."""
        source_code = "def my_func(a, b):\n    return a + b"
        tree = ast.parse(source_code)
        expected_ast = ast.dump(tree, indent=4)
        self.assert_ast_dump_equals(source_code, expected_ast)

    def test_expression(self):
        """Test a simple expression."""
        source_code = "1 + 2 * (3 - 1)"
        tree = ast.parse(source_code)
        expected_ast = ast.dump(tree, indent=4)
        self.assert_ast_dump_equals(source_code, expected_ast)

    def test_syntax_error_missing_colon(self):
        """Test code with a syntax error (missing colon in function definition)."""
        source_code = "def my_func(a, b)\n    return a + b"
        result = dump_python_ast(source_code)
        self.assertTrue(result.startswith("SyntaxError during parsing:"))
        # Check for a more specific part of the error message if desired,
        # but be mindful that error messages can change slightly between Python versions.
        # Example: self.assertIn("invalid syntax", result) # or expected ':'

    def test_syntax_error_invalid_operator(self):
        """Test code with a different syntax error (invalid operator)."""
        source_code = "a = 1 ++ 2" # In some contexts this might be valid, but basic parsing would differ
                                # Let's use something more clearly a syntax error
        source_code_error = "a = 1 then 2"
        result = dump_python_ast(source_code_error)
        self.assertTrue(result.startswith("SyntaxError during parsing:"))
        self.assertIn("invalid syntax", result.lower())


    def test_complex_code_sample(self):
        """Test with the more complex sample code provided in the original script."""
        source_code = """
def greet(name):
    message = "Hello, " + name + "!"
    print(message)
    return len(message)

x = greet("World")
"""
        tree = ast.parse(source_code)
        expected_ast = ast.dump(tree, indent=4)
        self.assert_ast_dump_equals(source_code, expected_ast)

    def test_code_with_comments_and_docstrings(self):
        """Test code that includes comments and docstrings."""
        source_code = '''
# This is a comment
def foo():
    """This is a docstring."""
    pass # Another comment

x = 1 # Inline comment
'''
        # Comments are generally not part of the AST nodes themselves,
        # but docstrings are (as Constant nodes).
        # ast.parse handles comments correctly by ignoring them for the tree structure.
        tree = ast.parse(source_code)
        expected_ast = ast.dump(tree, indent=4)
        self.assert_ast_dump_equals(source_code, expected_ast)
        # We can also check if the docstring is present in the AST dump
        self.assertIn("Constant(value='This is a docstring.')", expected_ast)


    def test_class_definition(self):
        """Test a simple class definition."""
        source_code = """
class MyClass:
    def __init__(self, value):
        self.value = value
    def get_value(self):
        return self.value
"""
        tree = ast.parse(source_code)
        expected_ast = ast.dump(tree, indent=4)
        self.assert_ast_dump_equals(source_code, expected_ast)

    # The generic "An unexpected error occurred" is hard to trigger reliably
    # without mocking internal ast module functions or finding a very obscure bug.
    # For practical purposes, testing SyntaxError and valid inputs covers most cases.

if __name__ == '__main__':
    unittest.main()