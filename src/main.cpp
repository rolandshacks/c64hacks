#include <cstddef>
#include <cstdint>

#include <sys>
using namespace sys;

const int16_t spriteMinX = 192;
const int16_t spriteMaxX = 2591;
const int16_t spriteMaxY = 1847;
const int16_t spriteMaxVY = 80;
const uint8_t spriteMaxFrame = 5;

struct Sprite {

    uint8_t id{0};
    int16_t x{0};
    int16_t y{0};
    int16_t vx{0};
    int16_t vy{0};
    uint8_t xdir{0};
    uint8_t address{0};
    uint8_t animation{0};
    uint8_t animation_delay{0};
    uint8_t animation_counter{0};

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
        if (x <= 0 || y <= 0) {
            Video::setSpritePos(id, 0, 0);
            return;
        }
        Video::setSpritePos(id, x>>3, y>>3);
    }

    inline void updateAnimation() const {
        Video::setSpriteAddress(id, this->address + animation);
    }

};

namespace SpriteBatch {

    const size_t sprite_count = 8;
    Sprite sprites[sprite_count];

    static void init() {

        Video::setSpriteCommonColors(1, 11);

        uint8_t sprite_colors[] = {2,6,2,11,2,4,2,9};

        uint8_t block_index = Video::getSpriteAddress();
        uint8_t i = 0;
        for (auto& sprite : sprites) {
            sprite.id = i;

            auto col = sprite_colors[i];
            sprite.set(true, block_index, col, true);

            sprite.x = (int16_t) (Constants::Width / 3 + i * 300);
            sprite.vx = (int16_t) (25 + i);
            sprite.xdir = 0;

            sprite.y = (int16_t) (- i * 100);
            sprite.vy = (int16_t) (- i * 30);

            sprite.animation_delay = 1 + i/2;

            sprite.updatePos();
            sprite.updateAnimation();

            i++;
        }
    }

    static void update() {

        for (auto& sprite : sprites) {

            if (sprite.animation_counter >= sprite.animation_delay) {
                sprite.animation_counter -= sprite.animation_delay;
                if (sprite.xdir == 0) {
                    if (sprite.animation == spriteMaxFrame) {
                        sprite.animation = 0;
                    } else {
                        sprite.animation++;
                    }
                } else {
                    if (sprite.animation == 0) {
                        sprite.animation = spriteMaxFrame;
                    } else {
                        sprite.animation--;
                    }
                }

            } else {
                sprite.animation_counter++;
            }

            if (sprite.xdir == 0) {
                sprite.x += sprite.vx;
                if (sprite.x > spriteMaxX) {
                    sprite.x = spriteMaxX;
                    sprite.xdir = 1;
                }
            } else {
                sprite.x -= sprite.vx;
                if (sprite.x < spriteMinX) {
                    sprite.x = spriteMinX;
                    sprite.xdir = 0;
                }
            }

            sprite.y += sprite.vy;
            if (sprite.y > spriteMaxY) {
                sprite.y = spriteMaxY;
                sprite.vy = -spriteMaxVY;
            }

            sprite.vy += 3;
            if (sprite.vy > spriteMaxVY) sprite.vy = spriteMaxVY;

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
        auto linePtr = Video::getColorPtr(y);
        while (y < 25) {
            memset((void*) linePtr, star_color[y%3], 40);
            linePtr += (size_t) (40 * step_size);
            y += step_size;
        }
    }

    static void update() {

        static uint8_t y;
        y = stars_y;

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

            if (enable_audio) Audio::init();
            if (enable_sprites) SpriteBatch::init();

            if (enable_irq) {
                auto metrics = Video::metrics();
                Video::enableRasterIrqDebug(enable_raster_debug);
                Video::addRasterSequenceStep(metrics.num_raster_lines - 60, onVerticalBlank);
                Video::enableRasterSequence();
            }

        }

        static void onVerticalBlank() {
            if (enable_audio) Audio::update();
        }

    public:
        static void main() {
            init();

            Video::puts(15, 0, "Hello World", 8);

            for (;;) {
                if (enable_sprites) SpriteBatch::update();
                if (enable_starfield) Starfield::update();
                Video::waitNextFrame();
                if (!enable_irq) onVerticalBlank();
            }
        }
};

int main() {
    Application::main();
    return 0;
}
