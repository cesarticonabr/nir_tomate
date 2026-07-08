"""
Pipeline NIRS -> Grid search de pre-processamento espectral
(Recomendacao 9.2 da METODOLOGIAV2.docx)

Compara, para cada um dos 9 parametros de referencia, quatro combinacoes de
pre-processamento espectral -- SNV (baseline atual), SNV+Detrend,
SNV + 2a derivada Savitzky-Golay (janela=15, ordem=3) e MSC -- usando
grid search sobre o numero de componentes PLS, com a mesma validacao
GroupKFold (5 folds x 10 repeticoes, agrupada por parcela) ja usada nos
demais pipelines do projeto.
"""
import pandas as pd, numpy as np, re, time, warnings
warnings.filterwarnings('ignore')
from scipy.signal import savgol_filter
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

from nirs_utils import criar_mascara_comprimentos

t0 = time.time()
print("=" * 70)
print("GRID SEARCH DE PRE-PROCESSAMENTO ESPECTRAL (Recomendacao 9.2)")
print("=" * 70)

# ===== CARREGAR DADOS =====
espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()

amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values
X_raw = espectros[amostras].T.values

df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)', a.strip()).groups() for a in amostras],
                        columns=['T', 'R', 'F'], index=amostras)
df_meta['Parcela'] = df_meta['T'] + df_meta['R']

# --- Remocao de faixas ruidosas (Recomendacao 9.2, ja implementada) ---
mask, n_rem = criar_mascara_comprimentos(wv)
X_raw = X_raw[:, mask]
wv = wv[mask]
print(f"Comprimentos mantidos apos remocao de faixas ruidosas: {len(wv)}/{len(mask)}")


# ===== FUNCOES DE PRE-PROCESSAMENTO =====
def snv(X):
    return (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)


def detrend(X, wv):
    """Remove tendencia polinomial de 2a ordem de cada espectro (Barnes et al., 1989)."""
    Xd = np.empty_like(X)
    for i in range(X.shape[0]):
        coef = np.polyfit(wv, X[i], 2)
        Xd[i] = X[i] - np.polyval(coef, wv)
    return Xd


def msc(X, ref=None):
    """Multiplicative Scatter Correction usando o espectro medio da amostra como referencia."""
    if ref is None:
        ref = X.mean(axis=0)
    Xc = np.empty_like(X)
    for i in range(X.shape[0]):
        a, b = np.polyfit(ref, X[i], 1)
        Xc[i] = (X[i] - b) / a
    return Xc


PREPROCESSAMENTOS = {
    'SNV':               lambda X, wv: snv(X),
    'SNV+Detrend':       lambda X, wv: detrend(snv(X), wv),
    'SNV+2aDeriv(15,3)': lambda X, wv: savgol_filter(snv(X), window_length=15, polyorder=3, deriv=2, axis=1),
    'MSC':               lambda X, wv: msc(X),
}

# ===== PARAMETROS ALVO (todos os 9 da metodologia) =====
PARAMETROS = [
    ('Comp',        dest.columns[3]),
    ('Diam.Equat.', dest.columns[4]),
    ('C:D',         dest.columns[5]),
    ('Firm',        dest.columns[6]),
    ('pH',          dest.columns[7]),
    ('Vit. C',      dest.columns[8]),
    ('AT',          dest.columns[9]),
    ('SS',          dest.columns[10]),
    ('SS/AT',       dest.columns[11]),
]

gkf = GroupKFold(n_splits=5)
grupos = df_meta['Parcela']
NC_LIST = [1, 2, 3, 5, 10, 15]
N_REPEATS = 10


def classif(rpd):
    return 'Excelente' if rpd > 2.5 else 'Bom' if rpd > 2.0 else 'Razoavel' if rpd > 1.5 else 'Fraco'


def avaliar(X, y):
    """GroupKFold (5 folds x 10 repeticoes); retorna a melhor config entre NC_LIST."""
    best = {'r2': -np.inf}
    for nc in NC_LIST:
        preds, reals = [], []
        for seed in range(N_REPEATS):
            g_shuf = grupos.sample(frac=1, random_state=seed)
            for tr, te in gkf.split(X, y, g_shuf):
                pls = PLSRegression(n_components=nc)
                scaler = StandardScaler()
                pls.fit(scaler.fit_transform(X[tr]), y[tr])
                preds.extend(pls.predict(scaler.transform(X[te])).ravel())
                reals.extend(y[te])
        r2 = r2_score(reals, preds)
        rmse = np.sqrt(mean_squared_error(reals, preds))
        rpd = y.std() / rmse
        if r2 > best['r2']:
            best = {'r2': r2, 'rmse': rmse, 'rpd': rpd, 'nc': nc}
    return best


resultados = {}         # {param: {preproc: best_dict}}
melhores_globais = {}    # {param: nome_preproc_vencedor}

for param_nome, col_nome in PARAMETROS:
    print(f"\n{'-' * 70}\nPARAMETRO: {param_nome}\n{'-' * 70}")
    y = np.array([dest.set_index('Parcela')[col_nome].to_dict()[p] for p in df_meta['Parcela']])
    resultados[param_nome] = {}
    for prep_nome, prep_fn in PREPROCESSAMENTOS.items():
        Xp = prep_fn(X_raw, wv)
        best = avaliar(Xp, y)
        resultados[param_nome][prep_nome] = best
        print(f"  {prep_nome:20s} melhor NC={best['nc']:2d}  R2={best['r2']:7.3f}  "
              f"RMSE={best['rmse']:.4f}  RPD={best['rpd']:.2f}  {classif(best['rpd'])}")
    melhor_prep = max(resultados[param_nome], key=lambda k: resultados[param_nome][k]['r2'])
    melhores_globais[param_nome] = melhor_prep
    ganho = resultados[param_nome][melhor_prep]['r2'] - resultados[param_nome]['SNV']['r2']
    print(f"  --> Melhor combinacao para {param_nome}: {melhor_prep} "
          f"(R2={resultados[param_nome][melhor_prep]['r2']:.3f}, "
          f"ganho vs. SNV = {ganho:+.3f})")

# ===== TABELA COMPARATIVA FINAL =====
print(f"\n{'=' * 70}")
print("TABELA COMPARATIVA FINAL - R2 POR PARAMETRO x PRE-PROCESSAMENTO")
print(f"{'=' * 70}")
preps = list(PREPROCESSAMENTOS.keys())
print(f"{'Parametro':15s}" + "".join(f"{p:>20s}" for p in preps) + f"{'MELHOR':>22s}")
linhas_csv = []
for param_nome, _ in PARAMETROS:
    linha = f"{param_nome:15s}"
    row_csv = {'Parametro': param_nome}
    for prep_nome in preps:
        b = resultados[param_nome][prep_nome]
        linha += f"{b['r2']:>14.3f}(nc={b['nc']:2d})"
        row_csv[f'{prep_nome}_R2'] = b['r2']
        row_csv[f'{prep_nome}_RMSE'] = b['rmse']
        row_csv[f'{prep_nome}_RPD'] = b['rpd']
        row_csv[f'{prep_nome}_NC'] = b['nc']
    linha += f"{melhores_globais[param_nome]:>22s}"
    row_csv['Melhor'] = melhores_globais[param_nome]
    linhas_csv.append(row_csv)
    print(linha)

df_out = pd.DataFrame(linhas_csv)
df_out.to_csv('resultados_gridsearch_preprocessamento.csv', index=False)
print("\nTabela salva: resultados_gridsearch_preprocessamento.csv")

# ===== GRAFICO COMPARATIVO =====
fig, ax = plt.subplots(figsize=(13, 6))
x = np.arange(len(PARAMETROS))
width = 0.2
cores = ['#4C72B0', '#DD8452', '#55A868', '#C44E52']
for i, prep_nome in enumerate(preps):
    r2s = [resultados[p][prep_nome]['r2'] for p, _ in PARAMETROS]
    ax.bar(x + (i - 1.5) * width, r2s, width, label=prep_nome, color=cores[i])
ax.set_xticks(x)
ax.set_xticklabels([p for p, _ in PARAMETROS], rotation=20)
ax.set_ylabel('R² (GroupKFold, melhor NC)')
ax.set_title('Comparação de pré-processamentos espectrais por parâmetro (Recomendação 9.2)')
ax.axhline(0, color='gray', lw=0.8)
ax.legend()
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('comparativo_gridsearch_preprocessamento.png', dpi=150)
print("Grafico salvo: comparativo_gridsearch_preprocessamento.png")

print(f"\nTempo total: {time.time() - t0:.1f}s")
print("Pipeline concluido!")
