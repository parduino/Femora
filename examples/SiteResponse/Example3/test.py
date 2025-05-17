# %%
gamma_w = 9.81
patm = 101 # kPa


h1 = 2.0 
G01 = 133.3
m1 = 0.5
gammaSat1 = 19.8
gammaEff1 = gammaSat1 - gamma_w


sigmav1  = (gammaEff1 *  h1/2.) # kPa
G1 = G01 * (sigmav1/patm)**m1


h2 = 6.0
G02 = 108.5
m2 = 0.5
gammaSat2 = 19.1
gammaEff2 = gammaSat2 - gamma_w
sigmav2  = (gammaEff2 *  h2/2. + h1 * gammaEff1) # kPa
G2 = G02 * (sigmav2/patm)**m2


h3 = 10.0
G03 = 130.0
m3 = 0.5
gammaSat3 = 19.9
gammaEff3 = gammaSat3 - gamma_w
sigmav3  = (gammaEff3 *  h3/2. + h1 * gammaEff1 + h2 * gammaEff2) # kPa
G3 = G03 * (sigmav3/patm)**m3



print(G1, G2, G3)


# %%
