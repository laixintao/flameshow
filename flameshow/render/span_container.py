import logging
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget


from .span import Span

logger = logging.getLogger(__name__)


class SpanContainer(Widget):
    DEFAULT_CSS = """
    SpanContainer {
      layout: vertical;
    }
    """

    def __init__(self, root_stack, my_width, level, i, sample_unit, *args, **kwargs):
        """
        Args:
            level: recursive render level limit
        """
        super().__init__(*args, **kwargs)
        self.root_stack = root_stack
        self.my_width = my_width
        self.level = level
        self.i = i
        self.sample_unit = sample_unit

    def compose(self) -> ComposeResult:
        # render current all the way down, until one got multi children

        current_stack = self.root_stack

        width = 1

        while 1:
            is_deepest_level = self.level == 0 and len(current_stack.children) > 1

            yield Span(
                current_stack,
                is_deepest_level,
                sample_index=self.i,
                sample_unit=self.sample_unit,
                my_width=width,
            )

            if is_deepest_level or not current_stack.children:
                return

            if len(current_stack.children) > 1:
                break

            current_stack_value = current_stack.values[self.i]
            if not current_stack_value:  # devide by zero
                return
            c0 = current_stack.children[0]
            # sometimes, child is not 100% of parent
            # even when only one child
            width = width * c0.values[self.i] / current_stack_value
            current_stack = c0

        yield self.render_children(current_stack, width)

    def on_mount(self) -> None:
        self.styles.width = self.my_width

    def render_children(self, stack, parent_width):
        total = stack.values[self.i]
        children = stack.children
        if not total:
            return Horizontal()

        ordered_children = sorted(
            children, key=lambda c: c.values[self.i], reverse=True
        )
        max_children_of_this_level = self.level
        render_children_ids = set(
            [s._id for s in ordered_children[:max_children_of_this_level]]
        )

        widgets = []
        for child in children:
            w = child.values[self.i] / total * parent_width * 100
            style_w = f"{w:.2f}%"

            if child._id in render_children_ids:
                level = self.level - 1
            else:
                level = 0
            widgets.append(
                SpanContainer(
                    child, style_w, level=level, i=self.i, sample_unit=self.sample_unit
                )
            )

        return Horizontal(*widgets)
