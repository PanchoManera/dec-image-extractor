.;Don't forget to change PATLEV as well as VERSION in .MODULE
.;.MODULE SYSGEN,RELEASE=V05,VERSION=52,COMMENT=<SYSGEN Control File>
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
.;
.SETS PATLEV	"V05.52"	.;SYSGEN version number

.BEGIN:
	.DISABLE PREFIX
	.DISABLE SUFFIX
	.ENABLE LOWERCASE
	.ENABLE ESCAPE
	.ENABLE QUIET

.; PARAMETERS:
.; P1 = LIST/NOLIST create LIST files
.; P2 = QUERY OR NOQUERY 
.; P3 = NAME OF ANSWER FILE TO BE USED
.; P4 = T/F if SYCND conditonal should be generated

	.SETS ANSFIL "SYSGEN.ANS"
	.SETT GENSYS
	.SETF LST
	.SETF NOQ
	.IF P1 EQ "" .GOTO WH5
	.IF P1 EQ "LIST" .SETT LST
	.IF P2 EQ "" .GOTO WH1
	.SETS TEMPS P2[1:3]
	.IF TEMPS EQ "NOQ" .SETT NOQ
	.IF P3 EQ "" .GOTO WH1
	.SETS ANSFIL P3
	.IF P4 EQ "" .GOTO WH1
	.SET'P4' GENSYS
.WH1:
	.IFT NOQ ;	SYSGEN RUN IN NOQUERY MODE
	.IFT NOQ ;	ANSWER FILE USED: 'ANSFIL'
	.IFF GENSYS ;	SYSGEN CONDITIONAL NOT PUT IN SYCND
	.IFT LST ;	LISTING FILES WILL BE CREATED ON LST:
.WH5:	.SETT VT100
	.SETF GRAFX
	.SETN EMPTY 0
	.SETN UPNO 0
	.SETS CANSF ""
	.SETS LP1 "P"	;CTS-300 PRINTERS
	.SETS LP2 "Q"
	.SETS LP3 "R"
	.SETS LP4 "S"
	.SETS LPID1 "3"	;LPn
	.SETS LPID2 "31";LQn
	.SETS LPID3 "32";LRn
	.SETS LPID4 "33";LSn
	.SETS C1 "first"
	.SETS C2 "second"
	.SETS C3 "third"
	.SETS C4 "fourth"
	.SETS C5 "fifth"
	.SETS C6 "sixth"
	.SETS C7 "seventh"
	.SETS C10 "eighth"
	.SETF CHANGE
	.SETT NOPRO
	.SETS SYCND "SYSGEN.CND"
	.SETS SYFIL SYCND
	.SETS DEVTBL "SYSGEN.TBL"
	.SETS DEVFIL DEVTBL
	.SETS MONBLD "SYSGEN.MON"
	.SETS DEVBLD "SYSGEN.DEV"
	.SETS SYSBLD "SYSGEN.BLD"
.; DEVBND is list of handlers that require /BOUND:512. on link command
	.SETS DEVBND " DU LS SL "

.; DEVSTR is list of "known" handler names
	.SETS DEVSTR " DX DY DD PD RF RK DL DP DM MT MM MS MU NL LD VM DZ DW SP XL XC NC NQ CR LP DU LS DT DS CT PC PR "
.; DEVSTR should currespond to DCMnn as listed below:
	.SETS DCM1 "DX  RX01 Single-Density Diskette"
	.SETS DCM2 "DY  RX02 Double-Density Diskette"
	.SETS DCM3 "DD  TU58 DECtape II             "
	.SETS DCM4 "PD  PDT-11 Intelligent Terminal "
	.SETS DCM5 "RF  RF11 Disk                   "
	.SETS DCM6 "RK  RK05 Cartridge Disk         "
	.SETS DCM7 "DL  RL01/RL02 Cartridge Disk    "
	.SETS DCM10 "DP  RP11 Disk Pack              "
	.SETS DCM11 "DM  RK06/RK07 Cartridge Disk    "
	.SETS DCM12 "MT  TM11 (UNIBUS) Magtape       "
	.SETS DCM13 "MS  TS11,TU80/TSV05/TSU05 Tape  "
	.SETS DCM14 "MM  TJU16 (MASSBUS) Magtape     "
	.SETS DCM15 "CR  Card Reader                 "
	.SETS DCM16 "NL  Null Handler                "
	.SETS DCM17 "LP  Line Printer                "
	.SETS DCM20 "DU  MSCP Disk Class Handler     "
	.SETS DCM21 "LD  Logical Disk Handler        "
	.SETS DCM22 "VM  Virtual Memory Handler      "
	.SETS DCM23 "DZ  RX50 PRO Series             "
	.SETS DCM24 "DW  RD50/51/52 PRO Series       "
	.SETS DCM25 "SP  Transparent Spooling Handler"
	.SETS DCM26 "XL  VTCOM Communications Handler"
	.SETS DCM27 "XC  VTCOM Handler PRO Series    "
	.SETS DCM30 "NC  Ethernet Handler PRO Series "
	.SETS DCM31 "NQ  Ethernet Handler for Q-BUS  "
	.SETS DCM32 "MU  TMSCP Magtape Class Handler "
	.SETN CTSMAX 32
.;; END OF CTS HANDLERS
	.SETS DCM33 "LS  Serial Line Printer         "
	.SETS DCM34 "DT  DECtape                     "
	.SETS DCM35 "DS  RJS03/4 Fixed-head Disk     "
	.SETS DCM36 "CT  TA11 Cassette               "
	.SETS DCM37 "PC  PC11 Paper Tape Reader/Punch"
	.SETS DCM40 "PR  PR11 Paper Tape Reader      "
	.SETN MAXDEV 40
	.SETN RTDEVS MAXDEV
	.SETN CNT 1
.Z27:
	.SETS DCOM DCM'CNT'[1:2]
	.SETF 'DCOM'
	.INC CNT
	.IF CNT LE RTDEVS  .GOTO Z27
	.SETF LPP
	.SETF LQP
	.SETF LRP
	.SETF LSP
	.SETF LPS
	.SETF LQS
	.SETF LRS
	.SETF LSS
	.SETF MT$FSM
	.SETF MM$FSM
	.SETF MS$FSM
	.SETF MU$FSM
	.SETF PROCTS
	.SETF BU$BBR
	.SETF BU$BOO
	.SETF CTS
	.SETF SWIT
	.SETS LINK "LINK/NOBITMAP/EXE:BIN:"
	.SETS MAP ""
	.IFT LST .SETS MAP "/MAP:LST:"
	.SETS STARS "*****************************************************************"
	;
	;
	; 'STARS'
	; 		RT-11 SYSTEM GENERATION PROGRAM 'PATLEV'
	; 'STARS'
	;
.INASK:
	.IFT NOQ .GOTO ANSFL
	;
	.ASK ANS Do you want an introduction to system generation (N)?
	.IFF <ESCAPE> .GOTO IN10
	;
	; Type  "Y"  for  a  detailed  explanation of the system generation
	; process.
	.GOTO INASK

.IN10:	.IFF ANS .GOTO CTSCHK
	;
	; The  System  Generation (SYSGEN)  program  functions as an inter-
	; active  dialog  in  which  the  program  asks  you  a  series  of 
	; questions.   Your   answers  establish  the  characteristics  and 
	; features  of  the monitor(s) and device handlers that the program
	; generates.  SYSGEN  prints  each  question  and  waits  for  your 
	; response.  You  can  reply  immediately with a valid response, or 
	; you can obtain a detailed explanation of the  question  by typing 
	; the  ESCAPE  key  followed  by  the  RETURN key.  You can prevent 
	; SYSGEN from printing the entire explanation  by  typing  <CTRL/O>
	; at  any  time during the explanation.  SYSGEN then stops printing 
	; the  explanation,   prints  the  question,  and  waits  for  your 
	; response.
	;
	; SYSGEN  can  generate one or more monitors from the output of one
	; dialog  session, depending  on  the responses you give.  However,
	; your  responses  during  a  session  apply  to  all  the monitors
	; generated  during  that  session.  
	.IFF VT100 .GOTO IN20
	;
	.ASK CONTIN Type RETURN to continue
.IN20:	;
	; The system generation process produces two conditional files  and  
	; three  indirect command files as output.  To produce these files,
	; the  SYSGEN  dialog  asks  you  questions about the target system
	; configuration  and  about  monitor and device support options you
	; want.  To  be able to respond effectively, you  should  read  the
	; RT-11 SYSTEM GENERATION GUIDE before proceeding.
	; 
	; The  dialog  simply  asks a question and waits for your response.
	; Although the dialog questions are  sequentially numbered, certain 
	; responses cause SYSGEN to skip some  questions which do not apply
	; for the system you are generating.
	;
	; Dialog  questions  require  one  of  several  types of responses.
	; Responses may be in the form of a character string, a number,  or
	; YES/NO  (Y/N).   SYSGEN  expects a decimal number for all numeric 
	; answers  except  for CSR and vector addresses;  in these cases it 
	; expects  an  octal  number.  A  default response, in parentheses,  
	; follows  each  question.   If  you  choose  to  use  the  default 
	; response, type only RETURN in response to the question.
	;
	; To terminate SYSGEN at any time, type <CTRL/C>.
.;;
.;; Check if this is a CTS SYSGEN
.;;
.CTSCHK:
	.TESTFILE SYSGEN.CTS
	.IF <FILERR> NE <SUCCES> .GOTO PCTSCK
	;
	.ASK [<TRUE>] CTS Do you want the CTS-300 dialog (Y)?
	.IFF <ESCAPE> .GOTO CTS5
	;
	; To  generate  a  CTS-300  system,  SYSGEN must change some of the
	; default responses, and add or remove some  of the  questions.  If 
	; you are generating a CTS-300 system, type "Y" in response to this
	; question.
	.GOTO CTSCHK
.CTS5:
	.IFT CTS .GOTO CTS10
.PCTSCK:
	.TESTFILE PROCTS.ANS
	.IF <FILERR> NE <SUCCES> .GOTO ANSFL
	;
	.ASK [<TRUE>] PROCTS Do you want the Professional CTS-300 dialog (Y)?
	.IFF <ESCAPE> .GOTO CTS10
	;
	; To generate  a  Professional  CTS-300  system, SYSGEN must change
	; some  of  the  default  responses, and add or remove some  of the  
	; questions.  If  you  are generating a CTS-300 system, type "Y" in
	; response to this question.
.CTS10:	
	.IFT PROCTS .SETT CTS
	.SETN HIGHL CTSMAX*3+1
	.IFT CTS .SETS DEVSTR DEVSTR[1:'HIGHL']
	.IFT CTS .SETN MAXDEV CTSMAX
.;;
.;; See if an answer file is to be used
.;;
.ANSFL: 
	.SETT ANS
	.IFT NOQ .GOTO AN30
	;
	.ASK ANS Do you want to use a previously created answer file (N)?
	.IFF <ESCAPE> .GOTO AN10
	;
        ; SYSGEN can use commands and responses contained in an answer file
	; to  determine  the  characteristics  of  the  monitors and device 
	; handlers  for your target system.  If you choose to use an answer 
	; file,  SYSGEN uses  the  responses in the answer file instead  of
	; printing the interactive dialog to obtain your responses.
	;
	; Answer  files  that  create the distributed monitors and handlers
	; are  included  on  the  RT-11  distribution kit. You can also use
	; answer  files  that you have created during earlier system gener-
	; ation sessions.
	.GOTO ANSFL

.AN10:	.IFF ANS .GOTO CRLOG

.AN20:
	.SETS ANSFIL "SYSGEN.ANS"
	.IFT CTS .SETS ANSFIL "SYSGEN.CTS"
	.IFT PROCTS .SETS ANSFIL "PROCTS.ANS"
	;
	.DISABLE LOWERCASE
	.ASKS [1:14.:ANSFIL] ANSFIL What answer file do you want to use ('ANSFIL')?
	.ENABLE LOWERCASE
	.IFF <ESCAPE> .GOTO AN30
	.GOSUB CR25
	.GOTO AN20
.AN30:
	.SETS FILE ANSFIL
	.SETS DEFFIL "SYSGEN"
	.SETS DEFEXT "ANS"
	.SETF NOPRO
	.GOSUB FILTST
	.SETS ANSNAM FIL
	.SETT NOPRO
	.SETS ANSFIL FILE
	.IFF FILST .GOTO ANSFL
	.TESTFILE 'ANSFIL'
	.IF <FILERR> = 1 .GOTO CRLOG
	.IF <FILERR> = 346 .GOTO FNFND
	;
	; ?SYSGEN-F-Input error 'ANSFIL'
	.EXIT 4

.FNFND:	;
	; ?SYSGEN-E-File not found 'ANSFIL' 
.AN40:
	;
	.ASK CONTIN Do you want to continue this session (N)?
	.IFF <ESCAPE> .GOTO AN50
	;
	; The answer file you entered was not on the specified  device.  If
	; you  want  to re-enter an answer file name type Y.  Type N if you
	; want to terminate this session.
	.GOTO AN40

.AN50:	.IFT CONTIN .GOTO ANSFL
	.EXIT
.;;
.;; See if an answer file is to be created.
.;;
.CRLOG:
	.SETF Q
	.IFT NOQ .GOTO CR10
	;
	.ASK Q Do you want to create an answer file (N)?
	.IFF <ESCAPE> .GOTO CR10
	;
	; Type Y to create an answer  file  that reflects the responses you
	; make  during this session.  This answer file can be used during a 
	; later SYSGEN session.
	.GOTO CRLOG
.CR10:	.IFF Q .GOTO CR60
.CR20:
	.SETS CANSF "SYSGEN.ANS"
	.IFT CTS .SETS CANSF "SYSGEN.CTS"
	.IFT PROCTS .SETS CANSF "PROCTS.ANS"
	;
	.DISABLE LOWERCASE
	.ASKS [1:14.:CANSF] CANSF What answer file do you want to create ('CANSF'):
	.ENABLE LOWERCASE
	.IFF <ESCAPE> .GOTO CR30
	.GOSUB CR25
	.GOTO CR20
.CR25:
	;
	; Type the device, filename and  filetype  of  the  answer file you
	; want to create.  Use the following format for your response:
	;
	;	ddn:filnam.typ
	;
	; The variable  ddn is  the device  name and unit number where  the
	; answer  file  is  to  reside, and  filnam.typ is the filename and
	; filetype of the answer file you are creating.
	.RETURN

.CR30:	.SETS FILE CANSF
	.SETS DEFFIL "SYSGEN"
	.SETS DEFEXT "ANS"
	.GOSUB FILTST
	.SETS QNAM FIL
	.SETS CANSF FILE
	.IFF FILST .GOTO CRLOG
	.TESTFILE 'CANSF'
	.IF <FILERR> NE 1 .GOTO CR60
	;
	; ?SYSGEN-W-File already exists 'CANSF' 
.CR40:
	;
	.ASK Q1 Do you want to create a new 'CANSF' file (N)?
	.IFF <ESCAPE> .GOTO CR50
	;
	; A file already exists with the  same  name as the answer file you
	; have  chosen  to  create.  If you still want to use this name for
	; your  output  answer  file, the  data  contained  in  the already
	; existing file of the same name will be lost.
	.GOTO CR40
.CR50:	
	.IFF Q1 .GOTO CR20
.CR60:
.;;
.;; Pick names for work files
.;;
.PI5:
	;
	;	...checking for protected output files.  
	;
	.SETS SYCND "SYSGEN.CND"
	.SETS DEVTBL "SYSGEN.TBL"
	.SETS MONBLD "SYSGEN.MON"
	.SETS DEVBLD "SYSGEN.DEV"
	.SETS SYSBLD "SYSGEN.BLD"
	.IFF ANS .GOTO PI6
	.SETS SYCND ANSNAM+".CND"
	.SETS DEVTBL ANSNAM+".TBL"
	.SETS MONBLD ANSNAM+".MON"
	.SETS DEVBLD ANSNAM+".DEV"
	.SETS SYSBLD ANSNAM+".BLD"
.PI6:	.IFF Q .GOTO PI7
	.SETS SYCND QNAM+".CND"
	.SETS DEVTBL QNAM+".TBL"
	.SETS MONBLD QNAM+".MON"
	.SETS DEVBLD QNAM+".DEV"
	.SETS SYSBLD QNAM+".BLD"
.PI7:	.SETS SYFIL SYCND
	.SETS DEVFIL DEVTBL

	.SETF NOPRO
	.SETS FILE SYCND
	.GOSUB FILTST
	.IFF FILST .GOTO PI5

	.SETS FILE DEVTBL
	.GOSUB FILTST
	.IFF FILST .GOTO PI5

.;; Check for output files protected
	.SETS FILE MONBLD
	.GOSUB FILTST
	.SETS FILE DEVBLD
	.GOSUB FILTST
	.SETS FILE SYSBLD
	.GOSUB FILTST
	.SETT NOPRO

	.SETS FILE "('SYCND','DEVTBL')"
	.GOSUB FLCHK
	.SETS FILE "('MONBLD','DEVBLD','SYSBLD')"
	.GOSUB FLCHK
.PI99:
	.IFT ANS .GOTO READA
	.GOTO MTYPE
.FILTST:
.;;Test a filename for validity.
.;;Input: FILE-filename   DEFFIL-default file DEFEXT-default extension
.;;	  NOPRO = <FALSE> - dont check for protect file
.;;Output:  FILST = <TRUE> -> Good   FILST = <FALSE> -> Bad   
.;;	    FILTYP = Filename without device specification
.;; It also checks to see if a protected file already exists with the
.;; given name.
.;;
	.SETF FILST
	.TEST FILE ":" 
	.IF <STRLEN> EQ 0 .GOTO NODEV
	.PARSE FILE ":." DEV FIL TYP
	.GOTO FL10
.NODEV:	.SETS DEV ""
	.PARSE FILE "." FIL TYP
.FL10:
	.TEST DEV
	.IF <STRLEN> GT 3 .GOTO FLBAD
	.IFF <ALPHAN> .GOTO FLBAD
	.TEST FIL
	.IF <STRLEN> EQ 0 .SETS FIL DEFFIL
	.IF <STRLEN> GT 6 .GOTO FLBAD
	.IFF <ALPHAN> .GOTO FLBAD
	.TEST TYP
	.IF <STRLEN> EQ 0 .SETS TYP DEFEXT
	.IF <STRLEN> GT 3 .GOTO FLBAD
	.IFF <ALPHAN> .GOTO FLBAD
	.GOTO FLGOOD
.FLBAD:	
	;
	; ?SYSGEN-E-Invalid filename: 'FILE'
	.RETURN
.FLGOOD:
	.IF DEV EQ "" .OR .IF DEV EQ "SY" .OR .IF DEV EQ "DK" .GOTO FL20
	LOAD 'DEV'
	.IF <EXSTAT> EQ <SUCCES> .GOTO FL20
	.GOTO FLBAD
.FL20:
	.SETT FILST
	.SETS FILTYP FIL+"."+TYP
	.SETS FILE FILTYP
	.IF DEV NE "" .SETS FILE DEV+":"+FILE
.FLCHK:
	.IFF NOPRO .RETURN
	DIR/PRO/FA/OU:SYSGEN.TMP 'FILE'
	.IF <EXSTAT> EQ <SUCCES> .GOTO FLOK
	;
	; ?SYSGEN-F-Input error 'FILE'
	.EXIT 4
.FLOK:
	.OPENR SYSGEN.TMP
	.READ LINE
	.READ FILES
	.CLOSE
	.IF FILES EQ "" .RETURN
	;
	;?SYSGEN-F-Protected file already exists 'FILES'
	.EXIT 4
	
.;;
.;; Determine what monitor(s) are to be generated
.;;
.MTYPE:
	.SETF BL
	.SETF SJ
	.SETF FB
	.SETF XM
	.SETF FBXM
	.SETF XMONLY
	;
	;
	; 'STARS'
	; 		MONITOR TYPE
	; 'STARS'
.Q1:
	.IFT PROCTS .GOTO Q2
	;
	.ASK [<TRUE>] SJ 1.   Do you want the single-job (SJ) monitor (Y)?
	.IFF <ESCAPE> .GOTO Q2
	;
	; SINGLE-JOB MONITOR:
	; The single-job (SJ) monitor provides an environment  suitable for
	; developing  simple FORTRAN or BASIC applications.  The SJ monitor
	; includes  many  of the same features as the foreground/background
	; (FB) monitor--it supports all hardware devices (except the memory
	; management  unit),  all  programmed  requests  (except  .MRKT and 
	; .CMKT), and all the utility programs. It offers the most features 
	; in the smallest size.  You can add features during SYSGEN, but at 
	; the cost of increased monitor size.
	.GOTO Q1

.Q2:
	.SETS TEMPS "Y"
	.SETS TEMP "TRUE"
	.IFT PROCTS .SETS TEMPS "N"
	.IFT PROCTS .SETS TEMP "FALSE"
	;
	.ASK [<'TEMP'>] FB 2.   Do you want the foreground/background (FB) monitor ('TEMPS')?
	.IFF <ESCAPE> .GOTO Q3
	;
	; FOREGROUND/BACKGROUND MONITOR:
	; The foreground/background (FB) monitor  offers an extended set of
	; features that aid real-time or data acquisition applications.  In
	; addition to the foreground job capability, this  monitor supports
	; serialized  asynchronous  I/O  and additional programmed requests
	; (including .MRKT and .CMKT).
	.GOTO Q2

.Q3:
	.SETS TEMP "FALSE"
	.SETS TEMPS "N"
	.IFT CTS .SETS TEMP "TRUE"
	.IFT CTS .SETS TEMPS "Y"
	;
	.ASK [<'TEMP'>] XM 3.   Do you want the extended memory (XM) monitor ('TEMPS')?
	.IFF <ESCAPE> .GOTO MO20
	;
	; EXTENDED MEMORY MONITOR:
	; The extended memory (XM) monitor, which supports up to 124K words
	; of  memory, is  a  version  of  the FB monitor.  It requires KT11
	; hardware  (the memory management unit) and  the extended instruc-
	; tion  set (EIS).  The  XM  monitor supports additional programmed
	; requests  that allow you to extend a program''s logical addressing
	; space.  However, the XM monitor is larger than the FB monitor and
	; requires that the user service routine (USR) be resident.
	.GOTO Q3

.MO20:	.IFT FB .OR .IFT XM .SETT FBXM
	.IFF BL .IFF SJ .IFF FB .IFT XM .SETT XMONLY
	.IFT SJ .OR .IFT FBXM .OR .IFT BL .GOTO MONOP
	;
	; ?SYSGEN-E-No monitor requested
	;
	.ASK [<TRUE>] CONTIN Do you want to return to the monitor dialog (Y)?
	.IFF <ESCAPE> .GOTO MO30
	;
	; You must respond  yes  to  at least one of questions 1 through 3. 
	; Each  SYSGEN  run must build at  least one monitor.   You  cannot 
	; build device support without building a monitor.  Type "Y" if you
	; want  to  be  re-prompted  for  the monitor type.  If you want to
	; terminate the SYSGEN session type N.
	.GOTO MO30
.MO30:	.IFT CONTIN .GOTO Q1
	.EXIT 
.;;
.;; Ask the monitor options
.;;
.MONOP:
	;
	;
	; 'STARS'
	; 		MONITOR OPTIONS
	; 'STARS'
	.IFF SJ .GOTO Q5

.Q4:
	.SETT TIME$R
	.IFT CTS .GOTO C5
	;
	.ASK TIME$R 4.   Do you want timer support in the SJ monitor (N)?
	.IFF <ESCAPE> .GOTO C5
	;
	; SJ TIMER SUPPORT OPTION:
	; The SJ monitor normally does not include timer support.  You  can
	; include  this  support, which  enables you to use the .MRKT (mark
	; time) and .CMKT (cancel mark time) programmed requests.
	.GOTO Q4
.C5:	.IFT CHANGE .GOTO MP10

.Q5:
	.SETS TEMP "FALSE"
	.SETS TEMPS "N"
	.IFT CTS .SETS TEMP "TRUE"
	.IFT CTS .SETS TEMPS "Y"
	;
	.ASK [<'TEMP'>] TIM$IT 5.   Do you want device time-out support ('TEMPS')?
	.IFF <ESCAPE> .GOTO MP10
	;
	; DEVICE TIME-OUT SUPPORT OPTION:
	; The device time-out option permits device handlers to issue .MRKT
	; (mark time)  programmed  requests.   DECNET support requires this
	; option.
	.GOTO Q5

.MP10:	.IFT TIM$IT .AND .IFT SJ .SETT TIME$R
	.IFT CHANGE .GOTO CH20
	.IFF SJ .GOTO Q7

.Q6:
	.SETT RDF$L
	.IFT CTS .GOTO C7
	;
	.ASK [<TRUE>] RDF$L 6.   Do you want an error message on system I/O errors (Y)?
	.IFF <ESCAPE> .GOTO C7
	;
	; ERROR MESSAGE ON SYSTEM I/O ERRORS OPTION:
	; The SJ monitor normally halts if a fatal system I/O error occurs.
	; You  can  replace this halt with a system error message.  DIGITAL
	; highly  recommends  this  option  if  the  system will be used by
	; anyone but the most experienced individuals.
	.GOTO Q6
.C7:	.IFT CHANGE .GOTO CH20
.Q7:
	.IFF FBXM .GOTO Q10
	;
	.ASK SYT$K 7.   Do you want system job support (N)?
	.IFF <ESCAPE> .GOTO C8
	;
	; SYSTEM JOB OPTION:
	; The system  job  option  allows you to run up to eight simultane-
	; ously  active  jobs.  The error logger, the SPOOL program, VTCOM, 
	; and  the  QUEUE  program  can be either foreground jobs or system
	; jobs.  If you want to run more than one simultaneously, or if you
	; want to run  any one along with a foreground job, you need system
	; job support.
	.GOTO Q7
.C8:	.IFT CHANGE .GOTO CH20
.Q8:
	.SETT SPC$PS
	.IFT CTS .GOTO C9
	;
	.ASK SPC$PS 8.   Do you want to use the .SPCPS request (N)?
	.IFF <ESCAPE> .GOTO C9
	;
	; SAVE/SET MAIN-LINE PC AND PS OPTION:
	; The  save/set  main-line  PC  and  PS  option  is a conditionally
	; assembled  programmed  request  for  the  FB and XM monitors. The
	; .SPCPS  request  changes the flow of control of main-line code by
	; saving the main-line code PC and PS and changing the main-line PC
	; to  a  new  value.  This  request  may  be  useful  in multi-user
	; applications to control switching among users.
	.GOTO Q8
.C9:	.IFT CHANGE .GOTO CH20
.Q9:
	.IFF FBXM .GOTO C10
	;
	.ASK SCCA$G 9.   Do you want global SCCA support (N)?
	.IFF <ESCAPE> .GOTO C10
	;
	; GLOBAL SCCA SUPPORT OPTION:
	; The  SCCA  programmed  request  inhibits  control/c''s  until the 
	; currently  running program exits.  Global SCCA support allows you
	; to issue a programmed request that will inhibit control/c''s even
	; after a program  exits.  Control/c''s  will remain inhibited until
	; a  global  SCCA programmed request is issued to explicitly turn it
	; off.
	.GOTO Q9
.C10:	.IFT CHANGE .GOTO CH20
	.SETT MTT$Y
	.IFT PROCTS .GOTO MP20
.Q10:	
	;
	.IFT CTS .ASK [<TRUE>] MTT$Y 10.  Do you want to use TSD with this monitor (Y)?
	.IFF CTS .ASK MTT$Y 10.  Do you want multiterminal support (N)?
	.IFF <ESCAPE> .GOTO MP20
	.SETS TSD1 "  multiterminal   option"
	.IFT CTS .SETS TSD1 "TSD multiterminal option"
	.SETS TSD ""
	.IFT CTS .SETS TSD "TSD "
	;
	; 'TSD'MULTITERMINAL SUPPORT OPTION:
	; The 'TSD1' lets  you  use  special  programmed
	; requests  to  do  I/O  to more than one terminal.  RT-11 normally
	; supports only one terminal  interfaced through the console (DL11)
	; which is  shared by both background and foreground jobs. You  can
	; select  multiterminal  support  for up to 16 terminals interfaced
	; through  a  choice  of  DL11  and  DZ11  interfaces.   Subsequent
	; questions will establish the number and type of interfaces.  Note
	; that  if  you  choose  multiterminal  support  your system cannot
	; support VT11 or VS60 graphics.
	.GOTO Q10

.MP20:	.IFF MTT$Y .GOTO Q13

.Q11:
	.SETT MAT$S
	.IFT CTS .GOTO C12
	;
	.ASK [<TRUE>] MAT$S 11.  Do you want asynchronous terminal status (Y)?
	.IFF <ESCAPE> .GOTO C12
	;
	; ASYNCHRONOUS TERMINAL STATUS OPTION:
	; The  asynchronous  terminal status option provides a program with
	; the  updated  status  of  a  terminal  and modem.  When a program
	; attaches  a  terminal,  the program can supply a status word that
	; the  monitor  updates  as  changes  occur  in the terminal status 
	; (double CTRL/C,  input  available, output  buffer  empty, carrier 
	; present).  This support is required for MU BASIC applications.
	.GOTO Q11
.C12:	.IFT CHANGE .GOTO CH20
.Q12:
	;
	.ASK [<TRUE>] MTI$M 12.  Do you want multiterminal time-out support (Y)?
	.IFF <ESCAPE> .GOTO MP30
	;
	; MULTITERMINAL TIME-OUT OPTION:
	; Multiterminal  time-out support  causes  the monitor to reset (at
	; regular  intervals)  any  terminal  that  may have gone off-line.
	; This  action  helps  to minimize the impact of static and similar
	; problems.  DIGITAL  recommends  selecting  this  option  if  your
	; application requires maximum terminal availability.
	.GOTO Q12

.MP30:	.IFF MTI$M .GOTO MP30A
	.IFT TIM$IT .GOTO MP30A
	;
	; ?SYSGEN-I-Device time-out support set on
	.SETT TIM$IT
.MP30A:	.IFT CHANGE .GOTO CH20

.Q13:
	;
	.ASKN [10.:134.:40.] TTYOUT 13.  Enter the size of the output buffers (40):
	.SETD TTYOUT
	.IFF <ESCAPE> .GOTO C14
	;
	; OUTPUT RING BUFFER SIZE OPTION:
	; The RT-11 terminal service requires a set of output ring  buffers
	; for each supported terminal.  The  output ring is a buffer in the
	; monitor that  holds characters until the terminal can print them.
	; (A program  can  send characters faster than a terminal can print
	; them.)  
	.GOTO Q13
.C14:	.IFT CHANGE .GOTO CH20
.Q14:
	;
	.ASKN [74.:254.:134.] TTYIN 14.  Enter the size of the input buffers (134):
	.SETD TTYIN
	.IFF <ESCAPE> .GOTO C15
	;
	; INPUT RING BUFFER SIZE OPTION:
	; The  RT-11  terminal service requires a set of input ring buffers
	; for  each  terminal supported.  The input ring is a buffer in the
	; monitor  that  holds  the  characters that you type at a terminal
	; until a program  requests them.  You may want to change the input 
	; ring size, in particular, since the size you need  depends on the 
	; terminal''s width and the amount of type-ahead you expect.
	.GOTO Q14
.C15:	.IFT CHANGE .GOTO CH20
.Q15:
	.IFF XM .GOTO C16
	;
	.ASK [<TRUE>] XM$FET 15.  Do you want to use the .FETCH request under XM (Y)?
	.IFF <ESCAPE> .GOTO C16
	;
	; .FETCH REQUEST OPTION:
	; If  you  choose .FETCH support under XM, then device handlers can
	; be  fetched  by  user  background  programs.  Also, pre-Version 5
	; programs  which  do  not  use  the form of the .PROTECT directive
	; which  includes automatic vector setup must be modified to do so.
	; If  you  do  not select this option, all in-line service routines
	; would, as in Version 4, have to remain clear of the memory mapped
	; by kernel APR 1 and handlers must be loaded before use.  .FETCH
	; adds approximately 400. words to the resident monitor.
	.GOTO Q15
.C16:	.IFT CHANGE .GOTO CH20
.Q16:
	;
	.ASK ROL$OV 16.  Do you want end of month and year date rollover (N)?
	.IFF <ESCAPE> .GOTO C20
	;
	; MONTH ROLLOVER OPTION:
	; When  you  run a system continuously, over a long period of time,
	; you  normally have to reset the date and time at the beginning of
	; each month.  You can select a feature that automatically sets the
	; correct date and time. However, this option greatly increases the
	; size of the monitor.
	.GOTO Q16
.C20:	.IFT CHANGE .GOTO CH20
.Q20:
	;
	.ASK [<TRUE>] U$CL 20.  Do you want the user command linkage (Y)?
	.IFF <ESCAPE> .GOTO C21
	;
	;USER COMMAND LINKAGE OPTION
	;The  user  command  linkage allows you to define your own commands
	;which  can  be  issued  in  a  format  similar to the standard DCL
	;commands.  
	.GOTO Q20
.C21:	.IFT CHANGE .GOTO CH20
.Q21:	
	;
	.ASK [<FALSE>] HSR$B 21.  Do you want high speed ring buffer support (N)?
	.IFF <ESCAPE> .GOTO C22
	;
	; HIGH SPEED RING BUFFER OPTION
	; When  the  high  speed  ring  buffer  is  present,  all character 
	; processing and interpretation is performed at  fork  level.   The 
	; advantage of having the high speed ring buffer is that it  allows
	; short bursts of characters coming in at a very high rate. This is
	; useful  for  systems  with  VT100  or other terminals that report
	; their  status  by  sending  a  burst  of  information to the host
	; computer.  Use  of  the  high  speed  ring  buffer  is especially 
	; recommended with a PDT.
	.GOTO Q21
.C22:	.IFT CHANGE .GOTO CH20
.;;
.;; Ask which KMON commands are needed
.;;
.Q22:
	;
	.ASK [<TRUE>] ANS 22.  Do you want all the keyboard monitor commands (Y)?
	.IFF <ESCAPE> .GOTO MP40
	;
	; KEYBOARD MONITOR COMMANDS OPTION:
	; The keyboard monitor commands option lets you choose the keyboard
	; monitor  commands  your generated monitor will support.  You will
	; probably  find  all  of  the  commands  useful.  However, you can
	; reduce  KMON  size  and assembly time if you select support for a
	; subset  of  the  available  commands.  You have a choice of three
	; subsets  (or  any  combination  of  subsets).  The  three command
	; subsets  you  can  choose  are: the UTILITY PROGRAM COMMANDS, the
	; LANGUAGE  COMMANDS,  and  the  MINIMAL  COMMANDS.  If you  do not 
	; choose  the  complete  set of commands or any of the subsets, you 
	; will be able to use only the RUN command.
	.GOTO Q22

.MP40:	.IFF ANS .GOTO MP50
	.SETT U$TIL
	.SETT L$ANG
	.SETT M$INI
	.GOTO C26

.MP50:
	.SETS SYM "U$TIL 23."
	.SETS OPT "UTILITY"
.MP60:
	;
	.ASK [<TRUE>] 'SYM'	Do you want the 'OPT' subset (Y)?
	.IFF <ESCAPE> .GOTO MP100
	;
	; The following commands are included when the 'OPT' commands
	; are chosen:
	;
	.IF OPT <> "UTILITY" .GOTO MP70
	; BACKUP		BOOT		COPY		CREATE	
	; DELETE		DIFFERENCES	DIRECTORY	DUMP
	; EDIT		FORMAT		INITIALIZE	PRINT
	; PROTECT	RENAME		SHOW		SQUEEZE
	; TYPE		UNPROTECT
	.GOTO MP90

.MP70:	.IF OPT <> "LANGUAGE" .GOTO MP80
	; COMPILE	DIBOL		EXECUTE	
	; FORTRAN	LIBRARY		LINK		MACRO
	.GOTO MP90

.MP80:	; ABORT		ASSIGN		B		CLOSE
	; D		DATE		DEASSIGN	DISMOUNT
	; E		FRUN		GET		GT
	; HELP		INSTALL		LOAD		MOUNT
	; R		REENTER		REMOVE		RESET
	; RESUME		RUN		SAVE		SET
	; SRUN		START		SUSPEND		TIME
	; UNLOAD
.MP90:	;
	; Type  Y  if  you  want  support  for the 'OPT' subset of the
	; keyboard monitor commands.  Type N if you do  not want the subset
	; or  if  you  wish  to  specify individual commands by defining
	; system conditionals later during this SYSGEN session.
	.GOTO MP60

.MP100:	.IF OPT <> "UTILITY" .GOTO MP110
	.SETS SYM "L$ANG 24."
	.SETS OPT "LANGUAGE"
	.GOTO MP60

.MP110:	.IF OPT <> "LANGUAGE" .GOTO C26
	.SETS SYM "M$INI 25."
	.SETS OPT "MINIMAL"
	.GOTO MP60

.C26:	.IFT CHANGE .GOTO CH20
.;;
.;; Continue monitor options
.;;
.Q26:
	;
	.ASK CLK 26.  Do you want the optional 50 Hz clock support (N)?
	.IFF <ESCAPE> .GOTO MP120
	;
	; 50 HZ CLOCK OPTION:
	; A line clock generates periodic interrupts to allow the system to
	; keep track of the time. The number of ticks per second depends on
	; the  power line frequency, 60 Hz or 50 Hz.  RT-11 assumes a 60 Hz
	; line frequency, but you can select support for a 50 Hz clock. The
	; 50 Hz  frequency has specialized uses and is the common frequency
	; in Europe.
	.GOTO Q26

.MP120:	.SETN CLOCK 60.
	.IFT CLK .SETN CLOCK 50.
	.SETD CLOCK
	.IFT CHANGE .GOTO CH20
.Q27:
	.SETF KW11$P
	.IFT CTS .GOTO C30
	;
	.ASK KW11$P 27.  Do you want to use the KW11-P clock as the system clock (N)?
	.IFF <ESCAPE> .GOTO C30
	;
	; PROGRAMMABLE CLOCK AS SYSTEM CLOCK OPTION:
	; RT-11 normally  uses  a line clock for the system clock.  You can
	; substitute the KW11-P programmable clock as the system clock, but
	; the  KW11-P  will  not  then  be  available for program use.  The
	; programmable  clock  normally allows you to program interrupts at
	; preset intervals.
	.GOTO Q27
.C30:	.IFT CHANGE .GOTO CH20
.Q30:
	;
	.ASK [<TRUE>] STAR$T 30.  Do you want the startup indirect file (Y)?
	.IFF <ESCAPE> .GOTO C31
	;
	; STARTUP INDIRECT COMMAND FILE OPTION:
	; This  option  causes the bootstrap to execute an indirect command
	; file  (with  the name STARTx.COM, where x identifies the monitor)
	; when  starting  the  system.  An  indirect  command file contains
	; monitor  commands  that  the  monitor  processes (in the order in
	; which they appear) when the file is executed.  A startup indirect
	; command  file  is  particularly  useful  for  setting  up initial
	; conditions (for example, assigning the default device to the data
	; device, installing  a  device  into  the  system  tables when the
	; device  was  not  originally  built into the system, or running a
	; specific program).
	.GOTO Q30
.C31:	.IFT CHANGE .GOTO CH20
.Q31:
	.SETF FPU$11
	.IFT CTS .GOTO MP130
	;
	.ASK FPU$11 31.  Do you want floating point support (N)?
	.IFF <ESCAPE> .GOTO MP130
	;
	; FLOATING POINT OPTION:
	; If  your  configuration includes floating point hardware and your
	; application requires this feature, you should enable this option.
	; Floating  point hardware is available for many PDP-11 and Profes-
	; sional  300  series  processors.   This  is especially useful for
	; FORTRAN and BASIC users whose applications perform data manipula-
	; tions.
	.GOTO Q31

.MP130:	.IFT CHANGE .GOTO CH20	
.Q32:
	;
	.ASK MPT$Y 32.  Do you want memory parity support (N)?
	.IFF <ESCAPE> .GOTO C33
	;
	; MEMORY PARITY SUPPORT OPTION:
	; If your configuration includes memory parity hardware, you should
	; select  this  option.  Memory  parity  hardware checks for memory
	; errors  and  this  option enables RT-11 support for the hardware.
	; RT-11 issues an error message and supplies the location of access
	; when a memory error occurs.  If you have this hardware but do not
	; enable  this  support, the system halts when memory errors occur.
	; If you select error logging as well as memory parity support, the
	; error logger logs parity errors as well as device errors.
	.GOTO Q32
.C33:	.IFT CHANGE .GOTO CH20
.Q33:
	;
	.ASK [<FALSE>] PWF$L 33.  Do you want power failure messages (N)?
	.IFF <ESCAPE> .GOTO C34
	;
	; POWER FAILURE MESSAGE OPTION:
	; The  monitor  normally  halts  on power recovery startup  after a
	; power failure.  You can elect to have the monitor print a message
	; explaining that power failure caused the halt.  However, you must
	; not select this option if you have semiconductor memory, which is
	; volatile.
	.GOTO Q33
.C34:	.IFT CHANGE .GOTO CH20
.Q34:
	;
	.ASK BATC$H 34.  Do you want BATCH support (N)?
	.IFF <ESCAPE> .GOTO C35
	;
	; BATCH SUPPORT OPTION:
	; You can select support for the BATCH job control  language, which
	; allows  RT-11  to  operate  unattended.  Once you prepare a BATCH
	; stream, you  can  leave  it for an operator to start and run, and
	; the  BATCH  stream  will  execute  programs  or  monitor commands
	; without  your intervention.  Indirect command file support, which
	; offers  similar  capabilities, is  separately  available  in  all
	; monitors.  You  need  not select BATCH support to obtain indirect
	; command file support.
	.GOTO Q34
.C35:	.IFT CHANGE .GOTO CH20
.Q35:
	;
	.ASK ERL$G 35.  Do you want error logging (N)?
	.IFF <ESCAPE> .GOTO MP140
	;
	; ERROR LOGGING OPTION:
	; The  error  logging  option creates the error logging (EL) system
	; job,  and  incorporates  error  logging  support  in  the  device
	; handlers.   Error  logging  reports  device,  memory  parity  (if
	; selected),  and  memory  cache  errors.  When  error  logging  is
	; enabled, most device handlers call EL on each successful transfer
	; and  on  each  error. The  EL  job retrieves information from the
	; handlers that is later available to you in summary report format.
	.GOTO Q35

.MP140:	.IFF ERL$G .GOTO C37

.Q36:
	;
	.ASKN [1.:34.:10.] ERL$U 36.  How many device units does error log job support (10)?
	.SETD ERL$U
	.IFF <ESCAPE> .GOTO C37
	;
	; NUMBER OF UNITS SUPPORTED BY ERROR LOGGING OPTION:
	; The  error  logger  can  handle up to 34 individual device units.
	; You can conserve space by reducing the number of units the logger
	; can  handle  to  the  specific  number  of supported units in the
	; target configuration.
	.GOTO Q36
.C37:	.IFT CHANGE .GOTO CH20
	.GOSUB USERPT
.;;
.;; Ask which devices are needed.
.;;
.DEVST:
	;
	;
	; 'STARS'
	;		DEVICE OPTIONS
	; 'STARS'
	.SETS TXT "device name you want support for"
.Z28:
	;
	; Type <ESCAPE><RETURN> for help.
	; Type ?<RETURN> to list all devices.
	; Type .<RETURN> when device selection is complete.
	;
.Z29:
	;
	.DISABLE LOWERCASE
	.ASKS [0:2] DNM Enter the 'TXT' [dd]:
	.ENABLE LOWERCASE
	.IFF <ESCAPE> .GOTO DE10
	;
	; The device options let you select the peripheral devices that the
	; generated  system  will  support.  By  selecting  support  for  a
	; specific  device, you  make  the  device  known  to the monitor''s
	; device  tables,  and  SYSGEN  generates  a  device  handler named
	; xx.SYG, (where xx  is  the  physical device name) for the device.
	; If you do not select a  specific  device  at  this time, you will
	; have  to create the device handler separately and use the monitor 
	; INSTALL command before you can access the device.
	;
	; The  following  is  a  list  of the valid RT-11 devices and their
	; associated  device  names.  SYSGEN  will  display the device name
	; list  each  time  you  type  a  question  mark  (?) followed by a
	; carriage  return  in  response  to  the device name question.  An
	; asterisk (*) will precede the device name if selected. Type a dot
	; when you have entered all the device names you want support for.
	;
	.IFT VT100 .ASK CONTIN Type RETURN to continue
	.GOSUB LIST
	.GOTO Z29
.;;
.;; Check device selected
.;;
.DE10:	.IF DNM = "?" .GOSUB LIST
	.IF DNM = "?" .GOTO Z29
	.IF DNM = "." .GOTO CU
	.IF DNM = ""  .GOTO Z29
	.TEST DEVSTR " "+DNM+" "
	.IF <STRLEN> NE 0 .GOTO DE20
	;
	; ?SYSGEN-E-Invalid device 'DNM':
	.GOTO Z29

.DE20:	
	.IFT BL .OR .IFT SJ .OR .IFT FB .GOTO DE30
	.IF DNM NE "PD" .GOTO DE30
	;
	; ?SYSGEN-E-Invalid device for the monitor(s) selected 'DNM':
	.GOTO Z29
.DE30:	.SETT 'DNM'
	.SETS TXT "next device name"
	.IFT CHANGE .SETS TXT "next device name to add/modify"
	.IF DNM = "DX" .OR .IF DNM = "DY" .GOSUB TOCON
	.IF DNM = "DD" .GOSUB TOCON
	.IF DNM = "RF" .GOSUB RFP
	.IF DNM = "DU" .GOSUB DUP
	.IF DNM = "DS" .GOSUB RJS
	.IF DNM = "DL" .GOSUB DLUN
	.IF DNM = "DP" .GOSUB RP0
	.IF DNM = "MT" .GOSUB MTF
	.IF DNM = "MM" .GOSUB MTF
	.IF DNM = "MS" .GOSUB MTF
	.IF DNM = "MU" .GOSUB MTF
	.IF DNM = "LP" .GOSUB LPC
	.IF DNM = "LS" .GOSUB LSC
	.IF DNM	= "XL" .GOSUB DXL
	.IF DNM = "SP" .GOSUB DSP
	.IFF XM .AND .IF DNM = "NC" .GOTO XMONLY
	.IFF XM .AND .IF DNM = "NQ" .GOTO XMONLY .;Must be before .GOSUB DNQ line
	.IF DNM = "NQ" .GOSUB DNQ
	.GOTO Z29

.XMONLY: ;
	; ?SYSGEN-E-Ethernet handler support available for XM only
	.SETF 'DNM'
	.GOTO Z29
.;;
.;; List the available devices
.;;
.LIST:
	;
	;
	.SETS DEF "* "
	.SETN CNT 1
.LISTER:
	.SETS DCOM2 ""
	.SETS AST1 "  "
	.SETS AST2 "  "
	.SETS DCOM1 DCM'CNT'
	.SETS DEV1 DCM'CNT'[1:2]
	.SETS DEV DEV1
	.INC CNT
	.IF CNT GT MAXDEV .GOTO L21
	.SETS DCOM2 DCM'CNT'
	.SETS DEV2 DCM'CNT'[1:2]
	.SETS DEV DEV2
	.IFT 'DEV2' .SETS AST2 DEF
.L21:
	.IFT 'DEV1' .SETS AST1 DEF
	;'AST1''DCOM1'   'AST2''DCOM2'
	.INC CNT
	.IF CNT LE MAXDEV .GOTO LISTER
	;
	.SETN ULDVNO 0
	.SETS AST1 DEF
	.SETS AST2 DEF
	.SETS COM "  User supplied device           "
.L30:
	.INC ULDVNO
	.IFNDF UD'ULDVNO' .RETURN
	.IF UD'ULDVNO' EQ "" .OR .IF UD'ULDVNO' EQ "?" .GOTO L30
	.SETS DCOM1 UD'ULDVNO'+COM
.L35:
	.INC ULDVNO
	.SETS DCOM2 ""
	.IFNDF UD'ULDVNO' .SETS AST2 ""
	.IFNDF UD'ULDVNO' .GOTO L40
	.IF UD'ULDVNO' EQ "" .OR .IF UD'ULDVNO' EQ "?" .GOTO L35
	.SETS DCOM2 UD'ULDVNO'+COM
.L40:	;'AST1''DCOM1''AST2''DCOM2'
	.GOTO L30
.;; 
.;; RX01, RX02, TU58
.;;
.TOCON:
	.IF DNM = "DX" .SETS DEV "RX11"
	.IF DNM = "DY" .SETS DEV "RX02"
	.IF DNM = "DD" .SETS DEV "Dectape II"
	;
	.ASK 'DNM'T$O 100.  Do you want support for a second 'DEV' controller (N)?
	.IFF <ESCAPE> .AND .IF DNM = "DY" .GOTO RX30
	.IFF <ESCAPE> .GOTO RX40
	.IF DNM <> "DX" .GOTO RX10
	;
	; The RX01 single-density flexible diskette subsystem supports only
	; two  drives  for  each  controller.  If your system contains four 
	; diskette drives, a second controller governs the third and fourth 
	; units, and you must select RT-11 support for it.
	.GOTO TOCON
.RX10:
	.IF DNM <> "DY" .GOTO RX20
	;
	; The  RX02  double-density  diskette  subsystem  supports only two
	; drives for each controller.  If your system contains four drives,
	; a  second  controller governs the third and fourth units, and you 
	; must select RT-11 support for it.
	.GOTO TOCON
.RX20:
	;
	; The TU58 DECtape II cartridge subsystem supports only two  drives 
	; for  each  controller.  If  your  system  contains four drives, a 
	; second  controller  governs  the  third and fourth units, and you 
	; must select RT-11 support for it.  
	.GOTO TOCON

.RX30:
	;
	.ASK DY$DD 101.  Do you want RX02 double density only support (N)?
	.IFF <ESCAPE> .GOTO RX40
	;
	; The  RX02  diskette supports both single and double  densities by 
	; default.  If  you  select  double-density  only  support, you can 
	; slightly  improve  the  performance  and  reduce  the size of the 
	; device handler.
	.GOTO RX30

.RX40:
	.IF DNM <> "DD" .SETN DEFC 177170
	.IF DNM = "DD" .SETN DEFC 176500
	.SETS CN "R"
	.SETS VN "EC"
	.SETS NUM "first "
	.IF DNM <> "DD" .SETN DEFV 264
	.IF DNM = "DD" .SETN DEFV 300
.RX50:
	;
	.ASKN [160000:177570:'DEFC'] 'DNM'$CS'CN' 102.  What is the CSR  address for the 'NUM''DEV' ('DEFC')?
	.IFF <ESCAPE> .GOTO RX60
	;
	; The valid range for the CSR address is from 160000 to 177570.
	.GOTO RX50

.RX60:  
	;
	.IF 'DNM'$CS'CN' = 'DNM'$CS'CN'/2*2 .GOTO RX65
	; ?SYSGEN-W-Address not even
	.GOTO RX50
.RX65:
	;
	.ASKN [100:474:'DEFV'] 'DNM'$V'VN' 103.  What is the vector address for the 'NUM''DEV' ('DEFV')?
	.IFF <ESCAPE> .GOTO RX70
	;
	; The valid range for the vector address is from 100 to 474.
	.GOTO RX65

.RX70:
	.IF 'DNM'$V'VN' = 'DNM'$V'VN'/2*2 .GOTO RX75
	; ?SYSGEN-W-Address not even
	.GOTO RX65

.RX75:
	.IFF 'DNM'T$O .RETURN 
	.IF CN = "2" .RETURN
	.IF 'DNM'$CS'CN' <> DEFC .SETN DEFC 'DNM'$CS'CN'
	.IF 'DNM'$V'VN' <> DEFV .SETN DEFV 'DNM'$V'VN'
	.SETS CN "2"
	.SETS VN "C2"
	.SETS NUM "second "
	.IF DNM = "DX" .SETN DEFC DEFC+4
	.IF DNM = "DY" .SETN DEFC DEFC-20
	.IF DNM <> "DD" .SETN DEFV DEFV+4
	.IF DNM = "DD" .SETN DEFV DEFV+10
	.IF DNM = "DD" .SETN DEFC DEFC+10
	.IF DEFC LE 177570 .IF DEFC GE 160000 .GOTO RX75A
	;
	; ?SYSGEN-F-Next default CSR address out of range ('DEFC')
	; ...Restarting query sequence for this device 
	;
	.GOTO TOCON

.RX75A: .IF DEFV LE 474 .IF DEFV GE 100 .GOTO RX50
	;
	; ?SYSGEN-F-Next default vector address out of range ('DEFV')
	; ...Restarting query sequence for this device 
	;
	.GOTO TOCON

.;;
.;; RF11, RJS03/4, RL01/2, RP02/3
.;;
.RFP:
	;
	.ASKN [1.:8.:1.] $RFNUM 104.  How many disk platters are installed on the RF11 (1)?
	.IFF <ESCAPE> .RETURN
	;
	; Respond  with  the  number (decimal) of RS11 platters included in 
	; your RF11 subsystem. The range of valid responses is from 1 to 8.
	.GOTO RFP

.RJS:
	.SETN COND 0
	.SETN REV 3
	;
	.ASK [<TRUE>] RJS0$3 105.  Do you want RJS03 rather than RJS04 support (Y)?
	.IFF <ESCAPE> .GOTO DS10
	;
	; Type Y  if  your  target  system includes an RJS03 disk subsystem 
	; rather than an RJS04.
	.GOTO RJS
.DS10:	.IFT RJS0$3 .RETURN
	;
	;RJS04 support assumed.
	.RETURN

.DLUN:
	;
	.ASKN [1.:4:2] DL$UN 106.  How many RL01/RL02 units are to be supported (2)?
	.IFF <ESCAPE> .RETURN
	;
	; Enter the  number  (decimal)  of RL01/RL02 units included in your
	; RL01/RL02 subsystem. The range of valid responses is from 1 to 4.
	.GOTO DLUN

.RP0:
	;
	.ASK RP3 107.  Do you want RPR02 rather than RPR02/RP03 support (N)?
	.IFF <ESCAPE> .GOTO RP10
	;
	; Type  Y  if  your  target system includes an RPR02 disk subsystem 
	; rather than RPR02/RP03.
	.GOTO RP0
.RP10:	
	.SETF RP0$3
	.IFT RP3 .RETURN
	.SETT RP0$3
	;
	;RPR02 and RP03 support assumed
	.RETURN
.;;
.;; DU
.;;
 .DUP:
	;
	.ASKN [1:4:1] DU$POR 108.  How many ports are to be supported (1)?
	.IFF <ESCAPE> .GOTO DUP10
	;
	; Enter  the  number  of ports you want the MSCP disk class handler
	; to support.  The range of valid responses is from 1 to 4.
	.GOTO DUP

.DUP10:
	.SETN DU$UN DU$POR.
	.SETD DU$UN
	.SETN DEFC 172150
	.SETN DEFV 154 
	.SETS NS "R"
	.SETS V "EC"
	.SETN C 1
	.SETS NUM C'C'
.DUP20:
	.IF NS = "R" .GOTO DUP30
	.SETN DEFC DEFC-4
	.IF DEFC >= 160000 .GOTO DUP25
	;
	; ?SYSGEN-F-Next default CSR address out of range ('DEFC')
	; ...Restarting query sequence for this device
	; 
	.GOTO DUP
.DUP25:	.SETN DEFV DEFV-4
	.IF DEFV >= 100 .GOTO DUP27
	;
	; ?SYSGEN-F-Next default vector address out of range ('DEFV')
	; ...Restarting query sequence for this device 
	;
	.GOTO DUP
.DUP27:	.SETS V "C"+"'C'"
	.INC C
	.SETS NUM C'C'
.DUP30:
	;
	.ASKN [160000:177570:'DEFC'] DU$CS'NS' 109.  What is the CSR (register) address for the 'NUM' port ('DEFC')?
	.IFF <ESCAPE> .GOTO DUP35
	;
	; Enter the CSR address (octal) of the 'NUM' port. The valid range
	; for CSR address is 160000 to 177570. The standard address is 'DEFC'.
	.GOTO DUP30
.DUP35:
	;
	.IF DU$CS'NS' = DU$CS'NS'/2*2 .GOTO DUP40
	; ?SYSGEN-W-Address not even
	.GOTO DUP30
.DUP40:
	;
	.ASKN [100:474:'DEFV'] DU$V'V' 110.  What is the vector address for the 'NUM' port ('DEFV')?
	.IFF <ESCAPE> .GOTO DUP45
	;
	; Enter the vector address (octal) of the 'NUM' unit. The range for
	; valid responses is from 100 to 474.
	.GOTO DUP40
.DUP45:
	;
	.IF DU$V'V' = DU$V'V'/2*2 .GOTO DUP50
	; ?SYSGEN-W-Address not even
	.GOTO DUP40

.DUP50:
	.DEC DU$UN
	.IF DU$POR = 1 .GOTO DUP70
	.IF DU$UN = 0 .GOTO DUP60
	.IF DU$CS'NS' <> DEFC .SETN DEFC DU$CS'NS'
	.IF DU$V'V' <> DEFV .SETN DEFV DU$V'V'
	.SETS NS "'C'"
	.GOTO DUP20
	
.DUP60:
	;
	.ASK DU$BOO 111.  Do you want support for multiple port booting (N)?

	.IFF <ESCAPE> .GOTO DUP70

	;
	; Multiple port booting support allows you to boot RT-11 from any 
	; DU port. If you do not select support for multiple port booting,
	; you can boot RT-11 from only port 0.
	;
	.GOTO DUP60

.DUP70:
	.IFF XM	.RETURN
	;
	.ASK DU$BBR 112.  Do you want support for DU initiated bad block replacement (N) ?
	.IFF <ESCAPE> .RETURN
	; 
	; Bad block replacement is a technique in which substitute blocks
	; are provided for blocks that have caused a read or write error.
	; If your system includes an RC25, or RA series device, you should
	; request support for DU initiated bad blocks. Enter YES if you want 
	; DU to perform the bad block replacement.
	;
	.GOTO DUP70

.DSP:
	;
	.ASK [<TRUE>] SP$FLG 140.  Do you want support for banner pages (Y)?
	.IFF <ESCAPE> .RETURN
	;
	; Type  Y  if you want  banner page support to be included with the
	; spool handler.
	.GOTO DSP
.;;
.;; XL
.;;
.DXL:
.XL20:
	;
	.ASKN [160000:177570:176500] XL$CSR 151.  What is the CSR address for XL (176500)?
	.IFF <ESCAPE> .GOTO XL30
	;
	; Enter the CSR address (octal) of XL.
	.GOTO XL20
.XL30:
	.IF XL$CSR = XL$CSR/2*2 .GOTO XL35
	; ?SYSGEN-W-Address not even
	.GOTO XL20
.XL35:
	;
	.ASKN [100:474:300] XL$VEC 152.  What is the vector address for XL (300)?
	.IFF <ESCAPE> .GOTO XL40
	;
	; Enter the vector address (octal) of XL.
	.GOTO XL35
.XL40:
	.IF XL$VEC = XL$VEC/2*2 .RETURN
	; ?SYSGEN-W-Address not even
	.GOTO XL35
	
.;;
.;; NQX
.;;
.DNQ:
.NQ20:
	;
	.ASKN [160000:177570:174440] NQ$CSR 153.  What is the CSR address for NQX (174440)?
	.IFF <ESCAPE> .GOTO NQ30
	;
	; Enter the CSR address (octal) of NQX.
	.GOTO NQ20
.NQ30:
	.IF NQ$CSR = NQ$CSR/2*2 .GOTO NQ35
	; ?SYSGEN-W-Address not even
	.GOTO NQ20
.NQ35:
	;
	.ASKN [100:474:120] NQ$VEC 154.  What is the vector address for NQX (120)?
	.IFF <ESCAPE> .GOTO NQ40
	;
	; Enter the vector address (octal) of NQ.
	.GOTO NQ35
.NQ40:	
	.IF NQ$VEC = NQ$VEC/2*2 .RETURN
	; ?SYSGEN-W-Address not even
	.GOTO NQ35
.;;
.;; MT, MS, MM, MU
.;;
.MTF:
	;
	.ASK [<TRUE>] 'DNM'$FSM 120.  Do you want the file-structured magtape handler (Y)?
	.IFF <ESCAPE> .GOTO MT10
	;
	; FILE-STRUCTURED MAGTAPE OPTION:
	; RT-11  magtape  support  is available in two forms.  The standard 
	; form  is  file-structured magtape support, which uses a subset of 
	; ANSI   file  format.   The  file-structured  handler  stores  and 
	; retrieves  data  in  a  file format usable with most RT-11 system 
	; programs.  The second form of magtape  support, hardware  handler 
	; support,  omits  file  structuring  and  reads  and  writes  data 
	; directly in variable length records.   While this handler is sig-
	; nificantly  smaller  than the file-structured handler, you cannot 
	; use it with any system programs.  The file-structured handler can 
	; also perform direct hardware functions.
	.GOTO MTF

.MT10:
	.SETN MAXMT 8.
	.IF DNM = "MU" .SETN MAXMT 4
	;
	.ASKN [1.:'MAXMT'.:2] MTU 121.  How many magtape units are to be supported (2)?
	.IFF <ESCAPE> .GOTO MT20
	;
	; NUMBER OF MAGTAPE UNITS OPTION:
	; The magtape  handler requires table space for each magtape  unit.
	; You can minimize the size of the magtape handler by limiting  the
	; number  of  units  it  can  simultaneously  handle  to the number 
	; actually present on the target machine.
	.GOTO MT10

.MT20:	
	.SETN 'DNM'$UN MTU.
	.SETD 'DNM'$UN
	.IF DNM <> "MS" .AND .IF DNM <> "MU" .RETURN
	.IF DNM = "MS" .SETN DEFC 172522
	.IF DNM = "MS" .SETN DEFV 224
	.IF DNM = "MU" .SETN DEFC 174500
	.IF DNM = "MU" .SETN DEFV 260
	.SETS NS "R"
	.SETS V "EC"
	.SETN C 0
	.SETS NUM C1

.MT30:
	.IF DNM <> "MU" .GOTO MT35
	.IF NS = "R" .GOTO MT35
	.SETN NNS 'NS'+1
	.SETS NS "'NNS'"
.MT35:
	;
	.ASKN [160000:177570:'DEFC'] 'DNM'$CS'NS' 122.  What is the address of the 'NUM' unit ('DEFC')?
	.IFF <ESCAPE> .GOTO MT40
	;
	; Each  unit  requires  two  contiguous  bus addresses for status
	; registers.  Enter  the  address (octal) of the 'NUM' unit.  The
	; range of valid responses is from 160000 to 177570.
	.GOTO MT35

.MT40:
	.IF 'DNM'$CS'NS' = 'DNM'$CS'NS'/2*2 .GOTO MT45A
	; ?SYSGEN-W-Address not even
	.GOTO MT35
.MT45A:
	.IF DNM <> "MU" .GOTO MT45
	.IF V = "EC" .GOTO MT45
	.SETS VSUB V[2:2]
	.SETN NNS 'VSUB'+1
	.SETS V "C"+"'NNS'"
.MT45:
	;
	.ASKN [100:474:'DEFV'] 'DNM'$V'V' 123.  What is the vector address of the 'NUM' unit ('DEFV')?
	.IFF <ESCAPE> .GOTO MT50
	;
	; Enter the vector address (octal) of the 'NUM' unit. The range for
	; valid responses is from 100 to 474.
	.GOTO MT45

.MT50:
	.IF 'DNM'$V'V' = 'DNM'$V'V'/2*2 .GOTO MT50A
	; ?SYSGEN-W-Address not even
	.GOTO MT45
.MT50A:
	.DEC MTU
	.IF MTU = 0 .RETURN
	.IF 'DNM'$CS'NS' <> DEFC .SETN DEFC 'DNM'$CS'NS'
	.IF 'DNM'$V'V' <> DEFV .SETN DEFV 'DNM'$V'V'
	.IF C <> 0 .GOTO MT60
	.IF DNM = "MS" .SETN DEFV 300
	.IF DNM = "MU" .SETN DEFV MU$V'V'+4
	.SETS E "C"
	.SETS NUM C2
	.INC C
	.GOTO MT70

.MT60:
	.SETN DEFV 'DNM'$V'V'+4
	.INC C
	.SETN TEMPN C+1
	.SETS NUM C'TEMPN'
.MT70:	
	.SETN DEFC DEFC+4
	.SETS V E+"'C'"
	.SETS NS "'C'"
	.IF DEFC LE 177570 .IF DEFC GE 160000 .GOTO MT70A
	;
	; ?SYSGEN-F-Next default CSR address out of range ('DEFC')
	; ...Restarting query sequence for this device
	; 
	.GOTO MTF
.MT70A: .IF DEFV LE 474 .IF DEFC GE 100 .GOTO MT30
	;
	; ?SYSGEN-F-Next default vector address out of range ('DEFV')
	; ...Restarting query sequence for this device
	; 
	.GOTO MTF
.;;
.;; LP, LS
.;;
.LPC:
	.IFT PROCTS .GOTO LSC
	.IFT CTS .GOTO CTSLP
	;
	.ASK LPC 130.  Does your printer have a nonstandard vector or CSR (N)?
	.IFF <ESCAPE> .GOTO LP10
	;
	; The standard line printer vector address is 200 and  the standard
	; CSR  address  is 177514.  If your printer is installed at another
	; vector or CSR address, specify the correct values.
	.GOTO LPC
.LP10:	
	.IFF LPC .RETURN
	;
	.ASKN [160000:177570:177514] LP$CSR 131.  What is the CSR address for the printer (177514)?
	.IFF <ESCAPE> .GOTO LP20
	;
	; Respond  with  the  address  of the control register for the line 
	; printer. The range for valid responses is from  160000 to 177570.
	.GOTO LP10
.LP20:
	.IF LP$CSR = LP$CSR/2*2 .GOTO LP20A
	; ?SYSGEN-W-Address not even
	.GOTO LP10
.LP20A:
	;
	.ASKN [100:474:200] LP$VEC 132.  What is the vector address for the printer (200)?
	.IFF <ESCAPE> .GOTO LP30
	;
	; Respond with the vector address for  the line printer.  The range
	; for valid responses is from 100 to 474.
	.GOTO LP20A
.LP30:
	.IF LP$VEC = LP$VEC/2*2 .RETURN
	; ?SYSGEN-W-Address not even
	.GOTO LP20A

.LSC:
	.IFF PROCTS .GOTO LS1
	.SETT LS$PC
	.SETN LS$CSR 173400
	.SETN LS$VEC 220
	.GOTO LS20
.LS1:
	.IFT CTS .GOTO CTSLP
	;
	.ASK [<FALSE>] LS$PC 133.  Do you want support for the PC300 printer port (N)?
	.IFF <ESCAPE> .GOTO LS5
	;
	; Type  Y if you will be using the LS handler with the PC300 series
	; of personal computers.
	.GOTO LSC
.LS5:	
	;
	.SETN DEFC 176500
	.SETN DEFV 300
.LS5A:
	;
	.ASKN [160000:177570:'DEFC'] LS$CSR 134.  What is the CSR for the serial line printer ('DEFC')?
	.IFF <ESCAPE> .GOTO LS10
	;
	; Respond with the address of  the  control register for the serial
	; line  printer.   The  range for valid responses is from 160000 to 
	; 177570.
	.GOTO LS5A
.LS10:
	.IF LS$CSR = LS$CSR/2*2 .GOTO LS10A
	; ?SYSGEN-W-Address not even
	.GOTO LS5A

.LS10A:
	;
	.ASKN [60:474:'DEFV'] LS$VEC 135.  What is the vector for the serial line printer ('DEFV')?
	.IFF <ESCAPE> .GOTO LS20
	;
	; Respond with the vector address for the serial line printer.  The
	; range for valid responses is from 100 to 474.
	.GOTO LS10A
.LS20:	;
	.IF LS$VEC = LS$VEC/2*2 .RETURN
	; ?SYSGEN-W-Address not even
	.GOTO LS10A
.CTSLP:
	.SETF LPP
	.SETF LQP
	.SETF LRP
	.SETF LSP
	.SETF LPS
	.SETF LQS
	.SETF LRS
	.SETF LSS
	;
	.ASK [<TRUE>] ANS 133.  Do you want serial line printer support (Y)?
	.IFF <ESCAPE> .GOTO CTLP10
	;
	;Respond with Y if you want any serial line printer support.
	.GOTO CTSLP
.CTLP10:
	.IFT ANS .SETT TIM$IT
	;
	.ASKN [0:4:1] LPNUM 134.  How many (serial & parallel) line printers (1)?
	.IFF <ESCAPE> .GOTO CTLP20
	;
	;Enter the total number of line printers you want support for.
	.GOTO CTLP10
.CTLP20:
	.;;DFAULT SYMBOLS = DF+(C=CSR,V=VECTOR)+(P=PARALLEL,S=SERIAL)+NUMBER
	.SETS DFCP1 "177514"
	.SETS DFVP1 "200"
	.SETS DFCS1 "176500"
	.SETS DFVS1 "300"
	.SETS DFCP2 "164004"
	.SETS DFVP2 "170"
	.SETS DFCS2 "176510"
	.SETS DFVS2 "310
	.SETS DFCP3 "164014"
	.SETS DFVP3 "174
	.SETS DFCS3 "176520"
	.SETS DFVS3 "320"
	.SETS DFCP4 "164024"
	.SETS DFVP4 "270"
	.SETS DFCS4 "176530"
	.SETS DFVS4 "330"
	.SETF SWIT
	.SETN CNT 1
.CTLP22:
	.IF CNT GT LPNUM .GOTO CTLP90
	.SETS NUM C'CNT'
	.SETT PAR
	.SETS TYP "P"
	.IFF ANS .GOTO CTLP30
.CTLP25:
	;
	.ASK [<TRUE>] PAR 135.  Is the 'num' line printer parallel (Y)?
	.IFF <ESCAPE> .GOTO CTLP30
	;
	;Respond with YES if your 'num' line printer is a parallel printer.
	.GOTO CTLP25
.CTLP30:
	.IFF PAR .SETS TYP "S"
	.SETS TEMPS LP'CNT'
	.SETT L'TEMPS''TYP'
.CTLP70:
	.SETS DFC DFC'TYP''CNT'
	.SETS DFV DFV'TYP''CNT'
	;
	.ASKN [160000:177570:'DFC'] LPC 136.  What is the CSR address for this printer ('DFC')?
	.IFF <ESCAPE> .GOTO CTLP73
	;
	; Respond with the CSR address for the line printer.  The range for
	; valid  responses  is from 160000 to 177570.  The default response 
	; is 'DFC'.
	.GOTO CTLP70

.CTLP73:
	;
	.IF LPC = LPC/2*2 .GOTO CTLP7A
	; ?SYSGEN-W-Address not even
	.GOTO CTLP70

.CTLP7A:
	;
	.ASKN [100:474:'DFV'] LPV 137.  What is the vector address for this printer ('DFV')?
	.IFF <ESCAPE> .GOTO CTLP74
	;
	; Respond  with the vector address for the line printer.  The range
	; for valid  responses  is from 100 to 474.  The dfault response is
	;'DFV'.
	.GOTO CTLP7A
.CTLP74:
	;
	.IF LPV = LPV/2*2 .GOTO CTLP7B
	; ?SYSGEN-W-Address not even
	.GOTO CTLP7A
.CTLP7B:
	;
	.SETS LPID LPID'CNT'
	.OPEN L'TEMPS''TYP'.MAC
	.IF <FILERR> EQ <SUCCES> .GOTO CTLP77
	;
	;?CTSGEN-F-Error creating L'TEMPS''TYP'
	.EXIT 4
.CTLP77:.IFF SWIT .GOTO CTLP80
	.SETN LPC L'TEMPS''TYP'CSR
	.SETN LPV L'TEMPS''TYP'VEC
.CTLP80:
	.ENABLE DATA
.MCALL	.DRDEF
	.DRDEF	L'TYP','LPID',WONLY$,0,'LPC','LPV'
.DISABLE DATA
	.CLOSE 
	.IFT SWIT .GOTO CTLP90
	.SETN L'TEMPS''TYP'CSR 'LPC'
	.SETN L'TEMPS''TYP'VEC 'LPV'
	.INC CNT 
	.GOTO CTLP22
.CTLP90:.RETURN

.CU:	.IFT CHANGE .GOTO CH98
.;; 
.;; Allow for user-provided device handlers
.;;
.U5:
	;
	.ASK UDEV Do you want to add support for any of your own devices (N)?
	.IFF <ESCAPE> .GOTO U10
	;
	; SYSGEN  will  generate  commands  to  assemble  and link any user
	; supplied device handlers.  SYSGEN  also  adds the device names to
	; the system device tables in DEVTBL.MAC.
	.GOTO U5
.U10:
	.IFF UDEV .GOTO C50
	.SETS TXT "device name you want support for"
	.SETN UDEVNO 0
	;
	; Type <ESCAPE><RETURN> for help.
	; Type ?<RETURN> to list all devices.
	; Type .<RETURN> when device specification is complete.
	;
.U15:
	.INC UDEVNO
	.IFDF UD'UDEVNO' .GOTO U15
.U17:
	;
	.DISABLE LOWERCASE
	.ASKS [0:2] UD'UDEVNO' Enter the 'TXT' [dd]:
	.ENABLE LOWERCASE
	.IFF <ESCAPE> .GOTO U20
	;
	; Enter  the  2  character device name for the device for which you
	; are supplying a device handler.
	.GOTO U17
.U20:
	.SETS TXT "next device name"
	.IF UD'UDEVNO' EQ "?" .GOSUB LIST
	.IF UD'UDEVNO' EQ "" .OR .IF UD'UDEVNO' EQ "?" .GOTO U17
	.IF UD'UDEVNO' NE "." .GOTO U15
	.ERASE LOCAL UD'UDEVNO'
.C50:
	.IFT CHANGE .GOTO CH100
.Q160:
	;
	.ASKN [0.:32.:0] EMPTY 160.  How many extra device slots do you want (0)?
	.IFF <ESCAPE> .GOTO C161
	;
	; EXTRA DEVICE SLOT OPTION:
	; SYSGEN  allocates  space  in  the  monitor  for only the devices
	; specified.    You  can  allocate  additional space by requesting
	; empty device slots.  Allocate one empty slot for each device you
	; intend to add to the system after it is built. Also keep in mind
	; that  the  number of logical device assignments you will be able 
	; to make in the running system is equal to  the number of devices
	; plus  empty  device slots in the system you have generated.  You 
	; may  need  to  allocate  extra  device  slots for logical device 
	; assignment purposes.
	.GOTO Q160
.C161:	.IFT CHANGE .GOTO CH20
.;; 
.;; Graphics Options
.;;
	.IFT MTT$Y .OR .IFT CTS .OR .IFT XMONLY .GOTO DE90
	;
	;
	; 'STARS'
	;		GRAPHICS OPTIONS
	; 'STARS'
.Q170:
	;
	.ASK GRAFX 170.  Do you want VT11 or VS60 graphics support (N)?
	.IFF <ESCAPE> .GOTO GR10
	;
	; Type  Y  if  your  target  configuration  includes a VT11 or VS60 
	; graphics  subsystem.   RT-11  support  for  VS60 is minimal.  The 
	; display  handler,  VTHDLR, supports VT11 but does not support any 
	; special features of VS60.
	.GOTO Q170
.GR10:
	.IFF GRAFX .GOTO DE90
	;
	.ASK [<FALSE>] VS60$ 171.  Do you want VS60 support (N)?
	.IFF <ESCAPE> .GOTO GR15
	;
	; Type Y if the graphics subsystem is VS60.
	.GOTO GR10
.GR15:
	.SETF VT11$
	.IFT VS60$ .GOTO GR20
	.SETT VT11$
	;
	; VT11 hardware assumed.
.GR20:
	;
	.ASKN [160000:177570:172000] GRFC 172.  What is the CSR address for the VT11/VS60 (172000)?
	.IFF <ESCAPE> .GOTO GR30
	;
	; The  CSR  addresses  can be floating.  The presence or absence of
	; such floating address devices affects the addresses at which  the
	; other  floating  address  devices  in  the  system are installed.
	; Floating   address  devices  must  be  installed  in  a  standard 
	; sequence.
	;
	; The standard VT11/VS60 CSR address is 172000. However, VT11/VS60s 
	; can  use  floating  addresses.  If your VT11/VS60 is installed at
	; nonstandard CSR  addresses, supply the correct value.  The  valid
	; range for responses is from 160000 to 177570.
	.GOTO GR15
.GR30:
	;
	.ASKN [100:474:320] GRFV 173.  What is the vector address for the VT11/VS60 (320)?
	.IFF <ESCAPE> .GOTO DE90
	;
	; Many  devices  have floating vector  addresses.   The presence or
	; absence of such floating address devices affects the addresses at
	; which  the  other  floating  address  devices  in  the system are
	; installed.   Floating  address  devices  must  be  installed in a
	; standard sequence.
	;
	; The standard VT11/VS60 vector address is 320. However, VT11/VS60s
	; can use floating addresses.   If  your VT11/VS60 is installed  at
	; nonstandard  vector addresses, supply  the  correct  value.   The 
	; range for valid responses is from 100 to 474.
	.GOTO GR30

.DE90:  .IFT CHANGE .GOTO CH20
	.IFF MTT$Y .GOTO C192
.;;
.;; Terminal interface options
.;;
	.IFF PROCTS .GOTO DLTR
	.SETN DLNUM 1
	.SETN DLMDM 0
	.SETN DLC$0 177560
	.SETN DLV$0 60
	.SETN DZ11$N 0
	.SETF DZM
	.GOTO C192	
.DLTR:
	;
	;
	; 'STARS'
	; 		TERMINAL INTERFACE OPTIONS
	; 'STARS'
.DLTRM:
.Q180:	;
	.ASK A Do you want an introduction to terminal interface options (N)?
	.IFF <ESCAPE> .AND .IFF A .GOTO TRST
	.IFF <ESCAPE> .AND .IFT A .GOTO TR10
	;
	; The  introduction  explains  the DL interfaces supported by RT-11
	; and how SYSGEN assigns the terminal numbers.
	.GOTO DLTRM

.TR10:
	;
	; The terminal interface options allow you to select  RT-11 support
	; for  the  terminal  interfaces  installed  in your system.  RT-11
	; supports  a  combination of serial asynchronous interfaces, which
	; include  the  DLV11,  DLV11-E,  DLV11-F,  DLV11-J,  and  the DL11
	; series.  It also supports  DL11-E  and DLV11-E  interfaces,  with
	; modem capabilities.
	;
	; The  dialog  asks first for the number of local DL11  lines, then
	; the  number  of  remote DL11 lines.  The total number of lines is
	; the  sum  of  local and remote lines and must not exceed 8 lines.
	; SYSGEN  assigns physical unit numbers of the  DL11 lines first to
	; local  lines  and  then  to  remote  lines.   This  assignment is
	; permanent  and  you cannot change its order.
	;
	; After SYSGEN has established the number of lines of each type, it
	; must  establish  the CSR and vector addresses for each line.  The
	; first  such  question  corresponds  to  the first local line (the
	; console),   the  second to the second local line, etc., until all
	; local  lines are accounted for.  At that point, the next question
	; applies to the first remote line, the second to the second remote
	; line, etc., until  all remote lines are accounted for.
	.IFF VT100 .GOTO TR15
	;
	.ASK CONTIN Type return to continue
.TR15:	;
	; If your interfaces are DL11-W interfaces, they should be at REV E
	; or higher.  If they are not, an Engineering Change Order (ECO DEC
	; -O-LOG  M7856-S0002)  must  be  applied  to the M7856 module. The 
	; field  service  representative  who installs your hardware should
	; apply the ECO, if necessary.
.TRST:
	;
	;180.  How many local DL11 lines, including the console, 
	.ASKN [1.:8.:1] DLNUM      are to be supported (1)?
	.IFF <ESCAPE> .GOTO TR16
	;
	; Enter  the  total number of LOCAL DL11 terminals included in  the
	; target configuration.  Since the console is always a local  DL11,
	; the  response  is  never less than 1.  Do not include REMOTE DL11
	; lines in this number. Remote DL11 lines are specified in the next
	; question.  The range for valid responses is from 1 to 8.
	.GOTO TRST
.TR16:
	.SETN LOC DLNUM
	;
	.ASKN [0.:7.] DLMDM 181.  How many remote DL11 lines are to be supported (0)?
	.IFF <ESCAPE> .GOTO TR20
	;
	; Enter the total number of REMOTE  DL11  terminals included in the
	; target configuration.  Do not include LOCAL  DL11  lines  in this
	; number.  This reponse must not be greater than 7.
	.GOTO TR16
.TR20:
	.SETN CNT DLNUM+DLMDM
	.IF CNT > 8. ; ?SYSGEN-W-Exceeded total number of valid DL11 lines
	.IF CNT > 8. .GOTO DLTRM
	.SETS IDENT "first (console)"
	.SETN DEFC 177560
	.SETN DEFV 60
	.SETN C 0

.TR25:
	;
	.ASKN [160000:177570:'DEFC'] DLC$'C' 182.  What is the CSR for the 'IDENT' DL11 ('DEFC')?
	.IFF <ESCAPE> .GOTO TR26
	;
	; Enter the  address  (octal) of the DL11 interface.  The range for
	; valid responses is from 160000 to 177570.
	.GOTO TR25
.TR26:
	;
	.ASKN [60:474:'DEFV'] DLV$'C' 183.  What is the vector for the 'IDENT' DL11 ('DEFV')?
	.IFF <ESCAPE> .GOTO TR30
	;
	; Enter  the vector address  (octal)  of the DL11 interface for the
	; console terminal.  The range for valid responses is from 
	; 60 to 474.
	.GOTO TR26

.TR30:
	.IF C EQ 0 .GOTO TR35
	.SETN DEFC DLC$'C'
	.SETN DEFV DLV$'C'
.TR35:	.INC C
	.IF C = 1 .SETN DEFC 176500-10
	.IF C = 1 .SETN DEFV 300-10
	.SETN DEFC DEFC+10
	.SETN DEFV DEFV+10
	.IF LOC = 0 .GOTO TR40
	.DEC LOC
	.IF LOC <> 0 .SETS IDENT "next (local)"
	.IF LOC <> 0 .GOTO TR35A
	.SETN DEFC DEFC-670	
	.SETN REM DLMDM+1
	.SETS IDENT "next (remote)"

.TR35A:	.IF DEFC LE 177570 .IF DEFC GE 160000 .GOTO TR35B
	;
	; ?SYSGEN-F-Next default address out of range ('DEFC')
	; ...Restarting query sequence for this device 
	;
	.GOTO DLTR
.TR35B:	.IF DEFV LE 474 .IF DEFV GE 60 .GOTO TR40
	;
	; ?SYSGEN-F-Next default vector address out of range ('DEFV')
	; ...Restarting query sequence for this device 
	;
	.GOTO DLTR
.TR40:
	.IF LOC <> 0 .GOTO TR25
	.DEC REM
	.IF REM <> 0 .GOTO TR25

.TR45:
	.SETN DZ11$N 0
	;
	.ASK DZM 184.  Do you want DZ11 or DZV11 multiplexer support (N)?
	.IFF <ESCAPE> .GOTO TR46
	;
	; You  can select RT-11 support for one DZ11-A or DZ11-B eight-line
	; multiplexer   with  an  additional  DZ11-C  or  DZ11-D eight-line
	; multiplexer, for a maximum of 16 lines.   Or  you can  select one
	; to four DZV11 four-line multiplexers.  Modem support is available
	; on  remote  lines,  but  is  limited  to  Bell 103 type modems or
	; equivalent.   RT-11  support  for  modems  requires the modems to
	; operate  in auto-answer mode.  Therefore, the "common carrier and
	; clear  to send" options must have been installed (during manufac-
	; ture  or  installation).  Type Y if your configuration includes a 
	; DZ11 or DZV11 multiplexer.
	.GOTO TR45
.TR46:
	.IFF DZM .GOTO C192
	;
	.ASK [<TRUE>] DZ11 185.  Do you want DZ11 multiplexer support (Y)?
	.IFF <ESCAPE> .GOTO TR50
	;
	; Type Y if your configuration includes a DZ11 multiplexer
	.GOTO TR46

.TR50:	.SETF DZV$11
	.IFF DZ11 .SETT DZV$11
	.IFT DZ11 .GOTO TR55
	;
	;DZV11 four-line multiplexer support is assumed.
	;
.TR55:
	.SETN DZLIM 2
	.IFT DZV$11 .SETN DZLIM 4
	;
	.ASKN [1.:'DZLIM':1] DZCNT 186.  How many DZ multiplexers are to be supported (1)?
	.IFF <ESCAPE> .GOTO TR60
	;
	; Enter the number of DZ multiplexers in the target configuration.
	.GOTO TR55
.TR60:	.SETN DZ11$N DZCNT.
.TR61:
	;
	.ASKN [0.:16.:1] DZ11$L 187.  How many local DZ lines are to be supported altogether (1)?
	.IFF <ESCAPE> .GOTO TR62
	;
	; Enter the  total  number  (decimal)  of  DZ  lines that are local
	; terminals.  The range for valid responses is from 0 t0 16.
	.GOTO TR61
.TR62:
	;
	.ASKN [0.:16.:0] DZ11$M 188.  How many remote DZ lines are to be supported altogether (0)?
	.IFF <ESCAPE> .GOTO TR80
	;
	; Enter  the  total  number  (decimal)  of DZ lines that are remote
	; terminals.  The range for valid responses is from 0 t0 16.
	.GOTO TR62
.TR70:
	;
	;The interface  vectors  and  CSR  addresses  are  assigned to  the
	;floating device region and vary with each installation.
	.RETURN
.TR80:
	.IF DZ11$M <> 0 .SETT TIM$IT

	.SETN C 1
	.SETN DEFC 160100
	.SETN DEFV 300
.TR90:
	.IF C GT DZCNT .GOTO TR105
	.SETS NUM C'C'
	.SETN D 'C'-1
.TR95:
	;
	.ASKN [160000:177570:'DEFC'] DZCS$'D' 189.  What is the CSR for the 'NUM' DZ multiplexer ('DEFC')?
	.IFF <ESCAPE> .GOTO TR96
	;
	; Enter  the  CSR  address for the 'NUM' DZ multiplexer.  The valid
	; range is 160000-177570.
	.GOTO TR95
.TR96:
	;
	.ASKN [60:474:'DEFV'] DZVC$'D' 190.  What is the vector for the 'NUM' DZ multiplexer ('DEFV')?
	.IFF <ESCAPE> .GOTO TR100
	;
	; Enter the vector address for the 'NUM' DZ multiplexer.  The valid
	; range is from 60 to 474.
	.GOTO TR96
.TR100:	 
	.SETN DEFC DZCS$'D'
	.SETN DEFV DZVC$'D'
	.INC C 
	.SETN DEFC DEFC+10
	.SETN DEFV DEFV+10
	.IF DEFV GT 320 .SETN DEFV DEFV+10
	.IF DEFC LE 177570 .IF DEFC GE 160000 .GOTO TR101
	;
	; ?SYSGEN-F-Next default CSR address out of range ('DEFC')
	; ...Restarting query sequence for this device 
	.GOTO TR45
.TR101:	.IF DEFV LE 474 .IF DEFC GE 60 .GOTO TR90
	;
	; ?SYSGEN-F-Next default vector address out of range ('DEFV')
	; ...Restarting query sequence for this device 
	.GOTO TR45
.TR105:
	;
	.ASKN [0.:9600.:300.] BAUD 191.  What baud rate do you want your lines initialized to (300)?
	.IFF <ESCAPE> .GOTO TR110
	;
	; The  lines must be initialized to a specific baud rate.   You can
	; select 9600, 4800, 2400, 1200, 300, 150, or 110 baud.  
	.GOTO TR105

.TR110:	.SETN DZST$P 0
	.IF BAUD = 9600. .SETN DZSP$D 7000
	.IF BAUD = 4800. .SETN DZSP$D 6000
	.IF BAUD = 2400. .SETN DZSP$D 5000
	.IF BAUD = 1200. .SETN DZSP$D 3400
	.IF BAUD = 300.  .SETN DZSP$D 2400
	.IF BAUD = 150.  .SETN DZSP$D 2000
	.IF BAUD = 110.  .SETN DZSP$D 1000
	.IF BAUD = 110.  .SETN DZST$P 40
	.IFDF DZSP$D .GOTO C192
	;
	; ?SYSGEN-E-Invalid baud rate.
	.GOTO TR105
.;;RNG$ this routine keeps control over the CSR/VECTOR address range
.;;

.RNG$:	
	;
	; ?SYSGEN-F-Next default 'ADRDF' address out of range ('DEFA')
	; ...Restarting query sequence for this device 
	.RETURN



.;;
.;; User defined system conditionals
.;;
.USERPT:
	;
	.ASK USERP 68.  Do you want to define any other system conditionals (N)?
	.IFF <ESCAPE> .GOTO UP10
	;
	; Some  of  the conditionals which the monitors and device handlers
	; use  are not set as a result of the SYSGEN questions.  An example
	; is PDT$OP, which causes the system to be built with code which is
	; optimal  for  a  PDT.  Respond  with  Y  if  you  want any system
	; conditionals to be included in your system conditional file which 
	; are not normally defined through SYSGEN.
	.GOTO USERPT
.UP10:
	.IFF USERP .RETURN
.UP11:
	.SETS TXT ""
	;
	; Enter system conditional definition in the form 
	;	symbol = value
	;
	; Type <ESCAPE><RETURN> for help.
	; Type ?<RETURN> to list user system conditional definitions.
	; Type .<RETURN> when all user system conditionals have been defined.
	;
.UP20:
	.INC UPNO
.UP21:
	;
	.ASKS [1] TEMPS 69.  Enter the 'TXT'system conditional and value:
	.IFF <ESCAPE> .GOTO UP30
	;
	; Enter  the system conditional definition as you want it to appear
	; in the system conditional (.CND) file.  For example:
	; PDT$OP = 1		; Generate PDT optimal code
	.GOTO UP21
.UP30:
	.IF TEMPS EQ "." .GOTO UPCH
	.IF TEMPS NE "?" .GOTO UP40
	;
	; User defined system conditionals:
	;
	.SETN TEMPN 1
.UP35:
	.IFNDF UP1 ; none
	.IFNDF UP'TEMPN' .GOTO UP21
	.SETS TEMPS UP'TEMPN'
	;'TEMPS'
	.INC TEMPN
	.GOTO UP35
.UP40:	.SETS UP'UPNO' TEMPS
	.SETS TXT "next "
	.GOTO UP20

.UPCH:	.IFF CHANGE .RETURN

.C192:	.IFT CHANGE .GOTO CH20

	.GOTO CHANG
.;;
.;; Read in an answer file
.;;
.READA:
	.IFNDF ANSFIL .GOTO CHANG
.;; Sett switch for cts-300 lp handlers
	.IFT CTS .SETT SWIT
	.OPENR #0 'ANSFIL'
	;        ...reading in answer file.
.RDLIN:
	.READ #0 STRING
	.IFF <EOF> .'STRING'
	.IFF <EOF> .GOTO RDLIN
	.PURGE #0
	
	.IFDF CLOCK .SETD CLOCK
	.IFDF TTYOUT .SETD TTYOUT
	.IFDF TTYIN .SETD TTYIN
	.IFDF EMPTY .SETD EMPTY
	.IFDF ERL$U .SETD ERL$U
	.IFDF DLNUM .SETD DLNUM
	.IFDF DZ11$L .SETD DZ11$L
	.IFDF DZ11$M .SETD DZ11$M

.;This is for compatability with V5 answer files:
	.IFNDF PCDZ .SETF PCDZ
	.IFNDF DZ .SETF DZ
	.SET'DZ' DZM		.;DZ in answer file means DZ11
				.;DZM internally means DZ11
	.SET'PCDZ' DZ		.;PCDZ in answer file means device DZ
				.;DZ internally means device DZ
				
.;;
.;; Allow user to change responses
.;;
.CHANG:
	.IFT NOQ .GOTO SYCND
	;
	.ASK CHANGE Do you want to change any of your responses (N)?
	.IFF <ESCAPE> .GOTO CH10
	;
	; Responses have  been  obtained  for  all of the SYSGEN  questions.
	; You  are  now  given  an  opportunity to make minor changes to the 
	; monitor options which you have selected or to remove support for a
	; device  or  add  support  for  a device.  If you have made a large
	; number of errors in this SYSGEN session it is recommended that you
	; restart the SYSGEN dialog.
	.GOTO CHANG
.CH10:
	.IFF CHANGE .GOTO SYCND
	.SETS TXT ""
	.GOTO CH21
.CH20:
	.SETS TXT " more"
.CH21:
	;
	.ASK CHMON Do you want to change'TXT' monitor/terminal option responses (N)?
	.IFF <ESCAPE> .GOTO CH22
	;
	; You  may  make changes to most of the dialog questions concerning
	; the options to be assembled into the monitor.  You may not change
	; the monitor types to be SYSGENed. Also, you may not add or remove
	; multiterminal  support.  To make these  changes, you must restart
	; the SYSGEN dialog.  
	.GOTO CH21
.CH22:
	.IFF CHMON .GOTO CH70
	;
	.ASKN [0:191.:0] CHNUM What question number do you want re-asked? 
	.IFF <ESCAPE> .GOTO CH25
	;
	; Respond with the number which precedes the question that  you wish
	; to have re-asked.  
	;
	; The  monitor option questions which you may change are:
	;
	;   4.  SJ timer support			20.  User command linkage
	;   5.  Device timeout support		21.  High speed ring buffer
	;   6.  System I/O error messages	22.  Keyboard monitor commands
	;   7.  System job support		26.  50 Hz clock
	;   8.  .SPCPS request			27.  KW11-P as system clock
	;   9.  Global SCCA support		30.  Startup command file
	;  11.  Asynchronous terminal status	31.  Floating point support
	;  12.  Multiterminal timeout support	32.  Memory parity support
	;  13.  Output buffer size		33.  Power failure message
	;  14.  Input buffer size		34.  Batch support
	;  15.  .FETCH request under XM		35.  Error logging
	;  16.  Month and year rollover support	160. Number of empty device slots
	;					170.  VT11/VS60 graphics
	;
	; If  you  do  not  want  to  modify  any additional monitor option
	; reponses, type <RETURN>.
		
	.GOTO CH22
.CH25:
	.IF CHNUM EQ 0 .GOTO CH70
	.IF CHNUM GT 3. .GOTO CH30
	;
	; You  may  not  modify which monitor types are to be built.  To do
	; this you must re-start the SYSGEN session.
	.GOTO CH20
.CH30:
	.IF CHNUM NE 10. .GOTO CH35
	;
	; You may not add or remove multiterminal  support.  To do this you
	; must restart the SYSGEN session.
	.GOTO CH20
.CH35:
	.IF CHNUM LT 100. .OR .IF CHNUM GT 159. .GOTO CH40
	;
	; You may not change any responses  concerning  devices.   You will
	; be  given  an opportunity to remove support  for a device or have
	; the  questions  concerning  a  specific device re-asked after you 
	; have completed making changes to the monitor option questions.
	.GOTO CH20
.CH40:
	.IFF CTS .GOTO CH44
	.TEST " 4 6 8 12 27 31 " " 'CHNUM' "
	.IF <STRLEN> EQ 0 .GOTO CH44
	;
	; When  generating  a  CTS-300 system the response to this question 
	; may not be changed.
	.GOTO CH20
.CH44:
	.DISABLE OCTAL
	.;;If its a GRAFX questions re-ask all GRAFX questions.
	.IF CHNUM GE 170. .IF CHNUM LE 173. .SETN CHNUM 170.
	
	.;;If its a KMON question re-ask all the KMON questions.
	.IF CHNUM GE 22. .IF CHNUM LE 25. .SETN CHNUM 22.

	.;;If its # of error log devices start with 1st EL question.
	.IF CHNUM EQ 36. .SETN CHNUM 35.

	.;;If its concerning Multiterms, ask all multiterm questions.
	.IF CHNUM GE 180. .SETN CHNUM 180.

	.;;Check whether question is valid for selected monitors.
	.TEST " 17 18 19 28 29 " " 'CHNUM' "
	.IF <STRLEN> NE 0 .GOTO CHER1
	.IF CHNUM GE 37. .IF CHNUM LE 99. .GOTO CHER1
	.IFF BL .GOTO CH45
	.IF CHNUM LT 13. .GOTO CHER1
	.IF CHNUM EQ 27. .GOTO CHER1
	.IF CHNUM GE 32. .GOTO CHER1
.CH45:	.IFT SJ .GOTO CH47
	.IF CHNUM EQ 4 .GOTO CHER1
	.IF CHNUM EQ 6 .GOTO CHER1
.CH47:	.IFT XM .GOTO CH48
	.IF CHNUM EQ 15. .GOTO CHER1
.CH48:	.IFF XMONLY .GOTO CH50
	.IF CHNUM EQ 170. .GOTO CHER1
.CH50:	.IFT FBXM .GOTO CH55
	.TEST " 7 8 9 35 36 " " 'CHNUM' "
	.IF <STRLEN> NE 0 .GOTO CHER1
.CH55:	.IFT MTT$Y .GOTO CH60
	.IF CHNUM EQ 11. .OR .IF CHNUM EQ 12. .GOTO CHER1
	.IF CHNUM GE 180. .GOTO CHER1
.CH60:	.IFF MTT$Y .GOTO CH65
	.IF CHNUM EQ 170. .GOTO CHER1
.CH65:
	.IF CHNUM NE 180. .GOTO CH66
	;
	; All terminal interface options must be answered again.
.CH66:	
	.ENABLE OCTAL
	.GOTO Q'CHNUM'

.CHER1:	
	.ENABLE OCTAL
	;
	; The  dialog  question  you  have  selected  is  invalid  for  the 
	; monitor(s)  being  built,  or for  your response to the query for
	; multiterminal support.
	.GOTO CH20
.CH70:
	;
	.ASK CHANGE Do you want to change your device support (N)?
	.IFF <ESCAPE> .GOTO CH71
	;
	; Type  "Y"  if  you want to remove, add, or modify support for any
	; devices.
	.GOTO CH70
.CH71:
	.IFF CHANGE .GOTO CH100
	.SETS TXT "device"
.CHDEV:
	;
	.ASK DEVREM Do you want to remove support for any 'TXT' (N)?
	.IFF <ESCAPE> .GOTO CH80
	;
	; You are now given an opportunity to remove support for any device
	; for which support was requested.	
	.GOTO CHDEV
.CH80:
	.IFF DEVREM .GOTO CH90
	.SETS TXT "more devices"
	;
	.DISABLE LOWERCASE
	.ASKS [0:2] DVREM What device do you NOT want supported?
	.ENABLE LOWERCASE
	.IFF <ESCAPE> .GOTO CH85
	;
	; If  you  previously asked to have a device supported, but you now
	; do  not  want  support for a device, type the two letter name for
	; that device.
	.GOTO CH86
.CH85:	.IF <STRLEN> EQ 0 .GOTO CHDEV
	.TEST DEVSTR " "+DVREM+" "
	.IF <STRLEN> NE 0 .GOTO CH87
	.SETN UDEVNO 0
.CH851:
	.INC UDEVNO
	.IFNDF UD'UDEVNO' .GOTO CH859
	.IF UD'UDEVNO' NE DVREM .GOTO CH851
	.SETS UD'UDEVNO' ""
	.GOTO CH871
.CH859:	;
	; 'DVREM' is not a valid RT-11 device or a user supplied device. 
.CH86:	;
	.ASK [<TRUE>] LSTD Do you want a list of available devices (Y)?
	.IFT LSTD .GOSUB LIST
	.GOTO CHDEV
.CH87:	.SETF 'DVREM'
.CH871:	;
	;'DVREM' will not be supported.
	.GOTO CHDEV
.CH90:	
	;
	;Do you want to add support for any device or have the questions
	.ASK DEVCHG  for any device re-asked (N)?
	.IFF <ESCAPE> .GOTO CH95
	;
	; SYSGEN  will  give  you  an  opportunity  to add support for both 
	; DIGITAL supported  devices and your own devices.  Type "Y" if you
	; want  to add support for any device or change your response to  a
	; question relating to a device.
	.GOTO CH90
.CH95:
	.IFF DEVCHG .GOTO CH100
.CH96:
	;
	.ASK [<TRUE>] DIGITL Do you want to add/modify a DIGITAL supported device (Y)?
	.IFF <ESCAPE> .GOTO CH97
	;
	; Type "Y" if you want  to  add  support  for any DIGITAL supported 
	; device or have questions related to any  such  device re-asked.
	.GOTO CH96
.CH97:
	.IFF DIGITL .GOTO CH98
	.SETS TXT "device name to add/modify"
	.GOTO Z28
.CH98:
	.GOTO U5
.CH100:
	;
	.ASK CHANGE Do you want to define or redefine any system conditionals (N)?
	.IFF <ESCAPE> .GOTO CH988
	;
	; Type "Y" if you want to define additional system conditionals.  If 
	; you want to change the value of a conditional, redefine it, and it
	; will assume the new value.
	.GOTO CH100
.CH988:	.IFF CHANGE .GOTO CHUP
	.;Skip through already defined user system conditionals.
	.SETN UPNO 1
.CH989:
	.IFNDF UP'UPNO' .GOTO CH99
	.INC UPNO
	.GOTO CH989
.CH99:
	.DEC UPNO
	.GOTO UP11
.CHUP:
	.GOTO SYCND
.CRTMAC:
.;;
.;;	Using previously created answer file, cts-300, create lxp and lxs
.;;	macro files for x.DEV file.
.;;
	.SETN CNT 1
	.SETT SWIT
.GO1:
	.IF CNT GT LPNUM .GOTO GO90
	.SETT PAR
	.SETS TYP "P"
.GO5:
	.SETS TEMPS LP'CNT'
	.IFT L'TEMPS''TYP' .GOSUB CTLP74
	.IFF PAR .GOTO GO10
	.SETF PAR
	.SETS TYP "S"
	.GOTO GO5
.GO10:
	.INC CNT
	.GOTO GO1
.GO90:
	.SETF SWIT
	.RETURN
.COPRIT:
'P'      
'P' THIS SOFTWARE IS FURNISHED UNDER A LICENSE AND MAY ONLY  BE  USED
'P' OR COPIED IN ACCORDANCE WITH THE TERMS OF SUCH LICENSE.
'P'
'P' COPYRIGHT (c) 1986 BY DIGITAL EQUIPMENT CORPORATION. 
'P' ALL RIGHTS RESERVED.
'P'     
.RETURN
.;;
.;; Create SYCND.MAC
.;;
.SYCND:	
	.IFNDF MTI$M .SETF MTI$M
	.IFNDF TIM$IT .SETF TIM$IT
	.IFNDF SJ .SETF SJ
	.IFF MTI$M .GOTO SCND1
	.IFT TIM$IT .GOTO SCND1
	;
	; ?SYSGEN-I-Device time-out support set on
	.SETT TIM$IT
.SCND1: .IFT TIM$IT .AND .IFT SJ .SETT TIME$R
	.IFT SWIT .GOSUB CRTMAC
	.OPEN #0 'SYCND'
	.ENABLE DATA #0
.SBTTL	'SYFIL' RT-11 'PATLEV' SYSTEM CONDITIONAL FILE CREATED '<DATE>' '<TIME>'

;SYSGEN EDIT LEVEL = 'PATLEV'
;+
.DISABLE DATA #0
	.SETS P ".DATA #0 ;"
	.GOSUB COPRIT
	.DATA #0 
	.IFT GENSYS .DATA #0 SYSG$N	= 1		;Indicate sysgened monitor
	.IFF Q .GOTO G5
	.OPEN #1 'CANSF'
	.DATA #1 ; SYSGEN 'PATLEV' ANSWER FILE CREATED '<DATE>'   '<TIME>'
	.SETS P ".DATA #1 ;"
	.GOSUB COPRIT
	
	.ENABLE DATA #1
SET'BL' BL			.;Baseline monitor
SET'SJ' SJ			.;Single job monitor
SET'FB' FB			.;Foreground/Background monitor
SET'XM' XM			.;Extended memory monitor
SET'FBXM' FBXM		.;FB or XM
SET'XMONLY' XMONLY		.;XM only
SET'CTS' CTS		.;CTS-300 SYSGEN
SET'PROCTS' PROCTS		.;Professional CTS-300 SYSGEN
.DISABLE DATA #1
.G5:
	.SETS ARG "TIM$IT,Device time out"
	.GOSUB SET
	.SETS ARG "TIME$R,SJ timer support"
	.GOSUB SET
	.SETS ARG "RDF$L,System I/O error messages,GENIF0"
	.GOSUB SET
	.SETS ARG "SYT$K,System job support"
	.GOSUB SET
	.SETS ARG "SPC$PS,Save/set main-line PC and PS support"
	.GOSUB SET
	.SETS ARG "SCCA$G,Global SCCA support"
	.GOSUB SET
	.SETS ARG "MTT$Y,Multiterminal support"
	.GOSUB SET
	.IFF MTT$Y .GOTO G8
	.SETS ARG "MAT$S,Asynchronous terminal status"
	.GOSUB SET
	.SETS ARG "MTI$M,Terminal time out"
	.GOSUB SET
.G8:
	.SETS ARG "XM$FET,.FETCH support under XM"
	.GOSUB SET

	.IFNDF TTYOUT .GOTO G10
	.SETS COM "Size of the output buffers"
	.DATA #0 TTYOUT  = 'TTYOUT'.		;'COM'
	.IFT Q .DATA #1 SETN TTYOUT 'TTYOUT'.		.;'COM'

.G10:	.IFNDF TTYIN .GOTO G20
	.SETS COM "Size of the input buffers"
	.DATA #0 TTYIN   = 'TTYIN'.		;'COM'
	.IFT Q .DATA #1 SETN TTYIN 'TTYIN'.		.;'COM'
.G20:

	.SETS ARG "ROL$OV,Month rollover support"
	.GOSUB SET

	.SETS ARG "U$CL,User command linkage"
	.GOSUB SET

	.SETS ARG "HSR$B,High speed ring buffer support"
	.GOSUB SET

	.SETS ARG "U$TIL,Utility commands,GENIF0"
	.GOSUB SET

	.SETS ARG "L$ANG,Language commands,GENIF0"
	.GOSUB SET

	.SETS ARG "M$INI,Minimal commands,GENIF0"
	.GOSUB SET

	.IFNDF CLOCK .GOTO G30
	.SETS COM "Power line frequency"
	.DATA #0 CLOCK	= 'CLOCK'.		;'COM'
	.IFT Q .DATA #1 SETN CLOCK 'CLOCK'.		.;'COM'

.G30:
	.SETS ARG "RTE$M,RTEM-11 Support"
	.GOSUB SET

	.SETS ARG "KW11$P,Use KW11$P clock as system clock"
	.GOSUB SET

	.SETS ARG "STAR$T,Startup command file"
	.GOSUB SET

	.SETS ARG "FPU$11,Floating point support"
	.GOSUB SET

	.SETS ARG "MPT$Y,Memory parity support"
	.GOSUB SET

	.SETS ARG "PWF$L,Power fail"
	.GOSUB SET

	.SETS ARG "BATC$H,Batch support"
	.GOSUB SET

	.SETS ARG "ERL$G,Error log support"
	.GOSUB SET

	.IFNDF ERL$G .SETF ERL$G
	.IFF ERL$G .GOTO G40
	.SETS COM "Number of units to be logged"
	.DATA #0 ERL$U	= 'ERL$U'.		;'COM'
	.IFT Q .DATA #1 SETN ERL$U 'ERL$U'.		.;'COM'
.G40:
	.IFF Q .GOTO G45
	
	.SETN CNT 1
.G43:
	.SETS DCOM DCM'CNT'[1:2]
	.TEST DCM'CNT'
	.SETS DC DCM'CNT'[5:'<STRLEN>']
	.IF DCOM NE "DZ" .GOTO G431
	.IFT 'DCOM' .DATA #1 SETT PCDZ		.;'DC'
	.IFF 'DCOM' .DATA #1 SETF PCDZ		.;'DC'
	.GOTO G432
.G431:	.IFT 'DCOM' .DATA #1 SETT 'DCOM'			.;'DC'
	.IFF 'DCOM' .DATA #1 SETF 'DCOM'			.;'DC'
.G432:	.INC CNT
	.IF CNT LE RTDEVS  .GOTO G43

	.SETN UDEVNO 1
.G435:
	.IFNDF UD'UDEVNO' .GOTO G44
	.SETS TEMPS UD'UDEVNO'
	.DATA #1 SETS UD'UDEVNO' "'TEMPS'"		.;User supplied handler
	.INC UDEVNO
	.GOTO G435
.G44:
	.IFNDF LPNUM .SETN LPNUM 0
	.SETS TEMPS "CTS-300 Line printer"
	.SETS TEMPSP "Number of CTS-300 Printers"
.ENABLE DATA #1
SET'GRAFX' GRAFX		.;Graphics
SET'LPP' LPP		.;'TEMPS'
SET'LQP' LQP		.;'TEMPS'
SET'LRP' LRP		.;'TEMPS'
SET'LSP' LSP		.;'TEMPS'
SET'LPS' LPS		.;'TEMPS'
SET'LQS' LQS		.;'TEMPS'
SET'LRS' LRS		.;'TEMPS'
SET'LSS' LSS		.;'TEMPS'
SETN LPNUM 'LPNUM'		.;'TEMPSP'

.DISABLE DATA

	.SETS TEMPS "Status register for CTS-300 printer"
	.SETS TEMPSP "Vector for CTS-300 printer"

	.IFNDF LPPCSR .GOTO G44A
.ENABLE DATA #1
SETN LPPCSR 'LPPCSR'	.;'TEMPS'
.DISABLE DATA
.G44A:
	.IFNDF LPPVEC .GOTO G44B
.ENABLE DATA #1 
SETN LPPVEC 'LPPVEC'		.;'TEMPSP'
.DISABLE DATA
.G44B:
	.IFNDF LQPCSR .GOTO G44C
.ENABLE DATA #1 
SETN LQPCSR 'LQPCSR'	.;'TEMPS'
.DISABLE DATA
.G44C:
	.IFNDF LQPVEC .GOTO G44D
.ENABLE DATA #1 
SETN LQPVEC 'LQPVEC'		.;'TEMPSP'
.DISABLE DATA
.G44D:
	.IFNDF LRPCSR .GOTO G44E
.ENABLE DATA #1 
SETN LRPCSR 'LRPCSR'	.;'TEMPS'
.DISABLE DATA
.G44E:
	.IFNDF LRPVEC .GOTO G44F
.ENABLE DATA #1 
SETN LRPVEC 'LRPVEC'		.;'TEMPSP'
.DISABLE DATA
.G44F:
	.IFNDF LSPCSR .GOTO G44G
.ENABLE DATA #1 
SETN LSPCSR 'LSPCSR'	.;'TEMPS'
.DISABLE DATA
.G44G:
	.IFNDF LSPVEC .GOTO G44H
.ENABLE DATA #1 
SETN LSPVEC 'LSPVEC'		.;'TEMPSP'
.DISABLE DATA
.G44H:
	.IFNDF LPSCSR .GOTO G44I
.ENABLE DATA #1 
SETN LPSCSR 'LPSCSR'	.;'TEMPS'
.DISABLE DATA
.G44I:
	.IFNDF LPSVEC .GOTO G44J
.ENABLE DATA #1 
SETN LPSVEC 'LPSVEC'		.;'TEMPSP'
.DISABLE DATA
.G44J:
	.IFNDF LQSCSR .GOTO G44K
.ENABLE DATA #1 
SETN LQSCSR 'LQSCSR'	.;'TEMPS'
.DISABLE DATA
.G44K:
	.IFNDF LQSVEC .GOTO G44L
.ENABLE DATA #1 
SETN LQSVEC 'LQSVEC'		.;'TEMPSP'
.DISABLE DATA
.G44L:
	.IFNDF LRSCSR .GOTO G44M
.ENABLE DATA #1 
SETN LRSCSR 'LRSCSR'	.;'TEMPS'
.DISABLE DATA
.G44M:
	.IFNDF LRSVEC .GOTO G44N
.ENABLE DATA #1 
SETN LRSVEC 'LRSVEC'		.;'TEMPSP'
.DISABLE DATA
.G44N:
	.IFNDF LSSCSR .GOTO G44O
.ENABLE DATA #1 
SETN LSSCSR 'LSSCSR'	.;'TEMPS'
.DISABLE DATA
.G44O:
	.IFNDF LSSVEC .GOTO G45
.ENABLE DATA #1 
SETN LSSVEC 'LSSVEC'		.;'TEMPSP'
.DISABLE DATA

.G45:
	.IFF DX .GOTO G50
	.SETS ARG "DXT$O,Second RX11 controller support"
	.GOSUB SET

	.SETS COM "Status register for first RX11"
	.DATA #0 DX$CSR	= 'DX$CSR'	;'COM'
	.IFT Q .DATA #1 SETN DX$CSR 'DX$CSR'	.;'COM'

	.SETS COM "Vector for first RX11"
	.DATA #0 DX$VEC	= 'DX$VEC'		;'COM'
	.IFT Q .DATA #1 SETN DX$VEC 'DX$VEC'		.;'COM'

	.IFF DXT$O .GOTO G50
	.SETS COM "Status register for second RX11"
	.DATA #0 DX$CS2	= 'DX$CS2'	;'COM'
	.IFT Q .DATA #1 SETN DX$CS2	'DX$CS2'	.;'COM'

	.SETS COM "Vector for second RX11"
	.DATA #0 DX$VC2	= 'DX$VC2'		;'COM'
	.IFT Q .DATA #1 SETN DX$VC2 'DX$VC2'		.;'COM'

.G50:
	.IFF DY .GOTO G60
	.SETS ARG "DY$DD,RX02 double density only"
	.GOSUB SET

	.SETS ARG "DYT$O,Second RX02 controller"
	.GOSUB SET

	.SETS COM "Status register for first RX02"
	.DATA #0 DY$CSR	= 'DY$CSR'	;'COM'
	.IFT Q .DATA #1 SETN DY$CSR 'DY$CSR'	.;'COM'

	.SETS COM "Vector for first RX02"
	.DATA #0 DY$VEC	= 'DY$VEC'		;'COM'
	.IFT Q .DATA #1 SETN DY$VEC 'DY$VEC'		.;'COM'

	.IFF DYT$O .GOTO G60
	.SETS COM "Status register for second RX02"
	.DATA #0 DY$CS2	= 'DY$CS2'	;'COM'
	.IFT Q .DATA #1 SETN DY$CS2 'DY$CS2'	.;'COM'
	
	.SETS COM "Vector for second RX02"
	.DATA #0 DY$VC2	= 'DY$VC2'		;'COM'
	.IFT Q .DATA #1 SETN DY$VC2 'DY$VC2'		.;'COM'

.G60:
	.IFF DD .GOTO G70

	.SETS ARG "DDT$O,Second DECtape II controller"
	.GOSUB SET
	
	.SETS COM "Status register for first DECtape II"
	.DATA DD$CSR	= 'DD$CSR'	;'COM'
	.IFT Q .DATA #1 SETN DD$CSR 'DD$CSR'	.;'COM'
 
	.SETS COM "Vector for first DECtape II"
	.DATA #0 DD$VEC	= 'DD$VEC'		;'COM'
	.IFT Q .DATA #1 SETN DD$VEC 'DD$VEC'		.;'COM'

	.IFF DDT$O .GOTO G70
	.SETS COM "Status register for second DECtape II"
	.DATA #0 DD$CS2	= 'DD$CS2'	;'COM'
	.IFT Q .DATA #1 SETN DD$CS2 'DD$CS2'	.;'COM'

	.SETS COM "Vector for second DECtape II"
	.DATA #0 DD$VC2	= 'DD$VC2'		;'COM'
	.IFT Q .DATA #1 SETN DD$VC2 'DD$VC2'		.;'COM'	
.G70:
	.IFF RF .GOTO G80
	.SETS COM "Number of RF11 platters"
	.DATA #0 $RFNUM	= '$RFNUM'.		;'COM'
	.IFT Q .DATA #1 SETN $RFNUM '$RFNUM'.		.;'COM'	
.G80:
	.IFF DS .GOTO G85
	.SETS ARG "RJS0$3,RJS disk is RJS03,GENIF0"
	.GOSUB SET
.G85:
	.IFF DL .GOTO G90
	.SETS COM "Number of RL01/RL02 units"
	.DATA #0 DL$UN	= 'DL$UN'.		;'COM'
	.IFT Q .DATA #1 SETN DL$UN 'DL$UN'.		.;'COM'
.G90:
	.IFF DU .GOTO G95
	.SETS COM "Number of MSCP ports"
	.DATA #0 DU$POR	= 'DU$POR'		;'COM'
	.IFT Q .DATA #1 SETN DU$POR 'DU$POR'		.;'COM'
.G91:
	.SETS COMC "Status register for "
	.SETS COMV "Vector of "
	.SETS COM2 " MSCP port"
	.DATA #0 DU$CSR = 'DU$CSR'		;'COMC''C1''COM2'
	.DATA #0 DU$VEC = 'DU$VEC'		;'COMV''C1''COM2'
	.IFF Q .GOTO G911
	.DATA #1 SETN DU$CSR 'DU$CSR'	.;'COMC''C1''COM2'
	.DATA #1 SETN DU$VEC 'DU$VEC'		.;'COMV''C1''COM2'
  
.G911:	.IF DU$POR EQ 1 .GOTO G999
	.DATA #0 DU$CS1 = 'DU$CS1'		;'COMC''C2''COM2'
	.DATA #0 DU$VC1 = 'DU$VC1'		;'COMV''C2''COM2'
	.IFF Q .GOTO G912
	.DATA #1 SETN DU$CS1 'DU$CS1'	.;'COMC''C2''COM2'
	.DATA #1 SETN DU$VC1 'DU$VC1'		.;'COMV''C2''COM2'
.G912:	.IF DU$POR EQ 2 .GOTO G998
	.DATA #0 DU$CS2 = 'DU$CS2'		;'COMC''C2''COM2'
	.DATA #0 DU$VC2 = 'DU$VC2'		;'COMV''C2''COM2'
	.IFF Q .GOTO G993
	.DATA #1 SETN DU$CS2 'DU$CS2'	.;'COMC''C3''COM2'
	.DATA #1 SETN DU$VC2 'DU$VC2'		.;'COMV''C3''COM2'
.G993:	.IF DU$POR EQ 3 .GOTO G998
	.DATA #0 DU$CS3 = 'DU$CS3'		;'COMC''C4''COM2'
	.DATA #0 DU$VC3 = 'DU$VC3'		;'COMV''C4''COM2'
	.IFF Q .GOTO G998
	.DATA #1 SETN DU$CS3 'DU$CS3'	.;'COMC''C4''COM2'
	.DATA #1 SETN DU$VC3 'DU$VC3'		.;'COMV''C4''COM2'

.G998:	.SETS ARG "DU$BOO,MSCP multiple port booting"
	.GOSUB SET
.G999:	.IFF XM .GOTO G95
	.SETS ARG "DU$BBR,MSCP Bad Block Replacement"
	.GOSUB SET

.G95:
	.IFF SP .GOTO G96
	.SETS ARG "SP$FLG,Spool banner page support"
	.GOSUB SET
.G96:
	.IFF DP .GOTO G100
	.SETS ARG "RP0$3,RP11 disk is RP03,GENIF0"
	.GOSUB SET
.G100:
	.IFF MT .GOTO G110
	.SETS ARG "MT$FSM,TM11 file-structured support"
	.GOSUB SET
	.SETS COM "Number of TM11 units"
	.DATA #0 MT$UN	= 'MT$UN'.		;'COM'
	.IFT Q .DATA #1 SETN MT$UN 'MT$UN'.		.;'COM'
.G110:
	.IFF MM .GOTO G120
	.SETS ARG "MM$FSM,TJU16 file-structured support"
	.GOSUB SET
	.SETS COM "Number of TJU16 units"
	.DATA #0 MM$UN 	= 'MM$UN'.		;'COM'
	.IFT Q .DATA #1 SETN MM$UN 'MM$UN'.		.;'COM'
.G120:

	.SETS COMC "Status register of "
	.SETS COMV "Vector of "

	.IFF MS .GOTO G129
	.SETS ARG "MS$FSM,TS11 file structured support"
	.GOSUB SET
	.SETS COM "Number of TS11 units"
	.DATA #0 MS$UN	= 'MS$UN'.		;'COM'
	.IFT Q .DATA #1 SETN MS$UN 'MS$UN'.		.;'COM'

	.DATA #0 MS$CSR	= 'MS$CSR'	;'COMC''C1' TS11
	.DATA #0 MS$VEC	= 'MS$VEC'		;'COMV''C1' TS11
	.IFF Q .GOTO G121
	.DATA #1 SETN MS$CSR 'MS$CSR'	.;'COMC''C1' TS11
	.DATA #1 SETN MS$VEC 'MS$VEC'   	.;'COMV''C1' TS11
.G121:	.IF MS$UN EQ 1 .GOTO G129
	.DATA #0 MS$CS1	= 'MS$CS1'	;'COMC''C2' TS11
	.DATA #0 MS$VC1	= 'MS$VC1'		;'COMV''C2' TS11
	.IFF Q .GOTO G122
	.DATA #1 SETN MS$CS1 'MS$CS1'	.;'COMC''C2' TS11
	.DATA #1 SETN MS$VC1 'MS$VC1'		.;'COMV''C2' TS11
.G122:	.IF MS$UN EQ 2 .GOTO G129
	.DATA #0 MS$CS2	= 'MS$CS2'	;'COMC''C3' TS11
	.DATA #0 MS$VC2	= 'MS$VC2'		;'COMV''C3' TS11
	.IFF Q .GOTO G123
	.DATA #1 SETN MS$CS2 'MS$CS2'	.;'COMC''C3' TS11
	.DATA #1 SETN MS$VC2 'MS$VC2'		.;'COMV''C3' TS11
.G123:	.IF MS$UN EQ 3 .GOTO G129
	.DATA #0 MS$CS3	= 'MS$CS3'	;'COMC''C4' TS11
	.DATA #0 MS$VC3	= 'MS$VC3'		;'COMV''C4' TS11
	.IFF Q .GOTO G124
	.DATA #1 SETN MS$CS3 'MS$CS3'	.;'COMC''C4' TS11
	.DATA #1 SETN MS$VC3 'MS$VC3'		.;'COMV''C4' TS11
.G124:	.IF MS$UN EQ 4 .GOTO G129
	.DATA #0 MS$CS4	= 'MS$CS4'	;'COMC''C5' TS11
	.DATA #0 MS$VC4	= 'MS$VC4'		;'COMV''C5' TS11
	.IFF Q .GOTO G125
	.DATA #1 SETN MS$CS4 'MS$CS4'	.;'COMC''C5' TS11
	.DATA #1 SETN MS$VC4 'MS$VC4'		.;'COMV''C5' TS11
.G125:	.IF MS$UN EQ 5 .GOTO G129
	.DATA #0 MS$CS5	= 'MS$CS5'	;'COMC''C6' TS11
	.DATA #0 MS$VC5	= 'MS$VC5'		;'COMV''C6' TS11
	.IFF Q .GOTO G126
	.DATA #1 SETN MS$CS5 'MS$CS5'	.;'COMC''C6' TS11
	.DATA #1 SETN MS$VC5 'MS$VC5'		.;'COMV''C6' TS11
.G126:	.IF MS$UN EQ 6 .GOTO G129
	.DATA #0 MS$CS6	= 'MS$CS6'	;'COMC''C7' TS11
	.DATA #0 MS$VC6	= 'MS$VC6'		;'COMV''C7' TS11
	.IFF Q .GOTO G127
	.DATA #1 SETN MS$CS6 'MS$CS6'	.;'COMC''C7' TS11
	.DATA #1 SETN MS$VC6 'MS$VC6'		.;'COMV''C7' TS11
.G127:	.IF MS$UN EQ 7 .GOTO G129
	.DATA #0 MS$CS7	= 'MS$CS7'	;'COMC''C10' TS11
	.DATA #0 MS$VC7	= 'MS$VC7'		;'COMV''C10' TS11
	.IFF Q .GOTO G129
	.DATA #1 SETN MS$CS7 'MS$CS7'	.;'COMC''C10' TS11
	.DATA #1 SETN MS$VC7 'MS$VC7'		.;'COMV''C10' TS11

.G129:
	.IFF MU .GOTO G130
	.SETS ARG "MU$FSM,TMSCP Magtape Class Handler Support"
	.GOSUB SET
	.SETS COM "Number of TMSCP Magtape units"
	.DATA #0 MU$UN 	= 'MU$UN'.		;'COM'
	.IFT Q .DATA #1 SETN MU$UN 'MU$UN'.		.;'COM'

	.DATA #0 MU$CSR	= 'MU$CSR'	;'COMC''C1' MSCP Tape
	.DATA #0 MU$VEC	= 'MU$VEC'		;'COMV''C1' MSCP Tape
	.IFF Q .GOTO G129A
	.DATA #1 SETN MU$CSR 'MU$CSR'	.;'COMC''C1' MSCP Tape
	.DATA #1 SETN MU$VEC 'MU$VEC'   	.;'COMV''C1' MSCP Tape
.G129A:	.IF MU$UN EQ 1 .GOTO G130
	.DATA #0 MU$CS2	= 'MU$CS2'	;'COMC''C2' MSCP Tape
	.DATA #0 MU$VC2	= 'MU$VC2'		;'COMV''C2' MSCP Tape
	.IFF Q .GOTO G129B
	.DATA #1 SETN MU$CS2 'MU$CS2'	.;'COMC''C2' MSCP Tape
	.DATA #1 SETN MU$VC2 'MU$VC2'		.;'COMV''C2' MSCP Tape
.G129B:	.IF MU$UN EQ 2 .GOTO G130
	.DATA #0 MU$CS3	= 'MU$CS3'	;'COMC''C3' MSCP Tape
	.DATA #0 MU$VC3	= 'MU$VC3'		;'COMV''C3' MSCP Tape
	.IFF Q .GOTO G129C
	.DATA #1 SETN MU$CS3 'MU$CS3'	.;'COMC''C3' MSCP Tape
	.DATA #1 SETN MU$VC3 'MU$VC3'		.;'COMV''C3' MSCP Tape
.G129C:	.IF MU$UN EQ 3 .GOTO G130
	.DATA #0 MU$CS4	= 'MU$CS4'	;'COMC''C4' MSCP Tape
	.DATA #0 MU$VC4	= 'MU$VC4'		;'COMV''C4' MSCP Tape
	.IFF Q .GOTO G130
	.DATA #1 SETN MU$CS4 'MU$CS4'	.;'COMC''C4' MSCP Tape
	.DATA #1 SETN MU$VC4 'MU$VC4'		.;'COMV''C4' MSCP Tape
.G130: 
	.IFF XL .GOTO G135
	.DATA #0 XL$CSR	= 'XL$CSR'	;XL CSR
	.DATA #0 XL$VEC	= 'XL$VEC'		;XL Vector
	.IFF Q .GOTO G135
	.DATA #1 SETN XL$CSR 'XL$CSR'	.;XL CSR
	.DATA #1 SETN XL$VEC 'XL$VEC'		.;XL Vector
.G135:
	.IFF NQ .GOTO G139
	.DATA #0 NQ$CSR	= 'NQ$CSR'	;NQX CSR
	.DATA #0 NQ$VEC	= 'NQ$VEC'		;NQX Vector
	.IFF Q .GOTO G139
	.DATA #1 SETN NQ$CSR 'NQ$CSR'	.;NQX CSR
	.DATA #1 SETN NQ$VEC 'NQ$VEC'		.;NQX Vector
.G139:
	.IFT CTS .IFF PROCTS .GOTO G150
	.SETS ARG "LS$PC,LS PC300 support"
	.GOSUB SET
	.IFF LP .GOTO G140
	.IFNDF LP$CSR .GOTO G140
	.DATA #0 LP$CSR	= 'LP$CSR'	;Line printer CSR
	.DATA #0 LP$VEC	= 'LP$VEC'		;Line printer vector
	.IFF Q .GOTO G140
	.DATA #1 SETN LP$CSR 'LP$CSR'	.;Line printer CSR
	.DATA #1 SETN LP$VEC 'LP$VEC'		.;Line printer vector
.G140:
	.IFF LS .GOTO G150
	.IFNDF LS$CSR .GOTO G150
	.DATA #0 LS$CSR	= 'LS$CSR'	;Serial LP CSR
	.DATA #0 LS$VEC	= 'LS$VEC'		;Vector for serial LP
	.IFF Q .GOTO G150
	.DATA #1 SETN LS$CSR 'LS$CSR'	.;Serial LP CSR
	.DATA #1 SETN LS$VEC 'LS$VEC'		.;Serial LP CSR
.G150:
	.IFT PC .OR .IFT PR .DATA #0 PR11$X	= 0		;PC11 or PR11 reader/punch
	
	.IFF GRAFX .GOTO G160
	.SETS ARG "VS60$,VS60 display support"
	.GOSUB SET

	.SETS ARG "VT11$,VT11 display support"
	.GOSUB SET

	.DATA #0 VT.CSR	= 'GRFC'		;CSR for VT11/VS60
	.DATA #0 VT.VEC	= 'GRFV'		;Vector for VT11/VS60
	.IFF Q .GOTO G160
	.DATA #1 SETN GRFC 'GRFC'	.;CSR for VT11/VS60
	.DATA #1 SETN GRFV 'GRFV'	.;Vector for VT11/VS60
.G160:
	.IFT Q .DATA #1 SETN EMPTY 'EMPTY'.		.;Empty device slots

	.SETN UPNO 1
.G161:
	.IFNDF UP'UPNO' .GOTO G200
	.SETS TEMPS UP'UPNO'
	.DATA #0 'TEMPS'
	.IFT Q .DATA #1 SETS UP'UPNO' "'TEMPS'"
	.INC UPNO
	.GOTO G161
.G200:
.;;
.;; Do SYCND.MAC and answer file for multiterminal
.;;
	.IFF MTT$Y .GOTO G400

	.SETS COM "Number of local DL11 interfaces"
	.DATA #0 DL11$L	= 'DLNUM'.		;'COM'
	.IFT Q .DATA #1 SETN DLNUM 'DLNUM'.		.;'COM'

	.SETS COM "Number of remote DL11-E lines"
	.DATA #0 DL11$M	= 'DLMDM'.		;'COM'
	.IFT Q .DATA #1 SETN DLMDM 'DLMDM'.		.;'COM'

	.SETN DL11$N DLNUM+DLMDM
	.SETS COM "Total number of DL11 lines"
	.DATA #0 DL11$N	= 'DL11$N'.		;'COM'
	.IFT Q .DATA #1 SETN DL11$N	'DL11$N'.	.;'COM'

	.DATA #0 DLC$0	= 'DLC$0'	;'COMC''C1' DL11 (Console)
	.DATA #0 DLV$0	= 'DLV$0'		;'COMV''C1' DL11 (Console)
	.IFF Q .GOTO G221
	.DATA #1 SETN DLC$0 'DLC$0'	.;'COMC''C1' DL11 
	.DATA #1 SETN DLV$0 'DLV$0'   	.;'COMV''C1' DL11 
.G221:	.IF DL11$N EQ 1 .GOTO G230
	.DATA #0 DLC$1	= 'DLC$1'	;'COMC''C2' DL11 
	.DATA #0 DLV$1	= 'DLV$1'		;'COMV''C2' DL11 
	.IFF Q .GOTO G222
	.DATA #1 SETN DLC$1 'DLC$1'	.;'COMC''C2' DL11 
	.DATA #1 SETN DLV$1 'DLV$1'		.;'COMC''C2' DL11 
.G222:	.IF DL11$N EQ 2 .GOTO G230
	.DATA #0 DLC$2	= 'DLC$2'	;'COMC''C3' DL11 
	.DATA #0 DLV$2	= 'DLV$2'		;'COMV''C3' DL11 
	.IFF Q .GOTO G223
	.DATA #1 SETN DLC$2 'DLC$2'	.;'COMC''C3' DL11 
	.DATA #1 SETN DLV$2 'DLV$2'		.;'COMC''C3' DL11 
.G223:	.IF DL11$N EQ 3 .GOTO G230
	.DATA #0 DLC$3	= 'DLC$3'	;'COMC''C4' DL11
	.DATA #0 DLV$3	= 'DLV$3'		;'COMV''C4' DL11
	.IFF Q .GOTO G224
	.DATA #1 SETN DLC$3 'DLC$3'	.;'COMC''C4' DL11
	.DATA #1 SETN DLV$3 'DLV$3'		.;'COMV''C4' DL11
.G224:	.IF DL11$N EQ 4 .GOTO G230
	.DATA #0 DLC$4	= 'DLC$4'	;'COMC''C5' DL11
	.DATA #0 DLV$4	= 'DLV$4'		;'COMV''C5' DL11
	.IFF Q .GOTO G225
	.DATA #1 SETN DLC$4 'DLC$4'	.;'COMC''C5' DL11
	.DATA #1 SETN DLV$4 'DLV$4'		.;'COMV''C5' DL11
.G225:	.IF DL11$N EQ 5 .GOTO G230
	.DATA #0 DLC$5	= 'DLC$5'	;'COMC''C6' DL11
	.DATA #0 DLV$5	= 'DLV$5'		;'COMV''C6' DL11
	.IFF Q .GOTO G226
	.DATA #1 SETN DLC$5 'DLC$5'	.;'COMC''C6' DL11
	.DATA #1 SETN DLV$5 'DLV$5'		.;'COMV''C6' DL11
.G226:	.IF DL11$N EQ 6 .GOTO G230
	.DATA #0 DLC$6	= 'DLC$6'	;'COMC''C7' DL11
	.DATA #0 DLV$6	= 'DLV$6'		;'COMV''C7' DL11
	.IFF Q .GOTO G227
	.DATA #1 SETN DLC$6 'DLC$6'	.;'COMC''C7' DL11
	.DATA #1 SETN DLV$6 'DLV$6'		.;'COMV''C7' DL11
.G227:	.IF DL11$N EQ 7 .GOTO G230
	.DATA #0 DLC$7	= 'DLC$7'	;'COMC''C10' DL11
	.DATA #0 DLV$7	= 'DLV$7'		;'COMV''C10' DL11
	.IFF Q .GOTO G230
	.DATA #1 SETN DLC$7 'DLC$7'	.;'COMC''C10' DL11
	.DATA #1 SETN DLV$7 'DLV$7'		.;'COMV''C10' DL11
.G230:
	.IFT Q .DATA #1 SET'DZM' DZ			.;DZ11 or DZ11V multiplexers
	.SETS COM "Number of DZ11 or DZ11V multiplexers"
	.DATA #0 DZ11$N	= 'DZ11$N'.		;'COM'
	.IFT Q .DATA #1 SETN DZ11$N 'DZ11$N'		.;'COM'

	.IFF DZM .GOTO G400

	.SETS COM "Number of Local lines"
	.DATA #0 DZ11$L	= 'DZ11$L'.		;'COM'
	.IFT Q .DATA #1 SETN DZ11$L 'DZ11$L'.		.;'COM'

	.SETS COM "Number of Remote lines"
	.DATA #0 DZ11$M	= 'DZ11$M'.		;'COM'
	.IFT Q .DATA #1 SETN DZ11$M 'DZ11$M'.		.;'COM'

	.SETS ARG "DZV$11,DZV11 multiplexer support"
	.GOSUB SET
	.IFF DZV$11 .DATA #0 DZV$11	= 0		;DZ11 multiplexer support
	.DATA #0 DZCS$0	= 'DZCS$0'	;'COMC''C1' DZ11
	.DATA #0 DZVC$0	= 'DZVC$0'		;'COMV''C1' DZ11
	.IFF Q .GOTO G321
	.DATA #1 SETN DZCS$0 'DZCS$0'	.;'COMC''C1' DZ11
	.DATA #1 SETN DZVC$0 'DZVC$0'   	.;'COMV''C1' DZ11 
.G321:	.IF DZ11$N EQ 1 .GOTO G330
	.DATA #0 DZCS$1	= 'DZCS$1'	;'COMC''C2' DZ11
	.DATA #0 DZVC$1	= 'DZVC$1'		;'COMV''C2' DZ11
	.IFF Q .GOTO G322
	.DATA #1 SETN DZCS$1 'DZCS$1'	.;'COMC''C2' DZ11
	.DATA #1 SETN DZVC$1 'DZVC$1'		.;'COMC''C2' DZ11
.G322:	.IF DZ11$N EQ 2 .GOTO G330
	.DATA #0 DZCS$2	= 'DZCS$2'	;'COMC''C3' DZV11
	.DATA #0 DZVC$2	= 'DZVC$2'		;'COMV''C3' DZV11
	.IFF Q .GOTO G323
	.DATA #1 SETN DZCS$2 'DZCS$2'	.;'COMC''C3' DZV11
	.DATA #1 SETN DZVC$2 'DZVC$2'		.;'COMC''C3' DZV11
.G323:	.IF DZ11$N EQ 3 .GOTO G330
	.DATA #0 DZCS$3	= 'DZCS$3'	;'COMC''C4' DZV11
	.DATA #0 DZVC$3	= 'DZVC$3'		;'COMV''C4' DZV11
	.IFF Q .GOTO G330
	.DATA #1 SETN DZCS$3 'DZCS$3'	.;'COMC''C4' DZV11
	.DATA #1 SETN DZVC$3 'DZVC$3'		.;'COMV''C4' DZV11
.G330:	
	.DATA #0 DZSP$D	= 'DZSP$D'		;Baud rate
	.IFT Q .DATA #1 SETN DZSP$D 'DZSP$D'	.;Baud rate
	.DATA #0 DZST$P	= 'DZST$P'		;Stop unit
	.IFT Q .DATA #1 SETN DZST$P 'DZST$P'	.;Stop unit
.G400:
	.CLOSE #0
	.CLOSE #1
	
	.GOTO BUILD
.;;SET: This procedure generates a TRUE/FALSE conditional to SYCND.MAC.
.;;	 It also generates a line to the answer file.
.;;	Input:
.;;	  A character string to be parsed, in the format:
.;;	    "COND,COM,GENFL"
.;;	      where
.;;		CNDL is the name of the conditional
.;;		COM  is the comment to be used if the CNDL is TRUE
.;;		GENFL, if defined -> gen a line to SYCND even if CNDL = 0

.SET:
	.PARSE ARG "," CNDL COM GENFL 
	.IFNDF 'CNDL' .RETURN
	.IFT 'CNDL' .DATA #0 'CNDL'	= 1		;'COM'
	.IFF 'CNDL' .IF GENFL NE "" .DATA #0 'CNDL'	= 0		;'COM'

	.;;Now do the answer file
	.IFF Q .GOTO SETT99
	.IFF 'CNDL' .GOTO SETT1
	.DATA #1 SETT 'CNDL'		.;'COM'
	.GOTO SETT99
.SETT1:.DATA #1 SETF 'CNDL'		.;No 'COM'
.SETT99:.RETURN
.;;
.;; Get devices for MONBLD
.;;
.BUILD:	
	.SETS DOUT$ <SYDISK>+"'<SYUNIT>'"
	.SETS DMAP$ DOUT$
	.SETS DIN$ <SYDISK>
	.IF <SYDISK> <> "DW" .SETS DIN$ DIN$+"1"
	.IF <SYDISK> = "DW" .SETS DIN$ DIN$+"0"
	.SETS OUT$ DOUT$
	.SETS MAP$ DMAP$
	.SETS IN$ DIN$
	.IF <SYUNIT> EQ 1 .SETS IN$ <SYDISK>+"0"
	;
	;
	; 'STARS'
	;	DEVICE ASSIGNMENTS AND SYSGEN CLEANUP
	; 'STARS'
.PHSRC:	
	.SETT SAV
	.SETT KEEPWK
	.IFT NOQ .GOTO SYBLD
	.DISABLE LOWERCASE
	;
	.ASKS [0:3:DIN$] IN$ What is the name of the source input device [xxn] ('DIN$')?
	.IFF <ESCAPE> .GOTO PHCK1
	.GOSUB PHHLP
	.GOTO PHSRC
.PHCK1:	.SETS DEV IN$
.PHOUT:
	;
	.ASKS [0:3:DOUT$] OUT$ What is the name of the binary output device [xxn] ('DOUT$')?
	.IFF <ESCAPE> .GOTO PHCK2
	.GOSUB PHHLP
	.GOTO PHOUT
.PHCK2:	.SETS DEV OUT$
.PHMAP:
	;
	.ASKS [0:3:DMAP$] MAP$ What is the name of the map output device [xxn] ('DMAP$')?
	.IFF <ESCAPE> .GOTO PHCK3
	.GOSUB PHHLP
	.GOTO PHMAP
.PHCK3:	.SETS DEV MAP$
	.ENABLE LOWERCASE
.OBJS:	
	.SETF SAV
	.IFT PROCTS .SETT KEEPWK
	.IFT CTS .GOTO SYBLD
	;
	.ASK [<TRUE>] SAV Do you want to retain the system OBJs (Y)?
	.IFF <ESCAPE> .GOTO DELWK
	;
	; RETAIN SYSTEM OBJS:
	; The  indirect  command  files  that  the SYSGEN program generates
	; delete  the  object modules (from which the system is built) when
	; the object modules are no longer needed.  This measure serves  to
	; conserve disk space while the system is being built. However, the
	; object  modules are often useful later when you patch the system.
	; If your output device has sufficient free space, you can elect to
	; retain all system object modules for future use.
	.GOTO OBJS
.DELWK:
	;
	.ASK [<TRUE>] KEEPWK Do you want to retain the work files (Y)?
	.IFF <ESCAPE> .GOTO SYBLD
	;
	; RETAIN SYSGEN WORK FILES:
	; SYSGEN  creates  five files which are used for the system builds.
	; These  are  the 3 indirect command files ('SYSBLD', 'MONBLD',
	; and 'DEVBLD'), and the 2 source conditional files ('SYCND'
	; and 'DEVTBL').  If you wish to have these files deleted after
	; the system  build  procedure,  'SYSBLD',  is  run, type "N" and
	; these work files will not be retained.
	.GOTO DELWK
.PHHLP:
	;
        ; SYSTEM BUILD:
	; The SYSGEN assembling and linking process requires a source input
	; device  and  a  binary output device, as well as an output device
	; for monitor link maps.  The name  you  specify  can  be  either a
	; physical or logical name (for example, RK1, DP4, BLD, etc.).  For
	; more explanation, see the RT-11 SYSTEM GENERATION GUIDE.
	.RETURN	 
.;;
.;; Create SYSBLD
.;;
.SYBLD:
	.OPEN #3 'SYSBLD'
	.IF <FILERR> EQ 1 .GOTO S10
	;
	; ?SYSGEN-F-Error creating 'SYSBLD'
	.EXIT 4
.S10:
	.ENABLE DATA #3
!SYSGEN EDIT LEVEL = 'PATLEV'
!	'SYSBLD' CREATED '<DATE>'  '<TIME>'
.DISABLE DATA
	.SETS P ".DATA #3 !"
	.GOSUB COPRIT
	.DATA #3 	.DATA #3 $@'MONBLD'
	.DATA #3 $@'DEVBLD'
	.IFF KEEPWK .DATA #3 DEL/NOQUERY ('SYCND','DEVTBL','MONBLD','DEVBLD','SYSBLD')
	.CLOSE #3
.;;
.;; Create MONBLD
.;;
.MNBLD:
	.SETS INDWRN "!DO NOT RUN THIS FILE THROUGH IND.  TO EXECUTE THIS FILE TYPE: $@"
	.SETF BSF
	.IFT BL .OR .IFT SJ .OR .IFT FB .SETT BSF
	.SETF TAPE
	.IFT MT .SETT TAPE
	.IFT MM .SETT TAPE
	.IFT MS .SETT TAPE
	.IFT MU .SETT TAPE
	.SETF FSM
	.IFT MT$FSM .OR .IFT MM$FSM .OR .IFT MS$FSM .OR .IFT MU$FSM .SETT FSM
	.SETT DEL
	.IFT SAV .SETF DEL
	.OPEN #3 'MONBLD'
	.IF <FILERR> EQ 1 .GOTO M10
	;
	; ?SYSGEN-F-Error creating 'MONBLD'
	.EXIT 4
.M10:
	.SETS MTT ""
	.SETS MAC "MACRO/OBJ:OBJ:"
	.SETS L "/CROSS/LIST:LST:"
	.SETS SYC "+'SYFIL'+EDTGBL+"
	.SETS TRMTBL ""
	.IFT MTT$Y .SETS TRMTBL "+TRMTBL"
	.ENABLE DATA #3
!SYSGEN EDIT LEVEL = 'PATLEV'
!       'MONBLD' CREATED  '<DATE>'  '<TIME>'
.DISABLE DATA
	.SETS P ".DATA #3 !"
	.GOSUB COPRIT
	.ENABLE DATA #3
!'STARS'
'INDWRN''MONBLD'
!'STARS'
.DISABLE DATA
	.IFT NOQ .GOTO M15
	.ENABLE DATA #3
ASSIGN 'IN$' SRC
ASSIGN 'OUT$' BIN
ASSIGN 'MAP$' MAP
ASSIGN 'OUT$' OBJ
.DISABLE DATA #3
.M15:	.IFF BL .GOTO M20
	.IFF LST .DATA #3 'MAC'KMBL SRC:(SJ'SYC'KMON+KMOVLY)
	.IFT LST .DATA #3 'MAC'KMBL'L'KMBL SRC:(SJ'SYC'KMON+KMOVLY)
	.IFF LST .DATA #3 'MAC'RMBL SRC:(SJ'SYC'USR+RMONSJ)
	.IFT LST .DATA #3 'MAC'RMBL'L'RMBL SRC:(SJ'SYC'USR+RMONSJ)
	.IFF LST .DATA #3 'MAC'TBBL SRC:(SJ'SYC''DEVFIL')
	.IFT LST .DATA #3 'MAC'TBBL'L'TBBL SRC:(SJ'SYC''DEVFIL')
	.IFF LST .DATA #3 'MAC'BTBL SRC:(SJ'SYC'BSTRAP)
	.IFT LST .DATA #3 'MAC'BTBL'L'BTBL SRC:(SJ'SYC'BSTRAP)
	.ENABLE DATA #3
LINK/EXE:BIN:RT11BL.SYG/BOU:1000/MAP:MAP:RT11BL
OBJ:(BT,RM,KM,TB)BL
OVLY0
	.DISABLE DATA #3
.IFT DEL .DATA #3 DELETE/NOQ OBJ:(BT,RM,KM,TB)BL.OBJ

.M20:	.IFF SJ .GOTO M30
	.IFF LST .DATA #3 'MAC'KMSJ SRC:(SJ'SYC'KMON+KMOVLY)
	.IFT LST .DATA #3 'MAC'KMSJ'L'KMSJ SRC:(SJ'SYC'KMON+KMOVLY)
	.IFF LST .DATA #3 'MAC'RMSJ SRC:(SJ'SYC'USR+RMONSJ)
	.IFT LST .DATA #3 'MAC'RMSJ'L'RMSJ SRC:(SJ'SYC'USR+RMONSJ)
	.IFF LST .DATA #3 'MAC'TBSJ SRC:(SJ'SYC''DEVFIL''TRMTBL')
	.IFT LST .DATA #3 'MAC'TBSJ'L'TBSJ SRC:(SJ'SYC''DEVFIL''TRMTBL')
	.IFF LST .DATA #3 'MAC'BTSJ SRC:(SJ'SYC'BSTRAP)
	.IFT LST .DATA #3 'MAC'BTSJ'L'BTSJ SRC:(SJ'SYC'BSTRAP)

	.IFF MTT$Y .GOTO M22
	.IFF LST .DATA #3 'MAC'MESJ SRC:(SJ'SYC'MTTEMT)
	.IFT LST .DATA #3 'MAC'MESJ'L'MESJ SRC:(SJ'SYC'MTTEMT)
	.IFF LST .DATA #3 'MAC'MISJ SRC:(SJ'SYC'MTTINT)
	.IFT LST .DATA #3 'MAC'MISJ'L'MISJ SRC:(SJ'SYC'MTTINT)

	.SETS MTT ",MESJ,MISJ"
.M22:
	.ENABLE DATA #3
LINK/EXE:BIN:RT11SJ.SYG/BOU:1000/PROMPT/MAP:MAP:RT11SJ OBJ:BTSJ
OBJ:RMSJ,KMSJ'MTT',TBSJ//
OVLY0
	.DISABLE DATA #3
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:(BT,RM,KM,TB)SJ.OBJ
	.IFT DEL .IFT MTT$Y .DATA #3 DELETE/NOQ OBJ:(ME,MI)SJ.OBJ
.M30:	
	.IFF FB .GOTO M40
	.IFF LST .DATA #3 'MAC'KMFB SRC:(FB'SYC'KMON+KMOVLY)
	.IFT LST .DATA #3 'MAC'KMFB'L'KMFB SRC:(FB'SYC'KMON+KMOVLY)
	.IFF LST .DATA #3 'MAC'RMFB SRC:(FB'SYC'USR+RMONFB)
	.IFT LST .DATA #3 'MAC'RMFB'L'RMFB SRC:(FB'SYC'USR+RMONFB)
	.IFF LST .DATA #3 'MAC'TBFB SRC:(FB'SYC''DEVFIL''TRMTBL')
	.IFT LST .DATA #3 'MAC'TBFB'L'TBFB SRC:(FB'SYC''DEVFIL''TRMTBL')
	.IFF LST .DATA #3 'MAC'BTFB SRC:(FB'SYC'BSTRAP)
	.IFT LST .DATA #3 'MAC'BTFB'L'BTFB SRC:(FB'SYC'BSTRAP)

	.IFF MTT$Y .GOTO M32
	.SETS MTT ",MEFB,MIFB"
	.IFF LST .DATA #3 'MAC'MEFB SRC:(FB'SYC'MTTEMT)
	.IFT LST .DATA #3 'MAC'MEFB'L'MEFB SRC:(FB'SYC'MTTEMT)
	.IFF LST .DATA #3 'MAC'MIFB SRC:(FB'SYC'MTTINT)
	.IFT LST .DATA #3 'MAC'MIFB'L'MIFB SRC:(FB'SYC'MTTINT)
.M32:
	.ENABLE DATA #3
LINK/EXE:BIN:RT11FB.SYG/BOU:1000/PROMPT/MAP:MAP:RT11FB OBJ:BTFB
OBJ:RMFB,KMFB'MTT',TBFB//
OVLY0
	.DISABLE DATA #3
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:(BT,RM,TB,KM)FB.OBJ
	.IFT DEL .IFT MTT$Y .DATA #3 DELETE/NOQ OBJ:(MI,ME)FB.OBJ
.M40:
	.IFF XM .GOTO M50
	.IFF LST .DATA #3 'MAC'KMXM SRC:(XM'SYC'KMON+KMOVLY)
	.IFT LST .DATA #3 'MAC'KMXM'L'KMXM SRC:(XM'SYC'KMON+KMOVLY)
	.IFF LST .DATA #3 'MAC'RMXM SRC:(XM'SYC'USR+RMONFB)
	.IFT LST .DATA #3 'MAC'RMXM'L'RMXM SRC:(XM'SYC'USR+RMONFB)
	.IFF LST .DATA #3 'MAC'SBXM SRC:(XM'SYC'XMSUBS)
	.IFT LST .DATA #3 'MAC'SBXM'L'SBXM SRC:(XM'SYC'XMSUBS)
	.IFF LST .DATA #3 'MAC'TBXM SRC:(XM'SYC''DEVFIL''TRMTBL')
	.IFT LST .DATA #3 'MAC'TBXM'L'TBXM SRC:(XM'SYC''DEVFIL''TRMTBL')
	.IFF LST .DATA #3 'MAC'BTXM SRC:(XM'SYC'BSTRAP)
	.IFT LST .DATA #3 'MAC'BTXM'L'BTXM SRC:(XM'SYC'BSTRAP)

	.IFF MTT$Y .GOTO M42
	.SETS MTT ",MEXM,MIXM"
	.IFF LST .DATA #3 'MAC'MEXM SRC:(XM'SYC'MTTEMT)
	.IFT LST .DATA #3 'MAC'MEXM'L'MEXM SRC:(XM'SYC'MTTEMT)
	.IFF LST .DATA #3 'MAC'MIXM SRC:(XM'SYC'MTTINT)
	.IFT LST .DATA #3 'MAC'MIXM'L'MIXM SRC:(XM'SYC'MTTINT)
.M42:
	.ENABLE DATA #3
LINK/EXE:BIN:RT11XM.SYG/BOU:1000/PROMPT/MAP:MAP:RT11XM OBJ:BTXM
OBJ:RMXM,SBXM,KMXM'MTT',TBXM//
OVLY0
	.DISABLE DATA #3
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:(BT,RM,SB,KM,TB)XM.OBJ
	.IFT DEL .IFT MTT$Y .DATA #3 DELETE/NOQ OBJ:(ME,MI)XM.OBJ
.M50:
	.CLOSE #3
	
.;;
.;; Create DEVBLD
.;;
.DVBLD:
	.OPEN #3 'DEVBLD'
	.GOTO D5
	.IF <FILERR> EQ 1 .GOTO D5
	;
	; ?SYSGEN-F-Error creating 'DEVBLD'
	.EXIT 4
.D5:
	.ENABLE DATA #3
!SYSGEN Edit level = 'PATLEV'
!	'DEVBLD' CREATED  '<DATE>'  '<TIME>'
.DISABLE DATA
	.SETS P ".DATA #3 !"
	.GOSUB COPRIT
	.ENABLE DATA #3
!'STARS'
'INDWRN''DEVBLD'
!'STARS'
.DISABLE DATA
	.IFT NOQ .GOTO D8
	.ENABLE DATA #3
ASSIGN 'IN$' SRC
ASSIGN 'OUT$' BIN
ASSIGN 'OUT$' OBJ
.DISABLE DATA #3
.D8:	.IFNDF BATC$H .SETF BATC$H
	.SET'BATC$H' BA
	.IFF BL .IFF SJ .GOTO D10
	.IFT MTT$Y .GOTO D10
	.SETF GEN
	.SETT NXM
	.SETT TT
	.SETS DEV "TT"
	.GOSUB DEVGEN

.D10:	.IFF ERL$G .GOTO D20
	.IFF FBXM .GOTO D15
	.IFF LST .DATA #3 'MAC'ELCOPY SRC:('SYFIL'+ELCOPY)
	.IFT LST .DATA #3 'MAC'ELCOPY'L'ELCOPY SRC:('SYFIL'+ELCOPY)
	.IFF LST .DATA #3 'MAC'ELINIT SRC:('SYFIL'+ELINIT)
	.IFT LST .DATA #3 'MAC'ELINIT'L'ELINIT SRC:('SYFIL'+ELINIT)
	.IFF LST .DATA #3 'MAC'ELTASK SRC:ELTASK
	.IFT LST .DATA #3 'MAC'ELTASK'L'ELTASK SRC:ELTASK

	.IFF LST .DATA #3 LINK/EXE:BIN:ERRLOG/FORE OBJ:(ELCOPY,ELTASK)
	.IFT LST .DATA #3 LINK/EXE:BIN:ERRLOG/FORE/MAP:LST:ERRLOG OBJ:(ELCOPY,ELTASK)
		 .DATA #3 LINK/EXE:BIN:'MAP' OBJ:ELINIT
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:(ELINIT.OBJ,ELCOPY.OBJ,ELTASK.OBJ)

.D15:
	.IFF SJ .IFF BL .GOTO D20
	.IFF LST .DATA #3 'MAC'EL SRC:('SYFIL'+EL)

	.IFT LST .DATA #3 'MAC'EL'L'EL SRC:('SYFIL'+EL)
		 .DATA #3 'LINK'EL.SYG'MAP' OBJ:EL
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:EL.OBJ

.D20:
	.SETF NXM
	.SETF GEN
	.SETS DEV "LD"
	.GOSUB DEVGEN
	.SETS DEV "BA"
	.GOSUB DEVGEN
	.SETS DEV "DX"
	.GOSUB DEVGEN
	.SETS DEV "DY"
	.GOSUB DEVGEN
	.SETS DEV "DD"
	.GOSUB DEVGEN
	.SETT NXM
	.SETS DEV "PD"
	.GOSUB DEVGEN
	.SETF NXM
	.SETS DEV "VM"
	.GOSUB DEVGEN
	.SETS DEV "DZ"
	.GOSUB DEVGEN
	.SETS DEV "DW"
	.GOSUB DEVGEN
	.SETS DEV "SP"
	.GOSUB DEVGEN
	.SETS DEV "XL"
	.GOSUB DEVGEN
	.SETS DEV "XC"
	.GOSUB DEVGEN
	.SETS DEV "DT"
	.GOSUB DEVGEN
	.SETS DEV "RF"
	.GOSUB DEVGEN
	.SETS DEV "DS"
	.GOSUB DEVGEN
	.SETS DEV "RK"
	.GOSUB DEVGEN
	.SETS DEV "DL"
	.GOSUB DEVGEN
	.SETS DEV "DU"
	.GOSUB DEVGEN
	.SETS DEV "DP"
	.GOSUB DEVGEN
	.SETS DEV "DM"
	.GOSUB DEVGEN
	.SETS DEV "NQ"
	.GOSUB DEVGEN
	.SETS DEV "NC"
	.GOSUB DEVGEN

	.IFF TAPE .GOTO D40
	.IFF FSM .GOTO D35
	.IFT BSF .IFF LST .DATA #3 'MAC'FSM SRC:('SYFIL'+FSM)
	.IFT BSF .IFT LST .DATA #3 'MAC'FSM'L'FSM SRC:('SYFIL'+FSM)
	.IFT XM .IFF LST .DATA #3 'MAC'FSMX SRC:(XM+'SYFIL'+FSM)
	.IFT XM .IFT LST .DATA #3 'MAC'FSMX'L'FSMX SRC:(XM+'SYFIL'+FSM)
.D35:
	.SETS DEV "MT"
	.SETS MAGSRC "TM"
	.GOSUB MAGGEN
	.SETS DEV "MM"
	.SETS MAGSRC "TJ"
	.GOSUB MAGGEN
	.SETS DEV "MS"
	.SETS MAGSRC "TS"
	.GOSUB MAGGEN
	.SETS DEV "MU"
	.SETS MAGSRC "TU"
	.GOSUB MAGGEN
	.IFF FSM .GOTO D40
	.IFT DEL .IFT BSF .DATA #3 DELETE/NOQ OBJ:FSM.OBJ
	.IFT DEL .IFT XM .DATA #3 DELETE/NOQ OBJ:FSMX.OBJ
.D40:
	.SETS DEV "CT"
	.GOSUB DEVGEN
	.IFT CTS .IFF PROCTS .GOTO D45
	.SETS DEV "LP"
	.GOSUB DEVGEN
	.SETS DEV "LS"
	.GOSUB DEVGEN
.D45:	.IFT PR .SETT PC
	.SETS DEV "PC"
	.GOSUB DEVGEN
	.SETS DEV "CR"
	.GOSUB DEVGEN
	.SETS DEV "NL"
	.GOSUB DEVGEN
	.SETS DEV "LPP"
	.GOSUB DVCTS
	.SETS DEV "LQP"
	.GOSUB DVCTS
	.SETS DEV "LRP"
	.GOSUB DVCTS
	.SETS DEV "LSP"
	.GOSUB DVCTS
	.SETS DEV "LPS"
	.GOSUB DVCTS
	.SETS DEV "LQS"
	.GOSUB DVCTS
	.SETS DEV "LRS"
	.GOSUB DVCTS
	.SETS DEV "LSS"
	.GOSUB DVCTS

	.SETT GEN
	.SETN UDEVNO 0
.D47:
	.INC UDEVNO
	.IFNDF UD'UDEVNO' .GOTO D50
	.IF UD'UDEVNO' EQ "" .GOTO D47
	.SETS DEV UD'UDEVNO'
	.GOSUB DEVGEN
	.GOTO D47

.D50:	.CLOSE	#3
	.GOTO DVTBL
.;; This generates statements to assemble and link a handler. (Not magtape).
.;; Input:
.;;		DEV = The name of the device, for example, "DX".
.;;		NXM = TRUE -> No XM handler
.;;		GEN = TRUE -> Generate it whether or not it was selected
.DEVGEN:
	.SETS BND ""
	.TEST DEVBND " "+DEV+" "
	.IF <STRLEN> NE 0 .SETS BND "/BOUNDARY:512."
	.SETS DEVMAC DEV
	.IFT PROCTS .IF DEV EQ "LP" .SETS DEVMAC "LS"
	.IFT GEN .GOTO DV5
	.IFF 'DEV' .GOTO DV20
.DV5:	.IFF BL .IFF SJ .IFF FB .GOTO DV10
	.IF DEV = "NQ" .OR .IF DEV = "NC" .GOTO DV10
	.IFF LST .DATA #3 'MAC''DEV' SRC:('SYFIL'+'DEVMAC')
	.IFT LST .DATA #3 'MAC''DEV''L''DEV' SRC:('SYFIL'+'DEVMAC')
	 .DATA #3 'LINK''DEV'.SYG'MAP''BND' OBJ:'DEV'
	.IF BND NE "" .DATA #3 SETOVR
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:'DEV'.OBJ
.DV10:	.IFF XM .OR .IFT NXM .GOTO DV20:
	.IFF LST .DATA #3 'MAC''DEV'X SRC:(XM+'SYFIL'+'DEVMAC')
	.IFT LST .DATA #3 'MAC''DEV'X'L''DEV'X SRC:(XM+'SYFIL'+'DEVMAC')
	.DATA #3 'LINK''DEV'X.SYG'MAP''BND' OBJ:'DEV'X
	.IF BND NE "" .DATA #3 SETOVR
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:'DEV'X.OBJ
.DV20:
	.RETURN
.;; This generates statements to assemble and link a CTS LP handler.
.;; Input:
.;;		DEV = The name of the device, for example, "LRP"

.DVCTS:
	.IFF 'DEV' .RETURN
	.SETS TEMPS DEV[3:3]
	.SETS DV DEV[1:2]
	.IFF SJ .IFF FB .GOTO CG10
	.ENABLE DATA #3
'MAC''DEV' SRC:('SYFIL'+'DEV'+L'TEMPS'.CTS)
'LINK''DV'.SYG OBJ:'DEV'
DELETE/NOQ OBJ:'DEV'.OBJ
.DISABLE DATA #3
.CG10:	.IFF XM .RETURN
	.ENABLE DATA #3
'MAC''DV'X SRC:(XM+'SYFIL'+'DEV'+L'TEMPS'.CTS)
'LINK''DV'X.SYG OBJ:'DV'X
DELETE/NOQ OBJ:'DV'X.OBJ
.DISABLE DATA #3
	.RETURN
.;; This generates statements to assemble and link a magtape handler. 
.;; Input:
.;;		DEV = The name of the device, for example, "MT".
.;;	     MAGSRC = The source file to be used, for example, "TM".	
.MAGGEN:
	.IFF 'DEV' .GOTO T20
	.IFF BL .IFF SJ .IFF FB .GOTO T10
	.IFF LST .DATA #3 'MAC''DEV' SRC:('SYFIL'+'MAGSRC')
	.IFT LST .DATA #3 'MAC''DEV''L''DEV' SRC:('SYFIL'+'MAGSRC')
	.IFT 'DEV'$FSM .DATA #3 'LINK''DEV'.SYG'MAP' OBJ:('DEV',FSM)
	.IFF 'DEV'$FSM .DATA #3 'LINK''DEV'HD.SYG'MAP' OBJ:'DEV'
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:'DEV'.OBJ
.T10:	
	.IFF XM .GOTO T20
	.IFF LST .DATA #3 'MAC''DEV'X SRC:(XM+'SYFIL'+'MAGSRC')
	.IFT LST .DATA #3 'MAC''DEV'X'L''DEV'X SRC:(XM+'SYFIL'+'MAGSRC')
	.IFT 'DEV'$FSM .DATA #3 'LINK''DEV'X.SYG'MAP' OBJ:('DEV'X,FSMX)
	.IFF 'DEV'$FSM .DATA #3 'LINK''DEV'HDX.SYG'MAP' OBJ:'DEV'X
	.IFT DEL .DATA #3 DELETE/NOQ OBJ:'DEV'X.OBJ
.T20:	
	.RETURN

.;; 
.;; Create DEVTBL.MAC
.;;
.DVTBL:
	.OPEN #0 'DEVTBL'
	.GOTO DVT10
	.IF <FILERR> EQ 1 .GOTO DVT10
	;
	;?SYSGEN-F-Error creating 'DEVTBL'
	.EXIT 4
.DVT10:
	.ENABLE DATA #0
	.TITLE	DEVTBL	SYSTEM DEVICE TABLES
;SYSGEN Edit Level = 'PATLEV'
; 'DEVFIL' - SYSTEM DEVICE TABLES	'PATLEV'
.DISABLE DATA
	.SETS P ".DATA #0 ;"
	.GOSUB COPRIT

	.ENABLE DATA #0
;+
; Define the DEVice macro, the device macro allocates sysgen dependent
; information into the various device tables.
;-

.ENABL	GBL
.MACRO DEV NAME,S
.PSECT PNAME$
$SLOT	== $SLOT +1
.IF NB NAME
.RAD50 /NAME/			;PNAME$ - DEVICE ->> NAME <<-
.IFF
.WORD	0			;PNAME$ - DEVICE ->> EMPTY <<-
.ENDC
.PSECT STAT$
.IF NB S
.WORD	S			;STAT$
.IFF
.WORD	0			;STAT$
.ENDC
.PSECT	ENTRY$
.IF NB NAME
.IF IDN NAME,BA
BA.NUM	==	2 * <$SLOT - 1>
.ENDC
.IF IDN NAME,PI
PI.NUM	==	2 * <$SLOT - 1>
.ENDC
.IF IDN NAME,TT
.IF NE BF!MTT$Y
.WORD	TTLQE			;ENTRY$ - TT ENTRY POINT
.IFF
TT.NUM	==	0
.WORD	0			;ENTRY$
.ENDC
.IFF
.IF IDN	NAME,MQ
.IF NE BF
MSGENT::.WORD	MQLQE
.IFF
.WORD	0
.ENDC
.IFF
.WORD	0
.ENDC
.ENDC
.IFF
.WORD	0			;ENTRY$
.ENDC
.PSECT	UNAM1$
.WORD	0			;UNAM1$
.PSECT	UNAM2$
.WORD	0			;UNAM2$
.IF NE BF
.PSECT	OWNER$
.WORD	0,0			;OWNER$
.ENDC
.PSECT	HSIZE$
.WORD	0
.PSECT	DVSIZ$
.WORD	0
.PSECT	DVREC$
.WORD	0			;DVREC$

.IF NE	MMG$T			;DVINT$
.IF NE  XM$FET
.PSECT	DVINT$
JSR	PC,INTPRO
.WORD	0
.ENDC	;NE XM$FET
.ENDC	;NE MMG$T

.ENDM
;+
; The following is the declaration of the system device tables.  Edit here
; to add a device to the system.  Each device is inserted using the DEV
; MACRO.  NOTE:  Monitor internal devices must be the first in the tables!
;-

$SLOT	== 0		;COUNT OF NUMBER OF DEVICES
 ;
DEV	TT,4			;MUST BE FIRST DEVICE
DEV				;MUST BE SECOND, SYSTEM DEVICE SLOT
.IF NE BF
DEV	MQ,SPECL$!42
.IF EQ RTE$M
DEV	PI
.ENDC
.ENDC

.DISABLE DATA #0

	.IFT RK .DATA #0 DEV	RK
	.IFT DL .DATA #0 DEV	DL
	.IFT DU .DATA #0 DEV	DU
	.IFT DY .DATA #0 DEV	DY
	.IFT DS .DATA #0 DEV	DS
	.IFT DM .DATA #0 DEV	DM
	.IFT RF .DATA #0 DEV	RF
	.IFT DP .DATA #0 DEV	DP
	.IFT DX .DATA #0 DEV	DX
	.IFT DT .DATA #0 DEV	DT
	.IFT PD .DATA #0 DEV	PD
	.IFT VM .DATA #0 DEV	VM
	.IFT DZ .DATA #0 DEV	DZ
	.IFT DW .DATA #0 DEV	DW
	.IFT SP .DATA #0 DEV	SP
	.IFT XL .DATA #0 DEV	XL
	.IFT XC	.DATA #0 DEV	XC
	.IFT NC	.DATA #0 DEV	NC
	.IFT NQ	.DATA #0 DEV	NQ
	.IFT DD .DATA #0 DEV	DD
	.IFT MT .DATA #0 DEV	MT
	.IFT MM .DATA #0 DEV	MM
	.IFT MS .DATA #0 DEV	MS
	.IFT MU .DATA #0 DEV	MU
	.IFT CT .DATA #0 DEV	CT

	.IFF LP .GOTO LPZ
	.IFF CTS .OR .IFT PROCTS .DATA #0 DEV	LP
.LPZ:	.IFF LS .GOTO LPZ1
	.IFF CTS .OR .IFT PROCTS .DATA #0 DEV	LS
.LPZ1:
	.IFF CTS .OR .IFT PROCTS .GOTO DT20
	.IFT LPP .DATA #0 DEV	LP
	.IFT LPS .DATA #0 DEV	LP
	.IFT LQP .DATA #0 DEV	LQ
	.IFT LQS .DATA #0 DEV	LQ
	.IFT LRP .DATA #0 DEV	LR
	.IFT LRS .DATA #0 DEV	LR
	.IFT LSP .DATA #0 DEV	LS
	.IFT LSS .DATA #0 DEV	LS
.DT20:
	.IFT PC .OR .IFT PR .DATA #0 DEV	PC
	.IFT CR .DATA #0 DEV	CR
	.IFT BATC$H .DATA #0 DEV	BA,4
	.IFT NL .DATA #0 DEV	NL

	.SETN UDEVNO 0
.DT25:
	.INC UDEVNO
	.IFNDF UD'UDEVNO' .GOTO DT40
	.SETS TEMPS UD'UDEVNO'
	.IF TEMPS EQ "" .GOTO DT25
	.DATA #0 DEV	'TEMPS'
	.GOTO DT25	

.DT40:	.ENABLE DATA #0
.IF NE	'EMPTY'.
.REPT	'EMPTY'.
DEV
.ENDR
.ENDC
.PSECT	UNAM1$
DKASSG:: .RAD50	/DK0/
SYASSG:: .RAD50	/SY0/
.PSECT	UNAM2$
.RAD50	/DK /
.RAD50	/SY /
 ;.PSECT	STAT$
 ;.WORD	0,0			;FOR MESSAGE CHANNEL
.PSECT	ENTRY$
.WORD	-1			;TABLE TERMINATOR

.IF NE	MMG$T			;Terminate XM interrupt table.
.IF NE  XM$FET
.PSECT	DVINT$
$DVITT::JSR	PC,INTPRO	;These 2 words in table save many later
.WORD	-1
.ENDC	;NE XM$FET
.ENDC	;NE MMG$T

.DISABLE DATA #0
	.IFF MTT$Y .DATA #0 .END
	.CLOSE	#0
	.OPEN SYSGEN.TMP
	.DATA TEMP DATA
	.CLOSE
	DELETE SYSGEN.TMP
	.IF <EXSTAT> EQ <SUCCES> .GOTO ENDMES
	?SYSGEN-W-Output error SYSGEN.TMP
	.EXIT 4
.ENDMES:
	;
	; To  build  an entire system, mount the source and binary volumes,
	; copy the files 'SYCND', 'DEVTBL', and the sources for any 
	; user  supplied  device  handlers  to  the source volume, and type
	; $@'SYSBLD'.  To build just the monitors, type $@'MONBLD'. To 
	; build just the device handlers, type $@'DEVBLD'.  For more 
	; information, read the RT-11 SYSTEM GENERATION GUIDE.
	;
	; END OF SYSGEN PROGRAM --
	.EXIT

                                                                                                                                                                                                                                  