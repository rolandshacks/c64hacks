#include <cstddef>
#include <cstdint>

#include <sys>
using namespace sys;

struct Sprite {

    uint8_t id{0};
    int16_t x{0};
    int16_t y{0};
    int16_t vx{0};
    int16_t vy{0};
    uint8_t address;
    uint8_t animation{0};

    Sprite()
    {}

    inline void set(uint8_t enabled, uint8_t address, uint8_t color, bool multicolor) {
        this->address = address;
        Video::setSpriteAddress(id, address);
        Video::setSpriteEnabled(id, enabled);
        Video::setSpriteMode(id, multicolor);
        Video::setSpriteColor(id, color);
    }

    inline void updatePos() const {
        uint16_t sx = (x > 0) ? x : 0;
        uint16_t sy = (y > 0) ? y : 0;
        Video::setSpritePos(id, sx>>3, sy>>3);
    }

    inline void updateAnimation() const {
        Video::setSpriteAddress(id, this->address + (animation>>3));
    }

};

namespace SpriteBatch {

    Sprite sprites[8];
    const size_t sprite_count = sizeof(sprites)/sizeof(sprites[0]);

    static void init() {

        Video::setSpriteCommonColors(1, 11);

        uint8_t sprite_colors[] = {2,6,2,11,2,4,2,9};

        auto& metrics = Video::metrics();

        uint8_t block_index = Video::getSpriteAddress();
        uint8_t i = 0;
        for (auto& sprite : sprites) {
            sprite.id = i;

            auto col = sprite_colors[i];
            sprite.set(true, block_index, col, true);

            sprite.x = Constants::Width / 3 + i * 300;
            sprite.y = - i * 100;
            sprite.vx = 25 + i;
            sprite.vy = - i * 30;
            sprite.updatePos();
            sprite.updateAnimation();

            i++;
        }
    }

    static void update() {

        for (auto& sprite : sprites) {

            sprite.x += sprite.vx;
            if (sprite.x > 2591) {
                sprite.x = 2591;
                sprite.vx = -sprite.vx;
            } else if (sprite.x < 192) {
                sprite.x = 192;
                sprite.vx = -sprite.vx;
            }

            sprite.y += sprite.vy;
            if (sprite.y > 1847) {
                sprite.y = 1847;
                sprite.vy = -80;
            }

            sprite.vy += 3;
            if (sprite.vy > 80) sprite.vy = 80;

            uint8_t da = 3 + (sprite.id % 3);
            if (sprite.vx >= 0) {
                sprite.animation = (sprite.animation + da) % 48;
            } else {
                sprite.animation = (sprite.animation + 48 - da) % 48;
            }

        }

    }

    static void sync() {
        for (const auto& sprite : sprites) {
            sprite.updatePos();
            sprite.updateAnimation();
        }
    }

} // namespace

namespace Starfield {

    struct Star {
        uint8_t x;
        uint8_t shift;
        uint8_t speed;
    };

    const size_t num_stars = 12;
    Star stars[num_stars] = {};
    const uint8_t star_char_base = 0x21; // 0x21..0x28
    const uint8_t star_color[] = { 0xf, 0xc, 0x1 };
    const uint8_t stars_y = 2;
    const uint8_t step_size = 2;

    static void init() {
        // prepare charset
        auto charset = (uint8_t*) Video::getCharacterBasePtr();
        for (int i=0; i<8; i++) {
            auto ptr = charset + (star_char_base + i) * 8;
            memset(ptr, 0, 8);
            *ptr = (1<<i);
        }

        // init stars
        for (int i=0; i<num_stars; i++) {
            stars[i].x = sys::rand() % 104; // 40+64
            stars[i].shift = 0;
            stars[i].speed = 1 + (i%3);
        }

        // init color buffer
        uint8_t y = stars_y;
        uint8_t* linePtr = (uint8_t*) Video::getColorBasePtr() + y * 40;
        while (y < 25) {
            memset(linePtr, star_color[y%3], 40);
            linePtr += 40 * step_size;
            y += step_size;
        }
    }

    static void update() {

        uint8_t y = stars_y;

        for (auto& star : stars) {
            if (y >= 25) break;

            if (star.x >= 40) {
                star.x--;
                y += step_size;
                continue;
            }

            star.shift += star.speed;
            if (star.shift >= 8) {
                star.shift -= 8;
                Video::putc(star.x, y, 0x20);
                if (star.x == 0) {
                    star.x = 40 + (sys::rand()>>2);
                    y += step_size;
                    continue;
                } else {
                    star.x--;
                }
            }

            Video::putc(star.x, y, star_char_base + star.shift);
            y += step_size;

        }
    }

} // namespace

class Application {
    private:
        static const bool enable_irq = true;
        static const bool enable_audio = true;
        static const bool enable_sprites = true;
        static const bool enable_starfield = true;
        static const bool enable_raster_debug = false;

    private:
        static void init() {
            System::init();
            System::disableKernalAndBasic();

            Keyboard::init();
            Video::init();
            Video::setBank(2);
            Video::setGraphicsMode(GraphicsMode::StandardTextMode);
            Video::setScreenBase(0x1);

            System::copyCharset((uint8_t*) Video::getCharacterBasePtr(1));
            Video::setCharacterBase(0x1);

            if (enable_starfield) Starfield::init();

            Video::clear();
            Video::setBackground(0);
            Video::setBorder(0);

            if (enable_irq) {
                auto metrics = Video::metrics();
                Video::enableRasterIrqDebug(enable_raster_debug);
                Video::addRasterSequenceStep(metrics.num_raster_lines - 70, onVerticalBlank);
                Video::enableRasterIrq();
            }

            if (enable_sprites) SpriteBatch::init();
            if (enable_audio) Audio::init();
        }

        static void onVerticalBlank() {
            if (enable_audio) Audio::update();
            if (enable_sprites) SpriteBatch::sync();
            if (enable_starfield) Starfield::update();
        }

    public:
        static void main() {
            init();

            Video::puts(15, 0, "Hello World", 8);

            for (;;) {
                if (enable_sprites) SpriteBatch::update();
                Video::waitNextFrame();
                if (!enable_irq) onVerticalBlank();
            }
        }
};

int main() {
    Application::main();
    return 0;
}
