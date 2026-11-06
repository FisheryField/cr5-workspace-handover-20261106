/* amscan.c - map file offsets of Application.app to runtime addresses.
 *
 * Reads anchor patterns (offset / length / hex bytes) from a text file, then
 * scans every readable region of a target process' /proc/PID/mem, reporting
 * each hit as:  runtime_addr  anchor_file_offset  implied_base
 *
 * Build (workspace-local zig):
 *   zig cc -target arm-linux-musleabihf -Os -static -o amscan amscan.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>

#define MAXA 128
#define MAXREG 256
#define CHUNK (1u << 20)   /* 1 MiB */

struct anchor { unsigned long off; int len; unsigned char pat[64]; };

static struct anchor A[MAXA];
static int NA = 0;

struct reg { unsigned long lo, hi; char perms[8]; char path[256]; };
static struct reg R[MAXREG];
static int NR = 0;

static int hexval(int c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int load_anchors(const char *p) {
    FILE *f = fopen(p, "r");
    char line[512];
    if (!f) { perror(p); return -1; }
    while (fgets(line, sizeof line, f)) {
        char *s = line;
        while (*s == ' ' || *s == '\t') s++;
        if (*s == '#' || *s == '\n' || *s == 0) continue;
        char *endp;
        unsigned long off = strtoul(s, &endp, 16);
        if (endp == s) continue;
        int len = (int)strtol(endp, &endp, 10);
        if (len <= 0 || len > 64) continue;
        while (*endp == ' ' || *endp == '\t') endp++;
        if (NA >= MAXA) break;
        A[NA].off = off;
        A[NA].len = len;
        int ok = 1;
        for (int i = 0; i < len; i++) {
            int h = hexval(endp[2 * i]), l = hexval(endp[2 * i + 1]);
            if (h < 0 || l < 0) { ok = 0; break; }
            A[NA].pat[i] = (unsigned char)((h << 4) | l);
        }
        if (ok) NA++;
    }
    fclose(f);
    return NA;
}

static void load_maps(int pid) {
    char path[64];
    snprintf(path, sizeof path, "/proc/%d/maps", pid);
    FILE *f = fopen(path, "r");
    char line[512];
    if (!f) { perror(path); return; }
    while (fgets(line, sizeof line, f) && NR < MAXREG) {
        unsigned long lo, hi;
        char perms[8] = {0}, p[256] = {0};
        int n = sscanf(line, "%lx-%lx %7s %*s %*s %*s %255[^\n]", &lo, &hi, perms, p);
        if (n < 3) continue;
        if (perms[0] != 'r') continue;          /* need read permission */
        R[NR].lo = lo; R[NR].hi = hi;
        strncpy(R[NR].perms, perms, 7);
        strncpy(R[NR].path, n >= 4 ? p : "", 255);
        NR++;
    }
    fclose(f);
}

static unsigned char *buf;

static void search_region(int fd, const struct reg *r) {
    unsigned long pos = r->lo;
    while (pos < r->hi) {
        size_t want = CHUNK;
        if ((unsigned long)want > r->hi - pos) want = (size_t)(r->hi - pos);
        ssize_t got = pread(fd, buf, want, (off_t)pos);
        if (got <= 0) break;    /* hole / gone / unreadable -> skip rest */
        for (int a = 0; a < NA; a++) {
            int L = A[a].len;
            if ((ssize_t)L > got) continue;
            unsigned char *p = buf, *e = buf + got - L;
            while (p <= e) {
                unsigned char *hit = memchr(p, A[a].pat[0], (size_t)(e - p + 1));
                if (!hit) break;
                if (memcmp(hit, A[a].pat, L) == 0) {
                    unsigned long addr = pos + (unsigned long)(hit - buf);
                    unsigned long base = addr - A[a].off;
                    printf("HIT\t0x%08lx\t0x%08lx\t%d\t0x%08lx\t%s\t%s\n",
                           addr, A[a].off, L, base, r->perms, r->path);
                }
                p = hit + 1;
            }
        }
        pos += (unsigned long)got;    /* stays page aligned since got is */
    }
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <pid> <anchors.txt>\n", argv[0]);
        return 2;
    }
    int pid = atoi(argv[1]);
    if (load_anchors(argv[2]) <= 0) { fprintf(stderr, "no anchors\n"); return 2; }
    load_maps(pid);
    fprintf(stderr, "[amscan] pid=%d anchors=%d regions=%d\n", pid, NA, NR);

    char mp[64];
    snprintf(mp, sizeof mp, "/proc/%d/mem", pid);
    int fd = open(mp, O_RDONLY);
    if (fd < 0) { perror(mp); return 1; }

    buf = malloc(CHUNK + 64);
    if (!buf) { fprintf(stderr, "oom\n"); return 1; }

    printf("# addr        file_off    len base        perms path\n");
    for (int i = 0; i < NR; i++)
        search_region(fd, &R[i]);

    close(fd);
    return 0;
}
