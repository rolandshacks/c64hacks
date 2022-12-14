#pragma once

#include "./system.h"

#include <cstdint>
#include <string.h>

struct sid_info_t {
  const uint16_t load_address;
  const uint16_t init_address;
  const uint16_t play_address;
  const uint16_t num_songs;
  const uint16_t start_song;
  const uint32_t speed;
  const uint8_t* data;
};

extern sid_info_t sid_info;
extern volatile uint8_t __sid_data[];

namespace sys {

class Audio {
    public:
        static void init();
        static inline void update() {
            asm volatile (
                "JSR %0"
                ::
                "n"(sid_info.play_address)
            );
        }
};

}  // namespace sys
