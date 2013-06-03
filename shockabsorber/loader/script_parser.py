#### Purpose:
# All script-related file parsing.
#

from .util import SeqBuffer, rev
from shockabsorber.model.scripts import ScriptNames

def parse_lnam_section(blob):
    buf = SeqBuffer(blob)
    [v1,v2,len1,len2,v3,numElems] = buf.unpack(">iiiiHH")
    names = []
    for i in range(numElems):
        names.append(buf.unpackString8())
    name_map = {} # For better printing
    for i in range(numElems):
        name_map[i] = names[i]
    return ScriptNames(names, [v1,v2,len1,len2,v3])
#--------------------------------------------------
