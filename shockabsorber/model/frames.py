import struct

class FrameSequence: #------------------------------
    def __init__(self, sprite_count, sprite_size, frame_list):
        """
        frame_list is a list of FrameDelta objects,
        one for each frame in order.

        sprite_count is the total number of sprites.

        sprite_size is the size of each sprite, in bytes.
        """
        self.sprite_count = sprite_count
        self.sprite_size = sprite_size
        self.frame_list = frame_list

        self.reset_sprite_vector()
        self.go_to_frame(1)

    def reset_sprite_vector(self):
        self.current_frame_nr = -1
        self.sprite_vector = bytearray(self.sprite_count * self.sprite_size)

    def frame_count(self):
        return len(self.frame_list)

    def sprite_count(self):
        return self.sprite_count

    def go_to_frame(self, where):
        where -=1 # Adjust: array is 0-based
        if self.current_frame_nr > where:
            # Could perhaps optimize this.
            self.reset()
        while self.current_frame_nr < where:
            self.current_frame_nr += 1
            self.frame_list[self.current_frame_nr].apply_to(self.sprite_vector)

    def get_sprite(self, sprite_nr):
        return Sprite(sprite_nr, self.get_raw_sprite(sprite_nr))

    def get_raw_sprite(self, sprite_nr):
        offset = sprite_nr * self.sprite_size
        return self.sprite_vector[offset : offset+self.sprite_size]

#--------------------------------------------------

class FrameDelta: #------------------------------
    def __init__(self, items):
        self.items = items

    def apply_to(self, target):
        for item in self.items:
            item.apply_to(target)
#--------------------------------------------------

class FrameDeltaItem: #------------------------------
    def __init__(self, start, bytes):
        self.start = start
        self.bytes = bytes

    def apply_to(self, target):
        target[self.start:self.start + len(self.bytes)] = self.bytes
#--------------------------------------------------

class Sprite: #------------------------------
    def __init__(self, nr, raw):
        self.nr = nr
        self.set_bytes(raw)

    def set_bytes(self,raw):
        self.raw = raw
        [flags1, v2, castlib, castmember, v5, interval_ref,
         posX, posY, width, height,
         v11, v12, v13, v14, v15, v16
        ] = struct.Struct('>16h').unpack_from(buffer(raw), 0)
        rest = raw[16:]
        self.member_ref = (castlib, castmember)
        self.interval_ref = interval_ref
        self.pos = (posX, posY)
        self.size = (width,height)
        self.extras = [flags1, v2, v5, v11, v12, v13, v14, v15, v16, rest]

    def __repr__(self):
        return "<Sprite #%d member=%s ref=%s pos=%s size=%s extras=%s>" % (
            self.nr, self.member_ref, self.interval_ref,
            self.pos, self.size, self.extras)
#--------------------------------------------------
