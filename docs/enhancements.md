## `code`
    
Formerly a set of [helper functions](helpers.md), the followings have been attached to the `code` module, which is now preimported.
    
Code can be monkey-patched at runtime using multiple functions, depending on what should be patched and how. Note that some of the functions rely on the [`patchy`](https://github.com/adamchainz/patchy) module.
    
- `add_line`, `add_lines`, `insert_line`, `insert_line`: it allows to add line(s) at specific indices (starting from 0), before or after (using `after=True`).
- `delete_line`, `delete_lines`, `remove_line`, `remove_lines`: it allows to delete line(s) by index (starting from 0).
- `patch`: alias for `patchy.patch`, taking a function and a patch file's text as arguments.
- `replace`: wrapper for `patchy.replace`, handling multiple replacements at a time, either replacing whole function (like in original `replace`) or only parts of the code.
- `replace_lines`: for replacing specific lines in the code of a given function, specifying replacements as pairs of line index (starting from 0) and replacement text.
- `restore`: for restoring a function to its original code.
- `revert`: for reverting code to a previous version (up to 3 previous versions).
- `source`: for getting function's source code (shortcut for `patchy.api._get_source`).
- `unpatch`: alias for `patchy.unpatch`, taking a function and a previous patch file's text as arguments in order to revert the function to its previous version.

A context manager is also available:

- `Patch`: alias for `patchy.temp_patch`, taking a function in argument and a patch ; it patches the function in the context of the open code block and then restores the function at the end of this block.

-----

## `codecs`

`codecs` has multiple additional encodings, among others:

- `leetspeak`: bidirectional conversion between leetspeak and normal text
- `markdown`: unidirectional conversion of Markdown to HTML using ´markdown2.markdown`
- `morse`: bidirectional conversion between morse and normal text
- `rot-N` (with N belonging to ]0, 26[): bidirectional conversion between ROT and normal text
- `xor-N` (with N belonging to ]0, 256[): XORing of 1 byte with normal text

New codecs can be added easilly using the new function `codecs.add_codec`.

??? example "XOR-N encoding"
    
    This defines a new codec XOR-N and adds it to `codecs`.
    
        :::python
        def _xorn(text, n=1):
            return "".join(chr(ord(c) ^ (n % 256)) for c in text)

        def xor_byte_encode(i):
            def encode(text, errors="strict"):
                r = _xorn(ensure_str(text), int(i))
                return r, len(r)
            return encode
        xor_byte_decode = xor_byte_encode

        codecs.add_codec("xorN", xor_byte_encode, xor_byte_decode,
                         r"(?i)xor[-_]?([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$")
    
    The pattern allows to dynamically define XOR so that XOR-1 to XOR-255 are valid and handles a different byte to XOR with the input text.

-----

## `hashlib`
    
`hashlib`, while imported with Tinyscript, is enhanced with additional functions so that these must not be rewritten in many applications, that is:

- `hash_file`: this hashes a file per block.
- `[hash]_file` (e.g. `sha256_file`): each hash algorithm existing in the native `hashlib` has a bound function for hashing a file (e.g. `md5` is a native function of `hashlib` and will then have `md5_file`).

-----

## `virtualenv`

`virtualenv`, while imported with Tinyscript, is enhanced with convenient functions for setting up a virtual environment.

- `activate(venv_dir)`: sets environment variables and globals as of `bin/activate_this.py` in order to activate the given environment
- `deactivate()`: unsets the current environment variables and globals
- `install(package, ...)`: uses Pip to install the given package ; "`...`" corresponds to the arguments and keyword-arguments that can be passed to Pip
- `is_installed(package)`: indicates if the given package is installed in the environment
- `list_packages()`: lists the packages installed in the environment
- `setup(venv_dir, requirements)`: sets up a virtual environment to the given directory and installs the given requirements (either a requirements file or a list of packages)
- `teardown(venv_dir)`: deactivates and removes the given environment ; if no directory given, the currently defined one is handled
