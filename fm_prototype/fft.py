from math import sin, pi, e, sqrt
from numpy import complex64, real, imag, conj
import matplotlib.pyplot as plt
from time import time
from threading import Thread



SAMPLES_PER_SECOND = 34000


signal: list = []


timey = 0.0

time_axis = []
amplitude_axis = []
filter_response_axis = []


def get_max_k(sps: int):
    return sps / 2

x = 0
# generate the input discrete time signal
while x < 2048 * 16:
    time_axis.append(timey)
    amplitude_axis.append(sin(2 * pi * timey * 2500 + pi) + 3 * sin(2 * pi * timey * 5000) + sin(2 * pi * timey * 17000) + sin(2 * pi * timey * 7000 + pi) + sin(2 * pi * timey * 4300 + pi))
    timey += (1 / SAMPLES_PER_SECOND)
    filter_response_axis.append(1/(pi * timey))
    x+= 1

twiddles = [e ** (-2j * (pi / len(time_axis)) * index) for index in range(len(time_axis))]
time_indicies = [x for x in range(len(time_axis))]


def get_even_index_values(buffer: list[float]) -> list[float]:
    return buffer[::2]

def get_odd_index_values(buffer: list[float]) -> list[float]:
    return buffer[1::2]

def fft_iteration(buffer: list[float], length: int, stride: int) -> list[float]: # stride start as 1
    if(length == 1):
        return buffer
    else:
        even_values = get_even_index_values(buffer)
        odd_values = get_odd_index_values(buffer)

        even_fft = fft_iteration(even_values, length // 2, stride * 2)
        odd_fft = fft_iteration(odd_values, length // 2, stride * 2)
    
    reassembled = [0 for x in range(length)]

    for index in range(length // 2):
        p = even_fft[index]
        q = odd_fft[index] * (e ** (-2j * pi * index / length))

        reassembled[index] = p + q
        reassembled[index + (length // 2)] = p - q

    return reassembled

def ifft_full(buffer: list[float]): # sort of understand. You gotta follow the idft formula and apply to fft where exponent sign is flipped. Conjugate of all inputs will reverse sign of complex components
    length = len(buffer)
    rearranged = [conj(x) for x in buffer] # conjugate all inputs

    result = fft_iteration(rearranged, len(rearranged), 1)

    result_de_conj = [real(conj(x)) / length for x in result] # deconjugate all inputs and scale

    return result_de_conj


time_start = time()

bins = fft_iteration(amplitude_axis, len(amplitude_axis), 1)

magnitudes = [abs(mag) for mag in bins]

print(time() - time_start)

frequencies_axis = [k * (SAMPLES_PER_SECOND / len(time_axis)) for k in range(len(time_axis))]

# plt.plot(frequencies_axis, magnitudes)
# plt.show()


ifft = ifft_full(bins)

# plt.plot(time_axis, [real(x) for x in ifft])#ifft_full(bins))
# plt.plot(time_axis, amplitude_axis)
# plt.show()