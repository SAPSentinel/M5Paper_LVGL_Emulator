# LVGL M5Stack Board Emulation - Windows SDL2 Setup Guide

## Project Overview

This is a **working LVGL board emulation** for M5Stack devices running on Windows with SDL2. The setup allows you to develop and test LVGL UI on PC before flashing to hardware, with visual consistency across different M5Stack boards.

**Status:** ✅ **FULLY FUNCTIONAL** on Windows (MinGW64 + SDL2)

---

## Environment Details

### Operating System
- **Primary:** Windows 10/11
- **Shell:** MinGW64 (MSYS2)
- **Build Tool:** PlatformIO 6.x
- **IDE:** VS Code

### Dependencies
- **LVGL Version:** v8.4.0 (currently active)
  - Alternative available: v9 (commented out in platformio.ini)
- **Graphics Framework:** M5GFX (develop branch)
- **Display Backend:** SDL2 (Simple DirectMedia Layer 2)
- **Compiler:** GCC (MinGW64)
- **C++ Standard:** C++17

### SDL2 Installation
The project requires SDL2 libraries for Windows emulation:
```bash
# Via package manager (if available)
pacman -S mingw-w64-x86_64-SDL2

# Or via vcpkg, Conan, or manual installation
```

---

## Critical Windows Compatibility Fixes

### ⚠️ THE EXACT 2-STEP SOLUTION

These are **NOT optional**. Without these, compilation will fail on Windows.

---

### STEP 1: Add Windows Compatibility Block

**File:** `src/utility/lvgl_port_m5stack.cpp`

**Location:** At the top of the file, after the includes for `<cstdlib>` (include headers section)

```cpp
#include <cstdlib>  // for aligned_alloc
#include "lvgl_port_m5stack.hpp"
#include <cstdlib>  // for aligned_alloc
#include <cstring>  // for memset

// ✅ ADD THIS BLOCK FOR WINDOWS COMPATIBILITY
#ifdef _WIN32
#include <malloc.h>
#define ALIGNED_ALLOC(alignment, size) _aligned_malloc(size, alignment)
#define ALIGNED_FREE(ptr) _aligned_free(ptr)
#else
#define ALIGNED_ALLOC(alignment, size) aligned_alloc(alignment, size)
#define ALIGNED_FREE(ptr) free(ptr)
#endif
```

**Why:** 
- Windows doesn't have `aligned_alloc()` natively
- Uses `_aligned_malloc()` instead (MSVC runtime)
- Macro centralizes the solution (no repeated #ifdefs everywhere)

---

### STEP 2: Replace All `aligned_alloc` Calls

This affects **TWO LOCATIONS** in the code:

#### 2A) LVGL v8 Section (around line 155-160)

**BEFORE:**
```cpp
static lv_color_t *buf1 = static_cast<lv_color_t *>(aligned_alloc(alignment, aligned_size));
static lv_color_t *buf2 = static_cast<lv_color_t *>(aligned_alloc(alignment, aligned_size));
```

**AFTER:**
```cpp
static lv_color_t *buf1 = static_cast<lv_color_t *>(ALIGNED_ALLOC(alignment, aligned_size));
static lv_color_t *buf2 = static_cast<lv_color_t *>(ALIGNED_ALLOC(alignment, aligned_size));
```

---

#### 2B) LVGL v9 Section (around line 310-315)

**BEFORE:**
```cpp
static uint8_t *buf1 = static_cast<uint8_t *>(aligned_alloc(alignment, aligned_size));
static uint8_t *buf2 = static_cast<uint8_t *>(aligned_alloc(alignment, aligned_size));
```

**AFTER:**
```cpp
static uint8_t *buf1 = static_cast<uint8_t *>(ALIGNED_ALLOC(alignment, aligned_size));
static uint8_t *buf2 = static_cast<uint8_t *>(ALIGNED_ALLOC(alignment, aligned_size));
```

---

## PlatformIO Configuration (`platformio.ini`)

### Key Build Settings

```ini
[env]
build_flags =
  -std=c++17                    # C++17 standard (required)
  -I include                    # Include headers
  -I src/utility               
  -D LV_CONF_INCLUDE_SIMPLE     # LVGL config mode
  -D LV_LVGL_H_INCLUDE_SIMPLE  
  -D LVGL_USE_V8=1              # Using LVGL v8 (set to 0 for v9)
  -D LVGL_USE_V9=0              # Disable v9 (enable if switching versions)

lib_deps = 
  https://github.com/m5stack/M5GFX#develop
  lvgl=https://github.com/lvgl/lvgl/archive/refs/tags/v8.4.0.zip
```

### Emulator Environment (SDL2-based)

```ini
[env:emulator_common]
build_flags =
  ${env.build_flags}
  -l SDL2                       # Link SDL2 library
  -D M5GFX_SHOW_FRAME           # Show device frame
  -D M5GFX_BACK_COLOR=0xFFFFFFU # White background
  -D M5GFX_SCALE=2              # 2x scaling for visibility
  -D M5GFX_ROTATION=0           # No rotation
```

### Platform-Specific Configs

**For Windows Emulator (Native Platform):**
```ini
[env:emulator_CoreS3]
extends = emulator_common
platform = native@^1.2.1
extra_scripts = support/sdl2_build_extra.py
build_type = debug
build_flags =
  ${env:emulator_common.build_flags}
  -D M5GFX_BOARD=board_M5StackCoreS3
```

**Available Emulator Environments:**
- `emulator_Core` - M5Stack Classic
- `emulator_Core2` - M5Stack Core2
- `emulator_CoreS3` - M5Stack Core S3
- `emulator_StickCPlus` - M5Stick-C Plus
- `emulator_StickCPlus2` - M5Stick-C Plus 2
- `emulator_Dial` - M5Dial
- `emulator_Tab5` - M5Tab5

---

## Project Architecture

### Directory Structure
```
lv_m5_emulator/
├── src/
│   ├── main.cpp                          # Entry point
│   ├── user_app.cpp                      # Your UI code
│   └── utility/
│       ├── lvgl_port_m5stack.cpp         # ⭐ CRITICAL: Contains the fixes
│       └── lvgl_port_m5stack.hpp         # LVGL port header
├── include/
│   ├── lv_conf_v8.h                      # LVGL v8 config
│   ├── lv_conf_v9.h                      # LVGL v9 config
│   └── lv_conf.h                         # Active config
├── lib/                                  # Library placeholder
├── support/
│   └── sdl2_build_extra.py               # SDL2 build script
└── platformio.ini                        # Build configuration
```

### Key Components

#### 1. LVGL Port (lvgl_port_m5stack.cpp)
- **Initializes LVGL** with M5GFX backend
- **Allocates display buffers** with proper alignment
- **Manages threading** (or SDL2 threads for emulator)
- **Handles touch input** through M5GFX

**Critical elements in this file:**
- Windows compatibility macros (ALIGNED_ALLOC, ALIGNED_FREE)
- Aligned memory allocation for SDL2 emulation
- Buffer chunking for display write (prevents SIMD issues)
- Mutex/thread management for GUI thread safety

#### 2. Buffer Management

**For SDL2 Emulation (Windows):**
- Uses **aligned memory** (64-byte alignment)
- Implements **chunked transmission** (8KB chunks)
- Prevents SIMD-related memory access issues

```cpp
const size_t alignment    = 64;  // 64-byte alignment
const size_t aligned_size = (total_bytes + alignment - 1) & ~(alignment - 1);
static lv_color_t *buf1 = static_cast<lv_color_t *>(ALIGNED_ALLOC(alignment, aligned_size));
```

#### 3. Display Flush Strategy

The flush callback uses **chunked transmission**:
```cpp
const uint32_t SAFE_CHUNK_SIZE = 8192;  // 8K pixels per chunk

if (pixels > SAFE_CHUNK_SIZE) {
    // Chunked transmission for large data
    while (remaining > 0) {
        uint32_t chunk_size = (remaining > SAFE_CHUNK_SIZE) ? SAFE_CHUNK_SIZE : remaining;
        gfx.writePixels(src + offset, chunk_size);
        offset += chunk_size;
        remaining -= chunk_size;
    }
}
```

**Why:** Prevents M5GFX SIMD optimization issues with large memory transfers.

---

## Build & Run

### Build for Windows SDL2 Emulation
```bash
pio run -e emulator_CoreS3
```

### Run with Monitor
```bash
pio run -e emulator_CoreS3 -t monitor
```

### Verbose Output
```bash
pio run -e emulator_CoreS3 -v
```

---

## LVGL Version Switching

### Use LVGL v8 (Default - RECOMMENDED)
```ini
-D LVGL_USE_V8=1
-D LVGL_USE_V9=0
lib_deps = lvgl=https://github.com/lvgl/lvgl/archive/refs/tags/v8.4.0.zip
```

### Use LVGL v9
```ini
-D LVGL_USE_V8=0
-D LVGL_USE_V9=1
lib_deps = lvgl=https://github.com/lvgl/lvgl#master
```

**Note:** When switching versions:
1. Update `platformio.ini`
2. Update `src/utility/lvgl_port_m5stack.cpp` (both v8 and v9 sections already have correct code)
3. Rebuild all: `pio run -e emulator_CoreS3 --full-clean`

---

## Configuration Files (LVGL)

### Active Configuration
- **File:** `include/lv_conf.h`
- This should match the LVGL version in use

### Version-Specific Configs
- **LVGL v8:** `include/lv_conf_v8.h`
- **LVGL v9:** `include/lv_conf_v9.h`

**Important Settings** (both versions):
```c
#define LV_CONF_INCLUDE_SIMPLE 1      // Simple include mode
#define LV_BUFFER_LINE 120             // Line buffer (affects memory usage)
#define LV_USE_PERF_MONITOR 0          // Performance monitor (disable for production)
#define LV_USE_MEM_MONITOR 0           // Memory monitor
```

---

## Known Issues & Solutions

### Issue: `undefined reference to aligned_alloc`
**Solution:** Apply STEP 1 and STEP 2 above. This is the Windows compatibility fix.

### Issue: Display flickering or corrupted pixels
**Solution:** Already handled by:
- Buffer alignment (64-byte)
- Chunked transmission (8KB chunks)
- Buffer initialization with `memset(..., 0, ...)`

### Issue: Touch input not working
**Solution:** Check M5GFX board definition and `gfx.getTouch()` implementation. Ensure correct board is selected in build flags.

### Issue: SDL2 not found
**Solution:** Install SDL2 development libraries:
```bash
# MSYS2
pacman -S mingw-w64-x86_64-SDL2

# Verify installation
pkg-config --list-all | grep SDL
```

---

## Applying This to M5Paper Project

### Prerequisite Checklist
- [ ] M5Paper project has `src/utility/lvgl_port_m5stack.cpp` file
- [ ] Project uses same platformio.ini structure
- [ ] M5GFX is installed for M5Paper board
- [ ] `platformio.ini` has LVGL v8 or v9 configured

### Implementation Steps

1. **Apply Windows Compatibility Block**
   - Open `src/utility/lvgl_port_m5stack.cpp` in your project
   - Add the `#ifdef _WIN32` block (STEP 1 above) after includes
   
2. **Replace aligned_alloc Calls**
   - Find all `aligned_alloc()` calls
   - Replace with `ALIGNED_ALLOC()` (STEP 2 above)
   - Check both LVGL v8 and v9 sections

3. **Verify platformio.ini**
   - Ensure C++17 standard: `-std=c++17`
   - Include `-l SDL2` in emulator environment
   - Set LVGL version flags correctly

4. **Test Build**
   ```bash
   pio run -e emulator_CoreS3 --full-clean
   ```

5. **Run Emulator**
   ```bash
   pio run -e emulator_CoreS3 -t monitor
   ```

---

## Summary

**The working setup requires:**

✅ LVGL v8.4.0 or v9 (both supported)  
✅ M5GFX (develop branch) for graphics abstraction  
✅ SDL2 for Windows desktop emulation  
✅ C++17 compiler (MinGW64 on Windows)  
✅ **WINDOWS COMPATIBILITY MACROS** (non-negotiable)  
✅ Aligned memory allocation (64-byte alignment)  
✅ Chunked display transmission (prevents SIMD issues)  

**Do NOT:**
- ❌ Use `aligned_alloc()` directly on Windows
- ❌ Skip buffer alignment
- ❌ Skip buffer initialization
- ❌ Use C++14 or older (need C++17)

---

## Incident Report: "The command line is too long" (2026-02-20)

### What Broke and Why

The build stopped working **without any local code changes**. The error was:

```
Linking .pio\build\emulator_CoreS3\program.exe
The command line is too long.
*** [.pio\build\emulator_CoreS3\program.exe] Error 1
```

**Root cause:** `M5GFX` is pinned to `#develop` — a **floating git reference**. PlatformIO silently pulled a newer commit (`sha.770e402`) which added new source files to M5GFX. With `lib_archive = false` (the project default), PlatformIO passes every compiled `.o` file individually on the linker command line. The new M5GFX commit pushed the total command length past Windows' hard **~32,767 character CreateProcess limit**.

This is an **external dependency breakage** — nothing in the project changed. It will happen again if M5GFX `#develop` continues adding files.

---

### What Was Tried and Why Each Attempt Failed

| Attempt | What was tried | Why it failed |
|---|---|---|
| 1 | `from SCons.Platform.TempFileMunge import TempFileMunge` | That submodule path doesn't exist in SCons 4.8.1 — class lives in `SCons.Platform.__init__` |
| 2 | `e["LINKCOM"] = e["TEMPFILE"](e["LINKCOM"])` | Calling the class directly creates an instance object; SCons later calls it as a FunctionAction and hits `TypeError: missing 1 required positional argument: 'for_signature'` |
| 3 | `lib_archive = true` in `[env:emulator_common]` | PlatformIO's `extends` system does **not** inherit library options (`lib_archive`, `lib_deps`) — only build flags. The child envs silently kept `lib_archive = false` |
| 4 | `lib_archive = true` in the base `[env]` | Moved the problem from linker to archiver — now **`ar`** hit the same limit with `The command line is too long` when building `liblvgl.a` |
| 5 | `e["LINKCOM"] = "${TEMPFILE('%s','$LINKCOMSTR')}" % str(lc)` | The TempFileMunge mechanism activated correctly and wrote the response file — but the original LINKCOM string `"C:\msys64\mingw64\bin\g++.exe" -o $TARGET ...` was embedded **literally** in the template. SCons parses `\b` in `mingw64\bin` as a **backspace escape sequence**, corrupting the path → "The filename, directory name, or volume label syntax is incorrect" |

---

### The Working Fix

**File:** `support/sdl2_build_extra.py`

The fix has two parts working together:

#### Part 1 — Extract the compiler into `$LINK`

PlatformIO expands the compiler path into a literal string in `LINKCOM` before the script sees it (e.g. `"C:\msys64\mingw64\bin\g++.exe" -o $TARGET ...`). We cannot embed this literal path inside a `${TEMPFILE('...')}` template string because SCons re-parses the template and interprets `\b`, `\t`, `\u` etc. as escape sequences.

**Solution:** Extract the compiler path into the `$LINK` SCons variable and use the variable reference `$LINK` in the template. SCons expands `$LINK` safely at link time, bypassing the escape-sequence problem.

#### Part 2 — Forward-slash path escaping in the response file

GCC (MinGW) treats backslashes as escape sequences when reading a response file. So `D:\platform-io\build\emulator_CoreS3\...` in the response file has `\b`, `\e`, `\p` misread as escape characters. `TEMPFILEARGESCFUNC` is a SCons hook that post-processes every argument before writing it to the response file — we use it to convert all `\` to `/`.

**Final code in `support/sdl2_build_extra.py`:**

```python
import sys
if sys.platform == "win32":
    import re
    from SCons.Subst import quote_spaces

    _WINPATH_RE = re.compile(r"\\([^\"'\\]|$)")

    def _win_path_esc(arg):
        """Quote spaces, then convert backslashes to forward slashes so GCC
        does not treat them as escape sequences inside the response file."""
        arg = quote_spaces(arg)
        return _WINPATH_RE.sub(r"/\1", arg)

    for e in [env, projenv]:
        e["TEMPFILEARGESCFUNC"] = _win_path_esc
        lc = str(e.get("LINKCOM", ""))
        if lc and "${TEMPFILE" not in lc:
            # Extract compiler path into $LINK variable so it is NOT embedded
            # as a literal backslash path inside the ${TEMPFILE('...')} template
            import shlex
            parts = shlex.split(lc, posix=False)
            if parts:
                e["LINK"] = parts[0].strip('"')
            e["LINKCOM"] = "${TEMPFILE('$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS','$LINKCOMSTR')}"
```

**What this does at build time:**

1. SCons evaluates `${TEMPFILE('$LINK -o $TARGET ...')}` → calls `TempFileMunge.__call__`
2. TempFileMunge expands `$LINK`, `$TARGET`, `$SOURCES` etc. to their actual values
3. Each argument is passed through `_win_path_esc` → backslashes become forward slashes
4. All arguments are written to a temp `.lnk` file
5. GCC is invoked as `g++ @D:/path/to/tmp.lnk` — no command line length limit applies
6. GCC reads the response file and links successfully

---

### How to Prevent Future Breakage

#### Option A — Pin M5GFX to a specific commit (most stable)

Instead of `#develop` (a floating branch tip), pin to the exact commit that is known to work:

```ini
; In platformio.ini [env] section:
lib_deps =
    https://github.com/m5stack/M5GFX#770e402    ; pinned to last known-good commit
```

**How to update the pin:** When you want to update M5GFX, check the [M5GFX commits page](https://github.com/m5stack/M5GFX/commits/develop), pick a specific commit SHA, test the build, and update the hash in `platformio.ini`.

#### Option B — Keep `#develop` with the response-file fix (current state)

The `sdl2_build_extra.py` fix is already in place and handles any command line length regardless of how many files M5GFX adds. As long as the script is listed in `extra_scripts`, all emulator environments are protected.

**What could still break this fix:**
- A PlatformIO update changes how `LINKCOM` is structured (check the `DEBUG LINKCOM` print in the script to verify)
- SCons is updated and changes the `TEMPFILE` / `TEMPFILEARGESCFUNC` API (rare, but check release notes)

If the link step fails again with a new error, run a verbose build first:
```bash
pio run -e emulator_CoreS3 -v 2>&1 | tail -30
```
Look at the `Using tempfile` line and the content of the `.tmp` file it references.

#### Option C — Permanent immunity: switch to a fixed release tag

```ini
lib_deps =
    https://github.com/m5stack/M5GFX/archive/refs/tags/0.2.19.zip
```

Using a release tag ZIP means PlatformIO never re-downloads it and the file count is forever fixed.

---

## References

- LVGL Documentation: https://docs.lvgl.io/
- M5GFX Repository: https://github.com/m5stack/M5GFX
- M5Stack Documentation: https://docs.m5stack.com/
- PlatformIO Documentation: https://docs.platformio.org/
- SCons TempFileMunge source: `C:\Users\<user>\.platformio\packages\tool-scons\scons-local-4.8.1\SCons\Platform\__init__.py`

---

**Document Version:** 1.1  
**Last Updated:** 2026-02-20  
**Status:** ✅ Verified Working on Windows MinGW64 + SDL2  
**Change:** Added Incident Report for M5GFX auto-update / command line too long breakage
