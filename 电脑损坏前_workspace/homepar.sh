echo "=== HOMEParams 相关符号与字符串 ==="
strings /dobot/bin/lib/libdataSvr.so.1.0.0 2>/dev/null | grep -iE "homeparam|home param|set/home|get/home|/home|home.*json|home.*txt" | sort -u | head -40
echo "=== 包含 home 的文件路径 ==="
strings /dobot/bin/gcontrol /dobot/bin/lib/libdataSvr.so.1.0.0 /dobot/bin/lib/libdataSvrPlugin.so.1.0.0 2>/dev/null | grep -E "/[a-zA-Z0-9_./-]*(home|Home|HOME)[a-zA-Z0-9_./-]*" | grep -E "\.(json|txt|dat|bin|conf)|/dobot/|/home/" | sort -u | head -40
echo "=== 所有 redis 相关键名 ==="
strings /dobot/bin/gcontrol /dobot/bin/lib/libdataSvr.so.1.0.0 2>/dev/null | grep -iE "^[a-z_]+:[a-z_]+$|dobot.*key" | sort -u | head -40
echo "=== 保存类函数符号 ==="
strings /dobot/bin/lib/libdataSvr.so.1.0.0 2>/dev/null | grep -iE "save|write|store|persist" | grep -vE "fmt|std::|_ZN3fmt" | sort -u | head -40