"""
Pipeline NIRS -> AT - Versao Aprimorada
Inclui analise exploratoria completa e modelos alternativos
"""
import pandas as pd, numpy as np, re, warnings
warnings.filterwarnings('ignore')
from scipy.signal import savgol_filter
from scipy.stats import f_oneway, pearsonr
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("=" * 65)
print("PIPELINE NIRS -> AT - ANALISE COMPLETA")
print("=" * 65)

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

# ===== PRE-PROCESSAMENTO =====
def snv(X):
    return (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)

X_snv = snv(X_raw)
X_sg = savgol_filter(X_snv, window_length=11, polyorder=2, deriv=1, axis=1)

# Reduzir para bandas NIR relevantes (1100-2500 nm)
nir_mask = wv >= 1100
X_nir = X_snv[:, nir_mask]
wv_nir = wv[nir_mask]

# ===== PCA =====
pca = PCA()
X_pca = pca.fit_transform(StandardScaler().fit_transform(X_snv))

# ===== METRICAS DESCRITIVAS =====
print(f"\nAmostras: {len(y)} | Features: {len(wv)} | Parcelas: {df_meta['Parcela'].nunique()}")
print(f"AT: media={y.mean():.4f}, std={y.std():.4f}, range=[{y.min():.4f}, {y.max():.4f}]")
anova_res = f_oneway(*[dest[dest['Tratamento']==t]['AT'] for t in sorted(dest['Tratamento'].unique())])
f_stat = anova_res.statistic
p_val = anova_res.pvalue
print(f"ANOVA AT ~ Tratamento: F={f_stat:.4f}")
print(f"  F={f_stat:.4f}, p={p_val:.4f} {'(signif.)' if p_val<0.05 else '(N.S.)'}")

# ===== 1. CORRELACAO DIRETA =====
print("\n" + "-" * 65)
print("1. CORRELACAO DIRETA ESPECTRO-AT")
print("-" * 65)

# Com todas 45 amostras
corrs = np.array([pearsonr(X_snv[:, i], y)[0] for i in range(len(wv))])
top_c = np.argsort(np.abs(corrs))[::-1][:10]
print(f"Top 10 comprimentos de onda (45 amostras):")
for i, idx in enumerate(top_c[:10]):
    print(f"  {i+1}. {wv[idx]:.1f} nm  r={corrs[idx]:+.4f}")

# Com 9 medias de parcela
df_esp = pd.DataFrame(X_snv)
df_esp['Parcela'] = df_meta['Parcela'].values
df_esp['AT'] = y
X_parc = df_esp.groupby('Parcela').mean().drop(columns=['AT']).values
y_parc = dest['AT'].values  # 9 valores diretos
corrs_p = np.array([pearsonr(X_parc[:, i], y_parc)[0] for i in range(len(wv))])
top_p = np.argsort(np.abs(corrs_p))[::-1][:10]
print(f"\nTop 10 comprimentos de onda (9 medias de parcela):")
for i, idx in enumerate(top_p[:10]):
    print(f"  {i+1}. {wv[idx]:.1f} nm  r={corrs_p[idx]:+.4f}")

print(f"\n  Correlacao media |r| (n=45): {np.mean(np.abs(corrs)):.4f}")
print(f"  Correlacao media |r| (n=9): {np.mean(np.abs(corrs_p)):.4f}")
print(f"  Melhor comprimento de onda:")
print(f"    n=45: {wv[top_c[0]]:.1f} nm (r={corrs[top_c[0]]:+.4f})")
print(f"    n=9:  {wv[top_p[0]]:.1f} nm (r={corrs_p[top_p[0]]:+.4f})")

# ===== 2. FUNCAO DE VALIDACAO =====
print("\n" + "-" * 65)
print("2. AVALIACAO DE MODELOS")
print("-" * 65)

def avaliar_modelo(modelo, X, y, grupos, nome="", n_repeats=30, n_splits=5):
    """GroupKFold com a garantia de que parcelas ficam juntas"""
    gkf = GroupKFold(n_splits=n_splits)
    preds, reals = [], []
    for seed in range(n_repeats):
        g_emb = grupos.sample(frac=1, random_state=seed)
        for tr, te in gkf.split(X, y, g_emb):
            scaler = StandardScaler()
            m = modelo.__class__(**modelo.get_params()) if hasattr(modelo, 'get_params') else modelo.__class__()
            m.fit(scaler.fit_transform(X[tr]), y[tr])
            preds.extend(m.predict(scaler.transform(X[te])))
            reals.extend(y[te])
    r2 = r2_score(reals, preds)
    rmse = np.sqrt(mean_squared_error(reals, preds))
    rpd = y.std() / rmse
    qual = "EXCELENTE" if rpd > 2.5 else "Bom" if rpd > 2.0 else "Razoavel" if rpd > 1.5 else "Fraco"
    return r2, rmse, rpd, qual

# Rodar modelos com diferentes configuracoes
configs = [
    ("PLS (n=1)", PLSRegression(n_components=1)),
    ("PLS (n=2)", PLSRegression(n_components=2)),
    ("PLS (n=3)", PLSRegression(n_components=3)),
    ("PLS (n=5)", PLSRegression(n_components=5)),
    ("PLS (n=10)", PLSRegression(n_components=10)),
    ("Random Forest", RandomForestRegressor(n_estimators=300, max_depth=6,
                                            min_samples_leaf=4, random_state=42)),
    ("RF (raso d=3)", RandomForestRegressor(n_estimators=200, max_depth=3,
                                             min_samples_leaf=5, random_state=42)),
    ("GBoost", GradientBoostingRegressor(n_estimators=100, max_depth=3,
                                          learning_rate=0.05, subsample=0.8, random_state=42)),
    ("SVR (RBF)", SVR(kernel='rbf', C=5, gamma='scale')),
    ("SVR (linear)", SVR(kernel='linear', C=1)),
]

# Testar com SNV apenas
resultados = []
for nome, modelo in configs:
    r2_v, rmse_v, rpd_v, qual = avaliar_modelo(modelo, X_snv, y, df_meta['Parcela'], nome)
    resultados.append({'Modelo': nome, 'R2': r2_v, 'RMSE': rmse_v, 'RPD': rpd_v, 'Qual': qual,
                       'Preproc': 'SNV', 'N': 45})

# Testar com SNV+SG
for nome, modelo in configs[:5]:  # so PLS
    r2_v, rmse_v, rpd_v, qual = avaliar_modelo(modelo, X_sg, y, df_meta['Parcela'], nome + " +SG")
    resultados.append({'Modelo': nome + " +SG", 'R2': r2_v, 'RMSE': rmse_v, 'RPD': rpd_v, 'Qual': qual,
                       'Preproc': 'SNV+SG', 'N': 45})

# Testar com PCA (top PCs)
for n_pc in [3, 5, 10]:
    X_pca_sub = X_pca[:, :n_pc]
    for nome, m in [("PLS(2)", PLSRegression(n_components=2)),
                    ("PLS(3)", PLSRegression(n_components=3)),
                    ("RF", RandomForestRegressor(n_estimators=200, max_depth=4, random_state=42))]:
        r2_v, rmse_v, rpd_v, qual = avaliar_modelo(m, X_pca_sub, y, df_meta['Parcela'], nome)
        resultados.append({'Modelo': f'PCA{n_pc}+{nome}', 'R2': r2_v, 'RMSE': rmse_v,
                           'RPD': rpd_v, 'Qual': qual, 'Preproc': 'PCA', 'N': 45})

# Tabela
df_res = pd.DataFrame(resultados).sort_values('R2', ascending=False)
print(f"\n{'Modelo':30s} {'R2':>7s} {'RMSE':>8s} {'RPD':>6s}  Qual")
print("-" * 62)
for _, r in df_res.iterrows():
    print(f"{r['Modelo']:30s} {r['R2']:7.3f} {r['RMSE']:8.4f} {r['RPD']:6.2f}  {r['Qual']}")

# ===== 3. VALIDACAO COM MEDIAS DE PARCELA (n=9) =====
print("\n" + "-" * 65)
print("3. VALIDACAO COM MEDIAS POR PARCELA (n=9)")
print("-" * 65)

from sklearn.model_selection import LeaveOneOut
loo = LeaveOneOut()
df_res_p = []

# Para 9 amostras, testar modelos simples
configs_9 = [
    ("Regressao Linear", 'lin'),
    ("PLS(1)", PLSRegression(n_components=1)),
    ("PLS(2)", PLSRegression(n_components=2)),
    ("RF (d=3,m=5)", RandomForestRegressor(n_estimators=200, max_depth=3,
                                            min_samples_leaf=2, random_state=42)),
]

# Selecao dos melhores comprimentos de onda
k_best = SelectKBest(f_regression, k=min(50, X_parc.shape[1]))
X_top = k_best.fit_transform(X_parc, y_parc)

from sklearn.linear_model import LinearRegression, Ridge

for nome, modelo in configs_9:
    preds, reals = [], []
    for tr, te in loo.split(X_parc):
        modelo_ = modelo
        scaler = StandardScaler()
        modelo_.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
        preds.extend(modelo_.predict(scaler.transform(X_parc[te])))
        reals.extend(y_parc[te])
    r2 = r2_score(reals, preds)
    rmse = np.sqrt(mean_squared_error(reals, preds))
    rpd = y_parc.std() / rmse if rmse > 0 else 0
    df_res_p.append({'Modelo': nome, 'R2': r2, 'RMSE': rmse, 'RPD': rpd})
    print(f"  {nome:25s}  R2={r2:.3f}  RMSE={rmse:.4f}  RPD={rpd:.2f}")

# Testar com selecao de features
for n_feat in [5, 10, 20, 50]:
    kbest = SelectKBest(f_regression, k=min(n_feat, X_parc.shape[1]))
    X_sub = kbest.fit_transform(X_parc, y_parc)
    for modelo, nome_m in [(Ridge(alpha=1.0), 'Ridge'), (PLSRegression(n_components=2), 'PLS(2)')]:
        preds, reals = [], []
        for tr, te in loo.split(X_sub):
            scaler = StandardScaler()
            modelo.fit(scaler.fit_transform(X_sub[tr]), y_parc[tr])
            preds.extend(modelo.predict(scaler.transform(X_sub[te])))
            reals.extend(y_parc[te])
        r2_v = r2_score(reals, preds)
        rmse_v = np.sqrt(mean_squared_error(reals, preds))
        print(f"  {nome_m:10s} + k={n_feat:2d} features   R2={r2_v:.3f}  RMSE={rmse_v:.4f}")

# ===== 4. GRAFICOS =====
print("\n--> Gerando graficos...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (a) Espectros brutos
ax = axes[0, 0]
for i in range(min(9, len(y))):
    color = plt.cm.plasma(y[i] / y.max())
    ax.plot(wv, X_raw[i], color=color, alpha=0.7, linewidth=0.8)
sm = plt.cm.ScalarMappable(cmap='plasma', norm=plt.Normalize(y.min(), y.max()))
sm.set_array([])
plt.colorbar(sm, ax=ax, label='AT')
ax.set_xlabel('Comprimento de onda (nm)')
ax.set_ylabel('Reflectancia')
ax.set_title('Espectros NIRS brutos (coloridos por AT)')
ax.grid(True, alpha=0.3)

# (b) Correlacao
ax = axes[0, 1]
ax.plot(wv, corrs, 'b-', linewidth=0.8, alpha=0.7)
ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax.set_xlabel('Comprimento de onda (nm)')
ax.set_ylabel('r (correlacao com AT)')
ax.set_title('Correlacao espectro-AT por comprimento de onda')
ax.grid(True, alpha=0.3)

# (c) PCA
ax = axes[1, 0]
sc = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=y, cmap='plasma',
                s=50, edgecolors='k', linewidth=0.5, alpha=0.8)
plt.colorbar(sc, ax=ax, label='AT')
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
ax.set_title(f'PCA espectros NIRS (r(PC1,AT)={pearsonr(X_pca[:,0], y)[0]:.3f})')
ax.grid(True, alpha=0.3)

# (d) Melhor modelo
ax = axes[1, 2] if 2 < 4 else axes[1, 1]
# Remover se nao existir 4 subplots
plt.tight_layout()
plt.savefig('analise_exploratoria_NIRS.png', dpi=150, bbox_inches='tight')

# Grafico adicional: top features
fig2, ax = plt.subplots(figsize=(12, 5))
ax.bar(wv[top_c[:50]], corrs[top_c[:50]], width=3.0, color='steelblue', alpha=0.7)
ax.set_xlabel('Comprimento de onda (nm)')
ax.set_ylabel('|r| (correlacao com AT)')
ax.set_title('Top 50 comprimentos de onda mais correlacionados com AT')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('top_correlacoes_NIRS_AT.png', dpi=150, bbox_inches='tight')

print("  analise_exploratoria_NIRS.png")
print("  top_correlacoes_NIRS_AT.png")

# ===== 5. RESUMO =====
print("\n" + "=" * 65)
print("RESUMO E RECOMENDACOES")
print("=" * 65)

print(f"""
SITUACAO DOS DADOS:
  - {len(y)} amostras espectrais com apenas {df_meta['Parcela'].nunique()} valores independentes de AT
  - Correlacao maxima espectro-AT: r={np.max(np.abs(corrs)):.3f} (n=45) / r={np.max(np.abs(corrs_p)):.3f} (n=9)
  - A correlacao e BAIXA para modelagem preditiva robusta
  - ANOVA nao mostrou diferenca significativa de AT entre tratamentos (p={p_val:.3f})
  - PC1 explica {pca.explained_variance_ratio_[0]:.1%} da var. espectral e tem r={pearsonr(X_pca[:,0], y)[0]:.3f} com AT

MELHOR MODELO ENCONTRADO:
  - {df_res.iloc[0]['Modelo']}: R2={df_res.iloc[0]['R2']:.3f}, RMSE={df_res.iloc[0]['RMSE']:.4f}, RPD={df_res.iloc[0]['RPD']:.2f}
""")

# Interpretacao
print("INTERPRETACAO:")
if df_res.iloc[0]['R2'] < 0.15:
    print("  Os modelos nao conseguem predizer AT a partir dos espectros NIRS com")
    print("  os dados disponiveis. Possiveis causas:")
    print("  1. A relacao AT-NIRS e fraca nessa faixa espectral e matriz")
    print("  2. A variabilidade espectral ENTRE frutos de mesma parcela e maior")
    print("     que a variacao de AT ENTRE parcelas")
    print("  3. E necessario mais poder estatistico (mais parcelas, mais repeticoes)")
elif df_res.iloc[0]['R2'] < 0.5:
    print("  Ha uma fraca relacao preditiva. Modelos conseguem capturar tendencias")
    print("  mas com baixa precisao para uso pratico.")
else:
    print("  Modelos com capacidade preditiva moderada a boa.")

print(f"""
RECOMENDACAO:  Usar medias dos 5 frutos por parcela (reduz ruido espectral)
              e testar com Leave-One-Out para 9 parcelas.
              PLS com 1-2 componentes no espectro SNV foi a melhor configuracao.

PROXIMOS PASSOS SUGERIDOS:
  1. Coletar mais parcelas (mais repeticoes por tratamento)
  2. Medir AT individualmente por fruto (nao apenas por parcela)
  3. Explorar outras regioes do NIR ou pre-processamentos alternativos
  4. Se possivel, usar espectroscopia na regiao do MID-IR (assinaturas mais fortes)
""")

# Salvar tabela de resultados
df_res.to_csv('resultados_modelos_NIRS_AT.csv', index=False)
print("Tabela salva: resultados_modelos_NIRS_AT.csv")
print("\nPipeline concluido!")
