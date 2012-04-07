import sublime, sublime_plugin
import os.path

version  = "0.2"
options  = {}
defaults = {
  # A list of all the directories that contain source and/or header files
  "paths": ['.', 'include', 'src'],
  
  # Folders specified in excluded_paths will not be traversed
  "excluded_paths": ['.git', '.svn', '.cvs'],

  # Define the extensions you'd like to switch between here
  "header_extensions": ['h', 'hpp', 'hh', 'hxx'],
  "source_extensions": ['c', 'cpp', 'cc', 'cxx', 'm', 'mm'],

  # Useful for debugging
  "logging_enabled": False
}

def log(msg):
  global options
  if not options["logging_enabled"]:
    return

  global version
  print "SwitchScript " + version + ": " + msg

def assign_options(args):
  global options
  global defaults

  options = defaults

  for entry in args:
    options[str(entry)] = args[str(entry)]

# Returns whether the given file is a source file according to the
# specified array of source file extensions
#
def is_source(fname):
  for ext in options["source_extensions"]:
    if fname.endswith(ext):
      return True
  return False

# Returns whether the given file is a header file according to the
# specified array of header file extensions
#
def is_header(fname):
  for ext in options["header_extensions"]:
    if fname.endswith(ext):
      return True
  return False

# Attempts to find all the files in the given directory that match the input file's
# name and match one of the opposing extensions
#
# Returns a set of file paths
#
def find_in_directory(in_dir, in_file_info):
  name = in_file_info["name"]
  path = in_file_info["path"]
  extension_checker = is_source if is_header(path) else is_header
  extensions = options["source_extensions"] if is_header(path) else options["header_extensions"]
  matched = []

  log("Searching for a spouse for: " + path)
  log("List of matching extensions: " + str(extensions))

  # Walk the tree and track every file that matches the source's name and opposing extension
  for root, dirs, files in os.walk( in_dir ):

    # Skip directories marked as excluded
    dir_name = os.path.basename(root)
    if dir_name in options["excluded_paths"]:
      continue

    for file in files:
      if os.path.splitext(file)[0] == name and extension_checker(file):
        matched.append( os.path.join(root, file) )

  return matched

# Removes any ancestor folder according to those specified as file containers
# from the given path
#
def strip_common_ancestors(in_path):
  for path in options["paths"]:
    if path not in in_path:
      continue

    in_path.remove(path)

  return in_path

def portable_split(path, debug=False):
    parts = []
    while True:
        newpath, tail = os.path.split(path)
        if debug: print repr(path), (newpath, tail)
        if newpath == path:
            assert not tail
            if path: parts.append(path)
            break
        parts.append(tail)
        path = newpath
    parts.reverse()
    return parts

def find_counterpart(in_root, in_file_path):

  file_info = { }
  file_info['path'] = os.path.normpath(in_file_path)
  file_info['name'], file_info['ext'] = os.path.splitext(os.path.basename(file_info['path']))

  candidates = find_in_directory(in_root, file_info)

  # TODO: what is a cross-platform way to do this? need to find the folder separator
  # 1. Strip the filename
  file_info["ancestors"] = os.path.dirname(file_info["path"])
  # 2. Break it down into parts in a cross-platform way
  # file_info["ancestors"] = strip_common_ancestors(file_info["ancestors"].split('/'))
  file_info["ancestors"] = strip_common_ancestors(portable_split(file_info["ancestors"]))
  
  file_info["steps"] = len(file_info["ancestors"])

  log("File's ancestors: " + str(file_info["ancestors"]) + "( " + str(file_info["steps"]) + ")")

  # Find the candidates according to the directory ancestry
  candidate = None
  for file in candidates:
    # ancestors = strip_common_ancestors(os.path.dirname(file).split('/'))
    ancestors = strip_common_ancestors(portable_split(os.path.dirname(file)))
    steps = len(ancestors)

    # Exclude any candidate which resides in a deeper or lesser directory level than the original file
    if steps != file_info["steps"]:
      continue

    # Calculate the actual rank
    valid = True
    for i in range(steps + 1):
      i += 1
      if file_info["ancestors"][file_info["steps"] - i] != ancestors[steps - i]:
        valid = False
        break

    if not valid:
      continue

    candidate = file
    log("A new candidate has been found: " + candidate)

  if candidate:
    log("Match found: " + candidate)
   
  return candidate

class SwitchScriptCommand(sublime_plugin.WindowCommand):
  def run(self, options = { "header_extensions": [], "source_extensions": [], "paths": [], "excluded_paths": [], "logging_enabled": False }):
    # Set user options
    assign_options(options)

    # Get the current active file name and active folder
    fname = self.window.active_view().file_name()
    if not fname:
      log("Can not switch script, file name can not be retrieved. Is a file currently open and active?")
      return

    if len(self.window.folders()) == 0:
      log("Can not switch script, a folder must be selected. Aborting.")
      return

    root = self.window.folders()[0]

    log("Switching script " + fname + " in " + root)

    counterpart = find_counterpart(root, fname)

    if counterpart and os.path.exists(counterpart):
      self.window.open_file(counterpart)
