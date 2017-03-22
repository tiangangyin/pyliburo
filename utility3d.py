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
import py3dmodel
import utility
import numpy
from collada import *

def write_2_collada(occshell_list, collada_filepath, face_rgb_colour_list=None, occedge_list = None):
    mesh = Collada()
    mesh.assetInfo.upaxis = asset.UP_AXIS.Z_UP
    mesh.assetInfo.unitmeter = 1.0
    mesh.assetInfo.unitname = "meter"
    
    if face_rgb_colour_list != None:
        mat_list = []
        colour_cnt = 0
        for rgb_colour in face_rgb_colour_list:
            effect = material.Effect("effect" + str(colour_cnt), [], "phong", diffuse=rgb_colour, specular=rgb_colour, double_sided = True)
            mat = material.Material("material" + str(colour_cnt), "mymaterial" + str(colour_cnt), effect)
            mesh.effects.append(effect)
            mesh.materials.append(mat)
            mat_list.append(mat)
            colour_cnt+=1
            
    else:
        effect = material.Effect("effect0", [], "phong", diffuse=(1,1,1), specular=(1,1,1))
        mat = material.Material("material0", "mymaterial", effect)
        mesh.effects.append(effect)
        mesh.materials.append(mat)
        
    edgeeffect = material.Effect("edgeeffect0", [], "phong", diffuse=(1,1,1), specular=(1,1,1), double_sided = True)
    edgemat = material.Material("edgematerial0", "myedgematerial", effect)
    mesh.effects.append(edgeeffect)
    mesh.materials.append(edgemat)
        
    geomnode_list = []
    shell_cnt = 0
    for occshell in occshell_list:
        vert_floats = []
        normal_floats = []
        vcnt = []
        indices = []
        
        face_list = py3dmodel.fetch.geom_explorer(occshell, "face")
        vert_cnt = 0
        for face in face_list:
            pyptlist = py3dmodel.fetch.pyptlist_frm_occface(face)
            vcnt.append(len(pyptlist))
            face_nrml = py3dmodel.calculate.face_normal(face)
            pyptlist.reverse()
            for pypt in pyptlist:
                vert_floats.append(pypt[0])
                vert_floats.append(pypt[1])
                vert_floats.append(pypt[2])
                
                normal_floats.append(face_nrml[0])
                normal_floats.append(face_nrml[1])
                normal_floats.append(face_nrml[2])
                
                indices.append(vert_cnt)
                vert_cnt+=1
                
        vert_id = "ID"+str(shell_cnt) + "1"
        vert_src = source.FloatSource(vert_id, numpy.array(vert_floats), ('X', 'Y', 'Z'))
        normal_id = "ID"+str(shell_cnt) + "2"
        normal_src = source.FloatSource(normal_id, numpy.array(normal_floats), ('X', 'Y', 'Z'))
        geom = geometry.Geometry(mesh, "geometry" + str(shell_cnt), "geometry" + str(shell_cnt), [vert_src, normal_src])
        input_list = source.InputList()
        input_list.addInput(0, 'VERTEX', "#"+vert_id)
        #input_list.addInput(1, 'NORMAL', "#"+normal_id)
        
        vcnt = numpy.array(vcnt)
        indices = numpy.array(indices)
        
        if face_rgb_colour_list!=None:
            mat_name="materialref"+ str(shell_cnt)
            polylist = geom.createPolylist(indices, vcnt, input_list,  mat_name)
            geom.primitives.append(polylist)
            mesh.geometries.append(geom)
            
            matnode = scene.MaterialNode(mat_name, mat_list[shell_cnt], inputs=[])
            geomnode = scene.GeometryNode(geom, [matnode])
            geomnode_list.append(geomnode)
        else:
            mat_name="materialref"
            polylist = geom.createPolylist(indices, vcnt, input_list,  mat_name)
            geom.primitives.append(polylist)
            mesh.geometries.append(geom)
            
            matnode = scene.MaterialNode(mat_name, mat, inputs=[])
            geomnode = scene.GeometryNode(geom, [matnode])
            geomnode_list.append(geomnode)
            
        shell_cnt +=1
        
    if occedge_list:
        edge_cnt = 0
        for occedge in occedge_list:
            vert_floats = []
            indices = []
            occpt_list = py3dmodel.fetch.points_from_edge(occedge)
            pypt_list = py3dmodel.fetch.occptlist2pyptlist(occpt_list)
            if len(pypt_list) == 2:
                vert_cnt = 0
                for pypt in pypt_list:
                    vert_floats.append(pypt[0])
                    vert_floats.append(pypt[1])
                    vert_floats.append(pypt[2])
                    
                    indices.append(vert_cnt)
                    vert_cnt+=1
                    
                vert_id = "ID"+str(edge_cnt+shell_cnt) + "1"
                vert_src = source.FloatSource(vert_id, numpy.array(vert_floats), ('X', 'Y', 'Z'))
                geom = geometry.Geometry(mesh, "geometry" + str(edge_cnt+ shell_cnt), "geometry" + str(edge_cnt+shell_cnt), [vert_src])
                input_list = source.InputList()
                input_list.addInput(0, 'VERTEX', "#"+vert_id)
                indices = numpy.array(indices)
                
                mat_name="edgematerialref"
                linelist = geom.createLineSet(indices, input_list,  mat_name)
                geom.primitives.append(linelist)
                mesh.geometries.append(geom)
                
                matnode = scene.MaterialNode(mat_name, edgemat, inputs=[])
                geomnode = scene.GeometryNode(geom, [matnode])
                geomnode_list.append(geomnode)
                edge_cnt+=1
        
                
    vis_node = scene.Node("node0", children=geomnode_list)
    myscene = scene.Scene("myscene", [vis_node])
    mesh.scenes.append(myscene)
    mesh.scene = myscene
    mesh.write(collada_filepath)
    
def write_2_collada_falsecolour(occface_list, result_list, unit_str, dae_filepath, description_str = None, 
                                minval = None, maxval=None):
    if minval == None:
        minval = min(result_list)
    if maxval == None:
        maxval = max(result_list)
        
    #FOR CREATING THE FALSECOLOUR BAR AND LABELS
    topo_cmpd = py3dmodel.construct.make_compound(occface_list)
    xmin,ymin,zmin,xmax,ymax,zmax = py3dmodel.calculate.get_bounding_box(topo_cmpd)
    x_extend = xmax-xmin
    y_extend = ymax-ymin
    interval = 10.0
    xdim = y_extend/interval
    ydim = y_extend
    rectangle = py3dmodel.construct.make_rectangle(xdim, ydim)
    
    rec_mid_pt = py3dmodel.calculate.face_midpt(rectangle)
    topo_centre_pt = py3dmodel.calculate.get_centre_bbox(topo_cmpd)
    topo_centre_pt = (topo_centre_pt[0], topo_centre_pt[1], zmin)
    loc_pt = py3dmodel.modify.move_pt(topo_centre_pt, (1,0,0), x_extend/1.5)
    moved_rectangle = py3dmodel.fetch.shape2shapetype(py3dmodel.modify.move(rec_mid_pt, loc_pt, rectangle))
    
    grid_srfs = py3dmodel.construct.grid_face(moved_rectangle, xdim, xdim)

    #generate uniform results between max and min
    inc1 = (maxval-minval)/(interval)
    uni_res = utility.frange(minval, end=maxval+0.1, inc=inc1)
    print len(uni_res), uni_res
    inc2 = inc1/2.0
    uni_res2 = utility.frange(minval+inc2, end=maxval, inc=inc1)
    bar_colour = utility.falsecolour(uni_res2, minval, maxval)
    grid_srfs2 = []
    moved_str_face_list = []
    srf_cnt = 0
    for srf in grid_srfs:
        reversed_srf = py3dmodel.modify.reverse_face(srf)
        grid_srfs2.append(reversed_srf)
        res_label = round(uni_res[srf_cnt],2)
        brep_str = py3dmodel.fetch.shape2shapetype(py3dmodel.construct.make_brep_text(str(res_label), xdim))
        orig_pt = py3dmodel.calculate.get_centre_bbox(brep_str)
        loc_pt = py3dmodel.calculate.face_midpt(srf)
        loc_pt = py3dmodel.modify.move_pt(loc_pt, (1,-0.2,0), xdim*3)
        moved_str = py3dmodel.modify.move(orig_pt, loc_pt, brep_str)
        moved_str_face_list.append(moved_str)
        
        if srf_cnt == len(grid_srfs)-1:
            res_label = round(uni_res[srf_cnt+1],2)
            brep_str = py3dmodel.fetch.shape2shapetype(py3dmodel.construct.make_brep_text(str(res_label), xdim))
            orig_pt = py3dmodel.calculate.get_centre_bbox(brep_str)
            loc_pt3 = py3dmodel.modify.move_pt(loc_pt, (0,1,0), xdim)
            moved_str = py3dmodel.modify.move(orig_pt, loc_pt3, brep_str)
            moved_str_face_list.append(moved_str)
        
            brep_str_unit = py3dmodel.construct.make_brep_text(str(unit_str), xdim)
            orig_pt2 = py3dmodel.calculate.get_centre_bbox(brep_str_unit)
            loc_pt2 = py3dmodel.modify.move_pt(loc_pt, (0,1,0), xdim*2)
            moved_str = py3dmodel.modify.move(orig_pt2, loc_pt2, brep_str_unit)
            moved_str_face_list.append(moved_str)
            
        if description_str !=None:    
            if srf_cnt == 0:
                d_str = py3dmodel.fetch.shape2shapetype(py3dmodel.construct.make_brep_text(description_str, xdim))
                orig_pt2 = py3dmodel.calculate.get_centre_bbox(d_str)
                loc_pt2 = py3dmodel.modify.move_pt(loc_pt, (0,-1,0), xdim*5)
                moved_str = py3dmodel.modify.move(orig_pt2, loc_pt2, d_str)
                moved_str_face_list.append(moved_str)
            

        srf_cnt+=1
        
    cmpd = py3dmodel.construct.make_compound(moved_str_face_list)
    face_list = py3dmodel.fetch.geom_explorer(cmpd, "face")
    meshed_list = []
    for face in face_list:    
        meshed_face_list = py3dmodel.construct.simple_mesh(face)
        mface = py3dmodel.construct.make_shell(meshed_face_list)
        #py3dmodel.construct.merge_faces(meshed_face_list)[0]
        face_mid_pt =  py3dmodel.calculate.face_midpt(face)
        str_mid_pt = py3dmodel.calculate.get_centre_bbox(mface)
        moved_mface = py3dmodel.modify.move(str_mid_pt,face_mid_pt,mface)
        meshed_list.append(moved_mface)
        
    meshed_cmpd = py3dmodel.construct.make_compound(meshed_list)
    str_colour_list = [(0,0,0)]
        
    falsecolour_list = utility.falsecolour(result_list, min(result_list), max(result_list))
    falsecolour_list = []
    for result in result_list:
        if result >= maxval:
            falsecolour_list.append(bar_colour[-1])
            
        elif result <= minval:
            falsecolour_list.append(bar_colour[0])
            
        else:
            ur_cnt=0
            for u_res in uni_res2:
                if u_res-inc2 <=result<= u_res+inc2:
                    falsecolour_list.append(bar_colour[ur_cnt])
                    break
                ur_cnt+=1
    
    #ARRANGE THE SURFACE AS ACCORDING TO ITS COLOUR
    colour_list = []
    c_srf_list = []
    for r_cnt in range(len(falsecolour_list)):
        fcolour = falsecolour_list[r_cnt]
        rf = occface_list[r_cnt]
        if fcolour not in colour_list:
            colour_list.append(fcolour)
            c_srf_list.append([rf])
            
        elif fcolour in colour_list:
            c_index = colour_list.index(fcolour)
            c_srf_list[c_index].append(rf)
          
    cmpd_list = []
    #SORT EACH SURFACE AS A COMPOUND
    for c_cnt in range(len(c_srf_list)):
        c_srfs = c_srf_list[c_cnt]
        compound = py3dmodel.construct.make_compound(c_srfs)
        cmpd_list.append(compound)
        
    write_2_collada(cmpd_list + grid_srfs2 + [meshed_cmpd]  , dae_filepath, face_rgb_colour_list = colour_list+bar_colour+str_colour_list  )
    
def generate_falsecolour_bar(minval, maxval, unit_str):
    xdim = 1
    ydim = 10
    rectangle = py3dmodel.construct.make_rectangle(xdim, ydim)
    grid_srfs = py3dmodel.construct.grid_face(rectangle, xdim, 1)
    #generate uniform results between max and min
    uni_res = utility.frange(minval, end=maxval+0.1, inc=(maxval-minval)/9.0)

    bar_colour = utility.falsecolour(uni_res, minval, maxval)
    moved_str_face_list = []
    str_colour_list= []
    srf_cnt = 0
    for srf in grid_srfs:
        res_label = round(uni_res[srf_cnt],2)
        brep_str = py3dmodel.construct.make_brep_text(str(res_label), 1)
        orig_pt = py3dmodel.calculate.get_centre_bbox(brep_str)
        loc_pt = py3dmodel.calculate.face_midpt(srf)
        loc_pt = py3dmodel.modify.move_pt(loc_pt, (1,0,0), 3)
        moved_str = py3dmodel.modify.move(orig_pt, loc_pt, brep_str)
        moved_str_face_list.append(moved_str)
        str_colour_list.append((0,0,0))
        if srf_cnt == len(grid_srfs)-1:
            brep_str_unit = py3dmodel.construct.make_brep_text(str(unit_str), 1)
            orig_pt2 = py3dmodel.calculate.get_centre_bbox(brep_str_unit)
            loc_pt2 = py3dmodel.modify.move_pt(loc_pt, (0,1,0), 1)
            moved_str = py3dmodel.modify.move(orig_pt2, loc_pt2, brep_str_unit)
            moved_str_face_list.append(moved_str)
            str_colour_list.append((0,0,0))
        srf_cnt+=1
        
    return grid_srfs, bar_colour, moved_str_face_list, str_colour_list
    