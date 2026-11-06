mg6flag=$(cat /dobot/userdata/robotType)
echo $mg6flag
#update
if [ -f "/dobot/userdata/project/bin.tar.gz" ]; then
	ls /dobot/userdata/project/bin.tar.gz -l
	echo "...... find /dobot/userdata/project/bin.tar.gz, start update"
	cd /dobot/
	echo "...... start rm bin,update"
	rm /dobot/bin/ -rf
	tar zxvf /dobot/userdata/project/bin.tar.gz -C /dobot
	rm -f /dobot/userdata/project/bin.tar.gz
	if [ -d "/dobot/system/home/ftp/PlcLogic/Application" ];then
		cp -rf /dobot/system/home/ftp/PlcLogic/Application /home/ftp/PlcLogic
		rm -rf /dobot/system/home/ftp/PlcLogic/Application
	fi
	sync
	cp lib/libevent* /usr/lib/
	echo "..... update finish"
fi

if [ -f "/dobot/userdata/afterUpdate.sh" ];then  # 第一次刷机的时候会带入这个文件 用来进行软链接的创建
	chmod +x /dobot/userdata/afterUpdate.sh
	/dobot/userdata/afterUpdate.sh
	rm /dobot/userdata/afterUpdate.sh
fi

#check update
rm -rf /tmp/update
if [ -b /dev/sda1 ]; then
    echo "Runing mount > /dobot/usb/"
    mkdir -p /dobot/usb
	count=1
	while [ $count -le 30 ]; do
		mount /dev/sda1 /dobot/usb
		ls /dobot/usb/ >> /ovalgeee
		if [ -f /dobot/usb/Controller_6R.tar.gz ]; then
			rm -rf /dobot/bin
			tar -zxvf /dobot/usb/Controller_6R.tar.gz -C /dobot
			if [ ! -d "/dobot/system/home/ftp/PlcLogic/Application" ];then
				mkdir "/dobot/system/home/ftp/PlcLogic/Application"
			fi
			if [ -d "/dobot/system/home/ftp/PlcLogic/Application" ];then
                cp -rf /dobot/system/home/ftp/PlcLogic/Application /home/ftp/PlcLogic
                rm -rf /dobot/system/home/ftp/PlcLogic/Application
				echo "..... update codesys"
			fi
			touch /tmp/update
			sync
			umount /dobot/usb
			break
		fi
		sleep 0.01
		count=$(($count + 1))
	done
else
    echo "Runing WLAN......"
fi 

if [ ! -d "/home/ftp/PlcLogic/Application" ];then # 2021-11-08 if not exist dir make it .
	mkdir -p "/home/ftp/PlcLogic/Application"
fi 

if [ -f "/dobot/Application.app" ]; then 
	echo " find Application.app  move it ......"
	mv "/dobot/Application.app" "/home/ftp/PlcLogic/Application/"
fi

if [ -f "/dobot/Application.crc" ]; then 
	echo " find Application.crc move it ......"
	mv "/dobot/Application.crc" "/home/ftp/PlcLogic/Application/"
fi

if [ -f "/etc/timezone.sh" ]; then
     /etc/timezone.sh 
fi

if [ -d "/dobot/userdata/project/process" ];then # 2021-09-23 if the top dir is not exist maybe something wrong 
	if [ ! -d "/dobot/userdata/project/process/identify" ];then 
		mkdir "/dobot/userdata/project/process/identify"
	fi
	if [ ! -d "/dobot/userdata/project/process/trajectory" ];then 
		mkdir "/dobot/userdata/project/process/trajectory"
	fi
	if [ ! -d "/dobot/userdata/project/process/pallet" ];then 
		mkdir "/dobot/userdata/project/process/pallet"
	fi
else 
	mkdir /dobot/userdata/project/process
	mkdir /dobot/userdata/project/process/elecSkin
	mkdir /dobot/userdata/project/process/identify
	mkdir /dobot/userdata/project/process/pallet
	mkdir /dobot/userdata/project/process/screw
	mkdir /dobot/userdata/project/process/sixForce
	mkdir /dobot/userdata/project/process/track
	mkdir /dobot/userdata/project/process/trajectory
	mkdir /dobot/userdata/project/process/vision
fi

if [[ $mg6flag != "MG6" ]]; then 
	if [  -b "/dev/mmcblk3p5" ];then                          #-b file exists and is a block special file.
		if [ ! -d "/dobot/userdata/project/logs" ];then
			mkdir "/dobot/userdata/project/logs"
		fi
		mount /dev/mmcblk3p5 /dobot/userdata/project/logs
		if [ ! -d "/dobot/userdata/project/logs/server" ];then
			mkdir "/dobot/userdata/project/logs/server"
		fi
		if [ ! -d "/dobot/userdata/project/logs/lua" ];then
			mkdir "/dobot/userdata/project/logs/lua"
		fi
		if [ ! -d "/dobot/userdata/project/logs/algs" ];then
			mkdir "/dobot/userdata/project/logs/algs"
		fi
		if [ ! -d "/dobot/userdata/project/logs/blackbox" ];then 
			mkdir "/dobot/userdata/project/logs/blackbox"
		fi
		if [ ! -d "/dobot/userdata/project/logs/all" ];then 
			mkdir "/dobot/userdata/project/logs/all"
		fi
		if [ ! -d "/dobot/userdata/project/logs/http" ];then 
			mkdir "/dobot/userdata/project/logs/http"
		fi
		if [ ! -d "/dobot/userdata/project/logs/codesys" ];then 
			mkdir "/dobot/userdata/project/logs/codesys"
		fi
		if [ ! -d "/dobot/userdata/project/logs/gcontrol" ];then 
			mkdir "/dobot/userdata/project/logs/gcontrol"
		fi
	fi
else 
	if [ ! -d "/dobot/userdata/project/logs" ];then
		mkdir "/dobot/userdata/project/logs"
	fi
	if [ ! -d "/dobot/userdata/project/logs/server" ];then
		mkdir "/dobot/userdata/project/logs/server"
	fi
	if [ ! -d "/dobot/userdata/project/logs/lua" ];then
		mkdir "/dobot/userdata/project/logs/lua"
	fi
	if [ ! -d "/dobot/userdata/project/logs/algs" ];then
		mkdir "/dobot/userdata/project/logs/algs"
	fi
	if [ ! -d "/dobot/userdata/project/logs/blackbox" ];then 
		mkdir "/dobot/userdata/project/logs/blackbox"
	fi
	if [ ! -d "/dobot/userdata/project/logs/all" ];then 
		mkdir "/dobot/userdata/project/logs/all"
	fi
	if [ ! -d "/dobot/userdata/project/logs/http" ];then 
		mkdir "/dobot/userdata/project/logs/http"
	fi
	if [ ! -d "/dobot/userdata/project/logs/codesys" ];then 
		mkdir "/dobot/userdata/project/logs/codesys"
	fi
	if [ ! -d "/dobot/userdata/project/logs/gcontrol" ];then 
		mkdir "/dobot/userdata/project/logs/gcontrol"
	fi
fi
/dobot/bin/logServer &  

if [ -d "/home/ovalgee/Projects/RobotController_4R/project/Robot4Axis_win/bin" ]; then
	topdir=/home/ovalgee/Projects/RobotController_4R/project/Robot4Axis_win/bin
	export PATH=/home/ovalgee/Projects/toolchain/arm-linux-gcc-6.3.1/bin:/home/ovalgee/Projects/iSCARA/Linux/toolchain/i686-linux-gcc-5.1.0/bin:$PATH
	export LD_LIBRARY_PATH=/home/ovalgee/Projects/toolchain/i686-linux-gcc-5.1.0/lib:$LD_LIBRARY_PATH
	qtdir=$topdir/lib/qt
elif [ -d "/home/ovalgee/Projects/iSCARA/RobotController_4R/trunk/RobotController/Linux/project/Robot4Axis_win/bin" ]; then
	topdir=/home/ovalgee/Projects/iSCARA/RobotController_4R/trunk/RobotController/Linux/project/Robot4Axis_win/bin
	export PATH=/home/ovalgee/Projects/iSCARA/Linux/toolchain/arm-linux-gcc-6.3.1/bin:/home/ovalgee/Projects/iSCARA/Linux/toolchain/i686-linux-gcc-5.1.0/bin:$PATH
	export LD_LIBRARY_PATH=/home/ovalgee/Projects/iSCARA/Linux/toolchain/i686-linux-gcc-5.1.0/lib:$LD_LIBRARY_PATH
	qtdir=$topdir/lib/qt
elif [ -d "/dobot/bin" ]; then
	topdir=/dobot/bin
	qtdir=/usr/local/qt-4.8.6
else
	echo "You must indicat path"
	exit 1
fi

tmpdir=$topdir/tmp

export LD_LIBRARY_PATH=$topdir/lib:$qtdir/lib:/usr/local/samba/lib:/usr/lib:$LD_LIBRARY_PATH
export PATH=$PYTHONHOME/bin:/usr/local/samba/bin:/usr/local/samba/sbin:$PATH

export LUA_PATH=$topdir/lua/?.lua
export LUA_CPATH=$topdir/lib/?.so

#clean tmp dir
rm -rf $tmpdir
mkdir -p $tmpdir
mkdir -p $tmpdir/smb
rm -f /project
ln -s $topdir/project /project

#check dir
if [ ! -d "log" ]; then
	mkdir log
fi
if [ ! -f "$topdir/etc/version.conf" ]; then
	echo "010000" > $topdir/etc/version.conf
fi

#log setting
logcntfile=$topdir/log/cnt.conf
logtypefile=$topdir/log/type.conf
logtempfile=/tmp/log_temp.conf
if [ ! -f "$logtypefile" ]; then
	echo file > $logtypefile
fi
logtype=$(cat ${logtypefile}) #stdout, socket, file
if [ -f "$logcntfile" ]; then
	logcnt=`awk '{print NR}' ${logcntfile}|tail -n1`
	allcount=`head -1 ${logcntfile}`
	if [ $logcnt -gt $allcount ]; then
		delfile=`sed -n '2p' ${logcntfile}`
		sed -i '2d' $logcntfile;
		rm -rf log/$delfile
	fi
fi

if [ ! -d "/dobot/userdata/project/redis" ]; then
	mkdir -p /dobot/userdata/project/redis
	#mount /dev/mmcblk3p5 /dobot/userdata/project/redis
fi

chmod 777 -R /dobot/bin
rm /dobot/userdata/project/redis/stdout -f
/dobot/bin/bin/redis-server /dobot/bin/etc/redis.conf
#  change mac to setted
if [ -f "/etc/mac" ]; then
	echo set mac to $(cat /etc/mac)
	/sbin/ifconfig eth2 down
	/sbin/ifconfig eth2 hw ether $(cat /etc/mac)
	/sbin/ifconfig eth2 up
	/sbin/ifconfig eth1 down
	/sbin/ifconfig eth1 hw ether $(cat /etc/mac)
	/sbin/ifconfig eth1 up
fi
#start smb
rm /usr/local/samba/ -rf
mkdir /usr/local/samba/
mkdir /usr/local/samba/private
mkdir /usr/local/samba/swat
mkdir /usr/local/samba/var
if [ -d "/usr/local/samba" ];then
/dobot/bin/bin/nmbd -s /dobot/bin/etc/smb.conf -D 
/dobot/bin/bin/smbd -s /dobot/bin/etc/smb.conf -D 
else
chmod 777 -R /usr/local/samba
/usr/local/samba/sbin/smbd -s /usr/local/samba/lib/smb.conf -D &
fi

#选择是否开启dhcp
dhcpflag=`grep eth2_dhcp /dobot/userdata/project/settings/iscara.conf | awk -F '=' '{print $2}'`
echo $dhcpflag

if [[ $dhcpflag == "true" ]]; then
	udhcpc -b -i eth2 -p /var/run/lan_udhcpc.pid -R  # 2021-09-01 add udhcpc run in back
else
	#判断是否修改网关
	ipflag=`grep eth2_ip /dobot/userdata/project/settings/iscara.conf | awk -F '=' '{print $2}'`
	gwflag=`grep eth2_gw /dobot/userdata/project/settings/iscara.conf | awk -F '=' '{print $2}'`
	maskflag=`grep eth2_mask /dobot/userdata/project/settings/iscara.conf | awk -F '=' '{print $2}'`
	echo $ipflag
	echo $gwflag
	echo $maskflag

	if [[ $ipflag == "" ] || [ $gwflag == "" ] || [ $maskflag == "" ]]; then
		chattr -i /etc/resolv.conf
		rm /etc/resolv.conf
    	echo "nameserver 127.0.0.1" > /etc/resolv.conf
		chattr +i /etc/resolv.conf
		ifconfig eth2 192.168.5.1 netmask 255.255.255.0
		route add -net 192.168.5.0/24 gw 192.168.5.1 eth2
		sleep 2
	else
		chattr -i /etc/resolv.conf
		rm /etc/resolv.conf
		echo "nameserver 127.0.0.1" > /etc/resolv.conf
		chattr +i /etc/resolv.conf
		ifconfig eth2 $ipflag netmask $maskflag
		route add default gw $gwflag
		sleep 2
    fi
fi

#ifconfig eth2 192.168.5.1 netmask 255.255.255.0
option="${1}"
case ${option} in
    -codesys)
        echo "[start] codesys"
	      if [ "$logtype" == "file" ]; then
	      	if [ ! -f "$logcntfile" ]; then
	 			echo 30 > $logcntfile
	  		fi
	  		logf=`cat /dev/urandom | head -n 10 | md5sum | head -c 10`
	     	echo $logf >> $logcntfile
	 		echo $logf > $logtempfile
	 		sync
	      fi       
		chmod +x /dobot/bin/gcontrol    
		if [[ $mg6flag != "MG6" ]]; then  
			/dobot/bin/gcontrol &      
		fi                                                                                                                        
		sleep 5
		/dobot/bin/getVersion > /dobot/userdata/SlaveLog
		ifconfig eth0 -promisc
		cat /dobot/userdata/SlaveLog
		if [ -f "/tmp/codesysBoot" ];then 
			echo "codesys for boot check done ,will boot $(cat /tmp/codesysBoot)"
			if [ -d $(cat /tmp/codesysBoot) ];then 
				echo "path of codesys $(cat /tmp/codesysBoot) exist , will change codesys to boot ... "
				rm -r /home/ftp/PlcLogic/Application/*
				cp $(cat /tmp/codesysBoot)* /home/ftp/PlcLogic/Application/ -rf
			else 
				echo "path of codesys $(cat /tmp/codesysBoot) not exist , will not change codesys to boot ... "
			fi 
		else 
			echo "codesys for boot check failed"
		fi		
		sleep 1
		if [[ $mg6flag != "MG6" ]]; then 
        	cd /opt/codesys/Platforms/Linux/Bin                                                              
        	./codesysload & 
		else 
			cd /opt/codesys 
			chmod +x aabbccdd
			cp aabbccdd codesyscontrol
			cp /home/ftp/.dobotConfig/CODESYSControl.cfg ./CODESYSControl.cfg
			./codesyscontrol & 
			rm codesyscontrol 
			sleep 1
			/dobot/bin/gcontrol &
		fi
        ;;
   -env)
	 echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
	 echo "PATH=$PATH"
      ;;
   -dobot) 
      echo "[start] iscara"
      if [ "$logtype" == "file" ]; then
      	if [ ! -f "$logcntfile" ]; then
 			echo 30 > $logcntfile
  		fi
  		logf=`cat /dev/urandom | head -n 10 | md5sum | head -c 10`
     	echo $logf >> $logcntfile
 		echo $logf > $logtempfile
 		sync
      fi
	  ./iscara
	  ;;
	-clog)
		echo "[start] clear all log"
	  	if [ -f "$logcntfile" ]; then
			allcount=1
			if [ "$logtype" == "file" ]; then
				allcount=2
			fi
			logcnt=`awk '{print NR}' ${logcntfile}|tail -n1`
			while [[ $logcnt -gt $allcount ]]  
			do 
				delfile=`sed -n '2p' ${logcntfile}`
				sed -i '2d' $logcntfile
				if [ -f "log/$delfile" ]; then
					rm -rf log/$delfile
				fi
				logcnt=`awk '{print NR}' ${logcntfile}|tail -n1`
			done
		fi
	  ;;
   *)
	  echo "`basename ${0}`:usage: "
	  echo "codesys"	"start codesys"
	  echo "[-env]   	echo current environment"
	  echo "[-dobot]  	start scara"
	  echo "[-clog]   	clear all log"
      exit 1 # Command to come out of the program with status 1
      ;;

esac

chmod +x /dobot/bin/autoCacheFree.sh
/dobot/bin/autoCacheFree.sh &

chmod +x /dobot/bin/autoSync.sh
/dobot/bin/autoSync.sh &