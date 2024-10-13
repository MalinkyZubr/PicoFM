from math import pi, sin


def generate_signal_sin(samples, timestep, frequency):
    time_vector = [x * timestep for x in range(samples)]
    magnitude_vector = [sin(2 * pi * frequency * time) for time in time_vector]

    return time_vector, magnitude_vector