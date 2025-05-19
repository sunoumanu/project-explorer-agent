import ast

def dump_python_ast(source_code: str) -> str:
    """
    Parses Python source code and returns a string representation of its AST.

    Args:
        source_code: A string containing the Python source code.

    Returns:
        A string representing the AST, formatted with an indent of 4.
        Returns an error message string if parsing fails.
    """
    try:
        # Parse the source code into an AST
        tree = ast.parse(source_code)
        # Dump the AST with an indent of 4
        # ast.dump returns a string representation of the tree
        # The 'indent' parameter was added in Python 3.9
        # For older versions, ast.dump(tree, annotate_fields=True, include_attributes=False)
        # would be used, but it doesn't have the 'indent' pretty-printing.
        # Modern ast.dump with indent is much more readable.
        return ast.dump(tree, indent=4)
    except SyntaxError as e:
        return f"SyntaxError during parsing: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"