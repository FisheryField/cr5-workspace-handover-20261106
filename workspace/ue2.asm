
libdataSvr.so.bin:     file format elf32-littlearm


Disassembly of section .text:

001d9e90 <robot_control::updateEncoderData()>:
  1d9e90:	e92d 47f0 	stmdb	sp!, {r4, r5, r6, r7, r8, r9, sl, lr}
  1d9e94:	b086      	sub	sp, #24
  1d9e96:	4d4e      	ldr	r5, [pc, #312]	; (1d9fd0 <robot_control::updateEncoderData()+0x140>)
  1d9e98:	4c4e      	ldr	r4, [pc, #312]	; (1d9fd4 <robot_control::updateEncoderData()+0x144>)
  1d9e9a:	447d      	add	r5, pc
  1d9e9c:	f205 45f4 	addw	r5, r5, #1268	; 0x4f4
  1d9ea0:	447c      	add	r4, pc
  1d9ea2:	f6da edd8 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
  1d9ea6:	2302      	movs	r3, #2
  1d9ea8:	f240 11e9 	movw	r1, #489	; 0x1e9
  1d9eac:	462a      	mov	r2, r5
  1d9eae:	f06f 000f 	mvn.w	r0, #15
  1d9eb2:	9400      	str	r4, [sp, #0]
  1d9eb4:	f6e0 ed22 	blx	ba8fc <void spdlog::logTerminal::basicLog<>(int, int, char const*, spdlog::level::level_enum, char const*)@plt>
  1d9eb8:	f6dd eae8 	blx	b748c <DataSvr::instance()@plt>
  1d9ebc:	2102      	movs	r1, #2
  1d9ebe:	f6dd eaaa 	blx	b7414 <SubProcessFactory::getInterface(ISubProcess::SPType) const@plt>
  1d9ec2:	4606      	mov	r6, r0
  1d9ec4:	2800      	cmp	r0, #0
  1d9ec6:	d073      	beq.n	1d9fb0 <robot_control::updateEncoderData()+0x120>
  1d9ec8:	f8df 910c 	ldr.w	r9, [pc, #268]	; 1d9fd8 <robot_control::updateEncoderData()+0x148>
  1d9ecc:	f500 5704 	add.w	r7, r0, #8448	; 0x2100
  1d9ed0:	f8df a108 	ldr.w	sl, [pc, #264]	; 1d9fdc <robot_control::updateEncoderData()+0x14c>
  1d9ed4:	463c      	mov	r4, r7
  1d9ed6:	3426      	adds	r4, #38	; 0x26
  1d9ed8:	3720      	adds	r7, #32
  1d9eda:	44f9      	add	r9, pc
  1d9edc:	f10d 080c 	add.w	r8, sp, #12
  1d9ee0:	44fa      	add	sl, pc
  1d9ee2:	2309      	movs	r3, #9
  1d9ee4:	9302      	str	r3, [sp, #8]
  1d9ee6:	f8d6 2e20 	ldr.w	r2, [r6, #3616]	; 0xe20
  1d9eea:	2100      	movs	r1, #0
  1d9eec:	4608      	mov	r0, r1
  1d9eee:	463b      	mov	r3, r7
  1d9ef0:	468e      	mov	lr, r1
  1d9ef2:	9103      	str	r1, [sp, #12]
  1d9ef4:	f8d2 10f4 	ldr.w	r1, [r2, #244]	; 0xf4
  1d9ef8:	3301      	adds	r3, #1
  1d9efa:	f502 629b 	add.w	r2, r2, #1240	; 0x4d8
  1d9efe:	2901      	cmp	r1, #1
  1d9f00:	bf06      	itte	eq
  1d9f02:	f803 1c01 	strbeq.w	r1, [r3, #-1]
  1d9f06:	3001      	addeq	r0, #1
  1d9f08:	f803 ec01 	strbne.w	lr, [r3, #-1]
  1d9f0c:	42a3      	cmp	r3, r4
  1d9f0e:	d1f1      	bne.n	1d9ef4 <robot_control::updateEncoderData()+0x64>
  1d9f10:	9003      	str	r0, [sp, #12]
  1d9f12:	f6da eda0 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
  1d9f16:	2302      	movs	r3, #2
  1d9f18:	f8cd 8004 	str.w	r8, [sp, #4]
  1d9f1c:	f8cd 9000 	str.w	r9, [sp]
  1d9f20:	462a      	mov	r2, r5
  1d9f22:	f240 11fb 	movw	r1, #507	; 0x1fb
  1d9f26:	f06f 000f 	mvn.w	r0, #15
  1d9f2a:	f6df efbe 	blx	b9ea8 <void spdlog::logTerminal::basicLog<int&>(int, int, char const*, spdlog::level::level_enum, char const*, int&)@plt>
  1d9f2e:	9b03      	ldr	r3, [sp, #12]
  1d9f30:	2b06      	cmp	r3, #6
  1d9f32:	d02a      	beq.n	1d9f8a <robot_control::updateEncoderData()+0xfa>
  1d9f34:	f6da ed8e 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
  1d9f38:	ab02      	add	r3, sp, #8
  1d9f3a:	462a      	mov	r2, r5
  1d9f3c:	9301      	str	r3, [sp, #4]
  1d9f3e:	f44f 7100 	mov.w	r1, #512	; 0x200
  1d9f42:	2302      	movs	r3, #2
  1d9f44:	f06f 000f 	mvn.w	r0, #15
  1d9f48:	f8cd a000 	str.w	sl, [sp]
  1d9f4c:	f6df efac 	blx	b9ea8 <void spdlog::logTerminal::basicLog<int&>(int, int, char const*, spdlog::level::level_enum, char const*, int&)@plt>
  1d9f50:	f04f 0e00 	mov.w	lr, #0
  1d9f54:	a804      	add	r0, sp, #16
  1d9f56:	f249 3ce0 	movw	ip, #37856	; 0x93e0
  1d9f5a:	4673      	mov	r3, lr
  1d9f5c:	f2c0 0c04 	movt	ip, #4
  1d9f60:	4672      	mov	r2, lr
  1d9f62:	9000      	str	r0, [sp, #0]
  1d9f64:	4671      	mov	r1, lr
  1d9f66:	4670      	mov	r0, lr
  1d9f68:	f8cd c014 	str.w	ip, [sp, #20]
  1d9f6c:	f8cd e010 	str.w	lr, [sp, #16]
  1d9f70:	f6df ebac 	blx	b96cc <select@plt>
  1d9f74:	9b02      	ldr	r3, [sp, #8]
  1d9f76:	1e5a      	subs	r2, r3, #1
  1d9f78:	9202      	str	r2, [sp, #8]
  1d9f7a:	2b00      	cmp	r3, #0
  1d9f7c:	d1b3      	bne.n	1d9ee6 <robot_control::updateEncoderData()+0x56>
  1d9f7e:	4630      	mov	r0, r6
  1d9f80:	f6df eb42 	blx	b9608 <DataSubProcess::updateEncoderData()@plt>
  1d9f84:	b006      	add	sp, #24
  1d9f86:	e8bd 87f0 	ldmia.w	sp!, {r4, r5, r6, r7, r8, r9, sl, pc}
  1d9f8a:	4c15      	ldr	r4, [pc, #84]	; (1d9fe0 <robot_control::updateEncoderData()+0x150>)
  1d9f8c:	f6da ed62 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
  1d9f90:	462a      	mov	r2, r5
  1d9f92:	2302      	movs	r3, #2
  1d9f94:	447c      	add	r4, pc
  1d9f96:	f240 11fd 	movw	r1, #509	; 0x1fd
  1d9f9a:	f06f 000f 	mvn.w	r0, #15
  1d9f9e:	9400      	str	r4, [sp, #0]
  1d9fa0:	f6e0 ecac 	blx	ba8fc <void spdlog::logTerminal::basicLog<>(int, int, char const*, spdlog::level::level_enum, char const*)@plt>
  1d9fa4:	4630      	mov	r0, r6
  1d9fa6:	f6df eb30 	blx	b9608 <DataSubProcess::updateEncoderData()@plt>
  1d9faa:	b006      	add	sp, #24
  1d9fac:	e8bd 87f0 	ldmia.w	sp!, {r4, r5, r6, r7, r8, r9, sl, pc}
  1d9fb0:	4c0c      	ldr	r4, [pc, #48]	; (1d9fe4 <robot_control::updateEncoderData()+0x154>)
  1d9fb2:	f6da ed50 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
  1d9fb6:	f06f 000f 	mvn.w	r0, #15
  1d9fba:	462a      	mov	r2, r5
  1d9fbc:	447c      	add	r4, pc
  1d9fbe:	2304      	movs	r3, #4
  1d9fc0:	f240 11ed 	movw	r1, #493	; 0x1ed
  1d9fc4:	9400      	str	r4, [sp, #0]
  1d9fc6:	f6e0 ec9a 	blx	ba8fc <void spdlog::logTerminal::basicLog<>(int, int, char const*, spdlog::level::level_enum, char const*)@plt>
  1d9fca:	f04f 30ff 	mov.w	r0, #4294967295	; 0xffffffff
  1d9fce:	e7d9      	b.n	1d9f84 <robot_control::updateEncoderData()+0xf4>
  1d9fd0:	0005a49a 	.word	0x0005a49a
  1d9fd4:	0005af90 	.word	0x0005af90
  1d9fd8:	0005aeee 	.word	0x0005aeee
  1d9fdc:	0005af14 	.word	0x0005af14
  1d9fe0:	0005ae48 	.word	0x0005ae48
  1d9fe4:	0005add0 	.word	0x0005add0
