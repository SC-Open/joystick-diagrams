import unittest

import joystick_diagrams.plugins.elite_dangerous_plugin.elite_dangerous as ed
from joystick_diagrams.input.profile_collection import ProfileCollection

class TestEDParserCases(unittest.TestCase):
    def setUp(self):
        self.file = ed.EliteDangerous("./tests/data/elite_dangerous/Custom.4.0_valid.binds")
    
    def test_parse(self):
        result = self.file.parse()
        self.assertIsInstance(result, ProfileCollection)

        # Check that the ProfileCollection is not empty
        self.assertNotEqual(len(result.profiles), 0, "ProfileCollection is empty")

        # Check that each profile has at least one bind
        for profile in result.profiles.values():
            self.assertNotEqual(len(profile.keybindings), 0, f"Profile {profile.name} has no keybinds")
        

    def test_bind_parse_button(self):
        # ("js1_button1")
        # ("js1_button22")
        # ("js1_button999")
        pass

    def test_bind_parse_blank(self):
        # ("js1_")
        pass

    def test_bind_parse_hat(self):
        # "js1_hat1_up")
        # ("js1_hat1_right")
        # "js1_hat1_down")
        # "js1_hat1_left")
        pass

    def test_bind_parse_axis(self):
        # "js1_rotz")
        # "js1_x")
        # "js1_slider1")
        pass

    def test_bind_no_device(self):
        pass

    def test_parser(self):
        pass


if __name__ == "__main__":
    unittest.main()
