import pyglet.image


# Returns an ImageData
def rle_decode(width, height, fullwidth, bpp, encoded_data):
    res = "" # TODO: pre-allocated bytestring
    in_pos = 0; in_len = len(encoded_data)
    out_pos = 0
    #x = 0; y = 0
    #fullwidth = width*(bpp//8)
    bytes_to_output = fullwidth*height
    while in_pos < in_len and out_pos < bytes_to_output:
        d = ord(encoded_data[in_pos]); in_pos+=1
        if d >= 128:
            run_length = 257-d
            v = encoded_data[in_pos]; in_pos+=1
            for i in range(run_length): res += v
            out_pos += run_length
        else:
            lit_length = 1+d
            res += encoded_data[in_pos:in_pos+lit_length]; in_pos += lit_length
            out_pos += lit_length
    print "DB| rle end: out_pos: %d vs. expected %d; in_pos: %d vs. %d" % (out_pos, bytes_to_output, in_pos, in_len)
    #print "DB| rle: converted %s to %s" % (encoded_data, res)

    if bpp == 8:
        return make_greyscale_image(width, height, fullwidth, res)
    elif bpp == 16:
        return make_16bit_rbg_image(width, height, fullwidth, res)
    elif bpp == 32:
        return make_32bit_rbg_image(width, height, fullwidth, res)
    else:
        print "Warning: RLE: Unknown bpp: %d" % bpp
        return make_greyscale_image(width, height, fullwidth, res)

def make_greyscale_image(width, height, fullwidth, data):
    return pyglet.image.ImageData(width, height, 'I', data, -fullwidth)

def make_8bit_rbg_image(width, height, fullwidth, data):
    color_res = ""
    for c in res:
        nr = ord(c)
        r = nr >> 5
        g = (nr >> 2) & 7
        b = nr & 3
        #r = nr // 36
        #g = (nr // 6) % 6
        #b = nr % 6
        #if r>5: r=5; g=5; b=5
        color_res += chr(r*(255//7))
        color_res += chr(g*(255//7))
        color_res += chr(b*(255//3))
    return pyglet.image.ImageData(width, height, 'RGB', color_res, -3*width)

def make_16bit_rbg_image(width, height, fullwidth, data):
    color_res = ""
    for y in range(height):
        for x in range(width):
            highbits = ord(data[y*fullwidth + x])
            lowbits  = ord(data[y*fullwidth + x + width])
            bits = (highbits << 8) | lowbits
            a = bits >> 15
            r = (bits >> 10) & 31
            g = (bits >> 5) & 31
            b = bits & 31
            if a>0: r=31; g=31; b=0
            color_res += chr(r*(255//31))
            color_res += chr(g*(255//31))
            color_res += chr(b*(255//31))
    return pyglet.image.ImageData(width, height, 'RGB', color_res, -3*width)

def make_32bit_rbg_image(width, height, fullwidth, data):
    color_res = ""
    for y in range(height):
        for x in range(width):
            r = data[y*fullwidth + x]
            g = data[y*fullwidth + x + width]
            b = data[y*fullwidth + x + 2*width]
            a = data[y*fullwidth + x + 3*width]
            color_res += r
            color_res += g
            color_res += b
            color_res += a
    return pyglet.image.ImageData(width, height, 'RGBA', color_res, -4*width)


