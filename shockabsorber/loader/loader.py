
#### Purpose:
# Parse D*R files.
# Individual envelope formats are handled elsewhere (dxr_loader etc.).

import struct
from shockabsorber.model.sections import Section, SectionMap
from shockabsorber.loader.util import SeqBuffer
import shockabsorber.loader.dxr_loader

class KeysSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        [v1,v2,nElems,v3] = buf.unpack('>HHii')
        print("KEY* header: %s" % [v1,v2,nElems,v3])

        res = KeysSection()
        while not buf.at_eof():
            [section_id, cast_id, tag] = buf.unpack('>ii4s')
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
    def parse(blob):
        buf = SeqBuffer(blob)
        res = CastTableSection()
        while not buf.at_eof():
            (item,) = buf.unpack('>i')
            res.entries.append(item)
        return res
#--------------------------------------------------

class CastMember: #------------------------------
    def __init__(self, section_nr, type, castdata):
        self.media = {}
        self.type = type
        self.section_nr = section_nr
        self.castdata = castdata

    def __repr__(self):
        return "<CastMember (@%d) type=%d meta=%s media=%s>" % \
            (self.section_nr, self.type, self.castdata, self.media)

    def add_media(self,tag,data):
        self.media[tag] = data

    @staticmethod
    def parse(blob,snr):
        buf = SeqBuffer(blob)
        (type,) = buf.unpack('>i')
        castdata = CastMember.parse_castdata(type, buf)
        res = CastMember(snr,type, castdata)
        return res

    @staticmethod
    def parse_castdata(type, buf):
        if type==1:
            return ImageCastType.parse(buf)
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
        print "DB| ImageCastType: misc=%s\n  dims=%s anchor=%s" % (misc, dims, anchor)
        self.misc = misc

    def repr_extra(self):
        return " name=\"%s\" dims=%s anchor=%s misc=%s" % (
            self.name, self.dims, self.anchor, self.misc)

    @staticmethod
    def parse(buf):
        [v1,v2,v3,v4,v5,v6,v7, nElems] = buf.unpack('>6iHi')
        for i in range(nElems):
            (_tmp,) = buf.unpack('>i')
        [v8] = buf.unpack('>i')
        name = buf.unpackString8()
        [v9,v10,v11, height,width,v12,v13,v14, anchor_x,anchor_y,
         v15,bits_per_pixel,v17
        ] = buf.unpack('>hIi HH ihh HH bbi')
        total_width = v10 & 0x7FFF
        v10 = "0x%x" % v10
        v12 = "0x%x" % v12
        misc = ((v1,v2,v3,v4,v5,v6,v7,v8),
                (v9,v10,v11), (v12,v13,v14), (v15,v17))
        return ImageCastType(name,
                             (width, height),
                             (total_width,height),
                             (anchor_x, anchor_y),
                             bits_per_pixel,
                             misc)

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
        if (magic=="RIFX" and tag=="MV93"):
            sections_map = shockabsorber.loader.dxr_loader.create_section_map(f)
            cast_table = create_cast_table(sections_map)
            #print "==== cast_table: ===="
            #for cm in cast_table: print "  %s" % cm
            return (cast_table,)
        else:
            raise Exception("Bad file type")

def create_cast_table(mmap):
    # Read the relevant table sections:
    keys_e = mmap.entry_by_tag("KEY*")
    cast_e = mmap.entry_by_tag("CAS*")
    cast_list_section = CastTableSection.parse(cast_e.bytes())
    keys_section      = KeysSection.parse(keys_e.bytes())

    # Create cast table with basic cast-member info:
    def section_nr_to_cast_member(nr):
        if nr==0: return None
        cast_section = mmap[nr].bytes()
        res = CastMember.parse(cast_section,nr)
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
        if cast_id != 0 and cast_id != 1024:
            # Find the cast member to add media to:
#            print "DB| cast_id=%d" % cast_id
            cast_member = aux_map[cast_id]

            # Read the media:
            tag = e["tag"]
            media_section_id = e["section_id"]
            media_section_e = mmap[media_section_id]
            media_section = media_section_e.bytes()
            media = Media.parse(media_section_id, tag, media_section)

            # Add it:
            #print "DB| adding media %s to cast_id %d" % (tag,cast_id)
            cast_member.add_media(tag, media)

    return cast_table
