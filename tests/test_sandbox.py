import os
import unittest
import tempfile
import shutil
from borneoai.tools import FileSandbox

class TestFileSandbox(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory as the workspace root
        self.test_dir = tempfile.mkdtemp()
        self.sandbox = FileSandbox(self.test_dir)
        
        # Create a test file inside workspace
        self.test_file_path = os.path.join(self.test_dir, "test.txt")
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("hello world")

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)

    def test_list_directory_inside(self):
        # Should succeed
        result = self.sandbox.list_directory(".")
        self.assertIn("test.txt", result)

    def test_read_file_inside(self):
        # Should succeed
        result = self.sandbox.read_file("test.txt")
        self.assertEqual(result, "hello world")

    def test_write_file_inside(self):
        # Should succeed
        result = self.sandbox.write_file("new.txt", "content")
        self.assertIn("Successfully wrote", result)
        
        # Verify write worked
        with open(os.path.join(self.test_dir, "new.txt"), "r") as f:
            self.assertEqual(f.read(), "content")

    def test_patch_file_inside(self):
        # Should succeed
        result = self.sandbox.patch_file("test.txt", "world", "borneo")
        self.assertIn("Successfully patched", result)
        
        # Verify patch worked
        with open(self.test_file_path, "r") as f:
            self.assertEqual(f.read(), "hello borneo")

    def test_delete_file_inside(self):
        # Should succeed
        result = self.sandbox.delete_file("test.txt")
        self.assertIn("Successfully deleted", result)
        self.assertFalse(os.path.exists(self.test_file_path))

    def test_sandbox_violation_read(self):
        # Trying to read a file outside the workspace root should return an error message
        result = self.sandbox.read_file("../some_external_file.txt")
        self.assertIn("Security Violation", result)

    def test_sandbox_violation_write(self):
        # Trying to write a file outside the workspace root should return an error message
        result = self.sandbox.write_file("/etc/passwd", "hack")
        self.assertIn("Security Violation", result)

    def test_sandbox_violation_delete(self):
        # Trying to delete a file outside the workspace root should return an error message
        result = self.sandbox.delete_file("../test.txt")
        self.assertIn("Security Violation", result)

if __name__ == "__main__":
    unittest.main()
