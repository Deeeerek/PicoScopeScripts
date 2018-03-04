"""
NOTE: Must change line below to use with "A" and "B" series PS2000 models
See http://www.picotech.com/document/pdf/ps2000pg.en-10.pdf for PS2000 models:
PicoScope 2104
PicoScope 2105
PicoScope 2202
PicoScope 2203
PicoScope 2204
PicoScope 2205
PicoScope 2204A
PicoScope 2205A
See http://www.picotech.com/document/pdf/ps2000apg.en-6.pdf for PS2000A models:
PicoScope 2205 MSO
PicoScope 2206
PicoScope 2206A
PicoScope 2206B
PicoScope 2207
PicoScope 2207A
PicoScope 2208
PicoScope 2208A
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time
from picoscope import ps2000
from picoscope import ps2000a
import pylab as plt
import numpy as np
import scipy
from datetime import datetime



passes = 1 # how many times to average measurements
##
#
FStart = 100
FEnd  = 20000 # in most cases max is 1MHz
FStep = 100
AWGAmp = 3.0 # 3V0 pk-pk, max is 4V0
saveFile = True
oscilloscopeType = "A" #if you have oscilloscope, that uses B type communications, change it to "B"
#
##



class BodePlot():

    def __init__(self,OscilloscopeType = "A", printFunction = print):
    
        printFunction("Attempting to open Picoscope 2000...")
                                                                                     
        if oscilloscopeType == "A":
            self.ps = ps2000a.PS2000a()  # Uncomment this line to use with the 2000a/2000b series
        elif oscilloscopeType == "B":
            self.ps = ps2000.PS2000()
        else:
            printFunction("You must choose proper communication type")
        
        if oscilloscopeType == "A" or oscilloscopeType == "B":
            printFunction("Found the following picoscope:") 
            printFunction(self.ps.getAllUnitInfo())
            self.ranges = [2.0 , 1.0 , 0.5 , 0.2 , 0.1 , 0.05] # oscilloscope ranges available form measurement
            self.connected = True
            self.samplesPerObservation = 16384
            self.currentRange = self.ranges[0] 
            self.nSamples = 0 

    def getSuitableRange(self,amp):
        inputmeasurementRange = self.ranges[0]; #assign highest possible range 
        for id,range in enumerate(self.ranges): #go trough all possible ranges
            if range > amp : #check if value is within range 
                inputmeasurementRange = range
        return inputmeasurementRange
    def getChannels(self):
        self.ps.runBlock()
        self.ps.waitReady()

        self.ps.runBlock()
        self.ps.waitReady()
        input = self.ps.getDataV('A', self.nSamples, returnOverflow=False)
        output = self.ps.getDataV('B', self.nSamples, returnOverflow=False)
        return (input,output)
    def measureChannelsAutoRange(self):
        (input,output) = self.getChannels()
        self.currentRange
        self.currentRange = self.getSuitableRange(max(output))
        self.ps.setChannel('B', 'DC', self.currentRange, 0.0, enabled=True, BWLimited=False)
        (input,output) = self.getChannels()

        return (input,output)
    def AmpPhase(self,freq, genAmp):
        Amp = 0.0
        Phase = 0.0

        periods = 10 # 10 periods wil be reorded

        observationPeriod = (1/freq)*periods
        period = 1/freq
        outputRange = 2.0
   

        
        sampling_interval = observationPeriod / self.samplesPerObservation
        (actualSamplingInterval, nSamples, maxSamples) = self.ps.setSamplingInterval(sampling_interval, observationPeriod)
        # enable AWG
        self.ps.setSigGenBuiltInSimple(offsetVoltage=0, pkToPk=genAmp, waveType="Sine", frequency=freq)
    
        #channel A is always connected to Gen, so no ampitude is 
        self.ps.setChannel('A', 'DC', self.getSuitableRange(genAmp), 0.0, enabled=True, BWLimited=False)
        self.ps.setChannel('B', 'DC', self.getSuitableRange(self.currentRange), 0.0, enabled=True, BWLimited=False)

        self.ps.setSimpleTrigger('A', 0.0, 'Rising', timeout_ms=100, enabled=True)

        (input,output) =  self.measureChannelsAutoRange()
    
        dataTimeAxis = np.arange(nSamples)
        Amp = max(output)



        # in samples

        y_rad=np.arccos(np.dot(input,output)/(np.linalg.norm(input)*np.linalg.norm(output)))
        y_deg=y_rad*360/(2*np.pi)


        # force the phase shift to be in [-pi:pi]
        recovered_phase_shift = y_deg



        printFunction("Frequency: " + str(freq))
        printFunction("Amplitude: " + str(Amp))
        printFunction("Phase: " + str(recovered_phase_shift))
        return (recovered_phase_shift,Amp) # return phase in degrees and P-P 
    def getCharacteristics(self,GenAmp, frequencies):
        Phases = []
        Amplitudes = []
        for freq in frequencies:
            (Phase,Amp) = self.AmpPhase(freq,GenAmp)
            Phases.append(Phase)
            Amplitudes.append(Amp)

        return (Amplitudes,Phases)
    def getCharacteristicsAveraged(self,GenAmp,frequencies,passes):
        
        AvgAmplitudes = [0.0] * len(frequencies);
        AvgPhases = [0.0] * len(frequencies);
        for k in range(passes):
            printFunction("Pass " + str(k) + " of " + str(passes))
            (Amplitudes,Phases) = self.getCharacteristics(AWGAmp,frequencies)
            for i in range(len(Amplitudes)):
                AvgAmplitudes[i] += Amplitudes[i] / passes
            for i in range(len(Phases)):
                AvgPhases[i] += Phases[i] / passes    
        return (AvgPhases,AvgAmplitudes)

    def __exit__(self, exc_type, exc_value, traceback):
        self.ps.stop()
        self.ps.close()


if __name__ == "__main__":
    printFunction(__doc__)
    
    plot = BodePlot(oscilloscopeType)
    
        
    if plot.connected:

        frequencies = range(FStart,FEnd,FStep)    
        (AvgPhases,AvgAmplitudes) = plot.getCharacteristicsAveraged(AWGAmp,frequencies,passes)
           
        del plot


        if saveFile == True:
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".dat"
            printFunction("Saving file as: " + filename)
            with open(filename, 'w+') as f:
                for i in range(len(AvgAmplitudes)):
                    dataToSave = str(AvgAmplitudes[i]) + " , " + str(AvgPhases[i]) + "\n"
                    f.write(dataToSave)



        plt.figure()
        plt.subplot(211)
        plt.plot(frequencies, AvgPhases, label="Phase")
        plt.grid(True, which='major')
        plt.ylabel("Degrees")
        plt.xlabel("Frequency")
        plt.legend()
        plt.subplot(212)
        plt.plot(frequencies, AvgAmplitudes, label="Amplitude")
        plt.grid(True, which='major')
        plt.ylabel("Voltage (V)")
        plt.xlabel("Frequency")
        plt.legend()
        plt.show()