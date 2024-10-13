from math import pi, sin, cos, atan2
from generate_signal import generate_signal_sin
import matplotlib.pyplot as plt
from numpy import convolve


def convolver(convolved, convolving, x_axis_len, time_step):
    summation = 0
    resultant_vector = [0 for x in range(x_axis_len)]

    convolved_vector =  [convolved(x * time_step) for x in range(x_axis_len)]
    convolving_vector = [0 for x in range(x_axis_len)] + [convolving(x * time_step) for x in range(x_axis_len)]

    # (f * g)[n] = sum(f[k]g[n-k])
    for index in range(len(resultant_vector)):
        for inner_index, value in enumerate(convolved_vector):
            summation += value * convolving_vector[index - inner_index]
        resultant_vector[index] = summation
        summation = 0

    return resultant_vector

def hilbert_kernel(time):
    if(time == 0):
        return 0
    return 1 / (pi * time)


time_axis, mag_axis = generate_signal_sin(500, 0.1, 1)
hilbert = convolver(lambda x: sin(2 * pi * x), hilbert_kernel, 500, 0.1)
hilbert_2 = convolve(mag_axis, [hilbert_kernel(index * 0.1) for index in range(500)])

phase = [0 for x in range(len(time_axis))]

for index, (real_value, imaginary_value) in enumerate(zip(mag_axis, hilbert)):
    phase[index] = atan2(imaginary_value, real_value)

plt.plot(time_axis, mag_axis)
plt.plot(time_axis, hilbert)
plt.plot(time_axis, hilbert_2[499:])
plt.show()