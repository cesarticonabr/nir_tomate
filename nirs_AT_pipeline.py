"""
Pipeline de Machine Learning para predicao de AT (Acidez Titulavel)
usando espectros NIRS de tomate
"""
import pandas as pd
import numpy as np
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, KFold
from sklearn.metrics import r2_score, mean_squared_error

# ========================
# 1. CARREGAR DADOS
# ========================
print("=" * 65)
print("PIPELINE NIRS -> AT (Acidez Titulavel)")
print("=" * 65)

espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
destrutiva = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')

# Nome da coluna 'Repeticao' pode vir com acento em UTF-8; usar indice
col_repeticao = destrutiva.columns[2]  # 'Repeticao' com acento

# Transpor: amostras nas linhas, comprimentos nas colunas
amostras = [c for c in espectros.columns if c != 'Espectro']
wavelengths = espectros['Espectro'].values
X_raw = espectros[amostras].T.values
n_amostras, n_features = X_raw.shape

# Extrair metadados (T, R, F) de cada amostra
def parse_amostra(nome):
    m = re.match(r'(T\d+)(R\d+)F(\d+)', nome.strip())
    return (m.group(1), m.group(2), int(m.group(3))) if m else (None, None, None)

df_meta = pd.DataFrame([parse_amostra(a) for a in amostras],
                        columns=['Tratamento', 'Repeticao', 'Fruto'],
                        index=amostras)
df_meta['Parcela'] = df_meta['Tratamento'] + df_meta['Repeticao']
df_meta['Grupo'] = df_meta['Parcela']

# Merge com AT
destrutiva['Parcela'] = destrutiva['Tratamento'].str.strip() + destrutiva[col_repeticao].str.strip()
at_map = destrutiva.set_index('Parcela')['AT'].to_dict()
y = np.array([at_map[p] for p in df_meta['Parcela']])

print(f"Amostras: {n_amostras}")
print(f"Comprimentos de onda: {n_features} ({wavelengths[0]:.0f}-{wavelengths[-1]:.0f} nm)")
print(f"Parcelas unicas: {df_meta['Parcela'].nunique()}")
print(f"AT: min={y.min():.4f}, max={y.max():.4f}, media={y.mean():.4f}, std={y.std():.4f}")

# ========================
# 2. PRE-PROCESSAMENTO ESPECTRAL
# ========================
print("\n" + "=" * 65)
print("PRE-PROCESSAMENTO ESPECTRAL")
print("=" * 65)

def snv_transform(X):
    """Standard Normal Variate"""
    mean = X.mean(axis=1, keepdims=True)
    std = X.std(axis=1, keepdims=True)
    return (X - mean) / std

def derivada_sg(X, window=11, polyorder=2, deriv=1):
    """Savitzky-Golay 1a derivada"""
    return savgol_filter(X, window_length=window, polyorder=polyorder, deriv=deriv, axis=1)

X_snv = snv_transform(X_raw)

# --- REMOCAO DE FAIXAS RUIDOSAS (Recomendacao 9.2) ---
from nirs_utils import criar_mascara_comprimentos
print('\n--- Remocao de faixas espectrais ruidosas ---')
mask, n_rem = criar_mascara_comprimentos(wavelengths)
print(f'  Removendo {n_rem}/{len(wavelengths)} pontos ({n_rem/len(wavelengths)*100:.1f}%)')
X_snv = X_snv[:, mask]
X_raw = X_raw[:, mask]
wavelengths = wavelengths[mask]
print(f'  Comprimentos mantidos: {len(wavelengths)}')
# ---

X_pre = derivada_sg(X_snv, window=11, polyorder=2, deriv=1)

print(f"  SNV: aplicado (cada espectro centrado e escalado)")
print(f"  Savitzky-Golay: 1a derivada (window=11, polyorder=2)")
print(f"  Dados pos-processamento: {X_pre.shape}")

# ========================
# 3. FUNCAO DE VALIDACAO
# ========================

def validar_modelo(modelo, X, y, grupos, nome="Modelo", n_repeats=20):
    """
    Validacao com GroupKFold + repeticoes aleatorias.
    Grupos = parcelas, nunca separadas entre treino e teste.
    """
    gkf = GroupKFold(n_splits=5)
    y_real_all, y_pred_all = [], []

    for seed in range(n_repeats):
        grupos_emb = grupos.sample(frac=1, random_state=seed)
        for train_idx, test_idx in gkf.split(X, y, grupos_emb):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)

            modelo.fit(X_train_s, y_train)
            y_pred = modelo.predict(X_test_s)

            y_real_all.extend(y_test)
            y_pred_all.extend(y_pred)

    y_real_all = np.array(y_real_all)
    y_pred_all = np.array(y_pred_all)
    r2 = r2_score(y_real_all, y_pred_all)
    rmse = np.sqrt(mean_squared_error(y_real_all, y_pred_all))
    rpd = y.std() / rmse

    qual = "** EXCELENTE" if rpd > 2.5 else "** Bom" if rpd > 2.0 else "* Razoavel" if rpd > 1.5 else "  Fraco"
    print(f"  {nome}:")
    print(f"    R2  = {r2:.4f}")
    print(f"    RMSE = {rmse:.4f}")
    print(f"    RPD = {rpd:.2f}  {qual}")

    return y_real_all, y_pred_all, r2, rmse, rpd


# ========================
# 4. OTIMIZACAO DE COMPONENTES PLS
# ========================
print("\n" + "=" * 65)
print("OTIMIZACAO DO NUMERO DE COMPONENTES PLS")
print("=" * 65)

n_components_range = range(2, 21)
resultados_pls = []

for nc in n_components_range:
    pls = PLSRegression(n_components=nc)
    _, _, r2, rmse, rpd = validar_modelo(pls, X_pre, y, df_meta['Grupo'],
                                          nome=f"PLS (n={nc:2d})", n_repeats=10)
    resultados_pls.append({'nc': nc, 'r2': r2, 'rmse': rmse, 'rpd': rpd})

df_pls = pd.DataFrame(resultados_pls)
best_idx = df_pls['r2'].idxmax()
best_nc = int(df_pls.loc[best_idx, 'nc'])

print(f"\n>> Melhor PLS: {best_nc} componentes (R2={df_pls.loc[best_idx, 'r2']:.4f})")

# Grafico de otimizacao do PLS
fig_opt, ax1 = plt.subplots(figsize=(9, 5))
color1, color2 = 'steelblue', 'crimson'
ax1.plot(df_pls['nc'], df_pls['r2'], 'o-', color=color1, linewidth=2, markersize=6, label='R2')
ax1.set_xlabel('Numero de componentes PLS', fontsize=12)
ax1.set_ylabel('R2 (val. cruzada)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)
ax1.axvline(best_nc, color='gray', linestyle='--', alpha=0.5)

ax2 = ax1.twinx()
ax2.plot(df_pls['nc'], df_pls['rmse'], 's--', color=color2, linewidth=2, markersize=6, label='RMSE')
ax2.set_ylabel('RMSE', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')

plt.title(f'Otimizacao PLS - melhor: {best_nc} componentes', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('otimizacao_PLS_components.png', dpi=150, bbox_inches='tight')
print(">> Grafico salvo: otimizacao_PLS_components.png")

# ========================
# 5. MODELO FINAL PLS + GRAFICO
# ========================
print("\n" + "=" * 65)
print("AVALIACAO FINAL - COMPARACAO DE MODELOS")
print("=" * 65)

modelos = {
    f'PLS ({best_nc} comps)': PLSRegression(n_components=best_nc),
    'Random Forest': RandomForestRegressor(
        n_estimators=500, max_depth=12, min_samples_leaf=3,
        max_features='sqrt', random_state=42
    ),
    'SVR (RBF)': SVR(kernel='rbf', C=10, gamma='scale'),
}

results = {}
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

for idx, (nome, modelo) in enumerate(modelos.items()):
    y_real, y_pred, r2, rmse, rpd = validar_modelo(
        modelo, X_pre, y, df_meta['Grupo'], nome=nome, n_repeats=20
    )
    results[nome] = {'y_real': y_real, 'y_pred': y_pred, 'r2': r2, 'rmse': rmse, 'rpd': rpd}

    ax = axes[idx]
    ax.scatter(y_real, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5, s=30)
    min_val = min(y_real.min(), y_pred.min()) - 0.02
    max_val = max(y_real.max(), y_pred.max()) + 0.02
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=1, alpha=0.7)
    ax.set_xlabel('AT Real', fontsize=11)
    ax.set_ylabel('AT Predito', fontsize=11)
    ax.set_title(f'{nome}\nR2={r2:.3f} | RMSE={rmse:.4f} | RPD={rpd:.2f}',
                 fontsize=11, fontweight='bold')
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

plt.tight_layout()
plt.savefig('predicao_AT_comparacao_modelos.png', dpi=150, bbox_inches='tight')
print(">> Grafico salvo: predicao_AT_comparacao_modelos.png")

# ========================
# 6. PLS - LOADINGS
# ========================
print("\n" + "=" * 65)
print("INTERPRETACAO - VARIAVEIS MAIS IMPORTANTES")
print("=" * 65)

pls_final = PLSRegression(n_components=best_nc)
scaler_final = StandardScaler()
X_scaled = scaler_final.fit_transform(X_pre)
pls_final.fit(X_scaled, y)

var_exp = np.var(pls_final.x_scores_, axis=0)
var_exp_rel = var_exp / var_exp.sum()
importances = np.sum(np.abs(pls_final.x_loadings_) * var_exp_rel[np.newaxis, :], axis=1)

top_idx = np.argsort(importances)[::-1][:30]
print("\n  Top 20 comprimentos de onda mais importantes:")
for i, idx in enumerate(top_idx[:20]):
    print(f"    {i+1:2d}. {wavelengths[idx]:7.1f} nm (importancia: {importances[idx]:.4f})")

# Grafico de importancia
fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

ax1.plot(wavelengths, X_pre.mean(axis=0), 'b-', linewidth=1.5, label='Espectro medio (SNV + deriv.)')
ax1.fill_between(wavelengths,
                 X_pre.mean(axis=0) - X_pre.std(axis=0),
                 X_pre.mean(axis=0) + X_pre.std(axis=0),
                 alpha=0.15, color='blue')
ax1.set_xlabel('Comprimento de onda (nm)', fontsize=12)
ax1.set_ylabel('Reflectancia (pre-processada)', fontsize=12)
ax1.set_title('Espectros NIRS processados (SNV + 1a derivada)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend()

ax2.bar(wavelengths, importances, width=2.0, color='darkred', alpha=0.7, linewidth=0)
ax2.set_xlabel('Comprimento de onda (nm)', fontsize=12)
ax2.set_ylabel('Importancia PLS', fontsize=12)
ax2.set_title(f'Variaveis mais importantes - PLS ({best_nc} componentes)', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)

top5_idx = top_idx[:5]
ax2.scatter(wavelengths[top5_idx], importances[top5_idx],
            color='red', s=80, zorder=5, label='Top 5 comprimentos')
for idx in top5_idx:
    ax2.annotate(f'{wavelengths[idx]:.0f} nm',
                xy=(wavelengths[idx], importances[idx]),
                xytext=(wavelengths[idx] + 15, importances[idx] + 0.002),
                fontsize=9, color='darkred', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='darkred', lw=0.8))
ax2.legend()

plt.tight_layout()
plt.savefig('importancia_comprimentos_onda_PLS.png', dpi=150, bbox_inches='tight')
print(">> Grafico salvo: importancia_comprimentos_onda_PLS.png")

# ========================
# 7. VALIDACAO CONSERVADORA (medias por parcela)
# ========================
print("\n" + "=" * 65)
print("VALIDACAO CONSERVADORA - MEDIAS POR PARCELA (n=9)")
print("=" * 65)

df_medias = pd.DataFrame(X_pre, index=df_meta.index)
df_medias['Parcela'] = df_meta['Parcela'].values
df_medias['AT'] = y

# Nomes das parcelas na ordem correta
parcela_nomes = df_medias.groupby('Parcela').groups.keys()
X_parcela = df_medias.groupby('Parcela').mean().values
y_parcela = np.array([at_map[p] for p in parcela_nomes])

print(f"  Amostras: {len(y_parcela)} (media espectral de 5 frutos por parcela)")

# LOOCV para as 9 parcelas
pls_parcela = PLSRegression(n_components=best_nc)
y_real_p, y_pred_p = [], []
loo = KFold(n_splits=len(y_parcela), shuffle=True, random_state=42)

for train_idx, test_idx in loo.split(X_parcela):
    X_tr, X_te = X_parcela[train_idx], X_parcela[test_idx]
    y_tr, y_te = y_parcela[train_idx], y_parcela[test_idx]
    scaler_parc = StandardScaler()
    pls_parcela.fit(scaler_parc.fit_transform(X_tr), y_tr)
    y_pred_p.extend(pls_parcela.predict(scaler_parc.transform(X_te)).ravel())
    y_real_p.extend(y_te)

y_real_p = np.array(y_real_p)
y_pred_p = np.array(y_pred_p)
r2_p = r2_score(y_real_p, y_pred_p)
rmse_p = np.sqrt(mean_squared_error(y_real_p, y_pred_p))
rpd_p = y_parcela.std() / rmse_p

print(f"\n  PLS (medias por parcela, LOOCV):")
print(f"    R2  = {r2_p:.4f}")
print(f"    RMSE = {rmse_p:.4f}")
print(f"    RPD = {rpd_p:.2f}")

fig3, ax = plt.subplots(figsize=(7, 7))
ax.scatter(y_real_p, y_pred_p, c='darkgreen', s=100, edgecolors='k', linewidth=1.2, zorder=5)
parcela_list = list(parcela_nomes)
for i, label in enumerate(parcela_list):
    ax.annotate(label, (y_real_p[i], y_pred_p[i]),
                xytext=(5, 5), textcoords='offset points', fontsize=9)
min_v = min(y_real_p.min(), y_pred_p.min()) - 0.015
max_v = max(y_real_p.max(), y_pred_p.max()) + 0.015
ax.plot([min_v, max_v], [min_v, max_v], 'r--', linewidth=1.5, alpha=0.7)
ax.set_xlabel('AT Real', fontsize=13)
ax.set_ylabel('AT Predito', fontsize=13)
ax.set_title(f'PLS - Medias por Parcela (LOOCV)\nR2={r2_p:.3f} | RMSE={rmse_p:.4f} | RPD={rpd_p:.2f}',
             fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(min_v, max_v)
ax.set_ylim(min_v, max_v)
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig('predicao_AT_parcelas_LOOCV.png', dpi=150, bbox_inches='tight')
print(">> Grafico salvo: predicao_AT_parcelas_LOOCV.png")

# ========================
# 8. TABELA COMPARATIVA
# ========================
print("\n" + "=" * 65)
print("TABELA COMPARATIVA DE MODELOS (45 amostras, GroupKFold 5-fold)")
print("=" * 65)
print(f"{'Modelo':25s} {'R2':>8s} {'RMSE':>8s} {'RPD':>8s}  {'Classif'}")
print("-" * 65)

for nome, res in results.items():
    if res['rpd'] > 2.5:
        qual = "EXCELENTE"
    elif res['rpd'] > 2.0:
        qual = "Bom"
    elif res['rpd'] > 1.5:
        qual = "Razoavel"
    else:
        qual = "Fraco"
    print(f"{nome:25s} {res['r2']:8.3f} {res['rmse']:8.4f} {res['rpd']:8.2f}  {qual}")

print("\n" + "=" * 65)
print("VALIDACAO CONSERVADORA (medias por parcela, LOOCV, n=9)")
print("=" * 65)
qual_p = "EXCELENTE" if rpd_p > 2.5 else ("Bom" if rpd_p > 2.0 else ("Razoavel" if rpd_p > 1.5 else "Fraco"))
print(f"{'PLS (' + str(best_nc) + ' comps)':25s} {r2_p:8.3f} {rmse_p:8.4f} {rpd_p:8.2f}  {qual_p}")

# ========================
# 9. RESUMO E RECOMENDACAO
# ========================
print("\n" + "=" * 65)
print("COMPRIMENTOS DE ONDA MAIS IMPORTANTES (Top 10)")
print("=" * 65)
for i, idx in enumerate(top_idx[:10]):
    print(f"  {i+1:2d}. {wavelengths[idx]:7.1f} nm")

# Identificar regioes espectrais
regioes = {
    'Visivel (400-700 nm)': (400, 700),
    'NIR curto (700-1100 nm)': (700, 1100),
    'NIR medio (1100-1800 nm)': (1100, 1800),
    'NIR longo (1800-2500 nm)': (1800, 2500),
}

print("\n" + "=" * 65)
print("DISTRIBUICAO DOS TOP 20 POR REGIAO ESPECTRAL")
print("=" * 65)
for regiao, (lo, hi) in regioes.items():
    count = sum(1 for idx in top_idx[:20] if lo <= wavelengths[idx] <= hi)
    bar = '#' * count
    print(f"  {regiao:30s}: {bar} ({count})")

print(f"\n{'='*65}")
print("RECOMENDACAO FINAL")
print(f"{'='*65}")
print(f"""
Modelo principal: PLS com {best_nc} componentes
Pre-processamento: SNV + Savitzky-Golay 1a derivada
Validacao: GroupKFold 5-fold (parcelas sempre juntas)

Metricas (val. cruzada com 45 amostras):
  R2  = {results.get(list(results.keys())[0], {}).get('r2', 0):.3f}
  RMSE = {results.get(list(results.keys())[0], {}).get('rmse', 0):.4f}
  RPD = {results.get(list(results.keys())[0], {}).get('rpd', 0):.2f}

Para validacao mais conservadora (medias por parcela, n=9):
  R2  = {r2_p:.3f}
  RMSE = {rmse_p:.4f}
  RPD = {rpd_p:.2f}

Arquivos gerados:
  1. otimizacao_PLS_components.png
  2. predicao_AT_comparacao_modelos.png
  3. importancia_comprimentos_onda_PLS.png
  4. predicao_AT_parcelas_LOOCV.png
""")

print("Pipeline concluido!")
