;
; C64 Standard Library
;

; -------------------------------------------------
; Common
; -------------------------------------------------

strcpy_fn ; (addr0, addr1), max 255 chars
    ldy #0

strcpy_loop
    lda (reg0),Y
    beq strcpy_end
    sta (reg1),Y
    iny
    bne strcpy_loop

strcpy_end
    rts

memset_fn
    ldy #0

memset_loop
    +beqw memset_end, reg1
    lda reg2
    sta (reg0),y
    +decw reg1
    +incw reg0
    jmp memset_loop

memset_end
    rts

memcpy_fn ; (reg0: dest, reg1: source, reg2, length)
    lda reg2+1
    beq memcpy_bytes

memcpy_pages
    ldy #0

memcpy_page_loop
    lda (reg1),Y
    sta (reg0),y
    dey
    bne memcpy_page_loop
    +incw reg0+1
    +incw reg1+1
    dec reg2+1
    jmp memcpy_fn

memcpy_bytes
    ldy reg2
    beq memcpy_end

memcpy_bytes_loop
    dey
    lda (reg1),Y
    sta (reg0),y
    cpy #0
    bne memcpy_bytes_loop

memcpy_end
    rts


; -------------------------------------------------
; System
; -------------------------------------------------

system_emulator_flag
    !byte $0

system_init
    jsr system_check_if_emulator
    rts

system_check_if_emulator
    lda $01
    cmp #$ff
    bne +
    lda #$1
    sta system_emulator_flag
+
    rts

system_disable_kernal_and_basic

    +system_disable_interrupts

    +poke $dc0d, $7f            ; disable timer interrupts
    +poke $dd0d, $7f

    lda $dc0d                   ; clear pending interrupts
    lda $dd0d

    +poke $d01a, $0             ; clear interrupt mask bits
    +poke $d019, $0             ; clear interrupt request bits

    +system_mem_map $5          ; disable kernel and basic rom

    +system_enable_interrupts

    rts

; -------------------------------------------------
; Video
; -------------------------------------------------

video_init

    +system_disable_interrupts

    lda #%00000011                   ; enable CIA port A write
    sta $dd02

    lda $dd00                       ; set VIC base
    and #%11111100
    ora # (3 - (video_vic_bank & 3))
    sta $dd00

    lda $dd00
    and #%00000011

    ;jsr video_set_text_mode
    ;jsr video_copy_charset

    jsr video_set_multicolor_bitmap_mode

    +system_enable_interrupts

    rts

video_enable
    lda $d011
    ora #$10
    sta $d011
    rts

video_disable
    lda $d011
    and #$ef
    sta $d011
    rts

video_set_text_mode

    lda $d011                       ; set text mode
    and #$9f                        ; clear bit 5 (BMM) and bit 6 (ECM)
    sta $d011

    lda $d016
    and #$ef                        ; clear bit 4 (MCM)
    sta $d016

    lda $d018                       ; set charset base
    and #$f1
    ora # ((video_charset_bank & $f) << 1)
    sta $d018

    rts

video_set_multicolor_bitmap_mode

    lda $d011                       ; set text mode
    ora #$20                        ; set bit 5 (BMM)
    and #$bf                        ; clear bit 6 (ECM)
    sta $d011

    lda $d016
    ora #$10                        ; set bit 4 (MCM)
    sta $d016

    lda $d018
    and #$07                        ; clear upper 5 bits
    ora # ((video_screen_bank & $f) << 4) ; set screen base
    ora # (video_bitmap_bank << 3)  ; set bitmap base
    sta $d018

    rts


video_copy_charset

    +system_disable_interrupts

    lda $01                         ; enable access char rom, no I/O
    sta reg0
    and #$fb
    sta $01

    ldx #0

video_copy_charset_loop

    !for offset, $0, $10 {
        lda video_charset_base_origin+(offset*$100),x
        sta video_charset_base+(offset*$100),x
    }

    dex
    bne video_copy_charset_loop

    lda reg0                        ; restore memory mapping
    sta $01

    +system_enable_interrupts

    rts

video_clear
    lda #$20                        ; set clear character
    jsr video_set_chars
    rts

video_set_chars ; (A = col)
    ldx #0

video_set_chars_loop
    sta video_screen_base+$0,x
    sta video_screen_base+$100,x
    sta video_screen_base+$200,x
    sta video_screen_base+$300,x
    dex
    bne video_set_chars_loop

    rts

video_set_colors ; (A = col)
    ldx #0

video_set_colors_loop
    sta video_color_base+$0,x
    sta video_color_base+$100,x
    sta video_color_base+$200,x
    sta video_color_base+$300,x
    dex
    bne video_set_colors_loop

    rts

video_set_background ; (A = col)
    sta $d021
    rts

video_set_border ; (A = col)
    sta $d020
    rts

video_wait_next_frame
    pha

-   lda $d011
    and #%10000000
    bne -

-   lda $d012                   ; while >= 80
    cmp #80
    bcs -

-   lda $d012                   ; while < 251
    cmp #251
    bcc -

    pla
    rts

; -------------------------------------------------
; NMI Interrupts
; -------------------------------------------------

nmi_irq_init

    +system_disable_interrupts

    pha                             ; push A to stack

    lda #<nmi_irq_handler           ; setup handler
    sta $fffa
    lda #>nmi_irq_handler
    sta $fffb

                                    ; setup timer A on CIA #2
    lda #<audio_timer_delay         ; timer A low byte
    sta $dd04
    lda #>audio_timer_delay         ; timer A high byte
    sta $dd05

    lda #%10000001                  ; enable interrupt
    sta $dd0d

    lda #%00010001                  ; timer A control
    sta $dd0e

    pla                             ; pull A from stack

    +system_enable_interrupts

    rts

; -------------------------------------------------
; Raster Interrupts
; -------------------------------------------------

raster_irq_init

    +system_disable_interrupts

    pha        ; push A to stack

    lda #$01   ; turn on raster irq
    sta $d01a

    lda #$ff   ; set irq raster line to 255
    sta $d012

    lda $d011
    and #$7f   ; clear irq raster line 9th bit
    sta $d011

    lda #<raster_irq_handler  ; setup handler
    sta $fffe
    lda #>raster_irq_handler
    sta $ffff

    pla         ; pull A from stack

    +system_enable_interrupts

    rts

; -------------------------------------------------
; Time measurement
; Calculates elapsed raster lines
; -------------------------------------------------

last_raster_line !word 0                        ; last raster line 0..312
current_raster_line !word 0                     ; current raster line 0..312
elapsed_raster_lines !word 0                    ; raster lines 0..312
elapsed_ticks !byte 0                           ; raster lines 0..255 (clamped)

get_elapsed_ticks

    pha                                         ; push a

    ;;;;;;;;;;;;;;;;;;;;;;;

    ; set test data for last pos
    ;lda #$0                                     ; hi
    ;sta last_raster_line+1
    ;lda #0                                     ; lo
    ;sta last_raster_line

    ; set test data raster pos
    ;lda #%10000000                              ; hi
    ;sta $d011
    ;lda #56                                    ; lo
    ;sta $d012

    ;;;;;;;;;;;;;;;;;;;;;;;

    ; current > last
    lda current_raster_line
    sta last_raster_line
    lda current_raster_line+1
    sta last_raster_line+1

    ; read current raster pos
    clc
    lda $d011                                   ; hi
    and #$80                                    ; keep bit 7
    rol                                         ; bit 7 > carry > bit 0
    rol
    sta current_raster_line+1
    lda $d012                                   ; lo
    sta current_raster_line

    ; calculate difference
    sec                                         ; set carry
    lda current_raster_line                     ; lo byte
    sbc last_raster_line                        ; sub
    sta elapsed_raster_lines                    ; store
    lda current_raster_line+1                   ; hi byte
    sbc last_raster_line+1                      ; sub
    sta elapsed_raster_lines+1                  ; store

    bpl +                                       ; 312-delta if negative
    clc
    lda elapsed_raster_lines                    ; lo
    adc #56
    sta elapsed_raster_lines
    lda elapsed_raster_lines+1                  ; hi
    adc #1
    sta elapsed_raster_lines+1
+

    lda elapsed_raster_lines+1                  ; hi
    cmp #0
    beq +
    lda #$ff
    jmp ++
+
    lda elapsed_raster_lines                    ; lo
++
    sta elapsed_ticks                           ; 0..255

    pla                                         ; pull a

    rts
