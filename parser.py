#!/usr/bin/env python
'''
Requirements : pyelftools capstone
Note: capstone in virtualenv has dynmaic library location misconfigured! see github aqyynh/capstone Issue #445 , Install via `pip install -I --pre --no-use-wheel capstone`
Note: this script has been only tested under version v6.3.6

Usage: python parser.py <soname>
        the so will be modified in place. 
'''
import sys
import struct
import re


from elftools.elf.elffile import ELFFile
import capstone
import capstone.x86
import capstone.arm

####decrypt function
def dword(val):
	return val & 0xffffffff

def decryptSegment(buf):
	length = len(buf)
	v20 = 0;
	resbuf = [0]*length
	v31 = struct.unpack('<I',buf[0x20:0x20+4])[0] - 0x567841C1;
	for i in range(length):
		v31 = dword(dword(dword(v31*v31) >>11) - 0x649B4A3B);
		resbuf[i] = chr((((ord(buf[i])+ (v31&0xff) )&0xff ) ^ (dword(v31*(i+1)) & 0xff) )&0xff)
	return resbuf

def getEncryptedFixByte(buf,pos,fix):
	length = len(buf)
	v20 = 0;
	resbuf = [0]*length
	v31 = struct.unpack('<I',buf[0x20:0x20+4])[0] - 0x567841C1;
	for i in range(length):
		v31 = dword(dword(dword(v31*v31) >>11) - 0x649B4A3B);
		if i == pos: 
			print "Src raw:\t0x%x\t-->\tdecrypt:0x%x"%(ord(buf[i]) ,(((ord(buf[i])+ (v31&0xff) )&0xff ) ^ (dword(v31*(i+1)) & 0xff) )&0xff )
			for test in range(256):
				if (((test+ (v31&0xff) )&0xff ) ^ (dword(v31*(i+1)) & 0xff) )&0xff  == fix:
					print "dst raw:\t0x%x\t-->\tfix:\t0x%x"%( test,fix)
					# print "get test value",hex(test)
					return chr(test),buf[i]
		resbuf[i] = chr((((ord(buf[i])+ (v31&0xff) )&0xff ) ^ (dword(v31*(i+1)) & 0xff) )&0xff)

####decrypt function end


f = open(sys.argv[1],'rb')
e = ELFFile(f)
print "Current so is under ",e.get_machine_arch()


dynamic_table = e.get_section_by_name(".dynamic")
for tags in dynamic_table.iter_tags():
	if tags["d_tag"] == 'DT_INIT':
		inittag = tags
		break
'''
union {
	dptr
	dval
}
'''
print "Entry Point : 0x%x"%(inittag["d_ptr"])

for sections in e.iter_sections():
	if sections.header["sh_offset"] <= inittag["d_ptr"] <= sections.header["sh_offset"]+ sections.header["sh_size"]:
		entrysection = sections
	if sections.header.sh_type== 'SHT_LOUSER':
		datasection = sections

entrysectiondata = entrysection.data()
encrypteddata = datasection.data()
print "LOUSER offset:0x%x"%(datasection.header.sh_offset)
#should i search firstush move and find -0x4 byte -> find the start of info
secondsegraw_offset = struct.unpack("<I",entrysectiondata[0x1c:0x1c+0x4])[0]
secondsegraw_size = struct.unpack("<I",entrysectiondata[0x1c+0x4:0x1c+0x8])[0]
secondsegraw_entry = struct.unpack("<I",entrysectiondata[0x10:0x10+0x4])[0]

print hex(secondsegraw_offset +datasection.header.sh_offset )
print hex(secondsegraw_size) 

secondsegraw = encrypteddata[secondsegraw_offset :secondsegraw_offset+secondsegraw_size ]
secondsegdecrypted = "".join(decryptSegment(secondsegraw))

jmpsize = ord(secondsegdecrypted[0])
# print "Jump additional header size:%x" %(jmpsize)

segs = struct.unpack("<I",secondsegdecrypted[3*0x4:3*0x4+0x4])[0]
#eachseginfosize = 0xc # src 0x4 dst 0x4 srcsize 0x2 dstsize 0x2
siginfostart = struct.unpack("<I",secondsegdecrypted[2*0x4:2*0x4+0x4])[0]

#x86  data in the [1] seg, code in the [2] seg  #arm  data in the [0] seg, code in the [1] seg
#but we can just find data seg [-3] for offset data seg [-2] for size
# dataseg[-6] is next entry with memoff(next's memoff)
if e.get_machine_arch() == 'x86':
	(src,dst,srcsize,dstsize) = struct.unpack("<IIHH",secondsegdecrypted[siginfostart+ 1*0xc:siginfostart+(1+1)*0xc])	
	pass
elif e.get_machine_arch() == 'ARM':
	(src,dst,srcsize,dstsize) = struct.unpack("<IIHH",secondsegdecrypted[siginfostart+ 0*0xc:siginfostart+(0+1)*0xc])
	pass
(todo_offset , todo_size)= struct.unpack("<II",secondsegdecrypted[jmpsize+src+srcsize - 3*0x4:jmpsize+src+srcsize - 0x4])
todo_entry = struct.unpack("<I",secondsegdecrypted[jmpsize+src+srcsize - 6*0x4:jmpsize+src+srcsize - (6-1 )* 0x4])[0]
print "Find val:0x%x"%(todo_offset)
print "Find val:0x%x"%(todo_size)	
print "Entry :0x%x"%(todo_entry)
todo_raw = encrypteddata[todo_offset :todo_offset+todo_size ]
todo_decrypted = "".join(decryptSegment(todo_raw))

todojmpsize = jmpsize = ord(todo_decrypted[0])
for i in range(struct.unpack("<I",todo_decrypted[3*0x4:3*0x4+0x4])[0]):
	(src,dst,srcsize,dstsize) = struct.unpack("<IIHH",todo_decrypted[struct.unpack("<I",todo_decrypted[2*0x4:2*0x4+0x4])[0]+ i*0xc:struct.unpack("<I",todo_decrypted[2*0x4:2*0x4+0x4])[0]+(i+1)*0xc])	
	if  dst <= todo_entry <= dst+dstsize:
		print "src:0x%x dst:0x%x srcsize:0x%x dstsize:0x%x"%(src,dst,srcsize,dstsize) 
		print "code in this seg"
		break

if e.get_machine_arch() == 'x86':
	cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
elif e.get_machine_arch() == 'ARM':
	cs = capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)


if e.get_machine_arch() == 'x86':
	tmp1 = re.findall('(\x55\x89\xe5.*\xe8....).*\xc9\xc3?', todo_decrypted[todojmpsize+todo_entry - (dst-src): src+srcsize+todojmpsize])[0]
	for i in cs.disasm(tmp1,todo_entry ):
		print("0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
	next_func_entry = int(i.op_str,16)
	next_func_end = todo_decrypted[next_func_entry+todojmpsize:].find('\xc3')
	print "next func entry :%x ends :%d"%(next_func_entry,next_func_end)
	next_func_text = todo_decrypted[next_func_entry - (dst-src)+todojmpsize:todojmpsize+next_func_entry + next_func_end+1]
	prev2 = None 
	prev1 = None
	for i in cs.disasm("".join(next_func_text),next_func_entry):
		print("0x%x:\t%s\t%s\t" %(i.address, i.mnemonic, i.op_str))
		if i.id == capstone.x86.X86_INS_JE and prev2.id ==capstone.x86.X86_INS_MOV and prev1.id == capstone.x86.X86_INS_CMP:
			print "Found"
			break
		prev2 = prev1
		prev1 = i
	modifytosegoffset = todojmpsize+ i.address  - (dst-src)
	print "MemAddress:%x"%(i.address)
	print "Segoffset: %x"%( modifytosegoffset)
	(newbyte,oldbyte) = getEncryptedFixByte(todo_raw, modifytosegoffset, 0xeb)
	#write back to
	modifyrawfilepos = datasection.header.sh_offset + todo_offset+modifytosegoffset
	print "Modify raw file @0x%x = 0x%x + 0x%x + 0x%x" %(modifyrawfilepos, datasection.header.sh_offset , todo_offset, modifytosegoffset)
	with open(sys.argv[1],'r+b') as wf:
		wf.seek(modifyrawfilepos)
		cmpbyte = wf.read(1)
		assert cmpbyte == oldbyte
		wf.seek(modifyrawfilepos)
		wf.write(newbyte)
	print "DONE!!!"
elif e.get_machine_arch() == 'ARM':
	#push	{fp, lr} --> bl xxx --> pop	{fp, pc}
	tmp1 = re.findall('(\x00\x48\x2d\xe9.*...\xeb).*\x00\x88\xbd\xe8?', todo_decrypted[todojmpsize+todo_entry - (dst-src): src+srcsize+todojmpsize])[0]
	for i in cs.disasm(tmp1,todo_entry ):
			print("0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str))
	next_func_entry = int(i.op_str[1:],16) #remove trailing '#'
	next_func_end = todo_decrypted[next_func_entry+todojmpsize:].find('\x00\x88\xbd\xe8')
	print "next func entry :%x ends :%d"%(next_func_entry,next_func_end)
	next_func_text = todo_decrypted[next_func_entry - (dst-src)+todojmpsize:todojmpsize+next_func_entry + next_func_end+4]
	prev1 = None
	for i in cs.disasm("".join(next_func_text),next_func_entry):
		print("0x%x:\t%s\t%s\t" %(i.address, i.mnemonic, i.op_str))
		if i.id == capstone.arm.ARM_INS_B  and prev1.id == capstone.arm.ARM_INS_CMP:
			print "Found"
			break
		prev1 = i	
	modifytosegoffset = todojmpsize+ i.address  - (dst-src) +0x3 # cause operand in th end
	print "MemAddress:%x"%(i.address)
	print "Segoffset: %x"%( modifytosegoffset)
	(newbyte,oldbyte) = getEncryptedFixByte(todo_raw, modifytosegoffset, 0xea) # beq(0a) -> b(ea)
	#write back to
	modifyrawfilepos = datasection.header.sh_offset + todo_offset+modifytosegoffset
	print "Modify raw file @0x%x = 0x%x + 0x%x + 0x%x" %(modifyrawfilepos, datasection.header.sh_offset , todo_offset, modifytosegoffset)
	with open(sys.argv[1],'r+b') as wf:
		wf.seek(modifyrawfilepos)
		cmpbyte = wf.read(1)
		assert cmpbyte == oldbyte
		wf.seek(modifyrawfilepos)
		wf.write(newbyte)
	print "DONE!!!"

'''
for x86
goto next entry  re find (push ebp mov ebp esp '\x55\x89\xe5 ..\xe8\\xoffset\xff ... \xc9\xc3' -> leave retn)
goto 
'''



