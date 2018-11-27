[![CodeFactor](https://www.codefactor.io/repository/github/dadmoscow/pyrandr2/badge)](https://www.codefactor.io/repository/github/dadmoscow/pyrandr2)
# pyrandr2
Module for working with displays as objects

### Setup

```
git clone https://github.com/dadmoscow/pyrandr2.git
cd pyrandr2
python3 setup.py install
```

## Example usage
```python
import pyrandr2

# show connected displays
pyrandr2.connected_displays()

# get first display
s1 = pyrandr2.connected_displays()[0]

# get display setting
s1.name
s1.is_enabled
s1.is_primary
s1.resolution
s1.rotation

# get available modes
s1.available_modes

# get available resolutions
s1.available_resolutions()

# set another setting
s1.is_primary = True
s1.rotation = 'inverted' # or s1.rotation = 180

# check and set new resolution
s1.check_resolution((1600, 1200))
s1.resolution = (1600, 1200)

# build xrandr command for check
s1.build_cmd()

# join displays, set new position
s1.position = ('rightof', 'HDMI-1')

# apply new setting
s1.apply_settings()
```
