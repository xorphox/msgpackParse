import tkinter as tk
import binascii

class Names:
    str16 = ['Str16', 'Bin16']

    def getStr16(x):
        return Names.str16[x & 1]

class parser:
    def curCh(self):
        return self.inStr[self.idx]
    
    def isEnd(self):
        return self.idx >= len(self.inStr)

    def isTrunc(self):
        return self.idx > len(self.inStr)

    def getIndent(self):
        if self.indentBypass:
            self.indentBypass = False
            return ''
        return '  '*self.indent

    def getInt8(self):
        ret = self.curCh()
        self.idx += 1
        if self.isTrunc():
            return None
        return ret
        
    def getInt16(self):
        start = self.idx
        self.idx += 2
        if self.isTrunc():
            return None
        ret = int.from_bytes(self.inStr[start:self.idx], "big")
        return ret
    
    def getInt32(self):
        start = self.idx
        self.idx += 4
        if self.isTrunc():
            return None
        ret = int.from_bytes(self.inStr[start:self.idx], "big")
        return ret

    def getInt64(self):
        start = self.idx
        self.idx += 8
        if self.isTrunc():
            return None
        ret = int.from_bytes(self.inStr[start:self.idx], "big")
        return ret

    def processMap(self, outBox, count):
        outBox.insert(tk.END, self.getIndent() + 'Map({0})\n'.format(count))
        self.indent += 1
        for x in range(count*2):
            if self.isEnd():
                return
            outBox.insert(tk.END, self.getIndent() + '[{0}.{1}] '.format(int(x / 2), x % 2))
            self.indentBypass = True
            self.process(outBox)
        self.indent -= 1

    def xPfixint(self, outBox):
        val = self.inStr[self.idx]
        self.idx += 1
        outBox.insert(tk.END, self.getIndent() + 'Int0 {0}\n'.format(val))

    def xFixmap(self, outBox):
        count = self.curCh() - 0x80
        self.idx += 1
        self.processMap(outBox, count)

    def xFixarray(self, outBox):
        count = self.curCh() - 0x90
        outBox.insert(tk.END, self.getIndent() + 'List({0})\n'.format(count))
        self.idx += 1
        self.indent += 1
        for x in range(count):
            if self.isEnd():
                return
            outBox.insert(tk.END, self.getIndent() + '[{0}] '.format(x))
            self.indentBypass = True
            self.process(outBox)
        self.indent -= 1
        
    def xInv(self, outBox):
        outBox.insert(tk.END, self.getIndent() + f"Invalid {self.curCh():#0{4}x}\n")
        self.idx += 1
        
    def xNil(self, outBox):
        outBox.insert(tk.END, self.getIndent() + 'Nil\n')
        self.idx += 1

    def xFalse(self, outBox):
        outBox.insert(tk.END, self.getIndent() + 'False\n')
        self.idx += 1

    def xTrue(self, outBox):
        outBox.insert(tk.END, self.getIndent() + 'True\n')
        self.idx += 1
        
    def xStr8(self, outBox):
        name = Names.getStr16(self.curCh())
        self.idx += 1
        count = self.getInt8()
        if count is None or (count != 0 and self.isEnd()):
            outBox.insert(tk.END, self.getIndent() + '{0}8 Truncated\n'.format(name))
            return
        start = self.idx
        if count == 0:
            T = 'Invalid'
        else:
            start += 1
            T = self.curCh()
        self.idx += count
        if self.isTrunc():
            outBox.insert(tk.END, self.getIndent() + '{0}8 Truncated Text\n'.format(name))
            return
        outBox.insert(tk.END, self.getIndent() + '{0}8({1}) type {2} "{3}"\n'.format(name, count, T, self.inStr[start:self.idx].decode('utf-8').replace('\x00', '\x01')))

    def xStr16(self, outBox):
        name = Names.getStr16(self.curCh())
        self.idx += 1
        count = self.getInt16()
        if count is None or (count != 0 and self.isEnd()):
            outBox.insert(tk.END, self.getIndent() + '{0}16 Truncated\n'.format(name))
            return
        start = self.idx
        if count == 0:
            T = 'Invalid'
        else:
            start += 1
            T = self.curCh()
        self.idx += count
        if self.isTrunc():
            outBox.insert(tk.END, self.getIndent() + '{0}16 Truncated Text\n'.format(name))
            return
        outBox.insert(tk.END, self.getIndent() + '{0}16({1}) type {2} "{3}"\n'.format(name, count, T, self.inStr[start:self.idx].decode('utf-8').replace('\x00', '\x01')))

    def xInt64(self, outBox):
        self.idx += 1
        val = self.getInt64()
        if val is None:
            outBox.insert(tk.END, self.getIndent() + 'Int64 Truncated\n')
            return
        outBox.insert(tk.END, self.getIndent() + 'Int64 {0} 0x{1:x}\n'.format(val, val))
        
    def xInt32(self, outBox):
        self.idx += 1
        val = self.getInt32()
        if val is None:
            outBox.insert(tk.END, self.getIndent() + 'Int32 Truncated\n')
            return
        outBox.insert(tk.END, self.getIndent() + 'Int32 {0} 0x{1:x}\n'.format(val, val))
        
    def xMap16(self, outBox):
        self.idx += 1
        count = self.getInt16()
        if count is None or (count != 0 and self.isEnd()):
            outBox.insert(tk.END, self.getIndent() + '{0} Truncated\n'.format('Map'))
            return
        self.processMap(outBox, count)

    def xExt8(self, outBox):
        self.idx += 1
        count = self.getInt8()
        if count is None:
            outBox.insert(tk.END, self.getIndent() + '{0} Truncated\n'.format('Ext8'))
            return
        extType = self.getInt8()
        if extType is None:
            outBox.insert(tk.END, self.getIndent() + '{0} Truncated\n'.format('Ext8'))
            return
        start = self.idx
        self.idx += count
        if self.isTrunc():
            outBox.insert(tk.END, self.getIndent() + '{0} Truncated\n'.format('Ext8'))
            return
        outBox.insert(tk.END, self.getIndent() + 'Ext8({0}) type 0x{1:x} {2}\n'.format(count, extType, binascii.hexlify(self.inStr[start:self.idx])))
        
    def __init__(self, inStr):
        self.inStr = inStr
        self.indent = 0
        self.indentBypass = False
        self.idx = 0
        self.table = [self.xInv]*256
        self.table[0x00:0x80] = [self.xPfixint]*0x80
        self.table[0x80:0x90] = [self.xFixmap]*0x10
        self.table[0x90:0xa0] = [self.xFixarray]*0x10
        self.table[0xc0] = self.xNil
        self.table[0xc1] = self.xFalse
        self.table[0xc2] = self.xTrue
        self.table[0xc5] = self.xStr16
        self.table[0xc7] = self.xExt8
        self.table[0xce] = self.xInt32
        self.table[0xcf] = self.xInt64
        self.table[0xd2] = self.xInt32
        self.table[0xd3] = self.xInt64
        self.table[0xd9] = self.xStr8
        self.table[0xda] = self.xStr16
        self.table[0xde] = self.xMap16
        
    def process(self, outBox):
        x = self.inStr[self.idx]
        self.table[x](outBox)
        
    def doStart(self, outBox):
        outBox['state'] = 'normal'
        outBox.delete('1.0', tk.END)
        if not self.isEnd():
            self.process(outBox)
        if not self.isEnd():
            outBox.insert(tk.END, self.getIndent() + 'Padding({0}) 0x{1}\n'.format(len(self.inStr) - self.idx, self.inStr[self.idx:].hex()))
        outBox['state'] = 'disabled'
        
top = tk.Tk()

lf = tk.Frame(top)
lf1 = tk.Frame(lf)
rf = tk.Frame(top)
inbox = tk.Text(lf1, width=80, height=60)
outbox = tk.Text(rf, width=80, height=60, wrap = "none")
outbox['state'] = 'disabled'

#inbox
inbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
S0 = tk.Scrollbar(lf1)
S0.pack(side=tk.RIGHT, fill=tk.Y)
S0.config(command=inbox.yview)
inbox.config(yscrollcommand=S0.set)

lf1.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.YES)

#button panel
lpan = tk.Frame(lf)
def doStart():
    x = inbox.get('1.0', 'end')
    y = bytes.fromhex(x)
    #print(y)
    p = parser(y)
    p.doStart(outbox)
b1 = tk.Button(lpan, text='Parse', command=doStart)
b1.pack(side=tk.LEFT)

lpan.pack(side=tk.TOP, fill=tk.X)
lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)

#outbox
outbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
S1 = tk.Scrollbar(rf)
S1.pack(side=tk.RIGHT, fill=tk.Y)
S1.config(command=outbox.yview)
outbox.config(yscrollcommand=S1.set)
rf.pack(side=tk.RIGHT, fill=tk.BOTH, expand=tk.YES)

#loop
#top.pack()
top.mainloop()
