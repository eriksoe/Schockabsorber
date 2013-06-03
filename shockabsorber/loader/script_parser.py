#### Purpose:
# All script-related file parsing.
#

from .util import SeqBuffer, rev
from shockabsorber.model.scripts import ScriptNames

def create_script_context(mmap, loader_context):
    lctx_e = mmap.entry_by_tag("LctX")
    if lctx_e == None: return (None,None)
    (lnam_sid, lscr_sids) = parse_lctx_section(lctx_e.bytes())

    lnam_e = mmap[lnam_sid]
    names = parse_lnam_section(lnam_e.bytes())
    print "DB| lscr_sids=%s" % (lscr_sids,)
    scripts = map(lambda sid: parse_lscr_section(mmap[sid].bytes(), names), lscr_sids)
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

def parse_lscr_section(blob, names):
    buf = SeqBuffer(blob)
    [v1,v2,totalLength,totalLength2,
     handler_offset0, count1, count2] = buf.unpack('>4i3H')
    [v3,v4,v5,v6,v7,v8,v9,v10,v11] = buf.unpack('>6ihhh')
    [after_strings_offset, v12, count3, offset3, count4, offset4] = buf.unpack('>iiHiHi')
    [handler_count, handler_offset] = buf.unpack('>Hi')
    [string_count, varnames_offset, v20, strings_offset] = buf.unpack('>Hiii')
    print "DB| Lscr extras: %s" % ([[v1,v2,totalLength,totalLength2],
                                    [handler_offset0,count1,count2],
                                    [v3,v4,v5,v6,v7,v8,v9,v10,v11],
                                    [v12, count3, offset4, count4, offset4],
                                    [v20]],)
    print "DB| Lscr offsets: %s" % ([handler_offset0, handler_offset, varnames_offset, strings_offset, after_strings_offset, offset3, offset4],)
    script_id = count1 # ?
    script_id2 = v9 # ?
    varnames_count = v8 # ?

    strings = parse_lscr_string_literals(blob[strings_offset:after_strings_offset],
                                         string_count)
    print "DB| string_count = %d varnames_count = %d handler_count = %d" % (string_count,varnames_count, handler_count)
    print "DB| Lscr.strings: %s" % (dict(enumerate(strings)),)
    return (strings,"TODO")

def parse_lscr_string_literals(blob, count):
    #print "DB| String literals:"
    buf = SeqBuffer(blob)
    res = []
    for i in range(count):
        [length] = buf.unpack('>i')
        #print "DB|   parse_lscr_string_literals: %d/%d: length=%d" % (i,count,length)
        s = buf.readBytes(length)
        if length>0 and s[length-1] == '\0': s=s[:length-1] # Remove NUL terminator
        #print "DB|   #%d/%d: \"%s\"" % (i,count,s)
        res.append(s)
        if length % 2 > 0: buf.unpack('b') # Skip padding

    #print "DB| parse_lscr_string_literals:  bytes left: %d" % (buf.bytes_left())
    return res
