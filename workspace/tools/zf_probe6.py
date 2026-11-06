"""zf_probe6.py - call-graph reachability of the persistence routines.

Builds a *function*-level call graph:
  * function entries = `push {...,lr}` sites + all `bl` targets
  * every `bl X` inside function F edge F -> owner(X)
Then: direct callers of each persistence entry point, and reachability from
Reset_Handler.

POSITIVE SELF-CHECK: the log-append routine (magic 0xBE6D4A8B) must have >= 1
caller and must be reachable from Reset; if these come back empty the graph is
broken.
"""
import sys, os, bisect
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import Img, load_pair

INTEREST = {
    'v328d8': dict(param_persist=0x08011708, log_append=0x080117D0,
                   flash_unlock=0x0801449C, flash_prog=0x08014360,
                   sector_class=0x08019C0E, log_init=0x08019C40),
    'v3150': dict(param_persist=0x08011748, log_append=0x08011810,
                  flash_unlock=0x08014100, flash_prog=0x08013FC4,
                  sector_class=0x080195B6, log_init=0x080195E8),
}


def build(im):
    entries = set()
    calls = {}
    for i in im.index():
        if i.mnemonic in ('push', 'push.w') and 'lr' in i.op_str:
            entries.add(i.address)
        c = im.call(i)
        if c is not None:
            entries.add(c)
            calls.setdefault(c, []).append(i.address)
    ents = sorted(entries)
    return ents, entries, calls


def owner(ents, addr):
    k = bisect.bisect_right(ents, addr) - 1
    return ents[k] if k >= 0 else None


def main():
    a, b = load_pair()
    for im in (a, b):
        key = 'v328d8' if 'd8' in im.name.lower() else 'v3150'
        tab = INTEREST[key]
        ents, entryset, calls = build(im)
        print('=' * 90)
        print('%s   entries=%d' % (im.name, len(ents)))
        # function -> callees
        edges = {}
        for i in im.index():
            c = im.call(i)
            if c is None:
                continue
            f = owner(ents, i.address)
            if f is None:
                continue
            edges.setdefault(f, set()).add(owner(ents, c))
        for label, addr in tab.items():
            cs = calls.get(addr & ~1, [])
            owners = sorted(set(owner(ents, c) for c in cs))
            print('  %-14s 0x%08x  call sites=%d  caller funcs: %s'
                  % (label, addr, len(cs), ['0x%08x' % o for o in owners if o]))
        # reachability
        reset = im.reset
        seen = set([reset])
        stack = [reset]
        while stack:
            f = stack.pop()
            for g in edges.get(f, ()):
                if g is not None and g not in seen:
                    seen.add(g)
                    stack.append(g)
        print('  reachable-from-Reset funcs: %d of %d' % (len(seen), len(ents)))
        for label, addr in tab.items():
            o = owner(ents, addr & ~1)
            print('     %-14s owner=0x%08x reachable=%s' % (label, o or 0, o in seen))
        print()


if __name__ == '__main__':
    sys.exit(main())
