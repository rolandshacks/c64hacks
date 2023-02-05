#include <cstddef>
#include <cstdint>
#include <string.h>

#include "libcpp64/audio.h"

extern "C" void init_audio(void);
extern "C" void update_audio(void);

using namespace sys;

void Audio::init() {

    // copy sid data to load address
    const void* srcAddress = (const void*) sid_data;
    void* loadAddress = (void*) sid_info.load_address;
    if (loadAddress != srcAddress) {
        memcpy(loadAddress, srcAddress, sid_info.size);
    }

    init_audio();

    /*
    asm volatile(
        "LDA #$00\n\t"
        "LDY #$00\n\t"
        "JSR %0"
        ::
        "n"(sid_info.init_address),
        "x"((uint8_t) sid_info.start_song)
    );
    */

}

void Audio::update() {
 {
    update_audio();

    /*
    asm volatile (
        "jsr %0\n"
        ::
        "n"(sid_info.play_address)
    );
    */
}   
}