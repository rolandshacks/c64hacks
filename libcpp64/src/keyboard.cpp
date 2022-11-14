#include <cstddef>
#include <cstdint>

#include "libcpp64/keyboard.h"

using namespace sys;

void Keyboard::init() noexcept {
    memory(0xDC02) = 0xff;  // CIA1 port A = outputs
    memory(0xDC03) = 0x0;   // CIA1 port B = inputs
}

void Keyboard::store() noexcept {
    memory(0xdc00) = 0b11111110;
    keyboard_buffer[0] = memory(0xdc01);
    memory(0xdc00) = 0b11111101;
    keyboard_buffer[1] = memory(0xdc01);
    memory(0xdc00) = 0b11111011;
    keyboard_buffer[2] = memory(0xdc01);
    memory(0xdc00) = 0b11110111;
    keyboard_buffer[3] = memory(0xdc01);
    memory(0xdc00) = 0b11101111;
    keyboard_buffer[4] = memory(0xdc01);
    memory(0xdc00) = 0b11011111;
    keyboard_buffer[5] = memory(0xdc01);
    memory(0xdc00) = 0b10111111;
    keyboard_buffer[6] = memory(0xdc01);
    memory(0xdc00) = 0b01111111;
    keyboard_buffer[7] = memory(0xdc01);
}

[[nodiscard]] bool Keyboard::getBufferedKeyState(uint8_t keycode) noexcept {
    uint8_t& bits = keyboard_buffer[keycode>>4];
    uint8_t bitnum = (keycode & 0x07);
    return (bits & (1<<bitnum)) == 0x0;
}

[[nodiscard]] bool Keyboard::getKeyState(uint8_t keycode) noexcept {
    memory(0xdc00) = (0b11111111 & ~(1<<(keycode>>4)));
    uint8_t bits = memory(0xdc01);
    uint8_t bitnum = (keycode & 0x07);
    return (bits & (1<<bitnum)) == 0x0;
}
