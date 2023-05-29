;
; C64 Demo
;
; 8 animated sprites
;
; Sample playback:  4kHz, 8 bit
;                   312 raster lines, 50 fps
;                   160 samples/frame,  2 lines/sample
;

!src "lib64/libmacro64.asm"

+std_startup $0801, main

; -------------------------------------------------
; application flags
; -------------------------------------------------

!set DEBUG = 0
!set AUDIO = 1

; -------------------------------------------------
; debug macros
; -------------------------------------------------

!macro debug_border_set .value {
    !if (DEBUG = 1) {
        lda #.value
        sta audio_debug_background_color
    }
}

!macro debug_border_on {
    !if (DEBUG = 1) {
        lda audio_debug_background_color
        sta $d020
    }
}

!macro debug_border_off {
    !if (DEBUG = 1) {
        lda #0
        sta $d020
    }
}

; -------------------------------------------------
; application data
; -------------------------------------------------

.hellotext !scr "hello, world!",0 ; zero-terminated string
!set raster_irq_interval = 42
!set sprite_count = 8

; -------------------------------------------------
; helpers
; -------------------------------------------------

print_title
    +strcpy video_screen_base + 93, .hellotext
    rts

; -------------------------------------------------
; init
; -------------------------------------------------

init
    jsr system_init                             ; initialize system
    jsr system_disable_kernal_and_basic         ; disable kernal and basic to get RAM

    jsr video_init                              ; init video and charset
    jsr sprite_init                             ; init sprites
    jsr audio_init                              ; init audio

    jsr video_clear                             ; clear screen

    lda #1
    jsr video_set_colors                        ; set color ram

    lda #0
    jsr video_set_background                    ; set background color

    lda #6
    jsr video_set_border                        ; set border color

    !for id, 0, sprite_count-1 {                  ; initialize sprites
        +sprite_set_enabled id, 1
        +sprite_set_mode id, 1
        +sprite_set_color id, .sprite_colors + id
        +sprite_set_common_colors 1, 11
    }

    jsr raster_irq_init                         ; enable raster interrupts

init_end
    rts                                         ; init end

; -------------------------------------------------
; raster interrupt
; -------------------------------------------------

raster_vblank_counter   !byte 0
raster_irq_handler
    pha                                         ; push a,x,y to stack
    txa
    pha
    tya
    pha

    lda #$ff                                    ; reset irq flag
    sta $d019

    inc raster_vblank_counter

    pla                                         ; pull a,x,y from stack
    tay
    pla
    tax
    pla

    rti

; -------------------------------------------------
; main loop
; -------------------------------------------------

run                                             ; run entrance
    pha                                         ; push to stack
    txa
    pha
    tya
    pha

    jsr print_title                             ; print title message to screen

run_loop
    lda #audio_update_queue_inc                 ; re-fill sample queue
    sta audio_update_queue

    +debug_border_set 1
    lda #audio_update_batch_1
    sta audio_update_max_count

    jsr sprites_update                          ; update sprites
    lda system_emulator_flag                    ; if not in cpu emulator
    bne run_loop

    +debug_border_set 2
    lda #audio_update_batch_2
    sta audio_update_max_count

run_wait_vblank_loop
    jsr audio_update                            ; update audio playback
    lda raster_vblank_counter                   ; check if vblank happened
    bne +
    jmp run_wait_vblank_loop                    ; not yet vblank
+

    lda #0                                      ; reset vblank flag
    sta raster_vblank_counter
    jmp run_loop                                ; main loop

run_end                                         ; program exit
    pla                                         ; restore from stack
    tay
    pla
    tax
    pla
    rts

; -------------------------------------------------
; main
; -------------------------------------------------

main                                            ; main entry
    jsr init                                    ; program init
    jsr run                                     ; program run loop
    rts

; -------------------------------------------------
; libraries
; -------------------------------------------------

!src "src/sprites.asm"
!src "src/audio.asm"
!src "lib64/libstd64.asm"