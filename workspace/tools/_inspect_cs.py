import inspect
from robodk.robolink import Robolink, Item

print("=== Item.ConnectedState ===")
print(inspect.getsource(Item.ConnectedState))
print("=== ROBOT_CONNECTION_* constants ===")
import robodk.robolink as rl
for n in dir(rl):
    if n.startswith("ROBOT_CONNECTION"):
        print(n, "=", getattr(rl, n))
