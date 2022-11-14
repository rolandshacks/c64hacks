

/* INCLUDE link.ld */


MEMORY {
    ram (rw) : ORIGIN = 0x0801, LENGTH = 0xf7ff
    /* ram (rw) : ORIGIN = 0x0801, LENGTH = 0x97ff */
}

INCLUDE commodore.ld

/* Set initial soft stack address to end of BASIC area. (It grows down.) */
__stack = 0x9FFF;

OUTPUT_FORMAT {
    /* Tells the C64 LOAD command where to place the file's contents. */
    SHORT(0x0801)
    TRIM(ram)
}

SECTIONS {
    OVERLAY 0x3000 : AT (0x3000)
    {
        .sid { }
    }

    OVERLAY 0x8000 : AT (0x8000)
    {
        .sprites { }
    }
}
