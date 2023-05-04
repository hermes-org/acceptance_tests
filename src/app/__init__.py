"""General app configuration."""

import os
import platform

if platform.system() == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# no kivy imports allowed before os.environ is set, see kivy docs
from kivy.config import Config # pylint: disable=wrong-import-position

Config.set('graphics', 'width', 1000)
Config.set('graphics', 'minimum_height', 400)
Config.set('graphics', 'minimum_width', 600)
Config.set('graphics', 'height', 600)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'exit_on_escape', '0')
