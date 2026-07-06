"""Gera relatorio Word Relatorio_VitC.docx com resultados NIRS -> Vit. C"""
import pandas as pd, numpy as np, re, os
from scipy.stats import pearsonr, f_oneway
from scipy.signal import savgol_filter
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge, LinearRegression
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("Gerando Relatorio_VitC.docx...")

espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()
col_vitc = dest.columns[8]
vc_map = dest.set_index('Parcela')[col_vitc].to_dict()
amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values; X_raw = espectros[amostras].T.values
def snv(X): return (X-X.mean(axis=1,keepdims=True))/X.std(axis=1,keepdims=True)
X_snv = snv(X_raw)
df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)',a.strip()).groups() for a in amostras],
                        columns=['T','R','F'], index=amostras)
df_meta['Parcela'] = df_meta['T']+df_meta['R']
y = np.array([vc_map[p] for p in df_meta['Parcela']])

anova = f_oneway(*[dest[dest['Tratamento']==t][col_vitc] for t in sorted(dest['Tratamento'].unique())])
corrs_full = np.array([pearsonr(X_snv[:,i],y)[0] for i in range(len(wv))])

gkf = GroupKFold(n_splits=5); grupos = df_meta['Parcela']
pls_res = []
for nc in [1,2,3,5,10,15]:
    preds, reals = [], []
    for seed in range(10):
        for tr,te in gkf.split(X_snv, y, grupos.sample(frac=1, random_state=seed)):
            pls = PLSRegression(n_components=nc); scaler = StandardScaler()
            pls.fit(scaler.fit_transform(X_snv[tr]), y[tr])
            preds.extend(pls.predict(scaler.transform(X_snv[te])))
            reals.extend(y[te])
    r2=r2_score(reals,preds); rmse=np.sqrt(mean_squared_error(reals,preds)); rpd=np.std(y)/rmse
    pls_res.append((nc, r2, rmse, rpd))

df_esp = pd.DataFrame(X_snv); df_esp['Parcela'] = df_meta['Parcela'].values
X_parc = df_esp.groupby('Parcela').mean().values; y_parc = dest[col_vitc].values
loo = LeaveOneOut()
loo_res = []
for nome,mod in [('PLS(1)',PLSRegression(n_components=1)),('PLS(2)',PLSRegression(n_components=2)),
                  ('Ridge(a=0.1)',Ridge(alpha=0.1)),('OLS',LinearRegression())]:
    preds, reals = [], []
    for tr,te in loo.split(X_parc):
        scaler = StandardScaler()
        mod.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
        preds.extend(mod.predict(scaler.transform(X_parc[te])))
        reals.extend(y_parc[te])
    r2=r2_score(reals,preds); rmse=np.sqrt(mean_squared_error(reals,preds)); rpd=np.std(y_parc)/rmse
    loo_res.append((nome, r2, rmse, rpd))

pca = PCA().fit(StandardScaler().fit_transform(X_snv))
X_pc = pca.transform(StandardScaler().fit_transform(X_snv))

# ===== DOCUMENTO =====
doc = Document()
for _ in range(4): doc.add_paragraph()
title = doc.add_paragraph(); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('Relatorio de Resultados'); run.bold = True; run.font.size = Pt(26)
run.font.color.rgb = RGBColor(0, 51, 102)
sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run('Predicao de Vitamina C (Vit. C) por Espectroscopia NIRS'); run.font.size = Pt(14)
run.font.color.rgb = RGBColor(80, 80, 80)
doc.add_paragraph()
dp = doc.add_paragraph(); dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = dp.add_run('Julho de 2026'); run.font.size = Pt(12); run.font.color.rgb = RGBColor(120,120,120)
doc.add_page_break()

# 1. DESCRICAO
doc.add_heading('1. Descricao dos Dados', level=1)
p = doc.add_paragraph()
p.add_run('Objetivo: ').bold = True; p.add_run('Predizer o teor de vitamina C (Vit. C) de tomates utilizando espectros NIRS.')
t = doc.add_table(rows=7, cols=2, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
dados = [('Item','Valor'),('Amostras espectrais',f'{len(y)} frutos'),
         ('Comprimentos de onda',f'{len(wv)} (400 a {wv[-1]:.0f} nm)'),
         ('Parcelas (valores indep.)',f'{df_meta["Parcela"].nunique()}'),
         ('Frutos por parcela','5'),('Vit. C (media +/- DP)',f'{y.mean():.2f} +/- {y.std():.2f}'),
         ('Amplitude Vit. C',f'[{y.min():.2f}, {y.max():.2f}]')]
for i,(k,v) in enumerate(dados):
    for j,val in enumerate([k,v]):
        c=t.cell(i,j); c.text=val
        if i==0:
            for pp in c.paragraphs:
                for rr in pp.runs: rr.bold=True
p = doc.add_paragraph()
p.add_run('Pre-processamento: ').bold = True
p.add_run('SNV, com ou sem derivada Savitzky-Golay.')

# 2. CORRELACAO
doc.add_heading('2. Correlacao Espectro-Vit. C', level=1)
doc.add_paragraph(f'Correlacao de Pearson (n=45).')
p = doc.add_paragraph()
p.add_run(f'Correlacao maxima: |r| = {np.max(np.abs(corrs_full)):.4f}').bold = True
p.add_run(f'\nCorrelacao media: {np.mean(np.abs(corrs_full)):.4f}')
top_c = np.argsort(np.abs(corrs_full))[::-1][:10]
t = doc.add_table(rows=11, cols=3, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['#','Comprimento (nm)','r (Pearson)']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i,idx in enumerate(top_c[:10]):
    t.cell(i+1,0).text=str(i+1); t.cell(i+1,1).text=f'{wv[idx]:.1f}'; t.cell(i+1,2).text=f'{corrs_full[idx]:+.4f}'
p = doc.add_paragraph()
p.add_run('Os comprimentos mais correlacionados estao no NIR medio (~2246 nm), regiao de absorcao de acidos organicos.')

# 3. ANOVA
doc.add_heading('3. Analise de Variancia (ANOVA)', level=1)
doc.add_paragraph(f'ANOVA Vit. C ~ Tratamento: F = {anova.statistic:.3f}, p = {anova.pvalue:.4f}')
p = doc.add_paragraph()
if anova.pvalue > 0.05:
    p.add_run('Resultado: ').bold = True; p.add_run(f'Nao ha diferenca significativa (p = {anova.pvalue:.4f} > 0,05).')
else:
    p.add_run('Resultado: ').bold = True; p.add_run('Ha diferenca significativa (p < 0.05).')

# 4. PCA
doc.add_heading('4. PCA', level=1)
t = doc.add_table(rows=6, cols=4, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['PC','Var. Explicada','Var. Acumulada','r(PC, Vit.C)']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i in range(5):
    t.cell(i+1,0).text=str(i+1); t.cell(i+1,1).text=f'{pca.explained_variance_ratio_[i]*100:.2f}%'
    t.cell(i+1,2).text=f'{sum(pca.explained_variance_ratio_[:i+1])*100:.2f}%'
    t.cell(i+1,3).text=f'{pearsonr(X_pc[:,i],y)[0]:.4f}'

# 5. MODELOS
doc.add_heading('5. Modelos de Machine Learning', level=1)
doc.add_heading('5.1. PLS (45 amostras, GroupKFold)', level=2)
t = doc.add_table(rows=len(pls_res)+1, cols=5, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['Componentes','R2','RMSE','RPD','Qualidade']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i,(nc,r2,rmse,rpd) in enumerate(pls_res):
    qual = 'EXCELENTE' if rpd>2.5 else 'Bom' if rpd>2.0 else 'Razoavel' if rpd>1.5 else 'Fraco'
    t.cell(i+1,0).text=str(nc); t.cell(i+1,1).text=f'{r2:.4f}'
    t.cell(i+1,2).text=f'{rmse:.4f}'; t.cell(i+1,3).text=f'{rpd:.2f}'; t.cell(i+1,4).text=qual
melhor_idx = np.argmax([r2 for _,r2,_,_ in pls_res])
mnc, mr2, mrmse, mrpd = pls_res[melhor_idx]
p = doc.add_paragraph()
p.add_run(f'Melhor: PLS({mnc}) R2={mr2:.3f}, RMSE={mrmse:.4f}, RPD={mrpd:.2f} (Fraco).').bold = True

doc.add_heading('5.2. PLS + Derivada (SG)', level=2)
X_sg = savgol_filter(X_snv, 11, 2, 1, axis=1)
t = doc.add_table(rows=4, cols=4, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['Componentes','R2','RMSE','RPD']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i,nc in enumerate([1,2,3]):
    preds,reals=[],[]
    for seed in range(10):
        for tr,te in gkf.split(X_sg, y, grupos.sample(frac=1, random_state=seed)):
            pls=PLSRegression(n_components=nc); scaler=StandardScaler()
            pls.fit(scaler.fit_transform(X_sg[tr]), y[tr])
            preds.extend(pls.predict(scaler.transform(X_sg[te])))
            reals.extend(y[te])
    r2=r2_score(reals,preds); rmse=np.sqrt(mean_squared_error(reals,preds)); rpd=np.std(y)/rmse
    t.cell(i+1,0).text=str(nc); t.cell(i+1,1).text=f'{r2:.4f}'
    t.cell(i+1,2).text=f'{rmse:.4f}'; t.cell(i+1,3).text=f'{rpd:.2f}'

doc.add_heading('5.3. Medias por Parcela (n=9, LOOCV)', level=2)
t = doc.add_table(rows=len(loo_res)+1, cols=4, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['Modelo','R2','RMSE','RPD']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i,(nome,r2,rmse,rpd) in enumerate(loo_res):
    t.cell(i+1,0).text=nome; t.cell(i+1,1).text=f'{r2:.4f}'
    t.cell(i+1,2).text=f'{rmse:.4f}'; t.cell(i+1,3).text=f'{rpd:.2f}'

# 6. GRAFICOS
doc.add_heading('6. Graficos', level=1)
fig, axes = plt.subplots(2,2,figsize=(14,10))
ax=axes[0,0]
for i in range(min(9,X_raw.shape[0])): ax.plot(wv,X_raw[i],alpha=0.6,lw=0.7)
ax.set_xlabel('Comprimento de onda (nm)',fontsize=11); ax.set_ylabel('Reflectancia',fontsize=11)
ax.set_title('(a) Espectros NIRS brutos',fontsize=12,fontweight='bold'); ax.grid(alpha=0.3)
ax=axes[0,1]; ax.plot(wv,corrs_full,'b-',lw=0.6,alpha=0.7); ax.axhline(0,color='gray',ls='--',alpha=0.5)
ax.set_xlabel('Comprimento de onda (nm)',fontsize=11); ax.set_ylabel('r (Pearson)',fontsize=11)
ax.set_title(f'(b) Correlacao Vit.C-espectro (max|r|={np.max(np.abs(corrs_full)):.3f})',fontsize=12,fontweight='bold')
ax.grid(alpha=0.3)
ax=axes[1,0]
from sklearn.decomposition import PCA as PCA2
X_pca2 = PCA2(2).fit_transform(StandardScaler().fit_transform(X_snv))
sc=ax.scatter(X_pca2[:,0],X_pca2[:,1],c=y,cmap='viridis',s=60,edgecolors='k',lw=0.5)
plt.colorbar(sc,ax=ax,label='Vit. C')
ax.set_xlabel('PC1',fontsize=11); ax.set_ylabel('PC2',fontsize=11)
ax.set_title(f'(c) PCA - r(PC1,Vit.C)={pearsonr(X_pca2[:,0],y)[0]:.3f}',fontsize=12,fontweight='bold')
ax.grid(alpha=0.3)
ax=axes[1,1]
preds_p,reals_p=[],[]
for tr,te in loo.split(X_parc):
    scaler=StandardScaler(); ridge=Ridge(alpha=0.1)
    ridge.fit(scaler.fit_transform(X_parc[tr]),y_parc[tr])
    preds_p.append(ridge.predict(scaler.transform(X_parc[te]))[0]); reals_p.append(y_parc[te][0])
r2_p = r2_score(reals_p,preds_p)
ax.scatter(reals_p,preds_p,c='darkgreen',s=80,edgecolors='k',lw=1,zorder=5)
for i,lbl in enumerate(dest['Parcela']):
    ax.annotate(lbl,(reals_p[i],preds_p[i]),fontsize=7,xytext=(4,4),textcoords='offset points')
m1,m2=min(min(reals_p),min(preds_p))-1,max(max(reals_p),max(preds_p))+1
ax.plot([m1,m2],[m1,m2],'r--',alpha=0.7)
ax.set_xlabel('Vit. C Real',fontsize=11); ax.set_ylabel('Vit. C Predito',fontsize=11)
ax.set_title(f'(d) LOOCV (medias parcela) - R2={r2_p:.3f}',fontsize=12,fontweight='bold')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig('vitc_resultados_graficos.png',dpi=200,bbox_inches='tight')
plt.close()
doc.add_picture('vitc_resultados_graficos.png',width=Inches(6.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('Figura 1. (a) Espectros brutos; (b) Correlacao; (c) PCA; (d) LOOCV.').italic = True

# 7. CONCLUSAO
doc.add_heading('7. Conclusao', level=1)
doc.add_paragraph('A predicao de Vitamina C por NIRS apresentou resultados insatisfatorios.')
doc.add_paragraph(f'PLS({mnc}): R2={mr2:.3f}, RPD={mrpd:.2f} (Fraco).')
doc.add_paragraph(f'Correlacao maxima |r| = {np.max(np.abs(corrs_full)):.3f}, ANOVA p={anova.pvalue:.4f} (N.S.).')

doc.add_paragraph()
p = doc.add_paragraph()
p.add_run('Comparacao entre parametros:').bold = True

t = doc.add_table(rows=4, cols=4, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['Parametro','R2 (PLS)','RPD','max |r|']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
t.cell(1,0).text='AT'; t.cell(1,1).text='0,093'; t.cell(1,2).text='1,05'; t.cell(1,3).text='0,464'
t.cell(2,0).text='Vit. C'; t.cell(2,1).text=f'{mr2:.3f}'; t.cell(2,2).text=f'{mrpd:.2f}'; t.cell(2,3).text=f'{np.max(np.abs(corrs_full)):.3f}'
t.cell(3,0).text='Firm'; t.cell(3,1).text='0,765'; t.cell(3,2).text='2,06'; t.cell(3,3).text='0,890'

output = 'Relatorio_VitC.docx'
doc.save(output)
print(f"Documento salvo: {output} ({os.path.getsize(output)/1024:.0f} KB)")
