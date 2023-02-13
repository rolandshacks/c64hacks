#pragma once

#include "./system.h"

#include <cstdint>
#include <string.h>

namespace sys {

class Audio {
    public:
        static void init();
        static void update();
};

}  // namespace sys
