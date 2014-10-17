"""Creates an SVG of the Databench logo. Optionally also a png."""

import os
import random
import svgwrite

DATA = [
    [0, 1, 1, 1, 1, 0, 1, 1],
    [1, 1, 0, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 0, 1, 1],
    [1, 1, 0, 1, 0, 1, 1, 0],
    [0, 1, 1, 1, 1, 0, 1, 1],
    [1, 0, 1, 0, 1, 1, 0, 1],
]


def color(x, y):
    """triangles.

    Colors:
    - http://paletton.com/#uid=70l150klllletuehUpNoMgTsdcs shade 2
    """

    if (x-4) > (y-4) and -(y-4) <= (x-4):
        # right
        return "#CDB95B"
    elif (x-4) > (y-4) and -(y-4) > (x-4):
        # top
        return "#CD845B"
    elif (x-4) <= (y-4) and -(y-4) <= (x-4):
        # bottom
        return "#57488E"
    elif (x-4) <= (y-4) and -(y-4) > (x-4):
        # left
        return "#3B8772"

    # should not happen
    return "black"


def simple(svg_document, x, y, v):
    if v == 1:
        svg_document.add(svg_document.rect(insert=(x*16, y*16),
                                           size=("16px", "16px"),
                                           # rx="2px",
                                           # stroke_width="1",
                                           # stroke=color(x, y),
                                           fill=color(x, y)))


def smaller(svg_document, x, y, v):
    # from center
    distance2 = (x-3.5)**2 + (y-3.5)**2
    max_distance2 = 2 * 4**2

    if v == 1:
        size = 16.0*(1.0 - distance2/max_distance2)
        number_of_cubes = int(16**2 / (size**2))
        for i in xrange(number_of_cubes):
            xi = x*16 + 1 + random.random()*(14.0-size)
            yi = y*16 + 1 + random.random()*(14.0-size)
            sizepx = str(size)+"px"
            svg_document.add(svg_document.rect(insert=(xi, yi),
                                               size=(sizepx, sizepx),
                                               rx="2px",
                                               stroke_width="1",
                                               stroke=color(x, y),
                                               fill=color(x, y)))


def main():
    svg_favicon = svgwrite.Drawing(filename="favicon.svg",
                                   size=("128px", "128px"))
    svg_document = svgwrite.Drawing(filename="logo.svg",
                                    size=("128px", "128px"))
    for y, r in enumerate(DATA):
        for x, v in enumerate(r):
            simple(svg_favicon, x, y, v)
            smaller(svg_document, x, y, v)
    print(svg_document.tostring())
    svg_favicon.save()
    svg_document.save()

    # create pngs
    os.system('svg2png logo.svg --width=100 --height=100')
    os.system('svg2png logo.svg --width=600 --height=600')
    favicon_sizes = [16, 32, 48, 128, 256]
    for s in favicon_sizes:
        os.system('svg2png favicon.svg --width='+str(s)+' --height='+str(s))
    png_favicon_names = ['favicon-w'+str(s)+'.png' for s in favicon_sizes]
    os.system('convert ' + (' '.join(png_favicon_names)) +
              ' -colors 256 favicon.ico')


if __name__ == "__main__":
    random.seed(42)
    main()
