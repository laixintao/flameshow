from flameshow.pprof_parser.parser import Line, PprofFrame, Frame


def test_pile_up():
    root = Frame("root", 0, values=[5])
    s1 = Frame("s1", 1, values=[4], parent=root)
    s2 = Frame("s2", 2, values=[4], parent=s1)

    root.children = [s1]
    s1.children = [s2]

    s1 = Frame("s1", 3, values=[3], parent=None)
    s2 = Frame("s2", 4, values=[2], parent=s1)
    s1.children = [s2]

    root.pile_up(s1)
    assert root.children[0].values == [7]
    assert root.children[0].children[0].values == [6]


def test_render_detail_when_parent_zero():
    root = PprofFrame("root", 0, values=[0])
    s1 = PprofFrame("s1", 1, values=[0], parent=root, root=root)
    s1.line = Line()
    s1.line.function.name = "asdf"

    detail = s1.render_detail(0, "bytes")
    assert "asdf: 0.0B" in str(detail)
