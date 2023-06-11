; -------------------------------------------------
; Audio
; -------------------------------------------------

!set SID_TYPE_UNKNOWN = 0
!set SID_TYPE_6581 = 1
!set SID_TYPE_8580 = 2

; -------------------------------------------------
; audio data structures
; -------------------------------------------------

!set audio_data = sample
!set audio_data_end = sample_end
!set audio_size = audio_data_end - audio_data
!set audio_update_queue_inc  = 80                       ; 50Hz, 4000kHz, 8 bits/sample, 80 samples/frame
!set audio_update_batch_1    = 4                        ; samples per update
!set audio_update_batch_2    = 1                        ; samples per update

audio_sid_type               !byte SID_TYPE_UNKNOWN     ; 0=unknown, 1=6581, 2=8580
audio_update_queue           !byte 0
audio_ofs                    !word 0
audio_high_nibble            !byte 0
audio_update_count           !byte 0
audio_update_max_count       !byte 0

; -------------------------------------------------
; audio init
; -------------------------------------------------

audio_init

    !if (AUDIO != 1) { rts }

audio_init_detect_sid
    +system_disable_interrupts

    lda #$ff
audio_init_detect_sid_wait
    cmp $d012	                ; don't run it on a badline.
    bne audio_init_detect_sid_wait
                                ; detection itself starts here
    lda #$ff	                ; set frequency in voice 3 to $ffff
    sta $d412	                ; ...and set testbit (other bits don't matter) in VCREG3 ($d412) to disable oscillator
    sta $d40e
    sta $d40f
    lda #$20	                ; sawtooth wave and gatebit OFF to start oscillator again.
    sta $d412
    lda $d41b	                ; accu now has different value depending on sid model (6581=3/8580=2)
    lsr		                    ; ...that is: Carry flag is set for 6581, and clear for 8580.
    bcc +

    lda #SID_TYPE_6581          ; SID model 6581 (old)
    sta audio_sid_type

    lda #<audio_volume_table_6581
    sta <audio_volume_table
    lda #>audio_volume_table_6581
    sta >audio_volume_table

    jmp ++

+   lda #SID_TYPE_8580          ; SID model 8580 (new)
    sta audio_sid_type

    lda #<audio_volume_table_8580
    sta <audio_volume_table
    lda #>audio_volume_table_8580
    sta >audio_volume_table

++
    +system_enable_interrupts

    ldx #$19                    ; write zero to all SID registers
    lda #0
audio_init_loop
    sta $d400,X
    dex
    bne audio_init_loop

    lda #$0f                    ; attack=0, decay=15
    sta $d405
    sta $d40c
    sta $d413

    lda #$ff                    ; sustain=15, release=15
    sta $d406
    sta $d40d
    sta $d414

    lda #$49                    ; waveform=square, testbit set
    sta $d404
    sta $d40b
    sta $d412

    lda #$ff                    ; cutoff as high as possible
    sta $d415
    sta $d416

    lda #$03                    ; enable voice 1 and 2 through filter
    sta $d417

    rts

; -------------------------------------------------
; audio update queue
; -------------------------------------------------

audio_fill_queue

    !if (AUDIO != 1) { rts }

    clc                                         ; increase update counter
    lda audio_update_queue
    cmp #$80
    bcs +
    adc #audio_update_queue_inc
    sta audio_update_queue
+
    rts

; -------------------------------------------------
; audio playback
; -------------------------------------------------

audio_update                                    ; audio update

    !if (AUDIO != 1) { rts }

    pha                                         ; push a to stack

    lda audio_update_queue
    bne +
    pla                                         ; no update needed
    rts                                         ; return
+

    txa                                         ; push registers to stack
    pha
    tya
    pha

audio_update_begin

    ldy audio_update_queue
    tya
    cmp audio_update_max_count
    bcc +
    ldy audio_update_max_count                  ; limit updates
+

    +debug_border_on

audio_update_loop
    +cmpw audio_ofs, audio_size                 ; check audio offset range
    bne +
    +storew audio_ofs, 0                        ; loop sample
+

    clc                                         ; get sample address
    lda #<audio_data
    adc audio_ofs
    sta reg0+0

    lda #>audio_data
    adc audio_ofs+1
    sta reg0+1

    ldx #0                                      ; read sample byte
    lda (reg0, X)
    tax

    lda audio_volume_table, X                   ; get volume from table
    sta $d418                                   ; set master volume

    +incw audio_ofs

    dec audio_update_queue                      ; drop from queue
    dey
    bne audio_update_loop                       ; next sample

audio_update_end                                ; audio update end
    +debug_border_off

    pla                                         ; pull registers from stack
    tay
    pla
    tax
    pla
    rts

; -------------------------------------------------
; audio volume tables
;
; Thanks to Pex 'Mahoney' Tufvesson!
; https://livet.se/mahoney/c64-files/Musik_RunStop_8-bit_sample_measurements_by_Pex_Mahoney_Tufvesson.zip
;
; -------------------------------------------------

audio_volume_table           !word 0x0000

audio_volume_table_6581 ; volume_table_common_6510_256_of_256
    !byte 159, 159, 159, 159, 159, 159, 159, 159, 159, 159, 159, 159, 159, 159, 159, 159
    !byte 159, 159, 159, 158, 158, 158, 158, 158, 157, 157, 157, 157, 157, 157, 156, 156
    !byte 156, 156, 156, 156, 155, 155, 155, 155, 155, 220, 220, 154, 154, 154, 154, 219
    !byte 153, 153, 153, 153, 153, 153, 218, 152, 152, 152, 152, 152, 217, 186, 186, 151
    !byte 151, 151, 151, 151, 151, 151, 151, 215, 215, 150, 150, 150, 150, 214, 214, 214
    !byte 149, 149, 149, 149, 149, 213, 213, 213, 148, 148, 148, 148, 181, 212, 212, 212
    !byte 180, 180, 147, 147, 244, 211, 211, 179, 179, 179, 146, 146, 146, 210, 210, 178
    !byte 178, 242, 242, 145, 145, 145, 209, 177, 241, 241, 18, 81, 81, 113, 144, 48, 0
    !byte 161, 162, 163, 164, 164, 165, 65, 97, 33, 33, 1, 1, 66, 66, 66, 98, 98, 34, 34
    !byte 34, 34, 67, 67, 99, 99, 99, 35, 35, 35, 35, 68, 100, 100, 100, 69, 69, 69, 36
    !byte 36, 36, 36, 101, 70, 70, 70, 70, 37, 37, 37, 71, 71, 71, 103, 103, 38, 38, 38
    !byte 38, 72, 72, 72, 104, 104, 39, 39, 39, 73, 73, 105, 105, 74, 74, 74, 74, 40, 40
    !byte 40, 40, 75, 75, 107, 41, 41, 41, 41, 41, 108, 108, 42, 42, 42, 42, 42, 42, 78
    !byte 78, 43, 43, 43, 43, 43, 43, 44, 44, 44, 44, 44, 44, 44, 45, 45, 45, 45, 45, 45
    !byte 45, 46, 46, 46, 46, 46, 46, 14, 47, 47, 47, 47

audio_volume_table_8580 ; volume_table_common_8580_256_of_256
    !byte 159, 159, 223, 223, 223, 223, 223, 158, 158, 158, 158, 158, 222, 222, 222
    !byte 222, 222, 157, 157, 157, 157, 157, 157, 221, 221, 221, 221, 221, 156, 156
    !byte 156, 156, 156, 220, 220, 220, 220, 220, 155, 155, 155, 155, 155, 155, 219
    !byte 219, 219, 219, 219, 154, 154, 154, 154, 154, 218, 218, 218, 218, 218, 153
    !byte 153, 153, 153, 153, 153, 217, 217, 217, 217, 217, 152, 152, 152, 152, 152
    !byte 216, 216, 216, 216, 216, 216, 63,  63,  63,  63,  151, 151, 151, 215, 215
    !byte 62,  62,  126, 126, 126, 61,  61,  125, 125, 125, 60,  60,  124, 124, 124
    !byte 59,  59,  123, 123, 123, 58,  58,  122, 122, 122, 57,  57,  57,  121, 121
    !byte 24,  24,  88,  88,  88,  120, 23,  23,  55,  87,  119, 22,  22,  22,  86
    !byte 86,  86,  21,  21,  85,  85,  85,  20,  20,  20,  84,  84,  19,  19,  19
    !byte 83,  83,  83,  18,  18,  18,  82,  82,  17,  17,  17,  81,  81,  240, 144
    !byte 128, 128, 128, 128, 1,   1,   1,   65,  65,  65,  2,   2,   66,  66,  66
    !byte 3,   3,   3,   3,   67,  67,  4,   4,   4,   4,   68,  68,  68,  5,   5
    !byte 5,   69,  69,  6,   6,   6,   6,   70,  70,  7,   7,   7,   7,   71,  71
    !byte 71,  40,  8,   8,   8,   72,  72,  41,  9,   9,   9,   73,  73,  10,  10
    !byte 10,  10,  74,  74,  11,  11,  11,  75,  75,  75,  44,  12,  12,  12,  76
    !byte 76,  45,  13,  13,  77,  77,  77,  46,  14,  14,  78,  78,  78,  47,  15, 15
