"""
Pipeline NIRS -> Firm (Firmeza)
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
print("="*60)
print("NIRS -> FIRM (Firmeza) - PIPELINE")
print("="*60)

espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()
firm_map = dest.set_index('Parcela')['Firm'].to_dict()
amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values; X_raw = espectros[amostras].T.values
def snv(X): return (X-X.mean(axis=1,keepdims=True))/X.std(axis=1,keepdims=True)
X_snv = snv(X_raw)

# --- REMOCAO DE FAIXAS RUIDOSAS (Recomendacao 9.2) ---
from nirs_utils import criar_mascara_comprimentos, FAIXAS_REMOVER
print('\n--- Remocao de faixas espectrais ruidosas ---')
mask, n_rem = criar_mascara_comprimentos(wv)
print(f'  Removendo {n_rem}/{len(wv)} pontos ({n_rem/len(wv)*100:.1f}%)')
X_snv = X_snv[:, mask]
X_raw = X_raw[:, mask]
wv = wv[mask]
print(f'  Comprimentos mantidos: {len(wv)}')
# ---

df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)',a.strip()).groups() for a in amostras],
                        columns=['T','R','F'], index=amostras)
df_meta['Parcela'] = df_meta['T']+df_meta['R']
y = np.array([firm_map[p] for p in df_meta['Parcela']])
print(f'\nDados: {len(y)} amostras, {len(wv)} features, {df_meta["Parcela"].nunique()} parcelas')
print(f'Firm: media={y.mean():.2f}, std={y.std():.2f}, [{y.min():.2f}, {y.max():.2f}]')

anova = f_oneway(*[dest[dest['Tratamento']==t]['Firm'] for t in sorted(dest['Tratamento'].unique())])
print(f'ANOVA Firm~Tratamento: F={anova.statistic:.3f}, p={anova.pvalue:.4f}')

corrs = np.array([pearsonr(X_snv[:,i],y)[0] for i in range(len(wv))])
print(f'Corr. maxima |r| = {np.max(np.abs(corrs)):.4f}')
print(f'Corr. media |r| = {np.mean(np.abs(corrs)):.4f}')
top5 = np.argsort(np.abs(corrs))[::-1][:5]
print('Top 5 comprimentos:')
for idx in top5:
    print(f'  {wv[idx]:.1f} nm  r={corrs[idx]:+.4f}')

# PLS - GroupKFold
print('\n--- PLS com GroupKFold 5-fold (10 rep) ---')
gkf = GroupKFold(n_splits=5); grupos = df_meta['Parcela']
best = {'r2': -999, 'nc': 0}
for nc in [1,2,3,5,10,15]:
    preds, reals = [], []
    for seed in range(10):
        for tr,te in gkf.split(X_snv, y, grupos.sample(frac=1, random_state=seed)):
            pls = PLSRegression(n_components=nc); scaler = StandardScaler()
            pls.fit(scaler.fit_transform(X_snv[tr]), y[tr])
            preds.extend(pls.predict(scaler.transform(X_snv[te])))
            reals.extend(y[te])
    r2 = r2_score(reals,preds); rmse = np.sqrt(mean_squared_error(reals,preds)); rpd = np.std(y)/rmse
    qual = 'EXCELENTE' if rpd>2.5 else 'Bom' if rpd>2.0 else 'Razoavel' if rpd>1.5 else 'Fraco'
    print(f'  PLS(n={nc:2d})  R2={r2:7.3f}  RMSE={rmse:.4f}  RPD={rpd:.2f}  {qual}')
    if r2 > best['r2']: best = {'r2': r2, 'nc': nc, 'rmse': rmse, 'rpd': rpd}

# PLS + SG
print('\n--- PLS + Savitzky-Golay ---')
X_sg = savgol_filter(X_snv, 11, 2, 1, axis=1)
for nc in [1,2,3]:
    preds, reals = [], []
    for seed in range(10):
        for tr,te in gkf.split(X_sg, y, grupos.sample(frac=1, random_state=seed)):
            pls = PLSRegression(n_components=nc); scaler = StandardScaler()
            pls.fit(scaler.fit_transform(X_sg[tr]), y[tr])
            preds.extend(pls.predict(scaler.transform(X_sg[te])))
            reals.extend(y[te])
    r2 = r2_score(reals,preds); rmse = np.sqrt(mean_squared_error(reals,preds))
    print(f'  PLS+SG(n={nc})  R2={r2:.3f}  RMSE={rmse:.4f}')

# LOOCV com 9 medias
print('\n--- MEDIAS POR PARCELA (n=9, LOOCV) ---')
df_esp = pd.DataFrame(X_snv); df_esp['Parcela'] = df_meta['Parcela'].values
X_parc = df_esp.groupby('Parcela').mean().values; y_parc = dest['Firm'].values
loo = LeaveOneOut()
for nome,mod in [('PLS(1)',PLSRegression(n_components=1)),('PLS(2)',PLSRegression(n_components=2)),
                  ('Ridge',Ridge(alpha=0.1)),('OLS',LinearRegression())]:
    preds, reals = [], []
    for tr,te in loo.split(X_parc):
        scaler = StandardScaler()
        mod.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
        preds.extend(mod.predict(scaler.transform(X_parc[te])))
        reals.extend(y_parc[te])
    r2 = r2_score(reals,preds); rmse = np.sqrt(mean_squared_error(reals,preds))
    print(f'  {nome:10s}  R2={r2:.3f}  RMSE={rmse:.4f}')

# PCA
print('\n--- PCA ---')
pca = PCA().fit(StandardScaler().fit_transform(X_snv))
X_pc = pca.transform(StandardScaler().fit_transform(X_snv))
for i in range(5):
    r = pearsonr(X_pc[:,i],y)[0]
    print(f'  PC{i+1}: var={pca.explained_variance_ratio_[i]:.2%}, r(Firm)={r:.4f}')

# GRAFICO
fig, axes = plt.subplots(2,2,figsize=(14,10))
ax=axes[0,0]
for i in range(min(9,X_raw.shape[0])): ax.plot(wv,X_raw[i],alpha=0.6,lw=0.7)
ax.set_xlabel('nm'); ax.set_ylabel('Reflectancia'); ax.set_title('Espectros brutos'); ax.grid(alpha=0.3)

ax=axes[0,1]; ax.plot(wv,corrs,'b-',lw=0.6,alpha=0.7); ax.axhline(0,color='gray',ls='--',alpha=0.5)
ax.set_xlabel('nm'); ax.set_ylabel('r'); ax.set_title(f'Correlacao Firm-espectro (max|r|={np.max(np.abs(corrs)):.3f})')
ax.grid(alpha=0.3)

ax=axes[1,0]
X_pca2 = PCA(2).fit_transform(StandardScaler().fit_transform(X_snv))
sc=ax.scatter(X_pca2[:,0],X_pca2[:,1],c=y,cmap='viridis',s=60,edgecolors='k',lw=0.5)
plt.colorbar(sc,ax=ax,label='Firm'); ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
ax.set_title(f'PCA (r(PC1,Firm)={pearsonr(X_pca2[:,0],y)[0]:.3f})'); ax.grid(alpha=0.3)

ax=axes[1,1]
preds_p,reals_p=[],[]
for tr,te in loo.split(X_parc):
    scaler=StandardScaler(); ridge=Ridge(alpha=0.1)
    ridge.fit(scaler.fit_transform(X_parc[tr]),y_parc[tr])
    preds_p.append(ridge.predict(scaler.transform(X_parc[te]))[0]); reals_p.append(y_parc[te][0])
r2_loo = r2_score(reals_p,preds_p)
ax.scatter(reals_p,preds_p,c='darkgreen',s=80,edgecolors='k',lw=1,zorder=5)
for i,lbl in enumerate(dest['Parcela']): ax.annotate(lbl,(reals_p[i],preds_p[i]),fontsize=7,xytext=(4,4),textcoords='offset points')
m1,m2=min(min(reals_p),min(preds_p))-0.5,max(max(reals_p),max(preds_p))+0.5
ax.plot([m1,m2],[m1,m2],'r--',alpha=0.7)
ax.set_xlabel('Firm Real'); ax.set_ylabel('Firm Predito')
ax.set_title(f'LOOCV (n=9) - Ridge - R2={r2_loo:.3f}'); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig('analise_Firm_NIRS_final.png',dpi=150)
print('\nGrafico: analise_Firm_NIRS_final.png')

print(f'\nTempo total: {time.time()-t0:.1f}s')
print('\n' + '='*60)
print('RESUMO')
print('='*60)
print(f'Melhor PLS: n={best["nc"]}, R2={best["r2"]:.3f}, RMSE={best["rmse"]:.4f}, RPD={best["rpd"]:.2f}')
print(f'Correlacao maxima |r| = {np.max(np.abs(corrs)):.3f}')
print(f'PCA: PC1 var={pca.explained_variance_ratio_[0]:.1%}, r(Firm)={pearsonr(X_pc[:,0],y)[0]:.3f}')
print(f'LOOCV (medias parcela): R2={r2_loo:.3f}')
