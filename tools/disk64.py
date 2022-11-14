#
# disk64 - C64/D64 Disk Utility
# (C) Roland Schabenberger
#

import sys
import os
import os.path
import getopt
from pathlib import Path

VERBOSE = False
MAX_LINE_LENGTH = 120
HEXCHARS = "0123456789abcdef"

def usage():
    print("Usage: disk64 [-l|--list] [-e|--export] DISK.D64 [FILENAME]")
    print("")
    print("DISK.D64          : C64 disk file")
    print("-l, --list        : List directory")
    print("-e, --export      : Export file from disk")

def get_sectors_of_track(track_number):
    if track_number < 17:
        return 21
    elif track_number < 24:
        return 19
    elif track_number < 30:
        return 18
    else:
        return 17


def get_track_offset(track_number):
    if track_number < 17:
        return track_number * 21 * 256
    elif track_number < 24:
        return 0x16500 + (track_number - 17) * 19 * 256
    elif track_number < 30:
        return 0x1EA00 + (track_number - 24) * 18 * 256
    else:
        return 0x25600 + (track_number - 30) * 17 * 256


def get_track_size(track_number):
    return get_sectors_of_track(track_number) * 256


def get_track(disk, track_number):
    ofs = get_track_offset(track_number)
    sz = get_track_size(track_number)
    track = disk[ofs:ofs+sz]
    return track

def petscii_to_ascii(c):
    if 48 <= c <= 57:
        return ord('0') + c - 48
    if 65 <= c <= 90:
        return ord('A') + c - 65
    return c

def get(data, pos):
    sz = len(data)
    if pos >= sz:
        return 0
    return data[pos]

def bit_count(b):
    num_bits = 0
    if b & 0x1:
        num_bits += 1
    if b & 0x2:
        num_bits += 1
    if b & 0x4:
        num_bits += 1
    if b & 0x8:
        num_bits += 1
    if b & 0x10:
        num_bits += 1
    if b & 0x20:
        num_bits += 1
    if b & 0x40:
        num_bits += 1
    if b & 0x80:
        num_bits += 1
    return num_bits

def wildcard_compare(pattern, s):
    w = pattern.find('*')
    if w != -1:
        if (s.startswith(pattern[0:w])):
            return True

    elif pattern == s:
        return True

    return False

class FileType:
    Unknown = -1
    Del = 0
    Seq = 1
    Prg = 2
    Usr = 3
    Rel = 4

class DirectoryEntry:
    def __init__(
        self,
        name,
        num_blocks,
        file_type,
        track_pos,
        sector_pos,
        rel_file_track_first_block,
        rel_file_sector_first_block,
        rel_file_record_len
    ) -> None:
        self.name = name
        self.num_blocks = num_blocks
        self.file_type = file_type
        self.track_pos = track_pos
        self.sector_pos = sector_pos
        self.rel_file_track_first_block = rel_file_track_first_block
        self.rel_file_sector_first_block = rel_file_sector_first_block
        self.rel_file_record_len = rel_file_record_len

    def get_type_name(self):
        type_name = ""
        if self.file_type == FileType.Del:
            type_name = "DEL"
        elif self.file_type == FileType.Seq:
            type_name = "SEQ"
        elif self.file_type == FileType.Prg:
            type_name = "PRG"
        elif self.file_type == FileType.Usr:
            type_name = "USR"
        elif self.file_type == FileType.Rel:
            type_name = "REL"

        return type_name

class Disk:
    def __init__(self, filename):
        self.filename = None
        self.disk = None
        self.disk_format = None
        self.disk_double_sided_flag = None
        self.free_blocks = 0
        self.disk_name = None
        self.dos_version = None
        self.disk_id = None
        self.directory = []

        self.open(filename)
        self.read_directory()

    def open(self, filename):

        if not filename.exists or not os.path.isfile(filename):
            print(f"failed to open {filename}")
            sys.exit(1)

        # standard .64 is 174848 bytes
        self.disk = None
        with open(filename, "rb") as in_file:
            self.disk = in_file.read()

        self.filename = filename

    def decode_name(self, ofs, max_len):
        name = ""
        for i in range(0, max_len):
            b = self.disk[ofs]
            if b == 160 or b == 0x0:
                break
            c = chr(petscii_to_ascii(b))
            ofs += 1
            name += c
        return name

    def read_directory(self):

        disk = self.disk
        disk_size = len(disk)

        # listing starts at track 17, sector 1. sector 17/0 is BAM
        track = 17

        track_ofs = get_track_offset(track)
        ofs = track_ofs

        # BAM

        # $00
        dir_track = disk[ofs]-1
        ofs += 1

        # $01
        dir_sector = disk[ofs]
        ofs += 1

        # $02
        # should be "A" for 1541/1570/1571
        self.disk_format = chr(petscii_to_ascii(disk[ofs]))
        ofs += 1

        # $03
        self.disk_double_sided_flag = disk[ofs]  # $00 for 1541
        ofs += 1

        # $04, 140 bytes
        # bit map of available blocks in tracks 1 - 35
        # 1 = available block, 0 = not available

        self.free_blocks = 0

        ofs_end = ofs + 0x8c  # 140 bytes

        track_number = 0
        while ofs < ofs_end:
            track_number += 1
            # track sector usage info
            # NUM_FREE USAGEMAP0 USAGEMAP1 USAGEMAP2 (1:free, 0:used)
            track_free_sectors = disk[ofs]
            #track_bitmap = bit_count(disk[ofs+1]) + bit_count(disk[ofs+2]) + bit_count(disk[ofs+3])
            if track_number != 18:
                self.free_blocks += track_free_sectors
            ofs += 4

        # Directory Header
        # $90
        self.disk_name = self.decode_name(ofs, 16)
        ofs += 16

        # $A0
        ofs += 2  # unused, shifted spaces ($A0)

        # $A2/$A3
        self.disk_id = chr(petscii_to_ascii(
            disk[ofs])) + chr(petscii_to_ascii(disk[ofs+1]))
        ofs += 2

        # $A4
        ofs += 1  # unused

        # $A5
        self.dos_version = chr(petscii_to_ascii(
            disk[ofs]))  # '2' = CBM DOS V2.6
        ofs += 1

        # skip the rest, extended formats not supported, yet

        track = dir_track
        sector = dir_sector

        while True:
            track_ofs = get_track_offset(track)
            sector_ofs = track_ofs + sector * 256

            entry_ofs = 0

            for entry in range(0, 7):

                ofs = sector_ofs + entry * 0x20

                if entry == 0:
                    next_track = disk[ofs]
                    next_sector = disk[ofs+1]
                ofs += 2

                file_flags = disk[ofs]
                ofs += 1

                file_type = file_flags & 0x07

                track_pos = disk[ofs]
                ofs += 1

                sector_pos = disk[ofs]
                ofs += 1

                name = self.decode_name(ofs, 16)
                ofs += 16

                rel_file_track_first_block = disk[ofs]
                ofs += 1

                rel_file_sector_first_block = disk[ofs]
                ofs += 1

                rel_file_record_len = disk[ofs]
                ofs += 1

                ofs += 6  # ignored (unless GEOS)

                num_blocks = disk[ofs] + disk[ofs+1] * 256
                ofs += 2

                if len(name) > 0:
                    directory_entry = DirectoryEntry(
                        name,
                        num_blocks,
                        file_type,
                        track_pos,
                        sector_pos,
                        rel_file_track_first_block,
                        rel_file_sector_first_block,
                        rel_file_record_len)

                    self.directory.append(directory_entry)

            if next_track == 0 or next_sector == 0:
                break

            track = next_track
            sector = next_sector

    def list(self, pattern=None):
        disk_name_s = f"{self.disk_name:16}"
        print(f"{self.disk_double_sided_flag} \"{disk_name_s}\" {self.disk_id} {self.dos_version}{self.disk_format}")

        for entry in self.directory:
            if pattern != None and not wildcard_compare(pattern, entry.name):
                continue
            name_s = f"\"{entry.name}\""
            print(f"{entry.num_blocks:<4} {name_s:18} {entry.get_type_name()}")

        print(f"{self.free_blocks} blocks free")

    def find_files(self, pattern):
        result = []
        for entry in self.directory:
            if (wildcard_compare(pattern, entry.name)):
                result.append(entry)
        return result

    def find_file(self, filename):
        result = self.find_files(filename)
        if len(result) == 1:
            return result[0]
        return None

    def read_sector(self, track, sector):
        print(f"read sector: {track}:{sector}")
        ofs = get_track_offset(track) + sector * 256
        sector = self.disk[ofs:ofs+256]
        return sector

    def read_file(self, dir_entry):
        disk = self.disk
        data = bytearray()
        next_track = dir_entry.track_pos
        next_sector = dir_entry.sector_pos

        while True:
            sector_ofs = get_track_offset(next_track-1) + next_sector * 256

            next_track = disk[sector_ofs+0]     # next track
            next_sector = disk[sector_ofs+1]    # next sector

            bytes_to_read = 254
            if next_track == 0:
                bytes_to_read = next_sector - 1

            ofs = sector_ofs + 2

            while bytes_to_read > 0:
                data.append(disk[ofs])
                ofs += 1
                bytes_to_read -= 1

            if next_track == 0:
                break

        return data

def show_dir(disk_filename, pattern=None):
    disk = Disk(disk_filename)
    disk.list()

def export(disk_filename, filename):
    disk = Disk(disk_filename)
    dir_entry = disk.find_file(str(filename))
    if not dir_entry:
        dir_entry = disk.find_file(str(filename)+"*")
    if not dir_entry:
        print(f"file not found: {filename}")
        return

    file_data = disk.read_file(dir_entry)

    with open("export.prg", "wb") as out_file:
        out_file.write(file_data)

def main():
    '''Main entry'''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:le", [
                                   "help", "list", "export"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if len(args) < 1:
        usage()
        sys.exit()

    opt_show_dir = False
    opt_export = False

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-l", "--list"):
            opt_show_dir = True
        elif o in ("-e", "--export"):
            opt_export = True

    disk_filename = Path(args[0])
    if not disk_filename.exists or not os.path.isfile(disk_filename):
        print(f"{disk_filename} does not exist or is invalid")
        sys.exit(1)

    if opt_show_dir:
        show_dir(disk_filename)
    elif opt_export:
        filename = args[1]
        export(disk_filename, filename)

if __name__ == "__main__":
    main()
