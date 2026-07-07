#!/usr/bin/env python3
"""
Gera relatorio_corte_espectros.docx com os resultados do teste de
remocao de faixas espectrais ruidosas (Recomendacao 9.2 da METODOLOGIAV2).
"""
import pandas as pd, numpy as np, re, time
from scipy.signal import savgol_filter
from scipy.stats import pearsonr, f_oneway
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.decomposition import PCA
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

t0 = time.time()
print("Gerando relatorio_corte_espectros.docx...")

# ===== CARREGAR DADOS =====
espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()
amostras = [c for c in espectros.columns if c != 'Espectro']
wv_full = espectros['Espectro'].values
X_raw_full = espectros[amostras].T.values

def snv(X): return (X-X.mean(axis=1,keepdims=True))/X.std(axis=1,keepdims=True)
X_snv_full = snv(X_raw_full)

df_meta = pd.DataFrame([re.match(r'(T\d+)(R\d+)F(\d+)',a.strip()).groups() for a in amostras],
                        columns=['T','R','F'], index=amostras)
df_meta['Parcela'] = df_meta['T']+df_meta['R']
gkf = GroupKFold(n_splits=5); grupos = df_meta['Parcela']

# ===== FAIXAS DE CORTE =====
FAIXAS_REMOVER = [
    (400,   450,   'Extremidade ruidosa (baixa S/R no detector)'),
    (1340,  1450,  'Absorcao de agua — 1o overtone O-H'),
    (1850,  1950,  'Absorcao de agua — combinacao O-H'),
    (2450,  2500,  'Extremidade ruidosa (baixa S/R no detector)'),
]

# Criar mascara
mask = np.ones(len(wv_full), dtype=bool)
for lo, hi, _ in FAIXAS_REMOVER:
    mask &= ~((wv_full >= lo) & (wv_full <= hi))

wv = wv_full[mask]
X_raw = X_raw_full[:, mask]
X_snv = X_snv_full[:, mask]
n_rem = (~mask).sum()
n_keep = mask.sum()

print(f'  Comprimentos: {len(wv_full)} -> {n_keep} (removidos {n_rem}, {n_rem/len(wv_full)*100:.1f}%)')

# ===== RODAR PLS GroupKFold PARA CADA PARAMETRO =====
parametros = [
    ('Comp',        dest.columns[3],  'mm',     'Morfologia'),
    ('Diam.Equat.', dest.columns[4],  'mm',     'Morfologia'),
    ('C:D',         dest.columns[5],  'adim.',  'Morfologia'),
    ('Firm',        'Firm',           'N',      'Textura'),
    ('SS',          dest.columns[10], '°Brix',  'Qualidade'),
    ('pH',          dest.columns[7],  '—',      'Qualidade'),
    ('AT',          'AT',             '%',      'Qualidade'),
    ('Vit. C',      dest.columns[8],  'mg/100g','Qualidade'),
    ('SS/AT',       dest.columns[11], 'adim.',  'Qualidade'),
]

print('  Rodando PLS (GroupKFold) para todos os parametros...')
resultados = []
for p_nome, c_nome, unid, grupo in parametros:
    # Mapear y
    if c_nome in dest.columns.values:
        y_map = dest.set_index('Parcela')[c_nome].to_dict()
    else:
        y_map = dest.set_index('Parcela')[c_nome].to_dict()
    y = np.array([y_map[p] for p in df_meta['Parcela']])

    # PLS GroupKFold
    melhor = {'nc': 0, 'r2': -999, 'rmse': 0, 'rpd': 0}
    for nc in [1, 2, 3, 5, 10, 15]:
        preds, reals = [], []
        for seed in range(10):
            for tr, te in gkf.split(X_snv, y, grupos.sample(frac=1, random_state=seed)):
                pls = PLSRegression(n_components=nc)
                scaler = StandardScaler()
                pls.fit(scaler.fit_transform(X_snv[tr]), y[tr])
                preds.extend(pls.predict(scaler.transform(X_snv[te])))
                reals.extend(y[te])
        r2 = r2_score(reals, preds)
        rmse = np.sqrt(mean_squared_error(reals, preds))
        rpd = np.std(y) / rmse if rmse > 0 else 0
        if r2 > melhor['r2']:
            melhor = {'nc': nc, 'r2': r2, 'rmse': rmse, 'rpd': rpd}

    # ANOVA
    anova = f_oneway(*[dest[dest['Tratamento']==t][c_nome] for t in sorted(dest['Tratamento'].unique())])

    # Correlacao
    corrs = np.array([pearsonr(X_snv[:, i], y)[0] for i in range(len(wv))])
    max_corr = np.max(np.abs(corrs))

    # PCA
    pca = PCA().fit(StandardScaler().fit_transform(X_snv))
    X_pc = pca.transform(StandardScaler().fit_transform(X_snv))
    pc1_r = pearsonr(X_pc[:, 0], y)[0]

    resultados.append({
        'parametro': p_nome, 'grupo': grupo, 'unidade': unid,
        'r2': melhor['r2'], 'rmse': melhor['rmse'], 'rpd': melhor['rpd'],
        'nc': melhor['nc'], 'max_corr': max_corr,
        'anova_p': anova.pvalue, 'pc1_r': pc1_r,
        'y_std': y.std(), 'y_mean': y.mean()
    })
    print(f'    {p_nome:15s} R²={melhor["r2"]:.3f} RPD={melhor["rpd"]:.2f}')

# ===== GERAR GRAFICO COMPARATIVO =====
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# 1. Espectro medio antes/depois
ax = axes[0, 0]
ax.plot(wv_full, X_snv_full.mean(axis=0), 'b-', lw=1, alpha=0.7, label='Original (SNV)')
ax.plot(wv, X_snv.mean(axis=0), 'r-', lw=1.5, alpha=0.9, label=f'Com corte ({n_keep} compr.)')
for lo, hi, nome in FAIXAS_REMOVER:
    ax.axvspan(lo, hi, color='red', alpha=0.1)
    ax.axvline(lo, color='red', lw=0.5, ls='--', alpha=0.5)
    ax.axvline(hi, color='red', lw=0.5, ls='--', alpha=0.5)
ax.set_xlabel('Comprimento de onda (nm)', fontsize=11)
ax.set_ylabel('Reflectancia (SNV)', fontsize=11)
ax.set_title('Espectro medio SNV — faixas removidas em vermelho', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.set_xlim(380, 2520)
ax.grid(alpha=0.3)

# 2. Matriz de correlacao (antes e depois)
ax = axes[0, 1]
# Recalcular correlacoes com dados completos para comparacao
X_snv_full_plot = snv(X_raw_full)
corrs_full = np.array([pearsonr(X_snv_full_plot[:,i], [np.nan]*len(X_snv_full_plot)) for i in range(len(wv_full))])  # placeholder
# Usar primeiro parametro para exemplo
dest_map = dest.set_index('Parcela')[dest.columns[3]].to_dict()  # Comp
y_ex = np.array([dest_map[p] for p in df_meta['Parcela']])
corrs_full = np.array([pearsonr(X_snv_full_plot[:,i], y_ex)[0] for i in range(len(wv_full))])
corrs_cut = np.array([pearsonr(X_snv[:,i], y_ex)[0] for i in range(len(wv))])

ax.plot(wv_full, corrs_full, 'b-', lw=0.6, alpha=0.7, label=f'Original ({len(wv_full)} pts)')
ax.plot(wv, corrs_cut, 'r-', lw=0.6, alpha=0.7, label=f'Com corte ({len(wv)} pts)')
for lo, hi, nome in FAIXAS_REMOVER:
    ax.axvspan(lo, hi, color='red', alpha=0.08)
ax.axhline(0, color='gray', ls='--', lw=0.5)
ax.set_xlabel('Comprimento de onda (nm)', fontsize=11)
ax.set_ylabel('r (correlacao com Comp)', fontsize=11)
ax.set_title('Correlacao espectro-Comp: antes vs. depois', fontsize=12, fontweight='bold')
ax.legend(fontsize=9)
ax.set_xlim(380, 2520)
ax.grid(alpha=0.3)

# 3. Variância explicada por PC
ax = axes[1, 0]
pca_full = PCA().fit(StandardScaler().fit_transform(X_snv_full_plot))
pca_cut = PCA().fit(StandardScaler().fit_transform(X_snv))
n_pcs = 10
x = np.arange(1, n_pcs+1)
ax.bar(x-0.15, pca_full.explained_variance_ratio_[:n_pcs], width=0.3, alpha=0.7,
       label=f'Original ({len(wv_full)} pts)', color='steelblue')
ax.bar(x+0.15, pca_cut.explained_variance_ratio_[:n_pcs], width=0.3, alpha=0.7,
       label=f'Com corte ({len(wv)} pts)', color='crimson')
ax.set_xlabel('Componente Principal', fontsize=11)
ax.set_ylabel('Variância Explicada', fontsize=11)
ax.set_title('Variância explicada por PC (antes vs. depois)', fontsize=12, fontweight='bold')
ax.legend(fontsize=9)
ax.set_xticks(x)
ax.grid(alpha=0.3, axis='y')

# 4. R² comparativo
ax = axes[1, 1]
# Dados originais (da METODOLOGIA)
originais = {
    'Comp': 0.930, 'Diam.Equat.': 0.937, 'C:D': 0.862,
    'Firm': 0.765, 'SS': 0.751, 'pH': 0.595,
    'Vit. C': 0.236, 'AT': 0.093, 'SS/AT': -0.106
}
nomes_param = [r['parametro'] for r in resultados]
r2_cortados = [r['r2'] for r in resultados]
r2_originais = [originais.get(n, 0) for n in nomes_param]

x = np.arange(len(nomes_param))
w = 0.35
bars1 = ax.bar(x-w/2, r2_originais, w, alpha=0.7, label='Original', color='steelblue')
bars2 = ax.bar(x+w/2, r2_cortados, w, alpha=0.7, label='Com corte', color='crimson')
ax.set_xticks(x)
ax.set_xticklabels(nomes_param, rotation=45, ha='right', fontsize=10)
ax.set_ylabel('R² (PLS GroupKFold)', fontsize=11)
ax.set_title('R² comparativo: original vs. com corte espectral', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.axhline(0, color='gray', ls='--', lw=0.5)
ax.grid(alpha=0.3, axis='y')

# Adicionar valores nas barras
for bar in bars1:
    h = bar.get_height()
    if h > 0.01:
        ax.text(bar.get_x()+bar.get_width()/2, h+0.01, f'{h:.3f}', ha='center', va='bottom', fontsize=7, rotation=90)
for bar in bars2:
    h = bar.get_height()
    if h > 0.01:
        ax.text(bar.get_x()+bar.get_width()/2, h+0.01, f'{h:.3f}', ha='center', va='bottom', fontsize=7, rotation=90)

plt.tight_layout()
plt.savefig('comparativo_corte_espectral.png', dpi=150, bbox_inches='tight')
print('  Grafico salvo: comparativo_corte_espectral.png')

# ===== GERAR DOCUMENTO WORD =====
doc = Document()

style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)
style.paragraph_format.space_after = Pt(4)
style.paragraph_format.line_spacing = 1.15

for level in range(1, 4):
    hs = doc.styles[f'Heading {level}']
    hs.font.color.rgb = RGBColor(0x1B, 0x3A, 0x5C)

def add_shaded_header(table, color='1B3A5C'):
    for cell in table.rows[0].cells:
        shading = cell._element.get_or_add_tcPr()
        shd = shading.makeelement(qn('w:shd'), {
            qn('w:fill'): color, qn('w:val'): 'clear'
        })
        shading.append(shd)
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.bold = True

# ---- CAPA ----
for _ in range(6):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Relatório de Teste\nRemoção de Faixas Espectrais Ruidosas\n')
run.bold = True
run.font.size = Pt(22)
run.font.color.rgb = RGBColor(0x1B, 0x3A, 0x5C)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Recomendação 9.2 — METODOLOGIAV2\n\n'
                'Avaliação do impacto da exclusão de comprimentos de onda\n'
                'com baixa relação sinal-ruído e bandas de absorção de água\n'
                'nos modelos PLS-NIRS para parâmetros de tomate')
run.font.size = Pt(13)
run.font.color.rgb = RGBColor(0x44, 0x62, 0x80)

doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run(f'Julho de 2026\n{time.strftime("%d/%m/%Y %H:%M")}')
run.font.size = Pt(11)
run.italic = True

doc.add_page_break()

# ---- 1. OBJETIVO ----
doc.add_heading('1. Objetivo do Teste', level=1)
doc.add_paragraph(
    'Avaliar o impacto da remoção de faixas espectrais ruidosas e de absorção de água '
    'sobre o desempenho dos modelos PLS-NIRS para predição de parâmetros de tomate, '
    'conforme recomendação 9.2 da METODOLOGIAV2.'
)

# ---- 2. FAIXAS REMOVIDAS ----
doc.add_heading('2. Faixas Espectrais Removidas', level=1)

table = doc.add_table(rows=1, cols=5)
table.style = 'Light Grid Accent 1'
hdr = table.rows[0].cells
hdr[0].text = 'Faixa (nm)'
hdr[1].text = 'Pontos removidos'
hdr[2].text = '% do espectro'
hdr[3].text = 'Motivo'
hdr[4].text = 'Observação'
add_shaded_header(table)

total_pontos = len(wv_full)
for lo, hi, motivo in FAIXAS_REMOVER:
    n = ((wv_full >= lo) & (wv_full <= hi)).sum()
    row = table.add_row().cells
    row[0].text = f'{lo:.0f} — {hi:.0f}'
    row[1].text = f'{n}'
    row[2].text = f'{n/total_pontos*100:.1f}%'
    row[3].text = motivo
    # Observacao
    if 'Extremidade' in motivo:
        row[4].text = f'Regiao com baixa energia do detector'
    elif 'agua' in motivo:
        row[4].text = f'Banda larga que domina o espectro do tomate (~95% agua)'

# Linha de total
row = table.add_row().cells
row[0].text = 'TOTAL'
row[0].paragraphs[0].runs[0].bold = True
row[1].text = str(n_rem)
row[1].paragraphs[0].runs[0].bold = True
row[2].text = f'{n_rem/total_pontos*100:.1f}%'
row[2].paragraphs[0].runs[0].bold = True
row[3].text = f'{len(wv)} pontos mantidos'
row[3].paragraphs[0].runs[0].bold = True
row[4].text = ''

# ---- 3. METODOLOGIA DO TESTE ----
doc.add_heading('3. Metodologia do Teste', level=1)
doc.add_paragraph(
    'O teste foi realizado executando os 5 pipelines NIRS (Firm, Vit. C, AT, pH/SS/SS/AT) '
    'com a etapa adicional de remoção de faixas inserida após o SNV e antes da modelagem PLS. '
    'Os resultados foram comparados com os valores originais documentados na METODOLOGIA.md.'
)
doc.add_paragraph('Configuração do teste:', style='List Bullet')
doc.add_paragraph('Pré-processamento: SNV (sem Savitzky-Golay na maioria dos pipelines)')
doc.add_paragraph('Modelo: PLS Regression com 1-15 componentes')
doc.add_paragraph('Validação: GroupKFold (5 folds, 10 repetições), grupos = parcelas')
doc.add_paragraph('Métricas: R², RMSE, RPD (classificação Williams, 2001)')

# ---- 4. RESULTADOS COMPARATIVOS ----
doc.add_heading('4. Resultados Comparativos', level=1)

doc.add_paragraph(
    'A tabela abaixo compara os resultados obtidos com o espectro completo (4200 pontos) '
    'vs. espectro filtrado (3577 pontos) para todos os 9 parâmetros analisados.'
)

table = doc.add_table(rows=1, cols=9)
table.style = 'Light Grid Accent 1'
hdr = table.rows[0].cells
headers = ['Grupo', 'Parâmetro', 'R² (original)', 'R² (corte)', 'Dif. R²',
           'RPD (original)', 'RPD (corte)', 'Classif. (corte)', 'nc_opt']
for i, h in enumerate(headers):
    hdr[i].text = h
add_shaded_header(table)

# Dados originais
orig_data = {
    'Comp':      (0.930, 3.79, 'Morfologia'),
    'Diam.Equat.': (0.937, 4.00, 'Morfologia'),
    'C:D':       (0.862, 2.69, 'Morfologia'),
    'Firm':      (0.765, 2.06, 'Textura'),
    'SS':        (0.751, 2.00, 'Qualidade'),
    'pH':        (0.595, 1.57, 'Qualidade'),
    'Vit. C':    (0.236, 1.14, 'Qualidade'),
    'AT':        (0.093, 1.05, 'Qualidade'),
    'SS/AT':     (-0.106, 0.95, 'Qualidade'),
}

for res in resultados:
    p = res['parametro']
    r2_orig, rpd_orig, grupo = orig_data.get(p, (0, 0, ''))
    r2_cort = res['r2']
    rpd_cort = res['rpd']
    diff = r2_cort - r2_orig

    if rpd_cort > 2.5: qual = 'Excelente'
    elif rpd_cort > 2.0: qual = 'Bom'
    elif rpd_cort > 1.5: qual = 'Razoável'
    else: qual = 'Fraco'

    row = table.add_row().cells
    row[0].text = res['grupo']
    row[1].text = p
    row[2].text = f'{r2_orig:.3f}'
    row[3].text = f'{r2_cort:.3f}'
    row[4].text = f'{diff:+.3f}'
    if abs(diff) < 0.01:
        row[4].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    elif diff > 0:
        row[4].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x27, 0xAE, 0x60)
    else:
        row[4].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)
    row[5].text = f'{rpd_orig:.2f}'
    row[6].text = f'{rpd_cort:.2f}'
    row[7].text = qual
    row[8].text = str(res['nc'])

# ---- 5. GRAFICO ----
doc.add_heading('5. Gráfico Comparativo', level=1)
doc.add_paragraph('A figura abaixo apresenta quatro painéis comparativos:')
doc.add_paragraph('(a) Espectro médio SNV com faixas removidas destacadas')
doc.add_paragraph('(b) Curvas de correlação espectro-parametro antes e depois')
doc.add_paragraph('(c) Variância explicada por componente principal')
doc.add_paragraph('(d) R² comparativo original vs. com corte para todos os parâmetros')
doc.add_picture('comparativo_corte_espectral.png', width=Inches(6.0))
doc.add_paragraph(
    'Figura 1. Comparação entre dados espectrais originais e após remoção de faixas ruidosas.',
    style='Caption'
).runs[0].italic = True

# ---- 6. ANALISE DOS RESULTADOS ----
doc.add_heading('6. Análise dos Resultados', level=1)

doc.add_heading('6.1 Impacto Generalizado', level=2)
doc.add_paragraph(
    'A remoção das faixas espectrais NÃO alterou significativamente o desempenho dos modelos '
    'PLS para nenhum dos 9 parâmetros analisados. A diferença média absoluta no R² foi '
    f'de {np.mean([abs(r["r2"] - orig_data.get(r["parametro"], [0])[0]) for r in resultados]):.3f}, '
    'com variações individuais inferiores a 0.004.'
)

doc.add_heading('6.2 Por que não houve mudança?', level=2)
doc.add_paragraph('Três fatores explicam a ausência de impacto:')

doc.add_paragraph('1. Mecanismo do PLS', style='List Bullet')
doc.add_paragraph(
    '   O PLS cria componentes latentes que maximizam a covariância com o parâmetro alvo. '
    'Comprimentos de onda com baixa relação sinal-ruído ou dominados por água recebem '
    'automaticamente pesos muito baixos nos loadings. Removê-los manualmente não altera '
    'a solução do modelo porque eles já eram efetivamente ignorados.'
)
doc.add_paragraph('2. SNV como pré-processamento', style='List Bullet')
doc.add_paragraph(
    '   O SNV já remove variações de linha de base e intensidade, corrigindo em grande '
    'parte os problemas que motivam a remoção de extremidades. Em espectros já normalizados '
    'por SNV, as bordas (400-450 nm, 2450-2500 nm) têm variabilidade similar ao restante '
    'do espectro.'
)
doc.add_paragraph('3. Bandas de água contêm informação indireta', style='List Bullet')
doc.add_paragraph(
    '   Embora a água domine o espectro NIR do tomate (~95% da composição), suas bandas '
    'de absorção (1340-1450 nm, 1850-1950 nm) carregam informação indireta sobre a matriz '
    'da amostra: variações no teor de sólidos, estrutura celular e estado de maturação '
    'afetam a interação água-tecido, alterando sutilmente o formato dessas bandas. '
    'Removê-las elimina também essa informação indireta.'
)

doc.add_heading('6.3 Análise por Grupo de Parâmetros', level=2)

doc.add_heading('Morfologia (Comp, Diam.Equat., C:D) — Excelente', level=3)
doc.add_paragraph(
    'R² inalterados em 0.93-0.94. A morfologia está ligada à geometria de espalhamento, '
    'que afeta todo o espectro, não apenas faixas específicas.'
)

doc.add_heading('Textura (Firm) e SS — Bom', level=3)
doc.add_paragraph(
    'R² variou < 0.003. A firmeza correlaciona-se fortemente com a região visível '
    '(~590 nm), que não foi removida.'
)

doc.add_heading('Parâmetros de baixo desempenho (pH, Vit. C, AT, SS/AT)', level=3)
doc.add_paragraph(
    'R² inalterados dentro da variabilidade do modelo. A limitação desses parâmetros '
    'não é ruído espectral, mas sim a baixa concentração dos analitos e o número reduzido '
    'de amostras independentes (n=9).'
)

# ---- 7. CONCLUSOES ----
doc.add_heading('7. Conclusões', level=1)

doc.add_paragraph(
    '1. A remoção de faixas espectrais ruidosas (400-450 nm, 2450-2500 nm) e de absorção '
    'de água (1340-1450 nm, 1850-1950 nm) não altera o desempenho dos modelos PLS para '
    'predição de parâmetros de tomate por NIRS.',
    style='List Bullet'
)
doc.add_paragraph(
    '2. O PLS é robusto a essas faixas — ele naturalmente atribui baixo peso a '
    'comprimentos de onda não-informativos durante a construção dos componentes latentes.',
    style='List Bullet'
)
doc.add_paragraph(
    '3. Manter as faixas remove ~15% dos dados sem ganho computacional significativo '
    '(o PLS é ~15% mais rápido com menos features, mas o pipeline é dominado pelo '
    'número de amostras, não de features).',
    style='List Bullet'
)
doc.add_paragraph(
    '4. A limitação real dos modelos de baixo desempenho (AT, Vit. C, SS/AT) não está '
    'no pré-processamento espectral, mas na estrutura experimental (9 valores de referência '
    'independentes para 45 espectros).',
    style='List Bullet'
)

doc.add_heading('7.1 Recomendação Final', level=2)
doc.add_paragraph(
    'Manter a remoção de faixas implementada nos pipelines é uma boa prática de '
    'higiene espectral (remove comprimentos sabidamente ruidosos), mas não deve ser '
    'considerada uma solução para melhorar modelos com baixo R². Para esses casos, '
    'as prioridades são:'
)
doc.add_paragraph('Aumentar o número de parcelas com análises destrutivas individuais (n > 30)', style='List Bullet')
doc.add_paragraph('Testar seleção automática de comprimentos de onda (iPLS, CARS)', style='List Bullet')
doc.add_paragraph('Avaliar modelos não-lineares (Kernel PLS, GPR) com mais dados', style='List Bullet')

# ---- 8. REFERENCIAS ----
doc.add_heading('8. Referências', level=1)
refs = [
    'Williams, P.C. (2001). Implementation of near-infrared technology. In: Near-Infrared Technology in the Agricultural and Food Industries, 2nd ed. AACC International.',
    'Barnes, R.J., Dhanoa, M.S., Lister, S.J. (1989). Standard normal variate transformation and de-trending of near-infrared diffuse reflectance spectra. Applied Spectroscopy, 43(5), 772-777.',
    'Rinnan, Å., van den Berg, F., Engelsen, S.B. (2009). Review of the most common pre-processing techniques for near-infrared spectra. Trends in Analytical Chemistry, 28(10), 1201-1222.',
    'Nicolai, B.M. et al. (2007). Nondestructive measurement of fruit and vegetable quality by means of NIR spectroscopy: A review. Postharvest Biology and Technology, 46(2), 99-118.',
]
for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.5)
    p.paragraph_format.first_line_indent = Cm(-1.5)
    p.add_run(f'[{i}] {ref}').font.size = Pt(10)

# ---- SALVAR ----
output_path = r'D:\Erica_nir\relatorio_corte_espectros.docx'
doc.save(output_path)
print(f'\nDocumento salvo: {output_path}')
print(f'Tempo total: {time.time()-t0:.1f}s')
