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
    [string_count, footnote_offset, v20, strings_offset] = buf.unpack('>Hiii')
    print "DB| Lscr extras: %s" % ([[v1,v2,totalLength,totalLength2],
                                    [handler_offset0,count1,count2],
                                    [v3,v4,v5,v6,v7,v8,v9,v10,v11],
                                    [v12, count3, offset4, count4, offset4],
                                    [v20]],)
    print "DB| Lscr offsets: %s" % ([handler_offset0, handler_offset, footnote_offset, strings_offset, after_strings_offset, offset3, offset4],)
    print "DB|   part-before-handler-table: <%s>" % (buf.buf[handler_offset0:handler_offset],)
    print "DB|   footnotes-part: <%s>" % (buf.buf[footnote_offset:strings_offset],)
    script_id = count1 # ?
    script_id2 = v9 # ?
    varnames_count = v8 # ?

    print "DB| string_count = %d varnames_count = %d handler_count = %d" % (string_count,varnames_count, handler_count)

    strings = parse_lscr_string_literals(blob[strings_offset:after_strings_offset],
                                         string_count)
    print "DB| Lscr.strings: %s" % (dict(enumerate(strings)),)
    handlers_meta = parse_lscr_handler_table(subblob(blob, (handler_offset, 46*handler_count)),
                                             handler_count, names)
    for h in handlers_meta:
        [name, code_slice, varnames_slice, varname_count,
         auxslice1, auxslice2, auxslice3, misc] = h
        varnames = parse_lscr_varnames_table(subblob(blob, varnames_slice), varname_count,
                                             names)
        aux1 = subblob(blob, auxslice1)
        aux2 = subblob(blob, auxslice2)
        aux3 = subblob(blob, auxslice3)
        code_blob = subblob(blob, code_slice)
        print "DB| handler %s:\n    code-bin=<%s>\n    vars=%s\n    aux=<%s>/<%s>/<%s>" % (
            name, code_blob, varnames, aux1, aux2, aux3)
        code = parse_lscr_code(code_blob, names, strings, varnames)
        print "DB| handler %s:\n    code=%s" % (name, code)
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

def parse_lscr_handler_table(blob, count, names):
    buf = SeqBuffer(blob)
    res = []
    for i in range(count):
        [handler_name_nr, v1, code_length, code_offset] = buf.unpack('>hhii')
        [varname_count, varnames_offset,
         length5, offset5,
         length7, offset7, v8] = buf.unpack('>hihihii')
        [v10, length12, offset12, v13] = buf.unpack('>hhii')

        handler_name = names[handler_name_nr]
        print "DB| * handler_name = '%s' (0x%x)" % (handler_name, handler_name_nr)
        print "DB|   subsections = %s" % ([(code_offset, code_length),
                                           (varnames_offset, varname_count),
                                           (offset5, length5),
                                           (offset7, length7),
                                           (offset12, length12)],)
        print "DB|   handler extras = %s" % ([v1, v8, v10, v13],)
        misc = [v1, v8, v10, v13]
        res.append((handler_name,
                    (code_offset, code_length),
                    (varnames_offset, 2 * varname_count), varname_count,
                    (offset5, length5),
                    (offset7, length7),
                    (offset12, length12),
                    misc))
    return res

def parse_lscr_varnames_table(blob, count, names):
    buf = SeqBuffer(blob)
    res = []
    for i in range(count):
        [name_nr] = buf.unpack('>h')
        res.append(names[name_nr])
    return res

OPCODE_SPEC = {
    0x01: ("Return", []),
    0x03: ("Push-int-0", []),
    0x04: ("Multiply", []),
    0x05: ("Add", []),
    0x06: ("Subtract", []),
    0x07: ("Divide", []),
    0x0e: ("Not-equals", []),
    0x0d: ("Less-than-or-equals", []),
    0x0f: ("Equals", []),

    0x10: ("Greater-than", []),
    0x15: ("String-contains", []),
    0x1e: ("Construct-linear-array", []),

    0x21: ("Push-something ('into')", []),

    0x41: ("Push-int", ['int8']),
    0x42: ("Set-arg-count-A", ['int8']),
    0x43: ("Set-arg-count-B", ['int8']),
    0x44: ("Push-string", ['str8']),
    0x45: ("Push-symbol", ['sym8']),
    0x49: ("Push-global", ['sym8']),
    0x4a: ("Push-property", ['sym8']),
    0x4b: ("Push-parameter", ['locvar8']),
    0x4c: ("Push-local", ['int8']), # ~> locvar8

    0x50: ("Store-property", ['sym8']),
    0x52: ("Store-local", ['int8']), # ~> locvar8
    0x56: ("Call-local", ['int8']),
    0x57: ("Call", ['sym8']),
    0x5c: ("Get-builtin", ['int8']),

    0x64: ("Dup", ['int8']),
    0x65: ("Pop", ['int8']),
    0x66: ("Call-getter", ['sym8']), # 'the'
    0x67: ("Call-getter-method", ['sym8']),
    0x70: ("Get-special-field", ['sym8']),

    0x61: ("Get-field", ['sym8']),
    0x62: ("Put-field", ['sym8']),

     # 16-versions of (opcode-0x40):
    0x85: ("Push-symbol", ['sym16']),
    0x89: ("Push-global", ['sym16']),
    0x8a: ("Push-property", ['sym16']),
    0x8f: ("Store-global", ['sym16']),
    0x90: ("Store-property", ['sym16']),
    0x94: ("Jump-relative-back", ['relb16']),
    0x93: ("Jump-relative", ['rel16']),
    0x97: ("Call", ['sym16']),
    0x9f: ("Call-getter", ['sym16']), # 'the'
    0xa1: ("Get-field", ['sym16']),
    0xa6: ("Call-getter-B", ['sym16']), # 'the'
    0xa7: ("Call-special", ['sym16']),
    0xae: ("Push-int", ['int16']),

    0x95: ("Jump-relative-unless", ['rel16']),
}

def parse_lscr_code(blob, names, strings, names_of_locals):
    print "DB| handler code blob (length %d): <%s>" % (len(blob), blob)
    buf = SeqBuffer(blob)
    res = []
    while not buf.at_eof():
        codepos = buf.offset
        [opcode] = buf.unpack('B')
        if opcode in OPCODE_SPEC:
            (opcode,argspec) = OPCODE_SPEC[opcode]
            args = []
            for a in argspec:
                if a=='int8':
                    [arg] = buf.unpack('b')
                elif a=='str8':
                    [arg] = buf.unpack('B')
                    arg = strings[arg]
                elif a=='sym8':
                    [arg] = buf.unpack('B')
                    arg = names[arg]
                elif a=='locvar8':
                    [arg] = buf.unpack('B')
                    arg = (arg,names_of_locals[arg])
                elif a=='rel8':
                    [arg] = buf.unpack('B')
                    arg = (arg, codepos+arg)
                elif a=='int16':
                    [arg] = buf.unpack('>h')
                elif a=='sym16':
                    [arg] = buf.unpack('>H')
                    arg = names[arg]
                elif a=='rel16':
                    [arg] = buf.unpack('>H')
                    arg = (arg, codepos+arg)
                elif a=='relb16':
                    [arg] = buf.unpack('>H')
                    arg = (arg, codepos-arg)
                args.append(arg)
        # TODO: Remove these fallbacks, eventually:
        elif opcode >= 0x80:
            opcode = ("UNKNOWN-OPCODE",opcode)
            [arg] = buf.unpack('>H')
            args = [arg]
        else:
            opcode = ("UNKNOWN-OPCODE",opcode)
            [arg] = buf.unpack('B')
            args = [arg]
        print "DB|    code: %s" % ((codepos,opcode,args),)
        res.append((codepos,opcode,args))
    return res

###========== Utilities: ========================================
def subblob(blob, slice_desc):
    (offset, length) = slice_desc
    return blob[offset : offset + length]
