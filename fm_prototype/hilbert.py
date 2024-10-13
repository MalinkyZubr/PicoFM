from math import pi, sin, atan2, cos
import matplotlib.pyplot as plt
from fft import fft_iteration, ifft_full, time_axis, amplitude_axis



SAMPLES_PER_SECOND = 34500
amplitude_axis = [sin(2 * pi * time) + 4 * sin(4 * pi * time) + sin(6 * pi * time) + sin(0.5 * time * pi + time) + sin(20 * time * pi + time) for time in time_axis]


def hilbert_frequency_domain(buffer: list[float]):
    n = len(buffer)
    for index in range(len(buffer) // 2):
        buffer[index] = buffer[index] * 1j
        buffer[n - 1 - index] = buffer[n - 1 - index] * -1j 
        
    return buffer
        

def hilbert_time_domain(buffer: list[float], samples_p_second: int):
    transformed = [0 for x in range(len(buffer))]
    running_sum = 0

    for index, value in enumerate(buffer):
        running_sum += value
        transformed[index] = running_sum * (1 / (2 * pi * ((index + 1) / samples_p_second)))

    return transformed

def argument_function(real_buffer: list[float], imaginary_buffer: list[float]):
    return [atan2(i_c, r_c) for r_c, i_c in zip(real_buffer, imaginary_buffer)]

def get_max_k(sps: int):
    return sps / 2


frequency_buffer = fft_iteration(amplitude_axis, len(amplitude_axis), 1)
frequency_hilbert = hilbert_frequency_domain(frequency_buffer)
hilbert_time = ifft_full(frequency_hilbert)
instantaneous_phase = argument_function(amplitude_axis, hilbert_time)

carrier_frequency = 1000
modulation_index = 20 / 1000
fm_modulated = [cos(2 * pi * carrier_frequency * time + 2 * pi * modulation_index * phase) for time, phase in zip(time_axis, instantaneous_phase)]


#plt.plot(time_axis, amplitude_axis)
plt.plot(time_axis, fm_modulated)
plt.show()


