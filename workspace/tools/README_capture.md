# 零点标定共享内存采集 —— 运行说明

## 它做什么

对标零**全过程的控制器共享内存做差分**，用来回答"零点到底被写到哪里"。

- 覆盖 **7 个共享内存段 / 13.4 MB（100%）**，不再赌地址
- 每轮：把整段与标零前基线做 `cmp -l`，得到**变化的字节偏移与页号**
- 只读（仅读 `/proc/<pid>/mem`），不写控制器任何业务文件
- 默认每轮约 0.7–1.0 秒

## 两个文件

| 文件 | 位置 | 作用 |
|---|---|---|
| `shm_zero_capture.sh` | 本目录 | 在**控制器**上运行的采集脚本（BusyBox sh） |
| `zero_capture.ps1` | 本目录 | 在 **PC** 上一键编排：上传 → 后台启动 → 等待 → 取回 → 解包 |

## 怎么运行（推荐：一键）

机械臂先摆好、上使能，然后：

```powershell
cd D:\mydata\workspace
powershell -ExecutionPolicy Bypass -File tools\zero_capture.ps1 -Duration 90
```

脚本会打印一个大横幅。**看到横幅后 90 秒内完成一次零点标定**：

- 用维护工具点"零点标定"，或
- `curl -X POST http://192.168.5.1:22000/calibrate/home -d '{}'`（必须使能状态）

90 秒后自动取回并解包到 `data\captures\<TAG>\`，并把 `changes.txt` 前 20 行打给你。

## 手动运行（如果不想用 ps1）

```powershell
cd D:\mydata\workspace
.\rscp.cmd -q tools\shm_zero_capture.sh root@192.168.5.1:/tmp/shm_zero_capture.sh
```
然后：
```powershell
# 启动（TAG 自定，DURATION 秒）
& ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=".ssh_agent\known_hosts" -o PreferredAuthentications=password -o NumberOfPasswordPrompts=1 root@192.168.5.1 "chmod +x /tmp/shm_zero_capture.sh; nohup /tmp/shm_zero_capture.sh TAG 90 > /tmp/TAG.log 2>&1 &"
# 90 秒内完成一次标定
# 取回
.\rscp.cmd -q root@192.168.5.1:/tmp/TAG.tar.gz data\captures\
tar -xzf data\captures\TAG.tar.gz -C data\captures\TAG
```
（SSH 密码来自 `.askpass.cmd`，需先 `$env:SSH_ASKPASS`，一键脚本已处理）

## 产物怎么读

```
<TAG>/
  regions.txt    监控的区域（起止地址、大小、名字）
  maps           采集时的 /proc/<pid>/maps
  summary.txt    regions / total_bytes / pid
  rounds.txt     每轮编号与 uptime —— 用它把变化对齐到墙钟时间
  changes.txt    ★ 每轮每区域的变化摘要：
                   round=.. t=.. region=.. name=..
                   diffs=<变化字节数> pages=<变化页数> first=<首个偏移> last=<末个偏移>
                       pages: <页号>:<该页变化字节数> …
  base/R*.bin    标零前基线（每区域一个文件）
  cur/R*.bin     最后一轮
  cur/R*.firstchange.bin  首次检出变化时的完整内容（做前后对比用）
```

**判读要点**：
- 把 `changes.txt` 里的 `t=` 与控制器日志的 `/calibrate/home` 时间戳对齐
- **标零瞬间才出现、且之后一直保持**的页 = 零点的落点
- 一直小幅变化的页（如 region 6 的第 65/132/133 页）= CODESYS 周期数据，噪声

## 已知注意事项

- **/tmp 空间**：tmpfs 仅 471 MB。脚本会预检，不足会报错退出（需要约 `总量×3`）。清理由此产生的目录：`rm -rf /tmp/<TAG>*`
- **必须使能状态**才能标定成功（未使能时接口同样返回 `{"status":true}`，但读数不变，还会报 114 Homing error）
- 采集期间不要重启控制器
