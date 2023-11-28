from flameshow.models import Profile
from flameshow.render.framedetail import FrameStatAll
from ..utils import create_frame


def test_render_self_value_all_instance():
    root = create_frame({
        "id": 0,
        "values": [10],
        "children": [
            {"id": 1, "values": [4], "children": []},
        ],
    })
    profile = Profile("asdf", root, 0, 0, [], {})
    widget = FrameStatAll(root, profile, 0)
    value = widget.frame_all_self_value
    assert value == 6

    child_frame = root.children[0]

    widget = FrameStatAll(child_frame, profile, 0)
    value = widget.frame_all_self_value
    assert value == 4
