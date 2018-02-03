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
import scipy
from scipy.signal import correlate

ranges = [2.0 , 1.0 , 0.5 , 0.2 , 0.1 , 0.05]
samplesPerObservation = 16384
currentRange = ranges[0]
nSamples = 0;

def getSuitableRange(amp):
    inputmeasurementRange = ranges[0]; #assign highest possible range 
    for id,range in enumerate(ranges): # go trough all possible ranges
        if amp  < range : #check if value id within range 
            inputmeasurementRange = range
    return inputmeasurementRange
def getChannels(ps):
    ps.runBlock()
    ps.waitReady()

    ps.runBlock()
    ps.waitReady()
    input = ps.getDataV('A', nSamples, returnOverflow=False)
    output = ps.getDataV('B', nSamples, returnOverflow=False)
    return (input,output)
def measureChannelsAutoRange(ps):
    (input,output) = getChannels(ps)
    global currentRange
    if currentRange != getSuitableRange(max(output)):
        currentRange = getSuitableRange(max(output))
        ps.setChannel('B', 'DC', currentRange, 0.0, enabled=True, BWLimited=False)
        (input,output) = getChannels(ps)

    return (input,output)


def AmpPhase(ps, freq, genAmp):
    Amp = 0.0
    Phase = 0.0

    periods = 100 # 10 periods wil be reorded

    observationPeriod = (1/freq)*periods
    period = 1/freq
    outputRange = 2.0
   

        
    sampling_interval = observationPeriod / samplesPerObservation
    (actualSamplingInterval, nSamples, maxSamples) = ps.setSamplingInterval(sampling_interval, observationPeriod)
    # enable AWG
    ps.setSigGenBuiltInSimple(offsetVoltage=0, pkToPk=genAmp, waveType="Sine", frequency=freq)
    
    #channel A is always connected to Gen, so no ampitude is 
    ps.setChannel('A', 'DC', getSuitableRange(genAmp), 0.0, enabled=True, BWLimited=False)
    ps.setChannel('B', 'DC', getSuitableRange(currentRange), 0.0, enabled=True, BWLimited=False)

    ps.setSimpleTrigger('A', 0.0, 'Rising', timeout_ms=100, enabled=True)

    (input,output) =  measureChannelsAutoRange(ps)
    
    dataTimeAxis = np.arange(nSamples)
    Amp = max(output)



    # in samples

    y_rad=np.arccos(np.dot(input,output)/(np.linalg.norm(input)*np.linalg.norm(output)))
    y_deg=y_rad*360/(2*np.pi)


    # force the phase shift to be in [-pi:pi]
    recovered_phase_shift = y_deg



    print("Frequency: " + str(freq))
    print("Amplitude: " + str(Amp))
    print("Phase: " + str(recovered_phase_shift))
    return (recovered_phase_shift,Amp) # return phase in degrees and P-P 


if __name__ == "__main__":
    print(__doc__)
    
    print("Attempting to open Picoscope 2000...")

   # ps = ps2000.PS2000()
    ps = ps2000a.PS2000a()  # Uncomment this line to use with the 2000a/2000b series

    print("Found the following picoscope:") 
    print(ps.getAllUnitInfo())
    FStart = 100
    FEnd  = 20000
    FStep = 100


    frequencies = range(FStart,FEnd,FStep)
    Phases = []
    Amplitudes = []
    lastRange = 2.0
    for freq in frequencies:
        (Phase,Amp) = AmpPhase(ps,freq,3.0)
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