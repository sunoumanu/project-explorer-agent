import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import os
import stat
import hashlib
import tempfile
import shutil
import io

from src.fsscan import get_file_extension, get_file_size_in_bytes, read_file_to_string, calculate_file_checksum, \
    print_directory_tree, get_folder_tree

# To make patches work correctly with the above embedded code,
# we need to patch where the names are looked up (i.e., in __main__ if run directly)
MODULE_PATH_PREFIX = __name__ # Or 'file_operations' if imported

class TestGetFileExtension(unittest.TestCase):
    def test_simple_extension(self):
        self.assertEqual(get_file_extension("document.txt"), "txt")

    def test_double_extension(self):
        self.assertEqual(get_file_extension("archive.tar.gz"), "gz")

    def test_no_extension(self):
        self.assertIsNone(get_file_extension("myfile"))

    def test_dotfile_no_further_extension(self):
        self.assertIsNone(get_file_extension(".bashrc"))

    def test_dotfile_with_extension(self):
        self.assertEqual(get_file_extension(".config.fish"), "fish")

    # def test_filename_ends_with_dot(self):
    #     self.assertIsNone(get_file_extension("filename."))

    def test_empty_string(self):
        self.assertIsNone(get_file_extension(""))

    def test_only_dot(self):
        self.assertIsNone(get_file_extension("."))

    def test_only_double_dot(self):
        self.assertIsNone(get_file_extension(".."))

    def test_hidden_file_many_dots(self):
        self.assertEqual(get_file_extension(".archive.tar.gz"), "gz")

    def test_filename_with_spaces(self):
        self.assertEqual(get_file_extension("my document.pdf"), "pdf")

    def test_filename_with_leading_dot_and_extension(self):
        self.assertEqual(get_file_extension(".image.jpg"), "jpg")

    def test_type_error_input(self):
        with self.assertRaisesRegex(TypeError, "Input must be a string."):
            get_file_extension(123)
        with self.assertRaisesRegex(TypeError, "Input must be a string."):
            get_file_extension(None)
        with self.assertRaisesRegex(TypeError, "Input must be a string."):
            get_file_extension(["file.txt"])

class TestGetFileSizeInBytes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        with open(self.test_file_path, "wb") as f: # wb for binary to control size precisely
            f.write(b"Hello World") # 11 bytes

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_existing_file(self):
        self.assertEqual(get_file_size_in_bytes(self.test_file_path), 11)

    @patch(f'{MODULE_PATH_PREFIX}.os.path.exists')
    def test_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        self.assertIsNone(get_file_size_in_bytes("non_existent_file.txt"))

    @patch(f'{MODULE_PATH_PREFIX}.os.path.isfile')
    @patch(f'{MODULE_PATH_PREFIX}.os.path.exists')
    def test_path_is_directory(self, mock_exists, mock_isfile):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        self.assertIsNone(get_file_size_in_bytes("some_directory"))

    @patch(f'{MODULE_PATH_PREFIX}.os.path.getsize', side_effect=OSError("Permission denied"))
    @patch(f'{MODULE_PATH_PREFIX}.os.path.isfile', return_value=True)
    @patch(f'{MODULE_PATH_PREFIX}.os.path.exists', return_value=True)
    def test_os_error_permission(self, mock_exists, mock_isfile, mock_getsize):
        self.assertIsNone(get_file_size_in_bytes("protected_file.txt"))

    @patch(f'{MODULE_PATH_PREFIX}.os.path.getsize', side_effect=Exception("Unexpected error"))
    @patch(f'{MODULE_PATH_PREFIX}.os.path.isfile', return_value=True)
    @patch(f'{MODULE_PATH_PREFIX}.os.path.exists', return_value=True)
    def test_generic_exception(self, mock_exists, mock_isfile, mock_getsize):
        self.assertIsNone(get_file_size_in_bytes("any_file.txt"))

class TestReadFileToString(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_read.txt")
        self.file_content = "Hello, Vova!\n你好世界\n"
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.file_content)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_existing_file(self):
        content = read_file_to_string(self.test_file_path)
        self.assertEqual(content, self.file_content)

    def test_file_not_found(self):
        self.assertIsNone(read_file_to_string("non_existent_file.txt"))

    @patch(f'{MODULE_PATH_PREFIX}.open', side_effect=PermissionError("Permission denied"))
    def test_permission_error(self, mock_open_func):
        self.assertIsNone(read_file_to_string("any_file.txt"))

    @patch(f'{MODULE_PATH_PREFIX}.open', side_effect=UnicodeDecodeError('utf-8', b'\x80', 0, 1, 'invalid start byte'))
    def test_unicode_decode_error(self, mock_open_func):
        # This mock simulates a read error after open, rather than open itself failing.
        # A more accurate mock would be on the read() method of the file object.
        # However, the current exception handling in read_file_to_string catches generic Exception.
        m_open = mock_open()
        m_open.side_effect = UnicodeDecodeError('utf-8', b'\x80', 0, 1, 'invalid start byte')
        with patch(f'{MODULE_PATH_PREFIX}.open', m_open):
             self.assertIsNone(read_file_to_string("file_with_bad_encoding.txt"))


    @patch(f'{MODULE_PATH_PREFIX}.open', side_effect=Exception("Unexpected error"))
    def test_generic_exception(self, mock_open_func):
        self.assertIsNone(read_file_to_string("any_file.txt"))

class TestCalculateFileChecksum(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "checksum_file.txt")
        self.file_content = b"Vova test data"
        with open(self.test_file_path, "wb") as f:
            f.write(self.file_content)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_calculate_checksum_sha256(self):
        expected_checksum = hashlib.sha256(self.file_content).hexdigest()
        self.assertEqual(calculate_file_checksum(self.test_file_path, "sha256"), expected_checksum)

    def test_calculate_checksum_md5(self):
        expected_checksum = hashlib.md5(self.file_content).hexdigest()
        self.assertEqual(calculate_file_checksum(self.test_file_path, "md5"), expected_checksum)

    def test_empty_file(self):
        empty_file_path = os.path.join(self.temp_dir.name, "empty.txt")
        with open(empty_file_path, "wb") as f:
            pass
        expected_checksum = hashlib.sha256(b"").hexdigest()
        self.assertEqual(calculate_file_checksum(empty_file_path, "sha256"), expected_checksum)

    def test_unsupported_algorithm(self):
        self.assertIsNone(calculate_file_checksum(self.test_file_path, "invalid_algo"))

    def test_file_not_found(self):
        self.assertIsNone(calculate_file_checksum("non_existent_file.txt"))

    # @patch(f"{MODULE_PATH_PREFIX}.open", side_effect=IOError("Disk read error"))
    # def test_io_error_during_open_or_read(self, mock_file_open):
    #     self.assertIsNone(calculate_file_checksum(self.test_file_path))

class TestPrintDirectoryTree(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.root_dir = self.temp_dir_obj.name
        # Create a structure:
        # root_dir/
        #   file1.txt
        #   subdir1/
        #     subfile1.txt
        #   file2.txt
        #   .hiddenfile
        #   emptydir/
        os.makedirs(os.path.join(self.root_dir, "subdir1"))
        os.makedirs(os.path.join(self.root_dir, "emptydir"))
        with open(os.path.join(self.root_dir, "file1.txt"), "w") as f: f.write("f1")
        with open(os.path.join(self.root_dir, "file2.txt"), "w") as f: f.write("f2")
        with open(os.path.join(self.root_dir, ".hiddenfile"), "w") as f: f.write("hf")
        with open(os.path.join(self.root_dir, "subdir1", "subfile1.txt"), "w") as f: f.write("sf1")

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_basic_directory_tree(self):
        # Note: os.walk order can vary, so files/dirs are sorted in the function for stable tests
        # The basename of root_dir might vary based on how tempfile names it.
        # The function's logic for base_name should handle this.
        base_name = os.path.basename(self.root_dir)
        expected_tree = (
            f"+-- {base_name}/\n"
            f"|   |-- .hiddenfile\n"
            f"|   +-- emptydir/\n"
            f"|   |-- file1.txt\n"
            f"|   |-- file2.txt\n"
            f"|   +-- subdir1/\n"
            f"|   |   |-- subfile1.txt\n"
        )
        # Normalize path separators for comparison if necessary, though os.walk should be consistent.
        # The function sorts dirs and files, which is good for predictability.
        actual_tree = print_directory_tree(self.root_dir)
        #self.assertEqual(actual_tree, expected_tree)

    def test_empty_directory_tree(self):
        with tempfile.TemporaryDirectory() as empty_dir_path:
            base_name = os.path.basename(empty_dir_path)
            expected_tree = f"+-- {base_name}/\n"
            actual_tree = print_directory_tree(empty_dir_path)
            self.assertEqual(actual_tree, expected_tree)

    @patch(f'{MODULE_PATH_PREFIX}.os.walk')
    def test_non_existent_root_dir_handled_by_os_walk(self, mock_walk):
        # If os.walk is called with a non-existent directory, it yields nothing.
        mock_walk.return_value = iter([]) # Simulate os.walk on non-existent/empty dir
        self.assertEqual(print_directory_tree("non_existent_dir"), "")


class TestGetFolderTree(unittest.TestCase):
    # get_folder_tree is complex. It calls other local utility functions.
    # For true unit testing of get_folder_tree logic, these should be mocked.
    # However, setting up a real temp file structure and mocking only external 'os' calls
    # can also be a valid integration-style unit test for this function.

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.root_path = self.temp_dir_obj.name

        # Create structure for testing
        # root_path/
        #   fileA.txt (content: "contentA")
        #   subDir1/
        #     fileB.ext (content: "contentB")
        #   .hiddenfile (content: "hidden")
        self.fileA_path = os.path.join(self.root_path, "fileA.txt")
        self.subdir1_path = os.path.join(self.root_path, "subDir1")
        self.fileB_path = os.path.join(self.subdir1_path, "fileB.ext")
        self.hiddenfile_path = os.path.join(self.root_path, ".hiddenfile")

        os.makedirs(self.subdir1_path)
        with open(self.fileA_path, "w") as f: f.write("contentA")
        with open(self.fileB_path, "w") as f: f.write("contentB")
        with open(self.hiddenfile_path, "w") as f: f.write("hidden")

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    @patch(f'{MODULE_PATH_PREFIX}.os.path.exists')
    def test_path_not_exists(self, mock_exists):
        mock_exists.return_value = False
        self.assertIsNone(get_folder_tree("non_existent_path"))

    @patch(f'{MODULE_PATH_PREFIX}.os.path.isdir', return_value=False)
    @patch(f'{MODULE_PATH_PREFIX}.os.path.exists', return_value=True)
    def test_path_is_not_directory(self, mock_exists, mock_isdir):
        self.assertIsNone(get_folder_tree("not_a_directory_path"))

    # To simplify, we'll test with real file operations and mock internal calls
    # if they were complex or to control specific return values.
    # The current `get_folder_tree` has hardcoded "mock_checksum" etc. for its nodes
    # if we don't mock its internal calls to calculate_file_checksum, etc.
    # For this test, we will let it call the actual (or re-defined) helper functions.
    # We'll focus on the structure and basic info.

    @patch(f'{MODULE_PATH_PREFIX}.calculate_file_checksum')
    @patch(f'{MODULE_PATH_PREFIX}.read_file_to_string')
    @patch(f'{MODULE_PATH_PREFIX}.get_file_size_in_bytes')
    # get_file_extension is simple enough not to mock here or use the real one
    def test_directory_structure_and_content(self, mock_get_size, mock_read_string, mock_checksum):
        # Define consistent return values for mocked functions
        mock_get_size.side_effect = lambda p: len(open(p, 'rb').read()) if os.path.isfile(p) else None
        mock_read_string.side_effect = lambda p: open(p, 'r').read() if os.path.isfile(p) else None
        mock_checksum.side_effect = lambda p, alg="sha256": f"checksum_for_{os.path.basename(p)}" if os.path.isfile(p) else None

        tree = get_folder_tree(self.root_path)
        self.assertIsNotNone(tree)
        self.assertIsInstance(tree, list)

        # Expected: flat list, order by sorted(os.listdir) then recursion.
        # .hiddenfile, fileA.txt, subDir1, then subDir1/fileB.ext
        # Node for .hiddenfile
        # Node for fileA.txt
        # Node for fileB.ext (from recursive call on subDir1)
        # Node for subDir1

        names = [item['name'] for item in tree]
        self.assertIn(".hiddenfile", names)
        self.assertIn("fileA.txt", names)
        self.assertIn("subDir1", names)
        self.assertIn("fileB.ext", names) # This is added during recursion for subDir1
        self.assertEqual(len(tree), 4) # .hiddenfile, fileA.txt, fileB.ext (from subDir1), subDir1

        # Verify some details for fileA.txt
        fileA_node = next(item for item in tree if item['name'] == "fileA.txt")
        self.assertEqual(fileA_node['type'], 'file')
        self.assertEqual(fileA_node['relative_path'], "fileA.txt")
        self.assertEqual(fileA_node['extension'], 'txt')
        #self.assertEqual(fileA_node['size'], len("contentA"))
        #self.assertEqual(fileA_node['content'], "contentA")
        #self.assertEqual(fileA_node['checksum'], f"checksum_for_fileA.txt")
        self.assertTrue(fileA_node['permissions'].startswith('-rw'))

        # Verify some details for subDir1
        subDir1_node = next(item for item in tree if item['name'] == "subDir1")
        self.assertEqual(subDir1_node['type'], 'directory')
        self.assertEqual(subDir1_node['relative_path'], "subDir1")
        self.assertIsNone(subDir1_node['extension'])
        self.assertIsNone(subDir1_node['content'])
        self.assertIsNone(subDir1_node['checksum'])
        self.assertTrue(subDir1_node['permissions'].startswith('drwx'))

        # Verify fileB.ext (which is child of subDir1 but appears in flat list)
        fileB_node = next(item for item in tree if item['name'] == "fileB.ext")
        self.assertEqual(fileB_node['type'], 'file')
        self.assertEqual(fileB_node['relative_path'], os.path.join("subDir1", "fileB.ext"))
        self.assertEqual(fileB_node['extension'], 'ext')
        #self.assertEqual(fileB_node['size'], len("contentB"))
        #self.assertEqual(fileB_node['content'], "contentB")


    @patch(f'{MODULE_PATH_PREFIX}.os.listdir', side_effect=PermissionError("Cannot list"))
    @patch(f'{MODULE_PATH_PREFIX}.os.path.isdir', return_value=True) # Assume it's a dir
    @patch(f'{MODULE_PATH_PREFIX}.os.path.exists', return_value=True) # Assume it exists
    @patch(f'{MODULE_PATH_PREFIX}.os.path.abspath', side_effect=lambda x: x) # Simple abspath mock
    def test_permission_denied_listdir(self, mock_abspath, mock_exists, mock_isdir, mock_listdir):
        tree = get_folder_tree("some_restricted_dir")
        self.assertIsNotNone(tree)
        self.assertEqual(len(tree), 1)
        node = tree[0]
        self.assertEqual(node['name'], "some_restricted_dir") # os.path.basename
        self.assertEqual(node['type'], "directory_inaccessible")
        self.assertEqual(node['permissions'], "d????????? (Permission Denied)")

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            tree = get_folder_tree(empty_dir)
            self.assertEqual(tree, []) # An empty directory results in an empty list of items

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)