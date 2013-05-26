import pyglet
import sys
import loader
import rle

W = 2600; H = 1200
window = pyglet.window.Window(width=W, height=H)

(cast_table,) = loader.load_file(sys.argv[1])

@window.event
def on_draw():
    print "\non_draw"
    window.clear()

    y = 0; x=0; maxw = 0
    for cm in cast_table:
        if cm==None: continue
        if cm.type != 1: continue
        if not 'BITD' in cm.media: continue
        castdata = cm.castdata
        media = cm.media['BITD']
        (w,h) = castdata.dims
        (tw,th) = castdata.total_dims
        #if len(media.data) < 500 or len(media.data) > 2000: continue
        print "DB| cm=%s media=%s w=%d h=%d tw=%d" % (cm,media, w,h, tw)
        image = rle.rle_decode(tw,h, media.data)
        if y+h>=H:
            y = 0; x+= maxw + 20; maxw = 0
            if x>=W: break
        image.blit(x,y)
        if tw>maxw: maxw = tw
        y += h + 20
    # canvas.blit(100,100)


pyglet.app.run()
