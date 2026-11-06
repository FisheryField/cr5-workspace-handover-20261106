@echo off
set "SSH_ASKPASS=%~dp0.askpass.cmd"
set "SSH_ASKPASS_REQUIRE=force"
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile="%~dp0.ssh_agent\known_hosts" -o PreferredAuthentications=password -o NumberOfPasswordPrompts=1 -o ConnectTimeout=15 root@192.168.5.1 "sh -s" < %1
