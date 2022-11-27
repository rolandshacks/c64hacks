#
# sidc - Sid file data extractor
# (C) Roland Schabenberger
#

from atexit import register
from genericpath import isfile
import sys
import os
import os.path
import getopt
from pathlib import Path

VERBOSE = False

MAX_LINE_LENGTH = 120
HEXCHARS = "0123456789abcdef"

sid = None
sid_ofs = 0
sid_size = 0

def usage():
    print("Usage: sidc SIDFILE CPPFILE")
    print("")
    print("SIDFILE : C64 SID music file")
    print("CPPFILE : C++ output file")

def format_byte(value):
    return "0x" + HEXCHARS[int(value/16)] + HEXCHARS[int(value%16)]

def read_int(num_bytes):
    '''Read int from buffer'''
    global sid, sid_ofs, sid_size
    if sid_ofs + num_bytes >= sid_size: return -1
    value = int.from_bytes(sid[sid_ofs:sid_ofs+num_bytes], 'big')
    sid_ofs += num_bytes
    return value

def read_str(num_bytes):
    '''Read int from buffer'''
    global sid, sid_ofs, sid_size
    if sid_ofs + num_bytes >= sid_size: return -1
    value = ""
    for i in range(num_bytes):
        c = sid[sid_ofs+i]
        if c == 0: break
        value += chr(c)
    sid_ofs += num_bytes
    return value

def show(label, num_bytes, show_hex=True, show_dec=True):
    s = ""
    s += label
    s += ": "
    v = read_int(num_bytes)
    if show_hex: s += f" ${v:0{num_bytes*2}x}"
    if show_dec: s += (f" {v}")
    print(s)
    return v

def sidc(sid_file, output_file):
    '''Dump SID file information'''
    global sid, sid_ofs, sid_size

    sid = None
    sid_ofs = 0
    sid_size = 0

    buffer_size = 64*1024
    with open(sid_file, "rb") as in_file:
        sid = in_file.read(buffer_size)
    sid_size = len(sid)

    if sid_size < 126:
        print("invalid file size")
        return

    magic = chr(sid[0]) + chr(sid[1]) + chr(sid[2]) + chr(sid[3])
    magic_num = read_int(4)

    if magic != "PSID" and magic != "RSID":
        print(f"invalid file magic bytes: {magic}")
        return

    print(f"file: {sid_file}")
    print(f"size: {sid_size} bytes")
    print(f"magic: {magic} ${magic_num:08x}")

    version = show("version", 2, False, True)
    data_offset = show("data offset", 2, True, True)
    load_address = show("load address", 2, True, False)
    if load_address == 0x0:
        load_address = int.from_bytes(sid[data_offset:data_offset + 2], 'little')
        print(f"encoded load address: ${load_address:04x}")

    init_address = show("init address", 2, True, False)
    play_address = show("play address", 2, True, False)
    num_songs = show("songs", 2, False, True)
    start_song = show("start song", 2, False, True)
    speed = show("speed", 4, True, True)

    sid_name = read_str(32)
    print(f"name: {sid_name}")

    sid_author = read_str(32)
    print(f"author: {sid_author}")

    sid_released = read_str(32)
    print(f"released/copyright: {sid_released}")

    if version == 1: return

    flags = show("flags", 2, True, True)

    if flags & 0x1:
        print("- built-in music player")
    else:
        print("- Compute!'s Sidplayer MUS data")

    if flags & 0x2:
        print("- C64 compatible")
    else:
        print("- PlaySID specific (PSID v2NG, v3, v4) / C64 BASIC flag (RSID)")

    if flags & 0x4 and flags & 0x8:
        print("- PAL and NTSC")
    elif flags & 0x4:
        print("- PAL")
    elif flags & 0x8:
        print("- NTSC")
    else:
        print("- no video standard")

    if not output_file: return

    ###############################################

    out_file = open(output_file, "w")

    out_file.write("// *****************************************************************************\n")
    out_file.write("// SID file data\n")
    out_file.write("// Name: " + sid_name + "\n")
    out_file.write("// Author: " + sid_author + "\n")
    out_file.write("// (C) " + sid_released + "\n")
    out_file.write("// *****************************************************************************\n")
    out_file.write("\n")

    out_file.write("#include <cstdint>\n")

    out_file.write("\n")
    #out_file.write('extern const uint8_t sid_data[] __attribute__ ((section (".sid"))) = {\n')
    out_file.write('extern const uint8_t sid_data[] = {\n')

    sid_music_data_size = sid_size - (data_offset+2)

    line = "  "
    for ofs in range(data_offset+2, sid_size):
        b = sid[ofs]
        line += format_byte(b)
        if ofs < sid_size - 1: line += ","
        if ofs == sid_size - 1 or len(line) >= MAX_LINE_LENGTH:
            out_file.write(line)
            out_file.write("\n")
            line = "  "

    out_file.write("};\n")
    out_file.write("\n")
    out_file.write("struct sid_info_t {\n")
    out_file.write("  const uint16_t load_address;\n")
    out_file.write("  const uint16_t init_address;\n")
    out_file.write("  const uint16_t play_address;\n")
    out_file.write("  const uint16_t num_songs;\n")
    out_file.write("  const uint16_t start_song;\n")
    out_file.write("  const uint32_t speed;\n")
    out_file.write("  const uint16_t size;\n")
    out_file.write("  const uint8_t* data;\n")
    out_file.write("};\n")
    out_file.write("\n")

    out_file.write("extern const sid_info_t sid_info {\n")
    out_file.write(f"  0x{load_address:04x},                       // load address\n")
    out_file.write(f"  0x{init_address:04x},                       // init address\n")
    out_file.write(f"  0x{play_address:04x},                       // play address\n")
    out_file.write(f"  0x{num_songs:04x},                       // song count\n")
    out_file.write(f"  0x{start_song:04x},                       // start song\n")
    out_file.write(f"  0x{speed:08x},                   // speed\n")
    out_file.write(f"  0x{sid_music_data_size:04x},                       // size\n")
    out_file.write(f"  (const uint8_t*) sid_data     // data\n")
    out_file.write("};\n")

    out_file.close()

    return

def main():
    '''Main entry'''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:", ["help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if len(args) < 1:
        usage()
        sys.exit()

    output = "build"
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

    source = Path(args[0])
    if not source.exists or not os.path.isfile(source):
        print(f"{source} does not exist or is invalid")
        sys.exit(3)

    dest = None
    if len(args) >= 2 : dest = Path(args[1])

    sidc(source, dest)

if __name__ == "__main__":
    main()
