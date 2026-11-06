#更新DNS配置文件
dhcpflag=`grep eth2_dhcp /dobot/userdata/project/settings/iscara.conf | awk -F '=' '{print $2}'`
if [[ $dhcpflag == "true" ]]; then
    echo "This dhcp setting, can't modify resolv.conf" 
else
    chattr -i /etc/resolv.conf 
    rm /etc/resolv.conf
    touch /etc/resolv.conf
    chmod +w /etc/resolv.conf
    echo "nameserver 127.0.0.1" > /etc/resolv.conf
    chmod -w /etc/resolv.conf
    chattr +i /etc/resolv.conf
fi

if [ -f "/tmp/bin.tar.gz" ];then #判断是否存在升级包
    echo "unzip update files .... waiting ..."
    tar zxvf "/tmp/bin.tar.gz" -C "/dobot/" #解压升级包
fi

log_mount_path=/dobot/userdata/project/logs
tmp_log_path=/tmp/robot_update.log

LogTrace()
{
    echo "[$(date +'%Y-%m-%d %H:%M:%S')][Trace][$0]" $*
}

logPrint()
{
    LogTrace $*
    LogTrace $* >> ${tmp_log_path}
}

umountLog()
{
    logPrint "Umount log block"
    local busy=true
    while ${busy}; do
        mountpoint -q ${log_mount_path}
        if [[ $? -eq 0 ]];then
            umount ${log_mount_path} # 卸载日志分区
            if [[ $? -eq 0 ]];then
                logPrint "Umount \"${log_mount_path}\" success!"
                busy=false
            else
                logPrint "Umount \"${log_mount_path}\" failed!"
                fuser -k ${log_mount_path}
                sleep 1
            fi
        else
            busy=false
        fi
    done
}
name=""
if [ -f "/dobot/userdata/robotType" ];then  #烧录和升级都会进入这个判断
    if [ ! -L "/dobot/userdata/project" ];then #只有烧录进入这个判断
        dos2unix /dobot/userdata/robotType
        name=$(cat /dobot/userdata/robotType) # 刷机的时候这个 型号是刷进去的！
        ln -s /dobot/userdata/${name}_sys_files/project /dobot/userdata/ # 创建软链接
    fi
fi
if [ ! -L "/dobot/userdata/project" ];then   # 判断是不是软链接，烧录不会进入这个判断，只有351/352升级353/354才会到这个里面
    echo "/dobot/userdata/project is not Link ..... need to classify ControllerType"
    if [ -f "/dobot/userdata/project/properties/controllerType.json" ];then # 判断是否存在controllerType.json 文件
        name=$(awk -F 'name' '/name/{print $0}' /dobot/userdata/project/properties/controllerType.json | awk -F ':' '{print $2 }' | awk -F '"' '{print $2}')
        echo "name is $name" # 从 json 文件中获得机器人的类型，注意nova系列会有问题
        echo "$name" > "/dobot/userdata/robotType" # 将机器人类型写入到文件
    fi    
    chmod -wx "/dobot/userdata/robotType" # 删除其他权限 只读
    pkill -9 logServer                    # 干掉日志服务器 准备卸载日志分区
    sleep 2
    umountLog # 卸载日志分区
    mv /dobot/userdata/project /dobot/userdata/projectOld  # 重新保存当前的系统内容    
    mv /dobot/userdata/${name}_sys_files /dobot/userdata/${name}_sys_files_bak # 备份当前的升级包内的系统的内容
    mkdir /dobot/userdata/${name}_sys_files  # 创建一个新的当前机型的文件夹
    cp -r /dobot/userdata/projectOld /dobot/userdata/${name}_sys_files #将之前的系统内的参数复制到指定机型的 文件夹内
    mv  /dobot/userdata/${name}_sys_files/projectOld /dobot/userdata/${name}_sys_files/project # 路径调整
    cp -rf /dobot/userdata/${name}_sys_files_bak/project/* /dobot/userdata/${name}_sys_files/project # 覆盖 本次升级准备替换的文件内容   
    rm -rf /dobot/userdata/${name}_sys_files_bak    # 删除备份的本次升级的文件内容

    ln -snf "/dobot/userdata/"$name"_sys_files/project" "/dobot/userdata/" # 创建软链接
    if [ ! -L "/dobot/userdata/project" ];then
        echo "soft link for "$name" create failed .....   "
        exit -1
    else
        echo "soft line for "$name" create success "
    fi
    # 参数的调整分为了三个阶段 1. 使用新版本参数创建文件夹 2. 旧版本的参数覆盖新版本的参数（主要是恢复结构参数等） 3. 新版参数覆盖 
    # 因为新版本的升级包参数 不包含 结构参数等
    echo "file operation done "
else
    echo "/dobot/userdata/project is Link ..... ,do not need to transform"
fi

if [ ! -f "/dobot/userdata/port" ];then
    cp "/dobot/userdata/CR5_sys_files/port"      "/dobot/userdata/"
fi 

if [ ! -f "/dobot/userdata/tty2ssh" ];then
    cp "/dobot/userdata/CR5_sys_files/tty2ssh"      "/dobot/userdata/"
fi 

if [ ! -f "/dobot/userdata/slaveinfo" ];then
    cp "/dobot/userdata/CR5_sys_files/slaveinfo"      "/dobot/userdata/"
fi 
    
sync
