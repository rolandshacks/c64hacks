#include <cstddef>
#include <cstdint>
#include <string.h>

#include "libcpp64/audio.h"

extern const uint8_t music[];
extern const size_t music_size;
extern const unsigned short music_load_address;
extern const unsigned short music_init_address;
extern const unsigned short music_play_address;
extern const unsigned short music_num_songs;
extern const unsigned char music_start_song;

extern "C" void init_audio(void);
extern "C" void update_audio(void);

asm (
  ".text\n"

  ".global init_audio\n"
  "init_audio:\n"                       // called once

  // self-modify init JSR jump address
  "  lda music_init_address\n"          // load init address hi
  "  sta 0f+1\n"                        // patch JSR address
  "  lda music_init_address+1\n"        // load init address lo
  "  sta 0f+2\n"                        // patch JSR address

  // self-modify update JSR jump address
  "  lda music_play_address\n"          // load play address hi
  "  sta 1f+1\n"                        // patch JSR address
  "  lda music_play_address+1\n"        // load play address lo
  "  sta 1f+2\n"                        // patch JSR address

  // call init
  "  ldx music_start_song\n"            // get tune number
  "  dex\n"                             // zero-based
  "  txa\n"                             // store tune number to register A
  "  ldx #0\n"                          // clear register X
  "  ldy #0\n"                          // clear register Y
  "0:\n"
  "  jsr $5000\n"                       // jsr, address will be overwritten
  "  rts\n"                             // return

  ".global update_audio\n"
  "update_audio:\n"                     // called every cycle

  // call update
  "1:\n"
  "  jsr $5003\n"                       // jsr, address will be overwritten
  "  rts\n"                             // return
);

using namespace sys;

void Audio::init() {

    // copy sid data to load address
    const void* srcAddress = (const void*) music;
    void* loadAddress = (void*) music_load_address;
    if (loadAddress != srcAddress) {
        memcpy(loadAddress, srcAddress, music_size);
    }

    init_audio();
}

void Audio::update() {
{
    update_audio();
}
}
