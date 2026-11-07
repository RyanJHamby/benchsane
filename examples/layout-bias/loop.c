/* Compile with -O0. Stack variables and statics are loaded and stored on every pass, so
   timing can depend on where the stack lands relative to the statics (4K aliasing on many
   x86 CPUs). At higher optimization levels the compiler deletes most of this loop. */
static int i, j, k;

int main(void) {
    int g = 0, inc = 1;
    for (; g < 100000000; g++) {
        i += inc;
        j += inc;
        k += inc;
    }
    return 0;
}
