# ==================================================================================================
#
#    Copyright (c) 2016, Chen Kian Wee (chenkianwee@gmail.com)
#
#    This file is part of pyliburo
#
#    pyliburo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyliburo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Dexen.  If not, see <http://www.gnu.org/licenses/>.
#
# ==================================================================================================
import math
import py3dmodel
import pycitygml

#==============================================================================================================================
#shp2citygml functions
#==============================================================================================================================
def make_transit_stop_box(length, width, height):
    box = py3dmodel.construct.make_box(length, width, height)
    return box
    
def create_transit_stop_geometry(occ_transit_box_shape, location_pt):
    trsf_shp = py3dmodel.modify.move((0,0,0), location_pt, occ_transit_box_shape)
    return trsf_shp

def extrude_building(building_footprint, height):
    face_list = []
    #polygons from shpfiles are always clockwise
    #holes are always counter-clockwise
    extrude = py3dmodel.construct.extrude(building_footprint,(0,0,1), height )
    extrude = py3dmodel.fetch.shape2shapetype(extrude)
    face_list = py3dmodel.fetch.faces_frm_solid(extrude)
    return face_list
    
def landuse_surface_cclockwise(pypt_list):
    luse_f = py3dmodel.construct.make_polygon(pypt_list)
    n = py3dmodel.calculate.face_normal(luse_f)
    if not py3dmodel.calculate.is_anticlockwise(pypt_list, n):
        luse_f.Reverse()
        
    luse_pts = py3dmodel.fetch.pyptlist_frm_occface(luse_f)
    return luse_pts
    
#==============================================================================================================================
#citygml2eval functions
#==============================================================================================================================
def generate_sensor_surfaces(occface, xdim, ydim):
    normal = py3dmodel.calculate.face_normal(occface)
    mid_pt = py3dmodel.calculate.face_midpt(occface)
    location_pt = py3dmodel.modify.move_pt(mid_pt, normal, 0.01)
    moved_oface = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(mid_pt, location_pt, occface))
    #put it into occ and subdivide surfaces 
    sensor_surfaces = py3dmodel.construct.grid_face(moved_oface, xdim, ydim)
    sensor_pts = []
    sensor_dirs = []
    for sface in sensor_surfaces:
        smidpt = py3dmodel.calculate.face_midpt(sface)
        sensor_pts.append(smidpt)
        sensor_dirs.append(normal)
    
    return sensor_surfaces, sensor_pts, sensor_dirs
        
def identify_srfs_according_2_angle(occface_list):
    roof_list = []
    facade_list = []
    footprint_list = []
    vec1 = (0,0,1)
    for f in occface_list:
        #get the normal of each face
        n = py3dmodel.calculate.face_normal(f)
        angle = py3dmodel.calculate.angle_bw_2_vecs(vec1, n)
        #means its a facade
        if angle>45 and angle<135:
            facade_list.append(f)
        elif angle<=45:
            
            roof_list.append(f)
        elif angle>=135:
            footprint_list.append(f)
    return facade_list, roof_list, footprint_list
            
def identify_building_surfaces(bldg_occsolid):
    face_list = py3dmodel.fetch.faces_frm_solid(bldg_occsolid)
    facade_list, roof_list, footprint_list = identify_srfs_according_2_angle(face_list)     
    return facade_list, roof_list, footprint_list
    
def faces_surface_area(occface_list):
    total_sa = 0
    for occface in occface_list:
        sa = py3dmodel.calculate.face_area(occface)
        total_sa = total_sa + sa
    return total_sa
    
#==============================================================================================================================
#gmlparameterise functions
#==============================================================================================================================
def get_building_footprint(gml_bldg, citygml_reader):
    bldg_occsolid = get_building_occsolid(gml_bldg, citygml_reader)
    bldg_footprint_list = get_bldg_footprint_frm_bldg_occsolid(bldg_occsolid)
    return bldg_footprint_list
            
def get_bldg_footprint_frm_bldg_occsolid(bldg_occsolid):
    face_list = py3dmodel.fetch.faces_frm_solid(bldg_occsolid)
    bldg_footprint_list = []
    bounding_footprint = get_building_bounding_footprint(bldg_occsolid)
    for face in face_list:
        normal = py3dmodel.calculate.face_normal(face)
        if normal == (0,0,-1):
            if py3dmodel.calculate.face_is_inside(face,bounding_footprint):
                bldg_footprint_list.append(face)
    return bldg_footprint_list
            
def gml_landuse_2_occface(gml_landuse, citygml_reader):
    lpolygon = citygml_reader.get_polygons(gml_landuse)[0]
    landuse_pts = citygml_reader.polygon_2_pt_list(lpolygon)
    landuse_occface = py3dmodel.construct.make_polygon(landuse_pts)
    return landuse_occface
            
def buildings_on_landuse(gml_landuse, gml_bldg_list, citygml_reader):
    display_list = []
    buildings_on_plot_list = []
    landuse_occface = gml_landuse_2_occface(gml_landuse, citygml_reader)
    flatten_landuse_occface = py3dmodel.modify.flatten_face_z_value(landuse_occface)
    display_list.append(landuse_occface)
    for gml_bldg in gml_bldg_list:
        bldg_fp_list = get_building_footprint(gml_bldg, citygml_reader)
        is_inside = False
        for bldg_fp in bldg_fp_list:
            flatten_fp = py3dmodel.modify.flatten_face_z_value(bldg_fp)
            #display_list.append(flatten_fp)
            occface_area = py3dmodel.calculate.face_area(flatten_fp)
            common_cmpd = py3dmodel.construct.boolean_common(flatten_fp, flatten_landuse_occface)
            face_list = py3dmodel.fetch.geom_explorer(common_cmpd, "face")
            if face_list:
                common_area = 0
                for common_face in face_list:
                    acommon_area = py3dmodel.calculate.face_area(common_face)
                    common_area = common_area +  acommon_area
                common_ratio = common_area/occface_area
                if common_ratio >= 0.5:
                    is_inside = True
                
        if is_inside:
            buildings_on_plot_list.append(gml_bldg)
            
    return buildings_on_plot_list
    
def detect_clash(bldg_occsolid, other_occsolids):
    compound = py3dmodel.construct.make_compound(other_occsolids)
    common_compound = py3dmodel.construct.boolean_common(bldg_occsolid, compound)
    is_cmpd_null = py3dmodel.fetch.is_compound_null(common_compound)
    if is_cmpd_null:
        return False
    else:
        return True
    
def detect_in_boundary(bldg_occsolid, luse_occface):
    luse_occsolid = py3dmodel.construct.extrude(luse_occface,(0,0,1), 10000)
    diff_cmpd = py3dmodel.construct.boolean_difference(bldg_occsolid, luse_occsolid)
    is_cmpd_null = py3dmodel.fetch.is_compound_null(diff_cmpd)
    return is_cmpd_null
            
def get_building_occsolid(gml_bldg, citygml_reader):
    pypolygon_list = citygml_reader.get_pypolygon_list(gml_bldg)
    solid = py3dmodel.construct.make_occsolid_frm_pypolygons(pypolygon_list)
    return solid
    
def get_building_height_storey(gml_bldg, citygml_reader):
    height = citygml_reader.get_building_height(gml_bldg)
    nstorey = citygml_reader.get_building_storey(gml_bldg)
    storey_height = height/nstorey
    return height, nstorey, storey_height
    
def calculate_bldg_height(bldg_occsolid):
    facade_list, roof_list, footprint_list = identify_building_surfaces(bldg_occsolid)
    roof_compound = py3dmodel.construct.make_compound(roof_list)
    xmin,ymin,zmin,xmax,ymax,zmax = py3dmodel.calculate.get_bounding_box(roof_compound)
    centre_roof_pypt = py3dmodel.calculate.get_centre_bbox(roof_compound)
    top_pypt = (centre_roof_pypt[0],centre_roof_pypt[1],zmax)
    
    fp_compound =  py3dmodel.construct.make_compound(footprint_list)
    xmin,ymin,zmin,xmax,ymax,zmax = py3dmodel.calculate.get_bounding_box(fp_compound)
    centre_fp_pypt = py3dmodel.calculate.get_centre_bbox(fp_compound)
    bottom_pypt = (centre_fp_pypt[0],centre_fp_pypt[1],zmax)
    
    height = round(py3dmodel.calculate.distance_between_2_pts(bottom_pypt,top_pypt),2)
    return height
    
def calculate_bldg_height_n_nstorey(bldg_occsolid, storey_height):
    height = calculate_bldg_height(bldg_occsolid)
    nstorey = int(math.floor(float(height)/float(storey_height)))
    return height,nstorey
    
def get_building_bounding_footprint(bldg_occsolid):
    xmin, ymin, zmin, xmax, ymax, zmax = py3dmodel.calculate.get_bounding_box(bldg_occsolid)
    bounding_footprint = py3dmodel.construct.make_polygon([(xmin,ymin,zmin),(xmin,ymax,zmin),(xmax, ymax, zmin),(xmax, ymin, zmin)])
    return bounding_footprint
    
def get_building_location_pt(bldg_occsolid):
    bounding_footprint = get_building_bounding_footprint(bldg_occsolid)
    loc_pt = py3dmodel.calculate.face_midpt(bounding_footprint)
    return loc_pt
    
def get_bulding_flrplates(bldg_occsolid, nstorey, storey_height):
    intersection_list = []
    bounding_list = []
    loc_pt = get_building_location_pt(bldg_occsolid)
    bounding_footprint = get_building_bounding_footprint(bldg_occsolid)
    bldg_footprint_list = get_bldg_footprint_frm_bldg_occsolid(bldg_occsolid)
    intersection_list.extend(bldg_footprint_list)
    for scnt in range(nstorey):
        z = loc_pt[2]+(scnt*storey_height)
        moved_pt = (loc_pt[0], loc_pt[1], z)
        moved_f = py3dmodel.modify.move(loc_pt, moved_pt, bounding_footprint)
        bounding_list.append(moved_f)
           
    bounding_compound = py3dmodel.construct.make_compound(bounding_list)
    floors = py3dmodel.construct.boolean_common(bldg_occsolid, bounding_compound)
    common_compound = py3dmodel.fetch.shape2shapetype(floors)
    inter_face_list = py3dmodel.fetch.geom_explorer(common_compound, "face")
    if inter_face_list:
        for inter_face in inter_face_list:
            intersection_list.append(inter_face)
    return intersection_list#, bounding_list
    
def get_bulding_floor_area(gml_bldg, nstorey, storey_height, citygml_reader):
    bldg_occsolid = get_building_occsolid(gml_bldg,citygml_reader)
    flr_plates = get_bulding_flrplates(bldg_occsolid, nstorey, storey_height)
    flr_area = 0
    for flr in flr_plates:
        flr_area = flr_area + py3dmodel.calculate.face_area(flr)
        
    return flr_area , flr_plates

def construct_building_through_floorplates(bldg_occsolid, bldg_flr_area, storey_height):
    intersection_list = []
    bounding_list = []
    loc_pt  = get_building_location_pt(bldg_occsolid)
    bounding_footprint = get_building_bounding_footprint(bldg_occsolid)
    bldg_footprint_list = get_bldg_footprint_frm_bldg_occsolid(bldg_occsolid)
    intersection_list.extend(bldg_footprint_list)
    scnt = 0
    while bldg_flr_area > 0:
        if scnt == 0:
            for bldg_footprint in bldg_footprint_list:
                flr_area = py3dmodel.calculate.face_area(bldg_footprint)
                bldg_flr_area = bldg_flr_area - flr_area
        else:
            z = loc_pt[2]+((scnt)*storey_height)
            moved_pt = (loc_pt[0], loc_pt[1], z)
            moved_f = py3dmodel.modify.move(loc_pt, moved_pt, bounding_footprint)
            bounding_list.append(py3dmodel.fetch.shape2shapetype(moved_f))
            floors = py3dmodel.construct.boolean_common(bldg_occsolid, moved_f)
            #py3dmodel.construct.visualise([[moved_f,building_solid]], ["WHITE"])
            compound = py3dmodel.fetch.shape2shapetype(floors)
            inter_face_list = py3dmodel.fetch.geom_explorer(compound,"face")
            if inter_face_list:
                for inter_face in inter_face_list:
                    flr_area = py3dmodel.calculate.face_area(inter_face)
                    bldg_flr_area = bldg_flr_area - flr_area
                    intersection_list.append(inter_face)
            else:
                #it means the original solid is not so tall
                #need to move a storey up 
                loc_pt2 = (moved_pt[0], moved_pt[1], (moved_pt[2]-storey_height))
                previous_flr = intersection_list[-1]
                moved_f2 = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(loc_pt2, moved_pt, previous_flr))
                flr_area = py3dmodel.calculate.face_area(moved_f2)
                bldg_flr_area = bldg_flr_area - flr_area
                intersection_list.append(moved_f2)

        scnt += 1
            
    last_flr = intersection_list[-1]
    rs_midpt = py3dmodel.calculate.face_midpt(last_flr)
    moved_pt = (rs_midpt[0], rs_midpt[1], (rs_midpt[2]+storey_height))
    roof_srf = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(rs_midpt, moved_pt, last_flr))

    intersection_list.append(roof_srf)
    flr_srf = intersection_list[0]
    
    new_building_shell = py3dmodel.construct.make_loft(intersection_list, rule_face = False)
    
    face_list = py3dmodel.fetch.faces_frm_shell(new_building_shell) 
    face_list.append(roof_srf)
    face_list.append(flr_srf)
    closed_shell = py3dmodel.construct.make_shell_frm_faces(face_list)[0]
    shell_list = py3dmodel.fetch.topos_frm_compound(closed_shell)["shell"]
    new_bldg_occsolid = py3dmodel.construct.make_solid(shell_list[0])
    
    return new_bldg_occsolid#, intersection_list, bounding_list

def rotate_bldg(gml_bldg, rot_angle, citygml_reader):
    bldg_occsolid = get_building_occsolid(gml_bldg,citygml_reader)
    loc_pt = get_building_location_pt(bldg_occsolid)
    rot_bldg_occsolid = py3dmodel.modify.rotate(bldg_occsolid, loc_pt, (0,0,1), rot_angle)
    return rot_bldg_occsolid
    
def landuse_2_grid(landuse_occface, xdim, ydim):
    pt_list = []
    grid_faces = py3dmodel.construct.grid_face(landuse_occface, xdim, ydim)
    for f in grid_faces:
        pt = py3dmodel.calculate.face_midpt(f)
        pt_list.append(pt)
        
    return pt_list, grid_faces

def rearrange_building_position(bldg_occsolid_list, luse_gridded_pypt_list, luse_occface, parameters, other_occsolids = [], clash_detection = True, 
                                boundary_detection = True):
    
    moved_buildings = []
    moved_buildings.extend(other_occsolids)
    npypt_list = len(luse_gridded_pypt_list)
    nbldgs = len(bldg_occsolid_list)
    print 'NBUILDINGS', nbldgs
    for cnt in range(nbldgs):      
        bldg_occsolid = bldg_occsolid_list[cnt]
        pos_parm = parameters[cnt]
        loc_pt = get_building_location_pt(bldg_occsolid)
        
        isclash = True
        for clash_cnt in range(npypt_list):
            #print "clash_cnt", clash_cnt
            #map the location point to the grid points
            mpt_index = pos_parm+clash_cnt
            if mpt_index >= npypt_list:
                mpt_index = mpt_index-(npypt_list-1) 
                
            moved_pt = luse_gridded_pypt_list[mpt_index]
            moved_solid = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(loc_pt, moved_pt, bldg_occsolid))
            #=======================================================================================
            if clash_detection == True and boundary_detection == False:
                if moved_buildings:
                    clash_detected = detect_clash(moved_solid, moved_buildings)                    
                    if not clash_detected:
                        #means there is no intersection and there is no clash
                        #print "I am not clashing onto anyone!!!"
                        isclash = False
                        break
                
                else:
                    isclash = False
                    break
                
            #=======================================================================================
            elif boundary_detection == True and clash_detection == False:
                is_in_boundary = detect_in_boundary(moved_solid, luse_occface)
                if is_in_boundary:
                    isclash = False
                    break
            #=======================================================================================
            elif boundary_detection == True and clash_detection == True:
                #need to check if the moved building is within the boundaries of the landuse 
                is_in_boundary = detect_in_boundary(moved_solid, luse_occface)
                
                if is_in_boundary:
                    #test if it clashes with the other buildings 
                    if moved_buildings:
                        clash_detected = detect_clash(moved_solid, moved_buildings)                    
                        if not clash_detected:
                            #print "I am not clashing onto anyone!!!"
                            isclash = False
                            break
                    
                    else:
                        isclash = False
                        break
            #=======================================================================================  
            elif clash_detection == False and boundary_detection == False:
                isclash = False
                break
            
        if isclash == True:
            print "it is not feasible with these parameters to create a design variant"
            #just append the original arrangements into the list
            return bldg_occsolid_list
        
        if isclash == False:
            #print "successfully positioned the building"
            moved_buildings.append(moved_solid)
            
    print "successfully positioned the buildings"
    return moved_buildings
    
#===========================================================================================================================
def update_gml_building(orgin_gml_building, new_bldg_occsolid, citygml_reader, citygml_writer, new_height = None, new_nstorey = None):
    building_name = citygml_reader.get_gml_id(orgin_gml_building)
    bclass = citygml_reader.get_building_class(orgin_gml_building)
    bfunction = citygml_reader.get_building_function(orgin_gml_building)
    rooftype = citygml_reader.get_building_rooftype(orgin_gml_building)
    stry_blw_grd = citygml_reader.get_building_storey_blw_grd(orgin_gml_building)
    #generic_attrib_dict = citygml_reader.get_generic_attribs(orgin_gml_building)
    face_list = py3dmodel.fetch.faces_frm_solid(new_bldg_occsolid)
    geometry_list = []
    pt_list_list = []
    
    if new_height == None:
        new_height = calculate_bldg_height(new_bldg_occsolid)
        
    if new_nstorey == None:
        #check if there is an existing 
        orig_height = citygml_reader.get_building_height(orgin_gml_building)
        nstorey = citygml_reader.get_building_storey(orgin_gml_building)
        if orig_height !=None and nstorey != None:
            storey_height = round(float(orig_height)/float(nstorey), 2)
            
        else:
            storey_height = 3
            
        new_nstorey = int(math.floor(new_height/storey_height))
        
    for face in face_list:
        pt_list = py3dmodel.fetch.pyptlist_frm_occface(face)
        first_pt = pt_list[0]
        pt_list.append(first_pt)
        pt_list_list.append(pt_list)
        srf = pycitygml.gmlgeometry.SurfaceMember(pt_list)
        geometry_list.append(srf)
    
    citygml_writer.add_building("lod1", building_name, geometry_list, bldg_class =  bclass, 
                                function = bfunction, usage = bfunction, rooftype = rooftype,height = str(new_height),
                                stry_abv_grd = str(new_nstorey), stry_blw_grd = stry_blw_grd)
        
def write_citygml(cityobjmembers, citygml_writer):
        citygml_root = citygml_writer.citymodelnode
        for cityobj in cityobjmembers:
            citygml_root.append(cityobj)
            
#===========================================================================================================================
#for massing2gml
#===========================================================================================================================
def write_gml_srf_member(occface_list):
    gml_geometry_list = []
    for face in occface_list:
        pypt_list = py3dmodel.fetch.pyptlist_frm_occface(face)
        first_pt = pypt_list[0]
        pypt_list.append(first_pt)
        pypt_list.reverse()
        srf = pycitygml.gmlgeometry.SurfaceMember(pypt_list)
        gml_geometry_list.append(srf)
    return gml_geometry_list

def write_gml_triangle(occface_list):
    gml_geometry_list = []
    for face in occface_list:
        pypt_list = py3dmodel.fetch.pyptlist_frm_occface(face)
        n_pypt_list = len(pypt_list)
        if n_pypt_list>3:
            occtriangles = py3dmodel.construct.simple_mesh(face)
            for triangle in occtriangles:
                t_pypt_list = py3dmodel.fetch.pyptlist_frm_occface(triangle)
                t_pypt_list.reverse()
                gml_tri = pycitygml.gmlgeometry.Triangle(t_pypt_list)
                gml_geometry_list.append(gml_tri)
        else:
            pypt_list.reverse()
            gml_tri = pycitygml.gmlgeometry.Triangle(pypt_list)
            gml_geometry_list.append(gml_tri)
            
    return gml_geometry_list
    
def write_gml_linestring(occedge):
    gml_edge_list = []
    occpt_list = py3dmodel.fetch.points_from_edge(occedge)
    pypt_list = py3dmodel.fetch.occptlist2pyptlist(occpt_list)
    linestring = pycitygml.gmlgeometry.LineString(pypt_list)
    gml_edge_list.append(linestring)
    return gml_edge_list
    
def redraw_occ_shell_n_edge(occcompound):
    #redraw the surfaces so the domain are right
    #TODO: fix the scaling 
    recon_shelllist = []
    shells = py3dmodel.fetch.geom_explorer(occcompound, "shell")
    for shell in shells:
        faces = py3dmodel.fetch.geom_explorer(shell, "face")
        recon_faces = []
        for face in faces:
            pyptlist = py3dmodel.fetch.pyptlist_frm_occface(face)
            recon_face = py3dmodel.construct.make_polygon(pyptlist)
            recon_faces.append(recon_face)
        nrecon_faces = len(recon_faces)
        if nrecon_faces == 1:
            recon_shell = py3dmodel.construct.make_shell(recon_faces)
        if nrecon_faces > 1:
            recon_shell = py3dmodel.construct.make_shell_frm_faces(recon_faces)[0]
        recon_shelllist.append(recon_shell)
        
    #boolean the edges from the shell compound and edges compound and find the difference to get the network edges
    shell_compound = py3dmodel.construct.make_compound(shells)
    shell_edges = py3dmodel.fetch.geom_explorer(shell_compound, "edge")
    shell_edge_compound = py3dmodel.construct.make_compound(shell_edges)
    
    edges = py3dmodel.fetch.geom_explorer(occcompound, "edge")
    edge_compound = py3dmodel.construct.make_compound(edges)
    network_edge_compound = py3dmodel.construct.boolean_difference(edge_compound,shell_edge_compound) 
    
    nw_edges = py3dmodel.fetch.geom_explorer(network_edge_compound,"edge")
    recon_edgelist = []
    for edge in nw_edges:
        eptlist = py3dmodel.fetch.points_from_edge(edge)
        epyptlist = py3dmodel.fetch.occptlist2pyptlist(eptlist)
        recon_edgelist.append(py3dmodel.construct.make_edge(epyptlist[0], epyptlist[1]))
        
    recon_compoundlist = recon_shelllist + recon_edgelist
    recon_compound = py3dmodel.construct.make_compound(recon_compoundlist)
    return recon_compound
        
def identify_open_close_shells(occshell_list):
    close_shell_list = []
    open_shell_list = []
    for shell in occshell_list:
        is_closed = py3dmodel.calculate.is_shell_closed(shell)
        if is_closed:
            close_shell_list.append(shell)
        else:
            open_shell_list.append(shell)
            
    return close_shell_list, open_shell_list
    
def reconstruct_open_close_shells(occshell_list):
    close_shell_list, open_shell_list = identify_open_close_shells(occshell_list)
            
    open_shell_compound = py3dmodel.construct.make_compound(open_shell_list)
    open_shell_faces = py3dmodel.fetch.geom_explorer(open_shell_compound, "face")
    #sew all the open shell faces together to check if there are solids among the open shells
    recon_shell_list = py3dmodel.construct.make_shell_frm_faces(open_shell_faces)
    recon_close_shell_list, recon_open_shell_list = identify_open_close_shells(recon_shell_list)
    if recon_close_shell_list:
        recon_close_shell_compound = py3dmodel.construct.make_compound(recon_close_shell_list)
        #boolean difference the close shells from the open shells 
        difference = py3dmodel.construct.boolean_difference(open_shell_compound, recon_close_shell_compound)
        difference = py3dmodel.fetch.shape2shapetype(difference)
        open_shell_faces2 = py3dmodel.fetch.geom_explorer(difference, "face")
        open_shell_list2 = py3dmodel.construct.make_shell_frm_faces(open_shell_faces2)
        return close_shell_list + recon_close_shell_list + open_shell_list2
    else:
        return occshell_list