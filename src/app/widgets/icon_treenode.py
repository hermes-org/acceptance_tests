"""
Custom treeview label.
"""

from kivy.uix.treeview import TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_file("app/widgets/icon_treenode.kv")

class TreeViewImageLabel(BoxLayout, TreeViewNode):
    """Custom treeview label with image and text."""

    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)

        self.text = text
        self.color = (1,1,1,1)

    @property
    def text(self)->str:
        """Text property."""
        return self.ids.lbl.text

    @text.setter
    def text(self, text):
        self.ids.lbl.text = text

    @property
    def color(self):
        """Color property."""
        return self.ids.lbl.color

    @color.setter
    def color(self, color):
        self.ids.lbl.color = color

# TODO: add icon support
#    def set_image(self, source: str):
#        self.ids.img.source = source
