# -*- coding: utf-8 -*-
#
"""
I/O for the tria gridpro surface format, cf.
<http://sp.gridpro.com/docs/WS_GUI_Manual_v6.6.pdf>.

2019-01-29 : forked based on off_op format 
"""
from itertools import islice
import logging

import numpy

from .mesh import Mesh


def read(filename):
    with open(filename) as f:
        points, cells = read_buffer(f)
    return Mesh(points, cells)


def read_buffer(f):
    # fast forward to the next significant line
    while True:
        line = next(islice(f, 1))
        stripped = line.strip()
        if stripped and stripped[0] != "#":
            break

    # This next line contains:
    # <number of vertices>
    # 95200
    num_verts = stripped.split(" ")
    num_verts = int(num_verts[0])

    verts = numpy.empty((num_verts, 3), dtype=float)

    # read vertices
    k = 0
    while True:
        if k >= num_verts:
            break
        try:
            line = next(islice(f, 1))
        except StopIteration:
            break
        stripped = line.strip()
        # skip comments and empty lines
        if not stripped or stripped[0] == "#":
            continue

        x, y, z = stripped.split()
        verts[k] = [float(x), float(y), float(z)]
        k += 1

    # This next line contains:
    # <number of faces>
    # 996534
    while True:
        line = next(islice(f, 1))
        stripped = line.strip()
        if stripped and stripped[0] != "#":
            break
    num_faces = stripped.split(" ")
    num_faces = int(num_faces[0])

    # read cells
    triangles = []
    k = 0
    while True:
        if k >= num_faces:
            break

        try:
            line = next(islice(f, 1))
        except StopIteration:
            break

        stripped = line.strip()

        # skip comments and empty lines
        if not stripped or stripped[0] == "#":
            continue

        data = stripped.split()
        num_int = len(data)
        assert num_int == 4, "Can only handle triangular faces, but 4th value is item (group), 0 by default"
        offset = -1 
        data = [int(data[0]) + offset, int(data[1]) + offset, int(data[2]) + offset]
        triangles.append(data)

    cells = {}
    if triangles:
        cells["triangle"] = numpy.array(triangles)

    return verts, cells


def write(filename, mesh):
    if mesh.points.shape[1] == 2:
        logging.warning(
            "gptria requires 3D points, but 2D points given. "
            "Appending 0 third component."
        )
        mesh.points = numpy.column_stack(
            [mesh.points[:, 0], mesh.points[:, 1], numpy.zeros(mesh.points.shape[0])]
        )

    for key in mesh.cells:
        assert key in ["triangle"], "Can only deal with triangular faces"

    tri = mesh.cells["triangle"]

    with open(filename, "wb") as fh:
        #fh.write(b"# Created by meshio\n")

        # counts
        c = "{}\n".format(mesh.points.shape[0])
        fh.write(c.encode("utf-8"))

        # vertices
        numpy.savetxt(fh, mesh.points, "%r")

        # counts
        c = "{}\n".format( len(tri))
        fh.write(c.encode("utf-8"))
        
        # triangles
        #data_with_label = numpy.c_[tri.shape[1] * numpy.ones(tri.shape[0]), tri]
        data_with_label = numpy.c_[ tri]
        numpy.savetxt(fh, data_with_label + 1 ,  "%d %d %d 0")
        

    return
