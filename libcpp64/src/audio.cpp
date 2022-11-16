#include <cstddef>
#include <cstdint>

#include "libcpp64/audio.h"

using namespace sys;

void Audio::init() {

    uint8_t sid_data_ref = __sid_data[0]; // NOLINT

    asm volatile(
        "LDA #$00\n\t"
        "LDY #$00\n\t"
        "JSR %0"
        ::
        "n"(sid_info.init_address),
        "x"((uint8_t) sid_info.start_song)
    );

}
