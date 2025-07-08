import numpy as np

def degree_of_polarization(array, angles):
    minv = min(array)
    maxv=max(array)
    min_i = np.argmin(array)
    max_i = np.argmax(array)
    return ((maxv-minv)/(minv+maxv), angles[min_i],angles[max_i])