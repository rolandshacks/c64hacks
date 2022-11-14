#include <cstddef>
#include <cstdint>

#include <sys>

using namespace sys;

const bool enable_irq = true;
const bool enable_audio = true;
const bool enable_sprites = true;
const bool enable_starfield = true;

static const uint8_t random_numbers[] = { // pre-randomize 256 8-bit integers
    203,22,77,162,177,233,222,231,130,85,19,117,28,206,23,200,118,217,29,207,
    138,41,174,201,224,52,235,133,208,108,11,168,226,199,91,99,123,170,160,1,
    83,111,150,102,161,8,127,53,13,253,164,70,191,244,4,49,68,135,112,82,96,
    128,27,64,35,151,140,247,234,227,209,66,51,129,169,71,182,107,189,42,89,
    192,69,17,60,149,213,184,57,167,12,95,79,0,47,219,134,251,113,242,195,21,
    45,147,54,121,171,176,109,10,202,126,14,50,6,122,146,241,238,30,198,196,72,
    211,90,194,225,58,61,142,59,239,31,158,103,76,143,136,152,73,9,65,155,188,
    116,145,74,120,166,157,16,24,94,144,119,163,255,100,175,228,63,78,250,36,44,
    173,104,179,221,88,232,114,204,220,141,86,5,67,80,110,214,40,187,223,252,26,
    7,125,218,115,3,230,248,38,240,181,180,137,39,92,186,75,159,154,156,34,178,
    148,37,215,246,131,55,105,15,245,62,81,243,172,193,237,25,33,212,98,216,32,
    236,46,183,197,18,185,249,101,48,210,20,87,124,43,106,93,132,153,139,84,205,
    254,229,56,165,97,190,2
};

uint8_t rnd_index = 0;
static inline uint8_t getRandomNumber() {
    return random_numbers[rnd_index++];
}

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

Sprite sprites[8];
const size_t sprite_count = sizeof(sprites)/sizeof(sprites[0]);

uint8_t star_char[] = { 0x21, 0x22, 0x23 };
uint8_t star_mask[] = { 0x1, 0x1, 0x1 };
uint8_t star_color[] = { 0xf, 0xc, 0x1 };
uint16_t star_x[12] = {};
const size_t num_stars = sizeof(star_x)/sizeof(star_x[0]);

void initStarfield() {
    auto charset = (uint8_t*) Video::getCharacterBasePtr();
    auto ptr = charset + star_char[0] * 8;
    memset(ptr, 0x0, 8*3); // clear star characters

    for (int i=0; i<num_stars; i++) {
        star_x[i] = getRandomNumber() % 80;
    }

    memset((void*) Video::getColorBasePtr(), 0x1, 40*25); // white starfield
}

void updateStarfield() {

    auto charset = (uint8_t*) Video::getCharacterBasePtr();
    auto ptr = charset + star_char[0] * 8;

    uint8_t delta = 1;

    for (int layer=0; layer<3; layer++) {
        uint8_t& mask = star_mask[layer];
        uint8_t& bits = *(ptr + layer*8);
        uint8_t c = star_char[layer];
        uint8_t col = star_color[layer];

        mask <<= delta;  // shift pixels
        delta <<= 1;     // 1 - 2 - 4 pixels shift

        if (0x0 == mask) {

            for (int i=0; i<num_stars; i++) {
                if (i%3 != layer) continue;

                auto& x = star_x[i];
                if (x < 40) {
                    Video::putc(x, 1 + i*2, 0x20);
                    if (x > 0) x--; else x = 40 + getRandomNumber()%40;
                } else {
                    x--;
                }
            }

            mask = 0x1;
            bits = mask;

            for (int i=0; i<num_stars; i++) {
                if (i%3 != layer) continue;

                auto& x = star_x[i];
                if (x < 40) Video::putc(x, 1 + i*2, c, col);
            }
        } else {
            bits = mask;
        }
    }
}

void initSprites() {

    Video::setSpriteCommonColors(1, 11);

    uint8_t sprite_colors[] = {2,6,2,11,2,4,2,9};

    auto& metrics = Video::metrics();

    uint8_t block_index = Video::getSpriteAddress(__sprite_data[0]);
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

void updateSprites() {

    for (auto& sprite : sprites) {

        sprite.x += sprite.vx;
        if (sprite.x > 2600) {
            sprite.x = 2600;
            sprite.vx = -sprite.vx;
        } else if (sprite.x < 200) {
            sprite.x = 200;
            sprite.vx = -sprite.vx;
        }

        sprite.y += sprite.vy;
        if (sprite.y > 1800) {
            sprite.y = 1800;
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


        if (!enable_irq) {
            sprite.updatePos();
            sprite.updateAnimation();
        }

    }

}

void onVerticalBlank() {
    if (enable_audio) Audio::update();

    if (enable_sprites) {
        for (const auto& sprite : sprites) {
            sprite.updatePos();
            sprite.updateAnimation();
        }
    }

    if (enable_starfield) updateStarfield();

}

int main() {

    System::init();
    System::disableKernalAndBasic();

    Keyboard::init();
    Video::init();
    Video::setBank(2);
    Video::setGraphicsMode(GraphicsMode::StandardTextMode);
    Video::setScreenBase(0x1);

    System::copyCharset((uint8_t*) Video::getCharacterBasePtr(1));
    Video::setCharacterBase(0x1);

    if (enable_starfield) initStarfield();

    Video::clear();
    Video::setBackground(0);
    Video::setBorder(0);

    if (enable_irq) {
        auto metrics = Video::metrics();
        Video::addRasterSequenceStep(metrics.num_raster_lines - 40, onVerticalBlank);
        Video::enableRasterIrq();
    }

    if (enable_sprites) initSprites();
    if (enable_audio) Audio::init();

    Video::puts(15, 0, "Hello World", 8);

    for (;;) {
        if (enable_sprites) updateSprites();
        if (enable_starfield && !enable_irq) updateStarfield();
        Video::waitNextFrame();
    }

    return 0;
}
