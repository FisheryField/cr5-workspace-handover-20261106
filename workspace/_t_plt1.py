import sys
sys.path.insert(0, 'tools')
sys.path.insert(0, '.pylibs')
import libdata_plt as P

built = P.build() if callable(getattr(P, 'build', None)) else None
import inspect
src = inspect.getsource(P.main)
print(src[:1500])
