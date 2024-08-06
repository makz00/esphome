#include "iec_std_lib.h"

#define __LOCATED_VAR(type, name, ...) type __##name;
#include "LOCATED_VARIABLES.h"
#undef __LOCATED_VAR

#define __LOCATED_VAR(type, name, ...) type *name = &__##name;
#include "LOCATED_VARIABLES.h"
#undef __LOCATED_VAR

TIME __CURRENT_TIME;
BOOL __DEBUG;
extern unsigned long long common_ticktime__;

void updateTime() {
  __CURRENT_TIME.tv_nsec += common_ticktime__;

  if (__CURRENT_TIME.tv_nsec >= 1000000000) {
    __CURRENT_TIME.tv_nsec -= 1000000000;
    __CURRENT_TIME.tv_sec += 1;
  }
}
