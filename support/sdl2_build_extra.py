Import("env", "projenv")

# Fix "The command line is too long" on Windows.
#
# Root cause: M5GFX #develop auto-updated with more source files. With
# lib_archive=false, every .o is passed individually to the linker, pushing
# the command past Windows' ~32 767-char CreateProcess limit.
#
# Fix: use SCons' built-in TempFileMunge to write all linker args to a
# response file and invoke GCC as `g++ @responsefile` instead.
# TEMPFILEARGESCFUNC is required: without it, Windows backslash paths written
# into the response file (e.g. \build\emulator_CoreS3\...) are misread by
# GCC as C escape sequences (\b, \e, \u ...), causing "filename syntax
# incorrect" or silent path corruption.
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
            # PlatformIO partially expands LINKCOM - the compiler path is already
            # a literal string (e.g. "C:\msys64\mingw64\bin\g++.exe") but other
            # vars like $TARGET/$SOURCES are still SCons variables.
            # We MUST NOT embed the literal path inside ${TEMPFILE('...')} because
            # SCons parses the template string and \b, \t, etc. in the path get
            # treated as escape sequences, corrupting the path.
            # Fix: extract the compiler into $LINK var, then reference $LINK in
            # the template so SCons expands it safely at link time.
            import shlex
            parts = shlex.split(lc, posix=False)
            if parts:
                e["LINK"] = parts[0].strip('"')
            e["LINKCOM"] = "${TEMPFILE('$LINK -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS','$LINKCOMSTR')}"

for e in [ env, projenv ]:
    # If compiler uses `-m32`, propagate it to linker.
    # Add via script, because `-Wl,-m32` does not work.
    if "-m32" in e['CCFLAGS']:
        e.Append(LINKFLAGS = ["-m32"])

exec_name = "${BUILD_DIR}/${PROGNAME}${PROGSUFFIX}"

# Override unused "upload" to execute compiled binary
from SCons.Script import AlwaysBuild
AlwaysBuild(env.Alias("upload", exec_name, exec_name))

# Add custom target to explorer
env.AddTarget(
    name = "execute",
    dependencies = exec_name,
    actions = exec_name,
    title = "Execute",
    description = "Build and execute",
    group="General"
)

#print('=====================================')
#print(env.Dump())
