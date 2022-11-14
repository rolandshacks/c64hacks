# C64 C++ Demo

## Infos

LLVM Inline Assembler

https://llvm.org/docs/LangRef.html#inline-assembler-expressions
https://llvm.org/docs/LangRef.html#inline-asm-modifiers

SID player
https://weblambdazero.blogspot.com/2022/04/embedding-data-in-executable-with-llvm.html

Raster IRQ
https://c64os.com/post/rasterinterruptsplitscreen


## Tools

### C64 Disassembler

DIS64 is a disassembler for 6502 machine code.


#### Usage

```
dis64 [-b] [-c] [-m] INFILE [OUTFILE]

INFILE            : C64 prg input file")
OUTFILE           : Output assembler file")
-b, --nobinary    : Do not add hex dump
-c, --nocomments  : Do not generate comments
-m, --monitor     : Run in continuous monitoring mode
```


#### Examples

Disassemble file and output commented assembly to console:

```
dis64 demo.prg
```

Disassemble file and output commented assembly including
address and binary data annotations to a file

```
dis64 demo.prg demo.s
```

Monitor and automatically disassemble file to be used as
background task to analyze generated machine code, especially
when working with higher level programming languaces such as
C/C++ (llvm-mos).

```
dis64 -m demo.prg demo.s
```

#### Limitations

Currently, the disassembler just supports C64 .PRG files,
support for other formats will be added later

### D64 Disk Tool (disk64)

Little helper to either show D64 directory listing or extract
individual files from a D64 file.

```
Usage: disk64 [-l|--list] [-e|--export] DISK.D64 [FILENAME]
DISK.D64          : C64 disk file
-l, --list        : List directory
-e, --export      : Export file from disk
```


### SID Extractor (sidc)

Extracts raw data and meta information from a .SID file and
generates a C++ byte array from it to be compiled into
an executable.

```
Usage: sidc SIDFILE CPPFILE

SIDFILE : C64 SID music file
CPPFILE : C++ output file
```
