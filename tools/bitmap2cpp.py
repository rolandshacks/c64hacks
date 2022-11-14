#
# Bitmap To C++
#

import sys
import os
import getopt
import png

HEXCHARS = "0123456789abcdef"
TYPENAME_BITMAP = "bitmap_info_t"

class Rect:
    def __init__(self, left, top, right, bottom):
        self.set(left, top, right, bottom)

    def set(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = right - left
        self.height = bottom - top

def colorToFloat(c):
    f = (float(c) + 0.5) / 255.0
    return min(1.0, f)

def brightness(r, g, b):
    return (r + g + b) / 3.0

def process(input_file, rect=None, index=None, flag_multicolor=False):
    r = png.Reader(input_file)
    width, height, rows, info = r.read()
    bytes_per_pixel = info["planes"]
    has_alpha = info["alpha"]
    bits_per_pixel = bytes_per_pixel * info["bitdepth"]
    palette = None
    if "palette" in info:
        palette = info["palette"]

    buffer = []

    if not rect:
        rect = Rect(0, 0, width, height)

    step_size = 8 if not flag_multicolor else 4
    max_steps = 24 if not flag_multicolor else 12

    y = 0
    for row in rows:

        if y < rect.top:
            y += 1
            continue
        elif y >= rect.bottom:
            break

        bit = 0
        accumulator = 0
        alpha_accumulator = 0

        for x in range(rect.left, rect.right):

            ofs = x * bytes_per_pixel

            transparent = False
            intensity = 1.0

            if 24 == bits_per_pixel:
                r = colorToFloat(row[ofs+0])
                g = colorToFloat(row[ofs+1])
                b = colorToFloat(row[ofs+2])
                intensity = brightness(r,g,b)
            elif 32 == bits_per_pixel:
                r = colorToFloat(row[ofs+0])
                g = colorToFloat(row[ofs+1])
                b = colorToFloat(row[ofs+2])
                intensity = brightness(r,g,b)
                if has_alpha:
                    a = row[ofs+3]
                    if a < 128:
                        transparent = True
            elif 8 == bits_per_pixel or 4 == bits_per_pixel or 2 == bits_per_pixel:
                if palette:
                    idx = row[ofs]
                    col = palette[idx]
                    r = col[0]
                    g = col[1]
                    b = col[2]
                    intensity = brightness(r,g,b)
                    if len(col) > 3:
                        a = col[3]
                        if a < 128:
                            transparent = True
                else:
                    intensity = 1.0 if row[ofs] != 0x0 else 0.0
            elif 1 == bits_per_pixel:
                intensity = 1.0 if row[ofs] != 0x0 else 0.0

            if flag_multicolor:

                if not transparent:
                    if intensity >= 0.66: col = 2
                    elif intensity >= 33: col = 3
                    else: col = 1
                    accumulator += (1 << (6-bit))
                    if col > 1:
                        accumulator += (1 << (7-bit))

                bit += 2
            else:
                if intensity >= 0.5 and not transparent:
                    accumulator += (1 << (7-bit))
                bit += 1

            if 8 == bit:
                bit = 0
                buffer.append(accumulator)
                accumulator = 0

        if 0 != bit:
            bit = 0
            buffer.append(accumulator)
            accumulator = 0
            x += step_size

        while x+step_size<=max_steps:
            buffer.append(0)
            x += 8

        y += 1

    while y < 21:
        x = 0
        while x+step_size<=max_steps:
            buffer.append(0)
            x += step_size
        y += 1


    l = len(buffer)

    buffer.append(0x00)

    name = os.path.splitext(os.path.basename(input_file))[0]



    s = to_string(name, buffer, flag_multicolor, index)

    return s # , rect.width, rect.height, bit_rows

def get_bit_char(v):
    if v: return '1'
    return '0'

def format_bits(bits):
    return "0b" + get_bit_char(bits & 0x80) + get_bit_char(bits & 0x40) + get_bit_char(bits & 0x20) + get_bit_char(bits & 0x10) + get_bit_char(bits & 0x8) + get_bit_char(bits & 0x4) + get_bit_char(bits & 0x2) + get_bit_char(bits & 0x1)

def format_txt(txt, width):
    if len(txt) < width:
        txt += " " * (width - len(txt))
    return txt

def to_string(name, data, multicolor, index):

    lines = []

    appendix = f"_{index}" if index else ""

    lines.append("\n////////////////////////////////////////////////////////////////////////////////")
    if multicolor:
        lines.append(f"// Sprite '{name}' (multi-color)")
    else:
        lines.append(f"// Sprite '{name}' (hi-res / monochrome)")
    lines.append("////////////////////////////////////////////////////////////////////////////////")
    lines.append("{")

    y = 0
    element = 0
    line_count = 0
    s = ""
    for bits in data:

        if line_count == 0: s = "  "
        s += format_bits(bits)
        if element < len(data)-1: s += ", "

        element += 1
        line_count += 1

        if line_count >= 3 or element == len(data):
            lines.append(s)
            line_count = 0
            s = ""
        y += 1

    content = "\n".join(lines)
    content+= "\n"

    return content

def save(filename, content):
    lines = []
    lines.append("////////////////////////////////////////////////////////////////////////////////")
    lines.append("// Sprite data")
    lines.append("// @generated")
    lines.append("// clang-format off")
    lines.append("////////////////////////////////////////////////////////////////////////////////")
    lines.append("\n#include <cstdint>\n")
    lines.append("uint8_t __sprite_data[][64] __attribute__ ((section (\".sprites\"))) = {\n")
    header = "\n".join(lines)

    lines = []
    lines.append("\n};\n")
    footer = "\n".join(lines)

    with open(filename, "w") as text_file:
        text_file.write(header)
        text_file.write(content)
        text_file.write(footer)

def usage():
    print("Usage: bitmap2cpp [-m|--multicolor] -o output input...")
    print("")
    print("-m, --multicolor  : Enable multi-color mode")
    print("-o                : Filename of C++ source file to be generated")
    print("INPUT             : PNG input files")

def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hmo:", ["multi", "help", "output="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    output = None
    multi = False
    for o, a in opts:
        if o in ("-m", "--multi"):
            multi = True
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-o", "--output"):
            output = a

    s = ""
    file_index = 0
    for arg in args:
        s += process(arg, None, None, multi)
        file_index += 1
        if file_index < len(args):
            s += "},\n"
        else:
            s += "}\n"

    if output:
        save(output, s)
    else:
        print(s)

if __name__ == "__main__":
    main()
