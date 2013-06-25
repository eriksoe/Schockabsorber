class FrameTable: #------------------------------
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

        self.current_frame_nr = 0
        self.sprite_vector = bytestring(sprite_count * sprite_size)

    def get_raw_sprite(self, sprite_nr):
        offset = sprite_nr * self.sprite_size
        return self.sprite_vector[offset : offset+sprite_size]
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
