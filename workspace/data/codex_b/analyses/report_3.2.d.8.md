# CR5 3.2.d.8 零点标定采集报告

## 采集文件

- EtherCAT 抓包：[zero32_calibration.pcap](zero32_calibration.pcap)
- 控制器日志：`controller.log`
- 标定结果：`homeEncoder.json`
- 解析摘要：`analysis_3.2.d.8.json`

## 时间线

- `15:45:15.448`：主控收到 `POST /calibrate/home`
- `15:45:15.454`：开始标定，`HomeNumdone=0`
- `15:45:15.754`：`HomeNumdone=2`
- `15:45:16.054`：`HomeNumdone=4`
- `15:45:16.355`：`HomeNumdone=6`，记录 `servo calihome done`
- `15:45:16.366`：写入 `homeEncoder.json`

## 3.2.d.8 保存的 innerEncoder

```text
J1   598234  = da 20 09 00 (little-endian)
J2  -192592  = b0 0f fd ff
J3  -580282  = 46 25 f7 ff
J4   389348  = e4 f0 05 00
J5  -718959  = 91 07 f5 ff
J6   576819  = 33 cd 08 00
```

抓包显示这些六个有符号 32 位值在标定请求前已经持续出现在 EtherCAT 周期 PDO 数据中。标定完成后，主控把当前 PDO 值复制到 `homeEncoder.json`；没有观察到“先向伺服写入一个新的 innerEncoder，再由伺服返回”的独立过程。

## 当前结论

3.2.d.8 的零点标定路径为：

```text
DobotStudio Pro
  -> POST /calibrate/home
  -> 主控等待六个伺服 calihome 完成
  -> 读取 EtherCAT PDO 中的 innerEncoder
  -> 写入 homeEncoder.json
  -> 后续使能时用该记录计算关节坐标
```

这说明后续与 3.1.5 的严格对比应首先检查：

1. innerEncoder 的 PDO 数据是否存在；
2. 数据宽度、符号位和字节序是否一致；
3. PDO 映射偏移是否改变；
4. 3.1.5 是否把该字段置零或不刷新。
