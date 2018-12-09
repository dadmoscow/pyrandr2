"""
Pyrandr2

Module for working with displays as objects
"""
from subprocess import check_output, STDOUT
from re import compile as re_compile


class Mode(object):
    """
    For work with supported display mods

    Args:
        width (int)
        height (int)
        freq (float)
        current (bool)
        preferred (bool)
    """

    def __init__(self, width, height, freq, current, preferred):
        super(Mode, self).__init__()
        self.width = width
        self.height = height
        self.freq = freq
        self.current = current
        self.preferred = preferred

    def resolution(self, string=False):
        """
        Get resolution

        Args:
             string (bool): is True -- return as str format

        Examples:
            >>> m = Mode(1920,1080, 60.0, True, True)
            >>> m.resolution()
            (1920, 1080)
            >>> m.resolution(True)
            '1920x1080'

        Returns:
             tuple: (width, height)
        """
        if string:
            return '{0}x{1}'.format(self.width, self.height)
        return self.width, self.height

    def __str__(self):
        return '<{0}, {1}, curr: {2}, pref: {3}>'.format(self.resolution(True),
                                                         self.freq,
                                                         self.current,
                                                         self.preferred)

    __repr__ = __str__


class ScreenSettings(object):
    """
    Class for set and get screen setting

    Attributes:
        name (str)
        resolution (tuple)
        is_primary (bool)
        is_enabled (bool)
        rotation (str)
        position (tuple)
        is_connected (bool)
    """

    def __init__(self):
        super(ScreenSettings, self).__init__()
        self.name = None
        self.resolution = (0, 0)
        self.is_primary = False
        self.is_enabled = True
        self.rotation = None
        self.position = (None, None)
        self.is_connected = True
        self.curr_mode = None
        self.modes = []

        self.change_table = {"resolution": False,
                             "is_primary": False,
                             "is_enabled": False,
                             "rotation": False,
                             "position": False}


class Display(object):
    """
    Class for work with display as object

    Args:
        name (str): output name
        raw_setting (dict): setting for first create Display object
    """
    def __init__(self, name, raw_setting):
        super(Display, self).__init__()
        self.__cfg = ScreenSettings()
        self.rot_convert = RotateDirection()
        self.pos_convert = PositionType()

        self.__cfg.name = name
        self.update_setting(raw_setting)

    @property
    def name(self):
        """str: output Display name"""
        return self.__cfg.name

    @property
    def current_mode(self):
        """obj: Current Mode object"""
        return self.__cfg.curr_mode

    @property
    def is_changed(self):
        """dict: Get change table"""
        return self.__cfg.change_table

    @property
    def is_connected(self):
        """bool: Get connected status"""
        return self.__cfg.is_connected

    @property
    def available_modes(self):
        """list: Get all available modes"""
        return self.__cfg.modes

    @property
    def position(self):
        """tuple: Get or set positions

        For set use (position, relative_to)
        """
        return self.__cfg.position

    @position.setter
    def position(self, new_pos):
        if new_pos != self.__cfg.position:
            self.__cfg.position = (new_pos[0].lower(), new_pos[1])
            self.__cfg.change_table["position"] = True

    @property
    def is_enabled(self):
        """bool: Get or set turn on status"""
        return self.__cfg.is_enabled

    @is_enabled.setter
    def is_enabled(self, enable):
        if enable != self.__cfg.is_enabled:
            self.__cfg.is_enabled = not self.__cfg.is_enabled
            self.__cfg.change_table["is_enabled"] = not self.__cfg.change_table["is_enabled"]

    @property
    def is_primary(self):
        """bool: Get or set primary status"""
        return self.__cfg.is_primary

    @is_primary.setter
    def is_primary(self, is_primary):
        if is_primary != self.__cfg.is_primary:
            self.__cfg.is_primary = not self.__cfg.is_primary
            self.__cfg.change_table["is_primary"] = not self.__cfg.change_table["is_primary"]

    @property
    def resolution(self):
        """tuple: Get or set resolution"""
        return self.__cfg.resolution

    @resolution.setter
    def resolution(self, new_res, custom=False):
        if not self.is_enabled and not self.is_changed["is_enabled"]:
            raise ValueError('The Screen is off')
        if new_res != self.__cfg.resolution:
            if not custom:
                self.check_resolution(new_res)
            self.__cfg.resolution = new_res
            self.__cfg.change_table["resolution"] = True

    @property
    def rotation(self):
        """str: Get or set rotation"""
        return self.__cfg.rotation

    @rotation.setter
    def rotation(self, direction):
        if isinstance(direction, int):
            direction = self.rot_convert[direction]
        if direction != self.__cfg.rotation:
            self.__cfg.rotation = direction
            self.__cfg.change_table["rotation"] = True

    def available_resolutions(self, string=False):
        """
        Get all available resolutions

        Args:
            string (bool): if set True -> return resolution as string format

        Returns:
            list: [(width, height), ...]
        """
        if string:
            return [r.resolution(True) for r in self.__cfg.modes]
        return [r.resolution() for r in self.__cfg.modes]

    def check_resolution(self, new_res):
        """
        Check resolution has in available modes

        Args:
            new_res (tuple): (width, height)

        Raises:
            ValueError: if new_res not in available modes
        """
        if new_res not in self.available_resolutions():
            raise ValueError('Requested resolution is not supported', new_res)

    def build_cmd(self):
        """
        Build command for apply new Display settings

        Returns:
             list: command if Display settings has been changed or False
        """
        # if has changed display settings
        if any(self.is_changed.values()):

            cmd = ['xrandr', '--output', self.name]

            # if display be disabled
            if self.is_changed['is_enabled'] and not self.is_enabled:
                cmd.append('--off')
                return cmd

            # add another settings if display not be disabled
            if self.is_changed['resolution']:
                cmd.extend(['--mode', '{0}x{1}'.format(*self.resolution)])
            else:
                cmd.extend(['--auto'])

            if self.is_primary and self.is_changed["is_primary"]:
                cmd.append('--primary')

            if self.is_changed["rotation"]:
                cmd.extend(['--rotate', self.rotation])

            if self.is_changed["position"]:
                rel, rel_to = self.position
                cmd.extend([self.pos_convert[rel], rel_to])

            return cmd
        return False

    def __reset_change_table(self):
        """
        Set False for all item in change_table
        """
        for key in self.__cfg.change_table:
            self.__cfg.change_table[key] = False

    def apply_settings(self, default=False):
        """
        Apply new setting

        Args:
            default (bool): if set True -> apply default best quality setting
        """
        if default:
            exec_cmd(['xrandr', '--output', self.name, '--auto'])
        else:
            if any(self.is_changed.values()):
                exec_cmd(self.build_cmd())
        self.update_setting()
        self.__reset_change_table()

    def update_setting(self, raw_setting=None):
        """
        Get and update actual settings

        Default parse setting from xrandr

        Args:
            raw_setting (dict): setting for current display
        """
        if not raw_setting:
            raw_setting = get_display_data(self.name)

        self.__cfg.modes = raw_setting['modes']

        for mode in raw_setting['modes']:
            if mode.current:
                self.__cfg.curr_mode = mode
                break
            self.__cfg.curr_mode = None

        self.__cfg.is_enabled = bool(self.__cfg.curr_mode)
        self.__cfg.is_connected = bool(self.__cfg.modes)
        self.__cfg.rotation = raw_setting['rot'] or self.rot_convert[0]
        self.__cfg.is_primary = bool(raw_setting['pr'])
        if self.is_enabled and self.current_mode:
            self.__cfg.resolution = self.__cfg.curr_mode.resolution()

        self.__reset_change_table()

    def __str__(self):
        return '<{0}, primary: {1}, modes: {2}, ' \
               'conn: {3}, rot: {4}, enabled: {5}>'.format(self.name,
                                                           self.is_primary,
                                                           len(self.available_modes),
                                                           self.is_connected,
                                                           self.rotation,
                                                           self.is_enabled)

    __repr__ = __str__


class RotateDirection(object):
    """
    Class with rotations

    Converting duration item for use with xrandr
    and reverse

    Attributes:
        normal, inverted, left, right

    Raises:
        ValueError: if value not in attributes

    Example:
        >>> r = RotateDirection()
        >>> r[0] -> 'normal'
        >>> r.left -> 270
    """

    __rotation = {0: 'normal',
                  90: 'right',
                  180: 'inverted',
                  270: 'left'}

    __inverted_rot = {v: k for k, v in __rotation.items()}

    def __getitem__(self, item):
        if isinstance(item, int):
            if item in self.__rotation:
                return self.__rotation[item]
        elif isinstance(item, str):
            item = item.lower().strip()
            if item in self.__inverted_rot:
                return self.__inverted_rot[item]
        raise ValueError('Invalid rotation ', item)

    __getattr__ = __getitem__


class PositionType(object):
    """
    Class with positions

    Converting "human" position item for use with xrandr

    Attributes:
        'above', 'below', 'leftof', 'rightof', 'sameas'

    Raises:
        ValueError: if value not in attributes

    Example:
        >>> p = PositionType()
        >>> p['LeftOf']
        '--left-of'
        >>> p.RightOf
        '--right-of'
    """
    __positions = {'leftof': '--left-of',
                   'rightof': '--right-of',
                   'above': '--above',
                   'below': '--below',
                   'sameas': '--same-as', }

    def __getitem__(self, item):
        if isinstance(item, str):
            item = item.lower()
            if item in self.__positions:
                return self.__positions[item]
        raise ValueError('Invalid position', item)

    __getattr__ = __getitem__


def exec_cmd(cmd):
    """
    Execute command and return stdout separate by newline

    Args:
        cmd (list): command

    Example:
        >>> exec_cmd(['xrandr', '--version'])
        'xrandr program version   1.5.0\nServer reports RandR version 1.5\n'

    Returns:
        list: strings split by new line
    """
    result = check_output(cmd, stderr=STDOUT)
    try:
        result = result.decode()
    except AttributeError:
        pass
    return result.splitlines()


def parse_xrandr(lines, raw=False):
    """
    Parsing xrandr output

    Args:
        lines (list): output func exec_cmd
        raw (bool): if True -> return list with raw data (for update exist Display)

    Return:
        list: Display objects
    """

    # {'out': 'HDMI-1', 'primary': None, 'rot': 'inverted', 'status': 'connected'}
    output = re_compile(
        r'^(?P<out>[\w-]+)\s(?P<status>connected)(?P<pr>\sprimary)?(\s[\w+]+)?(\s(?P<rot>\w+))?'
    )

    # {'current': '*', 'freq': '60.00', 'height': '1080', 'preferred': '+', 'width': '1920'}
    mode = re_compile(
        r'^\s+(?P<width>\d+)x(?P<height>\d+)\s+(?P<freq>(?:\d+\.)?\d+)(?P<curr>[*\s]?)?(?P<pref>[+\s]?)?'
    )

    connected_outputs = []
    modes = []

    for line in lines:
        find_out = output.search(line)
        if find_out:
            if modes:
                connected_outputs[-1].update({'modes': modes})
                modes = []
            connected_outputs.append(find_out.groupdict())
            continue
        find_mode = mode.search(line)
        if find_mode:
            mode_data = find_mode.groupdict()
            modes.append(Mode(
                int(mode_data["width"]),
                int(mode_data["height"]),
                float(mode_data["freq"]),
                bool(mode_data["curr"].strip()),
                bool(mode_data["pref"].strip())
            ))
    # if end of string -> add modes to last output
    if modes:
        connected_outputs[-1].update({'modes': modes})

    if raw:
        return connected_outputs

    displays = []
    for item in connected_outputs:
        displays.append(
            Display(
                item['out'],
                item,
            )
        )
    return displays


def get_display_data(output):
    """
    Get raw data for update exists Display object

    Args:
        output (str): output name

    Raises:
        ValueError: if invalid output name

    Return:
        dict: display raw data
    """
    for item in (scr for scr in parse_xrandr(exec_cmd(['xrandr']), True)):
        if item['out'] == output:
            return item
    raise ValueError('Invalid output', output)


def connected_displays():
    """
    Get all connected displays

    Return:
        list: Display objects
    """
    return [scr for scr in parse_xrandr(exec_cmd(['xrandr']))]


def enabled_displays():
    """
    Get enabled displays

    Return:
        list: Display objects if is_enabled is True
    """
    return [scr for scr in connected_displays() if scr.is_enabled]
