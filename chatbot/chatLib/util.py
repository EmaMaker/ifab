import argparse
import os
import shutil
import traceback
from enum import Enum, auto
from textwrap import TextWrapper, indent


class StyleBox(Enum):
    Double = auto()  # ══════════
    Light = auto()  # ─────────
    Bold = auto()  # ━━━━━━━━━━━
    Dash_Bold = auto()  # ┅┅┅┅┅┅┅┅┅┅
    Dash_Light = auto()  # ┄┄┄┄┄┄┄┄┄┄
    Error = auto()  # Per messaggi di errore


"""
@:param string: String, with multiple line, to wrap inside a box
@:param style: List with 6 element with the style block, if not chosen, use the default 
"""


def create_box(string, styleName: StyleBox = StyleBox.Double) -> str:
    match styleName:
        case StyleBox.Double:
            corner = ("╔", "╗", "╚", "╝", "═", "║")
        case StyleBox.Bold:
            corner = ("┏", "┓", "┗", "┛", "━", "┃")
        case StyleBox.Light:
            corner = ("┌", "┐", "└", "┘", "─", "│")
        case StyleBox.Dash_Bold:
            corner = ("┏", "┓", "┗", "┛", "┅", "┇")
        case StyleBox.Dash_Light:
            corner = ("╭", "╮", "╰", "╯", "┄", "┆")
        case StyleBox.Error:
            corner = ("┏", "┓", "┗", "┛", "┅", "┇")  # Usa lo stesso stile di Dash_Bold per gli errori
        case _:
            corner = ("╔", "╗", "╚", "╝", "═", "║")
    lines = string.replace("\t", "  ").splitlines()
    max_length = max(map(len, lines))
    box_width = max_length + 4
    # Draw box
    box = corner[0] + corner[4] * (box_width - 2) + corner[1] + "\n"
    box += "\n".join([f"{corner[5]} {line.ljust(max_length)} {corner[5]}" for line in lines])
    box += "\n" + corner[2] + corner[4] * (box_width - 2) + corner[3]
    return box


def getTermWidth(minRet: int = 0) -> int:
    terminal_size = shutil.get_terminal_size(fallback=(180, 60))  # fallback to width 180, because is bamboo log viewer max size (at 100% zoom)
    return max(terminal_size.columns, minRet)

wrapper = TextWrapper(width=getTermWidth(120) - 10)


def messageBox(who, text, style=StyleBox.Bold):
    print(f"{who}:")
    wrapped_text = []
    if not text:
        text = f"Call without text, stack trace: {traceback.format_exc()}"
    for line in text.splitlines():
        wrapped_text.extend(wrapper.wrap(line))
    print(indent(create_box("\n".join(wrapped_text), style), "  "))


# Default format helper class
formatHelp = lambda prog: CustomFormatter(prog, max_help_position=50, width=getTermWidth(60))


# TODO: modificare i metodi affichè il padre invii al figlio i suoi argomenti, così che si possa risalire all'usage completo
class TreeParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        super().print_help(file)
        print(f"\nCommand tree:\n{subparserTree(self)}")


class CustomFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Corrected _max_action_length for the indenting of subactions
    """

    def add_argument(self, action):
        if action.help is not argparse.SUPPRESS:
            # find all invocations
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            current_indent = self._current_indent
            for subaction in self._iter_indented_subactions(action):
                # compensate for the indent that will be added
                indent_chg = self._current_indent - current_indent
                added_indent = 'x' * indent_chg
                invocations.append(added_indent + get_invocation(subaction))
            # print('inv', invocations)

            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length, action_length)
            # add the item to the list
            self._add_item(self._format_action, [action])

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    # parts.append('%s %s' % (option_string, args_string))
                    parts.append('%s' % option_string)
                parts[-1] += ' %s' % args_string
            return ', '.join(parts)


def __option_strings_formatter(parser) -> str:
    # TODO: Capire se serve questa funzione o si riesce a rubare dall'help normale l'usage
    retStr = ""
    if parser._optionals:  # Add options if present
        options_str = []
        positional_str = []
        for action in parser._optionals._actions:
            if isinstance(action, argparse._SubParsersAction):
                continue  # Skip argparse._SubParsersAction because tree vision use it to move
            pars = []  # Init Str
            if action.option_strings:  # if optional argument, add option selector, short priority
                pars.append(f"{action.option_strings[0]}")
            # MetaVar of option, custom or default
            if action.metavar:
                metaJoin = "...".join(action.metavar)
                pars.append(f"{metaJoin}" if not isinstance(action.metavar, str) else f"{action.metavar}")
            elif (action.nargs or action.required) and action.dest:
                pars.append(f"{action.dest.upper()}")
            # Add to the right list only if something are present
            if pars:
                parStr = " ".join(pars)
                parStr = f"{parStr}" if action.required else f"[{parStr}]"
                options_str.append(parStr) if action.option_strings else positional_str.append(parStr)
        # Order the list and add to line
        if positional_str:
            positional_str.sort()  # Order to keep before required parameters and positional arguments
            retStr += " " + " ".join(positional_str)
        if options_str:
            options_str.sort()  # Order to keep before required parameters and positional arguments
            retStr += " " + " ".join(options_str)
        return retStr


def subparserTree(parser: argparse.ArgumentParser, start="", down=("│", " "), leaf=("├", "╰"), item=("┬", "─", "╴"), indInc=1) -> str:
    subparsers_actions = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
    strOut = f"{parser.prog} {__option_strings_formatter(parser)}\n" if not start else ""
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            endSublist = choice == list(subparsers_action.choices.keys())[-1]
            strOut += start + (leaf[endSublist] + item[1] * indInc)
            retString = subparserTree(subparser, start=start + (down[endSublist] + " " * indInc), down=down, leaf=leaf, indInc=indInc)
            strOut += item[0] if retString else ""
            strOut += item[2] + choice + __option_strings_formatter(subparser) + "\n" + retString
    return strOut
