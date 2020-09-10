#!/usr/bin/env python3
#
# This script updates/inserts copyright statements into any (preferably text)
# file. This works as following: The file should contain somet text like
#
#    Copyright (c) 2020 anabrid GmbH
#    Contact: https://www.anabrid.com/licensing/
#    This file is part of the @MODULE of the @SOFTWARE.
#
# Followed by a line containing something like "ANABRID_BEGIN_LICENSE:GPL",
# where the text after ":" is an identifier for the actual license.
# We have a dictionary of license texts below.
#

magic_begin_license="ANABRID_BEGIN_LICENSE"
magic_end_license  ="ANABRID_END_LICENSE"

license_text = {}

license_text["GPL"] = """
Commercial License Usage
Licensees holding valid commercial anabrid licenses may use this file in
accordance with the commercial license agreement provided with the
Software or, alternatively, in accordance with the terms contained in
a written agreement between you and Anabrid GmbH. For licensing terms
and conditions see https://www.anabrid.com/licensing. For further
information use the contact form at https://www.anabrid.com/contact.

GNU General Public License Usage
Alternatively, this file may be used under the terms of the GNU 
General Public License version 3 as published by the Free Software
Foundation and appearing in the file LICENSE.GPL3 included in the
packaging of this file. Please review the following information to
ensure the GNU General Public License version 3 requirements
will be met: https://www.gnu.org/licenses/gpl-3.0.html.
"""

import sys, os, re, pathlib, collections

files = os.popen("git ls-files").read().strip().split("\n")

counters = collections.defaultdict(int)

class MalformedTagsError(Exception): pass

for fname in files:
    #if pathlib.Path(fname) == pathlib.Path(__file__):
    #    continue # do not process this script itself

    groups = []
    with open(fname, "r") as fh:
        try:
            for i, line in enumerate(fh):
                start = re.match(f"^(?P<prefix>.*) {magic_begin_license}:(?P<license>[a-zA-Z0-9]+)\s*$", line)
                end   = re.match(f"^(?P<prefix>.*) {magic_end_license}\s*$", line)
                if start:
                    if not start.group("license") in license_text:
                        raise MalformedTagsError(f"{fname}: Skipped because license {license} not known. Available licenses are {list(keys(license_text))}.")
                    else:
                        groups.append({ "start": i, **start.groupdict() })
                if end:
                    if len(groups) == 0:
                        raise MalformedTagsError(f"{fname}: Encountered end license tag on line {i} but missed start license tag.")
                    else:
                        if not groups[-1]["prefix"] == end.group("prefix"):
                            raise MalformedTagsError(f"{fname}: Start line {groups[-1]['start']} has incompatible prefix to end line {i}")
                        else:
                            groups[-1]["end"] = i
        class MalformedTagsError as e:
            counters["Skipped (errnous tags)"] += 1
            print(e.message, file=sys.stderr)
            continue
        except UnicodeDecodeError:
            counters["Skipped (binary files)"] += 1
            continue

    if not groups:
        counters["Skipped (no license tag)"] += 1
        continue

    with open(fname, "rw") as fh:
        content = list(fh)
        for group in groups:
            content[group["start"]+1, group["end"]-1] = list(license_text[group["license"]].strip())
        fh.writelines(content)


print("Statistics on number of processed files:")
for k,v in counters.items(): print(f"* {k}: {v}")
