# Copyright (c) 2017 Akuli

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Simple debugging tool."""

import argparse
import code
import collections
import importlib.util
import inspect
import math
import pydoc
import shlex
import shutil
import sys
import textwrap
import traceback
try:
    # Just importing readline is enough to set up handy keyboard
    # shortcuts.
    import readline     # noqa
except ImportError:
    # Probably Windows.
    pass

__all__ = ['Command', 'DebugConsole', 'debug']


_NOTHING = object()
Command = collections.namedtuple('Command', 'func reqargs optargs doc')


def _wprint(string):
    """Wrap and print a string."""
    print(textwrap.fill(string), end='\n\n')


def _print_list(stringlist):
    maxlen = max(map(len, stringlist))
    columns = shutil.get_terminal_size().columns // (maxlen + 2)
    if columns < 2:
        for string in stringlist:
            print(string)
    else:
        rows = math.ceil(len(stringlist) / columns)
        for y in range(rows):
            line = '  '.join(
                string.ljust(maxlen) for string in stringlist[y::rows])
            print(line.rstrip(' '))


class _Helper:

    def __init__(self, console):
        self._console = console

    def __repr__(self):
        return textwrap.fill(
            "Type help() for help about this debugging console or "
            "help(something) to use Python's built-in help().")

    # We can't do something=None to allow help(None).
    def __call__(self, something=_NOTHING):
        if something is _NOTHING:
            _wprint("This is a special Python prompt for debugging large "
                    "projects that consist of several modules.")
            _wprint("Using this prompt is easy. You can enter any Python "
                    "commands to run them. They will be run in the "
                    "current module, which is a lot like the current "
                    "working directory of a shell or a command prompt.")
            print("Here is a list of the special commands:")
            for name, command in sorted(self._console.commands.items()):
                if command.doc is None:
                    print(name)
                else:
                    summary = inspect.cleandoc(command.doc).split('\n')[0]
                    # TODO: some way to get more detailed help of the special
                    # commands.
                    print('  %-10s  %s' % (name, summary))
        else:
            pydoc.help(something)


class DebugConsole(code.InteractiveConsole):
    """A special console for debugging purposes."""

    commands = {}    # {name: Command, ...}

    def __init__(self, *args, verbose=False, **kwargs):
        """Initialize the console."""
        super().__init__(*args, **kwargs)
        self._helper = _Helper(self)
        self.verbose = verbose
        self.modulename = None
        self.module = None

    # Tell code.InteractiveConsole to work in self.module.
    @property
    def locals(self):
        return self.module.__dict__

    # code.InteractiveConsole.__init__ assigns to this.
    @locals.setter
    def locals(self, value):
        pass

    def _check_args(self, commandname, args) -> bool:
        """Check if arguments for a command are valid."""
        command = self.commands[commandname]
        if len(args) < len(command.reqargs):
            print("Missing arguments for %s." % commandname, file=sys.stderr)
        elif len(args) > len(command.reqargs) + len(command.optargs):
            print("Too many arguments for %s." % commandname, file=sys.stderr)
        else:
            # everything's fine
            return True
        print("Usage:", commandname, end='')
        for arg in command.reqargs:
            print(' ' + arg.upper(), end='')
        for arg in command.optargs:
            print(' [' + arg.upper() + ']', end='')
        print()
        return None

    def raw_input(self, prompt=''):
        if prompt != sys.ps1:
            # It's probably '... ', no need to support special commands.
            return input(prompt)

        while True:
            string = input(prompt)
            try:
                commandname, *args = shlex.split(string)
                ok = self._check_args(commandname, args)
            except (ValueError, KeyError):
                # Not a special command.
                return string
            if ok:
                try:
                    self.run_command(commandname, args)
                except Exception as e:
                    print("An exception occurred while running %s!"
                          % commandname, file=sys.stderr)
                    traceback.print_exception(type(e), e, e.__traceback__)

    def run_command(self, commandname, args):
        self.commands[commandname].func(self, *args)

    @classmethod
    def command(cls, func):
        if 'commands' not in cls.__dict__:
            # Someone is subclassing DebugConsole and cls.commands
            # comes from DebugConsole or some other parent class. The
            # subclass must have a command mapping that gets commands
            # from the parent class, but adding a command won't add it
            # to the parent class.
            cls.commands = collections.ChainMap({}, cls.commands)

        reqargs = []
        optargs = []
        signature = inspect.signature(func)
        # We need to get rid of the first argument because it's the
        # DebugConsole instance.
        params = list(signature.parameters.items())[1:]
        for name, param in params:
            if param.kind != inspect.Parameter.POSITIONAL_OR_KEYWORD:
                raise TypeError("unsupported function signature: "
                                + func.__name__ + str(signature))
            if param.default is inspect.Parameter.empty:
                reqargs.append(name)
            else:
                optargs.append(name)

        cls.commands[func.__name__] = Command(
            func, reqargs, optargs, func.__doc__)
        return func

    # The special help variable.
    def add_helper(self):
        self.locals.setdefault('help', self._helper)

    def remove_helper(self):
        if self.locals.get('help', object()) is self._helper:
            del self.locals['help']


def _setup_commands():
    # This is a separate function to avoid polluting the namespace.

    @DebugConsole.command
    def cd(console, modulename='__main__'):
        """Change the current module.

        The new module will be imported, and it can be relative to the
        old module. If no arguments are given, go to __main__.
        """
        if console.verbose:
            print("Importing", modulename, "and changing the current",
                  "module to it")

        # These need to be first because the rest of this must not run
        # if these fail.
        modulename = importlib.util.resolve_name(modulename, console.modulename)
        module = importlib.import_module(modulename)

        if console.module is not None:
            # Not running for the first time.
            console.remove_helper()
        console.module = module
        console.modulename = modulename
        console.add_helper()

    @DebugConsole.command
    def ls(console):
        """Print a list of variables in the current module.

        This is equivalent to dir(), but this prints the list nicely in
        multiple columns.
        """
        if console.verbose:
            print("Listing the variables in", console.modulename)
        _print_list(sorted(dir(console.module)))

    @DebugConsole.command
    def pwd(console):
        """Print the name of the current module."""
        if console.verbose:
            print("You are currently in", end=" ")
        result = repr(console.module)
        if result.startswith('<') and result.endswith('>'):
            result = result[1:-1]
        print(result)


_setup_commands()


def debug(module='__main__', *, consoleclass=DebugConsole, **kwargs):
    print("Starting a debugging session in module", repr(module),
          "on Python", '.'.join(map(str, sys.version_info[:3])))
    print("Type 'help' for more info.")
    console = DebugConsole(**kwargs)
    console.run_command('cd', [module])
    console.interact('')
    print("Exiting the debugging session.")
    console.remove_helper()


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'module', help="the initial current module")
    parser.add_argument(
        '-v', '--verbose', action='store_true', help="explain what is done")
    args = parser.parse_args()
    debug(**args.__dict__)


if __name__ == '__main__':
    _main()
