#!/usr/bin/python3
# pynetem: network emulator
# Copyright (C) 2019 Mickael Royer <mickael.royer@recherche.enac.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import sys
import os
import argparse
import logging
import subprocess
import shlex
import glob
import shutil

DISTRIBUTIONS = [
    ("sid", "-1"),
    ("buster", "-1~bpo10+1"),
    ("focal", "-1~focal+1"),
]

parser = argparse.ArgumentParser(description='Network emulator daemon')
parser.add_argument(
    'version', metavar='VERSION', type=str, nargs=1,
    default=None, help='version number for this release'
)
parser.add_argument(
    "-d", "--debug", action="store_true", dest="debug", default=False,
    help="Log more debug informations"
)
parser.add_argument(
    "-s", "--skip", action="append", dest="skip_dists", default=[],
    help="Skip a distribution in the build process"
)
parser.add_argument(
    "-l", "--log-file", type=str, dest="log_file",
    metavar="FILE", default="/tmp/pkg-build.log",
    help="File where build logs are recorded"
)
parser.add_argument(
    "-p", "--pbuilder-dir", type=str, dest="pbuilder",
    metavar="FOLDER", default=None,
    help="Folder where pbuilder basetgz has been stored"
)
args = parser.parse_args()


def build(root_dir, pbuilder_dir, distribution, version, suffix, log_hd):
    logging.info("Build package for distribution %s", distribution)

    full_version = version + suffix
    # first run dch to update changelog
    if distribution != "sid":
        logging.debug("Run dch for distribution %s", distribution)
        cmd = shlex.split(
            "dch -b --distribution %s --package 'pynetem' "
            "-v '%s' 'new upstream release'" % (distribution, full_version))
        result = subprocess.run(cmd, cwd=root_dir, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logging.error(
                "Unable to update changelog for %s, skip build: %s" \
                % (distribution, result.stderr))
            return

    # use pdebuild to buil package
    logging.debug("Run pdebbuild for distribution %s", distribution)
    basetgz = os.path.join(pbuilder_dir, "{}.tgz".format(distribution))
    if not os.path.isfile(basetgz):
        logging.error("Basetgz '{}' is not found, skip build".format(basetgz))
        return
    cmd = shlex.split(
        "pdebuild --pbuilderroot sudo --pbuildersatisfydepends sudo "
        " --buildsourceroot sudo -- "
        "--basetgz {}".format(basetgz)
    )
    result = subprocess.run(
        cmd, cwd=root_dir, stderr=subprocess.STDOUT, stdout=log_hd)
    if result.returncode != 0:
        logging.error("Unable to build pkg for %s", distribution)
        logging.error("See log file for details")
        return False

    # save package in build dir
    build_dir = os.path.join(root_dir, "..", "build", version)
    build_dir = os.path.abspath(build_dir)
    if not os.path.isdir(build_dir):
        logging.debug("Create build folder '{}'".format(build_dir))
        os.mkdir(build_dir)
    files = glob.glob(
        "/var/cache/pbuilder/result/pynetem_{}*".format(full_version))
    for f in files:
        shutil.copy(f, build_dir)

    return True


if __name__ == "__main__":
    log_level = args.debug and logging.DEBUG or logging.INFO
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s: %(message)s',
        level=log_level)

    version = args.version[0]
    if args.pbuilder is None or not os.path.isdir(args.pbuilder):
        sys.exit("Pbuilder folder does not exist")
    root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".."))
    logging.debug("Set root_dir to %s", root_dir)

    # prepare source archive
    with open(args.log_file, "w") as log_hd:
        logging.info("Prepare source archive")

        cmd = shlex.split("./setup.py sdist")
        result = subprocess.run(
            cmd, cwd=root_dir,
            stderr=subprocess.STDOUT, stdout=log_hd)
        if result.returncode != 0:
            logging.error("Unable to prepare src archive")
            logging.error("See log file for details")
            sys.exit(1)

        dest_file = "pynetem_{}.orig.tar.gz".format(version)
        shutil.move(
            os.path.join(root_dir, "dist", "pynetem-{}.tar.gz").format(version),
            os.path.join(root_dir, "..", dest_file))

        # build packages for all distributions
        for (distrib, suffix) in DISTRIBUTIONS:
            if distrib in args.skip_dists:
                logging.info("Skip distribution %s", distrib)
                continue
            build_result = build(
                root_dir, args.pbuilder,
                distrib, version, suffix, log_hd)
            if not build_result:
                sys.exit(1)
