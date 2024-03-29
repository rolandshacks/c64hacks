#include <cstddef>
#include <cstdint>

#include "libcpp64/system.h"

volatile uint8_t& sys::memory(const uint16_t address) {
    return *(reinterpret_cast<address_t>(address));
}

void sys::set_bit(const uint16_t address, uint8_t bit, bool enabled) {
    if (enabled) {
        memory(address) |= (1 << bit);
    } else {
        memory(address) &= ~(1 << bit);
    }
}

[[nodiscard]] bool sys::get_bit(const uint16_t address, uint8_t bit) {
    return ((memory(address) & (1 << bit)) != 0x0);
}

using namespace sys;

bool System::kernalAndBasicDisabled{false};

void System::init() noexcept {
}

void System::disableInterrupts() noexcept {
    asm volatile("sei");
}

void System::enableInterrupts() noexcept {
    asm volatile("cli");
}

void System::disableKernalAndBasic() noexcept {
    kernalAndBasicDisabled = true;

    System::disableInterrupts();

    memory(0xdc0d) = 0x7f;              // disable timer interrupts which can be generated by the two CIA chips
    memory(0xdd0d) = 0x7f;              // kernal uses such an interrupt to flash the cursor and
                                        // scan the keyboard, so we better stop it.

    asm volatile(                       // by reading this two registers we negate any pending CIA irqs.
        "lda $dc0d\n"                   // if we don't do this, a pending CIA irq might occur after
        "lda $dd0d\n"                   // we finish setting up our irq. we don't want that to happen.
    );

    memory(0xd01a) = 0x0;               // clear VIC interrupt mask bits
    memory(0xd019) = 0x0;               // clear VIC interrupt request bits

    memMap(0x5);                        // NO kernel ROM + NO basic ROM + I/O

    System::enableInterrupts();
}

void System::enableKernalAndBasic() noexcept {
    System::disableInterrupts();
    memMap(0x7);                        // kernel ROM + basic ROM + I/O
    System::enableInterrupts();
    kernalAndBasicDisabled = false;
}

void System::memMap(uint8_t bits) noexcept {
    uint8_t memFlags = memory(0x01) & 0xf8;
    memFlags |= (bits & 0x7);
    memory(0x01) = memFlags;
}

// NOLINTNEXTLINE
void System::copyRomCharset(uint8_t* dest, size_t src_offset, size_t char_count) noexcept {
    const uint8_t* src = (const uint8_t*) (0xd000 +  src_offset);

    disableInterrupts();
    uint8_t oldMemFlags = memory(0x01);
    memory(0x1) = (oldMemFlags & 0xfb);  // enable access to Character ROM
                                         // instead of mem-mapped I/O at $d000

    if (0 == char_count) char_count = 256; // default size 2K
    while (char_count) {
        *(dest++) = *(src++); // 8 bytes per character
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        char_count--;
    }

    memory(0x01) = oldMemFlags;

    enableInterrupts();
}

void System::copyCharset(const uint8_t* src, uint8_t* dest, size_t char_count) noexcept {
    while (char_count) {
        *(dest++) = *(src++); // 8 bytes per character
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        *(dest++) = *(src++);
        char_count--;
    }
}

[[nodiscard]] constexpr uint8_t System::get_compiler_standard() noexcept {
    if (__cplusplus == 201703L) return 17;
    if (__cplusplus == 201402L) return 14;
    if (__cplusplus == 201103L) return 11;
    return 0;
}
