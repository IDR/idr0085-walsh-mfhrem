# Based on code from https://github.com/napari/napari/issues/693#issuecomment-554000321

import argparse
import sys

import numpy as np
from neurom.io import swc
import napari

import omero.cli
from omero.gateway import BlitzGateway
from omero.model import RoiI, PointI
from omero.rtypes import rint, rdouble


def create_roi(image, shapes):
    updateService = image._conn.getUpdateService()
    roi = RoiI()
    roi.setImage(image._obj)
    for shape in shapes:
        roi.addShape(shape)
    return updateService.saveAndReturnObject(roi)


def parse_swc(data, size_y):
    """
    Returns a list of paths (2D numpy arrays of path coordinates)

    Each path is [[z,y,x], [z,y,x]...] suitable for e.g. napari viewer.add_shapes(paths)
    with dimensions correct for overlay with OME image.
    """
    break_points = (
        [0] + list(np.nonzero(np.diff(data[:, 6]) < 0)[0] + 1) + [len(data) - 1]
    )
    paths = []
    max_x = 0
    max_y = 0
    max_z = 0
    for i in range(len(break_points) - 1):
        if break_points[i + 1] - break_points[i] > 2:
            path = data[break_points[i] : break_points[i + 1], :3]
            # path 2D array is [[x,y,z], [x,y,z]...]
            # need to flip to get [[z,y,x], [z,y,x]]
            path = np.flip(path, 1)
            # reverse coordinate direction for y axis.
            path[:, 1] = size_y - path[:, 1]
            paths.append(path)
    print(f"found {len(paths)} paths")
    return paths


def main(conn, argv):

    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Image ID")
    args = parser.parse_args(argv)

    image_id = args.image

    data = swc.read(
        "20200628-ftp/RL_35_guassian_4_4_80.tif_x94_y327_z241_app2_(GSBT).swc"
    ).data_block

    # img_name = 'FADU_tumour_Lectin_substack_deconvolved_RL_35iters_guassian_psf_4_4_80.tif'
    image = conn.getObject("Image", image_id)

    # delete existing ROIs
    roi_service = conn.getRoiService()
    result = roi_service.findByImage(image.id, None)
    roi_ids = [roi.id.val for roi in result.rois]
    if roi_ids:
        print("Deleting ROIs...")
        conn.deleteObjects("Roi", roi_ids, wait=True)

    size_y = image.getSizeY()
    paths = parse_swc(data, size_y)
    red_int = int.from_bytes([255, 0, 0, 255], byteorder="big", signed=True)

    for count, path in enumerate(paths):
        points = []
        for zyx in path:
            z, y, x = zyx
            point = PointI()
            point.x = rdouble(x)
            point.y = rdouble(y)
            point.theZ = rint(round(z))
            point.strokeColor = rint(red_int)
            points.append(point)
        print(f"{count}/{len(paths)} Creating ROI with {len(points)} points")
        create_roi(image, points)


# with napari.gui_qt():
#     viewer = napari.Viewer()
#     viewer.add_shapes(paths, shape_type='path', edge_color='blue')

if __name__ == "__main__":
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn, sys.argv[1:])
