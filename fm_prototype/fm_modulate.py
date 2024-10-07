import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert


SAMPLES_P_SECOND = 1000000
time_axis = np.arange(0, 100, 1/10)

#print(time_axis)

center_frequency = 10
pi_2 = 2 * np.pi

MODULATION_INDEX = (4 / pi_2) / center_frequency

def modulating_signal(x: float):
    return np.sin(4 * x) + 2 * np.cos(0.5 * x)

output = []

discrete_integral = 0
for time in time_axis:
    discrete_integral += modulating_signal(time) * (1 / SAMPLES_P_SECOND)
    freq_component = pi_2 * center_frequency * time
    phase_component = pi_2 * MODULATION_INDEX * discrete_integral
    
    output.append(np.cos(freq_component + phase_component))
    
plt.plot(time_axis, np.asarray(output))
plt.show()


# def find_slope(x1, x2, y1, y2):
#     return (y2 - y1) / (x2 - x1)

# def find_intercept(x0, y0, slope):
#     return slope * (-x0) + y0

# def get_line(x0, x1, y0, y1):
#     slope = find_slope(x0, x1, y0, y1)
#     intercept = x0, y0, slope

#     return slope, intercept

# def average(x1, x2):
#     return (x1 + x2) / 2

# def compute_avg_line(lower, upper):
#     return average(lower[0], upper[0]), average(lower[1], upper[1])

# def discrete_deriviative(x, y):
#     lower_div = get_line(x[0], x[1], y[0], y[1])
#     upper_div = get_line(x[1], x[2], y[1], y[2])

#     estimate = average(lower_div[0], upper_div[0])

#     return estimate

# def demodulate_fm(modulation_index: float, values_x: list[float], values_y: list[float], center_frequency: float) -> float:
#     derivative = discrete_deriviative(values_x, values_y)
#     return (-1 / modulation_index) * (((values_y[1] * derivative) / (pi_2 * np.sqrt(1 - values_y[1] ** 2))) + center_frequency)


analytic_signal = hilbert(output)
instantaneous_phase = np.unwrap(np.angle(analytic_signal))

# Derive instantaneous frequency from the phase
instantaneous_frequency = np.diff(instantaneous_phase) / (2.0 * np.pi * (1 / SAMPLES_P_SECOND))

# Plot the demodulated signal
plt.plot(time_axis[1:], instantaneous_frequency)
plt.show()
