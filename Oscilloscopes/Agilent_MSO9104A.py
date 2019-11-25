#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import socket
import subprocess
import numpy as np
hostname = "192.168.2.4"                #wire network hostname
#hostname = "10.146.73.180"              #wireless network hostname
port = 5025                             #host tcp port
#note that: every command should be termianated with a semicolon
#========================================================#
## plot waveform via gnuplot with parameters
# @param x_range x-axis range scope
# @param y_range y2-axis range scope
# @param ch1_offset channel one offset 
# @param timebase_position x-axis timebase position 
def plot(x_range,y_range,ch1_offset,timebase_position,x_unit):
   XRange = "x_var='%.5f'"%(x_range)            #xrange parameter 
   YRange = "y_var='%.3f'"%(y_range)            #yrange parameter
   CH1offset = "offset='%.3f'"%(ch1_offset)     #offset parameter
   Timebase_Position = "timebase_position='%.5f'"%(timebase_position)     #timebase position parameter
   X_Unit = "x_unit='%d'"%(x_unit)              #x-axis unit parameter
   print XRange,YRange,CH1offset,Timebase_Position,X_Unit
   subprocess.call("gnuplot -e %s -e %s -e %s -e %s -e %s keysight_oscilloscope.gp"%(XRange,YRange,CH1offset,Timebase_Position,X_Unit), shell = True)
#    subprocess.call("eps2png -resolution 400 keysight_oscilloscope.eps", shell = True)
   #subprocess.call("convert keysight_oscilloscope.eps keysight_oscilloscope.png", shell = True)
   subprocess.call("convert -flatten -density 400 -colorspace rgb keysight_oscilloscope.eps keysight_oscilloscope.png", shell = True)
   subprocess.call("xdg-open keysight_oscilloscope.png", shell = True)
   print "OK"
#========================================================#
## main function: sent oscilloscope commands and fetch data
#

def captureScreen(filename='testing.png'):
    '''Capture screen from remote PC
    Ref: https://community.keysight.com/thread/18792
    Not tested!!
    '''
    ss.send("*IDN?;")                           #read back device ID
    print "Instrument ID: %s"%ss.recv(128)   

    ss.send(":MMEM:STORE:SCR \'D:\\exa_screen.png\';*WAI")
    ss.send(":MMEM:DATA? \'D:\\exa_screen.png\'")

    owp = ss.recv(4096)
    with open(filename,'w') as f1:
        f1.write(owp)
    ss.send(":MMEM:DEL \'D:\\exa_screen.png\'")
    ss.send("*CLS")

    pass

def takeData(channels=[1],filename='temp1.dat'):
    '''Loop over channels and save data to file with name filename'''
    Timebase_scale = 0
    ss.send("*IDN?;")                           #read back device ID
    print "Instrument ID: %s"%ss.recv(128)   

    ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 

    ss.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
    Timebase_Poistion = float(ss.recv(128)[1:])
    print "Timebase_Position:%.6f"%Timebase_Poistion

    ss.send(":WAVeform:XRANge?;")               #Query X-axis range 
    X_Range = float(ss.recv(128)[1:])
    print "XRange:%g"%X_Range

    ss.send(":ACQuire:POINts:ANALog?;")         #Query analog store depth
    Sample_point = int(ss.recv(128)[1:]) - 3   
    print "Sample Point:%d"%Sample_point
    
    ss.send(":WAVeform:XUNits?;")               #Query X-axis unit 
    print "X-axis Unit:%s"%(ss.recv(128)[1:])   

    ss.send(":WAVeform:YUNits?;")               #Query Y-axis unit 
    print "Y-axis Unit:%s"%(ss.recv(128)[1:])   

    if X_Range >= 2.0:
        Xrange = np.arange(-X_Range/2.0,X_Range/2.0,X_Range*1.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion
        x_unit = 1
    elif X_Range < 2.0 and X_Range >= 0.002:
        Xrange = np.arange((-X_Range*1000)/2.0,(X_Range*1000)/2.0,X_Range*1000.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion * 1000.0
        x_unit = 2
    elif X_Range < 0.002 and X_Range >= 0.000002:
        Xrange = np.arange((-X_Range*1000000)/2.0,(X_Range*1000000)/2.0,X_Range*1000000.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion * 1000000.0
        x_unit = 3
    else:
        Xrange = np.arange((-X_Range*1000000000)/2.0,(X_Range*1000000000)/2.0,X_Range*1000000000.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion * 1000000000.0
        x_unit = 4
    #print Xrange
    #time.sleep(10)

    ss.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
    Sample_Rate = float(ss.recv(128)[1:])   
    print "Sample rate:%.1f"%Sample_Rate
    total_point = int(Sample_Rate * X_Range)
    print total_point

    ### dumpt info
#     X_Range,Y_Range,CH1_Offset,Timebase_Poistion


    ss.send(":SYSTem:HEADer OFF;")              #Query analog store depth
    ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
    ss.send(":WAVeform:FORMat WORD;")           #Waveform data format
    ss.send(":WAVeform:STReaming 1;")           #Waveform streaming on

    data = []
    ### get list of data
    for iChan in channels: 
        data_i = [0]*total_point
        ss.send(":WAVeform:SOURce CHANnel{0:d};".format(iChan))       #Waveform source 

        ## offset
        ss.send(":CHANnel{0:d}:OFFset?;".format(iChan))               #Channel1 Offset 
        CH1_Offset = float(ss.recv(128)[1:])   
        print "Channel %d Offset:%f"%(iChan, CH1_Offset)

        ### Y-range
        ss.send(":WAVeform:YRANge?;")               #Query Y-axis range
        Y_Range = float(ss.recv(128)[1:])   
        print "YRange:%f"%Y_Range
        Y_Factor = Y_Range/62712.0
        print Y_Factor

        ### get data
        ss.send(":WAVeform:DATA? 1,%d;"%total_point)         #Query waveform data with start address and length

        ### Why these magic numbers 2 and 3? A number contains 2 words? And there is a header with 3 words?
        n = total_point * 2 + 3
        print "n = %d"%n                            #calculate fetching data byte number
        totalContent = ""
        totalRecved = 0
        while totalRecved < n:                      #fetch data
            onceContent = ss.recv(int(n - totalRecved))
            totalContent += onceContent
            totalRecved = len(totalContent)
        length = len(totalContent[3:])/2              #print length
        if length != total_point:
            print iChan, 'data length:', length, 'NOT as expected', total_point

        for i in range(length):              #store data into file
            ### combine two words to form the number
            digital_number = (ord(totalContent[3+i*2+1])<<8)+ord(totalContent[3+i*2])
            if (ord(totalContent[3+i*2+1]) & 0x80) == 0x80:             
                data_i[i] = (digital_number - 65535+1000)*Y_Factor + CH1_Offset
            else:
                data_i[i] = (digital_number+1000)*Y_Factor + CH1_Offset
        data.append(data_i)

    #### write out: basic info, t, chanI
    with open(filename,'w') as fout:
        ### X_Range,Y_Range,CH1_Offset,Timebase_Poistion
        fout.write('# ')
        fout.write("\n##%/- "+"x_var='%.5f'"%(X_Range))            #xrange parameter 
        fout.write("\n##%/- "+"y_var='%.3f'"%(Y_Range))            #yrange parameter
        fout.write("\n##%/- "+"offset='%.3f'"%(CH1_Offset))     #offset parameter
        fout.write("\n##%/- "+"timebase_position='%.5f'"%(Timebase_Poistion))     #timebase position parameter
        fout.write("\n##%/- "+"x_unit='%d'"%(x_unit)) 
 
        fout.write('\n#time '+' '.join(['chan'+str(ichan) for ichan in channels]))
        for i in range(length-1):
            print i
            text = '\n{0:g} '.format(Xrange[i] + Timebase_Poistion_X)
            text += ' '.join(['{0:g}'.format(x[i]) for x in data])
            fout.write(text)

def captureWaveform():
    with open("./data_output.dat",'w') as outfile:
        Timebase_scale = 0
        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
        Timebase_Poistion = float(ss.recv(128)[1:])
        print "Timebase_Position:%.6f"%Timebase_Poistion

        ss.send(":WAVeform:XRANge?;")               #Query X-axis range 
        X_Range = float(ss.recv(128)[1:])
        print "XRange:%g"%X_Range

        ss.send(":WAVeform:YRANge?;")               #Query Y-axis range
        Y_Range = float(ss.recv(128)[1:])   
        print "YRange:%f"%Y_Range
        #Y_Factor = Y_Range/980.0
        Y_Factor = Y_Range/62712.0
        #print Y_Factor

        ss.send(":ACQuire:POINts:ANALog?;")         #Query analog store depth
        Sample_point = int(ss.recv(128)[1:]) - 3   
        print "Sample Point:%d"%Sample_point
        
        ss.send(":WAVeform:XUNits?;")               #Query X-axis unit 
        print "X-axis Unit:%s"%(ss.recv(128)[1:])   

        ss.send(":WAVeform:YUNits?;")               #Query Y-axis unit 
        print "Y-axis Unit:%s"%(ss.recv(128)[1:])   

        ss.send(":CHANnel1:OFFset?;")               #Channel1 Offset 
        CH1_Offset = float(ss.recv(128)[1:])   
        print "Channel 1 Offset:%f"%CH1_Offset
        print "X_Range:%g"%X_Range 
        if X_Range >= 2.0:
            Xrange = np.arange(-X_Range/2.0,X_Range/2.0,X_Range*1.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion
        elif X_Range < 2.0 and X_Range >= 0.002:
            Xrange = np.arange((-X_Range*1000)/2.0,(X_Range*1000)/2.0,X_Range*1000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000.0
        elif X_Range < 0.002 and X_Range >= 0.000002:
            Xrange = np.arange((-X_Range*1000000)/2.0,(X_Range*1000000)/2.0,X_Range*1000000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000000.0
        else:
            Xrange = np.arange((-X_Range*1000000000)/2.0,(X_Range*1000000000)/2.0,X_Range*1000000000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000000000.0
        #print Xrange
        #time.sleep(10)

        ss.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
        Sample_Rate = float(ss.recv(128)[1:])   
        print "Sample rate:%.1f"%Sample_Rate
        total_point = Sample_Rate * X_Range
        print total_point

        ss.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        ss.send(":WAVeform:FORMat WORD;")           #Waveform data format
        ss.send(":WAVeform:STReaming 1;")           #Waveform streaming on
        ss.send(":WAVeform:DATA? 1,%d;"%int(total_point))         #Query waveform data with start address and length

        ### Why these magic numbers 2 and 3? A number contains 2 words? And there is a header with 3 words?
        n = total_point * 2 + 3
        print "n = %d"%n                            #calculate fetching data byte number
        totalContent = ""
        totalRecved = 0
        while totalRecved < n:                      #fetch data
            #print n, (n-totalRecved)
            onceContent = ss.recv(int(n - totalRecved))
            #print len(onceContent)
            totalContent += onceContent
            totalRecved = len(totalContent)
        print len(totalContent)
        length = len(totalContent[3:])              #print length
        print length/2
        for i in xrange(length/2):              #store data into file
            ### combine two words to form the number
            digital_number = (ord(totalContent[3+i*2+1])<<8)+ord(totalContent[3+i*2])
            if (ord(totalContent[3+i*2+1]) & 0x80) == 0x80:             
                outfile.write("%f %f\n"%(Xrange[i] + Timebase_Poistion_X, (digital_number - 65535+1000)*Y_Factor + CH1_Offset))
            else:
                outfile.write("%f %f\n"%(Xrange[i] + Timebase_Poistion_X, (digital_number+1000)*Y_Factor + CH1_Offset))
    return [X_Range,Y_Range,CH1_Offset,Timebase_Poistion]             #return gnuplot parameters

def saveWaveform():
    xyrange = []
    xyrange = captureWaveform()
    print xyrange 
    if xyrange[0] >= 2.0:                                       #x-axis unit is second
        x_range = xyrange[0]*0.5    
        timebase_poistion = xyrange[3]
        x_unit = 1
    elif xyrange[0] < 2.0 and  xyrange[0] >= 0.002:             #x-axis unit is millisecond
        x_range = xyrange[0]*500
        timebase_poistion = xyrange[3] * 1000.0
        x_unit = 2
    elif xyrange[0] < 0.002 and  xyrange[0] >= 0.000002:        #x-axis unit is microsecond
        x_range = xyrange[0]*500000
        timebase_poistion = xyrange[3] * 1000000.0
        x_unit = 3
    else:                                                       #x-axis unit is nanosecond
        x_range = xyrange[0]*500000000
        timebase_poistion = xyrange[3] * 1000000000.0
        x_unit = 4
    plot(x_range,xyrange[1]*0.5,xyrange[2],timebase_poistion,x_unit)   #plot waveform using fetched data


def takeDataCmd():
    chan = [int(ic) for ic in sys.argv[1].split(',')]
    fname = 'temp.dat' if len(sys.argv)<3 else sys.argv[2]
    takeData(chan, fname)

def main1():
    ss = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #init local socket handle
    ss.connect((hostname,port))                                 #connect to the server
#     saveWaveform()
#     saveWaveform()
#     captureScreen()
#     takeData([1,2])
#     takeDataCmd()
    ss.close()
#========================================================#
## if statement
#

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
        self.ss.send(cmd+self.cmdSuffix)                           #read back device ID

    def test(self, step=0):
        self.connect() 
        ss = self.ss

        self.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)
        if step < 1: return


    def takeData(self, channels=[1], filename='temp1.dat'):
        '''Loop over channels and save data to file with name filename'''
        Timebase_scale = 0
        self.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        self.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        self.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
        Timebase_Poistion = float(ss.recv(128)[1:])
        print "Timebase_Position:%.6f"%Timebase_Poistion

        self.send(":WAVeform:XRANge?;")               #Query X-axis range 
        X_Range = float(ss.recv(128)[1:])
        print "XRange:%g"%X_Range

        self.send(":ACQuire:POINts:ANALog?;")         #Query analog store depth
        Sample_point = int(ss.recv(128)[1:]) - 3   
        print "Sample Point:%d"%Sample_point
        
        self.send(":WAVeform:XUNits?;")               #Query X-axis unit 
        print "X-axis Unit:%s"%(ss.recv(128)[1:])   

        self.send(":WAVeform:YUNits?;")               #Query Y-axis unit 
        print "Y-axis Unit:%s"%(ss.recv(128)[1:])   

        if X_Range >= 2.0:
            Xrange = np.arange(-X_Range/2.0,X_Range/2.0,X_Range*1.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion
            x_unit = 1
        elif X_Range < 2.0 and X_Range >= 0.002:
            Xrange = np.arange((-X_Range*1000)/2.0,(X_Range*1000)/2.0,X_Range*1000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000.0
            x_unit = 2
        elif X_Range < 0.002 and X_Range >= 0.000002:
            Xrange = np.arange((-X_Range*1000000)/2.0,(X_Range*1000000)/2.0,X_Range*1000000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000000.0
            x_unit = 3
        else:
            Xrange = np.arange((-X_Range*1000000000)/2.0,(X_Range*1000000000)/2.0,X_Range*1000000000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000000000.0
            x_unit = 4

        self.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
        Sample_Rate = float(ss.recv(128)[1:])   
        print "Sample rate:%.1f"%Sample_Rate
        total_point = int(Sample_Rate * X_Range)
        print total_point

        ### dumpt info
        self.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        self.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        self.send(":WAVeform:FORMat WORD;")           #Waveform data format
        self.send(":WAVeform:STReaming 1;")           #Waveform streaming on

        data = []
        ### get list of data
        for iChan in channels: 
            data_i = [0]*total_point
            self.send(":WAVeform:SOURce CHANnel{0:d};".format(iChan))       #Waveform source 

            ## offset
            self.send(":CHANnel{0:d}:OFFset?;".format(iChan))               #Channel1 Offset 
            CH1_Offset = float(ss.recv(128)[1:])   
            print "Channel %d Offset:%f"%(iChan, CH1_Offset)

            ### Y-range
            self.send(":WAVeform:YRANge?;")               #Query Y-axis range
            Y_Range = float(ss.recv(128)[1:])   
            print "YRange:%f"%Y_Range
            Y_Factor = Y_Range/62712.0
            print Y_Factor

            ### get data
            self.send(":WAVeform:DATA? 1,%d;"%total_point)         #Query waveform data with start address and length

            ### Why these magic numbers 2 and 3? A number contains 2 words? And there is a header with 3 words?
            n = total_point * 2 + 3
            print "n = %d"%n                            #calculate fetching data byte number
            totalContent = ""
            totalRecved = 0
            while totalRecved < n:                      #fetch data
                onceContent = ss.recv(int(n - totalRecved))
                totalContent += onceContent
                totalRecved = len(totalContent)
            length = len(totalContent[3:])/2              #print length
            if length != total_point:
                print iChan, 'data length:', length, 'NOT as expected', total_point

            for i in range(length):              #store data into file
                ### combine two words to form the number
                digital_number = (ord(totalContent[3+i*2+1])<<8)+ord(totalContent[3+i*2])
                if (ord(totalContent[3+i*2+1]) & 0x80) == 0x80:             
                    data_i[i] = (digital_number - 65535+1000)*Y_Factor + CH1_Offset
                else:
                    data_i[i] = (digital_number+1000)*Y_Factor + CH1_Offset
            data.append(data_i)

        #### write out: basic info, t, chanI
        with open(filename,'w') as fout:
            ### X_Range,Y_Range,CH1_Offset,Timebase_Poistion
            fout.write('# ')
            fout.write("\n##%/- "+"x_var='%.5f'"%(X_Range))            #xrange parameter 
            fout.write("\n##%/- "+"y_var='%.3f'"%(Y_Range))            #yrange parameter
            fout.write("\n##%/- "+"offset='%.3f'"%(CH1_Offset))     #offset parameter
            fout.write("\n##%/- "+"timebase_position='%.5f'"%(Timebase_Poistion))     #timebase position parameter
            fout.write("\n##%/- "+"x_unit='%d'"%(x_unit)) 
     
            fout.write('\n#time '+' '.join(['chan'+str(ichan) for ichan in channels]))
            for i in range(length-1):
                print i
                text = '\n{0:g} '.format(Xrange[i] + Timebase_Poistion_X)
                text += ' '.join(['{0:g}'.format(x[i]) for x in data])
                fout.write(text)

def test1():
    oc1 = Oscilloscope('Agilent MSO9104A',addr='192.168.2.4:5025')
    oc1.test(0)

if __name__ == '__main__':
    test1()
