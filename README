SwitchScript is a plugin for the Sublime Text 2 editor that adds support for switching between header and source files according to specified extensions within the current active directory tree. This editor ability is very helpful for working with projects that contain a large number of files (eg. C++ projects with .cpp and .hpp and files).

The plugin is flexible to support different project structures, and it makes no assumptions about where your files are stored so long as they're all under one root; the active folder you've opened in the editor.

### Options
You can configure SwitchScript in the key bindings file where you bind the command to a key. These are the default options:

```python
defaults = {
  # A list of all the directories that contain source and/or header files
  "paths": ['.', 'include', 'src'],
  
  # Folders specified in excluded_paths will not be traversed
  "excluded_paths": ['.git', '.svn', '.hg'],

  # Define the extensions you'd like to switch between here
  "header_extensions": ['h', 'hpp', 'hh', 'hxx'],
  "source_extensions": ['c', 'cpp', 'cc', 'cxx', 'm', 'mm'],

  # Useful for debugging
  "logging_enabled": False
}
```

What they mean:

* `paths`: SwitchScript will first attempt to find a matching file (based on the active file's name and extension) in the file's directory, if that fails, it will look in the `include` folder, and then in `src`.
* `excluded_paths` contains names of folders that will not be traversed or searched
* `header_extensions` and `source_extensions` specify the extensions of files to switch between.
* `logging_enabled` toggles logging; useful if you need to debug the plugin or want to submit a bug

### A Sample Configuration
This is a my configuration:

```python
  { "keys": ["ctrl+alt+up"], 
    "command": "switch_script", 
    "args": {
      "options": {
        "paths": [".", "include", "src", "funky"]
      }
    }
  }
```

I use Ctrl+Alt+Up to switch between files. I've added the `funky` folder to the paths because I have a funny project which headers are set in `funny_project/include/funky/some_class.hpp` but the source files are in `funny_project/src/some_class.cpp`; manually specifying the path will allow SwitchScript to match those two. 

### Troubleshooting

The plugin has been tested only on Linux (Arch x86_64) so far. If you come across any bugs or issues on other platforms (or on Linux) you can open a GitHub issue in this repository or email me directly: net.amireh[@]ahmad
