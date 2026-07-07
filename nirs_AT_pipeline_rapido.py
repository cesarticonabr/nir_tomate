"""
Pipeline NIRS -> AT - Versao Rapida e Otimizada
"""
import pandas as pd, numpy as np, re, warnings, time
warnings.filterwarnings('ignore')
from scipy.signal import savgol_filter
from scipy.stats import pearsonr, f_oneway
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import Ridge, LinearRegression
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

t0 = time.time()
print("=" * 60)
print("NIRS -> AT - PIPELINE OTIMIZADO")
print("=" * 60)

# ===== CARREGAR =====
espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()
at_map = dest.set_index('Parcela')['AT'].to_dict()

amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values
X_raw = espectros[amostras].T.values

df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)', a.strip()).groups() for a in amostras],
                        columns=['T','R','F'], index=amostras)
df_meta['Parcela'] = df_meta['T'] + df_meta['R']
y = np.array([at_map[p] for p in df_meta['Parcela']])

# Pre-processamento
def snv(X):
    return (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)

X_snv = snv(X_raw)

# --- REMOCAO DE FAIXAS RUIDOSAS (Recomendacao 9.2) ---
from nirs_utils import criar_mascara_comprimentos
print('\n--- Remocao de faixas espectrais ruidosas ---')
mask, n_rem = criar_mascara_comprimentos(wv)
print(f'  Removendo {n_rem}/{len(wv)} pontos ({n_rem/len(wv)*100:.1f}%)')
X_snv = X_snv[:, mask]
X_raw = X_raw[:, mask]
wv = wv[mask]
print(f'  Comprimentos mantidos: {len(wv)}')
# ---

X_sg = savgol_filter(X_snv, window_length=11, polyorder=2, deriv=1, axis=1)

print(f"\nAmostras: {len(y)} | Features: {len(wv)} | Parcelas: {df_meta['Parcela'].nunique()}")
print(f"AT: media={y.mean():.4f}, std={y.std():.4f}, [{y.min():.4f}, {y.max():.4f}]")

# ANOVA
anova_groups = [dest[dest['Tratamento']==t]['AT'] for t in sorted(dest['Tratamento'].unique())]
f_stat, p_val = f_oneway(*anova_groups)
print(f"ANOVA AT~Tratamento: F={f_stat:.3f}, p={p_val:.4f} {'(N.S.)' if p_val>0.05 else '(signif.)'}")

# ===== PCA =====
pca = PCA().fit(StandardScaler().fit_transform(X_snv))
print(f"PCA: PC1={pca.explained_variance_ratio_[0]:.1%}, PC1+PC2={sum(pca.explained_variance_ratio_[:2]):.1%}")

# ===== CORRELACAO =====
corrs = np.array([pearsonr(X_snv[:, i], y)[0] for i in range(0, len(wv), 10)])  # amostrar a cada 10 nm
max_corr = np.max(np.abs(corrs))
print(f"Corr. maxima espectro-AT: |r|={max_corr:.3f}")

# ===== FUNCAO DE VALIDACAO RAPIDA =====
def val_modelo(modelo, X, y, grupos, n_splits=5, n_repeats=10):
    gkf = GroupKFold(n_splits=n_splits)
    preds, reals = [], []
    for seed in range(n_repeats):
        for tr, te in gkf.split(X, y, grupos.sample(frac=1, random_state=seed)):
            scaler = StandardScaler()
            m = modelo
            m.fit(scaler.fit_transform(X[tr]), y[tr])
            preds.extend(m.predict(scaler.transform(X[te])))
            reals.extend(y[te])
    r2 = r2_score(reals, preds)
    rmse = np.sqrt(mean_squared_error(reals, preds))
    rpd = np.std(y) / rmse if rmse > 0 else 0
    return r2, rmse, rpd

# ===== TESTAR MODELOS (APENAS ESSENCIAIS) =====
print("\n--- AVALIACAO GroupKFold 5-fold (10 repeticoes) ---")
modelos = [
    ("PLS(1)",      PLSRegression(n_components=1)),
    ("PLS(2)",      PLSRegression(n_components=2)),
    ("PLS(5)",      PLSRegression(n_components=5)),
    ("RF d=3",      RandomForestRegressor(n_estimators=200, max_depth=3, min_samples_leaf=5, random_state=42)),
    ("RF d=6",      RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=4, random_state=42)),
]

resultados = []
for nome, modelo in modelos:
    for X_in, prep_nome in [(X_snv, "SNV"), (X_sg, "SNV+SG")]:
        r2, rmse, rpd = val_modelo(modelo, X_in, y, df_meta['Parcela'])
        resultados.append({'Modelo': f"{nome} ({prep_nome})", 'R2': r2, 'RMSE': rmse, 'RPD': rpd})

# Tabela
df_res = pd.DataFrame(resultados).sort_values('R2', ascending=False)
print(f"\n{'Modelo':30s} {'R2':>7s} {'RMSE':>8s} {'RPD':>6s}")
print("-" * 55)
for _, r in df_res.iterrows():
    print(f"{r['Modelo']:30s} {r['R2']:7.3f} {r['RMSE']:8.4f} {r['RPD']:6.2f}")

# ===== VALIDACAO COM MEDIAS POR PARCELA (n=9) =====
print("\n--- VALIDACAO MEDIAS POR PARCELA (n=9, LOOCV) ---")
df_esp = pd.DataFrame(X_snv)
df_esp['Parcela'] = df_meta['Parcela'].values
X_parc = df_esp.groupby('Parcela').mean().values
y_parc = dest['AT'].values  # 9 valores

loo = LeaveOneOut()
best_r2 = -999
for modelo, nome_m in [(PLSRegression(n_components=1), "PLS(1)"),
                        (PLSRegression(n_components=2), "PLS(2)"),
                        (Ridge(alpha=1.0), "Ridge(a=1)"),
                        (Ridge(alpha=0.1), "Ridge(a=0.1)"),
                        (LinearRegression(), "OLS")]:
    preds, reals = [], []
    for tr, te in loo.split(X_parc):
        scaler = StandardScaler()
        modelo.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
        preds.extend(modelo.predict(scaler.transform(X_parc[te])))
        reals.extend(y_parc[te])
    r2 = r2_score(reals, preds)
    rmse = np.sqrt(mean_squared_error(reals, preds))
    rpd = np.std(y_parc) / rmse
    print(f"  {nome_m:15s} R2={r2:.3f} RMSE={rmse:.4f} RPD={rpd:.2f}")
    if r2 > best_r2:
        best_r2, best_r2_n, best_rmse_n, best_rpd_n = r2, nome_m, rmse, rpd

print(f"  Melhor: {best_r2_n} (R2={best_r2:.3f})")

# Com selecao de features
print("  --- Com selecao de features (Top K) ---")
for nf in [5, 10, 20]:
    sel = SelectKBest(f_regression, k=min(nf, X_parc.shape[1]))
    X_sub = sel.fit_transform(X_parc, y_parc)
    for modelo, nome_m in [(Ridge(alpha=1.0), f"Ridge+k={nf}"),
                            (PLSRegression(n_components=1), f"PLS(1)+k={nf}")]:
        preds, reals = [], []
        for tr, te in loo.split(X_sub):
            scaler = StandardScaler()
            modelo.fit(scaler.fit_transform(X_sub[tr]), y_parc[tr])
            preds.extend(modelo.predict(scaler.transform(X_sub[te])))
            reals.extend(y_parc[te])
        r2 = r2_score(reals, preds)
        print(f"  {nome_m:15s} R2={r2:.3f}")

# ===== GRAFICOS =====
print("\n--> Gerando graficos...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Espectros
ax = axes[0, 0]
for i in range(min(9, X_raw.shape[0])):
    ax.plot(wv, X_raw[i], alpha=0.6, linewidth=0.7)
ax.set_xlabel('Comprimento de onda (nm)')
ax.set_ylabel('Reflectancia')
ax.set_title('Espectros NIRS brutos (9 amostras)')
ax.grid(True, alpha=0.3)

# Correlacao (amostrada a cada 2 nm)
ax = axes[0, 1]
corrs_full = np.array([pearsonr(X_snv[:, i], y)[0] for i in range(len(wv))])
ax.plot(wv, corrs_full, 'b-', linewidth=0.6, alpha=0.7)
ax.axhline(0, color='gray', ls='--', alpha=0.5)
ax.set_xlabel('Comprimento de onda (nm)')
ax.set_ylabel('r (correlacao com AT)')
ax.set_title(f'Correlacao AT-espectro (max |r|={np.max(np.abs(corrs_full)):.3f})')
ax.grid(True, alpha=0.3)

# PCA
ax = axes[1, 0]
X_pca = PCA(2).fit_transform(StandardScaler().fit_transform(X_snv))
sc = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=y, cmap='viridis', s=60, edgecolors='k', linewidth=0.5)
plt.colorbar(sc, ax=ax, label='AT')
ax.set_xlabel('PC1')
ax.set_ylabel('PC2')
ax.set_title('PCA dos espectros NIRS')
ax.grid(True, alpha=0.3)

# Parcela LOOCV
ax = axes[1, 1]
modelo_plot = Ridge(alpha=0.1)
preds_p, reals_p = [], []
for tr, te in loo.split(X_parc):
    scaler = StandardScaler()
    modelo_plot.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
    preds_p.append(modelo_plot.predict(scaler.transform(X_parc[te]))[0])
    reals_p.append(y_parc[te][0])
r2_p = r2_score(reals_p, preds_p)
ax.scatter(reals_p, preds_p, c='darkgreen', s=80, edgecolors='k', linewidth=1, zorder=5)
parc_labels = list(dest['Parcela'])
for i, lbl in enumerate(parc_labels):
    ax.annotate(lbl, (reals_p[i], preds_p[i]), xytext=(4, 4), textcoords='offset points', fontsize=7)
minv, maxv = min(min(reals_p), min(preds_p))-0.01, max(max(reals_p), max(preds_p))+0.01
ax.plot([minv, maxv], [minv, maxv], 'r--', alpha=0.7)
ax.set_xlabel('AT Real')
ax.set_ylabel('AT Predito')
ax.set_title(f'LOOCV (medias por parcela) - R2={r2_p:.3f}')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('analise_NIRS_AT.png', dpi=150)
print("  Grafico: analise_NIRS_AT.png")

# ===== RESUMO =====
print("\n" + "=" * 60)
print("RESUMO")
print("=" * 60)

melhor = df_res.iloc[0]
print(f"""
DADOS:
  - {len(y)} espectros, {df_meta['Parcela'].nunique()} valores de AT (1/parcela x 5 frutos)
  - Correlacao maxima AT-espectro: |r|={np.max(np.abs(corrs_full)):.3f}
  - ANOVA AT~Tratamento: p={p_val:.4f} {'(N.S. - grupos homogeneos)' if p_val>0.05 else '(diferem)'}
  - PC1 explica {pca.explained_variance_ratio_[0]:.1%} da variancia espectral

MELHOR MODELO (45 amostras, GroupKFold):
  {melhor['Modelo']}: R2={melhor['R2']:.3f}, RMSE={melhor['RMSE']:.4f}, RPD={melhor['RPD']:.2f}

MELHOR MODELO (9 medias de parcela, LOOCV):
  {best_r2_n}: R2={best_r2:.3f}, RMSE={best_rmse_n:.4f}, RPD={best_rpd_n:.2f}

CONCLUSOES:
  - {'Os modelos NAO conseguem predizer AT' if melhor['R2'] < 0.15 else 'Ha capacidade preditiva fraca-moderada'}
  - Principal limitacao: apenas 9 valores independentes de AT para 45 espectros
  - Sugestao: medir AT individualmente por fruto para aumentar n
""")
print(f"Tempo total: {time.time()-t0:.1f}s")
print("FIM")
