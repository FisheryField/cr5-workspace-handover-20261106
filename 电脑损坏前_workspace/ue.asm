
libdataSvr.so.bin:     file format elf32-littlearm


Disassembly of section .text:

000f9520 <DataSubProcess::updateEncoderData()>:
   f9520:	e92d 4ff0 	stmdb	sp!, {r4, r5, r6, r7, r8, r9, sl, fp, lr}
   f9524:	f2ad 5d4c 	subw	sp, sp, #1356	; 0x54c
   f9528:	ab44      	add	r3, sp, #272	; 0x110
   f952a:	4607      	mov	r7, r0
   f952c:	ae14      	add	r6, sp, #80	; 0x50
   f952e:	ad18      	add	r5, sp, #96	; 0x60
   f9530:	9306      	str	r3, [sp, #24]
   f9532:	f04f 0800 	mov.w	r8, #0
   f9536:	f7bb ea8e 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
   f953a:	f8df 4664 	ldr.w	r4, [pc, #1636]	; f9ba0 <DataSubProcess::updateEncoderData()+0x680>
   f953e:	2302      	movs	r3, #2
   f9540:	f8df 2660 	ldr.w	r2, [pc, #1632]	; f9ba4 <DataSubProcess::updateEncoderData()+0x684>
   f9544:	f643 515b 	movw	r1, #15707	; 0x3d5b
   f9548:	f06f 000f 	mvn.w	r0, #15
   f954c:	9603      	str	r6, [sp, #12]
   f954e:	447c      	add	r4, pc
   f9550:	9504      	str	r5, [sp, #16]
   f9552:	447a      	add	r2, pc
   f9554:	9400      	str	r4, [sp, #0]
   f9556:	3a44      	subs	r2, #68	; 0x44
   f9558:	ac1c      	add	r4, sp, #112	; 0x70
   f955a:	940f      	str	r4, [sp, #60]	; 0x3c
   f955c:	f7c1 e9ce 	blx	ba8fc <void spdlog::logTerminal::basicLog<>(int, int, char const*, spdlog::level::level_enum, char const*)@plt>
   f9560:	2300      	movs	r3, #0
   f9562:	f44f 6280 	mov.w	r2, #1024	; 0x400
   f9566:	4619      	mov	r1, r3
   f9568:	9806      	ldr	r0, [sp, #24]
   f956a:	f7c0 ef96 	blx	ba498 <rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>::GenericDocument(rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>*, unsigned int, rapidjson::CrtAllocator*)@plt>
   f956e:	4630      	mov	r0, r6
   f9570:	2104      	movs	r1, #4
   f9572:	f7bb eb3e 	blx	b4bf0 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::GenericValue(rapidjson::Type)@plt>
   f9576:	4628      	mov	r0, r5
   f9578:	2104      	movs	r1, #4
   f957a:	f7bb eb3a 	blx	b4bf0 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::GenericValue(rapidjson::Type)@plt>
   f957e:	ab20      	add	r3, sp, #128	; 0x80
   f9580:	4620      	mov	r0, r4
   f9582:	461d      	mov	r5, r3
   f9584:	930a      	str	r3, [sp, #40]	; 0x28
   f9586:	2104      	movs	r1, #4
   f9588:	ab24      	add	r3, sp, #144	; 0x90
   f958a:	461c      	mov	r4, r3
   f958c:	9305      	str	r3, [sp, #20]
   f958e:	f7bb eb30 	blx	b4bf0 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::GenericValue(rapidjson::Type)@plt>
   f9592:	4628      	mov	r0, r5
   f9594:	2103      	movs	r1, #3
   f9596:	f7bb eb2c 	blx	b4bf0 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::GenericValue(rapidjson::Type)@plt>
   f959a:	2104      	movs	r1, #4
   f959c:	4620      	mov	r0, r4
   f959e:	f7bb eb28 	blx	b4bf0 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::GenericValue(rapidjson::Type)@plt>
   f95a2:	ae10      	add	r6, sp, #64	; 0x40
   f95a4:	4640      	mov	r0, r8
   f95a6:	f8c6 8000 	str.w	r8, [r6]
   f95aa:	f7c1 ef6e 	blx	bb488 <time@plt>
   f95ae:	ab52      	add	r3, sp, #328	; 0x148
   f95b0:	9011      	str	r0, [sp, #68]	; 0x44
   f95b2:	461c      	mov	r4, r3
   f95b4:	930c      	str	r3, [sp, #48]	; 0x30
   f95b6:	ab11      	add	r3, sp, #68	; 0x44
   f95b8:	46a2      	mov	sl, r4
   f95ba:	4618      	mov	r0, r3
   f95bc:	f7be ea56 	blx	b7a6c <localtime@plt>
   f95c0:	abd2      	add	r3, sp, #840	; 0x348
   f95c2:	4605      	mov	r5, r0
   f95c4:	4641      	mov	r1, r8
   f95c6:	4620      	mov	r0, r4
   f95c8:	f44f 7200 	mov.w	r2, #512	; 0x200
   f95cc:	461c      	mov	r4, r3
   f95ce:	930b      	str	r3, [sp, #44]	; 0x2c
   f95d0:	46a1      	mov	r9, r4
   f95d2:	f7bd e9ba 	blx	b6948 <memset@plt+0x4>
   f95d6:	4641      	mov	r1, r8
   f95d8:	4620      	mov	r0, r4
   f95da:	f44f 7200 	mov.w	r2, #512	; 0x200
   f95de:	f7bd e9b4 	blx	b6948 <memset@plt+0x4>
   f95e2:	68ec      	ldr	r4, [r5, #12]
   f95e4:	f44f 7100 	mov.w	r1, #512	; 0x200
   f95e8:	696b      	ldr	r3, [r5, #20]
   f95ea:	4650      	mov	r0, sl
   f95ec:	f8df 25b8 	ldr.w	r2, [pc, #1464]	; f9ba8 <DataSubProcess::updateEncoderData()+0x688>
   f95f0:	9401      	str	r4, [sp, #4]
   f95f2:	692c      	ldr	r4, [r5, #16]
   f95f4:	f203 736c 	addw	r3, r3, #1900	; 0x76c
   f95f8:	447a      	add	r2, pc
   f95fa:	3401      	adds	r4, #1
   f95fc:	9400      	str	r4, [sp, #0]
   f95fe:	f7bd ebda 	blx	b6db4 <snprintf@plt>
   f9602:	682c      	ldr	r4, [r5, #0]
   f9604:	f44f 7100 	mov.w	r1, #512	; 0x200
   f9608:	68ab      	ldr	r3, [r5, #8]
   f960a:	4648      	mov	r0, r9
   f960c:	f8df 259c 	ldr.w	r2, [pc, #1436]	; f9bac <DataSubProcess::updateEncoderData()+0x68c>
   f9610:	9401      	str	r4, [sp, #4]
   f9612:	686c      	ldr	r4, [r5, #4]
   f9614:	447a      	add	r2, pc
   f9616:	9400      	str	r4, [sp, #0]
   f9618:	f7bd ebcc 	blx	b6db4 <snprintf@plt>
   f961c:	f8df 0590 	ldr.w	r0, [pc, #1424]	; f9bb0 <DataSubProcess::updateEncoderData()+0x690>
   f9620:	4641      	mov	r1, r8
   f9622:	4478      	add	r0, pc
   f9624:	f7bf eb58 	blx	b8cd8 <access@plt>
   f9628:	2800      	cmp	r0, #0
   f962a:	f040 80f9 	bne.w	f9820 <DataSubProcess::updateEncoderData()+0x300>
   f962e:	f7bb ea12 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
   f9632:	f8df 2580 	ldr.w	r2, [pc, #1408]	; f9bb4 <DataSubProcess::updateEncoderData()+0x694>
   f9636:	2302      	movs	r3, #2
   f9638:	f8df 457c 	ldr.w	r4, [pc, #1404]	; f9bb8 <DataSubProcess::updateEncoderData()+0x698>
   f963c:	f643 5174 	movw	r1, #15732	; 0x3d74
   f9640:	f06f 000f 	mvn.w	r0, #15
   f9644:	447a      	add	r2, pc
   f9646:	447c      	add	r4, pc
   f9648:	3a44      	subs	r2, #68	; 0x44
   f964a:	9400      	str	r4, [sp, #0]
   f964c:	f7c1 e956 	blx	ba8fc <void spdlog::logTerminal::basicLog<>(int, int, char const*, spdlog::level::level_enum, char const*)@plt>
   f9650:	9c06      	ldr	r4, [sp, #24]
   f9652:	f8df 0568 	ldr.w	r0, [pc, #1384]	; f9bbc <DataSubProcess::updateEncoderData()+0x69c>
   f9656:	4621      	mov	r1, r4
   f9658:	4478      	add	r0, pc
   f965a:	f7c1 eb62 	blx	bad20 <dobot::common::util::JsonUtil::readJsonFile(char const*, rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>&)@plt+0x4>
   f965e:	f8df 1560 	ldr.w	r1, [pc, #1376]	; f9bc0 <DataSubProcess::updateEncoderData()+0x6a0>
   f9662:	4620      	mov	r0, r4
   f9664:	4479      	add	r1, pc
   f9666:	f7ba ef7c 	blx	b4560 <rapidjson::internal::DisableIf<rapidjson::internal::RemoveSfinaeTag<rapidjson::internal::SfinaeTag& (*)(rapidjson::internal::NotExpr<rapidjson::internal::IsSame<rapidjson::internal::RemoveConst<char const>::Type, char> >)>::Type, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&>::Type rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::operator[]<char const>(char const*)@plt>
   f966a:	89c3      	ldrh	r3, [r0, #14]
   f966c:	2b04      	cmp	r3, #4
   f966e:	f040 8295 	bne.w	f9b9c <DataSubProcess::updateEncoderData()+0x67c>
   f9672:	6803      	ldr	r3, [r0, #0]
   f9674:	6033      	str	r3, [r6, #0]
   f9676:	f7bb e9ee 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
   f967a:	f8df 2548 	ldr.w	r2, [pc, #1352]	; f9bc4 <DataSubProcess::updateEncoderData()+0x6a4>
   f967e:	2302      	movs	r3, #2
   f9680:	f8df 4544 	ldr.w	r4, [pc, #1348]	; f9bc8 <DataSubProcess::updateEncoderData()+0x6a8>
   f9684:	f643 5178 	movw	r1, #15736	; 0x3d78
   f9688:	9601      	str	r6, [sp, #4]
   f968a:	f06f 000f 	mvn.w	r0, #15
   f968e:	447a      	add	r2, pc
   f9690:	447c      	add	r4, pc
   f9692:	3a44      	subs	r2, #68	; 0x44
   f9694:	9400      	str	r4, [sp, #0]
   f9696:	f7c0 ec08 	blx	b9ea8 <void spdlog::logTerminal::basicLog<int&>(int, int, char const*, spdlog::level::level_enum, char const*, int&)@plt>
   f969a:	9b06      	ldr	r3, [sp, #24]
   f969c:	691d      	ldr	r5, [r3, #16]
   f969e:	2d00      	cmp	r5, #0
   f96a0:	f000 827a 	beq.w	f9b98 <DataSubProcess::updateEncoderData()+0x678>
   f96a4:	6833      	ldr	r3, [r6, #0]
   f96a6:	2b09      	cmp	r3, #9
   f96a8:	f300 81a8 	bgt.w	f99fc <DataSubProcess::updateEncoderData()+0x4dc>
   f96ac:	f507 5303 	add.w	r3, r7, #8384	; 0x20c0
   f96b0:	f507 5904 	add.w	r9, r7, #8448	; 0x2100
   f96b4:	461a      	mov	r2, r3
   f96b6:	4649      	mov	r1, r9
   f96b8:	3230      	adds	r2, #48	; 0x30
   f96ba:	930d      	str	r3, [sp, #52]	; 0x34
   f96bc:	469a      	mov	sl, r3
   f96be:	f101 0320 	add.w	r3, r1, #32
   f96c2:	9302      	str	r3, [sp, #8]
   f96c4:	4616      	mov	r6, r2
   f96c6:	ab2a      	add	r3, sp, #168	; 0xa8
   f96c8:	f109 091f 	add.w	r9, r9, #31
   f96cc:	af28      	add	r7, sp, #160	; 0xa0
   f96ce:	2400      	movs	r4, #0
   f96d0:	f240 2b16 	movw	fp, #534	; 0x216
   f96d4:	f10d 08b0 	add.w	r8, sp, #176	; 0xb0
   f96d8:	9307      	str	r3, [sp, #28]
   f96da:	ab2b      	add	r3, sp, #172	; 0xac
   f96dc:	920e      	str	r2, [sp, #56]	; 0x38
   f96de:	9308      	str	r3, [sp, #32]
   f96e0:	9b08      	ldr	r3, [sp, #32]
   f96e2:	462a      	mov	r2, r5
   f96e4:	ecba 7b02 	vldmia	sl!, {d7}
   f96e8:	4639      	mov	r1, r7
   f96ea:	9803      	ldr	r0, [sp, #12]
   f96ec:	601c      	str	r4, [r3, #0]
   f96ee:	9b07      	ldr	r3, [sp, #28]
   f96f0:	f8a7 b00e 	strh.w	fp, [r7, #14]
   f96f4:	ed87 7b00 	vstr	d7, [r7]
   f96f8:	601c      	str	r4, [r3, #0]
   f96fa:	f7c1 ed04 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f96fe:	ecb6 7b02 	vldmia	r6!, {d7}
   f9702:	ab2f      	add	r3, sp, #188	; 0xbc
   f9704:	462a      	mov	r2, r5
   f9706:	4641      	mov	r1, r8
   f9708:	9804      	ldr	r0, [sp, #16]
   f970a:	601c      	str	r4, [r3, #0]
   f970c:	942e      	str	r4, [sp, #184]	; 0xb8
   f970e:	f8a8 b00e 	strh.w	fp, [r8, #14]
   f9712:	ed88 7b00 	vstr	d7, [r8]
   f9716:	f7c1 ecf6 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f971a:	f819 1f01 	ldrb.w	r1, [r9, #1]!
   f971e:	ab30      	add	r3, sp, #192	; 0xc0
   f9720:	9433      	str	r4, [sp, #204]	; 0xcc
   f9722:	462a      	mov	r2, r5
   f9724:	9431      	str	r4, [sp, #196]	; 0xc4
   f9726:	2900      	cmp	r1, #0
   f9728:	4619      	mov	r1, r3
   f972a:	bf14      	ite	ne
   f972c:	200a      	movne	r0, #10
   f972e:	2009      	moveq	r0, #9
   f9730:	81d8      	strh	r0, [r3, #14]
   f9732:	9805      	ldr	r0, [sp, #20]
   f9734:	601c      	str	r4, [r3, #0]
   f9736:	9432      	str	r4, [sp, #200]	; 0xc8
   f9738:	f7c1 ece4 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f973c:	9b02      	ldr	r3, [sp, #8]
   f973e:	429e      	cmp	r6, r3
   f9740:	d1ce      	bne.n	f96e0 <DataSubProcess::updateEncoderData()+0x1c0>
   f9742:	f8df 0488 	ldr.w	r0, [pc, #1160]	; f9bcc <DataSubProcess::updateEncoderData()+0x6ac>
   f9746:	ac40      	add	r4, sp, #256	; 0x100
   f9748:	9f0a      	ldr	r7, [sp, #40]	; 0x28
   f974a:	260c      	movs	r6, #12
   f974c:	9a03      	ldr	r2, [sp, #12]
   f974e:	4621      	mov	r1, r4
   f9750:	4478      	add	r0, pc
   f9752:	462b      	mov	r3, r5
   f9754:	6020      	str	r0, [r4, #0]
   f9756:	4638      	mov	r0, r7
   f9758:	6066      	str	r6, [r4, #4]
   f975a:	f7be ebc4 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f975e:	f8df 6470 	ldr.w	r6, [pc, #1136]	; f9bd0 <DataSubProcess::updateEncoderData()+0x6b0>
   f9762:	200a      	movs	r0, #10
   f9764:	6060      	str	r0, [r4, #4]
   f9766:	462b      	mov	r3, r5
   f9768:	9a04      	ldr	r2, [sp, #16]
   f976a:	4621      	mov	r1, r4
   f976c:	447e      	add	r6, pc
   f976e:	4638      	mov	r0, r7
   f9770:	6026      	str	r6, [r4, #0]
   f9772:	f7be ebb8 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9776:	f8df 645c 	ldr.w	r6, [pc, #1116]	; f9bd4 <DataSubProcess::updateEncoderData()+0x6b4>
   f977a:	200e      	movs	r0, #14
   f977c:	6060      	str	r0, [r4, #4]
   f977e:	462b      	mov	r3, r5
   f9780:	9a05      	ldr	r2, [sp, #20]
   f9782:	4621      	mov	r1, r4
   f9784:	447e      	add	r6, pc
   f9786:	4638      	mov	r0, r7
   f9788:	6026      	str	r6, [r4, #0]
   f978a:	f7be ebac 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f978e:	980c      	ldr	r0, [sp, #48]	; 0x30
   f9790:	2104      	movs	r1, #4
   f9792:	f8df 2444 	ldr.w	r2, [pc, #1092]	; f9bd8 <DataSubProcess::updateEncoderData()+0x6b8>
   f9796:	6061      	str	r1, [r4, #4]
   f9798:	7803      	ldrb	r3, [r0, #0]
   f979a:	447a      	add	r2, pc
   f979c:	6022      	str	r2, [r4, #0]
   f979e:	2b00      	cmp	r3, #0
   f97a0:	f000 81ef 	beq.w	f9b82 <DataSubProcess::updateEncoderData()+0x662>
   f97a4:	4603      	mov	r3, r0
   f97a6:	f813 2f01 	ldrb.w	r2, [r3, #1]!
   f97aa:	2a00      	cmp	r2, #0
   f97ac:	d1fb      	bne.n	f97a6 <DataSubProcess::updateEncoderData()+0x286>
   f97ae:	9a0c      	ldr	r2, [sp, #48]	; 0x30
   f97b0:	1a9f      	subs	r7, r3, r2
   f97b2:	980c      	ldr	r0, [sp, #48]	; 0x30
   f97b4:	ae3c      	add	r6, sp, #240	; 0xf0
   f97b6:	462b      	mov	r3, r5
   f97b8:	4632      	mov	r2, r6
   f97ba:	4621      	mov	r1, r4
   f97bc:	6077      	str	r7, [r6, #4]
   f97be:	6030      	str	r0, [r6, #0]
   f97c0:	980a      	ldr	r0, [sp, #40]	; 0x28
   f97c2:	f7c1 eaa0 	blx	bad04 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericStringRef<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f97c6:	980b      	ldr	r0, [sp, #44]	; 0x2c
   f97c8:	2104      	movs	r1, #4
   f97ca:	f8df 2410 	ldr.w	r2, [pc, #1040]	; f9bdc <DataSubProcess::updateEncoderData()+0x6bc>
   f97ce:	6061      	str	r1, [r4, #4]
   f97d0:	7803      	ldrb	r3, [r0, #0]
   f97d2:	447a      	add	r2, pc
   f97d4:	6022      	str	r2, [r4, #0]
   f97d6:	2b00      	cmp	r3, #0
   f97d8:	f000 81d1 	beq.w	f9b7e <DataSubProcess::updateEncoderData()+0x65e>
   f97dc:	4603      	mov	r3, r0
   f97de:	f813 2f01 	ldrb.w	r2, [r3, #1]!
   f97e2:	2a00      	cmp	r2, #0
   f97e4:	d1fb      	bne.n	f97de <DataSubProcess::updateEncoderData()+0x2be>
   f97e6:	9a0b      	ldr	r2, [sp, #44]	; 0x2c
   f97e8:	1a98      	subs	r0, r3, r2
   f97ea:	9b0b      	ldr	r3, [sp, #44]	; 0x2c
   f97ec:	4632      	mov	r2, r6
   f97ee:	6070      	str	r0, [r6, #4]
   f97f0:	4621      	mov	r1, r4
   f97f2:	6033      	str	r3, [r6, #0]
   f97f4:	462b      	mov	r3, r5
   f97f6:	9e0a      	ldr	r6, [sp, #40]	; 0x28
   f97f8:	4630      	mov	r0, r6
   f97fa:	f7c1 ea84 	blx	bad04 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericStringRef<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f97fe:	49f8      	ldr	r1, [pc, #992]	; (f9be0 <DataSubProcess::updateEncoderData()+0x6c0>)
   f9800:	9c06      	ldr	r4, [sp, #24]
   f9802:	4479      	add	r1, pc
   f9804:	4620      	mov	r0, r4
   f9806:	f7ba eeac 	blx	b4560 <rapidjson::internal::DisableIf<rapidjson::internal::RemoveSfinaeTag<rapidjson::internal::SfinaeTag& (*)(rapidjson::internal::NotExpr<rapidjson::internal::IsSame<rapidjson::internal::RemoveConst<char const>::Type, char> >)>::Type, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&>::Type rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::operator[]<char const>(char const*)@plt>
   f980a:	462a      	mov	r2, r5
   f980c:	4631      	mov	r1, r6
   f980e:	f7c1 ec7a 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9812:	48f4      	ldr	r0, [pc, #976]	; (f9be4 <DataSubProcess::updateEncoderData()+0x6c4>)
   f9814:	2201      	movs	r2, #1
   f9816:	4621      	mov	r1, r4
   f9818:	4478      	add	r0, pc
   f981a:	f7be e820 	blx	b785c <dobot::common::util::JsonUtil::writeJsonFile(char const*, rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>*, bool)@plt+0x4>
   f981e:	e0db      	b.n	f99d8 <DataSubProcess::updateEncoderData()+0x4b8>
   f9820:	f7bb e918 	blx	b4a54 <spdlog::logTerminal::Instance()@plt>
   f9824:	4af0      	ldr	r2, [pc, #960]	; (f9be8 <DataSubProcess::updateEncoderData()+0x6c8>)
   f9826:	2302      	movs	r3, #2
   f9828:	4cf0      	ldr	r4, [pc, #960]	; (f9bec <DataSubProcess::updateEncoderData()+0x6cc>)
   f982a:	f643 51ae 	movw	r1, #15790	; 0x3dae
   f982e:	f06f 000f 	mvn.w	r0, #15
   f9832:	447a      	add	r2, pc
   f9834:	447c      	add	r4, pc
   f9836:	3a44      	subs	r2, #68	; 0x44
   f9838:	9400      	str	r4, [sp, #0]
   f983a:	f7c1 e860 	blx	ba8fc <void spdlog::logTerminal::basicLog<>(int, int, char const*, spdlog::level::level_enum, char const*)@plt>
   f983e:	4bec      	ldr	r3, [pc, #944]	; (f9bf0 <DataSubProcess::updateEncoderData()+0x6d0>)
   f9840:	aa12      	add	r2, sp, #72	; 0x48
   f9842:	9c06      	ldr	r4, [sp, #24]
   f9844:	4611      	mov	r1, r2
   f9846:	447b      	add	r3, pc
   f9848:	4620      	mov	r0, r4
   f984a:	9312      	str	r3, [sp, #72]	; 0x48
   f984c:	9313      	str	r3, [sp, #76]	; 0x4c
   f984e:	f7be ea36 	blx	b7cbc <rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>& rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>::ParseStream<0u, rapidjson::UTF8<char>, rapidjson::GenericStringStream<rapidjson::UTF8<char> > >(rapidjson::GenericStringStream<rapidjson::UTF8<char> >&)@plt>
   f9852:	6926      	ldr	r6, [r4, #16]
   f9854:	2e00      	cmp	r6, #0
   f9856:	f000 819f 	beq.w	f9b98 <DataSubProcess::updateEncoderData()+0x678>
   f985a:	f507 5303 	add.w	r3, r7, #8384	; 0x20c0
   f985e:	f507 5a04 	add.w	sl, r7, #8448	; 0x2100
   f9862:	461a      	mov	r2, r3
   f9864:	4651      	mov	r1, sl
   f9866:	3230      	adds	r2, #48	; 0x30
   f9868:	930d      	str	r3, [sp, #52]	; 0x34
   f986a:	9302      	str	r3, [sp, #8]
   f986c:	f101 0320 	add.w	r3, r1, #32
   f9870:	9307      	str	r3, [sp, #28]
   f9872:	4690      	mov	r8, r2
   f9874:	ab3a      	add	r3, sp, #232	; 0xe8
   f9876:	f10a 0a1f 	add.w	sl, sl, #31
   f987a:	f10d 09e0 	add.w	r9, sp, #224	; 0xe0
   f987e:	2500      	movs	r5, #0
   f9880:	f240 2b16 	movw	fp, #534	; 0x216
   f9884:	af3c      	add	r7, sp, #240	; 0xf0
   f9886:	9308      	str	r3, [sp, #32]
   f9888:	ab3b      	add	r3, sp, #236	; 0xec
   f988a:	920e      	str	r2, [sp, #56]	; 0x38
   f988c:	9309      	str	r3, [sp, #36]	; 0x24
   f988e:	9b02      	ldr	r3, [sp, #8]
   f9890:	4632      	mov	r2, r6
   f9892:	4649      	mov	r1, r9
   f9894:	9803      	ldr	r0, [sp, #12]
   f9896:	ecb3 7b02 	vldmia	r3!, {d7}
   f989a:	9302      	str	r3, [sp, #8]
   f989c:	9b09      	ldr	r3, [sp, #36]	; 0x24
   f989e:	ed89 7b00 	vstr	d7, [r9]
   f98a2:	601d      	str	r5, [r3, #0]
   f98a4:	9b08      	ldr	r3, [sp, #32]
   f98a6:	f8a9 b00e 	strh.w	fp, [r9, #14]
   f98aa:	601d      	str	r5, [r3, #0]
   f98ac:	f7c1 ec2a 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f98b0:	ecb8 7b02 	vldmia	r8!, {d7}
   f98b4:	ab3f      	add	r3, sp, #252	; 0xfc
   f98b6:	4632      	mov	r2, r6
   f98b8:	4639      	mov	r1, r7
   f98ba:	9804      	ldr	r0, [sp, #16]
   f98bc:	601d      	str	r5, [r3, #0]
   f98be:	953e      	str	r5, [sp, #248]	; 0xf8
   f98c0:	f8a7 b00e 	strh.w	fp, [r7, #14]
   f98c4:	ed87 7b00 	vstr	d7, [r7]
   f98c8:	f7c1 ec1c 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f98cc:	f81a 2f01 	ldrb.w	r2, [sl, #1]!
   f98d0:	ac40      	add	r4, sp, #256	; 0x100
   f98d2:	ab43      	add	r3, sp, #268	; 0x10c
   f98d4:	4621      	mov	r1, r4
   f98d6:	9805      	ldr	r0, [sp, #20]
   f98d8:	2a00      	cmp	r2, #0
   f98da:	4632      	mov	r2, r6
   f98dc:	bf14      	ite	ne
   f98de:	f04f 0e0a 	movne.w	lr, #10
   f98e2:	f04f 0e09 	moveq.w	lr, #9
   f98e6:	601d      	str	r5, [r3, #0]
   f98e8:	9541      	str	r5, [sp, #260]	; 0x104
   f98ea:	9542      	str	r5, [sp, #264]	; 0x108
   f98ec:	f8a4 e00e 	strh.w	lr, [r4, #14]
   f98f0:	6025      	str	r5, [r4, #0]
   f98f2:	f7c1 ec08 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f98f6:	9b07      	ldr	r3, [sp, #28]
   f98f8:	4598      	cmp	r8, r3
   f98fa:	d1c8      	bne.n	f988e <DataSubProcess::updateEncoderData()+0x36e>
   f98fc:	4dbd      	ldr	r5, [pc, #756]	; (f9bf4 <DataSubProcess::updateEncoderData()+0x6d4>)
   f98fe:	200c      	movs	r0, #12
   f9900:	f8dd 8028 	ldr.w	r8, [sp, #40]	; 0x28
   f9904:	4633      	mov	r3, r6
   f9906:	6060      	str	r0, [r4, #4]
   f9908:	4621      	mov	r1, r4
   f990a:	447d      	add	r5, pc
   f990c:	9a03      	ldr	r2, [sp, #12]
   f990e:	4640      	mov	r0, r8
   f9910:	6025      	str	r5, [r4, #0]
   f9912:	f7be eae8 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9916:	4db8      	ldr	r5, [pc, #736]	; (f9bf8 <DataSubProcess::updateEncoderData()+0x6d8>)
   f9918:	200a      	movs	r0, #10
   f991a:	6060      	str	r0, [r4, #4]
   f991c:	4633      	mov	r3, r6
   f991e:	9a04      	ldr	r2, [sp, #16]
   f9920:	4621      	mov	r1, r4
   f9922:	447d      	add	r5, pc
   f9924:	4640      	mov	r0, r8
   f9926:	6025      	str	r5, [r4, #0]
   f9928:	f7be eadc 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f992c:	4db3      	ldr	r5, [pc, #716]	; (f9bfc <DataSubProcess::updateEncoderData()+0x6dc>)
   f992e:	200e      	movs	r0, #14
   f9930:	6060      	str	r0, [r4, #4]
   f9932:	4633      	mov	r3, r6
   f9934:	9a05      	ldr	r2, [sp, #20]
   f9936:	4621      	mov	r1, r4
   f9938:	447d      	add	r5, pc
   f993a:	4640      	mov	r0, r8
   f993c:	6025      	str	r5, [r4, #0]
   f993e:	f7be ead2 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9942:	980c      	ldr	r0, [sp, #48]	; 0x30
   f9944:	2104      	movs	r1, #4
   f9946:	4aae      	ldr	r2, [pc, #696]	; (f9c00 <DataSubProcess::updateEncoderData()+0x6e0>)
   f9948:	6061      	str	r1, [r4, #4]
   f994a:	7803      	ldrb	r3, [r0, #0]
   f994c:	447a      	add	r2, pc
   f994e:	6022      	str	r2, [r4, #0]
   f9950:	2b00      	cmp	r3, #0
   f9952:	d05d      	beq.n	f9a10 <DataSubProcess::updateEncoderData()+0x4f0>
   f9954:	4603      	mov	r3, r0
   f9956:	f813 2f01 	ldrb.w	r2, [r3, #1]!
   f995a:	2a00      	cmp	r2, #0
   f995c:	d1fb      	bne.n	f9956 <DataSubProcess::updateEncoderData()+0x436>
   f995e:	9a0c      	ldr	r2, [sp, #48]	; 0x30
   f9960:	1a9d      	subs	r5, r3, r2
   f9962:	980c      	ldr	r0, [sp, #48]	; 0x30
   f9964:	4633      	mov	r3, r6
   f9966:	463a      	mov	r2, r7
   f9968:	4621      	mov	r1, r4
   f996a:	607d      	str	r5, [r7, #4]
   f996c:	6038      	str	r0, [r7, #0]
   f996e:	980a      	ldr	r0, [sp, #40]	; 0x28
   f9970:	f7c1 e9c8 	blx	bad04 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericStringRef<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9974:	980b      	ldr	r0, [sp, #44]	; 0x2c
   f9976:	2104      	movs	r1, #4
   f9978:	4aa2      	ldr	r2, [pc, #648]	; (f9c04 <DataSubProcess::updateEncoderData()+0x6e4>)
   f997a:	6061      	str	r1, [r4, #4]
   f997c:	7803      	ldrb	r3, [r0, #0]
   f997e:	447a      	add	r2, pc
   f9980:	6022      	str	r2, [r4, #0]
   f9982:	2b00      	cmp	r3, #0
   f9984:	d046      	beq.n	f9a14 <DataSubProcess::updateEncoderData()+0x4f4>
   f9986:	4603      	mov	r3, r0
   f9988:	f813 2f01 	ldrb.w	r2, [r3, #1]!
   f998c:	2a00      	cmp	r2, #0
   f998e:	d1fb      	bne.n	f9988 <DataSubProcess::updateEncoderData()+0x468>
   f9990:	9a0b      	ldr	r2, [sp, #44]	; 0x2c
   f9992:	1a98      	subs	r0, r3, r2
   f9994:	990b      	ldr	r1, [sp, #44]	; 0x2c
   f9996:	463a      	mov	r2, r7
   f9998:	9d0a      	ldr	r5, [sp, #40]	; 0x28
   f999a:	4633      	mov	r3, r6
   f999c:	6078      	str	r0, [r7, #4]
   f999e:	6039      	str	r1, [r7, #0]
   f99a0:	4621      	mov	r1, r4
   f99a2:	4628      	mov	r0, r5
   f99a4:	f7c1 e9ae 	blx	bad04 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericStringRef<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f99a8:	4629      	mov	r1, r5
   f99aa:	9d0f      	ldr	r5, [sp, #60]	; 0x3c
   f99ac:	4632      	mov	r2, r6
   f99ae:	4628      	mov	r0, r5
   f99b0:	f7c1 eba8 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f99b4:	4894      	ldr	r0, [pc, #592]	; (f9c08 <DataSubProcess::updateEncoderData()+0x6e8>)
   f99b6:	2107      	movs	r1, #7
   f99b8:	6061      	str	r1, [r4, #4]
   f99ba:	4621      	mov	r1, r4
   f99bc:	4633      	mov	r3, r6
   f99be:	462a      	mov	r2, r5
   f99c0:	4478      	add	r0, pc
   f99c2:	6020      	str	r0, [r4, #0]
   f99c4:	9c06      	ldr	r4, [sp, #24]
   f99c6:	4620      	mov	r0, r4
   f99c8:	f7be ea8c 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f99cc:	488f      	ldr	r0, [pc, #572]	; (f9c0c <DataSubProcess::updateEncoderData()+0x6ec>)
   f99ce:	2201      	movs	r2, #1
   f99d0:	4621      	mov	r1, r4
   f99d2:	4478      	add	r0, pc
   f99d4:	f7bd ef42 	blx	b785c <dobot::common::util::JsonUtil::writeJsonFile(char const*, rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>*, bool)@plt+0x4>
   f99d8:	980d      	ldr	r0, [sp, #52]	; 0x34
   f99da:	2230      	movs	r2, #48	; 0x30
   f99dc:	2100      	movs	r1, #0
   f99de:	f7bc efb4 	blx	b6948 <memset@plt+0x4>
   f99e2:	2230      	movs	r2, #48	; 0x30
   f99e4:	2100      	movs	r1, #0
   f99e6:	980e      	ldr	r0, [sp, #56]	; 0x38
   f99e8:	f7bc efae 	blx	b6948 <memset@plt+0x4>
   f99ec:	9806      	ldr	r0, [sp, #24]
   f99ee:	f7bf ee12 	blx	b9614 <rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>::~GenericDocument()@plt>
   f99f2:	2000      	movs	r0, #0
   f99f4:	f20d 5d4c 	addw	sp, sp, #1356	; 0x54c
   f99f8:	e8bd 8ff0 	ldmia.w	sp!, {r4, r5, r6, r7, r8, r9, sl, fp, pc}
   f99fc:	9b06      	ldr	r3, [sp, #24]
   f99fe:	89db      	ldrh	r3, [r3, #14]
   f9a00:	2b03      	cmp	r3, #3
   f9a02:	d009      	beq.n	f9a18 <DataSubProcess::updateEncoderData()+0x4f8>
   f9a04:	f507 5303 	add.w	r3, r7, #8384	; 0x20c0
   f9a08:	930d      	str	r3, [sp, #52]	; 0x34
   f9a0a:	3330      	adds	r3, #48	; 0x30
   f9a0c:	930e      	str	r3, [sp, #56]	; 0x38
   f9a0e:	e7e3      	b.n	f99d8 <DataSubProcess::updateEncoderData()+0x4b8>
   f9a10:	461d      	mov	r5, r3
   f9a12:	e7a6      	b.n	f9962 <DataSubProcess::updateEncoderData()+0x442>
   f9a14:	4618      	mov	r0, r3
   f9a16:	e7bd      	b.n	f9994 <DataSubProcess::updateEncoderData()+0x474>
   f9a18:	4a7d      	ldr	r2, [pc, #500]	; (f9c10 <DataSubProcess::updateEncoderData()+0x6f0>)
   f9a1a:	ac40      	add	r4, sp, #256	; 0x100
   f9a1c:	4620      	mov	r0, r4
   f9a1e:	9906      	ldr	r1, [sp, #24]
   f9a20:	447a      	add	r2, pc
   f9a22:	f7c0 eb2a 	blx	ba078 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::FindMember(char const*)@plt>
   f9a26:	6823      	ldr	r3, [r4, #0]
   f9a28:	8bda      	ldrh	r2, [r3, #30]
   f9a2a:	2a04      	cmp	r2, #4
   f9a2c:	f040 80b6 	bne.w	f9b9c <DataSubProcess::updateEncoderData()+0x67c>
   f9a30:	691a      	ldr	r2, [r3, #16]
   f9a32:	2a00      	cmp	r2, #0
   f9a34:	f000 809c 	beq.w	f9b70 <DataSubProcess::updateEncoderData()+0x650>
   f9a38:	6999      	ldr	r1, [r3, #24]
   f9a3a:	f507 5b04 	add.w	fp, r7, #8448	; 0x2100
   f9a3e:	465a      	mov	r2, fp
   f9a40:	3310      	adds	r3, #16
   f9a42:	3220      	adds	r2, #32
   f9a44:	f507 5903 	add.w	r9, r7, #8384	; 0x20c0
   f9a48:	9202      	str	r2, [sp, #8]
   f9a4a:	4618      	mov	r0, r3
   f9a4c:	f101 0210 	add.w	r2, r1, #16
   f9a50:	f10b 0b1f 	add.w	fp, fp, #31
   f9a54:	f109 0930 	add.w	r9, r9, #48	; 0x30
   f9a58:	f507 5a03 	add.w	sl, r7, #8384	; 0x20c0
   f9a5c:	f10d 08d0 	add.w	r8, sp, #208	; 0xd0
   f9a60:	2600      	movs	r6, #0
   f9a62:	9308      	str	r3, [sp, #32]
   f9a64:	f7c0 ed38 	blx	ba4d8 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::Erase(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> > const*, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> > const*)@plt>
   f9a68:	ab35      	add	r3, sp, #212	; 0xd4
   f9a6a:	9307      	str	r3, [sp, #28]
   f9a6c:	4629      	mov	r1, r5
   f9a6e:	ecba 0b02 	vldmia	sl!, {d0}
   f9a72:	9803      	ldr	r0, [sp, #12]
   f9a74:	f7bc ea40 	blx	b5ef8 <rapidjson::internal::DisableIf<rapidjson::internal::RemoveSfinaeTag<rapidjson::internal::SfinaeTag& (*)(rapidjson::internal::OrExpr<rapidjson::internal::IsPointer<double>, rapidjson::internal::IsGenericValue<double> >)>::Type, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&>::Type rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack<double>(double, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9a78:	4629      	mov	r1, r5
   f9a7a:	ecb9 0b02 	vldmia	r9!, {d0}
   f9a7e:	9804      	ldr	r0, [sp, #16]
   f9a80:	f7bc ea3a 	blx	b5ef8 <rapidjson::internal::DisableIf<rapidjson::internal::RemoveSfinaeTag<rapidjson::internal::SfinaeTag& (*)(rapidjson::internal::OrExpr<rapidjson::internal::IsPointer<double>, rapidjson::internal::IsGenericValue<double> >)>::Type, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&>::Type rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack<double>(double, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9a84:	f81b 1f01 	ldrb.w	r1, [fp, #1]!
   f9a88:	ab37      	add	r3, sp, #220	; 0xdc
   f9a8a:	9807      	ldr	r0, [sp, #28]
   f9a8c:	462a      	mov	r2, r5
   f9a8e:	601e      	str	r6, [r3, #0]
   f9a90:	2900      	cmp	r1, #0
   f9a92:	4641      	mov	r1, r8
   f9a94:	bf14      	ite	ne
   f9a96:	f04f 0e0a 	movne.w	lr, #10
   f9a9a:	f04f 0e09 	moveq.w	lr, #9
   f9a9e:	6006      	str	r6, [r0, #0]
   f9aa0:	9805      	ldr	r0, [sp, #20]
   f9aa2:	9636      	str	r6, [sp, #216]	; 0xd8
   f9aa4:	f8c8 6000 	str.w	r6, [r8]
   f9aa8:	f8a8 e00e 	strh.w	lr, [r8, #14]
   f9aac:	f7c1 eb2a 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9ab0:	9b02      	ldr	r3, [sp, #8]
   f9ab2:	4599      	cmp	r9, r3
   f9ab4:	d1da      	bne.n	f9a6c <DataSubProcess::updateEncoderData()+0x54c>
   f9ab6:	4e57      	ldr	r6, [pc, #348]	; (f9c14 <DataSubProcess::updateEncoderData()+0x6f4>)
   f9ab8:	200c      	movs	r0, #12
   f9aba:	f8dd 8028 	ldr.w	r8, [sp, #40]	; 0x28
   f9abe:	462b      	mov	r3, r5
   f9ac0:	6060      	str	r0, [r4, #4]
   f9ac2:	4621      	mov	r1, r4
   f9ac4:	447e      	add	r6, pc
   f9ac6:	9a03      	ldr	r2, [sp, #12]
   f9ac8:	4640      	mov	r0, r8
   f9aca:	6026      	str	r6, [r4, #0]
   f9acc:	f7be ea0a 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9ad0:	4e51      	ldr	r6, [pc, #324]	; (f9c18 <DataSubProcess::updateEncoderData()+0x6f8>)
   f9ad2:	200a      	movs	r0, #10
   f9ad4:	6060      	str	r0, [r4, #4]
   f9ad6:	462b      	mov	r3, r5
   f9ad8:	9a04      	ldr	r2, [sp, #16]
   f9ada:	4621      	mov	r1, r4
   f9adc:	447e      	add	r6, pc
   f9ade:	4640      	mov	r0, r8
   f9ae0:	6026      	str	r6, [r4, #0]
   f9ae2:	f7be ea00 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9ae6:	4e4d      	ldr	r6, [pc, #308]	; (f9c1c <DataSubProcess::updateEncoderData()+0x6fc>)
   f9ae8:	200e      	movs	r0, #14
   f9aea:	6060      	str	r0, [r4, #4]
   f9aec:	462b      	mov	r3, r5
   f9aee:	9a05      	ldr	r2, [sp, #20]
   f9af0:	4621      	mov	r1, r4
   f9af2:	447e      	add	r6, pc
   f9af4:	4640      	mov	r0, r8
   f9af6:	6026      	str	r6, [r4, #0]
   f9af8:	f7be e9f4 	blx	b7ee4 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9afc:	980c      	ldr	r0, [sp, #48]	; 0x30
   f9afe:	2104      	movs	r1, #4
   f9b00:	4a47      	ldr	r2, [pc, #284]	; (f9c20 <DataSubProcess::updateEncoderData()+0x700>)
   f9b02:	6061      	str	r1, [r4, #4]
   f9b04:	7803      	ldrb	r3, [r0, #0]
   f9b06:	447a      	add	r2, pc
   f9b08:	6022      	str	r2, [r4, #0]
   f9b0a:	2b00      	cmp	r3, #0
   f9b0c:	d03d      	beq.n	f9b8a <DataSubProcess::updateEncoderData()+0x66a>
   f9b0e:	4603      	mov	r3, r0
   f9b10:	f813 2f01 	ldrb.w	r2, [r3, #1]!
   f9b14:	2a00      	cmp	r2, #0
   f9b16:	d1fb      	bne.n	f9b10 <DataSubProcess::updateEncoderData()+0x5f0>
   f9b18:	9a0c      	ldr	r2, [sp, #48]	; 0x30
   f9b1a:	ebc2 0e03 	rsb	lr, r2, r3
   f9b1e:	980c      	ldr	r0, [sp, #48]	; 0x30
   f9b20:	ae3c      	add	r6, sp, #240	; 0xf0
   f9b22:	462b      	mov	r3, r5
   f9b24:	4632      	mov	r2, r6
   f9b26:	4621      	mov	r1, r4
   f9b28:	f8c6 e004 	str.w	lr, [r6, #4]
   f9b2c:	6030      	str	r0, [r6, #0]
   f9b2e:	980a      	ldr	r0, [sp, #40]	; 0x28
   f9b30:	f7c1 e8e8 	blx	bad04 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericStringRef<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9b34:	980b      	ldr	r0, [sp, #44]	; 0x2c
   f9b36:	2104      	movs	r1, #4
   f9b38:	4a3a      	ldr	r2, [pc, #232]	; (f9c24 <DataSubProcess::updateEncoderData()+0x704>)
   f9b3a:	6061      	str	r1, [r4, #4]
   f9b3c:	7803      	ldrb	r3, [r0, #0]
   f9b3e:	447a      	add	r2, pc
   f9b40:	6022      	str	r2, [r4, #0]
   f9b42:	b303      	cbz	r3, f9b86 <DataSubProcess::updateEncoderData()+0x666>
   f9b44:	4603      	mov	r3, r0
   f9b46:	f813 2f01 	ldrb.w	r2, [r3, #1]!
   f9b4a:	2a00      	cmp	r2, #0
   f9b4c:	d1fb      	bne.n	f9b46 <DataSubProcess::updateEncoderData()+0x626>
   f9b4e:	9a0b      	ldr	r2, [sp, #44]	; 0x2c
   f9b50:	1a98      	subs	r0, r3, r2
   f9b52:	9b0b      	ldr	r3, [sp, #44]	; 0x2c
   f9b54:	4621      	mov	r1, r4
   f9b56:	9c0a      	ldr	r4, [sp, #40]	; 0x28
   f9b58:	4632      	mov	r2, r6
   f9b5a:	6070      	str	r0, [r6, #4]
   f9b5c:	6033      	str	r3, [r6, #0]
   f9b5e:	462b      	mov	r3, r5
   f9b60:	4620      	mov	r0, r4
   f9b62:	f7c1 e8d0 	blx	bad04 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::AddMember(rapidjson::GenericStringRef<char>, rapidjson::GenericStringRef<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9b66:	462a      	mov	r2, r5
   f9b68:	4621      	mov	r1, r4
   f9b6a:	9808      	ldr	r0, [sp, #32]
   f9b6c:	f7c1 eaca 	blx	bb104 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::PushBack(rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >&, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>&)@plt>
   f9b70:	482d      	ldr	r0, [pc, #180]	; (f9c28 <DataSubProcess::updateEncoderData()+0x708>)
   f9b72:	2201      	movs	r2, #1
   f9b74:	9906      	ldr	r1, [sp, #24]
   f9b76:	4478      	add	r0, pc
   f9b78:	f7bd ee70 	blx	b785c <dobot::common::util::JsonUtil::writeJsonFile(char const*, rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>*, bool)@plt+0x4>
   f9b7c:	e742      	b.n	f9a04 <DataSubProcess::updateEncoderData()+0x4e4>
   f9b7e:	4618      	mov	r0, r3
   f9b80:	e633      	b.n	f97ea <DataSubProcess::updateEncoderData()+0x2ca>
   f9b82:	461f      	mov	r7, r3
   f9b84:	e615      	b.n	f97b2 <DataSubProcess::updateEncoderData()+0x292>
   f9b86:	4618      	mov	r0, r3
   f9b88:	e7e3      	b.n	f9b52 <DataSubProcess::updateEncoderData()+0x632>
   f9b8a:	469e      	mov	lr, r3
   f9b8c:	e7c7      	b.n	f9b1e <DataSubProcess::updateEncoderData()+0x5fe>
   f9b8e:	9806      	ldr	r0, [sp, #24]
   f9b90:	f7bf ed40 	blx	b9614 <rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>::~GenericDocument()@plt>
   f9b94:	f7be ef66 	blx	b8a64 <__cxa_end_cleanup@plt>
   f9b98:	f7c2 ffc2 	bl	bcb20 <rapidjson::GenericDocument<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator>, rapidjson::CrtAllocator>::GetAllocator() [clone .isra.137] [clone .part.138]>
   f9b9c:	f7c3 f858 	bl	bcc50 <rapidjson::GenericValue<rapidjson::UTF8<char>, rapidjson::MemoryPoolAllocator<rapidjson::CrtAllocator> >::GetArray() [clone .part.201]>
   f9ba0:	0013b8e2 	.word	0x0013b8e2
   f9ba4:	0010ff9a 	.word	0x0010ff9a
   f9ba8:	00114d68 	.word	0x00114d68
   f9bac:	00114d5c 	.word	0x00114d5c
   f9bb0:	00114d5e 	.word	0x00114d5e
   f9bb4:	0010fea8 	.word	0x0010fea8
   f9bb8:	0013b7ea 	.word	0x0013b7ea
   f9bbc:	00114d28 	.word	0x00114d28
   f9bc0:	00114d58 	.word	0x00114d58
   f9bc4:	0010fe5e 	.word	0x0010fe5e
   f9bc8:	00114d34 	.word	0x00114d34
   f9bcc:	00114c84 	.word	0x00114c84
   f9bd0:	00114c78 	.word	0x00114c78
   f9bd4:	00114c6c 	.word	0x00114c6c
   f9bd8:	00114c66 	.word	0x00114c66
   f9bdc:	00114c36 	.word	0x00114c36
   f9be0:	00114bba 	.word	0x00114bba
   f9be4:	00114b68 	.word	0x00114b68
   f9be8:	0010fcba 	.word	0x0010fcba
   f9bec:	0013b5fc 	.word	0x0013b5fc
   f9bf0:	0012fa86 	.word	0x0012fa86
   f9bf4:	00114aca 	.word	0x00114aca
   f9bf8:	00114ac2 	.word	0x00114ac2
   f9bfc:	00114ab8 	.word	0x00114ab8
   f9c00:	00114ab4 	.word	0x00114ab4
   f9c04:	00114a8a 	.word	0x00114a8a
   f9c08:	001149fc 	.word	0x001149fc
   f9c0c:	001149ae 	.word	0x001149ae
   f9c10:	0011499c 	.word	0x0011499c
   f9c14:	00114910 	.word	0x00114910
   f9c18:	00114908 	.word	0x00114908
   f9c1c:	001148fe 	.word	0x001148fe
   f9c20:	001148fa 	.word	0x001148fa
   f9c24:	001148ca 	.word	0x001148ca
   f9c28:	0011480a 	.word	0x0011480a
