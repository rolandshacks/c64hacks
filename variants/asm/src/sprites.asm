; -------------------------------------------------
; Sprites
; -------------------------------------------------

; -------------------------------------------------
; sprite data structures
; -------------------------------------------------

.sprite_colors
    !byte 2, 6, 2, 11, 2, 4, 2, 9

.sprites
    +sprite_table sprite_count

; references to sprite info
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

; -------------------------------------------------
; sprite init
; -------------------------------------------------

sprite_init
    +memcpy video_vic_base, sprites, sprites_end - sprites
    rts

; -------------------------------------------------
; update sprite table
; -------------------------------------------------

sprites_update                                  ; update sprites
    !for id, 0, sprite_count-1 {
        !set sprite = .sprites + id * sprite_info_size

        +moveb sprite_id              , sprite + sprite_field_id
        +movew sprite_x               , sprite + sprite_field_x
        +moveb sprite_vx              , sprite + sprite_field_vx
        +moveb sprite_vxsub           , sprite + sprite_field_vxsub
        +movew sprite_y               , sprite + sprite_field_y
        +movew sprite_vy              , sprite + sprite_field_vy
        +moveb sprite_xdir            , sprite + sprite_field_xdir
        +moveb sprite_ydir            , sprite + sprite_field_ydir
        +moveb sprite_anim            , sprite + sprite_field_anim
        +moveb sprite_anim_counter    , sprite + sprite_field_anim_counter
        +moveb sprite_anim_delay      , sprite + sprite_field_anim_delay
        +moveb sprite_vx_counter      , sprite + sprite_field_vx_counter

        jsr audio_update
        jsr sprite_update

        +moveb sprite + sprite_field_id             , sprite_id
        +movew sprite + sprite_field_x              , sprite_x
        +moveb sprite + sprite_field_vx             , sprite_vx
        +moveb sprite + sprite_field_vxsub          , sprite_vxsub
        +movew sprite + sprite_field_y              , sprite_y
        +movew sprite + sprite_field_vy             , sprite_vy
        +moveb sprite + sprite_field_xdir           , sprite_xdir
        +moveb sprite + sprite_field_ydir           , sprite_ydir
        +moveb sprite + sprite_field_anim           , sprite_anim
        +moveb sprite + sprite_field_anim_counter   , sprite_anim_counter
        +moveb sprite + sprite_field_anim_delay     , sprite_anim_delay
        +moveb sprite + sprite_field_vx_counter     , sprite_vx_counter
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

    +addbv sprite_vx_counter, sprite_vxsub      ; handle sub-pixel move
    +cmpb sprite_vx_counter, $80
    bcs +
    +subb sprite_vx_counter, $80
    +addwb sprite_x, 1
+

    +addwbv sprite_x, sprite_vx                 ; increase x
    +cmpw sprite_x, 322                         ; check right border
    bcs +
    +storew sprite_x, 322                       ; do not go beyond
    +storeb sprite_xdir, 1                      ; reverse direction
+
    jmp sprite_x_move_done

sprite_x_move_left                              ; move left

    +addbv sprite_vx_counter, sprite_vxsub      ; handle sub-pixel move
    +cmpb sprite_vx_counter, $80
    bcs +
    +subb sprite_vx_counter, $80
    +subwb sprite_x, 1
+

    +subwbv sprite_x, sprite_vx                 ; decrease x
    +cmpw sprite_x, 24                          ; check left border
    bcc +
    +storew sprite_x, 24                        ; do not go beyond
    +storeb sprite_xdir, 0                      ; reverse direction
+
    jmp sprite_x_move_done

sprite_x_move_done                              ; done with x

sprite_y_move                                   ; update sprite y
    lda sprite_ydir                             ; check y direction
    bne sprite_y_move_up

sprite_y_move_down                              ; move down

    +cmpw sprite_vy, $1000                      ; handle gravity
    bcc +
    +addw sprite_vy, 80                         ; apply gravity force
+

    +storew reg0, 0                            ; increase y
    +moveb reg0, sprite_vy+1
    +addwv sprite_y, reg0

    +cmpw sprite_y, 230                         ; check bottom boundary
    bcs +
    +storew sprite_y, 230                       ; do not go below bottom
    +storew sprite_vy, $950                     ; set upwards speed
    +storeb sprite_ydir, 1                      ; reverse direction
+
    jmp sprite_y_move_done

sprite_y_move_up                                ; move upwards
    +cmpw sprite_vy, 80                         ; handle gravity
    bcc +
    +storeb sprite_ydir, 0                      ; reverse direction
    jmp ++
+
    +subw sprite_vy, 80                         ; apply gravity force
++

    +storew reg0,0                             ; update sprite y
    +moveb reg0, sprite_vy+1
    +subwv sprite_y, reg0

    +cmpw sprite_y, 80                          ; check top boundary
    bcc +
    +storew sprite_y, 80                        ; do not go above
    +storeb sprite_ydir, 0                      ; reverse direction
+

sprite_y_move_done

    ;+storew sprite_y, 120

    +sprite_set_pos sprite_id, sprite_x, sprite_y   ; set sprite position registers

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
    +sprite_set_data sprite_id, sprite_anim     ; update sprite data registers

sprite_sprite_update_end
    rts                                         ; sprite update end

sprite_set_pos_fn ; (reg0: sprite, reg1: x, reg2: y)

    +storew reg3, $d000              ; x-register

    +addbv reg3, reg0                ; add (sprite-id*2) bytes as offset to x-register
    +addbv reg3, reg0

    +movew reg4, reg3               ; y-register
    +incw reg4

    ldy #0
    lda reg1,y                       ; store x
    sta (reg3),y

    lda reg1+1,y
    sta reg7                          ; store high-byte from x

    ldy #0
    lda reg2,y                       ; store y
    sta (reg4),y

    ldx reg0                            ; create bit mask from sprite id
    lda #1
    cpx #0
-   beq +
    asl
    dex
    jmp -
+
    sta reg5                            ; store (1<<sprite)
    eor #$ff
    sta reg6                            ; store ~(1<<sprite)

    lda $d010                           ; clear bit
    and reg6

    ldx reg7
    cpx #0                              ; if (x < 256 - high-byte is zero)
    beq +
    ora reg5
+

    sta $d010

    rts
