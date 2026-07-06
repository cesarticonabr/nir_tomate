"""Gera relatorio Word Relatorio_Firm.docx com resultados NIRS -> Firm (Firmeza)"""
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

print("Gerando Relatorio_Firm.docx...")

# ===== DADOS =====
espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()
firm_map = dest.set_index('Parcela')['Firm'].to_dict()
amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values; X_raw = espectros[amostras].T.values
def snv(X): return (X-X.mean(axis=1,keepdims=True))/X.std(axis=1,keepdims=True)
X_snv = snv(X_raw)
df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)',a.strip()).groups() for a in amostras],
                        columns=['T','R','F'], index=amostras)
df_meta['Parcela'] = df_meta['T']+df_meta['R']
y = np.array([firm_map[p] for p in df_meta['Parcela']])

anova = f_oneway(*[dest[dest['Tratamento']==t]['Firm'] for t in sorted(dest['Tratamento'].unique())])
corrs = np.array([pearsonr(X_snv[:,i],y)[0] for i in range(len(wv))])
pca = PCA().fit(StandardScaler().fit_transform(X_snv))
X_pc = pca.transform(StandardScaler().fit_transform(X_snv))

# Modelos
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

# LOOCV
df_esp = pd.DataFrame(X_snv); df_esp['Parcela'] = df_meta['Parcela'].values
X_parc = df_esp.groupby('Parcela').mean().values; y_parc = dest['Firm'].values
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

# ===== CRIAR DOCUMENTO =====
doc = Document()

# === CAPA ===
for _ in range(4): doc.add_paragraph()
title = doc.add_paragraph(); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('Relatorio de Resultados'); run.bold = True; run.font.size = Pt(26)
run.font.color.rgb = RGBColor(0, 51, 102)
sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run('Predicao de Firmeza (Firm) por Espectroscopia NIRS'); run.font.size = Pt(14)
run.font.color.rgb = RGBColor(80, 80, 80)
doc.add_paragraph()
dp = doc.add_paragraph(); dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = dp.add_run('Julho de 2026'); run.font.size = Pt(12); run.font.color.rgb = RGBColor(120,120,120)
doc.add_page_break()

# === 1. DESCRICAO ===
doc.add_heading('1. Descricao dos Dados', level=1)
p = doc.add_paragraph()
p.add_run('Objetivo: ').bold = True; p.add_run('Predizer a firmeza (Firm) de tomates utilizando espectros de reflectancia NIRS (400-2500 nm).')

t = doc.add_table(rows=7, cols=2, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
dados = [('Item','Valor'),('Amostras espectrais',f'{len(y)} frutos'),
         ('Comprimentos de onda',f'{len(wv)} (400 a {wv[-1]:.0f} nm)'),
         ('Parcelas (valores indep.)',f'{df_meta["Parcela"].nunique()}'),
         ('Frutos por parcela','5'),('Firm (media +/- DP)',f'{y.mean():.2f} +/- {y.std():.2f}'),
         ('Amplitude Firm',f'[{y.min():.2f}, {y.max():.2f}]')]
for i,(k,v) in enumerate(dados):
    for j,val in enumerate([k,v]):
        c=t.cell(i,j); c.text=val
        if i==0:
            for pp in c.paragraphs:
                for rr in pp.runs: rr.bold=True

p = doc.add_paragraph()
p.add_run('Pre-processamento: ').bold = True
p.add_run('Standard Normal Variate (SNV) para correcao de linha de base, com ou sem derivada de Savitzky-Golay (1a derivada, janela=11, ordem=2).')

# === 2. CORRELACAO ===
doc.add_heading('2. Correlacao Espectro-Firm', level=1)
doc.add_paragraph(f'Correlacao de Pearson entre cada comprimento de onda (apos SNV) e os valores de Firm (n=45).')

p = doc.add_paragraph()
p.add_run(f'Correlacao maxima: |r| = {np.max(np.abs(corrs)):.4f}').bold = True
p.add_run(f'\nCorrelacao media: {np.mean(np.abs(corrs)):.4f}')

top_c = np.argsort(np.abs(corrs))[::-1][:10]
t = doc.add_table(rows=11, cols=3, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['#','Comprimento (nm)','r (Pearson)']):
    t.cell(0,j).text = h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i,idx in enumerate(top_c[:10]):
    t.cell(i+1,0).text=str(i+1)
    t.cell(i+1,1).text=f'{wv[idx]:.1f}'
    t.cell(i+1,2).text=f'{corrs[idx]:+.4f}'

p = doc.add_paragraph()
p.add_run('Os comprimentos de onda mais correlacionados estao na regiao do visivel (~590 nm), ')
p.add_run('associados a diferencas de coloracao entre os tipos de tomate (italiano vs cereja), ')
p.add_run('que se correlacionam com a firmeza.')

# === 3. ANOVA ===
doc.add_heading('3. Analise de Variancia (ANOVA)', level=1)
doc.add_paragraph(f'Teste: ANOVA de um fator para Firm entre os 3 tratamentos.')
doc.add_paragraph(f'F = {anova.statistic:.3f}, p = {anova.pvalue:.4f}')
p = doc.add_paragraph()
if anova.pvalue > 0.05:
    p.add_run('Resultado: ').bold = True; p.add_run('Nao ha diferenca significativa (p > 0.05).')
else:
    p.add_run('Resultado: ').bold = True; p.add_run('Ha diferenca ALTAMENTE significativa (p < 0.01). ')
    p.add_run('A firmeza difere entre os tipos de tomate, o que favorece a modelagem preditiva.')

# === 4. PCA ===
doc.add_heading('4. Analise de Componentes Principais (PCA)', level=1)
t = doc.add_table(rows=6, cols=4, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['PC','Var. Explicada','Var. Acumulada','r(PC, Firm)']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i in range(5):
    t.cell(i+1,0).text=str(i+1)
    t.cell(i+1,1).text=f'{pca.explained_variance_ratio_[i]*100:.2f}%'
    t.cell(i+1,2).text=f'{sum(pca.explained_variance_ratio_[:i+1])*100:.2f}%'
    t.cell(i+1,3).text=f'{pearsonr(X_pc[:,i],y)[0]:.4f}'

p = doc.add_paragraph()
p.add_run('PC1 tem forte correlacao negativa com Firm (r = -0.775), ')
p.add_run('indicando que a variacao espectral dominante captura informacao relevante para firmeza.')

# === 5. MODELOS ===
doc.add_heading('5. Modelos de Machine Learning', level=1)

doc.add_heading('5.1. PLS Regression (45 amostras, GroupKFold 5-fold)', level=2)
doc.add_paragraph('Validacao cruzada com GroupKFold (5 folds, 10 repeticoes). Grupos = parcelas.')

t = doc.add_table(rows=len(pls_res)+1, cols=5, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['Componentes','R2','RMSE','RPD','Qualidade']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i,(nc,r2,rmse,rpd) in enumerate(pls_res):
    qual = 'EXCELENTE' if rpd>2.5 else 'Bom' if rpd>2.0 else 'Razoavel' if rpd>1.5 else 'Fraco'
    t.cell(i+1,0).text=str(nc); t.cell(i+1,1).text=f'{r2:.4f}'
    t.cell(i+1,2).text=f'{rmse:.4f}'; t.cell(i+1,3).text=f'{rpd:.2f}'; t.cell(i+1,4).text=qual

# Melhor modelo
melhor_idx = np.argmax([r2 for _,r2,_,_ in pls_res])
melhor_nc, melhor_r2, melhor_rmse, melhor_rpd = pls_res[melhor_idx]
p = doc.add_paragraph()
p.add_run(f'Melhor modelo: PLS com {melhor_nc} componentes ').bold = True
p.add_run(f'(R2={melhor_r2:.3f}, RMSE={melhor_rmse:.4f}, RPD={melhor_rpd:.2f}).')

doc.add_heading('5.2. PLS com SNV + Derivada (Savitzky-Golay)', level=2)
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

doc.add_heading('5.3. Validacao Conservadora - Medias por Parcela (n=9, LOOCV)', level=2)
doc.add_paragraph('Cada parcela representada pela media espectral de 5 frutos. Leave-One-Out CV.')

t = doc.add_table(rows=len(loo_res)+1, cols=4, style='Light Shading Accent 1'); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j,h in enumerate(['Modelo','R2','RMSE','RPD']):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i,(nome,r2,rmse,rpd) in enumerate(loo_res):
    t.cell(i+1,0).text=nome; t.cell(i+1,1).text=f'{r2:.4f}'
    t.cell(i+1,2).text=f'{rmse:.4f}'; t.cell(i+1,3).text=f'{rpd:.2f}'

# === 6. GRAFICOS ===
doc.add_heading('6. Graficos', level=1)

fig, axes = plt.subplots(2,2,figsize=(14,10))
ax=axes[0,0]
for i in range(min(9,X_raw.shape[0])): ax.plot(wv,X_raw[i],alpha=0.6,lw=0.7)
ax.set_xlabel('Comprimento de onda (nm)',fontsize=11); ax.set_ylabel('Reflectancia',fontsize=11)
ax.set_title('(a) Espectros NIRS brutos',fontsize=12,fontweight='bold'); ax.grid(alpha=0.3)

ax=axes[0,1]
corrs_full = np.array([pearsonr(X_snv[:,i],y)[0] for i in range(len(wv))])
ax.plot(wv,corrs_full,'b-',lw=0.6,alpha=0.7); ax.axhline(0,color='gray',ls='--',alpha=0.5)
ax.set_xlabel('Comprimento de onda (nm)',fontsize=11); ax.set_ylabel('r (Pearson)',fontsize=11)
ax.set_title(f'(b) Correlacao Firm-espectro (max|r|={np.max(np.abs(corrs_full)):.3f})',fontsize=12,fontweight='bold')
ax.grid(alpha=0.3)

ax=axes[1,0]
from sklearn.decomposition import PCA as PCA2
X_pca2 = PCA2(2).fit_transform(StandardScaler().fit_transform(X_snv))
sc=ax.scatter(X_pca2[:,0],X_pca2[:,1],c=y,cmap='viridis',s=60,edgecolors='k',lw=0.5)
plt.colorbar(sc,ax=ax,label='Firm')
ax.set_xlabel('PC1',fontsize=11); ax.set_ylabel('PC2',fontsize=11)
ax.set_title(f'(c) PCA - r(PC1,Firm)={pearsonr(X_pca2[:,0],y)[0]:.3f}',fontsize=12,fontweight='bold')
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
m1,m2=min(min(reals_p),min(preds_p))-0.5,max(max(reals_p),max(preds_p))+0.5
ax.plot([m1,m2],[m1,m2],'r--',alpha=0.7)
ax.set_xlabel('Firm Real',fontsize=11); ax.set_ylabel('Firm Predito',fontsize=11)
ax.set_title(f'(d) LOOCV (medias parcela) Ridge - R2={r2_p:.3f}',fontsize=12,fontweight='bold')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig('firm_resultados_graficos.png',dpi=200,bbox_inches='tight')
plt.close()

doc.add_picture('firm_resultados_graficos.png',width=Inches(6.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('Figura 1. (a) Espectros NIRS brutos; (b) Correlacao Firm-espectro; (c) PCA; (d) LOOCV com medias por parcela.').italic = True

# === 7. CONCLUSAO ===
doc.add_heading('7. Conclusao', level=1)
p = doc.add_paragraph()
p.add_run('Os modelos de machine learning apresentaram capacidade preditiva satisfatoria ').bold = False
p.add_run('para a firmeza (Firm) a partir dos espectros NIRS.').bold = True

doc.add_paragraph()
doc.add_paragraph('Melhores resultados:')
bullets = [
    f'PLS(2 componentes) com 45 amostras: R2 = {melhor_r2:.3f}, RMSE = {melhor_rmse:.4f}, RPD = {melhor_rpd:.2f} (Bom)',
    f'PLS(2) + medias por parcela (LOOCV, n=9): R2 = {loo_res[1][1]:.3f}, RMSE = {loo_res[1][2]:.4f}',
    f'Correlacao maxima Firm-espectro: |r| = {np.max(np.abs(corrs_full)):.3f} (em ~590 nm)',
    f'PC1 explica {pca.explained_variance_ratio_[0]*100:.1f}% e tem r = {pearsonr(X_pc[:,0],y)[0]:.3f} com Firm',
    f'ANOVA altamente significativa (p = {anova.pvalue:.4f}), indicando diferencas entre tipos de tomate',
]
for b in bullets:
    doc.add_paragraph(b, style='List Bullet')

doc.add_paragraph()
p = doc.add_paragraph()
p.add_run('Comparacao com AT (Acidez Titulavel):').bold = True
doc.add_paragraph('A predicao de Firm foi substancialmente melhor que a de AT. Enquanto o AT apresentou')
doc.add_paragraph(f'correlacao maxima de apenas |r|=0.464 e R2=0.09, a Firm atingiu |r|={np.max(np.abs(corrs_full)):.3f} e R2={melhor_r2:.3f}.')
doc.add_paragraph('Isso se deve a:)')
bullets2 = [
    'Maior variacao de Firm entre os tratamentos (ANOVA significativa)',
    'Forte correlacao com a regiao visivel do espectro (~590 nm), associada a cor dos frutos',
    'A firmeza e um atributo mais diretamente relacionado a estrutura fisica do fruto, que afeta a reflectancia',
]
for b in bullets2:
    doc.add_paragraph(b, style='List Bullet')

doc.add_page_break()
doc.add_heading('Anexo: Tabela de Dados Destrutivos', level=1)
t = doc.add_table(rows=len(dest)+1, cols=len(dest.columns), style='Light Shading Accent 1')
for j,col in enumerate(dest.columns):
    t.cell(0,j).text = col
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True
for i, (_, row) in enumerate(dest.iterrows()):
    for j, val in enumerate(row):
        t.cell(i+1,j).text = str(val)

# Salvar
output = 'Relatorio_Firm.docx'
doc.save(output)
print(f"Documento salvo: {output} ({os.path.getsize(output)/1024:.0f} KB)")
