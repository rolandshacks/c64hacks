//
// Raster interrupt helpers
//
// Note: This is due to the overhead of LLVM generated IRQ entry/exit points
//       because of the amount of registers and pseudo-registers to be pushed
//       to the stack. In non-time-critical applications, it is recommended
//       to use the more convenient way with C++.
//

raster_irq_line_0   = 70        // set high-res text mode
raster_irq_line_1   = 140       // update audio and counters
raster_irq_line_2   = 235       // set multi-color text mode
raster_irq_debug    = 0         // enable/disable border color debugging

// unused .data

.text

//
// Set raster irq handler and irq raster line
// (does not support 9th bit)
//
.macro set_raster_irq fn, line
    lda #\line
    sta $d012
    lda #<\fn
    sta $fffe
    lda #>\fn
    sta $ffff
.endm

//
// Clear raster irq flag
//
.macro clear_raster_irq
    lda #$ff
    sta $d019
.endm

//
// Set border color
//
.macro set_border_color col
    lda #\col
    sta $d020
.endm

//
// Raster function. Sets normal (high-resolution) text mode.
//
.global on_raster_irq_0
on_raster_irq_0:
    pha

    .if raster_irq_debug
        set_border_color 1
    .endif

    set_raster_irq on_raster_irq_1, raster_irq_line_1 // set next irq handler

    lda #200    // hard-coded high-res text mode
    sta $d016

    clear_raster_irq

    .if raster_irq_debug
        set_border_color 0
    .endif

    pla
    rti

//
// Raster function. Updates audio.
//
.global on_raster_irq_1
on_raster_irq_1:
    pha

    .if raster_irq_debug
        set_border_color 1
    .endif

    txa
    pha
    tya
    pha

    set_raster_irq on_raster_irq_2, raster_irq_line_2 // set next irq handler

    jsr update_audio

    clear_raster_irq

    pla
    tay
    pla
    tax

    .if raster_irq_debug
        set_border_color 0
    .endif

    pla
    rti

//
// Raster function. Sets multi-color text mode.
//
.global on_raster_irq_2
on_raster_irq_2:
    pha

    .if raster_irq_debug
        set_border_color 1
    .endif

    set_raster_irq on_raster_irq_0, raster_irq_line_0       // set next irq handler

    lda #216                                                // hard-coded multi-color mode
    sta $d016

    inc stats_frame_counter                                 // increment 8-bit frame counter

    clear_raster_irq

    .if raster_irq_debug
        set_border_color 0
    .endif

    pla
    rti
