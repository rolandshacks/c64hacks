# C64 C++ Demo

![platform: c64](img/platforms.svg)
![lang: cpp20](img/lang.svg)
![dev: emulator](img/dev.svg)
![license: apache](img/license.svg)

Demo for the Commodore C64 written in C++ 20 using Clang for 6502/6510.

<table><tr>
  <td style="padding: 20px; padding-right: 40px;"><img src="img/demo.gif" height=136px></td>
</tr></table>

- Animated sprites
- Scrolling starfield
- SID music
- Raster interrupt handling
- C64 system programming SDK
- Support tools
- CMake build configuration

Prerequisites

-  The LLVM-MOS development environment needs to be installed (https://github.com/llvm-mos/llvm-mos-sdk).
- For development and building, please install the VS64 extension for Visual Studio Code (https://marketplace.visualstudio.com/items?itemName=rosc.vs64)

## Tools coming with the Demo

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

## Additional Infos

### Visual Studio Code

Please make sure you add the CMake "Kit" definition to the
use-local configuration file "cmake-tools-kits.json"

On Windows, it could look like this:

```

 {
    "name": "Clang 16.0.0 (MOS)",
    "compilers": {
      "C": "SOMEFOLDER\\llvm-mos\\bin\\mos-c64-clang.bat",
      "CXX": "SOMEFOLDER\\llvm-mos\\bin\\mos-c64-clang++.bat"
    }
  }

```

On Linux, it might look similar to this:

```

  {
    "name": "Clang 16.0.0 llvm-mos",
    "compilers": {
      "C": "/home/roland/llvm-mos/bin/mos-c64-clang",
      "CXX": "/home/roland/llvm-mos/bin/mos-c64-clang++"
    }
  }

```

### Links to Further Information

LLVM Assembler and Inline Assembler

- Have a look at the GNU assembler
- https://llvm.org/docs/LangRefhtml#inline-assembler-expressions
- https://llvm.org/docs/LangRef.html#inline-asm-modifiers

GoatTracker2 SID Generation

- gt2reloc music.sng music.sid -B0 -D0 -E0 -H0 -C0 -I1 -J0 -W50 -ZFE

