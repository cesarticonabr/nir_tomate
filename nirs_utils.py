"""
Utilitarios compartilhados para os pipelines NIRS.

Inclui funcoes de pre-processamento espectral, incluindo
remocao de faixas ruidosas (recomendacao 9.2 da metodologia).
"""
import numpy as np


def snv(X):
    """Standard Normal Variate: centra e escala cada espectro."""
    return (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)


# Faixas espectrais a remover (nm): [inicio, fim]
FAIXAS_REMOVER = [
    (400,   450),   # baixa relacao sinal-ruido (extremidade detector)
    (1340,  1450),  # absorcao de agua (1o overtone O-H)
    (1850,  1950),  # absorcao de agua (combinacao O-H)
    (2450,  2500),  # baixa relacao sinal-ruido (extremidade detector)
]


def criar_mascara_comprimentos(wv, faixas=None):
    """
    Cria mascara booleana para manter apenas comprimentos de onda
    fora das faixas de remocao.

    Parameters
    ----------
    wv : np.ndarray
        Vetor de comprimentos de onda (nm).
    faixas : list of tuple, optional
        Lista de (inicio_nm, fim_nm) a remover.
        Padrao: FAIXAS_REMOVER.

    Returns
    -------
    mask : np.ndarray bool
        True para comprimentos a MANTER.
    n_removidos : int
        Numero de comprimentos removidos.
    """
    if faixas is None:
        faixas = FAIXAS_REMOVER
    mask = np.ones(len(wv), dtype=bool)
    for lo, hi in faixas:
        mask &= ~((wv >= lo) & (wv <= hi))
    return mask, (~mask).sum()


def remover_faixas(X, wv, faixas=None):
    """
    Remove faixas espectrais ruidosas de X e wv.

    Parameters
    ----------
    X : np.ndarray (n_amostras, n_comprimentos)
        Dados espectrais.
    wv : np.ndarray (n_comprimentos,)
        Comprimentos de onda.
    faixas : list of tuple, optional
        Lista de (inicio_nm, fim_nm) a remover.

    Returns
    -------
    X_filt : np.ndarray (n_amostras, n_comprimentos_filt)
        Dados filtrados.
    wv_filt : np.ndarray (n_comprimentos_filt,)
        Comprimentos de onda mantidos.
    n_removidos : int
        Quantos comprimentos foram removidos.
    """
    mask, n_rem = criar_mascara_comprimentos(wv, faixas)
    return X[:, mask], wv[mask], n_rem


def resumo_faixas(wv, faixas=None):
    """Exibe resumo das faixas removidas."""
    if faixas is None:
        faixas = FAIXAS_REMOVER
    total = len(wv)
    mask, n_rem = criar_mascara_comprimentos(wv, faixas)
    mantidos = mask.sum()
    print(f"  Comprimentos originais: {total}")
    print(f"  Comprimentos mantidos:  {mantidos} ({mantidos/total*100:.1f}%)")
    print(f"  Comprimentos removidos: {n_rem} ({n_rem/total*100:.1f}%)")
    print(f"  Faixas removidas:")
    for lo, hi in faixas:
        n_faixa = ((wv >= lo) & (wv <= hi)).sum()
        print(f"    {lo:.0f}-{hi:.0f} nm: {n_faixa} pontos")
    return mask
