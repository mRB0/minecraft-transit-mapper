#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import itertools
import logging
from pprint import pprint, pformat
import math
import argparse

import cairo

import cairofont

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-7s %(message)s")

face = cairofont.create_cairo_font_face_for_file("/cygdrive/c/Windows/Fonts/verdana.ttf")

####

class Mapper(object):

    def __init__(self, map_specs):
        self.l = map_specs
        self.draw_region = tuple([sz * self.l.draw_area / self.l.scale
                                  for sz in self.l.output_size])

    def get_loc(self, loc_name):
        loc = [l for l in self.l.locations if l['name'] == loc_name][0]
        return loc

    # memoize this
    def get_dests(self, loc_name):
        '''
        return all the destinations for loc_name, as a sequence of tuples:

        [('name', time_in_seconds_or_None, list_of_hops),
        ...]
        '''
        loc = self.get_loc(loc_name)
        dests = []

        for d in loc['destinations']:
            if isinstance(d, str) or isinstance(d, unicode):
                name = d
                hops = []
                seconds = None
            else:
                name = d[0]

                # destination hops
                if len(d) == 2:
                    hops = []
                else:
                    # fill in missing parts
                    hops = []
                    last_coord = list(loc['location'])
                    for hop in d[2]:
                        resolved_hop = []
                        for coord_idx in range(3):

                            if hop[coord_idx] is None:
                                coord = last_coord[coord_idx]
                            else:
                                coord = hop[coord_idx]
                                last_coord[coord_idx] = coord

                            resolved_hop.append(coord)

                        hops.append(resolved_hop)


                # time in seconds
                if len(d) >= 1 and d[1] is not None:
                    tm = d[1]
                    if ':' in tm:
                        tm = [int(x) for x in tm.split(':')]
                        seconds = tm[0] * 60 + tm[1]
                    else:
                        seconds = int(tm)
                else:
                    seconds = None

            dests.append((name, seconds, hops))

        return dests

    def get_dest(self, loc_name, to_name):
        '''
        return loc_name's destination named to_name,
        '''

        dests = self.get_dests(loc_name)
        for d in dests:
            if d[0] == to_name:
                return d


    def triphops(self, fr_name, to_name, include_endpoints=False):
        dest = self.get_dest(fr_name, to_name)

        if include_endpoints:
            fr = self.get_loc(fr_name)
            to = self.get_loc(to_name)
            return [fr['location']] + dest[2] + [to['location']]
        else:
            return dest[2]

    def longest_path(self, loc1_name, loc2_name, include_endpoints=True):
        paths = [self.triphops(loc1_name, loc2_name, include_endpoints),
                 self.triphops(loc2_name, loc1_name, include_endpoints)]

        if len(paths[0]) > len(paths[1]):
            return paths[0]
        else:
            return paths[1]


    # memoize this
    def bounds(self):
        locs = [l['name'] for l in self.l.locations]
        coords = []
        for loc_name in locs:
            loc = self.get_loc(loc_name)
            coords.append(loc['location'])

            dests = self.get_dests(loc_name)
            for dest in dests:
                coords += self.triphops(loc_name, dest[0], True)

        top_left = []
        bottom_right = []

        for index in range(3):
            indexed_coords = [coord[index] for coord in coords]
            top_left.append(min(indexed_coords))
            bottom_right.append(max(indexed_coords))

        return (top_left, bottom_right)

    def map2img(self, x, y, z):
        tl, br = self.bounds()

        x_range = (br[0] - tl[0])
        img_x = (x - tl[0]) / x_range * self.draw_region[0]

        z_range = (br[2] - tl[2])
        img_y = (z - tl[2]) / z_range * self.draw_region[0]

        return img_x, img_y

    def draw_connecting_lines(self, ctx):
        colors = itertools.cycle(self.l.route_colors)
        ctx.set_line_width(5)

        drawn_paths = set()

        for loc in self.l.locations:
            dests = self.get_dests(loc['name'])
            for dest in dests: 
                path = tuple(sorted([loc['name'], dest[0]]))
                if path in drawn_paths:
                    continue

                hops = self.longest_path(loc['name'], dest[0])

                ctx.new_path()

                fr = self.map2img(*hops[0])
                ctx.move_to(*fr)

                for hop in hops[1:]:
                    to = self.map2img(*hop)
                    ctx.line_to(*to)

                color = colors.next()
                ctx.set_source_rgb(*color)
                ctx.stroke()

                drawn_paths.add(path)

    def plot_locations(self, ctx):
        ctx.set_line_width(1)

        for loc in self.l.locations:
            name = loc['name']
            plot = self.map2img(*loc['location'])

            logging.info('{} at {}'.format(name, plot))

            # draw a circle for the location

            # clear the area around (cut off the route lines) for prettying
            ctx.new_path()
            ctx.set_source_rgb(*self.l.bg_color)
            ctx.arc(plot[0], plot[1], 10, 0, 2 * math.pi)
            ctx.fill()

            # draw a filled circle for the location
            ctx.new_path()
            ctx.set_source_rgb(*self.l.location_color)
            ctx.arc(plot[0], plot[1], 3.5, 0, 2 * math.pi)
            ctx.fill()

            # and put a circle around it
            ctx.new_path()
            ctx.set_source_rgb(*self.l.location_color)
            ctx.arc(plot[0], plot[1], 6, 0, 2 * math.pi)
            ctx.stroke()

            # label the location

            ctx.set_font_face(face)
            ctx.set_font_size(self.l.font_size)
            x_off, y_off, text_w, text_h = ctx.text_extents(name)[:4]
            text_x = plot[0] - x_off - text_w / 2

            bottom_edge = plot[1] - (self.l.locplot_pad * 3.5) # technically just half the plot size, to move above the square; but then we add the same amount again as padding, so it's locplot_size / 2 * 2
            text_y = bottom_edge - y_off - text_h

            pad = self.l.locplot_pad

            textrect = (text_x + x_off - pad, text_y + y_off - pad,
                        text_w + pad * 2, text_h + pad * 2)

            # text inset overlay background
            ctx.new_path()
            ctx.rectangle(*textrect)
            ctx.set_source_rgba(*self.l.label_bg_color)
            ctx.fill()

            # and border
            ctx.new_path()
            ctx.rectangle(*textrect)
            ctx.set_source_rgb(*self.l.label_border_color)
            ctx.stroke()

            # and the text
            ctx.move_to(text_x, text_y)
            ctx.set_source_rgb(*self.l.label_text_color)
            ctx.show_text(name)


    def build(self, fn):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *self.l.output_size)
        ctx = cairo.Context(surface)

        ctx.new_path()
        ctx.rectangle(0, 0, *self.l.output_size)
        ctx.set_source_rgb(*self.l.bg_color)
        ctx.fill()

        pad = [(sz - (sz * self.l.draw_area)) / 2 for sz in self.l.output_size]
        ctx.translate(*pad)
        ctx.scale(*([self.l.scale] * 2))

        self.draw_connecting_lines(ctx)
        self.plot_locations(ctx)

        surface.write_to_png(fn)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a transit map.')

    parser.add_argument('-o',
                        metavar='OUTFILE',
                        type=str,
                        required=False,
                        help="Output filename (overrides whatever's specified inside LOC_FILE)")

    parser.add_argument('loc_file',
                        metavar='LOC_FILE',
                        type=str,
                        default='locations',
                        nargs='?',
                        help='Location file to import; default is locations')
    
    args = parser.parse_args()

    loc_file = args.loc_file
    if loc_file.endswith('.py'):
        loc_file = loc_file[:-3]

    locs = __import__(loc_file)
    
    if args.o is None:
        outfile = locs.output_filename
    else:
        outfile = args.o
    
    Mapper(locs).build(outfile)
