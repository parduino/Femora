from femora.tools.transferFunction import TransferFunction



soil = [
    {"h": 2,  "vs": 144.2535646321813, "rho": 19.8*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    {"h": 6,  "vs": 196.2675276462639, "rho": 19.1*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
    {"h": 10, "vs": 262.5199305117452, "rho": 19.9*1000/9.81, "damping": 0.03, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
]
rock = {"vs": 8000, "rho": 2000.0, "damping": 0.00}
tf = TransferFunction(soil_profile=soil, rock=rock,f_max = 22)

f, TF ,_ = tf.compute()

import matplotlib.pyplot as plt
import numpy as np
plt.figure(figsize=(10, 5))
plt.plot(f, np.abs(TF))
plt.xlabel("Frequency (Hz)")
plt.show()



