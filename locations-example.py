# -*- coding: utf-8 -*-

#
# Copy this to locations.py and put in your own custom locations and
# appearance.
#

# Locations.

locations = [{'name': 'Northland',
              'location': (-277, 78, -811),
              'destinations': (('Midnorth',
                                '1:12',
                                [[None, None, -540], [-164, None, None]]),)},
             {'name': 'Midnorth',
              'location': (-164, 53, -360),
              'destinations': (('Northland', '1:14'),
                               ("Keeper's keep", '58'))},
             {'name': "Keeper's keep",
              'location': (-169, 72, 11),
              'destinations': (('Lower NPCville',
                                None,
                                [[191, None, None], [None, None, 326]]),
                               ('Spawn',
                                '43'),
                               ('Midnorth', '54'))},
             {'name': 'Lower NPCville',
              'location': (210, 66, 324),
              'destinations': (("Keeper's keep", '1:44'),
                               ('Upper NPCville',
                                None,
                                [[663, None, None], [None, None, 685]]))},
             {'name': 'Upper NPCville',
              'location': (861, 63, 682),
              'destinations': (('Lower NPCville', '2:11'),)},
             {'name': 'Spawn',
              'location': (-165, 56, 231),
              'destinations': ("Keeper's keep",
                               ('Distant Valley',
                                '4:45',
                                [[-181, None, 330],
                                 [None, None, 796],
                                 [-496, None, None],
                                 [None, None, 891],
                                 [-556, None, None],
                                 [None, None, 1172]]),
                               ('Montcuq',
                                '1:36',
                                [[526, None, None]]))},
             {'name': 'Distant Valley',
              'location': (-993, 63, 1321),
              'destinations': (('Spawn', '4:59'),)},
             {'name': 'Montcuq',
              'location': (522, 65, 180),
              'destinations': ('Spawn',
                               ('Kanave', '1:15'))},
             {'name': 'Kanave',
              'location': (360, 59, -132),
              'destinations': ('Montcuq',)}]

# Output image filename.
# Can be overridden by using -o upon invocation.
output_filename = "locations-example.png"

# The size of the output image in pixels (width, height).
output_size = (1024, 1024)

# The fraction of the output_size where locations will be plotted.
# eg. 1.0 will plot locations on the very edges of the map, and 0.5
# will only use half the output space (eg 512 pixels in the center of
# a 1024-sized image).
draw_area = 0.85

# Scale everything.  Increasing this will make everything draw larger
# and closer together, and correspondingly decrease the space
# available for plotting.  Decreasing it will do the opposite.  1.0
# places everything as it appears in the code.
scale = 1.0

# How much space to put between a location plot and the text.  This is
# fuzzy at the moment, and also (erroneously) affects how much padding
# you get between the text and the border surrounding the text.  For
# both cases, larger number = more space.
locplot_pad = 5

# A list of colors to display routes in.  Each route will be drawn
# using the next available color in this list, cycling back to the
# first one when the list is exhausted.  These are RGB tuples from 0
# to 1.0.
route_colors = ((0.75, 0.25, 0.25),
                (0.25, 0.75, 0.25),
                (0.25, 0.25, 0.75),
                (0.75, 0.75, 0.25),
                (0.75, 0.25, 0.75),
                (0.25, 0.75, 0.75))

# Color for the location dots.
location_color = (0, 0, 0)

# Location label text color.
label_text_color = (0.5, 0, 0)

# Label background color (RGBA).
label_bg_color = (1, 1, 1, 0.75)

# Color for the location dots.
label_border_color = (0, 0, 0)

# Location label font size.
font_size = 13

# Background color
bg_color = (1, 1, 1)

