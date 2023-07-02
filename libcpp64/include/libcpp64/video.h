#pragma once

#include "./system.h"

#include <cstdint>
#include <string.h>

extern const size_t sprites_size;
extern const uint8_t sprites[];
extern const unsigned char sprites_col_background;
extern const unsigned char sprites_col_multi1;
extern const unsigned char sprites_col_multi2;
extern const unsigned char sprites_sprite_count;

namespace sys {

enum class GraphicsMode {
    StandardTextMode = 0x0,
    StandardBitmapMode = 0x1,
    MulticolorTextMode = 0x2,
    MulticolorBitmapMode = 0x3,
    ExtendedBackgroundColorMode = 0x4,
    IdleMode = 0x5
};

class Video {

    public:
        struct metrics_t {
            bool is_pal {true};
            uint16_t num_raster_lines{};
            uint8_t frames_per_second{};
            uint8_t millis_per_frame{};
        };

        struct stats_t {
            uint16_t frame_counter{0};
            uint16_t time_seconds{0};
            uint16_t time_millis{0};
            uint16_t time_delta{0};
            uint16_t time_micro_err{0};
        };

    public:
        static void init() noexcept;
        static void setGraphicsMode(GraphicsMode mode) noexcept;
        static void setBank(uint8_t bank) noexcept;
        static void setScreenBase(uint8_t base) noexcept;
        static void setBitmapBase(uint8_t base) noexcept;
        static void setCharacterBase(uint8_t base) noexcept;
        static volatile uint8_t* getBasePtr() noexcept { return (address_t)(vic_base); };
        static volatile uint8_t* getScreenBasePtr() noexcept { return (address_t)(screen_base); };
        static volatile uint8_t* getColorBasePtr() noexcept { return (address_t)(color_base); };
        static volatile uint8_t* getBitmapBasePtr() noexcept { return (address_t)(bitmap_base); };
        static volatile uint8_t* getCharacterBasePtr() noexcept { return (address_t)(char_base); };
        static volatile uint8_t* getCharacterBasePtr(uint8_t base) noexcept { return (address_t)(vic_base + base * 0x800); };
        static volatile uint8_t* getScreenPtr(uint8_t row) noexcept { return (address_t)(row_addresses[row]); };
        static volatile uint8_t* getColorPtr(uint8_t row) noexcept { return (address_t)(col_addresses[row]); };

    public:
        static void setScrollX(uint8_t offset) noexcept;
        static void setScrollY(uint8_t offset) noexcept;

    public:
        static void setSpriteEnabled(uint8_t sprite, bool enabled) noexcept;
        static void setSpriteData(uint8_t sprite, const uint8_t* data) noexcept;
        static void setSpriteAddress(uint8_t sprite, uint8_t block) noexcept;
        static void setSpriteMode(uint8_t sprite, bool multicolor) noexcept;
        static void setSpritePos(uint8_t sprite, uint16_t x, uint16_t y) noexcept;
        static void setSpriteColor(uint8_t sprite, uint8_t color) noexcept;
        static void setSpriteCommonColors(uint8_t colorA, uint8_t colorB) noexcept;
        static uint8_t getSpriteAddress(const uint8_t* data=nullptr) noexcept;
        static void setTextCommonColors(uint8_t colorA, uint8_t colorB) noexcept;

    public:
        static void enableRasterSequence() noexcept;
        static void enableRasterIrq(interrupt_handler_t fn, uint16_t raster_line) noexcept;
        static void setRasterIrqLine(uint16_t line) noexcept;
        static void addRasterSequenceStep(uint16_t line, interrupt_handler_t fn) noexcept;
        static inline uint8_t getCurrentRasterSequenceStep() noexcept { return raster_sequence_step; }
        static void enableRasterIrqDebug(bool enable) noexcept;

        [[nodiscard]] static inline uint16_t getRasterLine() noexcept {
            return (memory(0xd011) & 0x80 >> 7) | memory(0xd012);
        }

        [[nodiscard]] static inline const metrics_t& metrics() noexcept { return metrics_; }
        [[nodiscard]] static inline const volatile stats_t& stats() noexcept { return stats_; }

    public:
        static void clear(uint8_t c = 0x20) noexcept;
        static void fill(uint8_t c, size_t ofs, size_t count) noexcept;
        static void fillColor(uint8_t c, size_t ofs, size_t count) noexcept;

    public:
        [[nodiscard]] static inline uint8_t getBackground() noexcept { return memory(Constants::BackgroundColorRegister); };
        static void inline setBackground(uint8_t col) noexcept { memory(Constants::BackgroundColorRegister) = col; };
        [[nodiscard]] static inline uint8_t getBorder() noexcept { return memory(Constants::BorderColorRegister); };
        static inline void setBorder(uint8_t col) noexcept { memory(Constants::BorderColorRegister) = col; };
        static void inline setMultiBackground(uint8_t col0, uint8_t col1, uint8_t col2, uint8_t col3) noexcept {
            memory(0xd021) = col0;
            memory(0xd022) = col1;
            memory(0xd023) = col2;
            memory(0xd024) = col3;
        };

    public:
        static void puts(uint8_t x, uint8_t y, const char* s) noexcept;
        static void puts(uint8_t x, uint8_t y, const char* s, uint8_t col) noexcept;
        static void putStrCharData(uint8_t x, uint8_t y, const char* data, uint8_t data_ofs, uint8_t col) noexcept;

        static inline void putc(uint8_t x, uint8_t y, uint8_t c) noexcept {
            *((address_t) row_addresses[y] + x) = c;
        }

        static inline void putc(uint8_t x, uint8_t y, uint8_t c, uint8_t col) noexcept {
            *((address_t) row_addresses[y] + x) = c;
            *((address_t) col_addresses[y] + x) = col;
        }

        [[nodiscard]] static inline uint8_t getc(uint8_t x, uint8_t y) noexcept {
            return *((address_t) row_addresses[y] + x);
        }

        static void printNumber(uint8_t x, uint8_t y, uint8_t n) noexcept;
        static void printNumber(uint8_t x, uint8_t y, uint16_t n) noexcept;
        static void printNibble(uint8_t x, uint8_t y, uint8_t n) noexcept;
        static void printHexNumber(uint8_t x, uint8_t y, uint8_t n) noexcept;
        static void printHexNumber(uint8_t x, uint8_t y, uint16_t n) noexcept;

    public:
        __attribute__((interrupt_norecurse))
        static void onRasterInterrupt() noexcept;
        static void onVerticalBlank() noexcept;
        static void waitNextFrame() noexcept;
        static void waitLines(uint16_t lines) noexcept;

    private:
        static void setScreenPtrs() noexcept;
        static void setColorPtrs() noexcept;

    private:
        struct raster_step_t {
            uint16_t line{0xffff};
            interrupt_handler_t fn{nullptr};
        };

    private:
        static metrics_t metrics_;
        static volatile stats_t stats_;
        static volatile uint16_t last_frame_counter_;
        static bool raster_irq_enabled;
        static raster_step_t raster_sequence[8];
        static uint16_t row_addresses[25];
        static uint16_t col_addresses[25];
        static volatile uint8_t raster_sequence_step;
        static uint8_t raster_sequence_step_count;
        static bool raster_irq_debug;
        static uint16_t vic_base;
        static uint16_t screen_base;
        static uint16_t char_base;
        static uint16_t bitmap_base;
        static uint16_t color_base;
        static uint16_t sprite_base;
};

}  // namespace sys
