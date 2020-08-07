#!/usr/bin/env python

# This has to run as user omero-server.
# Assumes that omero-upload was installed on the server.

# sudo su omero-server
# . /opt/omero/server/venv3/bin/activate
# python upload_files.py

import os
import omero.clients
import omero.cli
from omero.model import FileAnnotationI
from omero_upload import upload_ln_s

"""
This script uploads files onto Images
"""

project_name = "idr0085-walsh-mfhrem/experimentA"

OMERO_DATA_DIR = "/data/OMERO"
FILESETS_DIR = "/uod/idr/filesets/idr0085-walsh-mfhrem/"
NAMESPACE = "openmicroscopy.org/idr/analysis/original"
MIMETYPE = "application/octet-stream"

# [file, Image]
to_upload = [
    [
        "20200717-ftp/Final_Display_of_RLTV_correct_scale0000.tif_import.tif_processed_MOST_thresh20.swc",
        "Deconvolved_brain_Lectin_pxl_xy_1.14_pxl_z_1.72.tif",
    ],
    [
        "20200628-ftp/RL_35_guassian_4_4_80.tif_x94_y327_z241_app2_(GSBT).swc",
        "FADU_tumour_Lectin_substack_deconvolved_RL_35iters_guassian_psf_4_4_80.tif",
    ],
]


def upload_and_link(conn, target, attachment):
    print("upload_and_link", attachment)
    attachment = os.path.join(FILESETS_DIR, attachment)
    fo = upload_ln_s(conn.c, attachment, OMERO_DATA_DIR, MIMETYPE)
    fa = FileAnnotationI()
    fa.setFile(fo._obj)
    fa.setNs(omero.rtypes.rstring(NAMESPACE))
    fa = conn.getUpdateService().saveAndReturnObject(fa)
    fa = omero.gateway.FileAnnotationWrapper(conn, fa)
    target.linkAnnotation(fa)


def main(conn):

    project = conn.getObject("Project", attributes={"name": project_name})
    print("Project", project.id)

    images_by_name = {}
    for dataset in project.listChildren():
        for image in dataset.listChildren():
            images_by_name[image.name] = image

    for names in to_upload:
        file_path = names[0]
        image_name = names[1]

        image = images_by_name[image_name]
        print("link to", image.name)
        upload_and_link(conn, image, file_path)


if __name__ == "__main__":
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn)
