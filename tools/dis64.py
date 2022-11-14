#
# dis64 - Disassembler for MOS 6502/6510
# (C) Roland Schabenberger
#

import sys
import os
import os.path
import getopt
import time
from pathlib import Path

VERBOSE = False

MAX_LINE_LENGTH = 120
HEXCHARS = "0123456789abcdef"

PROFILE_GNU = 0
PROFILE_ACME = 1

PROFILE = PROFILE_GNU

class FileType:
    Unknown = -1
    Del = 0
    Seq = 1
    Prg = 2
    Usr = 3
    Rel = 4

class AddressMode:
    imm = 0  # Immediate - imm
    abs = 1  # Absolute - abs
    zp = 2  # Zero Page - zp
    imp = 3  # Implied
    ind = 4  # Indirect Absolute - ind
    abx = 5  # Absolute indexed with X - abx / abs.x
    aby = 6  # Absolute indexed with Y - aby / abs.y
    zpx = 7  # Zero page indexed with X - zpx / zp.x
    zpy = 8  # Zero page indexed with Y - zpy / zp.y
    izx = 9  # Indexed indirect (with x) - izx / (zp.x)
    izy = 10 # Indirect indexed (with y) - izy / (zp).y
    rel = 11 # Relative - rel
    acc = 12 # Accumulator

InstructionNames = [
    "ADC","AND","ASL","BCC","BCS","BEQ","BIT","BMI","BNE","BPL",
    "BRK","BVC","BVS","CLC","CLD","CLI","CLV","CMP","CPX","CPY",
    "DEC","DEX","DEY","EOR","INC","INX","INY","JMP","JSR","LDA",
    "LDX","LDY","LSR","NOP","ORA","PHA","PHP","PLA","PLP","ROL",
    "ROR","RTI","RTS","SBC","SEC","SED","SEI","STA","STX","STY",
    "TAX","TAY","TSX","TXA","TXS","TYA",

    # from illegal opcodes

    "SLA", "RLA", "ISC", "SRE", "SAX", "RRA", "LAX", "DCP", "ANC",
    "ALR", "ARR", "SBX", "SBC", "LAS", "JAM", "SHA", "SHX", "XAA",
    "SHY", "TAS"

]

JumpInstructions = [
    3, 4, 5, 7, 8, 9, 11, 12, 27, 28
]

OpcodeTable = [
    # num,name,addressing,cycles,cross_page
    (0x69,0,AddressMode.imm,2,1), # ADC
    (0x65,0,AddressMode.zp,3,1),
    (0x75,0,AddressMode.zpx,4,1),
    (0x6D,0,AddressMode.abs,4,1),
    (0x7D,0,AddressMode.abx,4,1),
    (0x79,0,AddressMode.aby,4,1),
    (0x61,0,AddressMode.izx,6,1),
    (0x71,0,AddressMode.izy,5,1),

    (0x29,1,AddressMode.imm,2,1), # AND
    (0x25,1,AddressMode.zp,3,1),
    (0x35,1,AddressMode.zpx,4,1),
    (0x2D,1,AddressMode.abs,4,1),
    (0x3D,1,AddressMode.abx,4,1),
    (0x39,1,AddressMode.aby,4,1),
    (0x21,1,AddressMode.izx,6,1),
    (0x31,1,AddressMode.izy,5,1),

    (0x0A,2,AddressMode.acc,2,0), # ASL
    (0x06,2,AddressMode.zp,5,0),
    (0x16,2,AddressMode.zpx,6,0),
    (0x0E,2,AddressMode.abs,6,0),
    (0x1E,2,AddressMode.abx,6,0),

    (0x90,3,AddressMode.rel,4,1), # BCC

    (0xB0,4,AddressMode.rel,4,1), # BCS

    (0xF0,5,AddressMode.rel,4,1), # BEQ

    (0x24,6,AddressMode.zp,3,0), # BIT
    (0x2C,6,AddressMode.abs,4,0),

    (0x30,7,AddressMode.rel,4,1), # BMI

    (0xD0,8,AddressMode.rel,4,1), # BNE

    (0x10,9,AddressMode.rel,4,1), # BPL

    (0x00,10,AddressMode.imp,7,0), # BRK

    (0x50,11,AddressMode.rel,4,1), # BVC

    (0x70,12,AddressMode.rel,4,1), # BVS

    (0x18,13,AddressMode.imp,2,0), # CLC

    (0xD8,14,AddressMode.imp,2,0), # CLD

    (0x58,15,AddressMode.imp,2,0), # CLI

    (0xB8,16,AddressMode.imp,2,0), # CLV

    (0xC9,17,AddressMode.imm,2,0), # CMP
    (0xC5,17,AddressMode.zp,3,0),
    (0xD5,17,AddressMode.zpx,4,0),
    (0xCD,17,AddressMode.abs,4,0),
    (0xDD,17,AddressMode.abx,4,0),
    (0xD9,17,AddressMode.aby,4,0),
    (0xC1,17,AddressMode.izx,6,0),
    (0xD1,17,AddressMode.izy,5,0),

    (0xE0,18,AddressMode.imm,2,0), # CPX
    (0xE4,18,AddressMode.zp,3,0),
    (0xEC,18,AddressMode.abs,4,0),

    (0xC0,19,AddressMode.imm,2,0), # CPY
    (0xC4,19,AddressMode.zp,3,0),
    (0xCC,19,AddressMode.abs,4,0),

    (0xC6,20,AddressMode.zp,5,0), # DEC
    (0xD6,20,AddressMode.zpx,6,0),
    (0xCE,20,AddressMode.abs,6,0),
    (0xDE,20,AddressMode.abx,6,0),

    (0xCA,21,AddressMode.imp,2,0), # DEX

    (0x88,22,AddressMode.imp,2,0), # DEY

    (0x49,23,AddressMode.imm,2,1), # EOR
    (0x45,23,AddressMode.zp,3,1),
    (0x55,23,AddressMode.zpx,4,1),
    (0x4D,23,AddressMode.abs,4,1),
    (0x5D,23,AddressMode.abx,4,1),
    (0x59,23,AddressMode.aby,4,1),
    (0x41,23,AddressMode.izx,6,1),
    (0x51,23,AddressMode.izy,5,1),

    (0xE6,24,AddressMode.zp,5,0), # INC
    (0xF6,24,AddressMode.zpx,6,0),
    (0xEE,24,AddressMode.abs,6,0),
    (0xFE,24,AddressMode.abx,6,0),

    (0xE8,25,AddressMode.imp,2,0), # INX

    (0xC8,26,AddressMode.imp,2,0), # INY

    (0x4C,27,AddressMode.abs,3,0), # JMP
    (0x6C,27,AddressMode.ind,5,0),

    (0x20,28,AddressMode.abs,6,0), # JSR

    (0xA9,29,AddressMode.imm,2,1), # LDA
    (0xA5,29,AddressMode.zp,3,1),
    (0xB5,29,AddressMode.zpx,4,1),
    (0xAD,29,AddressMode.abs,4,1),
    (0xBD,29,AddressMode.abx,4,1),
    (0xB9,29,AddressMode.aby,4,1),
    (0xA1,29,AddressMode.izx,6,1),
    (0xB1,29,AddressMode.izy,5,1),

    (0xA2,30,AddressMode.imm,2,1), # LDX
    (0xA6,30,AddressMode.zp,3,1),
    (0xB6,30,AddressMode.zpy,4,1),
    (0xAE,30,AddressMode.abs,4,1),
    (0xBE,30,AddressMode.aby,4,1),

    (0xA0,31,AddressMode.imm,2,1), # LDY
    (0xA4,31,AddressMode.zp,3,1),
    (0xB4,31,AddressMode.zpx,4,1),
    (0xAC,31,AddressMode.abs,4,1),
    (0xBC,31,AddressMode.abx,4,1),

    (0x4A,32,AddressMode.acc,2,0), # LSR
    (0x46,32,AddressMode.zp,5,0),
    (0x56,32,AddressMode.zpx,6,0),
    (0x4E,32,AddressMode.abs,6,0),
    (0x5E,32,AddressMode.abx,6,0),

    (0xEA,33,AddressMode.imp,2,0), # NOP

    (0x09,34,AddressMode.imm,2,0), # ORA
    (0x05,34,AddressMode.zp,3,0),
    (0x15,34,AddressMode.zpx,4,0),
    (0x0D,34,AddressMode.abs,4,0),
    (0x1D,34,AddressMode.abx,4,0),
    (0x19,34,AddressMode.aby,4,0),
    (0x01,34,AddressMode.izx,6,0),
    (0x11,34,AddressMode.izy,5,0),

    (0x48,35,AddressMode.imp,3,0), # PHA

    (0x08,36,AddressMode.imp,3,0), # PHP

    (0x68,37,AddressMode.imp,4,0), # PLA

    (0x28,38,AddressMode.imp,4,0), # PLP

    (0x2A,39,AddressMode.acc,2,0), # ROL
    (0x26,39,AddressMode.zp,5,0),
    (0x36,39,AddressMode.zpx,6,0),
    (0x2E,39,AddressMode.abs,6,0),
    (0x3E,39,AddressMode.abx,6,0),

    (0x6A,40,AddressMode.acc,2,0), # ROR
    (0x66,40,AddressMode.zp,5,0),
    (0x76,40,AddressMode.zpx,6,0),
    (0x6E,40,AddressMode.abs,6,0),
    (0x7E,40,AddressMode.abx,6,0),

    (0x40,41,AddressMode.imp,6,0), # RTI

    (0x60,42,AddressMode.imp,6,0), # RTS

    (0xE9,43,AddressMode.imm,2,1), # SBC
    (0xE5,43,AddressMode.zp,3,1),
    (0xF5,43,AddressMode.zpx,4,1),
    (0xED,43,AddressMode.abs,4,1),
    (0xFD,43,AddressMode.abx,4,1),
    (0xF9,43,AddressMode.aby,4,1),
    (0xE1,43,AddressMode.izx,6,1),
    (0xF1,43,AddressMode.izy,5,1),

    (0x38,44,AddressMode.imp,2,0), # SEC

    (0xF8,45,AddressMode.imp,2,0), # SED

    (0x78,46,AddressMode.imp,2,0), # SEI

    (0x85,47,AddressMode.zp,3,0), # STA
    (0x95,47,AddressMode.zpx,4,0),
    (0x8D,47,AddressMode.abs,4,0),
    (0x9D,47,AddressMode.abx,4,0),
    (0x99,47,AddressMode.aby,4,0),
    (0x81,47,AddressMode.izx,6,0),
    (0x91,47,AddressMode.izy,5,0),

    (0x86,48,AddressMode.zp,3,0), # STX
    (0x96,48,AddressMode.zpy,4,0),
    (0x8E,48,AddressMode.abs,4,0),

    (0x84,49,AddressMode.zp,3,0), # STY
    (0x94,49,AddressMode.zpx,4,0),
    (0x8C,49,AddressMode.abs,4,0),

    (0xAA,50,AddressMode.imp,2,0), # TAX

    (0xA8,51,AddressMode.imp,2,0), # TAY

    (0xBA,52,AddressMode.imp,2,0), # TSX

    (0x8A,53,AddressMode.imp,2,0), # TXA

    (0x9A,54,AddressMode.imp,2,0), # TXS

    (0x98,55,AddressMode.imp,2,0), # TYA

    # ILLEGAL OPCODES

    (0x07,56,AddressMode.zp,5,0), # SLO
    (0x17,56,AddressMode.zpx,6,0),
    (0x03,56,AddressMode.izx,8,0),
    (0x13,56,AddressMode.izy,8,0),
    (0x0F,56,AddressMode.abs,6,0),
    (0x1F,56,AddressMode.abx,7,0),
    (0x1B,56,AddressMode.aby,7,0),

    (0x27,57,AddressMode.zp,5,0), # RLA
    (0x37,57,AddressMode.zpx,6,0),
    (0x23,57,AddressMode.izx,8,0),
    (0x33,57,AddressMode.izy,8,0),
    (0x2F,57,AddressMode.abs,6,0),
    (0x3F,57,AddressMode.abx,7,0),
    (0x3B,57,AddressMode.aby,7,0),

    (0xE7,58,AddressMode.zp,5,0), # ISC
    (0xF7,58,AddressMode.zpx,6,0),
    (0xE3,58,AddressMode.izx,8,0),
    (0xF3,58,AddressMode.izy,8,0),
    (0xEF,58,AddressMode.abs,6,0),
    (0xFF,58,AddressMode.abx,7,0),
    (0xFB,58,AddressMode.aby,7,0),

    (0x47,59,AddressMode.zp,5,0), # SRE
    (0x57,59,AddressMode.zpx,6,0),
    (0x43,59,AddressMode.izx,8,0),
    (0x53,59,AddressMode.izy,8,0),
    (0x4F,59,AddressMode.abs,6,0),
    (0x5F,59,AddressMode.abx,7,0),
    (0x5B,59,AddressMode.aby,7,0),

    (0x87,60,AddressMode.zp,3,0), # SAX
    (0x97,60,AddressMode.zpy,4,0),
    (0x83,60,AddressMode.izx,6,0),
    (0x8F,60,AddressMode.abs,4,0),

    (0x67,61,AddressMode.zp,5,0), # RRA
    (0x77,61,AddressMode.zpx,6,0),
    (0x63,61,AddressMode.izx,8,0),
    (0x73,61,AddressMode.izy,8,0),
    (0x6F,61,AddressMode.abs,6,0),
    (0x7F,61,AddressMode.abx,7,0),
    (0x7B,61,AddressMode.aby,7,0),

    (0xA7,62,AddressMode.zp,3,0), # LAX
    (0xB7,62,AddressMode.zpy,4,0),
    (0xA3,62,AddressMode.izx,6,0),
    (0xB3,62,AddressMode.izy,5,0),
    (0xAF,62,AddressMode.abs,4,0),
    (0xBF,62,AddressMode.aby,4,0),
    (0xAB,62,AddressMode.imm,2,0),

    (0xC7,63,AddressMode.zp,5,0), # DCP
    (0xD7,63,AddressMode.zpx,6,0),
    (0xC3,63,AddressMode.izx,8,0),
    (0xD3,63,AddressMode.izy,8,0),
    (0xCF,63,AddressMode.abs,6,0),
    (0xDF,63,AddressMode.abx,7,0),
    (0xDB,63,AddressMode.aby,7,0),

    (0x0B,64,AddressMode.imm,2,0), # ANC
    (0x2B,64,AddressMode.imm,2,0),

    (0x4B,65,AddressMode.imm,2,0), # ALR

    (0x6B,66,AddressMode.imm,2,0), # ARR

    (0xCB,67,AddressMode.imm,2,0), # SBX

    (0xEB,68,AddressMode.imm,2,0), # SBC

    (0xBB,69,AddressMode.aby,3,0), # LAS

    (0x1A,33,AddressMode.imp,2,0), # NOP
    (0x3A,33,AddressMode.imp,2,0),
    (0x5A,33,AddressMode.imp,2,0),
    (0x7A,33,AddressMode.imp,2,0),
    (0xDA,33,AddressMode.imp,2,0),
    (0xFA,33,AddressMode.imp,2,0),
    (0x80,33,AddressMode.imm,2,0),
    (0x82,33,AddressMode.imm,2,0),
    (0xC2,33,AddressMode.imm,2,0),
    (0xE2,33,AddressMode.imm,2,0),
    (0x89,33,AddressMode.imm,2,0),
    (0x04,33,AddressMode.zp,3,0),
    (0x44,33,AddressMode.zp,3,0),
    (0x64,33,AddressMode.zp,3,0),

    (0x14,33,AddressMode.zpx,4,0),
    (0x34,33,AddressMode.zpx,4,0),
    (0x54,33,AddressMode.zpx,4,0),
    (0x74,33,AddressMode.zpx,4,0),
    (0xD4,33,AddressMode.zpx,4,0),
    (0xF4,33,AddressMode.zpx,4,0),

    (0x0C,33,AddressMode.abs,4,0),

    (0x1C,33,AddressMode.abx,4,0),
    (0x3C,33,AddressMode.abx,4,0),
    (0x5C,33,AddressMode.abx,4,0),
    (0x7C,33,AddressMode.abx,4,0),
    (0xDC,33,AddressMode.abx,4,0),
    (0xFC,33,AddressMode.abx,4,0),

    (0x02,69,AddressMode.imp,1,0), # JAM
    (0x12,69,AddressMode.imp,1,0),
    (0x22,69,AddressMode.imp,1,0),
    (0x32,69,AddressMode.imp,1,0),
    (0x42,69,AddressMode.imp,1,0),
    (0x52,69,AddressMode.imp,1,0),
    (0x62,69,AddressMode.imp,1,0),
    (0x72,69,AddressMode.imp,1,0),
    (0x92,69,AddressMode.imp,1,0),
    (0xB2,69,AddressMode.imp,1,0),
    (0xD2,69,AddressMode.imp,1,0),
    (0xF2,69,AddressMode.imp,1,0),

    (0x93,70,AddressMode.zpy,1,0), # SHA
    (0x9F,70,AddressMode.aby,1,0),

    (0x9E,71,AddressMode.aby,1,0), # SHX

    (0x8B,72,AddressMode.imm,2,0), # XAA

    (0x9C,73,AddressMode.aby,1,0), # SHY

    (0x9B,74,AddressMode.aby,1,0), # TAS
]

OpcodeMap = None

def usage():
    print("Usage: dis64 [-m] INFILE [OUTFILE]")
    print("")
    print("INFILE            : Binary input file")
    print("OUTFILE           : Write output to file")
    print("-b, --binary      : Add hexdump of machine code")
    print("-c, --nocomments  : Add hexdump of machine code")
    print("-m, --monitor     : Run in continuous monitoring mode")

def format_byte(value):
    return "0x" + HEXCHARS[int(value/16)] + HEXCHARS[int(value%16)]

def petscii_to_ascii(c) :
    if 48 <= c <= 57: return ord('0') + c - 48
    if 65 <= c <= 90: return ord('A') + c - 65
    return c

def write(f, txt):
    if f :
        f.write(f"{txt.rstrip()}\n")
    else:
        print(txt.rstrip())

def get_label_name(statement):

    if statement.irq_handler:
        return f"irq{statement.index}"
    else:
        return f"label{statement.index}"

class Options:
    def __init__(self):
        self.show_binary = True
        self.show_comments = True

class Statement:
    def __init__(self, addr, opcode, instruction, data, data2, address_mode, cycles, cross_page, buffer):
        self.addr = addr
        self.opcode = opcode
        self.instruction = instruction
        self.data = data
        self.data2 = data2
        self.address_mode = address_mode
        self.cycles = cycles
        self.cross_page = cross_page
        self.refs = []
        self.index = None
        self.jump_target = None
        self.buffer = buffer
        self.comment = None
        self.jump_address = None
        self.irq_handler = None

    def has_refs(self):
        return len(self.refs) > 0

    def set_comment(self, comment):
        self.comment = comment

    def add_jump_target(self, jump_target):
        self.jump_target = jump_target

    def get_jump_addr(self):
        if self.jump_address: return self.jump_address
        if self.data2 != None:
            return (self.data2<<8) + self.data
        elif self.data != None:
            rel_addr = self.data
            if rel_addr >= 128: rel_addr -= 256 # signed 8bit
            return self.addr + rel_addr + 2
        else:
            return 0x0

    def add_ref(self, ref):
        self.refs.append(ref)

    def is_jump(self):
        return self.instruction in JumpInstructions

    def is_return(self):
        return self.instruction == 41 or self.instruction == 42 # RTS or RTI

    def to_string(self, options):
        if self.opcode == 0x0: return self.to_string_buffer(options)
        elif self.instruction != None: return self.to_string_valid(options)
        else: return self.to_string_invalid(options)

    def to_string_invalid(self, options):
        line_s = f"    ???                   "
        if options.show_binary:
            bin = f"; ${self.addr:04X}  {self.opcode:02x}"
            line_s += f"{bin:16}"
        if options.show_comments and self.comment != None:
            if options.show_binary: line_s += "  "
            line_s += f"; {self.comment}"
        return line_s

    def to_string_buffer(self, options):

        buffer_name = f"buffer{self.index}"

        label_s = f".{buffer_name} !byte"
        s = ""
        i = 0
        txt = ""
        while i < len(self.buffer):
            b = self.buffer[i]
            i += 1

            if len(s) > 0: s += " "
            s += f"${b:02x}"

            if len(s) >= 58 or i == len(self.buffer):
                if len(txt) > 0: txt += "\n"
                txt += f"{label_s} " + s
                label_s = "              "
                s = ""

        return txt

    def to_string_valid(self, options):
        addr_s = f"${self.addr:04X}"

        opcode_s = InstructionNames[self.instruction].lower()

        data_s = None
        val = None
        if self.data != None and self.data2 != None:
            val = (self.data2<<8) + self.data
            data_s = f"${val:04x}"
        elif self.data != None:
            data_s = f"${self.data:02x}"

        prefix = ""
        suffix = ""
        if self.address_mode == AddressMode.imm: prefix = "#"
        if self.address_mode == AddressMode.abx or self.address_mode == AddressMode.zpx: suffix = ",X"
        if self.address_mode == AddressMode.aby or self.address_mode == AddressMode.zpy: suffix = ",Y"
        if self.address_mode == AddressMode.izx:
            prefix = "("
            suffix = ",X)"
        if self.address_mode == AddressMode.izy:
            prefix = "("
            suffix = "),Y"

        hex_s = f"{self.opcode:02X}"
        if self.data2 != None: hex_s += f" {self.data:02X}{self.data2:02X}"
        elif self.data != None: hex_s += f" {self.data:02X}"

        statement_s = None
        if self.is_jump() and self.jump_target:
            statement_s = opcode_s + f" {get_label_name(self.jump_target)}"
        else:
            statement_s = opcode_s + (f" {prefix}{data_s}{suffix}" if data_s else "")

        line_s = f"    {statement_s:22}"
        if options.show_binary:
            line_s += f"; {addr_s}  {hex_s:7}"
        if options.show_comments and self.comment != None:
            if options.show_binary: line_s += "  "
            line_s += f"; {self.comment}"

        return line_s

def process_invalid_statement(addr, opcode):
    statement = Statement(addr, opcode, None, None, None, None, None, None, None)
    statement.set_comment("unknown opcode")
    return statement

def process_statement(addr, opcode, instruction, data, data2, address_mode, cycles, cross_page):
    statement = Statement(addr, opcode, instruction, data, data2, address_mode, cycles, cross_page, None)
    return statement

def process_buffer(addr, buffer):
    statement = Statement(addr, 0x0, None, None, None, None, None, None, buffer)
    return statement

def find_addr(statements, addr):
    for statement in statements:
        if statement.addr == addr:
            return statement

    return None

def get(data, pos):
    sz = len(data)
    if pos >= sz: return 0
    return data[pos]

def get_sectors_of_track(track_number):
    if track_number < 17: return 21
    elif track_number < 24: return 19
    elif track_number < 30: return 18
    else: return 17

def get_track_offset(track_number):
    if track_number < 17: return track_number * 21 * 256
    elif track_number < 24: return 0x16500 + (track_number - 17) * 19 * 256
    elif track_number < 30: return 0x1EA00 + (track_number - 24) * 18 * 256
    else: return 0x25600 + (track_number - 30) * 17 * 256

def get_track_size(track_number):
    return get_sectors_of_track(track_number) * 256

def get_track(disk, track_number):
    ofs = get_track_offset(track_number)
    sz = get_track_size(track_number)
    track = disk[ofs:ofs+sz]
    return track

def readInput(url):

    if not url.exists or not os.path.isfile(url):
        print(f"{url} does not exist or is invalid")
        sys.exit(1)

    binary = None
    buffer_size = 256*1024 # 256 KiB should be fine for whatever input

    with open(url, "rb") as in_file:
        binary = in_file.read(buffer_size)
    return binary

def process(input_file, output_file, options):
    '''Convert C64 program file to assembler'''

    fileType = FileType.Unknown

    ext = Path(input_file).suffix.lower()
    if ext == ".prg":
        fileType = FileType.Prg
    else:
        print(f"unsupported file format: {ext}")
        return

    OpcodeMap = {}
    for opcode_info in OpcodeTable:
        opcode = opcode_info[0]
        OpcodeMap[opcode] = opcode_info

    binary = readInput(input_file)
    if binary == None:
        print("failed to read input file")
        return

    binary_size = len(binary)
    if binary_size < 2:
        print("invalid file size")
        return

    ofs = 0

    out_file = None
    if output_file: out_file = open(output_file, "w")

    write(out_file, "; #############################################################################")
    write(out_file, "; #")
    write(out_file, "; # GENERATED BY DIS64")
    write(out_file, "; # " + str(input_file))
    write(out_file, "; #")
    write(out_file, "; #############################################################################")
    write(out_file, "")

    load_address = int.from_bytes(binary[ofs:ofs+2], 'little')
    ofs += 2
    out_s = f"*=${load_address:04X}"
    if options.show_comments: out_s += f" ; load address ({load_address})"
    write(out_file, out_s)

    basic_line_ptr = int.from_bytes(binary[ofs:ofs+2], 'little')
    ofs += 2

    basic_line_num = int.from_bytes(binary[ofs:ofs+2], 'little')
    ofs += 2

    while ofs < binary_size:
        dummy_byte = int.from_bytes(binary[ofs:ofs+1], 'little')
        if dummy_byte == 0x9e: break
        ofs += 1

    sys_command = int.from_bytes(binary[ofs:ofs+1], 'little')
    if sys_command != 0x9e:
        print(f"unexpected basic SYS command ${sys_command:02x}")
        return

    ofs += 1

    basic_statement = ""
    while ofs < binary_size:
        b = binary[ofs]
        ofs += 1
        if b == 0x0:
            break
        basic_statement += chr(petscii_to_ascii(b))

    basic_next_line_ptr = int.from_bytes(binary[ofs:ofs+2], 'little')
    if basic_next_line_ptr != 0x0:
        print(f"basic next line address: ${basic_next_line_ptr:04x}")
    ofs += 2

    byte_s = ""
    for i in range(2, ofs):
        b = binary[i]
        if i > 2: byte_s += ","
        byte_s += f"${b:02x}"

    out_s = f"!byte {byte_s}"
    if options.show_comments: out_s += f" ; {basic_line_num} SYS{basic_statement}"
    write(out_file, out_s)
    write(out_file, "")

    start_ofs = ofs

    statements = []
    buffer_index = 0

    while ofs < binary_size:
        addr = load_address + ofs - 2
        opcode = binary[ofs]

        if opcode == 0x0:
            buffer = []
            while ofs < binary_size and binary[ofs] == 0x0:
                buffer.append(binary[ofs])
                ofs += 1
            statement = process_buffer(addr, buffer)
            statement.index = buffer_index
            statements.append(statement)
            buffer_index += 1
            continue

        if not opcode in OpcodeMap:
            statements.append(process_invalid_statement(addr, opcode))
            ofs += 1
            continue

        opcode_info = OpcodeMap[opcode]
        instruction = opcode_info[1]
        opcode_name = InstructionNames[instruction]
        if not opcode_name:
            #print(f"unknown opcode name: ${opcode:02x}")
            opcode_name = "???"

        address_mode = opcode_info[2]
        cycles = opcode_info[3]
        cross_page = opcode_info[4]

        data = None
        data2 = None

        data_size = 0

        if address_mode == AddressMode.imm:
            data_size = 1
        elif address_mode == AddressMode.abs:
            data_size = 2
        elif address_mode == AddressMode.zp:
            data_size = 1
        elif address_mode == AddressMode.imp:
            pass
        elif address_mode == AddressMode.ind:
            data_size = 2
        elif address_mode == AddressMode.abx:
            data_size = 2
        elif address_mode == AddressMode.aby:
            data_size = 2
        elif address_mode == AddressMode.zpx:
            data_size = 1
        elif address_mode == AddressMode.zpy:
            data_size = 1
        elif address_mode == AddressMode.izx:
            data_size = 1
        elif address_mode == AddressMode.izy:
            data_size = 1
        elif address_mode == AddressMode.rel:
            data_size = 1
        elif address_mode == AddressMode.acc:
            pass
        else:
            pass

        if data_size >= 1:
            data = binary[ofs+1] if ofs + 1 < binary_size else 0
        if data_size >= 2:
            data2 = binary[ofs+2] if ofs + 2 < binary_size else 0

        instruction_size = 1 + data_size

        statement = process_statement(addr, opcode, instruction, data, data2, address_mode, cycles, cross_page)

        if instruction == 42: statement.set_comment("return")
        elif instruction == 41: statement.set_comment("return from interrupt")
        elif instruction == 35 or instruction == 36: statement.set_comment("push to stack")
        elif instruction == 37 or instruction == 38: statement.set_comment("pull from stack")
        elif instruction == 46: statement.set_comment("disable interrupts")
        elif instruction == 15: statement.set_comment("enable interrupts")
        elif opcode == 0xa2 and get(binary, ofs+2) == 0xa0 and get(binary, ofs+4) == 0x8e and get(binary, ofs+7) == 0x8c:
            addr_1 = get(binary, ofs+1) | (get(binary, ofs+3)<<8)
            addr_2 = get(binary, ofs+5) | (get(binary, ofs+6)<<8)
            addr_3 = get(binary, ofs+8) | (get(binary, ofs+9)<<8)

            if addr_2 == 0xfffe and addr_3 == 0xffff:
                statement.set_comment("set hardware raster irq handler")
                statement.jump_address = addr_1
            elif addr_2 == 0x0314 and addr_3 == 0x0315:
                statement.set_comment("set kernal raster irq handler")
                statement.jump_address = addr_1
        elif opcode == 0x8c and get(binary, ofs+3) == 0x8d:
            addr_1 = get(binary, ofs+1) | (get(binary, ofs+2)<<8)
            addr_2 = get(binary, ofs+4) | (get(binary, ofs+5)<<8)

            if addr_1 == 0xfffe and addr_2 == 0xffff:
                statement.set_comment("set hardware raster irq handler")
                statement.jump_address = addr_1
            elif addr_1 == 0x0314 and addr_2 == 0x0315:
                statement.set_comment("set kernal raster irq handler")
                statement.jump_address = addr_1

        elif ofs + instruction_size < binary_size:
            next_opcode = binary[ofs + instruction_size]
            if next_opcode in OpcodeMap:
                next_opcode_info = OpcodeMap[next_opcode]
                next_instruction = next_opcode_info[1]
                if instruction == 29 and next_instruction == 47: statement.set_comment("load/store A")
                elif instruction == 30 and next_instruction == 48: statement.set_comment("load/store X")
                elif instruction == 31 and next_instruction == 49: statement.set_comment("load/store Y")

        statements.append(statement)

        ofs += instruction_size

    for statement in statements:
        if statement.is_jump() or statement.jump_address != None:
            addr = statement.get_jump_addr()
            jump_target = find_addr(statements, addr)
            if jump_target:
                statement.add_jump_target(jump_target)
                jump_target.add_ref(statement)
                if not statement.is_jump():
                    jump_target.irq_handler = True

    label_index = 0
    irq_index = 0
    for statement in statements:
        if statement.has_refs():
            if statement.irq_handler != None:
                statement.index = irq_index
                irq_index += 1
            else:
                statement.index = label_index
                label_index += 1

    last_blank = False
    label_suffix = ""
    if PROFILE == PROFILE_GNU: label_suffix=":"
    for statement in statements:
        if statement.has_refs():
            if not last_blank: write(out_file, "")
            write(out_file, f"{get_label_name(statement)}{label_suffix}")
        last_blank = False
        write(out_file, statement.to_string(options))
        if statement.is_return():
            if not last_blank:
                write(out_file, "")
                last_blank = True

    if out_file: out_file.close()

    return

def monitor(source, dest, show_binary):
    sz = 0
    tm = 0.0
    running = True
    while running:
        try:
            stats = os.stat(source)
            if stats.st_size != sz or stats.st_mtime != tm:
                sz = stats.st_size
                tm = stats.st_mtime
                process(source, dest, show_binary)
        except:
            pass
        time.sleep(3.0)

def main():
    '''Main entry'''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:mbc", ["help", "monitor", "nobinary", "nocomments"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if len(args) < 1:
        usage()
        sys.exit()

    monitoring = False

    options = Options()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-m", "--monitor"):
            monitoring = True
        elif o in ("-b", "--nobinary"):
            options.show_binary = False
        elif o in ("-c", "--nocomments"):
            options.show_comments = False

    source = Path(args[0])

    dest = None
    if len(args) > 1: dest = Path(args[1])

    if monitoring:
        monitor(source, dest, options)
    else:
        process(source, dest, options)

if __name__ == "__main__":
    main()
