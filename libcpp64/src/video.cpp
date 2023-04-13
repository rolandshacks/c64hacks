#include <cstddef>
#include <cstdint>
#include <string.h>

#include "libcpp64/video.h"

using namespace sys;

Video::metrics_t Video::metrics_{};
volatile Video::stats_t Video::stats_{};
volatile uint16_t Video::last_frame_counter_{0xffff};
bool Video::raster_irq_enabled{false};
Video::raster_step_t Video::raster_sequence[8]{};
uint16_t Video::row_addresses[25]{};
uint16_t Video::col_addresses[25]{};
volatile uint8_t Video::raster_sequence_step{0};
uint8_t Video::raster_sequence_step_count{0};
bool Video::raster_irq_debug{false};

uint16_t Video::vic_base    = 0x0;
uint16_t Video::screen_base = 0x400;
uint16_t Video::char_base   = 0x1000;
uint16_t Video::bitmap_base = 0x2000;
uint16_t Video::color_base  = 0xd800;
uint16_t Video::sprite_base = 0x400 + 0x03f8;

void Video::init() noexcept {

    uint8_t acc=0x0;
    asm volatile (
        "pha\n"
        "w0: lda $d012\n"
        "w1: cmp $d012\n"
        "beq w1\n"
        "bmi w0\n"
        "pla\n"
        : "=a" (acc)
        :
    );
    metrics_.num_raster_lines = 256 + acc + 1;

    if (metrics_.num_raster_lines > 300) {
        // PAL = 312 (63 cycles per line)
        metrics_.is_pal = true;
        metrics_.num_raster_lines = 312;
        metrics_.frames_per_second = 50;
        metrics_.millis_per_frame = 20;
    } else {
        // NTSC = 263 or 262 (65/64 cycles per line)
        metrics_.is_pal = false;
        metrics_.num_raster_lines = 262;
        metrics_.frames_per_second = 60;
        metrics_.millis_per_frame = 16;
    }

    raster_sequence_step = 0;
    raster_sequence_step_count = 0;

    setScreenPtrs();
    setColorPtrs();
}

void Video::setBank(uint8_t bank) noexcept {
    // bank 0: bits 11:     0-16383 ($0000-$3FFF)
    // bank 1: bits 10: 16384-32767 ($4000-$7FFF)
    // bank 2: bits 01: 32768-49151 ($8000-$BFFF)
    // bank 3: bits 00: 49152-65535 ($C000-$FFFF)

    uint8_t flags = memory(0xdd00);
    flags = (flags & 0xfc) | (3 - (bank & 0x03));

    memory(0xdd02) = 0b00000011; // enable CIA port A write
    memory(0xdd00) = flags; // write bank settings

    vic_base = bank * 0x4000;
    screen_base = (screen_base & 0x3fff) + vic_base;
    char_base = (char_base & 0x3fff) + vic_base;
    bitmap_base = (bitmap_base & 0x3fff) + vic_base;
    sprite_base = screen_base + 0x03f8;

    setScreenPtrs();

    size_t sprite_data_size = 1024; // copy 16 sprites (just use 1K as default)
    memcpy((void*) vic_base, (const void*) sprites, sprite_data_size);

}

void Video::setScreenPtrs() noexcept {
    for (uint8_t row=0; row<25; row++) {
        row_addresses[row] = screen_base + row * 40;
    }
}

void Video::setColorPtrs() noexcept {
    for (uint8_t row=0; row<25; row++) {
        col_addresses[row] = color_base + row * 40;
    }
}

void Video::setScreenBase(uint8_t base) noexcept {
    uint8_t flags = memory(0xd018) & 0x0f;
    flags |= ((base & 0x0f) << 4); // 4 bits
    memory(0xd018) = flags;
    screen_base = vic_base + base * 0x400;
    sprite_base = screen_base + 0x03f8;

    setScreenPtrs();
}

void Video::setBitmapBase(uint8_t base) noexcept {
    set_bit(0xd018, 3, base!=0x0);
    bitmap_base = vic_base + ((base != 0x0) ? 0x2000 : 0x0);
}

void Video::setCharacterBase(uint8_t base) noexcept {
    uint8_t flags = memory(0xd018) & 0xf1;
    flags |= ((base & 0x7) << 1);
    memory(0xd018) = flags;
    char_base = vic_base + base * 0x800;
}

void Video::setGraphicsMode(GraphicsMode mode) noexcept {
    uint8_t flags0 = memory(0xd011)&0x9f;
    uint8_t flags1 = memory(0xd016)&0xef;

    switch (mode) {
        case GraphicsMode::StandardBitmapMode:
            flags0 |= 0x20; // bitmap flag
            break;
        case GraphicsMode::MulticolorTextMode:
            flags1 |= 0x10; // multi-color flag
            break;
        case GraphicsMode::MulticolorBitmapMode:
            flags0 |= 0x20; // bitmap flag
            flags1 |= 0x10; // multi-color flag
            break;
        case GraphicsMode::ExtendedBackgroundColorMode:
            flags0 |= 0x40; // ecm flag
            break;
        default:
            break;
    }

    memory(0xd011) = flags0;
    memory(0xd016) = flags1;
}

void Video::setScrollX(uint8_t offset) noexcept {
    uint8_t flags = memory(0xd016);
    flags = (flags & 0xf8) | (offset & 0x03);
    memory(0xd016) = flags;
}

void Video::setScrollY(uint8_t offset) noexcept {
    uint8_t flags = memory(0xd011);
    flags = (flags & 0xf8) | (offset & 0x03);
    memory(0xd011) = flags;
}

void Video::enableRasterSequence() noexcept {

    raster_irq_enabled = true;

    System::disableInterrupts();        // set interrupt flag, disable all maskable IRQs

    memory(0xd01a) = 0x01;              // tell VICII to generate a raster interrupt

    uint16_t rasterLineStop = (raster_sequence_step_count > 0) ? raster_sequence[0].line : metrics_.num_raster_lines - 1;
    setRasterIrqLine(rasterLineStop);

    interrupt_handler_t* irq_address = reinterpret_cast<interrupt_handler_t*>(
        System::isKernalAndBasicDisabled() ? Constants::HARDWARE_IRQ : Constants::KERNAL_IRQ
    );

    *irq_address = onRasterInterrupt;

    System::enableInterrupts();         // clear interrupt flag, allowing the CPU to respond to interrupt requests

}

void Video::enableRasterIrq(interrupt_handler_t fn, uint16_t raster_line) noexcept {

    raster_irq_enabled = true;

    System::disableInterrupts();        // set interrupt flag, disable all maskable IRQs

    memory(0xd01a) = 0x01;              // tell VICII to generate a raster interrupt

    setRasterIrqLine(raster_line);

    interrupt_handler_t* irq_address = reinterpret_cast<interrupt_handler_t*>(
        System::isKernalAndBasicDisabled() ? Constants::HARDWARE_IRQ : Constants::KERNAL_IRQ
    );

    *irq_address = fn;

    System::enableInterrupts();         // clear interrupt flag, allowing the CPU to respond to interrupt requests

}

void Video::setRasterIrqLine(uint16_t line) noexcept {
    memory(0xd012) = (uint8_t) (line & 0x00ff);
    set_bit(0xd011, 7, ((line & 0xff00)!=0x0));
}

void Video::addRasterSequenceStep(uint16_t line, interrupt_handler_t fn) noexcept {
    if (raster_sequence_step_count >= sizeof(raster_sequence)/sizeof(raster_sequence[0])) return;

    if (line == 0xffff) {
        line = metrics_.num_raster_lines - Constants::BottomInvisible;
    }

    auto& entry = raster_sequence[raster_sequence_step_count++];

    entry.line = line;
    entry.fn = fn;

    if (1 == raster_sequence_step_count) {
        setRasterIrqLine(line);
    }
}

void Video::enableRasterIrqDebug(bool enable) noexcept {
    raster_irq_debug = enable;
}

__attribute__((interrupt_norecurse))
void Video::onRasterInterrupt() noexcept {

    static uint8_t border;

    if (raster_irq_debug) {
        border = Video::getBorder();
        Video::setBorder(border+1);
    }

    const auto& entry = raster_sequence[raster_sequence_step];

    if (raster_sequence_step_count < 2) {
        onVerticalBlank();
    } else {
        raster_sequence_step = raster_sequence_step + 1;
        if (raster_sequence_step >= raster_sequence_step_count) {
            onVerticalBlank();
            raster_sequence_step = 0;
        }

        const auto& next_entry = raster_sequence[raster_sequence_step];
        setRasterIrqLine(next_entry.line);
    }

    if (nullptr != entry.fn) {
        entry.fn();
    }

    if (raster_irq_debug) {
        Video::setBorder(border);
    }

    memory(0xd019) = 0xff; // ACK irq, clear VIC irq flag
}

void Video::onVerticalBlank() noexcept {

    stats_.time_delta = metrics_.millis_per_frame;

    if (!metrics_.is_pal) {
        stats_.time_micro_err = stats_.time_micro_err + 667; // microseconds missing from 1000/60
        if (stats_.time_micro_err >= 1000) {
            stats_.time_micro_err = stats_.time_micro_err - 1000;
            stats_.time_delta = stats_.time_delta + 1;
        }
    }

    stats_.time_millis = stats_.time_millis + stats_.time_delta;
    if (stats_.time_millis >= 1000) {
        stats_.time_seconds = stats_.time_seconds+ 1;
        stats_.time_millis = stats_.time_millis + 1000;
    }

    stats_.frame_counter = stats_.frame_counter + 1;
}

void Video::waitNextFrame() noexcept {

    if (raster_irq_enabled) {
        while (last_frame_counter_ == stats_.frame_counter) {}
        last_frame_counter_ = stats_.frame_counter;
        return;
    }

    uint16_t line = getRasterLine();
    if (line >= 240) { while (getRasterLine() > 80) {}; }
    while (getRasterLine() < 240) {};

    onVerticalBlank();
}

void Video::waitLines(uint16_t lines) noexcept {
    while (lines > 0) {
        lines--;
        uint8_t line = memory(0xd012);
        while (line == memory(0xd012)) {};
    }
}

void Video::clear(uint8_t c) noexcept {
    __memset((char*) ((address_t)(screen_base)), c, 1000);
}

void Video::fill(uint8_t c, size_t ofs, size_t count) noexcept {
    __memset((char*) ((address_t)(screen_base + ofs)), c, count);
}

void Video::fillColor(uint8_t c, size_t ofs, size_t count) noexcept {
    __memset((char*) ((address_t)(color_base + ofs)), c, count);
}

void Video::setTextCommonColors(uint8_t colorA, uint8_t colorB) noexcept {
    memory(0xd022) = colorA; // color of "01"
    memory(0xd023) = colorB; // color 0f "10"
}

uint8_t char_to_screencode(char c) {

    uint8_t s = (uint8_t) c;
    if (c >= 'A' && c <= 'Z') s = (uint8_t) (1+c-'A');
    else if (c >= 'a' && c <= 'z') return (uint8_t) (1+c-'a');
    else if (c >= '0' && c <= '9') return (uint8_t) (0x30+c-'0');

    return s;
}

void Video::puts(uint8_t x, uint8_t y, const char* s) noexcept {
    auto ptr = getScreenPtr(y) + x;
    while (*s) {
        *(ptr++) = char_to_screencode(*(s++));
    }
}

void Video::putStrCharData(uint8_t x, uint8_t y, const char* data, uint8_t data_ofs, uint8_t col) noexcept {
    auto ptr = getScreenPtr(y) + x;
    auto ptr_col = getColorPtr(y) + x;
    while (*data) {
        *(ptr++) = char_to_screencode(*(data++)) + data_ofs;
        *(ptr_col++) = col;
    }
}

void Video::puts(uint8_t x, uint8_t y, const char* s, uint8_t col) noexcept {
    auto ptr = getScreenPtr(y) + x;
    auto ptr_col = getColorPtr(y) + x;
    while (*s) {
        *(ptr++) = char_to_screencode(*(s++));
        *(ptr_col++) = col;
    }
}

void Video::printNumber(uint8_t x, uint8_t y, uint8_t n) noexcept {
    uint16_t addr  = row_addresses[y] + x;
    uint8_t digit = 3;
    while (digit > 0 && n > 0) {
        memory(addr+digit - 1) = 0x30 + (n%10);
        n /= 10;
        digit--;
    }

    while (digit > 0) {
        memory(addr+digit - 1) = 0x20;
        digit--;
    }
}

void Video::printNumber(uint8_t x, uint8_t y, uint16_t n) noexcept {
    uint16_t addr  = row_addresses[y] + x;
    uint8_t digit = 5;
    while (digit > 0 && n > 0) {
        memory(addr+digit - 1) = 0x30 + (n%10);
        n /= 10;
        digit--;
    }

    while (digit > 0) {
        memory(addr+digit - 1) = 0x20;
        digit--;
    }
}

void Video::printNibble(uint8_t x, uint8_t y, uint8_t n) noexcept {
    uint16_t addr  = row_addresses[y] + x;
    if (n<10) memory(addr) = 0x30 + n;
    else memory(addr) = 0x1 + (n-10);
}

void Video::printHexNumber(uint8_t x, uint8_t y, uint8_t n) noexcept {
    printNibble(x+0, y, n>>4);
    printNibble(x+1, y, n&0xf);
}

void Video::printHexNumber(uint8_t x, uint8_t y, uint16_t n) noexcept {
    printNibble(x+0, y, (uint8_t) (n>>12));
    printNibble(x+1, y, (uint8_t) (n>>8)&0xf);
    printNibble(x+2, y, (uint8_t) (n>>4)&0xf);
    printNibble(x+3, y, (uint8_t) n&0xf);
}

void Video::setSpriteEnabled(uint8_t sprite, bool enabled) noexcept {
    set_bit(0xd015, sprite, enabled);
}

void Video::setSpriteMode(uint8_t sprite, bool multicolor) noexcept {
    set_bit(0xd01c, sprite, multicolor);
}

uint8_t Video::getSpriteAddress(const uint8_t* data) noexcept {
    if (nullptr == data) return (uint8_t) 0;
    uint8_t block = (uint8_t) ((reinterpret_cast<uint16_t>(data) - vic_base) / 64);
    return block;
}

void Video::setSpriteAddress(uint8_t sprite, uint8_t block) noexcept {
    memory(sprite_base + sprite) = block;
}

void Video::setSpriteData(uint8_t sprite, const uint8_t* data) noexcept {
    setSpriteAddress(sprite, getSpriteAddress(data));
}

void Video::setSpritePos(uint8_t sprite, uint16_t x, uint16_t y) noexcept {
    static uint16_t addr;
    addr = 0xd000 + (sprite << 1);
    *(reinterpret_cast<uint16_t*>(addr)) = ((y&0xff)<<8)|(x&0xff);
    set_bit(0xd010, sprite, (x&0xff00)!=0x0);
}

void Video::setSpriteColor(uint8_t sprite, uint8_t color) noexcept {
    memory(0xd027 + sprite) = color;
}

void Video::setSpriteCommonColors(uint8_t colorA, uint8_t colorB) noexcept {
    memory(0xd025) = colorA;
    memory(0xd026) = colorB;
}
