#!/usr/bin/python

import os, sys, re, math
from pavara.utils import drill
from pavara.utils.drill import XmlWriter

Path, Rect, Text = range(3)
class SVGObject():
    def __init__(self, type):
        self.x = None
        self.y = None
        self.fill = None
        self.stroke = None
        self.width = None
        self.height = None
        self.paths = None
        self.text = None
        self.type = type
        
    def __repr__(self):
        repr = "svg-o:<"+str(self.type)+">"
        repr += " x:" + self.x if self.x else ""
        repr += " y:" + self.y if self.y else ""
        repr += " fill:" + self.fill if self.fill else ""
        repr += " stroke:" + self.stroke if self.stroke else ""
        repr += " width:" + self.width if self.width else "" 
        repr += " height:" + self.width if self.width else ""
        repr += " paths:" + (self.paths.__repr__()) if self.paths else ""
        repr += " text: " + self.text if self.text else ""
        return repr
    
    def set_pos(self, pos_x, pos_y):
        self.x = pos_x
        self.y = pos_y
    
    def set_fill_stroke(self, fill, stroke):
        self.fill = fill
        self.stroke = stroke
    
    def set_box_dim(self, width, height):
        self.width = width
        self.height = height
    
    def set_paths(self, paths):
        self.paths = paths
    
    def set_text(self, text):
        self.text = text
    
class ConvertSVGLevel():
    def __init__(self, levelpath, outputpath, mapname):
        #self.oldfile = open(levelpath, 'r')
        levelpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), levelpath)
        outputpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), outputpath)
        
        self.svg_doc = drill.parse(levelpath)
        self.newfile = open(outputpath, 'w')
        self.newfile.write('<?xml version="1.0" standalone="yes" ?>\n')
        self.xml_writer = XmlWriter(self.newfile)
        
        #print self.svg_doc
        
        doc_width = float(self.svg_doc.attrs['width'].strip('px'))
        doc_height = float(self.svg_doc.attrs['height'].strip('px'))
        
        self.center_x = self.pix_to_units(doc_width / 2.0)
        self.center_y = self.pix_to_units(doc_height / 2.0)
        
        self.svg_stack = []
        self.curr_wa = 0
        self.curr_wall_height = 0
        
        #print self.svg_doc.attrs
        
        for child in self.svg_doc.find('//g'):
            for gchild in child.children():
                #print gchild.attrs
                #print gchild
                if gchild.tagname == "path":
                    p = SVGObject(Path)
                    p.set_paths(self.parse_pathdata(gchild.attrs['d']))
                    p.set_fill_stroke(*self.parse_style(gchild.attrs['style']))
                    self.svg_stack.append(p)
                elif gchild.tagname == "rect":
                    r = SVGObject(Rect)
                    x = gchild.attrs['x'] if 'x' in gchild.attrs else 0
                    y = gchild.attrs['y'] if 'y' in gchild.attrs else 0
                    r.set_pos(x, y)
                    r.set_box_dim(gchild.attrs['width'], gchild.attrs['height'])
                    self.svg_stack.append(r)
            
            continue
            found_paths = []
            found_rects = []
            found_script = []
            
            x = y = fill = stroke = width = height = ""
            rot = 0
            loc = ()
            
            for idx,sub in enumerate(child):
                #print idx,loc
                #print sub.tag
                #print sub.attrib
                if 'clipPath' in sub.tag:
                    continue
                if 'path' in sub.tag:
                    this_fill = this_stroke = ""
                    style = sub.get('style')
                    #self.block_follows = False
                    if style != None:
                        styles = style.split(";")
                        for style in styles:
                            s_split = style.split(':')
                            if s_split[0] == "fill" and s_split[1] != "none":
                                this_fill = s_split[1]
                            if s_split[0] == "stroke":
                                this_stroke = s_split[1]
                    else:
                        this_fill = sub.get('fill')
                        this_stroke = sub.get('stroke')
                    pathdata = sub.get('d')
                    if not this_fill or this_fill == "" or this_fill == "none":
                        print "getting rot from %s" %pathdata
                        rot = self.get_rot_loc_from_path(pathdata, True)
                        stroke = this_stroke
                    else:
                        print "getting loc from %s" %pathdata
                        loc = self.get_rot_loc_from_path(pathdata, False)
                        fill = this_fill
                    found_paths.append((pathdata))
                if 'rect' in sub.tag[-4:]:
                    x = sub.get('x')
                    if not x:
                        x = 0
                    y = sub.get('y')
                    if not y:
                        y = 0
                    width = sub.get('width')
                    height = sub.get('height')
                    style = sub.get('style')
                    
                    if style != None:
                        styles = style.split(";")
                        for style in styles:
                            s_split = style.split(':')
                            if s_split[0] == "fill":
                                fill = s_split[1]
                            if s_split[0] == "stroke":
                                stroke = s_split[1]
                    else:
                        fill = sub.get('fill')
                        stroke = sub.get('stroke')
                    found_rects.append((x,y,width,height,fill,stroke))
                
                if "g" == sub.tag[-1]:
                    for t in sub:
                        if "text" == t.tag[-4:]:
                            out_text = ""
                            if(t.text):
                                out_text += (t.text.replace("\n",";").replace("\r",";"))
                                out_text += ";"
                            else:
                                for tspan in t:
                                    out_text += tspan.text
                                out_text += ";"
                            print "out_text: %s"%out_text
                            found_script.append(out_text)
                        
            #end for each subelement
            if len(found_paths) > 0 and len(loc) > 1:
                #arc
                #print loc
                self.el_stack.append(self.Arc(float(loc[0]),float(loc[1]), rot, fill, stroke))
                del(found_paths[:])
            if len(found_rects) > 0:
                #print found_rects
                for found_rect in found_rects:
                    #print "found_rect: %s,%s,%s,%s" % found_rect
                    if(len(found_rect) > 3):
                        print found_rect
                        self.el_stack.append(self.Rect(float(found_rect[0]),float(found_rect[1]), float(found_rect[2]), float(found_rect[3]), found_rect[4], found_rect[5]))
                del(found_rects[:])
            if len(found_script) > 0 or self.block_follows:
                script = "".join([x for x in found_script if x])
                #print "starting script on %s withscript %s" % (self.el_stack, script)
                lines = script.split(";")
                print lines
                print child
                for ch in child:
                    print ch
                    print ch.attrib
                    for c in ch:
                        print c
                        print c.text
                self.parse_script(lines)
                del(found_script[:])
        #end for each child
        print self.svg_stack
    
    def parse_style(self, stylestring):
        this_fill = None
        this_stroke = None
        styles = stylestring.split(";")
        for style in styles:
            s_split = style.split(':')
            if s_split[0] == "fill" and s_split[1] != "none":
                this_fill = s_split[1]
            if s_split[0] == "stroke":
                this_stroke = s_split[1]
        return (this_fill, this_stroke)
    
    def parse_pathdata(self, pathdata):
        instructions = pathdata.split(',')
        path_data_out = []
        for inst in instructions:
            command = inst[0]
            arguments = inst[1:]
            path_data_out.append((command,arguments))
        return path_data_out
                    
    def get_rot_loc_from_path(self, pathdata, is_stroke):
        #print pathdata
        pdata = re.split('([a-zA-Z]{1})',pathdata)
        
        start_x = start_y = curr_x = curr_y = 0
        
        has_h = has_c = has_l = has_v = has_H = has_V = False
        h_length = v_length = H_to = V_to = c_angle = l_x = l_y = 0
        c_points = []
        
        loc_x = loc_y = 0
        
        for idx,inst in enumerate(pdata):
            """http://www.w3.org/TR/SVG/paths.html#PathData"""
            if len(inst) < 1:
                continue
            if inst == "M":
                coords = pdata[idx+1]
                s_coords = coords.split(',')
                start_x = float(s_coords[0])
                start_y = float(s_coords[1])
                curr_x = start_x
                curr_y = start_y
                continue
            if inst == "v":
                has_v = True
                v_length = float(pdata[idx+1])
                curr_y += v_length
                continue
            if inst == "h":
                has_h = True
                h_length = float(pdata[idx+1])
                curr_x += h_length
                continue
            if inst == "V":
                has_V = True
                V_to = float(pdata[idx+1])
                curr_y = V_to
            if inst == "H":
                has_H = True
                H_to = float(pdata[idx+1])
                curr_x = H_to
            if inst == "l":
                has_l = True
                coords = pdata[idx+1]
                s_coords = self.chunks(self.points_list_from_c(coords), 2)
                l_y = float(s_coords[0][0])
                l_x = float(s_coords[0][1])
                curr_x += l_x
                curr_y += l_y
                continue
            if inst == "c":
                has_c = True
                coords = pdata[idx+1]
                c_points = self.points_list_from_c(coords)
                for idx,value in enumerate(c_points):
                    if(idx % 2 > 0):
                        c_points[idx] += curr_y
                    else:    
                        c_points[idx] += curr_x
                c_points.reverse()
                c_points.append(curr_y)
                c_points.append(curr_x)
                c_points.reverse()
                c_points = self.chunks(c_points, 2)
                c_angle = self.get_angle_from_arc_curve(c_points)
                continue
        #end for inst in pdata
            
        """the fill shape of arcs seems to follow this pattern:
            1. a absolute move "M" to coordinates
            2. a line, "V", "H", "v", "h", or "l"
            3. curve instruction "c" that completes the arc 
               and returns to the start point.
            These instructions are to find the middle of the line (or
            in the case of a relative line, the endpoint of the line)
            for positioning of objects using the arc as positional info.
        """

        if has_v:
            loc_y = start_y + (v_length / 2)
            loc_x = start_x
        elif has_h:
            loc_x = start_x + (h_length / 2)
            loc_y = start_y
        elif has_V:
            if start_y > V_to:    
                loc_y = start_y - ((start_y - V_to) / 2)
            elif start_y < V_to:
                loc_y = start_y + ((V_to - start_y) / 2)
            loc_x = start_x
        elif has_H:
            if start_x > H_to:
                loc_x = start_x - ((start_x - H_to) / 2)
            elif start_x < H_to:
                loc_x = start_x + ((H_to - start_x) / 2)
            loc_y = start_y
        elif has_l:
            loc_x = start_x + l_x
            loc_y = start_y + l_y
        else:
            loc_y = start_y
            loc_x = start_x
        
        
        #print "rotation: %s, position: %s" %(c_angle, (loc_x, loc_y))
        if(is_stroke): 
            return c_angle
        else:    
            print (loc_x, loc_y)
            return (loc_x,loc_y)
    
    
    def points_list_from_c(self, cstring):
        nums = cstring.replace(',',' ').replace('-',' -').split(' ')
        return [float(n) for n in nums if n]
         
    
    def get_angle_from_arc_curve(self, point_list):
        #print "point_list: %s" %point_list
        """this gets the angle of the normal of the quadratic curve with the coordinates 
            supplied in point_list. point_list starts with the current point of the cursor
            and the curve points follow (added with the current cursor point coordinates 
            as the curves are all relative). the angle provided is degrees distance from the x-axis
        """
        dividend = (-1*(point_list[0][1]) + point_list[1][1] - point_list[2][1] + point_list[3][1])
        divisor = (-1*(point_list[0][0]) + point_list[1][0] - point_list[2][0] + point_list[3][0])
        return math.degrees(math.atan2(dividend, divisor)) 
    
    def chunks(self, l, n):
        return [l[i:i+n] for i in range(0, len(l), n)]
        
    def parse_script(self, scriptlines):
        print scriptlines
        scriptlines = [x for x in scriptlines if x]
        in_object = False
        object_type = None
        
        in_information = False
        info_text = ""
        
        has_ramp = False
        has_incarn = False
        has_wall = False
        nonramp = False
        
        set_sky_color = False
        set_ground_color = False
        
        has_wa = False
        
        y = 0
        delta_y = 0
        ramp_thickness = 0
        skip_next = False
        
        for idx,line in enumerate(scriptlines):
            if skip_next:
                skip_next = False
                continue
            words = [x for x in re.split("\s?=?\s?", line) if x]
            if len(words) < 2 and words[0] != "end":
                words += scriptlines[idx+1]
                skip_next = True
            print "testing on %s, in_object = %s" % (words[0],in_object)
            if(words[0] == "adjust"):
                if(words[1] == "SkyColor"):
                    set_sky_color = True
                if(words[1] == "GroundColor"):
                    set_ground_color = True
            if(words[0] == "wa"):
                self.block_follows = True
                self.curr_wa = float(words[1])
                has_wa = True
            elif(words[0] == "wallHeight"):
                self.block_follows = True
                self.curr_wall_height = float(words[1])
            elif(words[0] == "designer"):
                self.newtree.set("author", " ".join(words[1:]))
            elif(words[0] == "information"):
                in_information = True
                info_text += " ".join(words[1:])
                info_text += " "
            elif(words[0][0:4] == "light"):
                in_information = False
                print words
            elif(in_information):
                info_text += " ".join(words)
                info_text += " "
            elif(words[0] == "object"):
                in_object = True
                object_type = words[1]
            elif (in_object):
                if(words[0] == "y"):
                    y = float(words[1])
                if(object_type == "Ramp"):
                    has_ramp = True
                    if(words[0] == "deltaY"):
                        delta_y = float(words[1])
                    if(words[0] == "thickness"):
                        ramp_thickness = words[1];
                else:
                    nonramp = True
                if(object_type == "Incarnator"):
                    has_incarn = True
                    
            elif(words[0] == "end"):
                in_object = False
                object_type = ""
        #end for line in scriptlines
        
        if set_sky_color:
            self.make_sky_element()
            
        if set_ground_color:
            self.make_ground_element()
        
        if info_text:
            self.newtree.set("description", info_text)
            
        if (self.block_follows or nonramp) and (has_ramp == False):
            self.make_block_from_rect()
        
        if has_ramp:
            self.make_ramp(y, delta_y, ramp_thickness)
            
        if has_incarn:
            self.make_incarn(y) 
            
        if not has_wa:
            self.curr_wa = 0
            
    def pix_to_units(self, pixels):
        return float(pixels) / 18.0
        
        
    def recenter_coordinates(self, coord_tuple):
        x = float(coord_tuple[0])# - self.center_x
        y = float(coord_tuple[1])# - self.center_y 
        return (self.pix_to_units(x) - self.center_x,self.pix_to_units(y) - self.center_y)
    
    def hex_color_to_rgb(self, color):
        color = color.lstrip("#")
        if len(color) != 6:
            raise ValueError, "input #%s is not in #RRGGBB format" % color
        r, g, b = color[:2], color[2:4], color[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)] 
        return "%s,%s,%s"%((r/255.0, g/255.0, b/255.0)) # colors are rgb between 1 and 0
    
    
    def make_ramp(self, y, delta_y, thickness):
        ramp_base = 0
        ramp_top = 0
        base_x_z_coords = (0,0)
        top_x_z_coords = (0,0)
        arc = False
        rect = False
        fill = "#FFFFFF"
        print self.el_stack
        for el in self.el_stack:
            if isinstance(el, self.Arc):
                if el.fill != "none":
                    fill = el.fill
                arc = el
            if isinstance(el, self.Rect):
                if el.fill == "none":
                    rect = el
                else:
                    fill = el.fill
        if arc == False:
            print "warning no arc found for ramp..."
            del(self.el_stack[:])
            return
        if rect == False:
            print "warning no rect found for ramp..."
            del(self.el_stack[:])
            return
        
        if fill != "#FFFFFF" or arc.fill == "none":
            arc.fill = fill
            
        print arc, fill
        
        print "pointing ramp downhill to %s" % arc.angle
        #angle points to bottom of ramp
        if(arc.angle == 180 or (-10 < (135 - arc.angle) < 10 )):
            #points to top
            top_x_z_coords = self.recenter_coordinates(((rect.x+(rect.width/2)), rect.y+rect.height))
            base_x_z_coords = self.recenter_coordinates(((rect.x+(rect.width/2)), rect.y))
            ramp_width = str(self.pix_to_units(rect.width))
        elif(arc.angle == 360 or arc.angle == 0 or (-10 < (-45 - arc.angle) < 10) or (-10 < (-135 - arc.angle) < 10)): #fuck you
            #points to bottom
            top_x_z_coords = self.recenter_coordinates(((rect.x+(rect.width/2)), rect.y))
            base_x_z_coords = self.recenter_coordinates(((rect.x+(rect.width/2)), rect.y+rect.height))
            ramp_width = str(self.pix_to_units(rect.width))
        elif(arc.angle == 90):
            #points to left
            top_x_z_coords = self.recenter_coordinates((rect.x+rect.width, (rect.y+(rect.height/2))))
            base_x_z_coords = self.recenter_coordinates((rect.x, (rect.y+(rect.height/2))))
            ramp_width = str(self.pix_to_units(rect.height))
        elif(arc.angle == 270 or arc.angle == -90):
            #points to right
            top_x_z_coords = self.recenter_coordinates((rect.x, (rect.y+(rect.height/2))))
            base_x_z_coords = self.recenter_coordinates((rect.x+rect.width, (rect.y+(rect.height/2))))
            ramp_width = str(self.pix_to_units(rect.height))
        else:
            "warning arc pointing at weird angle?? angle = %s" % arc.angle
            #return
            
        ramp_base = "%s,%s,%s" % (base_x_z_coords[0], float(y), base_x_z_coords[1])
        ramp_top = "%s,%s,%s" % (top_x_z_coords[0], (float(y)+float(delta_y)), top_x_z_coords[1])
        
        new_ramp = et.SubElement(self.newtree, "ramp")
        new_ramp.set("base", ramp_base)
        new_ramp.set("top", ramp_top)
        new_ramp.set("width", ramp_width)
        new_ramp.set("color", self.hex_color_to_rgb(arc.fill))
        if thickness > 0:
            new_ramp.set("thickness", thickness)
        print "added ramp - base: %s, top:%s, width: %s, color: %s, y: %s, deltaY: %s" % (ramp_base, ramp_top, ramp_width, new_ramp.get('color'), y, delta_y)
        del(self.el_stack[:])
        
    def make_block_from_rect(self):
        fill_x = 0
        fill_y = 0
        for idx,el in enumerate(self.el_stack):
            print el
            if (not isinstance(el, self.Rect)):
                continue
            if el.fill != "none":
                self.curr_fill = el.fill
                fill_x = el.x
                fill_y = el.y
                #del(self.el_stack[idx])
                continue
            if fill_y == 0 or fill_x == 0 or (el.x - fill_x > 1 and el.y - fill_y > 1):
                continue
            print el
            #<block center="x,y,z" size="width,height,depth" color="1,1,1" />
            x_z_coords = self.recenter_coordinates(((el.x+(el.width/2.0)), (el.y+(el.height/2.0))))
            
            #round down to zero
            if self.curr_wall_height < .1:
                self.curr_wall_height = 0
                
            center_y = (self.curr_wa + (self.curr_wall_height/2.0))
            
            
            #sanity bumpz for 0 thickness blox
            if self.curr_wall_height == 0:
                center_y += .001
            #if(self.curr_wall_height == 0):
            #    center_y += .001
            
            new_block = et.SubElement(self.newtree, "block")
            
            new_block.set("size", "%s,%s,%s" % (self.pix_to_units(el.width), self.curr_wall_height, self.pix_to_units(el.height)))
            
            new_block.set("center", "%s,%s,%s" % ( x_z_coords[0], center_y, x_z_coords[1]))
            
            new_block.set("color", self.hex_color_to_rgb(self.curr_fill))
            print "added block - size: %s, center: %s, color: %s" % (new_block.get('size'), new_block.get('center'), new_block.get('color'))
            del(self.el_stack[idx])
            self.curr_fill = "#FFFFFF"
    
    def make_incarn(self, y):
        for idx, el in enumerate(self.el_stack):
            if isinstance(el, self.Arc):
                new_incarn = et.SubElement(self.newtree, "incarnator")
                location = (self.pix_to_units(el.x), y, self.pix_to_units(el.y))
                new_incarn.set("location", "%s,%s,%s" % location)
                incarn_angle = 0
                if el.angle > 0:
                    incarn_angle = el.angle
                else:
                    incarn_angle = el.angle + 360.0
                new_incarn.set("angle", "%s" % (str(incarn_angle)))
                print "added incarn - pos: %s, angle: %s" % (location, incarn_angle)
                del(self.el_stack[idx])
                
    def make_sky_element(self):
        horizon = 0
        color = 0
        print "Making sky element"
        print self.el_stack
        for el in self.el_stack:
            if isinstance(el, self.Arc):
                if el.fill != "none":
                    horizon = self.hex_color_to_rgb(el.fill)
                if el.stroke:
                    color = self.hex_color_to_rgb(el.stroke)
        new_sky = et.SubElement(self.newtree, "sky")
        new_sky.set("horizon", horizon)
        new_sky.set("color", color)
        del(self.el_stack[:])
    
    def make_ground_element(self):
        color = 0
        for el in self.el_stack:
            if isinstance(el, self.Arc):
                if el.fill != "none":
                    color = self.hex_color_to_rgb(el.fill)
        new_ground = et.SubElement(self.newtree, "ground")
        new_ground.set("color", color)
        del(self.el_stack[:])
        
if __name__ == "__main__":
    try:
        c = ConvertSVGLevel(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e:
        print "Failed: %s" % e
        raise
