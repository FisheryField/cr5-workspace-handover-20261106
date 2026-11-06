/* amdump.c - dump a byte range of a target process' memory to a file.
 *
 * amdump <pid> <start-hex> <len-hex> <outfile>
 *
 * Build: zig cc -target arm-linux-musleabihf -Os -static -o amdump amdump.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>

#define CHUNK (1u << 20)

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "usage: %s <pid> <start_hex> <len_hex> <outfile>\n", argv[0]);
        return 2;
    }
    int pid = atoi(argv[1]);
    unsigned long start = strtoul(argv[2], NULL, 16);
    unsigned long len = strtoul(argv[3], NULL, 16);
    char mp[64];
    snprintf(mp, sizeof mp, "/proc/%d/mem", pid);
    int fd = open(mp, O_RDONLY);
    if (fd < 0) { perror(mp); return 1; }
    int out = open(argv[4], O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (out < 0) { perror(argv[4]); return 1; }

    unsigned char *buf = malloc(CHUNK);
    if (!buf) { fprintf(stderr, "oom\n"); return 1; }
    unsigned long done = 0, zero = 0;
    while (done < len) {
        size_t want = CHUNK;
        if ((unsigned long)want > len - done) want = (size_t)(len - done);
        ssize_t got = pread(fd, buf, want, (off_t)(start + done));
        if (got <= 0) { perror("pread"); break; }
        /* count all-zero pages so a reader can spot unmapped filler */
        for (ssize_t i = 0; i < got; i += 4096) {
            int allz = 1;
            for (ssize_t j = i; j < i + 4096 && j < got; j++)
                if (buf[j]) { allz = 0; break; }
            if (allz) zero++;
        }
        ssize_t w = write(out, buf, (size_t)got);
        if (w != got) { perror("write"); break; }
        done += (unsigned long)got;
    }
    fprintf(stderr, "[amdump] %lu bytes dumped, %lu zero pages\n", done, zero);
    close(out); close(fd);
    return 0;
}
