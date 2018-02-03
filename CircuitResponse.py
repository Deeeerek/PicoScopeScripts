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
import peakutils

def avgDelay(input,output,minDist):
    inputPeaks = peakutils.indexes(input, thres=0.5, min_dist=minDist)
    outputPeaks = peakutils.indexes(output, thres=0.5, min_dist=minDist)

    avgDifference = 0;
    for i in range(inputPeaks.size):
        if i < outputPeaks.size:
            avgDifference +=  outputPeaks[i] - inputPeaks[i]

    return avgDifference / min([inputPeaks.size,outputPeaks.size])
def AmpPhase(ps, freq, genAmp,lastRange):
    Amp = 0.0
    Phase = 0.0

    periods = 100 # 10 periods wil be reorded

    observationPeriod = (1/freq)*periods
    period = 1/freq
    outputRange = 2.0
    ranges = [2.0 , 1.0 , 0.5 , 0.2 , 0.1 , 0.05]
    samplesPerObservation = 16384

    for idx, range in enumerate(ranges):
       
       
        
        if (range > lastRange):
            continue
        else:
            lastRange = range

        sampling_interval = observationPeriod / samplesPerObservation
        (actualSamplingInterval, nSamples, maxSamples) = ps.setSamplingInterval(sampling_interval, observationPeriod)

        # the setChannel command will chose the next largest amplitude
        channelRange = ps.setChannel('A', 'DC', range, 0.0, enabled=True, BWLimited=False)
        ps.setChannel('B', 'DC', range, 0.0, enabled=True, BWLimited=False)

        ps.setSimpleTrigger('A', 0.0, 'Rising', timeout_ms=100, enabled=True)

        ps.setSigGenBuiltInSimple(offsetVoltage=0, pkToPk=genAmp, waveType="Sine", frequency=freq)

        ps.runBlock()
        ps.waitReady()
        time.sleep(0.5)
        ps.runBlock()
        ps.waitReady()
        input = ps.getDataV('A', nSamples, returnOverflow=False)
        output = ps.getDataV('B', nSamples, returnOverflow=False)

        dataTimeAxis = np.arange(nSamples)
        Amp = max(output)

        # in samples
        timeDelay = (avgDelay(input, output, samplesPerObservation/periods*4)*(actualSamplingInterval) )
        Phase =  timeDelay/period * 360
        if max(output) > range/2 :
            break


    print("Frequency: " + str(freq))
    print("Amplitude: " + str(Amp))
    print("Phase: " + str(Phase))
    return (Phase,Amp*2,lastRange) # return phase in degrees and P-P 


if __name__ == "__main__":
    print(__doc__)

    print("Attempting to open Picoscope 2000...")

   # ps = ps2000.PS2000()
    ps = ps2000a.PS2000a()  # Uncomment this line to use with the 2000a/2000b series

    print("Found the following picoscope:")
    print(ps.getAllUnitInfo())

    frequencies = range(10000,1000000,10000)
    Phases = []
    Amplitudes = []
    lastRange = 2.0
    for freq in frequencies:
        (Phase,Amp,lastRange) = AmpPhase(ps,freq,1.2,lastRange)
        Phases.append(Phase)
        Amplitudes.append(Amp)



    ps.stop()
    ps.close()

    #Uncomment following for call to .show() to not block
    #plt.ion()
    

    plt.figure()
    plt.subplot(211)
    plt.plot(frequencies, Phases, label="Phase")
    plt.grid(True, which='major')
    plt.ylabel("Degrees")
    plt.xlabel("Frequency")
    plt.legend()
    plt.subplot(212)
    plt.plot(frequencies, Amplitudes, label="Amplitude")
    plt.grid(True, which='major')
    plt.ylabel("Voltage (V)")
    plt.xlabel("Frequency")
    plt.legend()
    plt.show()
    