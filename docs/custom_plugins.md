# Joystick Diagrams Plugin Management
The ParserPluginManager class is designed to manage plugins within the context of the running application. It discovers plugins, loads them, and wraps them in a PluginWrapper for further management.

As a plugin developer, you don't directly interact with the ParserPluginManager. Instead, you should ensure your plugin conforms to the PluginInterface and includes the expected files (__init__, config, main, settings). The ParserPluginManager will handle loading and executing your plugin within the application.

However, you should be aware of the PluginInterface methods that your plugin needs to implement. These methods will be called by the PluginWrapper or the ParserPluginManager. The exact methods depend on the PluginInterface definition, see Plugin Interface below.

In summary, focus on developing your plugin according to the expected interface and file structure. The ParserPluginManager will take care of integrating it into the application.

# Plugin Interface
The plugin_interface.py script defines an abstract base class (ABC) PluginInterface that serves as a blueprint for all plugins in the application. Here's a breakdown of its main components:

Imports: The script imports several modules for logging, handling file paths, and loading settings dynamically.

PluginInterface Class: This class is an abstract base class, meaning it provides a common interface for all plugins but cannot be instantiated itself. It defines several methods and properties that all plugins must implement.

Nested Classes FolderPath and FilePath: These classes are used to specify the type of path sourcing method a plugin uses. They are returned by the path_type method.

Exception Methods: These methods return specific exceptions related to file and directory validation. They can be used by the plugin to raise exceptions with custom messages.

Path Methods: These methods are related to handling the plugin's data path. get_plugin_data_path returns the full path to the plugin's data directory, and get_plugin_data returns all available files/folders for the plugin.

Abstract Methods: These methods must be implemented by any class that inherits from PluginInterface. They include process (which should return a ProfileCollection object), set_path (which sets the file/directory path for the plugin), load_settings (which loads the plugin's settings), and icon (which returns a path string to the plugin's icon file).

Properties: These properties return information about the plugin, such as its name, version, and current path.

clean_plugin_name Function: This function cleans the plugin name from any potentially problematic characters for Windows.

In summary, this script provides a blueprint for creating plugins for the application. Any plugin must inherit from PluginInterface and implement its abstract methods. The PluginInterface also provides several utility methods and properties for handling paths and raising exceptions.

# Parser Plugin Template Files
## main.py
The ParserPlugin class in main.py is a concrete implementation of the PluginInterface abstract base class. It provides the specific functionality for your plugin. Here's what it does:

Initialization: In the __init__ method, it initializes the plugin settings and registers any validators. It also sets the path attribute to None.

Processing: The process method is where you would implement the logic for processing your plugin. It should return a ProfileCollection instance. Currently, it returns an empty ProfileCollection.

Setting the Path: The set_path method attempts to set the path for the plugin. It first tries to use the default Elite Dangerous bindings path. If that doesn't exist, it prompts the user to select a valid path. If the user doesn't select a valid path, it raises a ValueError. If any other error occurs, it logs the error and returns False.

Saving Plugin State: The save_plugin_state method is a placeholder for code to persist any data changes when they are modified. It currently does nothing.

Loading Settings: The load_settings method is a placeholder for code to load any data or initialize your plugin. It's automatically called on startup if the plugin is enabled. It currently does nothing.

Path Type: The path_type property returns a FolderPath instance with a message and a default path. This could be used to prompt the user to select a path.

Icon: The icon property returns the path to the plugin's icon file.

In summary, main.py provides the specific functionality for your plugin, including initialization, processing, setting the path, saving the plugin state, and loading settings. It also provides properties for the path type and icon.

## your_plugin.py
This file is a placeholder for your plugin's specific logic. You should implement the process method in this file to define how your plugin processes data. You can also add any additional methods or logic specific to your plugin.

# Joystick Template Diagrams
## template.py
The Template class in joystick_diagrams/template.py provides several methods for extracting data from a joystick diagram template file:

get_template_data(self, template_path: Path): Reads the template file and returns its content as a string.

get_template_modifiers(self) -> set[str]: Returns the available modifier numbers supported for a given control from the template.

get_template_buttons(self) -> set[str]: Returns the available button controls from the template.

get_template_axis(self) -> set[str]: Returns the available axis controls from the template.

get_template_hats(self) -> set[str]: Returns the available hat controls from the template.

In addition, the class provides several properties for getting counts of different control types:

axis_count(self) -> int: Returns the number of axis available.

hat_count(self) -> int: Returns the number of hats available.

modifier_count(self) -> int: Returns the number of modifiers available.

button_count(self) -> int: Returns the number of buttons available.

These methods and properties allow you to extract data from a joystick diagram template file and work with the control types and modifiers available in the template.
