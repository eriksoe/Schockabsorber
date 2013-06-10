
#### Purpose:
# Parse D*R files.
# Individual envelope formats are handled elsewhere (dxr_envelope etc.).

import struct
from shockabsorber.model.sections import Section, SectionMap
from shockabsorber.loader.util import SeqBuffer, rev
from . import script_parser
import shockabsorber.loader.dxr_envelope
import shockabsorber.loader.dcr_envelope

class LoaderContext: #------------------------------
    """Contains information about endianness and file format version of a file."""
    def __init__(self, file_tag, is_little_endian):
        self.file_tag = file_tag
        self.is_little_endian = is_little_endian
#--------------------------------------------------

class KeysSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    @staticmethod
    def parse(blob, loader_context):
        buf = SeqBuffer(blob, loader_context.is_little_endian)
        [v1,v2,nElems,v3] = buf.unpack('>HHii')
        print("KEY* header: %s" % [v1,v2,nElems,v3])

        res = KeysSection()
        while not buf.at_eof():
            [section_id, cast_id] = buf.unpack('>ii', '<ii')
            tag = buf.readTag()
            res.entries.append(dict(section_id=section_id,
                                    cast_id=cast_id,
                                    tag=tag))
        return res
#--------------------------------------------------

class CastTableSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    @staticmethod
    def parse(blob, loader_context):
        buf = SeqBuffer(blob)
        res = CastTableSection()
        while not buf.at_eof():
            (item,) = buf.unpack('>i')
            res.entries.append(item)
        return res
#--------------------------------------------------

class CastMember: #------------------------------
    def __init__(self, section_nr, type, name, attrs, castdata):
        self.media = {}
        self.type = type
        self.name = name
        self.attrs = attrs
        self.section_nr = section_nr
        self.castdata = castdata

    def __repr__(self):
        return "<CastMember (@%d) type=%d name=\"%s\" attrs=%s meta=%s media=%s>" % \
            (self.section_nr, self.type, self.name, self.attrs, self.castdata, self.media)

    def add_media(self,tag,data):
        self.media[tag] = data

    @staticmethod
    def parse(blob,snr, loader_context):
        buf = SeqBuffer(blob)
        [type,common_length,v2] = buf.unpack('>3i')
        common_blob = buf.readBytes(common_length)
        buf2 = SeqBuffer(common_blob)
        [v3,v4,v5,v6,script_id,nElems] = buf2.unpack('>5iH')
        offsets = []
        for i in range(nElems+1):
            [tmp] = buf2.unpack('>i')
            offsets.append(tmp)

        blob_after_table=buf2.peek_bytes_left()
        attrs = []
        for i in range(len(offsets)-1):
            attr = blob_after_table[offsets[i]:offsets[i+1]]
            print "DB|   Cast member attr #%d: <%s>" % (i, attr)
            attrs.append(attr)

        if len(attrs)>=2 and len(attrs[1])>0:
            name = SeqBuffer(attrs[1]).unpackString8()
        else:
            name = None

        print "DB| Cast-member common: name=\"%s\"  attrs=%s  misc=%s" % (
            name, attrs, [v2,v3,v4,v5,v6])
        noncommon = buf.peek_bytes_left()
        #print "DB| non-common bytes 2 (len %d): <%s>" % (len(noncommon), noncommon)

        buf.seek(4)

        castdata = CastMember.parse_castdata(type, buf)
        res = CastMember(snr,type, name, attrs, castdata)
        return res

    @staticmethod
    def parse_castdata(type, buf):
        if type==1:
            return ImageCastType.parse(buf)
        elif type==11:
            return ScriptCastType.parse(buf)
        else:
            return None

class CastType: #--------------------
    def __repr__(self):
        return "<%s%s>" % (self.__class__.__name__, self.repr_extra())

    def repr_extra(self): return ""

class ImageCastType(CastType): #--------------------
    def __init__(self, name, dims, total_dims, anchor, bpp, misc):
        self.name = name
        self.dims = dims
        self.total_dims = total_dims
        self.anchor = anchor
        self.bpp = bpp # Bits per pixel
        print "DB| ImageCastType: misc=%s\n  dims=%s total_dims=%s anchor=%s" % (misc, dims, total_dims, anchor)
        self.misc = misc

    def repr_extra(self):
        return " name=\"%s\" dims=%s anchor=%s bpp=%d misc=%s" % (
            self.name, self.dims, self.anchor, self.bpp, self.misc)

    @staticmethod
    def parse(buf):
        [v1,v2,v3,v4,v5,v6,v7,v7b, nElems] = buf.unpack('>6iHHH')
        dims_offset = v1 + 8
        for i in range(nElems):
            (_tmp,) = buf.unpack('>i')
        [v8] = buf.unpack('>i')
        name = buf.unpackString8()
        buf.seek(dims_offset)
        [v9,v10,v11, height,width,v12,v13,v14, anchor_x,anchor_y,
         v15,bits_per_pixel,v17
        ] = buf.unpack('>hIi HH ihh HH bbi')
        total_width = v10 & 0x7FFF
        v10 = "0x%x" % v10
        v12 = "0x%x" % v12
        print "DB| ImageCastType.parse: ILE=%s %s" % (buf.is_little_endian, [(width, height), (total_width,height), bits_per_pixel])
        misc = ((v1,v2,v3,v4,v5,v6,v7,v7b,v8),
                (v9,v10,v11), (v12,v13,v14), (v15,v17))
        return ImageCastType(name,
                             (width, height),
                             (total_width,height),
                             (anchor_x, anchor_y),
                             bits_per_pixel,
                             misc)

#--------------------------------------------------

class ScriptCastType(CastType): #--------------------
    def __init__(self, id, name, misc):
        self.id = id
        self.name = name
        self.misc = misc
        print "DB| ScriptCastType: id=#%d name=\"%s\" misc=%s" % (id, name, misc)

    def repr_extra(self):
        return " id=#%d name=\"%s\" misc=%s" % (self.id, self.name, self.misc)

    @staticmethod
    def parse(buf):
        sz = buf.bytes_left()
        [length_minus_10,v2,v3,v4,v5,v6,script_id,nElems] = buf.unpack('>7iH')
        elems = []
        for i in range(nElems):
            [tmp] = buf.unpack('>i')
            elems.append(tmp)
        [nameLength] = buf.unpack('>i')

        if nameLength>0:
            blob2 = buf.readBytes(nameLength)
            buf2 = SeqBuffer(blob2)
            name = buf2.unpackString8()
        else:
            name = None

        [v30] = buf.unpack('>H')
        misc = [[v2,v3,v4,v5,v6], elems, [v30]]
        return ScriptCastType(script_id, name, misc)

#--------------------------------------------------

class Media: #------------------------------
    def __init__(self,snr,tag,data):
        self.snr = snr
        self.data = data
        self.tag = tag

    def __repr__(self):
        return "<%s (@%d)%s>" % (self.__class__.__name__, self.snr,
                                 self.repr_extra())

    def repr_extra(self): return ""

    @staticmethod
    def parse(snr,tag,blob):
        if tag=="BITD":
            return BITDMedia(snr,tag,blob)
        else:
            return Media(snr,tag,blob)

class BITDMedia(Media): #------------------------------
    def __init__(self,snr,tag,blob):
        Media.__init__(self,snr,tag,blob)
        buf = SeqBuffer(blob)
        "TODO"
#--------------------------------------------------


def load_file(filename):
    with open(filename) as f:
        xheader = f.read(12)
        [magic,size,tag] = struct.unpack('!4si4s', xheader)

        is_little_endian = (magic == "XFIR")
        if is_little_endian:
            tag = rev(tag)
            magic = rev(magic)
        if magic != "RIFX":
            raise Exception("Bad file type")

        loader_context = LoaderContext(tag, is_little_endian)
        print "DB| Loader context: %s / %s" % (tag, is_little_endian)
        if (tag=="MV93"):
            sections_map = shockabsorber.loader.dxr_envelope.create_section_map(f, loader_context)
        elif (tag=="FGDM"):
            sections_map = shockabsorber.loader.dcr_envelope.create_section_map(f, loader_context)
        else:
            raise Exception("Bad file type")

        # for e in sections_map.entries:
        #     if e.tag=="Lnam": print "DB| section: %s: <%s>" % (e.tag, LnamSection.parse(e.bytes()))
        #     if e.tag=="Lscr": print "DB| section: %s: <%s>" % (e.tag, e.bytes())

        cast_lib_table = parse_cast_lib_section(sections_map, loader_context)
        cast_table = create_cast_table(sections_map, loader_context)
        script_ctx = script_parser.create_script_context(sections_map, loader_context)

        #print "==== cast_table: ===="
        #for cm in cast_table: print "  %s" % cm
        print "DB| script_ctx=%s" % (script_ctx,)
        return (cast_table,script_ctx)

def create_cast_table(mmap, loader_context):
    # Read the relevant table sections:
    keys_e = mmap.entry_by_tag("KEY*")
    cast_e = mmap.entry_by_tag("CAS*")
    cast_list_section = CastTableSection.parse(cast_e.bytes(), loader_context)
    keys_section      = KeysSection.parse(keys_e.bytes(), loader_context)
    print "DB| Cast list: %s" % cast_list_section

    # Create cast table with basic cast-member info:
    def section_nr_to_cast_member(nr):
        if nr==0: return None
        cast_section = mmap[nr].bytes()
        res = CastMember.parse(cast_section,nr, loader_context)
        return res
    cast_table = map(section_nr_to_cast_member, cast_list_section.entries)

    # Calculate section_nr -> cast-table mapping:
    aux_map = {}
    for cm in cast_table:
        if cm != None:
            aux_map[cm.section_nr] = cm

    # Add media info:
    for e in keys_section.entries:
        cast_id = e["cast_id"]
        tag = e["tag"]
        if cast_id==0:
            continue
        if not cast_id in aux_map:
            print "No cast section %d (for media section %s)" % (cast_id,tag)
            continue
        if (cast_id & 1024)>0 or tag == "Thum" or tag == "ediM":
            continue
        # Read the media:
        media_section_id = e["section_id"]
        media_section_e = mmap[media_section_id]
        if media_section_e == None:
            print "DB| cast media unresolved: %s->%s (tag=%s)" % (cast_id, media_section_id, tag)
            cast_member.add_media(tag, None)
            continue # Why is this? External media?
        media_section = media_section_e.bytes()
        media = Media.parse(media_section_id, tag, media_section)

        # Add it:
        print "DB| adding media %s to cast_id %d" % (tag,cast_id)
        #print "DB| media contents(#%d:%s)=<%s>" % (media_section_id,tag,media.data)
        # Find the cast member to add media to:
        cast_member = aux_map[cast_id]
        cast_member.add_media(tag, media)

    return cast_table

def parse_cast_lib_section(mmap, loader_context):
    # Obtain 'MCsL' section:
    mcsl_e = mmap.entry_by_tag("MCsL")
    if mcsl_e == None: return None
    blob = mcsl_e.bytes()

    # Read header:
    buf = SeqBuffer(blob)
    [v1,nElems,ofsPerElem,nOffsets,v5] = buf.unpack('>iiHii')
    print "DB| Cast lib section header: nElems=%d, nOffsets=%d, ofsPerElem=%d, misc=%s" % (nElems, nOffsets, ofsPerElem, [v1,v5])

    # Read offset table:
    offsets = []
    for i in range(nOffsets):
        [offset] = buf.unpack('>i')
        offsets.append(offset)
    base = buf.tell()
    #print "DB| Cast lib section: offsets=%s" % offsets

    offnr = 0
    table = []
    for enr in range(nElems):
        entry = []
        for i in range(ofsPerElem):
            subblob = buf.buf[base + offsets[offnr]:base + offsets[offnr+1]]
            offnr += 1
            #print "DB|   i=%d subblob=<%s>" % (i,subblob)
            buf2 = SeqBuffer(subblob)
            if i==0:
                item = buf2.unpackString8()
            elif i==1:
                if buf2.bytes_left()>0:
                    item = buf2.unpackString8()
                else:
                    item = None
            elif i==2:
                [item] = buf2.unpack('>h')
            elif i==3:
                [w1,w2,w3,w4] = buf2.unpack('>hhhh')
                item = (w1,w2,w3,w4)
            else:
                item = subblob
            entry.append(item)
        print "DB| Cast lib table entry: %s" % entry
        table.append(entry)

    return table
