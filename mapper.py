#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import itertools
import logging
from pprint import pprint, pformat
from PIL import Image, ImageDraw, ImageFont

from locations import locations

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-7s %(message)s")

output_size = (800, 800)
plot_size = (700, 700)

locplot_size = (4, 4)

route_colors = ((192, 64, 64),
                (64, 192, 64),
                (64, 64, 192),
                (192, 192, 64),
                (192, 64, 192),
                (64, 192, 192),)

try:
    font = ImageFont.truetype("/cygdrive/c/Windows/Fonts/tahomabd.ttf", 11)
except:
    font = ImageFont.load_default()

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
        
logging.info("Bounds: {}".format(pformat(bounds())))

def plot_region():
    xpad = (output_size[0] - plot_size[0]) / 2
    ypad = (output_size[1] - plot_size[1]) / 2
    

    return ((xpad, ypad),
            (xpad + plot_size[0], ypad + plot_size[1]))

def map2img(x, y, z):
    tl, br = bounds()
    plot_tl, plot_br = plot_region()
    
    x_range = (br[0] - tl[0])
    img_x = (x - tl[0]) / x_range * plot_size[0] + plot_tl[0]

    z_range = (br[2] - tl[2])
    img_y = (z - tl[2]) / z_range * plot_size[1] + plot_tl[1]

    return (int(round(img_x)),
            int(round(img_y)))

def draw_connecting_lines(img):
    draw = ImageDraw.Draw(img)

    colors = itertools.cycle(route_colors)
    
    try:
        drawn_paths = set()

        for loc in locations:
            dests = get_dests(loc['name'])
            for dest in dests: 
                path = tuple(sorted([loc['name'], dest[0]]))
                if path in drawn_paths:
                    continue

                hops = longest_path(loc['name'], dest[0])
                color = colors.next()
                
                for i in range(len(hops) - 1):
                    fr = map2img(*hops[i])
                    to = map2img(*hops[i + 1])
                    draw.line((tuple(fr), tuple(to)), color)

                drawn_paths.add(path)
    finally:
        del draw
            
def draw_translucent_poly(img, coord_list, fill_rgb, fill_alpha):
    # adapted from http://stackoverflow.com/a/433638/339378
    base_layer = img.copy()
    color_layer = Image.new('RGBA', base_layer.size, fill_rgb)
    alpha_mask = Image.new('L', base_layer.size, 0)
    alpha_mask_draw = ImageDraw.Draw(alpha_mask)
    alpha_mask_draw.polygon(coord_list, fill=fill_alpha)
    base_layer = Image.composite(color_layer, base_layer, alpha_mask)

    img.paste(base_layer, None)

def draw_translucent_rect(img, bounds, fill_rgb, fill_alpha):
    return draw_translucent_poly(img,
                                 ((bounds[0], bounds[1]),
                                  (bounds[2], bounds[1]),
                                  (bounds[2], bounds[3]),
                                  (bounds[0], bounds[3])),
                                 fill_rgb,
                                 fill_alpha)
    
def plot_locations(img):
    draw = ImageDraw.Draw(img)

    try:
        for loc in locations:
            name = loc['name']
            plot = map2img(*loc['location'])

            logging.info('{} at {}'.format(name, plot))

            # draw a square for the location

            rectbounds = []
            for i in range(2):
                rectbounds.append(int(round(plot[i] - locplot_size[i] / 2)))
            for i in range(2):
                rectbounds.append(int(round(plot[i] + locplot_size[i] / 2)))

            draw.rectangle(rectbounds, (0, 0, 0))

            # label the location

            textsize = draw.textsize(name, font=font)

            text_x = int(round(plot[0] - textsize[0] / 2))

            bottom_edge = plot[1] - (locplot_size[1] + 3) # technically just half the plot size, to move above the square; but then we add the same amount again as padding, so it's locplot_size / 2 * 2
            text_y = int(round(bottom_edge - textsize[1]))

            textrect = (text_x - 3, text_y - 3,
                        text_x + textsize[0] + 2, text_y + textsize[1] + 2)
            
            draw_translucent_rect(img,
                                  textrect,
                                  (255, 255, 255),
                                  128)
            
            draw.rectangle(textrect, outline=(0, 0, 0), fill=None)
            
            draw.text((text_x, text_y),
                      name,
                      font=font,
                      fill=(0, 0, 0))


    finally:
        del draw

        

        
def build(fn):
    img = Image.new('RGB', output_size, (255, 255, 255))
    draw_connecting_lines(img)
    plot_locations(img)
    img.save(fn, 'PNG')


if __name__ == '__main__':
    build('out.png')
