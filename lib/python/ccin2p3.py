"""Utilities for running RETRO at CCIN2P3
"""

import json
import math
import os
import shutil
import subprocess
import sys

TOPO_PATH = "/sps/hep/trend/neu/maps/ASTER-GDEM2"

def system(cmd, mute=False):
    """Run a system command
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if mute:
        return
    if err:
        raise RuntimeError(err)
    return out


def retro_install(path=None, topography=None, hashtag=None):
    """Install RETRO locally
    """

    # Set the path
    if path is None:
        path = os.getenv("TMPDIR")
        if (path is None) or (path == "/scratch"):
            user = os.getenv("USER")
            path = os.path.join("/tmp", user)
    if not os.path.exists(path):
        os.makedirs(path)
    rootdir = os.getcwd()
    os.chdir(path)

    # Get RETRO from GitHub
    if os.path.exists("retro"):
        shutil.rmtree("retro")
    system("git clone https://github.com/grand-mother/retro", mute=True)
    if hashtag is not None:
        system("cd retro && git checkout " + hashtag, mute=True)

    # Build RETRO
    system("cd retro && ./install.sh", mute=True)
    sys.path.append(os.path.join(path, "retro", "lib", "python"))

    # Get the topography tiles from /sps
    if topography:
        sx, sy = None, None
        if not isinstance(topography, dict):
            topography, sx, sy = topography
        if os.path.exists(topography["path"]):
            shutil.rmtree(topography["path"])
        os.makedirs(topography["path"])
        lat0 = int(topography["latitude"])
        lng0 = int(topography["longitude"])
        if sx is None:
            sx = sy = (int(math.sqrt(topography["stack_size"])) - 1) / 2
        for i in xrange(-sx, sx + 1):
            lat = lat0 + i
            if lat >= 0: sn = "N"
            else: sn = "S"
            for j in xrange(-sy, sy + 1):
                lng = lng0 + j
                if lng >= 0: ew = "E"
                else: ew = "W"
                path = os.path.join(TOPO_PATH,
                    "ASTGTM2_{:}{:02d}{:}{:03d}_dem.tif".format(
                        sn, lat, ew, lng))
                shutil.copy(path, topography["path"])

    # Build the worker tag
    tag = os.getenv("JOB_ID")
    if tag is None:
        tag = "local"
    else:
        tid = os.getenv("SGE_TASK_ID")
        if tid is not None:
            tag = ".".join((tag, tid))

    return rootdir, path, tag


def retro_run(events, options, setup=None, outfile=None):
    """Run RETRO with the given options and antenna positions
    """

    # Dump the configuration card
    if outfile is None:
        outfile = "events.json"
    else:
        outdir = os.path.dirname(outfile)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir)
    card = options.copy()
    card["processor"] = {"requested": events}
    card["logger"] = {"path": outfile}
    if setup is not None:
        card["setup"] = { "path": "setup.json" }

    with open("card.json", "wb+") as f:
        json.dump(card, f)

    # Dump the antenna layout
    if setup is not None:
        with open("setup.json", "wb+") as f:
            json.dump(setup, f)

    # Run RETRO
    system(". retro/setup.sh && ./retro/bin/retro-run card.json")
