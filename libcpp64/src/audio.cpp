#include <cstddef>
#include <cstdint>
#include <string.h>

#include "libcpp64/audio.h"

extern const uint8_t music[];
extern "C" void init_audio(void);
extern "C" void update_audio(void);

asm (
  ".text\n"
  ".global init_audio\n"
  "init_audio:\n"
  "  lda #0\n"
  "  ldy #0\n"
  "  ldx #$01\n"
  "  jsr $5000\n"
  "  rts\n"
  ".global update_audio\n"
  "update_audio:\n"
  "  jsr $5003\n"
  "  rts\n"
);

using namespace sys;

void Audio::init() {

    // copy sid data to load address
    const void* srcAddress = (const void*) music;
    void* loadAddress = (void*) 0x5000;
    if (loadAddress != srcAddress) {
        memcpy(loadAddress, srcAddress, 2460);
    }

    init_audio();
}

void Audio::update() {
{
    update_audio();
}
}
