#### Purpose:
# All script-related file parsing.
#

from .util import SeqBuffer, rev
from shockabsorber.model.scripts import ScriptNames

def create_script_context(mmap, loader_context):
    lctx_e = mmap.entry_by_tag("LctX")
    (lnam_sid, lscr_sids) = parse_lctx_section(lctx_e.bytes())

    lnam_e = mmap[lnam_sid]
    names = parse_lnam_section(lnam_e.bytes())
    #scripts = map(lambda sid: parse_lscr_section(mmap[sid].bytes()), lscr_sids)
    scripts = map(lambda sid: (sid,mmap[sid].bytes()), lscr_sids)
    return (names,scripts)

def parse_lctx_section(blob):
    buf = SeqBuffer(blob)
    [v1, v2, nEntries, nEntries2] = buf.unpack('>4i') # Usually v1=v2=0
    [offset,v4] = buf.unpack('>2h') # Usually offset=96, v4=12
    [v5,v6] = buf.unpack('>2i') # Usually v5=0, v6=1
    print "DB| LctX extras: %s" % ([[v1,v2, nEntries2], [v4], [v5,v6]],)

    def read_entry():
        [w1, section_id, w2,w3] = buf.unpack('>ii2h')
        print "DB|   LctX section extras: %s" % ([w1,w2,w3],)
        return section_id

    lnam_section_id = read_entry()
    buf.seek(offset)
    lscr_sections = []
    for i in range(nEntries):
        sid = read_entry()
        if sid != -1: lscr_sections.append(sid)

    return (lnam_section_id, lscr_sections)

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
