#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import itertools
import logging
from pprint import pprint, pformat
import math

import cairo

import cairofont

from locations import locations

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-7s %(message)s")

output_size = (1024, 1024)
draw_area = 0.85 # as a fraction of output_size

locplot_pad = 0.005

route_colors = ((0.75, 0.25, 0.25),
                (0.25, 0.75, 0.25),
                (0.25, 0.25, 0.75),
                (0.75, 0.75, 0.25),
                (0.75, 0.25, 0.75),
                (0.25, 0.75, 0.75))

face = cairofont.create_cairo_font_face_for_file("/cygdrive/c/Windows/Fonts/tahoma.ttf")

####

def get_loc(loc_name):
    loc = [l for l in locations if l['name'] == loc_name][0]
    return loc

# memoize this
def get_dests(loc_name):
    '''
    return all the destinations for loc_name, as a sequence of tuples:

    [('name', time_in_seconds_or_None, list_of_hops),
     ...]
    '''
    loc = get_loc(loc_name)
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
    
def get_dest(loc_name, to_name):
    '''
    return loc_name's destination named to_name,
    '''

    dests = get_dests(loc_name)
    for d in dests:
        if d[0] == to_name:
            return d
                

def triphops(fr_name, to_name, include_endpoints=False):
    dest = get_dest(fr_name, to_name)

    if include_endpoints:
        fr = get_loc(fr_name)
        to = get_loc(to_name)
        return [fr['location']] + dest[2] + [to['location']]
    else:
        return dest[2]

def longest_path(loc1_name, loc2_name, include_endpoints=True):
    paths = [triphops(loc1_name, loc2_name, include_endpoints),
             triphops(loc2_name, loc1_name, include_endpoints)]

    if len(paths[0]) > len(paths[1]):
        return paths[0]
    else:
        return paths[1]
    

# memoize this
def bounds():
    locs = [l['name'] for l in locations]
    coords = []
    for loc_name in locs:
        loc = get_loc(loc_name)
        coords.append(loc['location'])
        
        dests = get_dests(loc_name)
        for dest in dests:
            coords += triphops(loc_name, dest[0], True)
    
    top_left = []
    bottom_right = []
    
    for index in range(3):
        indexed_coords = [coord[index] for coord in coords]
        top_left.append(min(indexed_coords))
        bottom_right.append(max(indexed_coords))

    return (top_left, bottom_right)
        
def map2img(x, y, z):
    tl, br = bounds()
    
    x_range = (br[0] - tl[0])
    img_x = (x - tl[0]) / x_range

    z_range = (br[2] - tl[2])
    img_y = (z - tl[2]) / z_range

    return img_x, img_y

def draw_connecting_lines(ctx):
    colors = itertools.cycle(route_colors)
    ctx.set_line_width(0.01)
    
    drawn_paths = set()

    for loc in locations:
        dests = get_dests(loc['name'])
        for dest in dests: 
            path = tuple(sorted([loc['name'], dest[0]]))
            if path in drawn_paths:
                continue

            hops = longest_path(loc['name'], dest[0])

            ctx.new_path()

            fr = map2img(*hops[0])
            ctx.move_to(*fr)

            for hop in hops[1:]:
                to = map2img(*hop)
                ctx.line_to(*to)

            color = colors.next()
            ctx.set_source_rgb(*color)
            ctx.stroke()

            drawn_paths.add(path)
    
def plot_locations(ctx):
    ctx.set_line_width(0.001)
    
    for loc in locations:
        name = loc['name']
        plot = map2img(*loc['location'])

        logging.info('{} at {}'.format(name, plot))

        # draw a circle for the location

        # clear the area around (cut off the route lines) for prettying
        ctx.new_path()
        ctx.set_source_rgb(1, 1, 1)
        ctx.arc(plot[0], plot[1], 0.012, 0, 2 * math.pi)
        ctx.fill()

        # draw a filled circle for the location
        ctx.new_path()
        ctx.set_source_rgb(0, 0, 0)
        ctx.arc(plot[0], plot[1], 0.005, 0, 2 * math.pi)
        ctx.fill()

        # and put a circle around it
        ctx.new_path()
        ctx.set_source_rgb(0, 0, 0)
        ctx.arc(plot[0], plot[1], 0.0085, 0, 2 * math.pi)
        ctx.stroke()
        
        # label the location

        ctx.set_font_face(face)
        ctx.set_font_size(0.018)
        x_off, y_off, text_w, text_h = ctx.text_extents(name)[:4]
        text_x = plot[0] - x_off - text_w / 2

        bottom_edge = plot[1] - (locplot_pad * 3.5) # technically just half the plot size, to move above the square; but then we add the same amount again as padding, so it's locplot_size / 2 * 2
        text_y = bottom_edge - y_off - text_h

        pad = locplot_pad
        
        textrect = (text_x + x_off - pad, text_y + y_off - pad,
                    text_w + pad * 2, text_h + pad * 2)

        ctx.new_path()
        ctx.rectangle(*textrect)
        ctx.set_source_rgba(1, 1, 1, 0.75)
        ctx.fill()
        
        ctx.new_path()
        ctx.rectangle(*textrect)
        ctx.set_source_rgb(0, 0, 0)
        ctx.stroke()

        ctx.move_to(text_x, text_y)
        ctx.set_source_rgb(0.5, 0, 0)
        ctx.show_text(name)

        
def build(fn):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *output_size)
    ctx = cairo.Context(surface)
    ctx.scale(*output_size)
    pad = (1 - draw_area) / 2
    ctx.translate(pad, pad)
    ctx.scale(draw_area, draw_area)
    
    draw_connecting_lines(ctx)
    plot_locations(ctx)
    
    surface.write_to_png(fn)


if __name__ == '__main__':
    build('out.png')
