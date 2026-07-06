"""
Pipeline NIRS -> pH, SS, SS/AT
"""
import pandas as pd, numpy as np, re, time
from scipy.signal import savgol_filter
from scipy.stats import pearsonr, f_oneway
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge, LinearRegression
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

t0 = time.time()
print("="*65)
print("NIRS -> pH / SS / SS:AT - PIPELINE COMPLETO")
print("="*65)

espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()
amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values; X_raw = espectros[amostras].T.values
def snv(X): return (X-X.mean(axis=1,keepdims=True))/X.std(axis=1,keepdims=True)
X_snv = snv(X_raw)
df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)',a.strip()).groups() for a in amostras],
                        columns=['T','R','F'], index=amostras)
df_meta['Parcela'] = df_meta['T']+df_meta['R']
gkf = GroupKFold(n_splits=5); grupos = df_meta['Parcela']

# Encontrar indices das colunas
col_map = {}
for nome_possivel in ['pH', 'SS', 'SS/AT']:
    for i, c in enumerate(dest.columns):
        if nome_possivel in c.strip():
            col_map[nome_possivel] = i
            break

parametros = [
    ('pH', dest.columns[col_map['pH']]),
    ('SS (Solidos Soluveis)', dest.columns[col_map['SS']]),
    ('SS/AT (Razao)', dest.columns[col_map['SS/AT']]),
]

resultados_gerais = {}

for param_nome, col_nome in parametros:
    print(f"\n{'='*65}")
    print(f" ANALISE: {param_nome}")
    print(f"{'='*65}")

    y = np.array([dest.set_index('Parcela')[col_nome].to_dict()[p] for p in df_meta['Parcela']])
    print(f'  Dados: {len(y)} amostras, {df_meta["Parcela"].nunique()} parcelas')
    print(f'  {param_nome}: media={y.mean():.4f}, std={y.std():.4f}, [{y.min():.4f}, {y.max():.4f}]')

    anova = f_oneway(*[dest[dest['Tratamento']==t][col_nome] for t in sorted(dest['Tratamento'].unique())])
    print(f'  ANOVA~Tratamento: F={anova.statistic:.3f}, p={anova.pvalue:.4f}')

    corrs = np.array([pearsonr(X_snv[:,i],y)[0] for i in range(len(wv))])
    print(f'  Corr. maxima |r| = {np.max(np.abs(corrs)):.4f}')
    print(f'  Corr. media |r| = {np.mean(np.abs(corrs)):.4f}')

    # PLS GroupKFold
    best = {'r2': -999, 'nc': 0}
    print(f'  {"PLS GroupKFold (10 rep):":30s}', end='')
    for nc in [1,2,3,5,10,15]:
        preds, reals = [], []
        for seed in range(10):
            for tr,te in gkf.split(X_snv, y, grupos.sample(frac=1, random_state=seed)):
                pls = PLSRegression(n_components=nc); scaler = StandardScaler()
                pls.fit(scaler.fit_transform(X_snv[tr]), y[tr])
                preds.extend(pls.predict(scaler.transform(X_snv[te])))
                reals.extend(y[te])
        r2 = r2_score(reals,preds); rmse = np.sqrt(mean_squared_error(reals,preds)); rpd = np.std(y)/rmse
        qual = 'EXCEL' if rpd>2.5 else 'Bom' if rpd>2.0 else 'Razoavel' if rpd>1.5 else 'Fraco'
        if nc==1: print(f'\n  {"":30s}', end='')
        print(f'  n={nc:2d} R2={r2:.3f}/{rpd:.2f}({qual})', end='')
        if r2 > best['r2']: best = {'r2': r2, 'nc': nc, 'rmse': rmse, 'rpd': rpd}
    print()

    # LOOCV medias parcela
    df_esp = pd.DataFrame(X_snv); df_esp['Parcela'] = df_meta['Parcela'].values
    X_parc = df_esp.groupby('Parcela').mean().values; y_parc = dest[col_nome].values
    loo = LeaveOneOut()
    loo_melhores = []
    for nome_m,mod in [('PLS1',PLSRegression(1)),('PLS2',PLSRegression(2)),
                        ('Ridge',Ridge(0.1)),('OLS',LinearRegression())]:
        preds, reals = [], []
        for tr,te in loo.split(X_parc):
            scaler = StandardScaler()
            mod.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
            preds.extend(mod.predict(scaler.transform(X_parc[te])))
            reals.extend(y_parc[te])
        r2 = r2_score(reals,preds); loo_melhores.append((nome_m, r2))
    print(f'  LOOCV (n=9): {", ".join([f"{n}:R2={r2:.3f}" for n,r2 in loo_melhores])}')

    # PCA
    pca = PCA().fit(StandardScaler().fit_transform(X_snv))
    X_pc = pca.transform(StandardScaler().fit_transform(X_snv))
    print(f'  PCA: PC1 var={pca.explained_variance_ratio_[0]:.1%}, r={pearsonr(X_pc[:,0],y)[0]:.3f}')

    resultados_gerais[param_nome] = {
        'best': best, 'corr_max': np.max(np.abs(corrs)),
        'corr_media': np.mean(np.abs(corrs)),
        'anova_p': anova.pvalue, 'pca_r': pearsonr(X_pc[:,0],y)[0],
        'loo_best': max(loo_melhores, key=lambda x: x[1]),
        'dados': {'n': len(y), 'media': y.mean(), 'std': y.std(), 'min': y.min(), 'max': y.max()}
    }

# ===== TABELA COMPARATIVA FINAL =====
print(f"\n{'='*65}")
print("TABELA COMPARATIVA - TODOS OS PARAMETROS")
print(f"{'='*65}")
print(f"{'Parametro':20s} {'R2(PLS)':>9s} {'RPD':>6s} {'max|r|':>7s} {'ANOVA(p)':>9s} {'PC1(r)':>7s} {'Qualif'}")
print("-"*65)
for p_nome, res in resultados_gerais.items():
    b = res['best']
    qual = 'EXCELENTE' if b['rpd']>2.5 else 'Bom' if b['rpd']>2.0 else 'Razoavel' if b['rpd']>1.5 else 'Fraco'
    print(f"{p_nome:20s} {b['r2']:9.3f} {b['rpd']:6.2f} {res['corr_max']:7.3f} {res['anova_p']:9.4f} {res['pca_r']:7.3f} {qual}")

# Incluir AT, Firm, Vit.C da tabela
print(f"\n{'='*65}")
print("COMPARATIVO COM ANALISES ANTERIORES")
print(f"{'='*65}")
print(f"{'Parametro':20s} {'R2(PLS)':>9s} {'RPD':>6s} {'max|r|':>7s} {'ANOVA(p)':>9s} {'Qualif'}")
print("-"*65)
dados_prev = [
    ('AT', 0.093, 1.05, 0.464, 0.6293, 'Fraco'),
    ('Vit. C', 0.236, 1.14, 0.593, 0.2945, 'Fraco'),
    ('Firm', 0.765, 2.06, 0.890, 0.0011, 'Bom'),
]
for nome, r2, rpd, rmax, ap, qual in dados_prev:
    print(f"{nome:20s} {r2:9.3f} {rpd:6.2f} {rmax:7.3f} {ap:9.4f} {qual}")

print(f"\nTempo total: {time.time()-t0:.1f}s")
print("Pipeline concluido!")
