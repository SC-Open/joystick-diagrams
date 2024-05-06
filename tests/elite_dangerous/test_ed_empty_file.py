import pytest

import joystick_diagrams.plugins.elite_dangerous_plugin.elite_dangerous as ed

def test_empty_file():
    with pytest.raises(Exception) as context:
        ed.EliteDangerous("./tests/data/elite_dangerous/empty.xml")
    assert "File is not a valid Elite Dangerous XML" in str(context.value)

def test_invalid_file():
    with pytest.raises(Exception) as context:
        ed.EliteDangerous("./tests/data/elite_dangerous/invalid.xml")
    assert "File is not a valid Elite Dangerous XML" in str(context.value)

def test_invalid_file_type():
    with pytest.raises(Exception) as context:
        ed.EliteDangerous("./tests/data/elite_dangerous/invalid_type.abc")
    assert "File must be an XML file" in str(context.value)

def test_invalid_file_path():
    with pytest.raises(Exception) as context:
        ed.EliteDangerous("./tests/data/elite_dangerous/not_a_file.file")
    assert "File not found" in str(context.value)

if __name__ == "__main__":
    pytest.main()
