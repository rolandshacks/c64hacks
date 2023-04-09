#pragma once

#include <cstdint>
#include <string.h>

using address_t = volatile uint8_t*;

namespace sys {

typedef void (*interrupt_handler_t)(void);

volatile uint8_t& memory(const uint16_t address);
void set_bit(const uint16_t address, uint8_t bit, bool enabled);
[[nodiscard]] bool get_bit(const uint16_t address, uint8_t bit);


class Constants {
    public: // Screen constants
        static const uint16_t Width = 320;
        static const uint16_t Height = 200;
        static const uint8_t LeftBorder = 46;
        static const uint8_t RightBorder = 36;

    public: // PAL constants
        static const uint8_t TopBorder = 43;
        static const uint8_t BottomBorder = 40;
        static const uint8_t TopInvisible = 7;
        static const uint8_t BottomInvisible = 13;
        static const uint16_t RasterLines = 312;
        static const uint8_t CyclesPerLine = 63;
        static const uint16_t FirstVBlankLine = 300;
        static const uint16_t LastVBlankLine = 15;

    public: // NTSC constants
        static const uint16_t NtscRasterLines = 263;
        static const uint8_t NtscCyclesPerLine = 65;
        static const uint16_t NtscFirstVBlankLine = 13;
        static const uint16_t NtscLastVBlankLine = 40;

    public:
        static const uint16_t BorderColorRegister = 0xd020;
        static const uint16_t BackgroundColorRegister = 0xd021;
        static const uint16_t ColorRAM = 0xd800; // ..0xdbe7

    public:
        static const uint16_t KERNAL_IRQ = 0x0314;
        static const uint16_t HARDWARE_IRQ = 0xfffe;

};

class System {

    public:
        static void init() noexcept;

    public:
        static void disableInterrupts() noexcept;
        static void enableInterrupts() noexcept;
        static void disableKernalAndBasic() noexcept;
        static void enableKernalAndBasic() noexcept;
        static bool isKernalAndBasicDisabled() noexcept { return kernalAndBasicDisabled; }
        static void memMap(uint8_t bits) noexcept;
        static void copyRomCharset(uint8_t* dest, size_t src_offset=0, size_t char_count=0) noexcept;
        static void copyCharset(const uint8_t* src, uint8_t* dest, size_t char_count) noexcept;

    public:
        [[nodiscard]] static constexpr uint8_t get_compiler_standard() noexcept;

    public:
        static bool kernalAndBasicDisabled;
};

}  // namespace sys
