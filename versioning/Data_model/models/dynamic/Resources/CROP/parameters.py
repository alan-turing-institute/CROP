# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 10:35:04 2021

@author: rmw61
"""
deltaT = 600

# Calibration parameters

ACH = 4.
ias = 0.3

# Constants
g = 9.81
nu = 15.1e-6
lam = 0.025
cd_c = 7932.5
R = 8.314
atm = 1.013e5
M_w = 0.018
M_a = 0.029
H_fg = 2437000.
c_i = 1003.2
T_k = 273.15
N_A = 6.02214e+23
heat_phot = 3.6368e-19
Le = 0.819

# Geometry
A_c = 147.
A_f = 120.
A_p = 184.
A_m = A_p
V = 175.
l_f = 0.15
AF_g = 0.31
A_v = AF_g*A_p
A_l = 63.
l_m = 0.01

# Vegetation
c_v = 3500.
msd_v = 1.212
LAI = 2.
#LAI = 0.5 # to test

# Critical dimensions
d_c = 2.0
d_f = 1.3
d_v = 0.1
d_m = 0.1
d_p = 1.

# View Factors
F_c_f = 0.6875
F_f_c = (2.6-1.)/2.6
F_c_v = AF_g/3.2
F_c_m = (1.-AF_g)/3.2
F_c_l = 0.
F_l_c = 0.125
F_l_v = 0.25
F_l_m = 0.25
F_l_p = 0.375
F_p_f = 0.25
F_p_v = 0.75*AF_g
F_p_m = 0.75*(1-AF_g)
F_p_l = 0.
F_v_c = 0.125
F_v_p = 3./8.
F_v_m = 0.5
F_v_l = 0.
F_m_c = (1.-AF_g)/4.
F_m_p = (1.-AF_g)*3./4.
F_m_v = AF_g
F_m_l = 0.
F_f_p = 1./2.6

# Emissivity/Reflectivity
eps_c = 0.9
eps_f = 0.9
eps_v = 0.9
eps_m = 0.95
eps_p = 0.95
eps_l = 1.
rho_c = 0.1
rho_f = 0.1
rho_v = 0.1
rho_m = 0.05
rho_p = 0.05
rho_l = 0.

# Conduction
lam_c = [0.03, 55.0, 1.1, 1.41, 1.41, 1.41]
lam_f = 0.8
lam_p = 0.25
l_c = [0.005, 0.02, 0.05, 0.15, 0.3, 0.6]
l_f = 0.15
c_c = [1670., 456., 880., 1200., 1200., 1200.]
c_f = 302400.
c_p = 12525.
rhod_c = [950., 7920., 2400., 1800., 1800., 1800.]
#rho_fl = 2400

T_ss = 14. + T_k
#T_fl = 17. + T_k

# Ventilation

# Lights
P_al = 7680.*2.
f_heat = 0.5
f_light = 1-f_heat
P_ambient_al = 500.
T_al = 25.+T_k

# Dehumification heat input
P_dh = 700
#P_dh = 0 # to test

# Moisture
dsat = 0.5
c_m = 17104.*dsat+304.*(1-dsat)
#dehumidify = 2*1.9/V







#dict = {'g':g, 'd_c':d_c, 'd_f':d_f, 'nu':nu, 'ias':ias, 'A_c':A_c, 'A_f':A_f, 'V':V, 'lam':lam,
#        'cd_c':cd_c, 'R':R, 'atm':atm, 'M_w':M_w, 'M_a':M_a, 'H_fg':H_fg, 'c_i':c_i, 'c_f':c_f}

#np.save('parameters.npy',dict)
