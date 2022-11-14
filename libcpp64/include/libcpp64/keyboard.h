#pragma once

#include "./system.h"

#include <cstdint>
#include <string.h>

namespace sys {

class Keyboard {
    public:
        static void init() noexcept;
        static void store() noexcept;
        [[nodiscard]] static bool getBufferedKeyState(uint8_t keycode) noexcept;
        [[nodiscard]] static bool getKeyState(uint8_t keycode) noexcept;

    public:
        // CIA1 PA|PB
        static const uint8_t KEY_CURSOR_DOWN = 0x07;
        static const uint8_t KEY_CURSOR_RIGHT = 0x02;
        static const uint8_t KEY_LSHIFT = 0x17;
        static const uint8_t KEY_STOP = 0x77;
        static const uint8_t KEY_SPACE = 0x74;

        static const uint8_t KEY_A = 0x12;
        static const uint8_t KEY_B = 0x43;

    private:
        static uint8_t keyboard_buffer[8];

};

}  // namespace sys
