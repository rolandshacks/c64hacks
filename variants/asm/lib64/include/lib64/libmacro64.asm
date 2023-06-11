;
; C64 Macro Library
;

; -------------------------------------------------
; Program Startup
; -------------------------------------------------

;
; Generate startup BASIC code line (1973 SYS xxxx)
;
!macro __startup_basic_code {
    !word +, 1973                               ; basic line
    !byte $9e                                   ; 'SYS' command
    !byte $20                                   ; space character
    !byte $30+((+ +2)/1000)%10                  ; address digit
    !byte $30+((+ +2)/100)%10                   ; address digit
    !byte $30+((+ +2)/10)%10                    ; address digit
    !byte $30+(+ +2)%10                         ; address digit
    !byte $0                                    ; end of basic line
+   !word $0                                    ; end of basic program
}

!macro std_startup .load_address, .jump_address {
    *=.load_address                              ; set load address
    +__startup_basic_code                       ; basic startup line
    jmp .jump_address                           ; jump to label
}

!macro std_startup .load_address {
    *=.load_address                              ; set load address
    +__startup_basic_code                       ; basic startup line
}

!macro std_startup {
    +__startup_basic_code                        ; basic startup line
}

; -------------------------------------------------
; Common
; -------------------------------------------------

!macro poke .addr, .value {
    lda #.value
    sta .addr
}

; -------------------------------------------------
; Zero-Page Registers
; -------------------------------------------------

; General purpose (always available)
!addr reg0 = $fb ; $fb+fc
!addr reg1 = $fd ; $fd+fe

; General purpose (just if no RS232)
!addr reg2 = $f7 ; $f7+f8
!addr reg3 = $f9 ; $f9+fa

; General purpose (just if no BASIC used)
!addr reg4 = $62 ; $62+63
!addr reg5 = $64 ; $64+65
!addr reg6 = $66 ; $66+67
!addr reg7 = $68 ; $68+69

; Used for math operations (just if no BASIC used)
; !addr regl0 = $6a ; $6a+6b+6c+6d

; -------------------------------------------------
; Data Handling
; -------------------------------------------------

!macro storeb .addr, .value {
    lda #.value
    sta .addr
}

!macro storebi .addr, .value {
    +storew 0, .addr
    +storebi reg0, .value
}

!macro storebv .addr, .value {
    lda .value
    sta .addr
}

!macro storeibv .addr, .value {
    lda .value
    ldy #0
    sta (.addr),y
}

!macro storew .addr, .value {
    lda #<(.value)
    sta .addr
    lda #>(.value)
    sta .addr+1
}

!macro moveb .dest, .src {
    lda .src
    sta .dest
}

!macro movew .dest, .src {
    lda .src
    sta .dest
    lda .src+1
    sta .dest+1
}

!macro movel .dest, .src {
    lda .src
    sta .dest
    lda .src+1
    sta .dest+1
    lda .src+2
    sta .dest+2
    lda .src+3
    sta .dest+3
}

!macro incw .t {
    inc .t
    bne +
    inc .t + 1
+
}

!macro decw .t {
    dec .t
    lda .t
    cmp #$ff
    bne +
    dec .t + 1
+
}

!macro beqw .addr, .val {
    lda .val
    bne +
    lda .val + 1
    beq .addr
+
}

!macro addb .addr,.value {
    clc
    lda .addr
    adc .value
    sta .addr
}

!macro subb .addr,.value {
    sec
    lda .addr
    sbc .value
    sta .addr
}

!macro addw .addr,.value {
    clc
    lda .addr
    adc #<(.value)
    sta .addr
    lda .addr+1
    adc #>(.value)
    sta .addr+1
}

!macro addwb .addr,.value {
    clc
    lda .addr
    adc #.value
    sta .addr
    lda .addr+1
    adc #0
    sta .addr+1
}

!macro addwv .addr,.value {
    clc
    lda .addr
    adc .value
    sta .addr
    lda .addr+1
    adc .value+1
    sta .addr+1
}

!macro addwbv .addr,.value {
    clc
    lda .addr
    adc .value
    sta .addr
    lda .addr+1
    adc #0
    sta .addr+1
}

!macro subw .addr,.value {
    sec
    lda .addr
    sbc #<(.value)
    sta .addr
    lda .addr+1
    sbc #>(.value)
    sta .addr+1
}

!macro subwb .addr,.value {
    sec
    lda .addr
    sbc #<(.value)
    sta .addr
    lda .addr+1
    sbc #0
    sta .addr+1
}

!macro subwv .addr,.value {
    sec
    lda .addr
    sbc .value
    sta .addr
    lda .addr+1
    sbc .value+1
    sta .addr+1
}

!macro subwbv .addr,.value {
    sec
    lda .addr
    sbc .value
    sta .addr
    lda .addr+1
    sbc #0
    sta .addr+1
}

!macro addbv .addr,.addr2 {
    clc
    lda .addr
    adc .addr2
    sta .addr
}

!macro subbv .addr,.addr2 {
    sec
    lda .addr
    sbc .addr2
    sta .addr
}

!macro cmpw .addr, .val {
    lda #>(.val)
    cmp .addr+1
    bne +
    lda #<(.val)
    cmp .addr
+
}

!macro cmpb .addr, .val {
    lda .val
    cmp .addr
}

!macro cmpwi .addr, .val {
    +storew reg0, .addr
    +cmpw reg0, .val
+
}

!macro clearb .addr {
    lda #0
    sta .addr
}

!macro clearw .addr {
    lda #0
    sta .addr
    sta .addr+1
}

!macro set_bit .addr,.bitnum,.bitvalue {
    lda .addr
    !if (.bitvalue=1) {
        ora #(1 << .bitnum)
    } else {
        and #($ff - (1 << .bitnum))
    }
    sta .addr
}

; -------------------------------------------------
; Common
; -------------------------------------------------

!macro strcpy .dst, .src {
    +storew reg0, .src
    +storew reg1, .dst
    jsr strcpy_fn
}

!macro memset .dst,.val,.len {
    +storew reg0, .dst
    +storeb reg2, .val
    +storew reg1, .len
    jsr memset_fn
}

!macro memcpy .dst,.src,.len {
    +storew reg0, .dst
    +storew reg1, .src
    +storew reg2, .len
    jsr memcpy_fn
}

; -------------------------------------------------
; System
; -------------------------------------------------

!macro system_disable_interrupts {
    sei
}

!macro system_enable_interrupts {
    cli
}

!macro system_mem_map .flags {
    lda $01
    and #$f8
    ora #.flags
    sta $01
}

; -------------------------------------------------
; Video
; -------------------------------------------------

!set video_vic_bank = 2
!set video_screen_bank = 1
!set video_charset_bank = 1
!addr video_vic_base = video_vic_bank * $4000 ; ($8000)
!addr video_screen_base = video_vic_base + video_screen_bank * $400 ; ($8400)
!addr video_bitmap_base = video_vic_base + $2000 ; ($A000)
!addr video_color_base = $d800
!addr video_charset_base = video_vic_base + video_charset_bank * $800 ; ($8800)
!addr video_charset_base_origin = $d000

; -------------------------------------------------
; Sprites
; -------------------------------------------------

!addr sprite_base = video_vic_base ; ($8000)
!set sprite_base_index = 0

!addr sprw0 = $6a ; $6a+6b
!addr sprw1 = $6c ; +6c+6d

!macro sprite_line .v {
	!by .v>>16, (.v>>8)&255, .v&255
}

!macro sprite_set_enabled .sprite,.enabled {
    +set_bit $d015,.sprite,.enabled
}

!macro sprite_set_mode .sprite,.multicolor {
    +set_bit $d01c,.sprite,.multicolor
}

!macro sprite_set_data .sprite,.block {

    lda #>(video_screen_base + $03f8)                                 ; do not go beyond
    sta reg0 + 1
    lda #<(video_screen_base + $03f8)
    sta reg0

    clc
    lda reg0
    adc #.sprite
    sta reg0
    lda reg0+1
    adc #0
    sta reg0+1

    lda .block
    ldy #0
    sta (reg0),y

}

!macro sprite_set_color .sprite,.color {
    +moveb $d027+.sprite, .color
}

!macro sprite_set_common_colors .color_a,.color_b {
    +moveb $d026, .color_a
    +moveb $d025, .color_b
}

!macro sprite_set_pos .sprite,.x,.y {
    +storeb reg0, .sprite
    +movew reg1, .x
    +movew reg2, .y
    jsr sprite_set_pos_fn
}

!macro sprite_define .id,.x,.y,.vx,.vy,.anim_delay {
    !byte .id               ; [00] id
    !word .x                ; [01] x
    !word .y                ; [03] y
    !byte >(.vx)            ; [05] vx
    !byte <(.vx)            ; [05] vx_sub
    !word .vy               ; [07] vy
    !byte 0                 ; [09] xdir (0: right, 1: left)
    !byte 0                 ; [10] ydir (0: down, 1: up)
    !byte 0                 ; [11] anim
    !byte .anim_delay       ; [12] anim_delay
    !byte 0                 ; [13] anim_counter
    !byte 0                 ; [14] vx_counter
                            ; len = 15
}

!macro sprite_table .num_sprites {
    !for id, 0, .num_sprites-1 {
        +sprite_define id, 24 + ((id*169)%298), 0+(id*25), $200 + id*50, id*41, 2
    }
}

!set sprite_field_id = 0
!set sprite_field_x = 1
!set sprite_field_y = 3
!set sprite_field_vx = 5
!set sprite_field_vxsub = 6
!set sprite_field_vy = 7
!set sprite_field_xdir = 9
!set sprite_field_ydir = 10
!set sprite_field_anim = 11
!set sprite_field_anim_delay = 12
!set sprite_field_anim_counter = 13
!set sprite_field_vx_counter = 14
