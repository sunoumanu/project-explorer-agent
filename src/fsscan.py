import os
import stat
import hashlib

def get_file_extension(file_name: str) -> str | None:
    """
    Parses a file name and returns its extension without the leading dot.

    Args:
        file_name: The name of the file (e.g., "document.txt", "archive.tar.gz").

    Returns:
        The file extension without the leading dot (e.g., "txt", "gz").
        Returns an empty string if the file has no extension or
        if the file name starts with a dot and has no other dots (e.g., ".bashrc" would return "").
        Returns the part after the last dot if multiple dots are present (e.g., "archive.tar.gz" returns "gz").
    """
    if not isinstance(file_name, str):
        raise TypeError("Input must be a string.")

    # os.path.splitext splits the path into a pair (root, ext)
    # For example, splitext("mydoc.txt") returns ("mydoc", ".txt")
    # If there's no dot, or if it's the first character, ext will be empty.
    # e.g. splitext("nodot") -> ("nodot", "")
    # e.g. splitext(".bashrc") -> (".bashrc", "") - special case for dotfiles
    # e.g. splitext("archive.tar.gz") -> ("archive.tar", ".gz")
    root, extension_with_dot = os.path.splitext(file_name)

    # Handle cases like ".bashrc" where splitext returns (".bashrc", "")
    # In such cases, we consider it as having no extension part to return.
    # However, if the filename is just "." or "..", it should also have no extension.
    if not extension_with_dot and file_name.startswith('.') and file_name != '.' and file_name != '..':
        # If the original filename started with a dot and splitext returned an empty extension,
        # it means it was a "dotfile" without a further extension part (e.g., ".bashrc").
        # We want to return "" in this case, not "bashrc".
        # If we simply sliced extension_with_dot[1:], it would be an error on empty string.
        return None

    # If an extension exists (e.g., ".txt"), return it without the leading dot.
    if extension_with_dot:
        return extension_with_dot[1:]
    else:
        # No extension found (e.g., "filename" or "filename.")
        return None

def get_file_size_in_bytes(file_path):
    """
    Calculates the size of a file in bytes.

    Args:
        file_path (str): The path to the file.

    Returns:
        int: The size of the file in bytes, or None if an error occurs.
    """
    try:
        # Check if the path exists and is a file
        if not os.path.exists(file_path):
            print(f"Error: File not found at '{file_path}'")
            return None
        if not os.path.isfile(file_path):
            print(f"Error: '{file_path}' is a directory, not a file.")
            return None

        # Get the file size in bytes
        file_size = os.path.getsize(file_path)
        return file_size
    except OSError as e:
        # Handle potential OS-related errors (e.g., permission issues)
        print(f"Error accessing file '{file_path}': {e}")
        return None
    except Exception as e:
        # Handle any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return None

def read_file_to_string(filepath: str) -> str | None:
    """
    Reads the content of a text file into a string.

    Args:
        filepath: The path to the text file.

    Returns:
        The content of the file as a string, or None if an error occurs.
    """
    try:
        # Open the file in read mode ('r') with UTF-8 encoding (common for text files)
        with open(filepath, 'r', encoding='utf-8') as file:
            # Read the entire content of the file
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None
    except PermissionError:
        print(f"Error: Permission denied when trying to read '{filepath}'.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def calculate_file_checksum(file_path, hash_algorithm="sha256", chunk_size=4096):
    """
    Calculates the checksum of a file using the specified hash algorithm.

    Args:
        file_path (str): The path to the file.
        hash_algorithm (str, optional): The hash algorithm to use (e.g., "md5", "sha1", "sha256", "sha512").
                                         Defaults to "sha256".
        chunk_size (int, optional): The size of chunks to read from the file (in bytes).
                                    Defaults to 4096.

    Returns:
        str: The hexadecimal representation of the file's checksum.
             Returns None if the file is not found or an error occurs.
    """
    # Ensure the hash algorithm is supported by hashlib
    if not hasattr(hashlib, hash_algorithm):
        print(f"Error: Unsupported hash algorithm '{hash_algorithm}'.")
        print(f"Supported algorithms: {hashlib.algorithms_available}")
        return None

    # Create a hash object
    hasher = hashlib.new(hash_algorithm)

    try:
        # Open the file in binary read mode
        with open(file_path, 'rb') as f:
            while True:
                # Read a chunk of the file
                chunk = f.read(chunk_size)
                if not chunk:
                    # End of file
                    break
                # Update the hash object with the chunk
                hasher.update(chunk)
        # Return the hexadecimal representation of the digest
        return hasher.hexdigest()
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def print_directory_tree(root_dir, indent_char='|   ', file_prefix='|-- ', dir_prefix='+-- '):
    """Prints a directory tree structure."""
    tree = ""
    for root, dirs, files in os.walk(root_dir):
        level = root.replace(root_dir, '').count(os.sep)
        indent = indent_char * level
        tree = tree + f"{indent}{dir_prefix}{os.path.basename(root)}/\n"

        sub_indent = indent_char * (level + 1)
        for f in files:
            tree = tree + f"{sub_indent}{file_prefix}{f}\n"

    return tree

def get_folder_tree(root_folder_path):
    """
    Generates a tree structure of files and folders for a given path.

    Args:
        root_folder_path (str): The absolute or relative path to the folder.

    Returns:
        list: A list of dictionaries, where each dictionary represents a file or folder
              in the root_folder_path. For directories, a 'children' key will contain
              a list of its contents. Returns None if the path is invalid.
    """
    abs_root_path = os.path.abspath(root_folder_path)

    if not os.path.exists(abs_root_path):
        print(f"Error: Path '{root_folder_path}' does not exist.")
        return None
    if not os.path.isdir(abs_root_path):
        print(f"Error: Path '{root_folder_path}' is not a directory.")
        return None

    def _get_permissions(item_path):
        """Helper function to get permissions in a human-readable format."""
        try:
            mode = os.stat(item_path).st_mode
            return stat.filemode(mode)
        except OSError as e:
            # Handle cases like permission denied for os.stat()
            print(f"Warning: Could not get permissions for {item_path}: {e}")
            return "Permission denied or error"

    def _build_tree_recursive(current_dir_path, base_path, tree_nodes = None):
        """
        Recursively builds the tree structure for the current directory.
        """
        if tree_nodes is None:
            tree_nodes = []
        try:
            for item_name in os.listdir(current_dir_path):
                full_path = os.path.join(current_dir_path, item_name)

                # Ensure relative_path is calculated correctly even for the top-level items
                if current_dir_path == base_path:
                    relative_path = item_name
                else:
                    relative_path = os.path.relpath(full_path, base_path)

                permissions = _get_permissions(full_path)
                checksum = calculate_file_checksum(full_path)
                content = read_file_to_string(full_path)
                filesize = get_file_size_in_bytes(full_path)
                extension = get_file_extension(item_name)

                node = {
                    "name": item_name,
                    "full_path": full_path,
                    "relative_path": relative_path,
                    "permissions": permissions,
                    "checksum": checksum,
                    "size": filesize,
                    "extension": extension,
                    "content": content
                }

                if os.path.isdir(full_path):
                    node["type"] = "directory"
                    # Recursively call for subdirectories
                    _build_tree_recursive(full_path, base_path, tree_nodes)
                elif os.path.isfile(full_path):
                    node["type"] = "file"
                else:  # Symlinks, special files, etc.
                    node["type"] = "other"

                tree_nodes.append(node)
        except PermissionError:
            print(f"Warning: Permission denied to access directory {current_dir_path}")
            # Optionally, add a node indicating restricted access
            tree_nodes.append({
                "name": os.path.basename(current_dir_path),
                "full_path": current_dir_path,
                "relative_path": os.path.relpath(current_dir_path,
                                                 base_path) if current_dir_path != base_path else os.path.basename(
                    current_dir_path),
                "permissions": "d????????? (Permission Denied)",
                "type": "directory_inaccessible",
                "children": []
            })
        except OSError as e:
            print(f"Warning: Could not list directory {current_dir_path}: {e}")

        return tree_nodes

    # Start building the tree from the root folder itself, but return its contents
    # The user expects a tree *of* files and folders *within* the input path,
    # not a single root node representing the input path itself.
    # So, we directly call _build_tree_recursive on the abs_root_path.
    return _build_tree_recursive(abs_root_path, abs_root_path)


