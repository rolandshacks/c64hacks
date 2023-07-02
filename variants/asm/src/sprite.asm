; -------------------------------------------------
; Sprites
; -------------------------------------------------

; -------------------------------------------------
; sprite data structures
; -------------------------------------------------

sprite_colors
    !byte 2, 6, 2, 11, 2, 4, 2, 9

sprite_common_colors
    !byte sprites_col_multi1, sprites_col_multi2

sprite_data
    +sprite_table SPRITE_COUNT

; references to sprite info
sprite_registers
sprite_id               !byte 0
sprite_x                !word 0
sprite_y                !word 0
sprite_vx               !byte 0
sprite_vxsub            !byte 0
sprite_vy               !word 0
sprite_xdir             !byte 0
sprite_ydir             !byte 0
sprite_anim             !byte 0
sprite_anim_delay       !byte 0
sprite_anim_counter     !byte 0
sprite_vx_counter       !byte 0
sprite_registers_end

!set sprite_registers_size = sprite_registers_end - sprite_registers

; -------------------------------------------------
; sprite init
; -------------------------------------------------

sprite_init
    +memcpy video_vic_base, sprites, sprites_end - sprites
    rts

; -------------------------------------------------
; update sprite table
; -------------------------------------------------

sprites_update
    ; update sprite data tables
    !for id, 0, SPRITE_COUNT-1 {
        !set sprite = sprite_data + id * sprite_registers_size

        !for ofs, 0, sprite_registers_size-1 {
            lda sprite+ofs
            sta sprite_registers+ofs
        }

        jsr sprite_update

        !for ofs, 0, sprite_registers_size-1 {
            lda sprite_registers+ofs
            sta sprite+ofs
        }

    }

    rts

sprites_flush

    ; set all vic sprite registers at once
    !for id, 0, SPRITE_COUNT-1 {
        !set sprite = sprite_data + id * sprite_registers_size

        ; set sprite position registers
        +sprite_set_pos id, sprite + sprite_field_x, sprite + sprite_field_y

        ; update sprite data registers
        +sprite_set_data id, sprite + sprite_field_anim
    }

    rts

; -------------------------------------------------
; update one sprite
; -------------------------------------------------

sprite_update

sprite_x_move                                   ; update sprite x
    lda sprite_xdir                             ; check x direction
    bne sprite_x_move_left

sprite_x_move_right                             ; move right

    ; handle sub-pixel move

    clc                                         ; clear carry
    lda sprite_vx_counter
    adc sprite_vxsub
    cmp #$80
    bcs +
    sec                                         ; set carry
    sbc #$80
    sta sprite_vx_counter

    clc                                         ; sprite x += 1
    lda sprite_x
    adc #1
    sta sprite_x
    lda sprite_x + 1
    adc #0
    sta sprite_x + 1
+
    sta sprite_vx_counter

    ; calculate x += vx

    clc
    lda sprite_x
    adc sprite_vx
    sta sprite_x
    lda sprite_x + 1
    adc #0
    sta sprite_x + 1

    lda #>(322)                                 ; check right border
    cmp sprite_x + 1
    bne +                                       ; msb not identical, skip
    lda #<(322)
    cmp sprite_x
+   bcs +

    lda #>(322)                                 ; do not go beyond
    sta sprite_x + 1
    lda #<(322)
    sta sprite_x

    lda #1
    sta sprite_xdir                             ; reverse direction
+
    jmp sprite_x_move_done

sprite_x_move_left                              ; move left


    ; handle sub-pixel move

    clc                                         ; clear carry
    lda sprite_vx_counter
    adc sprite_vxsub
    cmp #$80
    bcs +
    sec                                         ; set carry
    sbc #$80
    sta sprite_vx_counter

    sec                                         ; sprite x -= 1
    lda sprite_x
    sbc #1
    sta sprite_x
    lda sprite_x + 1
    sbc #0
    sta sprite_x + 1
+
    sta sprite_vx_counter

    ; move x -= vx

    sec
    lda sprite_x
    sbc sprite_vx
    sta sprite_x
    lda sprite_x + 1
    sbc #0
    sta sprite_x + 1

    lda #>(24)                                  ; check left border
    cmp sprite_x + 1
    bne +                                       ; msb not identical, skip
    lda #<(24)
    cmp sprite_x
+   bcc +

    lda #>(24)                                 ; do not go beyond
    sta sprite_x + 1
    lda #<(24)
    sta sprite_x

    lda #0
    sta sprite_xdir                             ; reverse direction
+

sprite_x_move_done                              ; done with x

sprite_y_move                                   ; update sprite y
    lda sprite_ydir                             ; check y direction
    bne sprite_y_move_up

sprite_y_move_down                              ; move down

    lda #>($1000)                               ; handle gravity
    cmp sprite_vy + 1
    bne +
    lda #<($1000)
    cmp sprite_vy
+   bcc +

    clc                                         ; apply gravity force: vy+= 80
    lda sprite_vy
    adc #<(80)
    sta sprite_vy
    lda sprite_vy + 1
    adc #>(80)
    sta sprite_vy + 1
+

    clc                                         ; y += MSB(vy)
    lda sprite_y
    adc sprite_vy + 1
    sta sprite_y
    lda sprite_y + 1
    adc #0
    sta sprite_y + 1

    lda #>(230)                                 ; do not go below bottom
    cmp sprite_y + 1
    bne +
    lda #<(230)
    cmp sprite_y
+   bcs +

    lda #<(230)                                 ; set bottom position
    sta sprite_y
    lda #>(230)
    sta sprite_y + 1

    lda #<($950)                                ; set upwards speed
    sta sprite_vy
    lda #>($950)
    sta sprite_vy + 1

    lda #1                                      ; reverse direction
    sta sprite_ydir

+
    jmp sprite_y_move_done

sprite_y_move_up                                ; move upwards

    lda #>(80)                                  ; handle gravity
    cmp sprite_vy + 1
    bne +
    lda #<(80)
    cmp sprite_vy
+   bcc +
    lda #0                                      ; reverse direction
    sta sprite_ydir
    jmp ++
+

    sec                                         ; apply gravity force
    lda sprite_vy
    sbc #<(80)
    sta sprite_vy
    lda sprite_vy + 1
    sbc #>(80)
    sta sprite_vy + 1

++

    sec                                         ; y -= MSB(vy)
    lda sprite_y
    sbc sprite_vy + 1
    sta sprite_y
    lda sprite_y + 1
    sbc #0
    sta sprite_y + 1

    lda #>(80)                                  ; check top boundary
    cmp sprite_y + 1
    bne +
    lda #<(80)
    cmp sprite_y
+   bcc +

    lda #<(80)                                 ; do not go below bottom
    sta sprite_y
    lda #>(80)
    sta sprite_y + 1

    lda #0                                     ; reverse direction
    sta sprite_ydir
+

sprite_y_move_done
    ;+storew sprite_y, 120

sprite_anim_update                              ; update animation

    lda sprite_anim_counter                     ; check animation delay counter
    cmp sprite_anim_delay
    bcc sprite_anim_update_delay

    +clearb sprite_anim_counter                 ; update animation frame
    lda sprite_anim
    cmp #5                                      ; loop animation frames
    bne +
    +clearb sprite_anim
    jmp sprite_anim_update_end
+
    inc sprite_anim                             ; next animation frame
    jmp sprite_anim_update_end

sprite_anim_update_delay
    inc sprite_anim_counter                     ; increase animation delay counter

sprite_anim_update_end

sprite_sprite_update_end
    rts                                         ; sprite update end


sprite_set_pos_fn ; (reg0: sprite, reg1: x, reg2: y)

    lda #<($d000)                       ; set base address
    sta reg3
    lda #>($d000)
    sta reg3+1

    lda reg0                            ; set offset
    asl                                 ; offset is id * 2
    tay                                 ; now y points to x coords

    lda reg1                            ; store lsb(x)
    sta (reg3),Y
    iny
    lda reg2                            ; store y
    sta (reg3),Y

    ldx reg0                            ; create bit mask from sprite id
    lda #1
    cpx #0
-   beq +
    asl
    dex
    jmp -
+

    ldy #$10                            ; bitmask for msb(x) at $d010
    ldx reg1 + 1                        ; load msb(x) to x
    cpx #0                              ; if (x < 256) then high-byte is zero
    beq +
    ora (reg3),Y                        ; a |= (1<<sprite)
    sta (reg3),Y                        ; store $d010
    jmp ++
+
    eor #$ff                            ; a = ~(1<<sprite)
    sta reg4                            ; store ~(1<<sprite)
    lda (reg3),Y                        ; fetch $d010
    and reg4                            ; clear bit
    sta (reg3),Y                        ; store $d010
++

    rts
