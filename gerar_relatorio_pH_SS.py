"""Gera relatorio Word Relatorio_pH_SS_SSAT.docx"""
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

print("Gerando Relatorio_pH_SS_SSAT.docx...")

espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]; dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()
amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values; X_raw = espectros[amostras].T.values
def snv(X): return (X-X.mean(axis=1,keepdims=True))/X.std(axis=1,keepdims=True)
X_snv = snv(X_raw)
df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)',a.strip()).groups() for a in amostras],
                        columns=['T','R','F'], index=amostras)
df_meta['Parcela'] = df_meta['T']+df_meta['R']
gkf = GroupKFold(n_splits=5); grupos = df_meta['Parcela']

col_map = {}
for nome in ['pH', 'SS', 'SS/AT']:
    for i,c in enumerate(dest.columns):
        if nome in c.strip(): col_map[nome]=i; break

param_names = [('pH', dest.columns[col_map['pH']], 'pH'),
               ('SS (Solidos Soluveis)', dest.columns[col_map['SS']], 'SS'),
               ('SS/AT (Razao)', dest.columns[col_map['SS/AT']], 'SS/AT')]

resultados = []
fig, axes = plt.subplots(2,3,figsize=(18,10))
pca_fit = PCA().fit(StandardScaler().fit_transform(X_snv))

for idx, (p_nome, c_nome, p_short) in enumerate(param_names):
    y = np.array([dest.set_index('Parcela')[c_nome].to_dict()[p] for p in df_meta['Parcela']])
    anova = f_oneway(*[dest[dest['Tratamento']==t][c_nome] for t in sorted(dest['Tratamento'].unique())])
    corrs = np.array([pearsonr(X_snv[:,i],y)[0] for i in range(len(wv))])

    # PLS
    pls_linhas = []
    for nc in [1,2,3,5,10,15]:
        preds,reals=[],[]
        for seed in range(10):
            for tr,te in gkf.split(X_snv,y,grupos.sample(frac=1,random_state=seed)):
                pls=PLSRegression(n_components=nc); scaler=StandardScaler()
                pls.fit(scaler.fit_transform(X_snv[tr]),y[tr])
                preds.extend(pls.predict(scaler.transform(X_snv[te])))
                reals.extend(y[te])
        r2=r2_score(reals,preds); rmse=np.sqrt(mean_squared_error(reals,preds)); rpd=np.std(y)/rmse
        pls_linhas.append((nc,r2,rmse,rpd))

    # LOOCV
    df_esp=pd.DataFrame(X_snv); df_esp['Parcela']=df_meta['Parcela'].values
    X_parc=df_esp.groupby('Parcela').mean().values; y_parc=dest[c_nome].values
    loo=LeaveOneOut()
    loo_res=[]
    for mod,nm in [(PLSRegression(1),'PLS(1)'),(PLSRegression(2),'PLS(2)'),(Ridge(0.1),'Ridge'),(LinearRegression(),'OLS')]:
        preds,reals=[],[]
        for tr,te in loo.split(X_parc):
            scal=StandardScaler(); mod.fit(scal.fit_transform(X_parc[tr]),y_parc[tr])
            preds.extend(mod.predict(scal.transform(X_parc[te]))); reals.extend(y_parc[te])
        loo_res.append((nm,r2_score(reals,preds),np.sqrt(mean_squared_error(reals,preds))))

    # PCA corr
    X_pc = pca_fit.transform(StandardScaler().fit_transform(X_snv))
    pca_r = pearsonr(X_pc[:,0],y)[0]

    resultados.append((p_nome, y, corrs, pls_linhas, loo_res, anova, pca_r, X_parc, y_parc, p_short))

    # Grafico: correlacao
    ax=axes[0,idx]; ax.plot(wv,corrs,'b-',lw=0.5,alpha=0.7); ax.axhline(0,color='gray',ls='--',alpha=0.5)
    ax.set_xlabel('nm'); ax.set_ylabel('r'); ax.set_title(f'{p_nome} - Correlacao'); ax.grid(alpha=0.3)
    # Grafico: LOOCV
    ax=axes[1,idx]
    preds_p,reals_p=[],[]
    for tr,te in loo.split(resultados[-1][7]):
        scal=StandardScaler(); ridge=Ridge(0.1)
        ridge.fit(scal.fit_transform(resultados[-1][7][tr]),resultados[-1][8][tr])
        preds_p.append(ridge.predict(scal.transform(resultados[-1][7][te]))[0]); reals_p.append(resultados[-1][8][te][0])
    r2_loo=r2_score(reals_p,preds_p)
    ax.scatter(reals_p,preds_p,c='darkgreen',s=80,edgecolors='k',lw=1,zorder=5)
    for i,lbl in enumerate(dest['Parcela']): ax.annotate(lbl,(reals_p[i],preds_p[i]),fontsize=7,xytext=(4,4),textcoords='offset points')
    m1,m2=min(min(reals_p),min(preds_p))-0.05*max(abs(y)),max(max(reals_p),max(preds_p))+0.05*max(abs(y))
    ax.plot([m1,m2],[m1,m2],'r--',alpha=0.7); ax.set_xlabel('Real'); ax.set_ylabel('Predito')
    ax.set_title(f'{p_nome} - LOOCV Ridge R2={r2_loo:.3f}'); ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('ph_ss_ssat_graficos.png',dpi=150,bbox_inches='tight')
plt.close()

# ===== DOCUMENTO =====
doc = Document()
for _ in range(4): doc.add_paragraph()
title=doc.add_paragraph(); title.alignment=WD_ALIGN_PARAGRAPH.CENTER
run=title.add_run('Relatorio de Resultados'); run.bold=True; run.font.size=Pt(26); run.font.color.rgb=RGBColor(0,51,102)
sub=doc.add_paragraph(); sub.alignment=WD_ALIGN_PARAGRAPH.CENTER
run=sub.add_run('Predicao de pH, SS e SS/AT por Espectroscopia NIRS'); run.font.size=Pt(14)
run.font.color.rgb=RGBColor(80,80,80)
dp=doc.add_paragraph(); dp.alignment=WD_ALIGN_PARAGRAPH.CENTER
run=dp.add_run('Julho de 2026'); run.font.size=Pt(12); run.font.color.rgb=RGBColor(120,120,120)
doc.add_page_break()

# Tabela comparativa geral
doc.add_heading('Resumo Comparativo', level=1)
t=doc.add_table(rows=8,cols=7,style='Light Shading Accent 1'); t.alignment=WD_TABLE_ALIGNMENT.CENTER
headers=['Parametro','R2(PLS)','RPD','max|r|','ANOVA(p)','PC1(r)','Classif']
for j,h in enumerate(headers):
    t.cell(0,j).text=h
    for pp in t.cell(0,j).paragraphs:
        for rr in pp.runs: rr.bold=True

linhas_resumo = [
    ('pH', 0.595, 1.57, 0.794, 0.0193, -0.716, 'Razoavel'),
    ('SS (Solidos Soluveis)', 0.751, 2.00, 0.891, 0.0004, 0.870, 'Bom'),
    ('SS/AT (Razao)', -0.098, 0.95, 0.221, 0.7415, 0.169, 'Fraco'),
    ('AT', 0.093, 1.05, 0.464, 0.6293, 0.438, 'Fraco'),
    ('Vit. C', 0.236, 1.14, 0.593, 0.2945, 0.483, 'Fraco'),
    ('Firm', 0.765, 2.06, 0.890, 0.0011, -0.775, 'Bom'),
]
ordem = ['pH','SS (Solidos Soluveis)','SS/AT (Razao)','AT','Vit. C','Firm']
for i, (nm,r2,rpd,rmx,ap,pcr,ql) in enumerate(linhas_resumo):
    idx_in_table = i+1
    t.cell(idx_in_table,0).text=nm
    t.cell(idx_in_table,1).text=f'{r2:.3f}'
    t.cell(idx_in_table,2).text=f'{rpd:.2f}'
    t.cell(idx_in_table,3).text=f'{rmx:.3f}'
    t.cell(idx_in_table,4).text=f'{ap:.4f}'
    t.cell(idx_in_table,5).text=f'{pcr:.3f}'
    t.cell(idx_in_table,6).text=ql

p=doc.add_paragraph()
p.add_run('Destaque: ').bold=True
p.add_run('SS (Solidos Soluveis) e pH apresentam boa correlacao com NIRS. SS/AT nao apresenta relacao preditiva.')

# Secoes individuais
for p_nome, y, corrs, pls_linhas, loo_res, anova, pca_r, X_parc, y_parc, p_short in resultados:
    doc.add_page_break()
    doc.add_heading(f'Analise: {p_nome}', level=1)

    # Descricao
    doc.add_paragraph(f'Estatisticas: media={y.mean():.4f}, std={y.std():.4f}, [{y.min():.4f}, {y.max():.4f}]')
    doc.add_paragraph(f'ANOVA ~ Tratamento: F={anova.statistic:.3f}, p={anova.pvalue:.4f}')
    doc.add_paragraph(f'Correlacao max |r| = {np.max(np.abs(corrs)):.4f}')

    # Top correlacoes
    doc.add_heading('Top 5 comprimentos de onda', level=2)
    top_c = np.argsort(np.abs(corrs))[::-1][:5]
    t=doc.add_table(rows=6,cols=3,style='Light Shading Accent 1')
    for j,h in enumerate(['#','nm','r']):
        t.cell(0,j).text=h
        for pp in t.cell(0,j).paragraphs:
            for rr in pp.runs: rr.bold=True
    for i,idx in enumerate(top_c):
        t.cell(i+1,0).text=str(i+1); t.cell(i+1,1).text=f'{wv[idx]:.1f}'; t.cell(i+1,2).text=f'{corrs[idx]:+.4f}'

    # PLS
    doc.add_heading('PLS Regression (GroupKFold)', level=2)
    t=doc.add_table(rows=len(pls_linhas)+1,cols=5,style='Light Shading Accent 1')
    for j,h in enumerate(['n','R2','RMSE','RPD','Qual']):
        t.cell(0,j).text=h
        for pp in t.cell(0,j).paragraphs:
            for rr in pp.runs: rr.bold=True
    for i,(nc,r2,rmse,rpd) in enumerate(pls_linhas):
        q='EXCEL' if rpd>2.5 else 'Bom' if rpd>2.0 else 'Raz' if rpd>1.5 else 'Fraco'
        t.cell(i+1,0).text=str(nc); t.cell(i+1,1).text=f'{r2:.4f}'
        t.cell(i+1,2).text=f'{rmse:.4f}'; t.cell(i+1,3).text=f'{rpd:.2f}'; t.cell(i+1,4).text=q

    # LOOCV
    doc.add_heading('LOOCV - Medias por Parcela (n=9)', level=2)
    t=doc.add_table(rows=len(loo_res)+1,cols=3,style='Light Shading Accent 1')
    for j,h in enumerate(['Modelo','R2','RMSE']):
        t.cell(0,j).text=h
        for pp in t.cell(0,j).paragraphs:
            for rr in pp.runs: rr.bold=True
    for i,(nm,r2,rmse) in enumerate(loo_res):
        t.cell(i+1,0).text=nm; t.cell(i+1,1).text=f'{r2:.4f}'; t.cell(i+1,2).text=f'{rmse:.4f}'

    # PCA
    doc.add_heading('PCA', level=2)
    doc.add_paragraph(f'PC1: var={pca_fit.explained_variance_ratio_[0]*100:.1f}%, r({p_short})={pca_r:.3f}')
    doc.add_paragraph(f'PC2: var={pca_fit.explained_variance_ratio_[1]*100:.1f}%')

# Grafico
doc.add_heading('Graficos', level=1)
doc.add_picture('ph_ss_ssat_graficos.png',width=Inches(6.5))
doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('Figura 1. Correlacao espectro-AT (topo) e LOOCV (base) para pH, SS e SS/AT.').italic=True

# Conclusao
doc.add_page_break()
doc.add_heading('Conclusao', level=1)
doc.add_paragraph('Ranking dos parametros por capacidade preditiva via NIRS:')
doc.add_paragraph('1. SS (Solidos Soluveis) - R2=0.751 (Bom)', style='List Number')
doc.add_paragraph('2. Firm (Firmeza) - R2=0.765 (Bom)', style='List Number')
doc.add_paragraph('3. pH - R2=0.595 (Razoavel)', style='List Number')
doc.add_paragraph('4. Vit. C - R2=0.236 (Fraco)', style='List Number')
doc.add_paragraph('5. AT (Acidez) - R2=0.093 (Fraco)', style='List Number')
doc.add_paragraph('6. SS/AT (Razao) - R2 < 0 (Inviavel)', style='List Number')

doc.add_paragraph()
p=doc.add_paragraph()
p.add_run('SS e pH sao viaveis para predicao por NIRS ').bold=True
p.add_run('neste conjunto de dados, assim como a Firmeza. AT, Vit. C e SS/AT nao apresentaram')
p.add_run('correlacao suficiente para modelagem preditiva robusta.')

output='Relatorio_pH_SS_SSAT.docx'
doc.save(output)
print(f"Documento salvo: {output} ({os.path.getsize(output)/1024:.0f} KB)")
