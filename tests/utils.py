from flameshow.models import Frame


def create_frame(data, id_store=None):
    name = "node-{}".format(data["id"])
    if "name" in data:
        name = data["name"]
    root = Frame(
        name=name,
        _id=data["id"],
        values=data["values"],
    )
    root.children = []
    for child in data["children"]:
        cf = create_frame(child, id_store)
        root.children.append(cf)
        cf.parent = root

    if id_store is not None:
        id_store[root._id] = root
    return root


def frame2json(frame):
    data = {
        frame.name: {
            "values": frame.values,
            "children": [frame2json(c) for c in frame.children],
        }
    }
    return data
