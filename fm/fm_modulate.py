import numpy as np
import matplotlib.pyplot as plt


SAMPLES_P_SECOND = 10
time_axis = np.arange(0, 100, 1/10)

#print(time_axis)

center_frequency = 10
pi_2 = 2 * np.pi

MODULATION_INDEX = 2

def modulating_signal(x: float):
    return np.sin(x)

output = []

discrete_integral = 0
for time in time_axis:
    discrete_integral += modulating_signal(time) * (1 / SAMPLES_P_SECOND)
    freq_component = pi_2 * center_frequency * time
    phase_component = pi_2 * MODULATION_INDEX * discrete_integral
    
    output.append(np.cos(freq_component + phase_component))
    
plt.plot(time_axis, np.asarray(output))
plt.show()