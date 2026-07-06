"""Gera relatorio Word (resultados1.docx) com os resultados do pipeline NIRS -> AT"""
import pandas as pd, numpy as np, re, os, sys
from scipy.stats import pearsonr
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("Gerando relatorio resultados1.docx...")

# ===== DADOS =====
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
from scipy.stats import f_oneway
anova = f_oneway(*[dest[dest['Tratamento']==t]['AT'] for t in sorted(dest['Tratamento'].unique())])
def snv(X): return (X-X.mean(axis=1,keepdims=True))/X.std(axis=1,keepdims=True)
X_snv = snv(X_raw)
corrs = np.array([pearsonr(X_snv[:,i],y)[0] for i in range(0, len(wv), 5)])

# Reexecutar modelos para ter dados frescos
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.decomposition import PCA

gkf = GroupKFold(n_splits=5); grupos = df_meta['Parcela']
# PLS resultados com 45 amostras
pls_results = []
for nc in [1,2,3,5,10,15]:
    preds, reals = [], []
    for seed in range(20):
        for tr,te in gkf.split(X_snv, y, grupos.sample(frac=1, random_state=seed)):
            pls = PLSRegression(n_components=nc); scaler = StandardScaler()
            pls.fit(scaler.fit_transform(X_snv[tr]), y[tr])
            preds.extend(pls.predict(scaler.transform(X_snv[te])))
            reals.extend(y[te])
    r2 = r2_score(reals,preds); rmse = np.sqrt(mean_squared_error(reals,preds)); rpd = np.std(y)/rmse
    pls_results.append((nc, r2, rmse, rpd))

# PLS com SG
from scipy.signal import savgol_filter
X_sg = savgol_filter(X_snv, 11, 2, 1, axis=1)
pls_sg_results = []
for nc in [1,2,3]:
    preds, reals = [], []
    for seed in range(20):
        for tr,te in gkf.split(X_sg, y, grupos.sample(frac=1, random_state=seed)):
            pls = PLSRegression(n_components=nc); scaler = StandardScaler()
            pls.fit(scaler.fit_transform(X_sg[tr]), y[tr])
            preds.extend(pls.predict(scaler.transform(X_sg[te])))
            reals.extend(y[te])
    r2 = r2_score(reals,preds); rmse = np.sqrt(mean_squared_error(reals,preds)); rpd = np.std(y)/rmse
    pls_sg_results.append((nc, r2, rmse, rpd))

# LOOCV com 9 medias
df_esp = pd.DataFrame(X_snv); df_esp['Parcela'] = df_meta['Parcela'].values
X_parc = df_esp.groupby('Parcela').mean().values; y_parc = dest['AT'].values
loo = LeaveOneOut()
loo_results = []
from sklearn.linear_model import Ridge, LinearRegression
for nome,mod in [('PLS(1)',PLSRegression(n_components=1)),('PLS(2)',PLSRegression(n_components=2)),
                  ('Ridge(a=0.1)',Ridge(alpha=0.1)),('OLS',LinearRegression())]:
    preds, reals = [], []
    for tr,te in loo.split(X_parc):
        scaler = StandardScaler()
        mod.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
        preds.extend(mod.predict(scaler.transform(X_parc[te])))
        reals.extend(y_parc[te])
    r2 = r2_score(reals,preds); rmse = np.sqrt(mean_squared_error(reals,preds)); rpd = np.std(y_parc)/rmse
    loo_results.append((nome, r2, rmse, rpd))

# PCA
pca = PCA().fit(StandardScaler().fit_transform(X_snv))
X_pca = pca.transform(StandardScaler().fit_transform(X_snv))
pca_results = [(i+1, pca.explained_variance_ratio_[i], pearsonr(X_pca[:,i], y)[0]) for i in range(5)]

# ===== CRIAR DOCUMENTO =====
doc = Document()

# Estilo
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)

# ===== CAPA =====
for _ in range(4):
    doc.add_paragraph()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('Relatorio de Resultados')
run.bold = True
run.font.size = Pt(26)
run.font.color.rgb = RGBColor(0, 51, 102)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('Predicao de Acidez Titulavel (AT) por Espectroscopia NIRS')
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(80, 80, 80)

doc.add_paragraph()
date_p = doc.add_paragraph()
date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = date_p.add_run('Julho de 2026')
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(120, 120, 120)

doc.add_page_break()

# ===== 1. INTRODUCAO =====
doc.add_heading('1. Descricao dos Dados', level=1)

p = doc.add_paragraph()
p.add_run('Objetivo: ').bold = True
p.add_run('Predizer a acidez titulavel (AT) de tomates utilizando espectros de reflectância NIRS (400-2500 nm).')

doc.add_paragraph()
tabela_intro = doc.add_table(rows=7, cols=2, style='Light Shading Accent 1')
tabela_intro.alignment = WD_TABLE_ALIGNMENT.CENTER
dados_intro = [
    ('Item', 'Valor'),
    ('Amostras espectrais', f'{len(y)} frutos'),
    ('Comprimentos de onda', f'{len(wv)} (400 a {wv[-1]:.0f} nm, passo 0.5 nm)'),
    ('Parcelas (valores indep. de AT)', f'{df_meta["Parcela"].nunique()} (3 tratamentos x 3 repeticoes)'),
    ('Frutos por parcela', '5 (media espectral usada como preditor)'),
    ('AT (media +/- DP)', f'{y.mean():.4f} +/- {y.std():.4f}'),
    ('Amplitude AT', f'[{y.min():.4f}, {y.max():.4f}]'),
]
for i, (k, v) in enumerate(dados_intro):
    for j, val in enumerate([k, v]):
        cell = tabela_intro.cell(i, j)
        cell.text = val
        if i == 0:
            for p_ in cell.paragraphs:
                for r_ in p_.runs:
                    r_.bold = True

p = doc.add_paragraph()
p.add_run('Dados espectrais: ').bold = True
p.add_run('45 frutos de tomate (3 tratamentos, 3 repeticoes, 5 frutos cada) medidos por espectroscopia NIRS de reflectância (4200 comprimentos de onda). Os valores de AT foram medidos destrutivamente por parcela (1 valor para cada 5 frutos).')

p = doc.add_paragraph()
p.add_run('Pre-processamento: ').bold = True
p.add_run('Standard Normal Variate (SNV) para correcao de linha de base e escala, seguido ou nao de derivada de Savitzky-Golay (1a derivada, janela=11, ordem=2).')

# ===== 2. CORRELACAO =====
doc.add_heading('2. Correlacao Espectro-AT', level=1)

top_c = np.argsort(np.abs(corrs))[::-1][:10]
doc.add_paragraph(f'Correlacao de Pearson entre cada comprimento de onda (SNV) e os valores de AT (n=45). Devido ao numero limitado de valores independentes de AT, os valores de correlacao devem ser interpretados com cautela.')

p = doc.add_paragraph()
p.add_run(f'Correlacao maxima: |r| = {np.max(np.abs(corrs)):.4f}').bold = True
p.add_run(f'\nCorrelacao media: {np.mean(np.abs(corrs)):.4f}')
p.add_run(f'\nCorrelacao mediana: {np.median(np.abs(corrs)):.4f}')

tabela_corr = doc.add_table(rows=11, cols=3, style='Light Shading Accent 1')
tabela_corr.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ['#', 'Comprimento (nm)', 'r (Pearson)']
for j, h in enumerate(headers):
    tabela_corr.cell(0, j).text = h
    for p_ in tabela_corr.cell(0, j).paragraphs:
        for r_ in p_.runs:
            r_.bold = True
for i, idx in enumerate(top_c[:10]):
    # converter idx para comprimento de onda (estamos com step de 5)
    actual_idx = np.where(wv == np.round(wv[idx*5], 1))[0]
    if len(actual_idx) > 0:
        wv_val = wv[actual_idx[0]]
    else:
        wv_val = wv[idx*5 if idx*5 < len(wv) else -1]
    tabela_corr.cell(i+1, 0).text = str(i+1)
    # Calcular correlacao no comprimento exato
    idx_exato = idx * 5
    if idx_exato >= len(wv): idx_exato = -1
    r_exato = pearsonr(X_snv[:, idx_exato], y)[0] if idx_exato < len(wv) and idx_exato >= 0 else 0
    tabela_corr.cell(i+1, 1).text = f'{wv[idx_exato]:.1f}'
    tabela_corr.cell(i+1, 2).text = f'{r_exato:.4f}'

# ===== 3. PCA =====
doc.add_heading('3. Analise de Componentes Principais (PCA)', level=1)

doc.add_paragraph('PCA aplicada aos espectros pre-processados com SNV e escalonamento (StandardScaler).')

tabela_pca = doc.add_table(rows=6, cols=4, style='Light Shading Accent 1')
tabela_pca.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ['PC', 'Var. Explicada (%)', 'Var. Acumulada (%)', 'r(PC, AT)']
for j, h in enumerate(headers):
    tabela_pca.cell(0, j).text = h
    for p_ in tabela_pca.cell(0, j).paragraphs:
        for r_ in p_.runs:
            r_.bold = True
for i, (pc, var, r) in enumerate(pca_results):
    tabela_pca.cell(i+1, 0).text = str(pc)
    tabela_pca.cell(i+1, 1).text = f'{var*100:.2f}%'
    tabela_pca.cell(i+1, 2).text = f'{sum(pca.explained_variance_ratio_[:pc])*100:.2f}%'
    tabela_pca.cell(i+1, 3).text = f'{r:.4f}'

p = doc.add_paragraph()
p.add_run('Interpretacao: ').bold = True
p.add_run(f'PC1 explica {pca.explained_variance_ratio_[0]*100:.1f}% da variancia espectral e tem correlacao de {pca_results[0][2]:.3f} com AT. ')
p.add_run(f'As PCs seguintes tem correlacao com AT proxima de zero, indicando que a informacao espectral relacionada ao AT esta concentrada na PC1.')

# ===== 4. ANOVA =====
doc.add_heading('4. Analise de Variancia (ANOVA)', level=1)
p = doc.add_paragraph()
p.add_run('Teste: ').bold = True
p.add_run('ANOVA de um fator para AT entre os 3 tratamentos (T1=italiano, T2=cereja, T3=...).')
doc.add_paragraph(f'F = {anova.statistic:.3f}, p = {anova.pvalue:.4f}')

p = doc.add_paragraph()
if anova.pvalue > 0.05:
    p.add_run('Resultado: ').bold = True
    p.add_run('Nao ha diferenca significativa de AT entre os tratamentos (p > 0.05). ')
    p.add_run('Isso significa que a variacao de AT entre parcelas e maior que a variacao entre tratamentos.')
else:
    p.add_run('Resultado: ').bold = True
    p.add_run('Ha diferenca significativa de AT entre os tratamentos (p < 0.05).')

# ===== 5. MODELOS =====
doc.add_heading('5. Modelos de Machine Learning', level=1)

doc.add_heading('5.1. PLS Regression (45 amostras, GroupKFold 5-fold)', level=2)
doc.add_paragraph(f'Validacao cruzada com GroupKFold (5 folds, 20 repeticoes). Grupos = parcelas (garantindo que os 5 frutos de cada parcela nunca sejam separados entre treino e teste).')

tabela_pls = doc.add_table(rows=len(pls_results)+1, cols=4, style='Light Shading Accent 1')
tabela_pls.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(['Componentes', 'R2', 'RMSE', 'RPD']):
    tabela_pls.cell(0, j).text = h
    for p_ in tabela_pls.cell(0, j).paragraphs:
        for r_ in p_.runs:
            r_.bold = True
for i, (nc, r2, rmse, rpd) in enumerate(pls_results):
    tabela_pls.cell(i+1, 0).text = str(nc)
    tabela_pls.cell(i+1, 1).text = f'{r2:.4f}'
    tabela_pls.cell(i+1, 2).text = f'{rmse:.4f}'
    tabela_pls.cell(i+1, 3).text = f'{rpd:.2f}'

doc.add_heading('5.2. PLS com SNV + Derivada (Savitzky-Golay)', level=2)
tabela_pls_sg = doc.add_table(rows=len(pls_sg_results)+1, cols=4, style='Light Shading Accent 1')
tabela_pls_sg.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(['Componentes', 'R2', 'RMSE', 'RPD']):
    tabela_pls_sg.cell(0, j).text = h
    for p_ in tabela_pls_sg.cell(0, j).paragraphs:
        for r_ in p_.runs:
            r_.bold = True
for i, (nc, r2, rmse, rpd) in enumerate(pls_sg_results):
    tabela_pls_sg.cell(i+1, 0).text = str(nc)
    tabela_pls_sg.cell(i+1, 1).text = f'{r2:.4f}'
    tabela_pls_sg.cell(i+1, 2).text = f'{rmse:.4f}'
    tabela_pls_sg.cell(i+1, 3).text = f'{rpd:.2f}'

doc.add_heading('5.3. Validacao Conservadora - Medias por Parcela (n=9, LOOCV)', level=2)
doc.add_paragraph('Cada parcela e representada pela media espectral dos 5 frutos. Leave-One-Out Cross-Validation (9 folds).')

tabela_loo = doc.add_table(rows=len(loo_results)+1, cols=4, style='Light Shading Accent 1')
tabela_loo.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(['Modelo', 'R2', 'RMSE', 'RPD']):
    tabela_loo.cell(0, j).text = h
    for p_ in tabela_loo.cell(0, j).paragraphs:
        for r_ in p_.runs:
            r_.bold = True
for i, (nome, r2, rmse, rpd) in enumerate(loo_results):
    tabela_loo.cell(i+1, 0).text = nome
    tabela_loo.cell(i+1, 1).text = f'{r2:.4f}'
    tabela_loo.cell(i+1, 2).text = f'{rmse:.4f}'
    tabela_loo.cell(i+1, 3).text = f'{rpd:.2f}'

# ===== 7. GRAFICOS =====
doc.add_heading('6. Graficos', level=1)

# Gerar figura
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
# (a) Espectros
ax = axes[0, 0]
for i in range(min(9, X_raw.shape[0])):
    ax.plot(wv, X_raw[i], alpha=0.6, linewidth=0.7)
ax.set_xlabel('Comprimento de onda (nm)', fontsize=11)
ax.set_ylabel('Reflectancia', fontsize=11)
ax.set_title('(a) Espectros NIRS brutos (9 amostras)', fontsize=12, fontweight='bold')
ax.grid(alpha=0.3)
# (b) Correlacao
ax = axes[0, 1]
corrs_full = np.array([pearsonr(X_snv[:, i], y)[0] for i in range(len(wv))])
ax.plot(wv, corrs_full, 'b-', lw=0.6, alpha=0.7)
ax.axhline(0, color='gray', ls='--', alpha=0.5)
ax.set_xlabel('Comprimento de onda (nm)', fontsize=11)
ax.set_ylabel('r (Pearson)', fontsize=11)
ax.set_title(f'(b) Correlacao AT-espectro (max |r|={np.max(np.abs(corrs_full)):.3f})', fontsize=12, fontweight='bold')
ax.grid(alpha=0.3)
# (c) PCA
ax = axes[1, 0]
from sklearn.decomposition import PCA as PCA_sk
pca2 = PCA_sk(2).fit_transform(StandardScaler().fit_transform(X_snv))
sc = ax.scatter(pca2[:, 0], pca2[:, 1], c=y, cmap='viridis', s=60, edgecolors='k', lw=0.5)
plt.colorbar(sc, ax=ax, label='AT')
ax.set_xlabel('PC1', fontsize=11); ax.set_ylabel('PC2', fontsize=11)
ax.set_title(f'(c) PCA - r(PC1,AT)={pearsonr(pca2[:,0],y)[0]:.3f}', fontsize=12, fontweight='bold')
ax.grid(alpha=0.3)
# (d) LOOCV
ax = axes[1, 1]
modelo_ridge = Ridge(alpha=0.1)
preds_p, reals_p = [], []
for tr, te in loo.split(X_parc):
    scaler = StandardScaler()
    modelo_ridge.fit(scaler.fit_transform(X_parc[tr]), y_parc[tr])
    preds_p.append(modelo_ridge.predict(scaler.transform(X_parc[te]))[0])
    reals_p.append(y_parc[te][0])
r2_p = r2_score(reals_p, preds_p)
ax.scatter(reals_p, preds_p, c='darkgreen', s=80, edgecolors='k', lw=1, zorder=5)
for i, lbl in enumerate(dest['Parcela']):
    ax.annotate(lbl, (reals_p[i], preds_p[i]), fontsize=7, xytext=(4, 4), textcoords='offset points')
m1, m2 = min(min(reals_p), min(preds_p))-0.01, max(max(reals_p), max(preds_p))+0.01
ax.plot([m1, m2], [m1, m2], 'r--', alpha=0.7)
ax.set_xlabel('AT Real', fontsize=11); ax.set_ylabel('AT Predito', fontsize=11)
ax.set_title(f'(d) LOOCV (medias parcela) - R2={r2_p:.3f}', fontsize=12, fontweight='bold')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig('resultados_graficos.png', dpi=200, bbox_inches='tight')
plt.close()

doc.add_picture('resultados_graficos.png', width=Inches(6.5))
last_paragraph = doc.paragraphs[-1]
last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('Figura 1. (a) Espectros NIRS brutos; (b) Correlacao de Pearson entre cada comprimento de onda e AT; (c) PCA dos espectros; (d) LOOCV com medias por parcela.').italic = True

# ===== 8. CONCLUSAO =====
doc.add_heading('7. Conclusao', level=1)

p = doc.add_paragraph()
p.add_run('Os modelos de machine learning testados (PLS, Ridge, OLS) nao conseguiram predizer o AT ')
p.add_run('a partir dos espectros NIRS com precisao satisfatoria.').bold = True

doc.add_paragraph()
doc.add_paragraph('Os melhores resultados foram:')

bullets = [
    f'PLS(1 componente) com 45 amostras: R2 = {pls_results[0][1]:.3f}, RMSE = {pls_results[0][2]:.4f}',
    f'PLS(1) + medias por parcela (n=9): R2 = {loo_results[0][1]:.3f}, RMSE = {loo_results[0][2]:.4f}',
    f'Correlacao maxima AT-espectro: |r| = {np.max(np.abs(corrs_full)):.3f}',
    f'PC1 explica {pca.explained_variance_ratio_[0]*100:.1f}% da variancia espectral e tem r = {pca_results[0][2]:.3f} com AT',
]
for b in bullets:
    doc.add_paragraph(b, style='List Bullet')

doc.add_paragraph()
p = doc.add_paragraph()
p.add_run('Principais limitacoes identificadas:').bold = True

limitacoes = [
    'Apenas 9 valores independentes de AT para 45 espectros (5 frutos/parcela compartilham o mesmo AT)',
    f'Correlacao intrinseca baixa entre espectro e AT (max |r| = {np.max(np.abs(corrs_full)):.3f})',
    'ANOVA nao mostrou diferenca significativa de AT entre os tratamentos (p > 0.05)',
    'Alta variabilidade espectral entre frutos da mesma parcela',
]
for l in limitacoes:
    doc.add_paragraph(l, style='List Bullet')

doc.add_paragraph()
p = doc.add_paragraph()
p.add_run('Recomendacoes para trabalhos futuros:').bold = True

recomendacoes = [
    'Medir AT individualmente para cada fruto (em vez de por parcela) para obter 45 valores independentes',
    'Aumentar o numero de repeticoes experimentais (mais parcelas)',
    'Explorar a regiao do NIR entre 1100-1800 nm',  # comprimentos mais importantes
    'Considerar espectroscopia MID-IR para acidez',
    'Testar agregacao de espectros (media de varias leituras por fruto) para reduzir ruido',
]
for r in recomendacoes:
    doc.add_paragraph(r, style='List Bullet')

# ===== SALVAR =====
output_path = 'resultados1.docx'
doc.save(output_path)
print(f"Documento salvo: {output_path}")
print(f"Tamanho: {os.path.getsize(output_path)/1024:.0f} KB")
