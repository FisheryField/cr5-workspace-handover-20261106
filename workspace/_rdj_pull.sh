#!/bin/sh
tail -c 3000000 /dobot/userdata/CR5_sys_files/project/logs/all/log > /tmp/_logtail.bin
ls -l /tmp/_logtail.bin
