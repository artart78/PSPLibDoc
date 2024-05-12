#! /usr/bin/env python3

import psp_libdoc
import glob
from collections import defaultdict

nid_map = defaultdict(set)

filelist = glob.glob('**/*.xml', recursive=True)[:1000]
for (idx, file) in enumerate(filelist):
    if (idx % 100 == 99):
        print("%d/%d..." % (idx + 1, len(filelist)))
    entries = psp_libdoc.loadPSPLibdoc(file)
    for e in entries:
        nid_map[e.nid].add(e.name)

for nid in nid_map:
    if len(nid_map[nid]) > 1:
        if not all([x.endswith(nid) for x in nid_map[nid]]):
            print(nid_map[nid])

