.; .MODULE AI,VERSION=46,COMMENT=<Auto Installation Program>
.;
.;                        COPYRIGHT (c) 1986 BY
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
.;
.;***********************************************************************
.;			   STARTA.COM
.;	     RT-11 AUTOMATIC INSTALLATION PROGRAM
.;***********************************************************************
.;
.;***********************************************************************
.;	   INITIALIZATION CODE FOR ALL CONFIGURATIONS
.;***********************************************************************
.;
.SETS RTVERS "V5.3"	.;this sets the version in the text
.SETN MINSIZ 4800.	.;minimum blocks on single output for install
.SETS TAPE "MU0"	.;tape input unit (variable?)

.ENABLE QUIET,LOWERCASE
.DISABLE PREFIX,SUFFIX,TYPEAHEAD,ABORT
$SET TT QUIET
$SET EXIT NOSWAP
.IF <SYDISK> EQ "PD" .GOTO PDT
.SETF VT100		.; T=> VT100 class video, F=>hardcopy
.TESTFILE TERMID.SAV
.SETS ERRTYP " running TERMID.SAV"
.IF <FILERR> NE <SUCCES> .GOTO CRASH
$RUN TERMID
.IF <EXSTAT> EQ 1 .SETT VT100
.IFT VT100 ; <[?5h[?4l[H[2J[4;22r
.SETS	HEADER  "RT-11 Automatic Installation Process"
.GOSUB HEADER
.;Volume ID and owner name decoder:
.;	V + (I or O) + media + kit + volume number
.;	I or O above means ID or Owner
.;	media = Y -> RX02   L -> RL02   F -> RD/RX50 P -> PC325/50
.;	kit =   D -> Distribution (original and backup)
.;		W -> working system volume (and backup)
.;
.;
.;LABEL DECODER:
.;	LB + media + kit + volume number
.;	media = Y -> RX02   L -> RL02  F -> RD/RX50  P -> PC325/50
.;	kit =   D -> original distribution
.;		B -> backup of distribution
.;		W -> working system volume
.;		X -> backup of working system volume
.;
.SETN MAXVOL 7	.; Constant - number of floppies in RX50 and DZ kits
.SETF HELP	.; Variable - MNTBLK is/isn't to display help info
.SETS SYSTEM "'<SYDISK>''<SYUNIT>'"
.;Identify the configuration
.; IFT VM --> VM (dist. is on Magtape)
.; IFT DY --> Dual RX02s only
.; IFT DL --> Dual RL02s only
.; IFT RX --> Dual RX50 with RD5x(s)
.; IFT DW --> PC350/80
.; IFT DZ --> PC325
.; IFT PC --> PC350/80 OR PC325
.; IFT RD --> uPDP w/RD5x
.; IFT DU --> VM is sys, MU is src, DU is Dest
.SETF DL
.SETF DU
.SETF DY
.SETF DW
.SETF DZ
.SETF PC
.SETF RD
.SETF RX
.SETF VM
.IF <SYDISK>  EQ "DL" .SETT DL
.IF <SYDISK>  EQ "DU" .SETT RX
.IF <SYDISK>  EQ "DY" .SETT DY
.IF <SYDISK>  EQ "VM" .SETT VM
.IF <SYDISK>  NE "DZ" .GOTO PRE5
.SETT PC
.TESTDEVICE DW0:
.SETS TEMPS <EXSTRI>[1:3]
.IF TEMPS EQ "DW0" .SETT DW
.IF TEMPS NE "DW0" .SETT DZ
.PRE5:
.SETS DISK "disk"
.IFT DY .SETS DISK "diskette"
.SETS DDISK "D"+DISK[2:8.]
.IFT DL .GOTO PREDL
.IFT DY .GOTO PREDY
.IFT PC .GOTO PREPC
.IFT RX .GOTO PRERX
.IFT VM .GOTO PREVM
.GOTO FEXIT
.PREVM:
.;IDs and OWNERs for working system volume
.SETS WORKID "RTV5 WORK   "
.SETS WORKOW "MT  WORK"
.SETS LBLW1 "RT-11 'RTVERS' BIN WORKING"
.SETS SYSTMD TAPE+" (Drive "+TAPE[3:3]+")"
.SETF DUCHK
.SETF DLCHK
.TESTFILE CONFIG.SAV
.IF <FILERR> NE <SUCCES> .GOTO CRASH
$RUN CONFIG /A:174400
.IF <EXSTAT> EQ 1 .SETT DLCHK
$RUN CONFIG /A:172150
.IF <EXSTAT> EQ 1 .SETT DUCHK
.IFF DLCHK .AND .IFF DUCHK .GOTO PREVM1
.IFT DLCHK .SETS TRIALS "DL0,DL1"
.IFT DUCHK .SETS TRIALS "DU0,DU1,DU2,DU3"
.IFT DLCHK .AND .IFT DUCHK .SETS TRIALS "DU0,DU1,DU2,DU3,DL0,DL1"
.TRYNXT:
.PARSE TRIALS "," TRY TRIALS
.IF TRY = "" .GOTO PREVM1
.TESTDEVICE 'TRY'
.PARSE <EXSTRI> "," DNAME DSIZE REST
.IF DNAME = "NSD" .GOTO TRYNXT
.SETN TEMPN 'DSIZE'
.IF TEMPN < MINSIZ .GOTO TRYNXT
.GOTO PREVM1
.PREDY:
.;IDs and OWNERs for RX02 distribution
.SETS VIYD0 "BA-P732F-BC "
.SETS VIYD1 "BA-P727F-BC "
.SETS VIYD2 "BA-P728F-BC "
.SETS VIYD3 "BA-P729F-BC "
.SETS VIYD4 "BA-P730F-BC "
.SETS VIYD5 "BA-P731F-BC "
.SETS VOYD0 "RX2 AUTO"
.SETS VOYD1 "RX2 1/5"
.SETS VOYD2 "RX2 2/5"
.SETS VOYD3 "RX2 3/5"
.SETS VOYD4 "RX2 4/5"
.SETS VOYD5 "RX2 5/5"
.;LABELS FOR RX02 ORIGINAL DISTRIBUTIONS
.SETS LBYD0 "RT-11 'RTVERS' BIN RX02 AUTO"
.SETS LBYD1 "RT-11 'RTVERS' BIN RX02 1"
.SETS LBYD2 "RT-11 'RTVERS' BIN RX02 2"
.SETS LBYD3 "RT-11 'RTVERS' BIN RX02 3"
.SETS LBYD4 "RT-11 'RTVERS' BIN RX02 4"
.SETS LBYD5 "RT-11 'RTVERS' BIN RX02 5"

.SETS SYVID VIYD0
.SETS SYVOL LBYD0
.SETS INSDSK VIYD0
.SETS DTYPE "RX02"
.SETS LAB LBYD1
.SETS VID VIYD1
.SETN MAXVOL 5	.; Constant - number of floppies in RX02 kit
.GOTO PRE0x1
.PREDL:
.;IDs and OWNERs for RL02 distribution
.SETS VILD1 "BC-P607F-BC "
.SETS VOLD1 "RL2 1/1"
.;IDs and OWNERs for RL02 backup of distribution
.SETS VILB1 "RTV5 BKUP   "
.SETS VOLB1 "RL2 1/1"
.;IDs and OWNERs for RL02 working system volume
.SETS VILW1 "RTV5 WORK   "
.SETS VOLW1 "RL2 WORK"
.;LABEL FOR RL02 ORIGINAL DISTRIBUTION
.SETS LBLD1 "RT-11 'RTVERS' BIN RL02 AUTO"
.;LABEL FOR RL02 DISTRIBUTION BACKUP
.SETS LBLB1 "RT-11 'RTVERS' BIN RL02 BACKUP"
.;LABEL FOR RL02 WORKING VOLUME
.SETS LBLW1 "RT-11 'RTVERS' BIN RL02 WORKING"

.SETS SYVID VILD1
.SETS SYVOL LBLD1
.SETS WORKID VILW1
.SETS WORKOW VOLW1
.SETS INSDSK VILD1
.GOTO PRE0x1
.PRERX:
.;IDs and OWNERs for RX50 distribution
.SETS VIFD0 "BL-P746F-BC "
.SETS VIFD1 "BL-P741F-BC "
.SETS VIFD2 "BL-P742F-BC "
.SETS VIFD3 "BL-P743F-BC "
.SETS VIFD4 "BL-P744F-BC "
.SETS VIFD5 "BL-P745F-BC "
.SETS VIFD6 "BL-AV43E-BC "
.SETS VIFD7 "BL-ED30B-BC "
.SETS VOFD0 "RX5 I"
.SETS VOFD1 "RX5 1"
.SETS VOFD2 "RX5 2"
.SETS VOFD3 "RX5 3"
.SETS VOFD4 "RX5 4"
.SETS VOFD5 "RX5 5"
.SETS VOFD6 "RX5 6"
.SETS VOFD7 "RX5 7"
.;IDs and OWNERs for RD51/RD52 working system
.SETS VIFW51 "RT11 WORK   "
.SETS VOFW51 "RD5 WORK"
.;LABELS FOR RX50 ORIGINAL DISTRIBUTIONS
.SETS LBFD0 "RT-11 'RTVERS' BIN RX50 AUTO"
.SETS LBFD1 "RT-11 'RTVERS' BIN RX50 1"
.SETS LBFD2 "RT-11 'RTVERS' BIN RX50 2"
.SETS LBFD3 "RT-11 'RTVERS' BIN RX50 3"
.SETS LBFD4 "RT-11 'RTVERS' BIN RX50 4"
.SETS LBFD5 "RT-11 'RTVERS' BIN RX50 5"
.SETS LBFD6 "RT-11 'RTVERS' BIN RX50 6"
.SETS LBFD7 "RT-11 'RTVERS' BIN RX50 7"

.SETS SYVID VIFD0
.SETS SYVOL LBFD0
.SETS MIDDLE "F"
.SETS INSDSK VIFD0
.SETS DTYPE "RX50"
.;>>>uncomment the following .;>>> statements when .TESTDEVICE/DU fixed
.;>>>.SETN FUNIT -1
.;>>>.SETS ERRTYP " trying to find 2nd floppy drive"
.;>>>.FLOPPY:
.;>>>.INC FUNIT
.;>>>.; Change following dest for a single drive floppy system
.;>>>.IF FUNIT > 7 .GOTO CRASH
.;>>>.SETS TEMPS "DU'FUNIT'"
.;>>>.TESTDEVICE 'TEMPS'
.;>>>.PARSE <EXSTRI> "," DNAME DSIZE REST
.;>>>.IF DNAME = "NSD" .GOTO FLOPPY
.;>>>.SETN TEMPN 'DSIZE'
.;>>>.IF TEMPN = 0 .GOTO FLOPPY
.;>>>.IF TEMPN >= MINSIZ .GOTO FLOPPY
.;>>>.IF FUNIT = <SYUNIT> .GOTO FLOPPY
.;>>>remove the following statement when .TESTDEVICE/DU fixed
.SETN FUNIT 2
.;>>>following six statements used for both fixed/broken .TESTDEVICE/DU
.SETS LEFT "DU'<SYUNIT>'"
.SETS RIGHT "DU'FUNIT'"
.SETS OTHER RIGHT
.IF <SYUNIT> LT FUNIT .GOTO LFIX
.SETN FUNIT 1
.SETS RIGHT "DU'<SYUNIT>'"
.SETS LEFT "DU'FUNIT'"
.SETS OTHER LEFT
.LFIX:
.;>>>.SETN FUNIT -1
.;>>>.FIXED:
.;>>>.INC FUNIT
.;>>>.IF FUNIT > 7 .GOTO PREALL
.;>>>.SETS TEMPS "DU'FUNIT'"
.;>>>.TESTDEVICE 'TEMPS'
.;>>>.PARSE <EXSTRI> "," DNAME DSIZE REST
.;>>>.IF DNAME = "NSD" .GOTO FIXED
.;>>>.SETN TEMPN 'DSIZE'
.;>>>.IF TEMPN < MINSIZ .GOTO FIXED
.;>>>.IFT RD .GOTO PREALL
.;>>>remove the following statement when .TESTDEVICE/DU fixed
.SETN FUNIT 0
.SETT RD
.SETS RDUNIT "DU'FUNIT'"
.GOTO PREALL
.PREPC:
.;IDs and OWNERs for PC325 and PC350/80 distribution
.SETS VIPD0 "BL-AI39E-BH "
.SETS VIPD1 "BL-AI30E-BH "
.SETS VIPD2 "BL-AI31E-BH "
.SETS VIPD3 "BL-AI32E-BH "
.SETS VIPD4 "BL-AI33E-BH "
.SETS VIPD5 "BL-AI34E-BH "
.SETS VIPD6 "BL-AI35E-BH "
.SETS VIPD7 "BL-ED31B-BH "
.SETS VOPD0 "RTPC I"
.SETS VOPD1 "RTPC 1"
.SETS VOPD2 "RTPC 2"
.SETS VOPD3 "RTPC 3"
.SETS VOPD4 "RTPC 4"
.SETS VOPD5 "RTPC 5"
.SETS VOPD6 "RTPC 6"
.SETS VOPD7 "RTPC 7"
.;IDs and OWNERs for PC350/80 working system
.SETS VIPW51 "RT11 WORK   "
.SETS VOPW51 "RTPC WORK"
.;LABELS FOR PC325/PC350/80 ORIGINAL DISTRIBUTIONS
.SETS LBPD0 "RT-11 'RTVERS' BIN RTPC AUTO"
.SETS LBPD1 "RT-11 'RTVERS' BIN RTPC 1"
.SETS LBPD2 "RT-11 'RTVERS' BIN RTPC 2"
.SETS LBPD3 "RT-11 'RTVERS' BIN RTPC 3"
.SETS LBPD4 "RT-11 'RTVERS' BIN RTPC 4"
.SETS LBPD5 "RT-11 'RTVERS' BIN RTPC 5"
.SETS LBPD6 "RT-11 'RTVERS' BIN RTPC 6"
.SETS LBPD7 "RT-11 'RTVERS' BIN RTPC 7"

.SETS SYVID VIPD0
.SETS SYVOL LBPD0
.SETS LEFT "DZ0"
.SETS RIGHT "DZ1"
.SETS RDUNIT "DW0"
.SETS MIDDLE "P"
.SETS INSDSK VIPD0
.SETS DTYPE "RX50"
.SETS LAB LBPD1
.SETS VID VIPD1

.PRE0x1:
.IF <SYUNIT> EQ 0 .SETS OTHER <SYDISK>+"1"
.IF <SYUNIT> NE 0 .SETS OTHER <SYDISK>+"0"
.PREALL:
.SETN MAXRX MAXVOL .; Variable - number of floppies in kits to copy
.SETS ERRTYP ": Installation 'DISK' contains invalid volume ID."
.ONERR CRASH
.VOL VOLID 'SYSTEM'
.ONERR
.IF VOLID NE INSDSK .GOTO CRASH
.SETS OTHERD OTHER+" (Drive "+OTHER[3:3]+")"
.SETS SYSTMD SYSTEM+" (Drive '<SYUNIT>')"
.IFT DL .GOTO INIDL
.IFT RX .GOTO INIWYZ
.IFT DW .GOTO INIWYZ
.IFT DY .GOTO INIWYZ
.IFT DZ .GOTO INIWYZ
.SETS ERRTYP "Logic error 1"
.GOTO CRASH
.WELCOM:
;
;	Welcome to RT-11 'RTVERS'
;
.RETURN

.ONLYRT:
;	This  working  system disk will only  contain  the  RT-11  operating
;	system.  After  the  RT-11  installation  is  complete,  follow  the 
;	installation instructions  packaged  with  any optional languages or
;	utility software which you will be using.
;
.RETURN

.GUIDE:
.GOSUB HEADER
;
;	You  will  be guided through the installation process by a series of
;	instructions  and questions; you have an interactive dialog with the
;	RT-11  installation  program.   All  you  need  to  do is follow the
;	instructions  carefully.  When  the  instructions ask you to mount a
.RETURN

.INIWYZ:
.GOSUB WELCOM
;	You have bootstrapped the RT-11 'RTVERS' Installation Diskette.
;
;	Your RT-11 'RTVERS' software package has two sets of 'DTYPE' diskettes
;	containing identical copies of the RT-11 software.   Each set consists
;	of  a  'MAXVOL'  diskette  operating  system   and   one  installation
;	diskette.
;
;	One  set  is  your  master  copy; store it in a safe place.  The other
.IFF PC .IFF RD .GOTO INIEZY
;	set,  from  which the installation diskette is now mounted, is the set
;	you  will  use to build your working system volume on your fixed disk.
.GOSUB RURTC
.GOSUB GUIDE
;	diskette in  a  specified drive,  find the diskette with the correct
;	label and  mount  it  in  the  drive, as  shown in your installation
;	booklet.  Remember  that  the  'DTYPE' drives are  numbered from top to
;	bottom on  a  horizontally  mounted  unit,  and  left  to right on a
;	vertically  mounted unit.  The top or left-hand drive is 'LEFT' and the
;	bottom  or right-hand drive is drive 'RIGHT'.  The  fixed disk is always
;	'RDUNIT'.
.GOTO INTRTC

.INIEZY:
;	set,  from  which  the  installation  diskette is now mounted, is your
;	working system which should be used for your work with RT-11.
;
;	The installation procedure for an 'DTYPE' system consists only of boot-
;	strapping diskette volume 1 from your working system.
.GOTO INTRTC

.PREVM1:
.GOSUB WELCOM
;	You have bootstrapped the RT-11 Distribution Tape.  Use this tape to
;	install your RT-11 system, then store it in a safe place.
;
;	RT-11  'RTVERS'  provides an automatic installation procedure which
;	will build a working system disk which should be used for your work
;	with RT-11.
.GOSUB ONLYRT
;
;	Please enter the device name to have the working system built on.
;	If the default device is correct, just press RETURN.
;
.IF DNAME = "NSD" .GOTO Q2
.ASKS [2:3:DNAME] DNAME		What device is the working system to be built on ('DNAME')?
.GOTO MAIN1
.Q2:
.ASKS DNAME		What device is the working system to be built on ?
.IFT DNAME EQ "" .GOTO Q2
.MAIN:
.SETS OTHER DNAME
.SETS TEMPS DNAME[1:2]
.IF TEMPS = "DU" .SETT DU
.SETS OTHERD OTHER+" (Drive "+OTHER[3:3]+")"
.GOTO INIVMM
.INIDL:
.GOSUB WELCOM
;	You have bootstrapped the RT-11 Distribution Disk.  Use this disk to
;	install your RT-11 system, then store it in a safe place.
;
;	RT-11  'RTVERS'  provides an automatic installation procedure which will
;	back up your distribution disk and build a working system disk which
;	should  be  used for your work with RT-11.
.GOSUB ONLYRT
.GOSUB RURTC
.INIVMM:
.GOSUB HEADER
;	You  can  choose  to  install  RT-11  manually.  This  procedure  is
;	described in the RT-11 Installation Guide. 
;
;	If  you  are a new user of RT-11, DIGITAL highly recommends that you
;	use the automatic installation procedure.
;
.INTUSE:
;	Do you want to use the automatic installation procedure?
.ASK USE         (Type YES or NO and press the "RETURN" key):
.IFT <DEFAUL> .GOTO INTUSE
.IFT USE .GOTO INTINS
.GOSUB HEADER
;
.IFF VM ;	The standard RT-11 monitor boostrap (RT11FB) will now be
.IFF VM ;	copied to this disk and this system disk will be rebooted.
.IFT VM ;	RT-11 is currently running from VM.  VM also contains the
.IFT VM ;	utility programs and handlers required for a installation.
;	Please refer to the RT-11 Installation Guide for assistance
;	while manually installing RT-11 'RTVERS'.
.SETS FILE "RT11FB"
.SETS BOTVOL SYSTEM
.GOSUB COPBOT
.GOSUB RURTC
.IFT VT100 ;[2J[?5l[r
$BOOT 'SYSTEM':
.SETS ERRTYP " booting 'SYSTEM'"
.GOTO CRASH

.INTINS:
.GOSUB GUIDE
;	disk in a specified drive, find the disk with the correct label  and
;	mount it in the drive, as shown in your installation booklet. 
;
;	Do  not  remove  any  'DISK' until specifically instructed to do so.
;	Once  a  'DISK'  is  mounted in a drive, it must remain in the drive
;	until a message appears asking you to remove the 'DISK'.
.INTRTC:
.GOSUB RURTC
.SETF CONF
.IFT VM .GOTO INTVM1
.IFT DL .GOTO INTDL1
.IFT RD .GOTO INTDAT
.IFT DW .GOTO INTCNF
.IFT RX	.GOTO INTBOT
.IFT DY	.GOTO INTBOT
.IFT DZ	.GOTO INTBOT
.SETS ERRTYP " Logic error 2"
.GOTO CRASH
.INTCNF:
.SETS HEADER "PC300 Configuration Option"
.GOSUB HEADER
;
;	This installation  procedure  gives  you  the  choice of creating a
;	configured system,  or  copying  the  complete  distribution to the
;	working disk.   If you select the configured system,   your working
;	disk will contain a pre-built extended memory monitor, and only the
;	handlers and utilities  supported  for  use  on the PC300.  This is
;	sufficient for most requirements,   however,  if you wish to use an
;	alternate monitor or perform a system generation (SYSGEN)  then the
;	complete distribution will be required.   Also, some of the layered
;	products (such as CTS300) require a complete distribution.
;
;
.ASK [<TRUE>] CONF         Do you want a configured working disk (Y)?
.IFT CONF .SETN MAXRX 3

.INTDAT:
.GOSUB GETDAT		.;Enter the date
.GOSUB BACKRX		.;Copy the RX50s to RD51
.IFT CONF .GOSUB DELS	.;Delete unnecessary files.
.GOTO INTBOT

.INTVM1:
.GOSUB GETDAT
.GOSUB INSTDL
.GOTO INTBOT

.INTDL1:
.GOSUB GETDAT		.;Enter the date
.GOSUB BACKDL		.;Backup an RL02 kit
.GOSUB INSTDL		.;Build a working RL02

.INTBOT:
.SETS BOTVOL OTHER
.IFT RD .OR .IFT DW .SETS BOTVOL RDUNIT
.;Boot the working volume.
.;
.SETS HEADER "RT-11 'RTVERS' Installation Complete"
.GOSUB HEADER
;
;	Your working system 'DISK' will now be bootstrapped.
.IFF DY .AND .IFF DZ .GOSUB RURTC
.IFT DY .OR .IFT DZ .GOSUB MOUNT
.IFT VT100 ;[2J[?5l[r
.SETS INSPEC BOTVOL+":"
.GOTO BOOT
.HEADER:
.;
.;	Clear the Screen and Display Heading
.;
.IFF VT100 .RETURN
;[H[2J[4;22r
; #3  'HEADER'
; #4  'HEADER'
; [4;1H[m
.RETURN
.YHR:
.SETS READY "you have removed the 'DISK'"
.GOTO CONTIN

.YHM:
.SETS READY "you have mounted the 'DISK'"
.GOTO CONTIN

.RURTC:
.SETS READY "ready to continue"

.CONTIN:
.;Do the CONTINUE? prompt.  If REPEAT is true on exit, the user
.;wants to continue after answering NO to CONTINUE?
.;
.SETF REPEAT
;
.ASK [<TRUE>] CONT         Press the "RETURN" key when 'READY'.
;
.IFT CONT .RETURN
.CON10:
.SETT REPEAT
.ASK CONT         Do you want to continue with this installation?
.IFT <DEFAUL> .GOTO CON10
.IFT CONT .RETURN
.GOTO AEXIT
.GETDAT:
.IF <DATE> NE "         " .IFF PC .RETURN
.SETS HEADER "Enter Today''s Date"
.GOSUB HEADER
;
;	Please enter today''s date in the following format:
;
;	DD-MMM-YY
;          where DD is the day of the month
;		MMM is the first 3 letters in the name of the month
;	YY is the last two numbers of the year
;
;	For example:   September 19, 1984 is 19-SEP-84
;
;	Type in the date, then press the "RETURN" key.
;
.ASKS DAT              
;
;
$DATE 'DAT'
.IF <EXSTAT> EQ <SUCCES> .GOTO GETTIM
;
;	Wrong format for date.
.GOSUB RURTC
.GOTO GETDAT
.;this subroutine test for QUANTUM RD52 disk
.QNTCHK:
$RUN CONFIG /R:440/B/V:5
.IF <EXSTAT> NE 1 .GOTO EX1
$RUN CONFIG DW:/F:1700/V:177777
.IF <EXSTAT> EQ 1 .GOTO EX1
.SETS	HEADER  "RT-11 Automatic Installation Process"
.GOSUB HEADER
;
;	The Automatic Installation (AI) Procedure has determined that your
;	PRO 300 series computer contains an RD52 hard disk that may require
;	special operations. The initialization of that hard disk performed by 
;	the AI Procedure will decrease the available size of your hard disk 
;	by 128 (decimal) blocks. 
;
;	Carefully read section 3 of the "RT-11 On The PRO Cover Letter" you 
;	received with your distribution before continuing the AI Procedure.
;
.GOSUB CON10
.EX1: .RETURN
.GETTIM:
.IFF PC .RETURN
.SETS HEADER "Enter the correct time"
.GOSUB HEADER
;
;	Please enter the correct time in the following format:
;
;	HH:MM
;          where HH is the hour of the day
;                MM is the number of minutes past the hour
;
;	For example:   3:05 PM  is 15:05
;
;	Type in the time, then press the "RETURN" key.
;
.ASKS TIM              
.PARSE DAT "-" DAY MON YEA
.SETS DAT DAY+":"+MON+":"+YEA
$SETUP TIME:'TIM',DATE:'DAT'
.IF <EXSTAT> EQ <SUCCES> .RETURN
;
;	Wrong format for time.
.GOSUB RURTC
.GOTO GETTIM
.;*************************************************************************
.;		RL02 CONFIGURATION PROCEDURES
.;*************************************************************************
.;
.BACKDL:
.;Backup a RL02 distribution kit
.;
.SETS HEADER "Backing Up Distribution Disk
.GOSUB HEADER
;
;	A backup copy of the distribution disk will now be built.
.SETS OUVID VILB1
.SETS OUOWN VOLB1
.SETT HELP
.GOSUB MNTBLK
.SETF HELP
.GOSUB HEADER
;
;	Now copying the distribution disk from 'SYSTMD' to 'OTHERD'.
;
;	This may take up to five minutes.  Please wait...
;
.GOSUB COPYSY
.GOSUB HEADER
;
;	Your backup copy of the distribution disk is in 'OTHERD'.
;
;	Please remove this disk from 'OTHER' and label it
;	"'LBLB1'".
;	Refer to Appendix B of your installation booklet for instructions
;	for dismounting a disk.
.GOSUB YHR
.RETURN
.INSTDL:
.;Install RT-11 on a working system disk from a single distribution volume.
.;
.SETS HEADER "Building Working System"
.GOSUB HEADER
;
;	Your working system disk will now be built automatically. This  disk
;	will contain the RT-11 Operating System.
.SETS OUVID WORKID
.SETS OUOWN WORKOW
.SETS LABEL LBLW1
.GOSUB MNTLAB
.GOSUB HEADER
;
;	Now copying RT-11 from 'SYSTMD' to 'OTHERD'.
;
;	This can take approximately two minutes.  Please wait...
.IFF VM .GOTO INST10
;??? here force a rewind???
.SETS INSPEC TAPE+":*.*/SYSTEM/POSITION:-1"
.SETS OUSPEC OTHER+":/NOREPLACE"
.GOSUB COPY
.SETS FILE "RT11FB"
.SETS BOTVOL OTHER
.GOSUB COPBOT
.GOTO INST20:

.INST10:
.GOSUB COPYSY
.INST20:
.SETS INSPEC OTHER+":*.*"
.GOSUB UNPROT
.RETURN
.;***********************************************************************
.;               MICRO PDP-11 AND PC300 PROCEDURES
.;***********************************************************************
.BACKRX:
.;Backup the floppies to the whinnie
.SETS HEADER "Building Working System"
.SETS OUVID VI'MIDDLE'W51
.SETS OUOWN VO'MIDDLE'W51
.SETS SAV OTHER
.SETS OTHER RDUNIT
.GOSUB MNTBLK
.SETS OTHER SAV
.SETN COUNT 1
.RX10:
.GOSUB HEADER
.SETS LAB LB'MIDDLE'D'COUNT'
.SETS VID VI'MIDDLE'D'COUNT'
;
.GOSUB MOUNT
.GOSUB HEADER
;
;	Now copying 'LAB' to the fixed disk ('RDUNIT').
;
;	This can take approximately two minutes.  Please wait...
.SETS INSPEC "'OTHER':*.*"
.SETS OUSPEC "'RDUNIT':*.*"
.GOSUB COPY
.INC COUNT
.IF COUNT LE MAXRX .GOTO RX10
.SETS INSPEC "CONFIG.*,*.TXT"
.SETS OUSPEC RDUNIT+":"
.GOSUB COPY
.SETS FILE "RT11FB"
.IFT PC .SETS FILE "RT11XM"
.SETS BOTVOL RDUNIT
.GOSUB COPBOT
;
;	Remove 'LAB' from 'OTHER'.
.GOSUB YHR
.RETURN
.DELS:
.;Remove unnecessary files from the working disk.
.SETS HEADER "Customizing working disk"
.GOSUB HEADER
;
;         Your working disk is now being customized for a PC300.
;
;         Deleting unnecessary files
;
;         This can take approximately three minutes, please wait...
.SETS DV RDUNIT+":"
.SETS INSPEC DV+"(DLX.SYS,DMX.SYS,DXX.SYS,DYX.SYS,MMX.SYS,MSX.SYS)"
.GOSUB UNPROT
.GOSUB DELETE
.SETS INSPEC DV+"(MTX.SYS,RKX.SYS,XLX.SYS,LPX.SYS,DDX.SYS,DUX.SYS)"
.GOSUB UNPROT
.GOSUB DELETE
.SETS INSPEC DV+"(ODT.OBJ,KED.SAV,K52.SAV,FILEX.SAV,NQX.SYS)"
.GOSUB UNPROT
.GOSUB DELETE
.SETS INSPEC DV+"(RT11BL.SYS,RT11SJ.SYS,RT11FB.SYS,%%.SYS)"
.GOSUB UNPROT
.GOSUB DELETE
.SETS INSPEC DV+"(STARTS.COM,STARTF.COM,BATCH.SAV,ERROUT.SAV,SPEED.SAV)"
.GOSUB UNPROT
.GOSUB DELETE
.SETS INSPEC DV+"(TRANSF.SAV,VTCOM.REL,DATIME.SAV)"
.GOSUB UNPROT
.GOSUB DELETE
.SETS INSPEC DV
;
;        Squeezing working disk
;
;        This can take approximately five minutes, please wait....
;
.GOSUB SQUEEZ
.RETURN
.;***********************************************************************
.;		COMMON PROCEDURES
.;***********************************************************************
.;
.;This procedure mounts a blank volume in the OTHER drive.
.;The volume is assumed blank if it has no volid or contains no files.
.;
.; MNTLAB asks for labeling before
.; MNTBLK does mount
.;Input:  OUVID = Volume id to be put on volume
.;	  OUOWN = Owner name for volume
;
.MNTLAB:
;	Select a blank 'DISK' and label it: "'LABEL'"
;	and mount it in 'OTHERD'.
.GOTO MNTCOM

.MNTBLK:
.IFT DW .OR .IFT RX .OR .IFT DU .GOTO MNTCOM
;	Mount a blank 'DISK' in 'OTHERD'.
.IFT DL;	See the Automatic Installation Booklet for mounting instructions.
;	(Remember that the disk is not mounted until you have pressed the LOAD
;	button and the READY indicator light is on).
.MNTCOM:;
;
.SETS INIVOL OTHER
.IFT DW .OR .IFT RX .OR .IFT DU .GOTO MNT7
.GOSUB YHM
.MNT7:	.IFT REPEAT .GOTO MNTBLK
.STRUCTURE TYPE 'OTHER':
.SETN NTYPE 'TYPE'/10
.IF NTYPE = 0 .GOTO INIBLK
.IF NTYPE = 1 .SETS STRUCT " PDP/8  "
.; this part of code is position dependent and should not be replaced
.IF NTYPE = 2 .AND .IFT DW .GOSUB QNTCHK
.IF NTYPE = 2 .AND .IFT DW .GOSUB HEADER
.IF NTYPE = 2 .AND .IFT DW .GOTO MNT15
.IF NTYPE = 2 .GOTO FLCHK
.IF NTYPE = 3 .SETS STRUCT "  RSTS  "
.IF NTYPE = 4 .SETS STRUCT "FILES-11"
.IF NTYPE = 5 .SETS STRUCT "  UNIX  "
.IF NTYPE = 6 .SETS STRUCT "   DSM  "
.IF NTYPE = 10 .SETS STRUCT "  CP/M  "
.IF NTYPE = 11 .SETS STRUCT "  UCSD  "
.IF NTYPE = 12 .SETS STRUCT " MS-DOS "
.IFNDF STRUCT .SETN STRUCT "UNKNOWN "
.GOSUB HEADER
;	The  Automatic  Installation  Procedure  has detected that the working
;	volume you specified has been previously used as a 'STRUCT' disk.  The
;	next procedure initializes 'OTHER'.
.GOTO MNT15
.FLCHK:	$DIR/OUT:'OTHER':CI.TMP 'OTHER':
.IF <EXSTAT> NE 1 .GOTO INIBLK
.OPENR 'OTHER':CI.TMP
.READ LINE
.READ LINE
.CLOSE
.SETS INSPEC "'OTHER':CI.TMP"
.GOSUB DELETE
.IF LINE EQ "" .GOTO INIBLK
.VOL VOLID 'OTHER'
.GOSUB CHKVOL
.SETS NOBLK "NOT blank."
.IFF VOLBLK .SETS NOBLK "an original distribution"
.GOSUB HEADER
;
.IFT DW .OR .IFT RX .OR .IFT DU .GOTO MNT20
;	The 'DISK' you mounted in 'OTHERD' is 'NOBLK'
.IFF VOLBLK;        or backup 'DISK'.
.GOTO MNT15

.MNT20:
;	The Automatic Installation Procedure has detected RT-11  files  on
;	your working system volume.
.MNT15:;
;	The next procedure initializes 'OTHER'.  As a  result,  any  files
;	that currently reside on 'OTHER' will be permanently lost. If  you 
;	would like to retain any files,  EXIT  from Automatic Installation
;	Procedure and copy  them  to another volume.
;
;
.ASK [<TRUE>] CONT 	Do you want to EXIT from Automatic Installation (Y)?
.SETS INIVOL OTHER
.IFF CONT .GOTO INIBLK
.IFT DW .OR .IFT RX .OR .IFT DU .GOTO FAEXIT
.GOSUB HEADER
.GOTO MNTBLK
.CHKVOL:
.;Check a volume ID to see if it is that of a distribution or
.;backup of a distribution volume.
.;
.;Input:   VOLID
.;Output:  VOLBLK - <TRUE> Volume id is of a blank volume
.;	          - <FALSE> Volume id is of a dis or backup volume
.;
.SETT VOLBLK
.IFF DY .GOTO CV10
.SETN CNT 0
.CV5:
.IF VOLID EQ VIYD'CNT' .OR .IF VOLID EQ VIYB'CNT' .SETF VOLBLK
.INC CNT
.IF CNT LE MAXVOL .GOTO CV5
.RETURN

.CV10:	.IFF DL .RETURN
	.IF VOLID EQ VILD1 .OR .IF VOLID EQ VILB1 .SETF VOLBLK
.RETURN
.INIBLK:
.; Initialize a volume in 'INIVOL'.
.; Input: OUVID - Volume ID
.;	  OUOWN - Owner name
.GOSUB HEADER
.IFF HELP .GOTO INI3
;
;	Before  a  blank  disk  can  be used it must be prepared so that the
;	software can write data to it. This preparation is called initiali-
;	zation.
;
.INI3:
;	The disk in 'INIVOL' is now being initialized.
;
;	The following procedure should produce informational  messages
;	in the form ?FORMAT-I-Message,  or ?DUP-I-Message.  No  action
;	is required as a result of these messages.  If BAD blocks  are
;	detected, the block number will be provided.  This information
;	should be noted for future reference.
;
;	This can take approximately fifteen minutes.  Please wait...
;
;
.OPEN CI.TMP
.SETS ERRTYP " creating CI.TMP."
.IF <FILERR> NE <SUCCES> .GOTO CRASH
.SETS REP "/REPLACE"
.IFT RX .OR .IFT DW .OR .IFT DU .SETS REP "/BAD"
.IFF DW .GOTO INI4
.ENABLE DATA
$UNLOAD DW:
$REMOVE DW:
$FORMAT/NOQ 'INIVOL':
$INSTALL DW:
$FORMAT/NOQ/VERIFY:ONLY 'INIVOL':
.DISABLE DATA
.INI4:
.ENABLE DATA
$INIT/NOQUERY'REP'/VOL 'INIVOL':
'OUVID'
'OUOWN'
.DISABLE DATA
.CLOSE
$@CI.TMP
.IF <EXSTAT> EQ <SUCCES> .GOTO INI6
.IF <EXSTAT> NE <WARNIN> .GOTO BAD5
.IFT DZ .GOTO BADBLK
.INI6:
.SETS INSPEC "CI.TMP"
.GOSUB DELETE
.RETURN

.BAD5:
.SETS INSPEC "CI.TMP"
.GOSUB DELETE
.IFT RX .GOTO BADQIT
;
;	An error occurred while initializing 'INIVOL'.
.IFF DL .GOTO BADRTY
;	This may have been caused by an incorrectly mounted disk.
;	Be sure that:
;	      - Cartridge is positioned correctly in drive
;	      -	Protective cover is in place
;	      - Drive is write enabled (WRITE PROT button is NOT lit)
;	      - Yellow LOAD button is pushed and time allowed for
;		white READY light to come on
;
.ASK RETRY         Do you want to try again?
.IFF RETRY .GOTO BADRTY
.GOSUB RURTC
.GOTO INIBLK

.BADRTY:
;
.ASK RETRY         Do you want to try another blank disk?
.IFT <DEFAUL> .GOTO BADRTY
.IFF RETRY .GOTO BADQIT
.IFT DW $INSTALL DW:
.GOTO MNTBLK

.BADQIT:
.SETS ERRTYP " initializing 'INIVOL'"
.GOTO CRASH

.BADBLK:
.SETS INSPEC "CI.TMP"
.GOSUB DELETE
.GOSUB	HEADER
;
;
;	The 'DISK' in 'INIVOL' contains bad blocks.
.BADMNT:
;
;	Mount another blank 'DISK' in 'INIVOL'.
.GOSUB YHM
.IFT REPEAT .GOTO BADMNT
.GOTO INIBLK
.MOUNT:
.;Mount a volume.
.;Input:  LAB and VID = Label and volume id of volume to mount
.;	  OTHER = drive to mount it.
.MNT1:
;
;	Mount 'LAB' in 'OTHERD'.
.GOSUB YHM
.ONERR MNT2
.VOL VOLID 'OTHER':
.ONERR
.IF VOLID EQ VID .RETURN
;
;	Wrong 'DISK' mounted in 'OTHERD'.
.GOTO MNT1

.MNT2:
;
;	The 'DISK' mounted in 'OTHERD' is not properly mounted.  See
;	your installation booklet for mounting instructions.
.GOTO MNT1
.COPYSY:
$SQUEEZE/NOQ/OUT:'OTHER': 'SYSTEM':
.SETS ERRTYP " copying 'SYSTMD' to 'OTHERD'"
.IF <EXSTAT> GT 1 .GOTO CRASH
.SETS FILE "RT11FB"
.SETS BOTVOL OTHER
.; drop thru

.COPBOT:
$COPY/BOOT 'BOTVOL':'FILE' 'BOTVOL':
.IF <EXSTAT> EQ <SUCCES> .RETURN
.SETS DCLCMD "COPBOT"
.SETS ERRTYP " copying the bootstrap to 'BOTVOL'
.GOTO DCLERR

.RENAME:
$RENAME/NOLOG 'INSPEC' 'OUSPEC'
.IF <EXSTAT> LE 1 .RETURN
.SETS DCLCMD "RENAME"
.SETS ERRTYP " renaming 'INSPEC' to 'OUSPEC'"
.GOTO DCLERR

.DELETE:
$DELETE/NOQ 'INSPEC'
.IF <EXSTAT> LE 1 .RETURN
.SETS DCLCMD "DELETE"
.SETS ERRTYP " deleting 'INSPEC'"
.GOTO DCLERR

.COPY:
$COPY/NOREPL/NOLOG/SYS 'INSPEC' 'OUSPEC'
.IF <EXSTAT> LE 1 .RETURN
.SETS DCLCMD "COPY"
.SETS ERRTYP " copying 'INSPEC' to 'OUSPEC'"
.GOTO DCLERR

.UNPROT:
$UNPROTECT/NOLOG/SYS 'INSPEC'
.IF <EXSTAT> EQ <SUCCES> .RETURN
.SETS DCLCMD "UNPROT"
.SETS ERRTYP " unprotecting 'INSPEC'"
.GOTO DCLERR

.BOOT:
$BOOT 'INSPEC'
.IF <EXSTAT> EQ <SUCCES> .RETURN
.SETS DCLCMD "BOOT"
.SETS ERRTYP " bootstrapping 'INSPEC'"
.GOTO DCLERR

.SQUEEZ:
$SQUEEZE/NOQ 'INSPEC'
.IF <EXSTAT> EQ <SUCCES> .RETURN
.SETS DCLCMD "SQUEEZ"
.SETS ERRTYP " squeezing 'INSPEC'"

.DCLERR:
;
;	An error occurred'ERRTYP'
;
.ASK RETRY	Do you want to try again?
.IFT RETRY .GOTO 'DCLCMD'
.CRASH:
.SETS HEADER "Installation Error"
.GOSUB HEADER
;
;
;  Error 'ERRTYP'
;
;  If you cannot immediately identify and correct the error,
;  please call the HOTLINE number on your instruction sheet
;  for assistance.  
.EXIT

.PDT:
;
; You are operating under a special RT-11 monitor. To obtain a full
; function system for PDT use, mount volume 1 in PD1 and change the
; bootstrap with the command  COPY/BOOT PD1:RT11FB PD1:  The volume
; in PD1 can then be booted and RT-11 manually installed.    Do NOT
; use this special monitor for any other purpose.
;
.EXIT

.FEXIT:
.SETS HEADER "Fatal RT-11 Installation Error
.GOSUB HEADER
;
;	    The Installation procedures on this disk cannot be
;   used with this hardware configuration.
.EXIT

.AEXIT:
.SETS HEADER "Installation Aborted"
.GOSUB HEADER
;
;     Installation aborted by operator.
;
;     Reboot 'SYVOL' to begin again.
.EXIT

.FAEXIT:
.SETS HEADER "Installation Aborted"
.GOSUB HEADER
;
;	Make a copy of the files on 'OTHER' that you want to keep  and
;	begin the Automatic Installation procedure again.
;
;
.EXIT
                   