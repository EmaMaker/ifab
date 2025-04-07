from enum import Enum, auto
from textwrap import TextWrapper, indent


class StyleBox(Enum):
    Double = auto()  # ══════════
    Light = auto()  # ─────────
    Bold = auto()  # ━━━━━━━━━━━
    Dash_Bold = auto()  # ┅┅┅┅┅┅┅┅┅┅
    Dash_Light = auto()  # ┄┄┄┄┄┄┄┄┄┄


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

wrapper = TextWrapper(width=150)

def messageBox(who, text):
    print(f"{who}:")
    wrapped_text = []
    for line in text.splitlines():
        wrapped_text.extend(wrapper.wrap(line))
    print(indent(create_box("\n".join(wrapped_text), StyleBox.Bold), "  "))
