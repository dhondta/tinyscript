#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module for extending argparse features, for simplifying parser.py.

"""
import random
import shlex
import sys
from argparse import _ActionsContainer, _ArgumentGroup, _AttributeHolder, \
                     _SubParsersAction, ArgumentDefaultsHelpFormatter, \
                     Action, ArgumentError, RawTextHelpFormatter, SUPPRESS, \
                     Namespace, ArgumentParser as BaseArgumentParser
from gettext import gettext as gt
from os.path import basename, splitext

from tinyscript.helpers.lambdas import is_long_opt, is_pos_int, is_short_opt
from tinyscript.helpers.utils import user_input


__all__ = ["gt", "ArgumentParser", "SUPPRESS"]


DEFAULT_MAX_LEN = 20
DEFAULT_LST_MAX_LEN = 10


class _DemoAction(Action):
    def __init__(self, option_strings, dest=SUPPRESS, default=SUPPRESS,
                 help=None, examples=None):
        super(_DemoAction, self).__init__(option_strings=option_strings,
                                          dest=dest, default=default, nargs=0,
                                          help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.demo_args()


class _WizardAction(Action):
    def __init__(self, option_strings, dest=SUPPRESS, default=SUPPRESS,
                 help=None):
        super(_WizardAction, self).__init__(option_strings=option_strings,
                                            dest=dest, default=default, nargs=0,
                                            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.input_args()


class _NewActionsContainer(_ActionsContainer):
    """
    Modified version of argparse._ActionsContainer for handling a new "note"
     keyword argument.
    """
    
    def __init__(self, *args, **kwargs):
        super(_NewActionsContainer, self).__init__(*args, **kwargs)
        self.register('action', 'parsers', _NewSubParsersAction)
        self.register('action', 'demo', _DemoAction)
        self.register('action', 'wizard', _WizardAction)
    
    def add_argument(self, *args, **kwargs):
        new_kw = {k: v for k, v in kwargs.items()}
        # collect Tinyscript-added keyword-arguments
        cancel = new_kw.pop('cancel', False)
        note = new_kw.pop('note', None)
        last = new_kw.pop('last', False)
        prefix = new_kw.pop('prefix', None)
        suffix = new_kw.pop('suffix', None)
        try:
            # define the action based on argparse, with only argparse-known
            #  keyword-arguments
            action = super(_NewActionsContainer, self).add_argument(*args,
                                                                    **new_kw)
            # now set Tinyscript-added keyword-arguments
            action.note = note
            action.last = last
            action.prefix = prefix
            action.suffix = suffix
            return True
        except ArgumentError:
            # drop the argument if conflict and cancel True
            if cancel:
                return False
            # otherwise, retry after removing the short option string
            args = list(args)
            short_opt = filter(is_short_opt, args)
            if len(short_opt) > 0:
                args.remove(short_opt[0])
                return self.add_argument(*args, **kwargs)
            # otherwise, retry after modifying the long option string with the
            #  precedence to the prefix (if set) then the suffix (if set)
            long_opt = filter(is_long_opt, args)
            if len(long_opt) > 0:
                long_opt = args.pop(args.index(long_opt[0]))
                if kwargs.get('action') in \
                    [None, 'store', 'append', 'store_const', 'append_const']:
                    kwargs['metavar'] = kwargs.get('metavar') or \
                                        long_opt.lstrip('-').upper()
                if prefix:
                    long_opt = "--{}-{}".format(prefix,
                                                long_opt.split("--", 1)[1])
                    args.append(long_opt)
                    return self.add_argument(*args, **kwargs)
                elif suffix:
                    long_opt = "{}-{}".format(long_opt, suffix)
                    args.append(long_opt)
                    return self.add_argument(*args, **kwargs)
        return False

    def add_argument_group(self, *args, **kwargs):
        group = _NewArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group


class _NewArgumentGroup(_ArgumentGroup, _NewActionsContainer):
    """
    Modified version of argparse._ArgumentGroup for modifying arguments groups
     handling in the modified ActionsContainer.
    """
    pass
    

class _NewSubParsersAction(_SubParsersAction):
    """
    Modified version of argparse._SubParsersAction for handling formatters of
     subparsers, inheriting from this of the main parser.
    """
    def add_parser(self, name, **kwargs):
        # set prog from the existing prefix
        if kwargs.get('prog') is None:
            kwargs['prog'] = '%s %s' % (self._prog_prefix, name)
        # create a pseudo-action to hold the choice help
        if 'help' in kwargs:
            help = kwargs.pop('help')
            choice_action = self._ChoicesPseudoAction(name, help)
            self._choices_actions.append(choice_action)
        # create the parser, but with another formatter and separating the help
        #  into an argument group
        parser = self._parser_class(formatter_class=HelpFormatter,
                                    add_help=False, **kwargs)
        info = parser.add_argument_group("extra arguments")
        info.add_argument("-h", "--help", action='help', default=SUPPRESS,
                          help=gt('show this help message and exit'))
        # add it to the map
        self._name_parser_map[name] = parser
        return parser
        

class ArgumentParser(_NewActionsContainer, BaseArgumentParser):
    """
    Modified version of argparse.ArgumentParser, based on the modified
     ActionsContainer.
    """
    def __init__(self, globals_dict=None, *args, **kwargs):
        self._reparse_args = None
        globals_dict = globals_dict or {}
        self.examples = globals_dict.get('__examples__')
        if self.examples and len(self.examples) == 0:
            self.examples = None
        script = globals_dict.get('__file__')
        if script:
            script = basename(script)
            kwargs['prog'], _ = splitext(script)
        else:
            kwargs['prog'] = ""
        kwargs['add_help'] = False
        kwargs['conflict_handler'] = "error"
        kwargs['formatter_class'] = HelpFormatter
        # format the epilog message
        if self.examples and script:
            kwargs['epilog'] = gt("Usage examples") + ":\n" + \
                               '\n'.join("  python {0} {1}".format(script, e) \
                                         for e in self.examples)
        # format the description message
        d = ''.join(x.capitalize() for x in kwargs['prog'].split('-'))
        v = globals_dict.get('__version__')
        if v:
            d += " v" + v
        for k in ['__author__', '__reference__', '__source__', '__training__']:
            m = globals_dict.get(k)
            if m:
                d += "\n%s: %s" % (k.strip('_').capitalize(), m)
                if k == '__author__':
                    e = globals_dict.get('__email__')
                    if e:
                        d += " ({})".format(e)
        doc = globals_dict.get('__doc__')
        if doc:
            d += "\n\n" + doc
        kwargs['description'] = d
        # now initialize argparse's ArgumentParser with the new arguments
        super(ArgumentParser, self).__init__(*args, **kwargs)
    
    def demo_args(self):
        """
        Additional method for replacing input arguments by demo ones.
        
        :post: modified sys.argv
        """
        argv = random.choice(self.examples).replace("--demo", "")
        self._reparse_args = shlex.split(argv)
    
    def input_args(self):
        """
        Additional method for making the user input arguments manually.
        
        :post: modified sys.argv
        """
        new_args = []
        is_action = lambda a, nl: any(type(a) is \
                                  self._registry_get('action', n) for n in nl)
        first_actions = filter(lambda a: not a.last, self._actions)
        last_actions = filter(lambda a: a.last, self._actions)
        for actions in [first_actions, last_actions]:
            for action in actions:
                if action.dest is SUPPRESS or action.default is SUPPRESS:
                    continue  # this prevents 'help' and 'version' actions
                try:
                    ostr = action.option_strings[0]
                except IndexError:  # occurs when positional argument
                    ostr = None
                prompt = (action.help or action.dest).capitalize()
                if is_action(action, ('store', 'append')):
                    value = user_input(prompt, action.choices, action.default)
                    if value:
                        new_args.extend([ostr, value] if ostr else [value])
                elif is_action(action, ('store_const', 'append_const')):
                    value = user_input(prompt, ("(A)dd", "(D)iscard"), "d")
                    if value == "add":
                        new_args.append(ostr)
                elif is_action(action, ('store_true', )):
                    value = user_input(prompt, ("(Y)es", "(N)o"), "n")
                    if value == "y":
                        new_args.append(ostr)
                elif is_action(action, ('store_false', )):
                    value = user_input(prompt, ("(Y)es", "(N)o"), "n")
                    if value == "n":
                        new_args.append(ostr)
                elif is_action(action, ('count', )):
                    value = user_input(prompt, is_pos_int, 0,
                                       "positive integer")
                    otype = ['A', 'O'][ostr.startswith("--")]
                    if otype == "A":
                        new_arg = ["-{}".format(int(value) * ostr.strip('-'))]
                    else:
                        new_arg = [ostr for i in range(int(value))]
                    new_args.extend(new_arg)
                else:
                    raise NotImplementedError("Unknown argparse action")
        self._reparse_args = new_args
        
    def parse_args(self, args=None, namespace=None):
        """
        Reparses new arguments when _DemoAction (triggering parser.demo_args())
         or _WizardAction (triggering input_args()) was called.
        """
        args = super(ArgumentParser, self).parse_args(args, namespace)
        if self._reparse_args is not None:
            args = [_ for _ in self._reparse_args]
            self._reparse_args = None
            args = super(ArgumentParser, self).parse_args(args, namespace)
        return args

    def error(self, message):
        """
        Prints a usage message incorporating the message to stderr and exits in
         the case when no new arguments to be reparsed, that is when no special
         action like _DemoAction (triggering parser.demo_args()) or 
         _WizardAction (triggering input_args()) was called. Otherwise, it
         simply does not stop execution so that new arguments can be reparsed.
        """
        if self._reparse_args is None:  # normal behavior with argparse
            self.print_usage(sys.stderr)
            self.exit(2, gt('%s: error: %s\n') % (self.prog, message))


class HelpFormatter(ArgumentDefaultsHelpFormatter, RawTextHelpFormatter):
    """
    Help message formatter for appending a custom note (as input through the
     add_argument method of CustomArgumentParser) to argument help. It also
     allows to reduce long default values (e.g. a list of integers) to something
     readable.
    """
    def _expand_help(self, action):
        params = dict(vars(action), prog=self._prog)
        for name in list(params):
            if params[name] is SUPPRESS:
                del params[name]
        for name in list(params):
            if hasattr(params[name], '__name__'):
                params[name] = params[name].__name__
        if params.get('choices') is not None:
            choices_str = ', '.join([str(c) for c in params['choices']])
            params['choices'] = choices_str
        if params.get('default') is not None:
            s = str(params['default'])
            # if the default value string representation is too long, reduce it
            if len(s) > DEFAULT_MAX_LEN:
                p = s.split(',')
                if len(p) > DEFAULT_LST_MAX_LEN:
                    s = ','.join(p[:2] + ["..."] + p[-2:])
            params['default'] = s
        return self._get_help_string(action) % params

    def _get_help_string(self, action):
        help = super(HelpFormatter, self)._get_help_string(action)
        if '%(note)' not in help and hasattr(action, "note") and \
            action.note is not None:
            help += '\n NB: %(note)s'
        return help
