from math import sin, pi, e, sqrt
from numpy import complex64, real, imag
import matplotlib.pyplot as plt
from time import time

SAMPLES_PER_SECOND = 34500


signal: list = []


timey = 0.0

time_axis = []
amplitude_axis = []


def get_max_k(sps: int):
    return sps / 2

x = 0
# generate the input discrete time signal
while x < 4096:
    time_axis.append(timey)
    amplitude_axis.append(sin(2 * pi * timey * 1000 + pi) + 3 * sin(2 * pi * timey * 5000) + sin(2 * pi * timey * 17000) + sin(2 * pi * timey * 7000 + pi))
    timey += (1 / SAMPLES_PER_SECOND)
    x+=1


# dft

frequency_bins = []
N = len(time_axis)

time_start = time()

for k in range(len(time_axis)):
    frequency_contribution = 0
    for n in range(N):
        amplitude_value = amplitude_axis[n]
        frequency_contribution += amplitude_value * (e ** (-2j * pi * k * n / N))
    frequency_bins.append(frequency_contribution) 

#print(time.time() - start)
frequencies_real = [abs(frequency) for frequency in frequency_bins]
print(time() - time_start)

frequencies = [k * (SAMPLES_PER_SECOND / N) for k in range(N)]

# plt.plot(frequencies, frequencies_real)
# plt.show()

#idft
# reassembled = []
# start = time.time()
# for k in range(len(time_axis)):
#     time_domain_value = 0
#     for n in range(N):
#         amplitude_value = frequency_bins[n]
#         time_domain_value += amplitude_value * (e ** (2j * pi * k * n / N))
#     reassembled.append(time_domain_value) 

# reassembled = [real(value) / N for value in reassembled] # amplitude is only the real component. Imaginary component is phase
# print(time.time() - start)

# plt.plot(time_axis, reassembled)
# plt.plot(time_axis, amplitude_axis)
# plt.show()
