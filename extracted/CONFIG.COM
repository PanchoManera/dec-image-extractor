.;.MODULE CONFIG,20,<System configuration file>
.;
.;			  COPYRIGHT (c) 1986 BY
.;             DIGITAL EQUIPMENT CORPORATION, MAYNARD, MASS.
.;                         ALL RIGHTS RESERVED.
.;
.; THIS SOFTWARE IS FURNISHED UNDER A LICENSE AND MAY BE USED AND  COPIED
.; ONLY  IN  ACCORDANCE  WITH  THE  TERMS  OF  SUCH  LICENSE AND WITH THE
.; INCLUSION OF THE ABOVE COPYRIGHT NOTICE.  THIS SOFTWARE OR  ANY  OTHER
.; COPIES  THEREOF MAY NOT BE PROVIDED OR OTHERWISE MADE AVAILABLE TO ANY
.; OTHER PERSON.  NO TITLE TO AND OWNERSHIP OF  THE  SOFTWARE  IS  HEREBY
.; TRANSFERRED.
.;
.; THE INFORMATION IN THIS SOFTWARE IS SUBJECT TO CHANGE  WITHOUT  NOTICE
.; AND  SHOULD  NOT  BE  CONSTRUED  AS  A COMMITMENT BY DIGITAL EQUIPMENT
.; CORPORATION.
.;
.; DIGITAL ASSUMES NO RESPONSIBILITY FOR THE USE OR  RELIABILITY  OF  ITS
.; SOFTWARE ON EQUIPMENT WHICH IS NOT SUPPLIED BY DIGITAL.
.; File used to configure an RT-11 system disk.
.; James Williams 24-Jan-84, 30-Aug-84, 26-Jan-85, 21-Feb-85, 27-Mar-85
	.GoTo	Config

.Check:
	.TestFile SYS:'File'
	.If <FilErr> EQ 346 .Return
	.If <FilErr> NE <Succes> .GoTo 1$
	.SetT FilFnd
	.Return
.1$:
;?CONFIG-F-Unexpected file error value "'<FilErr>'" - SY:'File'
	.Stop

.CnfDev:
	.Parse ArgLst	"," P0 P1 P2 P3
	.SetF $DelXX
	.SetF $OkXX
	.SetF FilFnd
	.SetF Defalt
	.SetS File P0[1:2]+".SYS"
	.GoSub Check
	.IfT FilFnd .GoTo 2$
	.SetS File P0[1:2]+"X.SYS"
	.GoSub Check
	.IfF FilFnd .Return
.2$:
	.If P0 NE "VM" $Run	SY:Config	'P0':/P
	.If P0 EQ "VM" $Run	SY:Config	/A:177572
	.If <ExStat> EQ <Succes> .SetT Defalt
	.SetL $OkXX Defalt
	.If P1 NE "Ask" .GoTo 3$
	.SetT Defalt
	.SetT $OkXX
;
; The "'P0'" device may be valid for your system
	.IfF $NoQue .GoTo 4$
; It was not removed.
;
	.Return
.3$:
	.IfF $Query .GoTo 5$
;
.4$:
	.SetS YN "Y"
	.IfF Defalt .SetS YN "N"
	.Ask [Defalt] Defalt Do you want 'P0' ('P2' handler) ('YN')?
.5$:
	.SetL $OkXX Defalt
	.IfT Defalt .Return
	.SetT $DelXX
	.IfT $Delet		'PIP''P0'(,X).SYS,'P0'.MAC'S'
	.Return
.Config:.Disable Prefix,Suffix,LowerCase
.;DEBUG	comment out next line
	.Enable Quiet
	.SetT LP
	.SetT LS
	.SetT MM
	.SetT MS
	.SetT MT
	.SetT MU
	.SetT NC
	.SetT NQ
	.SetT NU
	.SetT SL
	.SetT XC
	.SetT XL
	.SetT Spool
	.SetT Queue
	.SetT Batch
	.SetF DelMM
	.SetF DelMS
	.SetF DelMT
	.SetF DelMU
	.SetF DelNC
	.SetF DelNQ
	.SetF DelNU
	.SetF DelSL
	.SetF DelXC
	.SetF DelXL
	.SetF $Query
	.SetF $SomeQ
	.SetF $NoQue
	.SetF $NoDCL
	.SetT $Delet
	.SetS S	"/D/X:-1"
	.SetS TempS P1[1:4]
	.If TempS EQ "/QUE" .SetT $Query
	.If TempS EQ "/SOM" .SetT $SomeQ
	.If TempS EQ "/NOQ" .SetT $NoQue
	.IfT $NoQue .GoTo 10$
	.SetS TempS P1[1:2]
	.If TempS EQ "/N" .SetT $NoDCL
.10$:	.If P1 EQ "" .GoTo 20$
	.SetL Option $Query!$SomeQ!$NoQue!$NoDCL
	.IfT Option .GoTo 20$
;?CONFIG-F-Unknown option, use /QUERY /SOMEQUERY or /NOQUERY, found "'P1'"
	.Exit
.20$:	.IfDisabled DCL .SetT $NoDCL
	.IfT $NoDCL	.Disable Quiet
	.IfT $NoDCL	.SetS PIP ";PIP	SYS:"
	.IfF $NoDCL	.SetS PIP "$PIP	SYS:"
.;
.; For the very trusting user, this command file may be invoked using:
.;
.; @CONFIG /NOQUERY
.;
.; which will perform most of the configuration WITHOUT asking questions.
.;
.; For the somewhat trusting user, this command file may be invoked using:
.;
.; @CONFIG /SOMEQUERY
.;
.; which will ask questions about configuration details not "forced" by
.; hardware.
.;
.; For the less trusting user, this command file may be invoked using:
.;
.; @CONFIG /QUERY
.;
.; which will asks questions about every group of deletions.
.;
.; To "practice" configuration the user/debugger can use:
.;
.; @CONFIG/N /{|SOME|NO}QUERY
.;
.; which will display the deletions it would have done, without doing them.
.;
.; This procedure configures the device with the logical name "SYS:".  If
.; SYS: is not defined prior to running CONFIG.COM, it will default it to "SY:".
.;
	.Enable DCL,LowerCase
$Run	SY:Config	SYS:
	.If <ExStat> NE <Succes> 		$Assign SY: SYS:
$Run	SY:Config	/R:370/M:020000/V:020000
	.SetF Pro3XX
	.If <ExStat> EQ <Succes> .SetT Pro3XX
	.SetL OkSJ ^Pro3XX
	.SetF OkXM
$Run	SY:Config	/A:177572
	.If <ExStat> EQ <Succes> .SetT OkXM
	.If P1 NE "" .GoTo 50$
; This command file can be run in 3 modes:
;
;	Query
;	SomeQuery (the default)
;	NoQuery
;
; In Query mode this command file asks a series of questions.  The default
; answers are determined from the currently booted system''s characteristics
; and represent a "reasonable" guess of a good configuration.
;
; In SomeQuery mode this command file asks questions only when it can not
; determine the answer from testing hardware configuration. (e.g. is the
; device connected to the serial port a printer, or do you want the files for
; automatic installation to be retained).
;
; In NoQuery mode this command file asks no questions, simply taking defaults
; for the questions it would ask in the other modes.
;
	.SetT $SomeQ
	.Ask [$SomeQ] $SomeQ Do you want "SomeQuery" mode (Y)?
	.IfT $SomeQ .GoTo 50$
;
	.SetF $NoQue
	.Ask [$NoQue] $NoQue Do you want "NoQuery" mode (N)?
	.IfT $NoQue .GoTo 50$
;
; Defaulting to "Query" mode
;
.50$:	.SetL $Query ^($SomeQ!$NoQue)
	.IfT $NoQue .GoTo 30$
;
; This command file is designed to remove system files that are not
; applicable to the currently booted system.  It should be applied
; to a copy of the distribution, NOT to the distribution media itself,
; since it deletes files.
;
; For best results the system on which @CONFIG is run should be the
; system the system disk is ultimately to be used with.  Also any
; devices that have non-standard CSRs should have the handler csr''s
; modified using the SET xx CSR=nnnnnn command before running @CONFIG.
;
; This command file may be stopped at any time by entering two "Ctrl/C"s.
;
	.SetT TF
	.Ask [TF] TF Do you want to configure your new system disk (Y)?
	.IfF TF .Exit
.30$:	.IfF $NoDCL 				$UnProtect SYS:*.*/SYS/NoLog
	.IfF $Query .GoTo 60$
;
	.SetT TF
	.Ask [TF] TF Do you want to remove unused device handlers (Y)?
	.IfF TF .GoTo SkipDv
.60$:
	.SetS	ArgLst	"DD,Ask,DECTape II"
	.GoSub	CnfDev
	.SetS	ArgLst	"LS,Ask,Serial line printer"
	.GoSub	CnfDev
	.SetL	LS	$OkXX
	.SetF	$Delet
	.SetS	ArgLst	"XL,Ask,Serial line communications"
	.GoSub	CnfDev
	.SetL	DelXL	$DelXX
	.SetL	XL	$OkXX
	.SetT	$Delet

	.SetS	ArgLst	"CR,   ,Card reader"
	.GoSub	CnfDev
	.SetS	ArgLst	"CT,   ,Cassette tape"
	.GoSub	CnfDev
	.SetS	ArgLst	"DL,   ,RL01/RL02"
	.GoSub	CnfDev
	.SetS	ArgLst	"DM,   ,RK06/RK07"
	.GoSub	CnfDev
	.SetS	ArgLst	"DP,   ,RP02/RP03"
	.GoSub	CnfDev
	.SetS	ArgLst	"DS,   ,RS03/4"
	.GoSub	CnfDev
	.SetS	ArgLst	"DT,   ,DECTape"
	.GoSub	CnfDev
	.SetS	ArgLst	"DU,   ,Generic disk"
	.GoSub	CnfDev
	.SetS	ArgLst	"DW,   ,PRO3__ winchester"
	.GoSub	CnfDev
	.SetS	ArgLst	"DX,   ,RX01 floppy"
	.GoSub	CnfDev
	.SetS	ArgLst	"DY,   ,RX02 floppy"
	.GoSub	CnfDev
	.SetS	ArgLst	"DZ,   ,PRO3__ RX50 floppy"
	.GoSub	CnfDev
	.SetS	ArgLst	"LD,   ,Logical disk subsetting"
	.GoSub	CnfDev
	.SetS	ArgLst	"LP,   ,Line printer"
	.GoSub	CnfDev
	.SetL	LP	$OkXX
	.SetS	ArgLst	"MM,   ,TJU16/TU45 magtape"
	.GoSub	CnfDev
	.SetL	DelMM	$DelXX
	.SetL	MM	$OkXX
	.SetS	ArgLst	"MS,   ,TK25/TS11/TS05/TU80 magtape""
	.GoSub	CnfDev
	.SetL	DelMS	$DelXX
	.SetL	MS	$OkXX
	.SetS	ArgLst	"MT,   ,TM11/TMA11/TS03/TE16 magtape"
	.GoSub	CnfDev
	.SetL	DelMT	$DelXX
	.SetL	MT	$OkXX
	.SetS	ArgLst	"MU,   ,TK50/TU81 magtape"
	.GoSub	CnfDev
	.SetL	DelMU	$DelXX
	.SetL	MU	$OkXX
	.SetS	ArgLst	"NC,   ,PRO3__ Ethernet"
	.GoSub	CnfDev
	.SetL	DelNC	$DelXX
	.SetL	NC	$OkXX
	.SetS	ArgLst	"NL,   ,Null"
	.GoSub	CnfDev
	.SetS	ArgLst	"NQ,   ,QBus Ethernet"
	.GoSub	CnfDev
	.SetL	DelNQ	$DelXX
	.SetL	NQ	$OkXX
	.SetS	ArgLst	"NU,   ,UniBus Ethernet"
	.GoSub	CnfDev
	.SetL	DelNU	$DelXX
	.SetL	NU	$OkXX
	.SetS	ArgLst	"PC,   ,Papertape"
	.GoSub	CnfDev
	.SetS	ArgLst	"PD,   ,PDT/150 floppy"
	.GoSub	CnfDev
	.SetS	ArgLst	"PI,   ,PRO3__ interface"
	.GoSub	CnfDev
	.SetS	ArgLst	"RF,   ,RF11/RS11"
	.GoSub	CnfDev
	.SetS	ArgLst	"RK,   ,RK05"
	.GoSub	CnfDev
	.SetS	ArgLst	"SL,   ,Single Line editor"
	.GoSub	CnfDev
	.SetL	DelSL	$DelXX
	.SetS	ArgLst	"VM,   ,Memory as disk"
	.GoSub	CnfDev
	.SetS	ArgLst	"XC,   ,PRO3__ Serial line communications"
	.GoSub	CnfDev
	.SetL	DelXC	$DelXX
	.SetL	XC	$OkXX

.SkipDv:
	.SetT DOMONS
	.IfF $Query .GoTo 110$
;
	.Ask [DOMONS] DOMONS Do you want to remove unused monitors (Y)?
	.IfF DOMONS .GoTo SkipSY
.110$:
	.IfT $NoQue .GoTo 140$
	.IfT $SomeQ .GoTo 140$
	.IfF Pro3XX .GoTo 130$
;
; RT11SJ/BL will not run on PRO3__ hardware
.130$:
;
	.SetS YN "Y"
	.IfF OkSJ .SetS YN "N"
	.Ask [OkSJ] OkSJ Do you want support for RT11SJ/BL ('YN')?
.140$:	.SetT OkFB
	.IfT $NoQue .GoTo 150$
;
	.Ask [OkFB] OkFB Do you want support for RT11FB (Y)?
.150$:	.IfF $Query .GoTo 170$
	.IfT OkXM .GoTo 160$
;
; RT11XM will not run on this machine since it lacks memory management
.160$:
;
	.SetS YN "Y"
	.IfF OkXM .SetS YN "N"
	.Ask [OkXM] OkXM Do you want support for RT11XM ('YN')?
.170$:
.SkipSY:
	.SetF AI
	.IfT $NoQue .GoTo 180$
;
	.Ask [AI] AI Do you want support for automatic installation (N)?
.180$:	.SetF ErrLog
	.IfT $NoQue .GoTo 190$
;
	.Ask [ErrLog] ErrLog Do you want support for device error logging (N)?
.190$:	.SetT Sysgen
	.IfT $NoQue .GoTo 200$
;
	.Ask [Sysgen] Sysgen Do you want support for sysgenning new monitors (Y)?
.200$:	.SetL Printr LP!LS
	.SetL Spool Printr
	.IfF $Query .GoTo 210$
	.SetS YN "Y"
	.IfF Spool .SetS YN "N"
;
	.Ask [Spool] Spool Do you want support for the transparent SPOOLer ('YN')?
.210$:
	.SetL Queue	^Spool&Printr
	.IfF $Query .GoTo 220$
;
	.Ask [Queue] Queue Do you want support for the QUEUE program (N)?
.220$:	.SetL MagTap	MM!MS!MT!MU
	.IfF $Query .GoTo 230$
;
	.SetS YN "Y"
	.IfF MagTap .SetS YN "N"
	.Ask [MagTap] MagTap Do you want support for 1/2" Magtapes ('YN')?
.230$:	.SetF Batch
	.IfT $NoQue .GoTo 240$
;
	.Ask [Batch] Batch Do you want support for BATCH (N)?
.240$:	.SetL OkPro PRO3XX
	.IfF PRO3XX .GoTo 120$
	.IfF $Query .GoTo 120$
;
; Certain utilities do not run on PRO3__ hardware
;
	.SetS YN "Y"
	.IfF OkPro .SetS YN "N"
	.Ask [OKPro] OkPro Do you want to save them anyway ('YN')?
.120$:
.;
.;ask about utility groups (PATCH, ...)
.;
;
; A more deletions (prompted by combinations of answers) may
; now be performed.  This will be followed by a Squeeze of the
; system disk.  Please be patient...
;
.IfF	AI	'PIP'(IVP,STARTA,VERIFY).COM'S'
.IfF	AI	'PIP'IVP.MAC'S'
.IfF	AI	'PIP'TERMID.SAV,MDUP.AI'S'
.IfF	AI	'PIP'RT11(A,P)I.SYS'S'

.IfF	ErrLog	'PIP'EL.SYS,EL(,COPY,INIT,TASK).MAC'S'
.IfF	ErrLog	'PIP'ERR(OUT.OBJ,TXT.MAC,LOG.REL),(ELINIT,ERROUT).SAV'S'

.IfF	Spool	'PIP'SPOOL.REL,SP(,X).SYS,SP.MAC'S'

.IfF	Queue	'PIP'QUE(UE.REL,MAN.SAV)'S'

.IfF	Batch	'PIP'BA(TCH.SAV,.SYS,X.SYS,.MAC)'S'

.IfF	Sysgen	'PIP'(BL,SJFB,XM).ANS'S'
.IfF	Sysgen	'PIP'SYSGEN.COM'S'
.IfF	Sysgen	'PIP'MTT(EM,IN)T.MAC'S'
.IfF	Sysgen	'PIP'(RMONFB,RMONSJ,TRMTBL).MAC'S'
.IfF	Sysgen	'PIP'(USR,XM,XMSUBS,FSM).MAC'S'
.IfF	Sysgen	'PIP'(BA,CR,CT,EL).MAC'S'
.IfF	Sysgen	'PIP'D(D,L,M,P,S,T).MAC'S'
.IfF	Sysgen	'PIP'D(U,W,X,Y,Z).MAC'S'
.IfF	Sysgen	'PIP'L(D,P,S).MAC'S'
.IfF	Sysgen	'PIP'N(C,I,L,Q,U).MAC'S'
.IfF	Sysgen	'PIP'(PC,PD,RF,RK,SP,VM).MAC'S'
.IfF	Sysgen	'PIP'T(J,M,S,T,U).MAC'S'
.IfF	Sysgen	'PIP'X(C,L).MAC'S'

.IfF	MagTap	'PIP'M(BOOT,BOT16,SBOOT,UBOOT).BOT'S'
.IfF	MagTap	'PIP'DISMT(1,2).COM,FSM.MAC'S'
.IfF	MagTap	'PIP'T(J,M,S,U).MAC'S'
.IfF	MagTap	'PIP'MDUP.(AI,MM,MS,MT,MU,SAV)'S'
.IfF	MagTap	'PIP'(MM,MS,MT,MU).SYS'S'
.IfF	MagTap	'PIP'(MM,MS,MT,MU)X.SYS'S'
.IfF	MagTap	'PIP'(MM,MS,MT,MU)HD.SYS'S'

.IfT	OkPro	'PIP'DATIME.(COM,MAC,SAV)'S'
.IfT	OkPro	'PIP'(CONSOL,VTMAC).MAC'S'
.IfT	OkPro	'PIP'(ODT,VTHDLR).OBJ'S'
.IfT	OkPro	'PIP'(FILEX,K52,SPEED).SAV'S'

.IfF	DOMONS	.GoTo SkipXX

.IfF	OkFB	'PIP'RT11(FB,PI).SYS,STARTF.COM,RTFB.MAP'S'

.IfF	OkSJ	'PIP'BL.ANS'S'
.IfF	OkSJ	'PIP'STARTS.COM'S'
.IfF	OkSJ	'PIP'(RMONSJ,SJ,TT,EL).MAC'S'
.IfF	OkSJ	'PIP'RT(SJ,BL).MAP'S'
.IfF	OkSJ	'PIP'RT11(AI,BL,SJ).SYS,TT.SYS'S'
.IfF	OkXM	'PIP'RT11XM.SYS,XMSUBS.MAC,RTXM.MAP,STARTX.COM'S'
.IfF	OkXM	'PIP'(CR,CT,DD,DL,DM,DP)X.SYS'S'
.IfF	OkXM	'PIP'D(S,T,U,W,X,Y)X.SYS'S'
.IfF	OkXM	'PIP'(DZ,LD,LP,LS,MM,MS)X.SYS'S'
.IfF	OkXM	'PIP'(MT,MU,NC,NL,NQ,NU)X.SYS'S'
.IfF	OkXM	'PIP'(PC,PI,RF,RK,SL,SP)X.SYS'S'
.IfF	OkXM	'PIP'(VM,XC,XL)X.SYS,XM.ANS,XM.MAC'S'
.IfF	OkXM	'PIP'DEMOX1.MAC,V.SAV,VBGEXE.SAV,VTCOM.SAV,KEX.SAV'S'
.IfF	OkXM	'PIP'GIDIS.SAV,ALPH00.FNT'S'

.SetL	SJFB	OkSJ!OkFB
.IfF	SJFB	'PIP'(CR,CT,DD,DL,DM,DP).SYS'S'
.IfF	SJFB	'PIP'D(S,T,U,W,X,Y).SYS'S'
.IfF	SJFB	'PIP'(DZ,LD,LP,LS,MM,MMHD).SYS'S'
.IfF	SJFB	'PIP'M(S,SHD,T,THD,U,UHD).SYS'S'
.IfF	SJFB	'PIP'(NL,PC,PD,PI,RF,RK).SYS'S'
.IfF	SJFB	'PIP'(SL,SP,VM,XC,XL,SLMIN).SYS'S'
.IfF	SJFB	'PIP'SJFB.ANS'S'

.SetL	FBXM	OkFB!OkXM
.IfF	FBXM	'PIP'(RTMON,QUEUE,SPOOL,VTCOM).REL'S'
.IfF	FBXM	'PIP'QUEMAN.SAV'S'
.IfF	FBXM	'PIP'(FB,RMONFB,DEMOBG,DEMOFG).MAC,DEMOF1.FOR'S'

.SkipXX:
.IfT 	DelMM	'PIP'TJ.MAC,MMHD.SYS,MDUP.MM'S'
.IfT 	DelMS	'PIP'TS.MAC,MSHD.SYS,MDUP.MS'S'
.IfT 	DelMT	'PIP'TM.MAC,MTHD.SYS,MDUP.MT'S'
.IfT	DelMU	'PIP'TU.MAC,MUHD.SYS,MDUP.MU,MDUP.AI,MUBOOT.BOT'S'
.IfT	DelSL	'PIP'SLMIN.SYS,LET.SAV'S'
.IfF	XL	'PIP'XL(,X).SYS'S'

.IfF	OkPro	'PIP'GIDIS.SAV,ALPH00.FNT'S'

.SetL	TempL	NC!NQ!NU
.IfF	TempL	'PIP'NI.MAC,NITEST.MAC'S'

.SetL	TempL	XC&XL
.IfF	TempL	'PIP'XL.MAC'S'

.;DEBUG comment out next line
.IfF	$NoDCL	$Squeeze SYS:/NoQuery
.;DEBUG uncomment out next line
.;.Dump
.Exit
                                                                                                                                          