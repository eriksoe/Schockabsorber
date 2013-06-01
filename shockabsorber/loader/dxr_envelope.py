
#### Purpose:
# Parse and create section map for DXR files.
#

import struct
from shockabsorber.model.sections import Section, SectionMap
from shockabsorber.loader.util import SeqBuffer

def create_section_map(f):
    return find_and_read_section(f, "mmap")

def find_and_read_section(f, tag_to_find):
    while True:
        xheader = f.read(8)
        [tag,size] = struct.unpack('!4si', xheader)
        print("  tag=%s" % tag)
        if tag==tag_to_find:
            blob = f.read(size)
            return parse_mmap_section(blob, f)
        else:
            f.seek(size, 1)

def parse_mmap_section(blob, file):
    buf = SeqBuffer(blob)
    [v1,v2,nElems,nUsed,junkPtr,v3,freePtr] = buf.unpack('>HHiiiii')
    print("mmap header: %s" % [v1,v2,nElems,nUsed,junkPtr,v3,freePtr])

    sections = []
    for i in range(nUsed):
        [tag, size, offset, w1,w2, link] = buf.unpack('>4sIIhhi')
        #print("mmap entry: %s" % [tag, size, offset, w1,w2, link])
        sections.append(SectionImpl(tag, size, offset, file))
    return SectionMap(sections)


class SectionImpl(Section):  #------------------------------
    def __init__(self,tag,size,offset, file):
        Section.__init__(self,tag,size)
        self.offset = offset
        self.file = file

    def read_bytes(self):
        file = self.file
        file.seek(self.offset)
        xheader = file.read(8)
        [tag,size] = struct.unpack('!4si', xheader)
        if tag != self.tag:
            raise Exception("section header is actually %s, not %s as expected" % (tag, self.tag))
        return file.read(self.size)
#--------------------------------------------------
