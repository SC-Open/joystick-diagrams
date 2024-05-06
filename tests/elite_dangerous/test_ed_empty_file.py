import unittest

import joystick_diagrams.plugins.elite_dangerous_plugin.elite_dangerous as ed


class TestEDFileErrors(unittest.TestCase):
    def test_empty_file(self):
        with self.assertRaises(Exception) as context:
            ed.EliteDangerous("./tests/data/elite_dangerous/empty.xml")
        self.assertTrue(
            "File is not a valid Elite Dangerous XML" in str(context.exception)
        )

    def test_invalid_file(self):
        with self.assertRaises(Exception) as context:
            ed.EliteDangerous("./tests/data/elite_dangerous/invalid.xml")
        self.assertTrue(
            "File is not a valid Elite Dangerous XML" in str(context.exception)
        )

    def test_invalid_file_type(self):
        with self.assertRaises(Exception) as context:
            ed.EliteDangerous("./tests/data/elite_dangerous/invalid_type.abc")
        self.assertTrue("File must be an XML file" in str(context.exception))

    def test_invalid_file_path(self):
        with self.assertRaises(Exception) as context:
            ed.EliteDangerous("./tests/data/elite_dangerous/not_a_file.file")
        self.assertTrue("File not found" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
    