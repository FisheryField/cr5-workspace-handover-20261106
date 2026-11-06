/* amrd.c - read a range of a target process' memory: hexdump, ascii, or raw.
 *
 *   amrd <pid> <start_hex> <len_hex> hex           # hexdump
 *   amrd <pid> <start_hex> <len_hex> ascii         # printable view
 *   amrd <pid> <start_hex> <len_hex> raw > out.bin # raw bytes to stdout
 *
 * Unreadable pages (holes) are skipped page by page and reported on stderr;
 * the raw stream is padded with zeroes so dump offset == address - start.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>

#define PAGE 4096
#define CHUNK (1u << 20)

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "usage: %s <pid> <start_hex> <len_hex> [hex|ascii|raw]\n", argv[0]);
        return 2;
    }
    int pid = atoi(argv[1]);
    unsigned long start = strtoul(argv[2], NULL, 16);
    unsigned long len = strtoul(argv[3], NULL, 16);
    const char *mode = argv[4];
    int hexmode = (strcmp(mode, "hex") == 0);
    int asciimode = (strcmp(mode, "ascii") == 0);
    int rawmode = !hexmode && !asciimode;

    char mp[64];
    snprintf(mp, sizeof mp, "/proc/%d/mem", pid);
    int fd = open(mp, O_RDONLY);
    if (fd < 0) { perror(mp); return 1; }

    unsigned char *buf = malloc(CHUNK + PAGE);
    if (!buf) { fprintf(stderr, "oom\n"); return 1; }
    unsigned char *zero = calloc(1, PAGE);
    if (!zero) { fprintf(stderr, "oom\n"); return 1; }

    unsigned long holes = 0, bytes = 0;
    for (unsigned long pos = start; pos < start + len; pos += PAGE) {
        size_t n = PAGE;
        if ((unsigned long)n > start + len - pos) n = (size_t)(start + len - pos);
        ssize_t got = pread(fd, buf, n, (off_t)pos);
        if (got <= 0) {
            holes++;
            memset(buf, 0, n);
            got = (ssize_t)n;
        }
        bytes += (unsigned long)got;
        if (rawmode) {
            if (write(1, buf, (size_t)got) != got) { perror("write"); break; }
            continue;
        }
        if (hexmode || asciimode) {
            for (ssize_t i = 0; i < got; i += 16) {
                printf("%08lx |", pos + (unsigned long)i);
                ssize_t k = got - i; if (k > 16) k = 16;
                for (ssize_t j = 0; j < 16; j++) {
                    if (j < k) printf(" %02x", buf[i + j]); else printf("   ");
                    if (j == 7) printf(" ");
                }
                printf(" |");
                if (asciimode)
                    for (ssize_t j = 0; j < k; j++) {
                        unsigned char c = buf[i + j];
                        putchar((c >= 32 && c < 127) ? c : '.');
                    }
                printf("\n");
            }
        }
        (void)zero;
    }
    fprintf(stderr, "[amrd] %lu bytes, %lu empty/unreadable pages\n", bytes, holes);
    return 0;
}
