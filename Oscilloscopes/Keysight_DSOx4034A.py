#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import socket
import numpy as np
import time

class Oscilloscope:
    def __init__(self, name='Keysight MSO-x 4054', addr='192.168.2.5:5025'):
        self.addr = addr
        self.ss = None
        self.name = name
        self.fileSuffix = '.1'
        self.connected = False
        self.cmdSuffix = '\n'

    def connect(self):
        if self.connected: return

        t = self.addr.split(':')
        hostname = t[0]
        port = int(t[1]) if len(t)>1 else 5025

        self.ss = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #init local socket handle
        self.ss.connect((hostname,port))                                 #connect to the server
        self.connected = True

    def send(self, cmd):
        ### to have costumize command string
        cmdx = bytes(cmd+self.cmdSuffix, encoding='UTF-8')
        self.ss.send(cmdx)                           #read back device ID
#         self.ss.send(cmd+self.cmdSuffix)                           #read back device ID

    def test(self, step=0):
        self.connect() 
        ss = self.ss

        self.send("*IDN?;")                           #read back device ID
        print("Instrument ID: %s"%ss.recv(128))
        if step < 1: return

        self.send(":WAVeform:PREamble?;")
        print("PREamble: %s"%ss.recv(128))
        if step < 2: return

        self.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        self.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        self.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
        Timebase_Poistion = ss.recv(128)
        print(Timebase_Poistion)
        Timebase_Poistion = float(Timebase_Poistion)

    def saveData(self,channels=[1], filename='temp1.dat'):
        ss = self.ss
        data_0 = None
        data = []
        ######### Channel i ###########
        for iChan in channels: 
            print("Start channel {0}".format(iChan))

            ### waveform
            self.send(":WAVeform:SOURce CHANnel{0:d};".format(iChan))       #Waveform source 
            ### meta data
            self.send(":WAVeform:PREamble?;")
            a = ss.recv(256) ### the data is longer than 128
            print(a)
            pre = a.split(',')

            total_point = int(pre[2])
            xInc = float(pre[4])
            xOrig = float(pre[5])
            xRef = float(pre[6])
            yInc = float(pre[7])
            yOrig = float(pre[8])
            yRef = int(float(pre[9]))

            ### get data
            self.send(":WAVeform:DATA? 1,%d;"%total_point)  #Query waveform data with start address and length

            ### There is a header with 2 words. Each data point contains 2 words. And there is a END at the end.
            n = total_point * 2 + 3
            print("n = %d"%n)                            #calculate fetching data byte number
            totalContent = ""
            totalRecved = 0
            while totalRecved < n:                      #fetch data
                onceContent = ss.recv(int(n - totalRecved))
                totalContent += onceContent
                totalRecved = len(totalContent)

            pureData = totalContent[2:-1]
            length = len(pureData)/2              #print length

            if length != total_point:
                print(iChan, 'data length:', length, 'NOT as expected', total_point)

            #store data into file
            data_i = [((ord(pureData[i*2+1])<<8)+ord(pureData[i*2])-(ord(pureData[i*2+1])&0x80)/0x80*65535 - yRef)*yInc+yOrig for i in range(length)]
            if data_0 is None: data_0 = [(i - xRef)*xInc+xOrig for i in range(length)]

            data.append(data_i)

        #### write out: basic info, t, chanI
        with open(filename,'w') as fout:
            ### X_Range,Y_Range,CH1_Offset,Timebase_Poistion
            fout.write('\n#time '+' '.join(['chan'+str(ichan) for ichan in channels]))
            for i in range(length-1):
                text = '\n{0:g} '.format(data_0[i])
                text += ' '.join(['{0:g}'.format(x[i]) for x in data])
                fout.write(text)

    def takeData(self, channels=[1], filename='temp1.dat'):
        '''Loop over channels and save data to file with name filename'''
        self.connect()
        ss = self.ss

        Timebase_scale = 0
        self.send("*IDN?;")                           #read back device ID
        print("Instrument ID: %s"%ss.recv(128))   

        debug = False
        if debug:
            self.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
            Sample_Rate = float(ss.recv(128))   
            print("Sample rate:%.1f"%Sample_Rate)
            total_point = int(Sample_Rate * X_Range)
            print(total_point)


        ### other config
        self.send(":ACQuire:TYPE NORMal;")          #data acquire type, could be AVERage | HRESolution | PEAK
        self.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        self.send(":WAVeform:FORMat WORD;")           #Waveform data format
        self.send(":WAVeform:UNSigned OFF;")           #Waveform data format
#         self.send(":WAVeform:STReaming 1;")           #Waveform streaming on

        data_0 = None
        data = []
        ######### Channel i ###########
        for iChan in channels: 
            print("Start channel {0}".format(iChan))

            ### waveform
            self.send(":WAVeform:SOURce CHANnel{0:d};".format(iChan))       #Waveform source 
            ### meta data
            self.send(":WAVeform:PREamble?;")
            aa = ss.recv(256) ### the data is longer than 128
            a = str(aa)[:-3]
            pre = a.split(',')

            total_point = int(pre[2])
            xInc = float(pre[4])
            xOrig = float(pre[5])
            xRef = float(pre[6])
            yInc = float(pre[7])
            yOrig = float(pre[8])
            yRef = int(float(pre[9]))

            ### get data
            self.send(":WAVeform:DATA?")  #Query waveform data with start address and length. No arguments needed for Keysight DSO-x 4034A


            ### There is a header with 2 words. Each data point contains 2 words. And there is a END at the end.
            totalContent = ss.recv(20)
            nStart = int(totalContent[1:3].decode()[0]) ## need to use this trick to get the length of meta data
            n = int(totalContent[2:2+nStart].decode())
            totalContent = totalContent[2+nStart:] ## remove the meta data

            print("n = %d"%n)                            #calculate fetching data byte number
            totalRecved = 0
            while totalRecved < n:                      #fetch data
                onceContent = ss.recv(int(n - totalRecved))
                totalContent += onceContent
                totalRecved = len(totalContent)

            pureData = totalContent
            length = int(len(pureData)/2)              #print length

            if length != total_point:
                print(iChan, 'data length:', length, 'NOT as expected', total_point)

            #store data into file
            data_i = [((int(pureData[i*2+1])<<8)+int(pureData[i*2])-(int(pureData[i*2+1])&0x80)/0x80*65535 - yRef)*yInc+yOrig for i in range(length)]
            if data_0 is None: data_0 = [(i - xRef)*xInc+xOrig for i in range(length)]

            data.append(data_i)

        #### write out: basic info, t, chanI
        with open(filename,'w') as fout:
            ### X_Range,Y_Range,CH1_Offset,Timebase_Poistion
            fout.write('\n#time '+' '.join(['chan'+str(ichan) for ichan in channels]))
            for i in range(length-1):
                text = '\n{0:g} '.format(data_0[i])
                text += ' '.join(['{0:g}'.format(x[i]) for x in data])
                fout.write(text)

    def testMore(self):
        '''Loop over channels and save data to file with name filename'''
        self.connect()
        ss = self.ss

        Timebase_scale = 0
        self.send("*IDN?;")                           #read back device ID
        print("Instrument ID: %s"%ss.recv(128))   

        self.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        self.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        self.send(":WAVeform:FORMat WORD;")           #Waveform data format
        self.send(":WAVeform:STReaming 1;")           #Waveform streaming on

        for i in range(10):
            ss.send(":SINGle;")
            self.saveData([3],'test_data_{0:d}.dat'.format(i))
            ss.send(":RUN;")

def test1():
    oc1 = Oscilloscope('Agilent MSO9104A',addr='192.168.2.6:5025')
#     oc1.testMore()
#     oc1.test(0)
    oc1.takeData([1])

if __name__ == '__main__':
    test1()
