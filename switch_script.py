import sublime, sublime_plugin
import os.path

version  = "0.3"
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
  print "SwitchScript %s: %s" % (version, msg)

def assign_options(args):
  global options
  global defaults

  options = defaults

  for entry in args:
    options[str(entry)] = args[str(entry)]

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

# Returns whether @file_path is a part of @parent_path
# ie: /some/folder/nested/file.cpp is "in" /some/folder and /some/folder/nested
def is_within(parent_path, file_path):
  parent_parts = portable_split(parent_path)
  child_parts  = portable_split(file_path)

  if len(parent_parts) > len(child_parts):
    return False

  for i in range(len(parent_parts)):
    if parent_parts[i] != child_parts[i]:
      return False

  return True

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

  log("Searching for a spouse for: %s" % path)
  log("List of matching extensions: %r" % extensions)

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
    log("Checking if %s is in %r" % (path, in_path))
    if path not in in_path:
      continue

    in_path = filter(lambda a: a != path, in_path)

  return in_path

# Looks for a matching counterpart file for the one specified in @in_file_path
# within the folder tree @in_root. Returns a string containing the filepath of
# the counterpart if found, None otherwise.
#
# When in strict mode, a counterpart will only be valid if it resides within
# the same folder as the original file. Turning the strict flag off will make
# the method settle for any counterpart it can find in the given folder, regardless
# of whether the folders (the cp and the original) match.
#
# Update: v0.3 - added strict mode to close #1
# Issue URL: https://github.com/amireh/SwitchScript/issues/1
def find_counterpart(in_root, in_file_path, strict = True):

  file_info = { }
  file_info['path'] = os.path.normpath(in_file_path)
  file_info['name'], file_info['ext'] = os.path.splitext(os.path.basename(file_info['path']))

  candidates = find_in_directory(in_root, file_info)

  log("Candidates: %r" % candidates)

  # Strip the filename
  file_info["ancestors"] = os.path.dirname(file_info["path"])
  # Break it down into parts in a cross-platform way
  file_info["ancestors"] = strip_common_ancestors(portable_split(file_info["ancestors"]))
  # How many parts?
  file_info["steps"] = len(file_info["ancestors"])

  log("File's ancestors: %r (%d)" % (file_info["ancestors"], file_info["steps"]))

  # Find the candidates according to the directory ancestry
  candidate = None
  for file in candidates:
    ancestors = strip_common_ancestors(portable_split(os.path.dirname(file)))
    steps = len(ancestors)

    log("Stripped candidate: %r" % ancestors)

    # Exclude any candidate which resides in a deeper or lesser directory level than the original file
    if strict and steps != file_info["steps"]:
      continue

    # Calculate the actual rank
    valid = True
    for i in range(steps + 1):
      i += 1
      if file_info["ancestors"][file_info["steps"] - i] != ancestors[steps - i]:
        valid = False
        break

    if strict and not valid:
      continue

    candidate = file
    log("A new candidate has been found: %s" % candidate)

  if candidate:
    log("Match found: %s" % candidate)

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

    # Update: disabled in 0.3
    # root = self.window.folders()[0]

    counterpart = None

    # If more than one folder is open, we'll begin our search
    # within the folder that contains the current file, and if
    # no match was found there, we will grab any candidate we
    # find in the other folders.
    #
    # See for more info: https://github.com/amireh/SwitchScript/issues/1
    root = None
    root_open = False # we need to account for the possibility of the file's folder not being open
    for root in self.window.folders():
      if is_within(root, fname):
        root_open = True
        break

    if root_open:
      log("Looking inside my folder first: %s" %(root))
      counterpart = find_counterpart(root, fname)
    else:
      # reset the root so it doesn't get skipped by the later sibling loop
      # thinking it was searched, it wasn't
      root = None

    if counterpart and os.path.exists(counterpart):
      self.window.open_file(counterpart)
    else:
      for uncle in self.window.folders():
        if uncle == root:
          continue

        log("Looking in root sibling folder: %s" % (uncle))

        counterpart = find_counterpart(uncle, fname, False)

        if counterpart and os.path.exists(counterpart):
          self.window.open_file(counterpart)
          break
        else:
          counterpart = None

    if counterpart:
      log("Switching script %s in %s" % (fname, root))
    else:
      log("Unable to switch script, can not find a suitable match for: %s" % (fname))
