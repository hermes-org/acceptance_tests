"""User interface for IPC-Hermes 9852 test system."""

import logging
from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

# pylint: disable=import-error
from app.widgets.icon_treenode import TreeViewImageLabel
from mgr.hermes_test_manager import hermes_test_api
from mgr.hermes_test_manager.callback_tags import CbEvt

class Hitmanager(Widget):
    """Main widget for HitManager. So far just one window
       and MVC pattern is not used.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._log = logging.getLogger('hitmanager')
        self._available_tests = hermes_test_api.available_tests()
        self._tree = self.ids.testlist_tv

        test_modules = []
        for test_info in hermes_test_api.available_tests().values():
            if test_info.module not in test_modules:
                test_modules.append(test_info.module)
                module_node = TreeViewImageLabel(text=test_info.module, is_leaf=False)
                self._tree.add_node(module_node, self._tree.root)

            test_node = TreeViewImageLabel(text=test_info.name, is_leaf=True,
                                           on_touch_down=self.treeview_touch_down)
            self._tree.add_node(test_node, module_node)

        self._reset_ui()
        rst_text = "Welcome to Hermes 9852 Interface Test Manager\n"
        self.ids.test_info.text = rst_text

    def treeview_touch_down(self, node=None, touch=None) -> bool:
        """Treeview touch down event handler
           resets ui and highlight selection but don't run test.
        """
        self._reset_ui()
        if node is not None:
            selected_test = node.text
            test_info = self._available_tests.get(selected_test)
            # display test info
            name = selected_test.replace('_', ' ').title()
            rst_text = f"**{test_info.tag}**\n\n"
            rst_text += name + "\n"
            rst_text += "=" * len(name) + "\n\n"
            rst_text += test_info.description
            self.ids.test_info.text = rst_text
            # update graphic
            if 'upstream' in test_info.module:
                self.ids.img_upstream1.opacity = 1
                self.ids.img_upstream2.opacity = 1
            else:
                self.ids.img_upstream1.opacity = 0
                self.ids.img_upstream2.opacity = 0
            if 'downstream' in test_info.module:
                self.ids.img_downstream1.opacity = 1
                self.ids.img_downstream2.opacity = 1
            else:
                self.ids.img_downstream1.opacity = 0
                self.ids.img_downstream2.opacity = 0
        return True

    def run_selected_tests(self) -> None:
        """Button press event handler to run selected tests."""
        selected_test = self._tree.selected_node.text
        if selected_test not in self._available_tests:
            return
        self._log.debug('button: run selected tests')
        self._running_ui()
        thread = Thread(target=self._run_selected_test, args=(selected_test,))
        thread.start()

    def user_confirm(self, val: bool):
        """Button press event handler for user confirmation."""
        self.ids.instruction_label.text = 'Pressed: ' + str(val)

    # pylint: disable=unused-argument
    def test_callback(self, text: str, from_func: str, evt: CbEvt, **kwargs):
        """Hermes test API callback function."""
        Clock.schedule_once(lambda _: self._callback(text, from_func, evt, **kwargs))

    def _callback(self, text: str, from_func: str, evt: CbEvt, **kwargs):
        """Hermes test API callback function in main thread."""
        if text is not None:
            old_text = self.ids.instruction_label.text
            self.ids.instruction_label.text = f"{old_text}\n{text}"

    def _run_selected_test(self, selected_test):
        result = hermes_test_api.run_test(selected_test, self.test_callback, True)
        Clock.schedule_once(lambda _: self._done_ui(result))

    def _reset_ui(self):
        """Reset user interface. Use when changing selection."""
        self.ids.state_label.text = ''
        self.ids.state_label.background_color = (0.5, 0.5, 0.5, 1)
        self.ids.instruction_label.text = ''

    def _running_ui(self):
        """Set user interface to running state."""
        self.ids.btn_run.disabled = True
        self._reset_ui()
        self.ids.state_label.text = "Running"
        self._tree.selected_node.color = (0, 1, 1, 1)

    def _done_ui(self, result: bool):
        """Reset user interface after test."""
        if result:
            self.ids.state_label.text = "Success"
            self.ids.state_label.background_color = (0, 1, 0, 1)
            self._tree.selected_node.color = (0, 1, 0, 1)
        else:
            self.ids.state_label.text = "Fail"
            self.ids.state_label.background_color = (1, 0, 0, 1)
            self._tree.selected_node.color = (1, 0, 0, 1)
        self.ids.btn_run.disabled = False

class HitmanagerApp(App):
    """Main application class for HitManager."""

    title = 'IPC-9852 Hermes interface tester'

    def build(self):
        return Hitmanager()


if __name__ == '__main__':
    HitmanagerApp().run()
