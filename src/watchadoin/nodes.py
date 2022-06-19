class Item:
    def __init__(self, parent=None, id=None) -> None:
        self.id = id
        self._parent = None
        if parent:
            self.parent = parent

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, x):
        self._id = x

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, other):
        if self._parent is not None:
            if self._parent.has_child(self):
                self._parent.remove_child(self)
        self._parent = other
        if isinstance(other, Node):
            other.add_child(self)

    def level(self) -> int:
        if self._parent:
            return self._parent.level()
        return 0

    def accept(self, visitor):
        visitor.visit(self)


class Node(Item):
    def __init__(self, parent=None, id=None) -> None:
        self._children = []
        super().__init__(parent=parent, id=id)

    def level(self) -> int:
        if self.parent:
            return self.parent.level() + 1
        return 0

    def add_child(self, other):
        if not self.has_child(other):
            self._children.append(other)
        if not other._parent == self:
            other.set_parent(self)

    def remove_child(self, other):
        index = self._children.index(other)
        return self._children.pop(index)

    @property
    def children(self):
        return self._children

    def has_child(self, child):
        if child in self._children:
            return True
        else:
            return False


class ContentNode(Node):
    def __init__(self, parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)
        self._contents = []

    def add_content(self, content) -> None:
        self._contents.append(content)

    @property
    def contents(self):
        return self._contents


class Empty(Item):
    def __init__(self, parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)


class Tag(Item):
    def __init__(self, name=None, parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)
        self.name = name


class TextTag(Tag):
    def __init__(self, name=None, value=None, parent=None, id=None) -> None:
        super().__init__(name=name, parent=parent, id=id)
        self.value = value


class DateTag(Tag):
    def __init__(self, name=None, value=None, parent=None, id=None) -> None:
        super().__init__(name=name, parent=parent, id=id)
        self.value = value


class DateTimeTag(Tag):
    def __init__(self, name=None, value=None, parent=None, id=None) -> None:
        super().__init__(name=name, parent=parent, id=id)
        self.value = value


class IntTag(Tag):
    def __init__(self, name=None, value=None, parent=None, id=None) -> None:
        super().__init__(name=name, parent=parent, id=id)
        self.value = value


class FloatTag(Tag):
    def __init__(self, name=None, value=None, parent=None, id=None) -> None:
        super().__init__(name=name, parent=parent, id=id)
        self.value = value


class Text(Item):
    def __init__(self, value=None, parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)
        self.value = value


class TaskPaperDocument(Node):
    def __init__(self, parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)


class Project(Node):
    def __init__(self, name, parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)
        self.name = name
        self._tag = None

    def attach_tag(self, tag: Tag) -> None:
        self._tag = tag

    @property
    def tag(self):
        return self._tag

    def has_tag(self):
        return self._tag is not None


class Task(ContentNode):
    def __init__(self, symbol="-", parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)
        self.symbol = symbol


class Doing(Task):
    def __init__(self, date, symbol="-", parent=None, id=None) -> None:
        super().__init__(symbol=symbol, parent=parent, id=id)
        self.date = date


class Note(ContentNode):
    def __init__(self, parent=None, id=None) -> None:
        super().__init__(parent=parent, id=id)
