"""
Gera Relatorio_Codigo_GridSearch.docx explicando, secao por secao,
o funcionamento do script nirs_preprocessamento_gridsearch.py.
"""
import os
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

print("Gerando Relatorio_Codigo_GridSearch.docx...")

doc = Document()

# ===== ESTILO BASE =====
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)


def set_cell_bg(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)


def code_block(texto):
    """Insere um bloco de codigo monoespacado com fundo cinza claro."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    set_cell_bg(cell, 'F2F2F2')
    cell.text = ''
    p = cell.paragraphs[0]
    linhas = texto.strip('\n').split('\n')
    for i, linha in enumerate(linhas):
        run = p.add_run(linha if i == 0 else '\n' + linha)
        run.font.name = 'Consolas'
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(30, 30, 30)
    doc.add_paragraph()


def explicacao(texto):
    p = doc.add_paragraph()
    p.add_run(texto)
    return p


def tabela(headers, rows):
    t = doc.add_table(rows=len(rows) + 1, cols=len(headers), style='Light Shading Accent 1')
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        t.cell(0, j).text = h
        for pp in t.cell(0, j).paragraphs:
            for rr in pp.runs:
                rr.bold = True
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            t.cell(i + 1, j).text = str(val)
    return t


# ===== CAPA =====
for _ in range(4):
    doc.add_paragraph()
title = doc.add_paragraph(); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('Explicação do Código'); run.bold = True; run.font.size = Pt(26)
run.font.color.rgb = RGBColor(0, 51, 102)
sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run('nirs_preprocessamento_gridsearch.py'); run.font.size = Pt(15)
run.font.color.rgb = RGBColor(80, 80, 80)
sub2 = doc.add_paragraph(); sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub2.add_run('Grid Search de Pré-processamento Espectral (Recomendação 9.2)')
run.font.size = Pt(13); run.font.color.rgb = RGBColor(100, 100, 100)
doc.add_paragraph()
dp = doc.add_paragraph(); dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = dp.add_run('Julho de 2026'); run.font.size = Pt(12); run.font.color.rgb = RGBColor(120, 120, 120)
doc.add_page_break()

# ===== 1. OBJETIVO =====
doc.add_heading('1. Objetivo do Script', level=1)
explicacao(
    'O script nirs_preprocessamento_gridsearch.py implementa a Recomendação 9.2 da '
    'METODOLOGIAV2.docx ("Pré-processamento Espectral"), que propõe:'
)
p = doc.add_paragraph(style='List Bullet')
p.add_run('Avaliar SNV + Detrend, SNV + 2ª derivada (janela 15, ordem 3) e MSC, '
          'usando grid search para selecionar a combinação ótima de pré-processamento '
          'para cada parâmetro de referência.')
explicacao(
    'Para isso, o script compara quatro combinações de pré-processamento espectral '
    '(SNV isolado, usado como baseline; SNV+Detrend; SNV + 2ª derivada; e MSC) para '
    'os 9 parâmetros de qualidade do tomate (Comp, Diam.Equat., C:D, Firm, pH, Vit. C, '
    'AT, SS e SS/AT), usando sempre o mesmo esquema de validação cruzada GroupKFold '
    '(5 folds x 10 repetições, agrupado por parcela) já adotado nos demais pipelines '
    'do projeto, de forma a manter os resultados comparáveis entre si.'
)

# ===== 2. IMPORTACOES =====
doc.add_heading('2. Importações', level=1)
code_block("""import pandas as pd, numpy as np, re, time, warnings
warnings.filterwarnings('ignore')
from scipy.signal import savgol_filter
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

from nirs_utils import criar_mascara_comprimentos""")
explicacao(
    'pandas/numpy manipulam os dados tabulares e as matrizes espectrais; '
    're extrai o tratamento/repetição/fruto do nome de cada amostra; time mede '
    'a duração do script. savgol_filter (do scipy) implementa o filtro Savitzky-Golay '
    'usado tanto para calcular a 2ª derivada quanto (indiretamente) o conceito de '
    'suavização por polinômios locais. PLSRegression, StandardScaler, GroupKFold, '
    'r2_score e mean_squared_error vêm do scikit-learn e formam o núcleo do modelo '
    'preditivo e da validação cruzada. matplotlib.use(\'Agg\') configura o backend '
    'sem interface gráfica, necessário para salvar os gráficos em PNG em modo script. '
    'Por fim, criar_mascara_comprimentos é importada de nirs_utils.py — o módulo '
    'compartilhado que já implementa a remoção de faixas ruidosas (Recomendação 9.2, '
    'parte já feita anteriormente).'
)

# ===== 3. CARREGAMENTO DOS DADOS =====
doc.add_heading('3. Carregamento e Preparação dos Dados', level=1)
code_block("""espectros = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Capturas_NIRS')
dest = pd.read_excel('Capturas_tomate_NIRS_16jun26_corrigido.xlsx', sheet_name='Dados_analise_destrutiva')
col_rep = dest.columns[2]
dest['Parcela'] = dest['Tratamento'].str.strip() + dest[col_rep].str.strip()

amostras = [c for c in espectros.columns if c != 'Espectro']
wv = espectros['Espectro'].values
X_raw = espectros[amostras].T.values

df_meta = pd.DataFrame([re.match(r'(T\\d+)(R\\d+)F(\\d+)', a.strip()).groups() for a in amostras],
                        columns=['T', 'R', 'F'], index=amostras)
df_meta['Parcela'] = df_meta['T'] + df_meta['R']""")
explicacao(
    'A planilha é lida em duas abas: "Capturas_NIRS" contém os 45 espectros de '
    'reflectância (um por fruto, 400-2500 nm) e "Dados_analise_destrutiva" contém os '
    '9 valores de referência por parcela. A coluna "Parcela" é criada concatenando '
    'Tratamento + Repetição (ex.: "T1R1"), que é a chave usada para ligar cada fruto '
    'ao seu valor de referência e para agrupar amostras no GroupKFold. A matriz X_raw '
    'é transposta para o formato (amostras x comprimentos de onda), e df_meta extrai, '
    'via expressão regular, o tratamento (T), a repetição (R) e o número do fruto (F) '
    'a partir do nome de cada coluna (ex.: "T1R2F3").'
)

# ===== 4. REMOCAO DE FAIXAS RUIDOSAS =====
doc.add_heading('4. Remoção de Faixas Espectrais Ruidosas', level=1)
code_block("""mask, n_rem = criar_mascara_comprimentos(wv)
X_raw = X_raw[:, mask]
wv = wv[mask]
print(f"Comprimentos mantidos apos remocao de faixas ruidosas: {len(wv)}/{len(mask)}")""")
explicacao(
    'Antes de testar as combinações de pré-processamento, o script reaproveita a '
    'função criar_mascara_comprimentos (já usada nos demais pipelines) para excluir '
    'as faixas de baixa relação sinal-ruído nas extremidades do detector (400-450 nm '
    'e 2450-2500 nm) e as regiões de forte absorção de água (1340-1450 nm e '
    '1850-1950 nm). Isso reduz o número de comprimentos de onda de 4200 para cerca de '
    '3577, e garante que todas as comparações de pré-processamento partam da mesma '
    'base "limpa" — isolando o efeito de SNV/Detrend/2ª derivada/MSC do efeito da '
    'remoção de faixas, que já havia sido validado separadamente.'
)

# ===== 5. FUNCOES DE PRE-PROCESSAMENTO =====
doc.add_heading('5. Funções de Pré-processamento', level=1)
explicacao(
    'Esta é a parte central do script: quatro transformações espectrais são '
    'implementadas como funções puras (recebem a matriz X e devolvem a matriz '
    'transformada), o que permite compará-las de forma intercambiável no loop principal.'
)

doc.add_heading('5.1. SNV (baseline)', level=2)
code_block("""def snv(X):
    return (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)""")
explicacao(
    'Standard Normal Variate: cada espectro (linha de X) é centrado subtraindo sua '
    'própria média e escalado dividindo pelo seu próprio desvio-padrão. É o '
    'pré-processamento já usado como padrão em todos os pipelines anteriores do '
    'projeto, e serve aqui como ponto de comparação ("baseline") para medir o ganho '
    'ou a perda de cada alternativa.'
)

doc.add_heading('5.2. SNV + Detrend', level=2)
code_block("""def detrend(X, wv):
    \"\"\"Remove tendencia polinomial de 2a ordem de cada espectro (Barnes et al., 1989).\"\"\"
    Xd = np.empty_like(X)
    for i in range(X.shape[0]):
        coef = np.polyfit(wv, X[i], 2)
        Xd[i] = X[i] - np.polyval(coef, wv)
    return Xd""")
explicacao(
    'Após o SNV, ajusta-se um polinômio de 2º grau (quadrático) de cada espectro em '
    'função do comprimento de onda, e esse polinômio é subtraído do espectro. Isso '
    'remove curvaturas de linha de base que a normalização simples do SNV não elimina '
    'completamente — a combinação SNV+Detrend é a técnica clássica descrita por Barnes, '
    'Dhanoa e Lister (1989), citada na Seção 4.3 da METODOLOGIAV2.docx como uma '
    'combinação comum mas ainda não testada no projeto até este script.'
)

doc.add_heading('5.3. SNV + 2ª Derivada (Savitzky-Golay)', level=2)
code_block("""'SNV+2aDeriv(15,3)': lambda X, wv: savgol_filter(snv(X), window_length=15,
                                                  polyorder=3, deriv=2, axis=1),""")
explicacao(
    'Aplica-se o SNV e, em seguida, o filtro Savitzky-Golay pedindo diretamente a 2ª '
    'derivada (deriv=2), com janela de 15 pontos e polinômio de ordem 3 — exatamente '
    'a configuração citada na Recomendação 9.2. A 2ª derivada realça bandas de '
    'absorção sobrepostas e remove tanto deslocamentos constantes quanto tendências '
    'lineares de linha de base, mas amplifica ruído de alta frequência; por isso a '
    'janela usada aqui (15) é maior que a da 1ª derivada usada nos pipelines '
    'anteriores (janela 11), como compensação.'
)

doc.add_heading('5.4. MSC (Multiplicative Scatter Correction)', level=2)
code_block("""def msc(X, ref=None):
    \"\"\"Multiplicative Scatter Correction usando o espectro medio da amostra como referencia.\"\"\"
    if ref is None:
        ref = X.mean(axis=0)
    Xc = np.empty_like(X)
    for i in range(X.shape[0]):
        a, b = np.polyfit(ref, X[i], 1)
        Xc[i] = (X[i] - b) / a
    return Xc""")
explicacao(
    'O espectro médio de todas as amostras é usado como referência. Para cada '
    'espectro individual, ajusta-se uma reta (coeficientes a e b) entre ele e o '
    'espectro de referência; o espectro corrigido é obtido subtraindo o intercepto '
    '(b) e dividindo pelo coeficiente angular (a). Isso modela explicitamente o '
    'espalhamento multiplicativo de luz, sendo uma alternativa ao SNV mencionada na '
    'Seção 4.3 da metodologia como potencialmente superior para parâmetros físicos '
    'como a firmeza.'
)

doc.add_heading('5.5. Dicionário de Pré-processamentos', level=2)
code_block("""PREPROCESSAMENTOS = {
    'SNV':               lambda X, wv: snv(X),
    'SNV+Detrend':       lambda X, wv: detrend(snv(X), wv),
    'SNV+2aDeriv(15,3)': lambda X, wv: savgol_filter(snv(X), window_length=15, polyorder=3, deriv=2, axis=1),
    'MSC':               lambda X, wv: msc(X),
}""")
explicacao(
    'As quatro funções são reunidas em um dicionário nome -> função, o que permite '
    'iterar sobre elas de forma genérica no loop principal (Seção 8), sem repetir '
    'código para cada combinação.'
)

# ===== 6. PARAMETROS ALVO =====
doc.add_heading('6. Parâmetros-Alvo Analisados', level=1)
code_block("""PARAMETROS = [
    ('Comp',        dest.columns[3]),
    ('Diam.Equat.', dest.columns[4]),
    ('C:D',         dest.columns[5]),
    ('Firm',        dest.columns[6]),
    ('pH',          dest.columns[7]),
    ('Vit. C',      dest.columns[8]),
    ('AT',          dest.columns[9]),
    ('SS',          dest.columns[10]),
    ('SS/AT',       dest.columns[11]),
]""")
explicacao(
    'Diferente dos pipelines anteriores (que tratavam cada parâmetro em um script '
    'separado), este script varre todos os 9 parâmetros da metodologia em um único '
    'loop, usando o índice de coluna correspondente na planilha '
    '"Dados_analise_destrutiva". Isso garante que a busca em grade (grid search) '
    'de pré-processamento seja aplicada de forma consistente a todos os parâmetros, '
    'morfológicos e de qualidade química.'
)

# ===== 7. VALIDACAO E FUNCAO AVALIAR =====
doc.add_heading('7. Validação Cruzada e a Função avaliar()', level=1)
code_block("""gkf = GroupKFold(n_splits=5)
grupos = df_meta['Parcela']
NC_LIST = [1, 2, 3, 5, 10, 15]
N_REPEATS = 10


def avaliar(X, y):
    \"\"\"GroupKFold (5 folds x 10 repeticoes); retorna a melhor config entre NC_LIST.\"\"\"
    best = {'r2': -np.inf}
    for nc in NC_LIST:
        preds, reals = [], []
        for seed in range(N_REPEATS):
            g_shuf = grupos.sample(frac=1, random_state=seed)
            for tr, te in gkf.split(X, y, g_shuf):
                pls = PLSRegression(n_components=nc)
                scaler = StandardScaler()
                pls.fit(scaler.fit_transform(X[tr]), y[tr])
                preds.extend(pls.predict(scaler.transform(X[te])).ravel())
                reals.extend(y[te])
        r2 = r2_score(reals, preds)
        rmse = np.sqrt(mean_squared_error(reals, preds))
        rpd = y.std() / rmse
        if r2 > best['r2']:
            best = {'r2': r2, 'rmse': rmse, 'rpd': rpd, 'nc': nc}
    return best""")
explicacao(
    'A função avaliar() encapsula a busca em grade sobre o número de componentes '
    'PLS (1, 2, 3, 5, 10 ou 15), para uma matriz X e um vetor y já pré-processados. '
    'Para cada número de componentes, executa-se GroupKFold com 5 folds, repetido 10 '
    'vezes com embaralhamentos diferentes dos grupos (parcelas) — o mesmo esquema '
    'usado nos demais pipelines, que garante que os 5 frutos de uma mesma parcela '
    'nunca fiquem divididos entre treino e teste (evitando falsa replicação). Dentro '
    'de cada fold, o StandardScaler é ajustado apenas com os dados de treino e depois '
    'aplicado ao teste, evitando vazamento de informação. Ao final, calculam-se R², '
    'RMSE e RPD sobre todas as previsões acumuladas, e a função retorna apenas a '
    'melhor configuração de número de componentes (maior R²) para aquela combinação '
    'de pré-processamento.'
)

# ===== 8. LOOP PRINCIPAL =====
doc.add_heading('8. Loop Principal (Grid Search)', level=1)
code_block("""resultados = {}
melhores_globais = {}

for param_nome, col_nome in PARAMETROS:
    y = np.array([dest.set_index('Parcela')[col_nome].to_dict()[p] for p in df_meta['Parcela']])
    resultados[param_nome] = {}
    for prep_nome, prep_fn in PREPROCESSAMENTOS.items():
        Xp = prep_fn(X_raw, wv)
        best = avaliar(Xp, y)
        resultados[param_nome][prep_nome] = best
    melhor_prep = max(resultados[param_nome], key=lambda k: resultados[param_nome][k]['r2'])
    melhores_globais[param_nome] = melhor_prep""")
explicacao(
    'Para cada um dos 9 parâmetros, o vetor y é montado repetindo o valor de '
    'referência da parcela para os 5 frutos correspondentes (os 45 espectros '
    'compartilham apenas 9 valores independentes). Em seguida, para cada uma das '
    'quatro combinações de pré-processamento, a matriz X_raw é transformada (Xp) e '
    'avaliada pela função avaliar(). O resultado (melhor R², RMSE, RPD e número de '
    'componentes) é armazenado no dicionário aninhado resultados[parametro][preproc]. '
    'Ao final de cada parâmetro, melhor_prep identifica qual das quatro combinações '
    'obteve o maior R² — essa é a resposta central da Recomendação 9.2: qual '
    'pré-processamento é ótimo para cada parâmetro.'
)

# ===== 9. TABELA, CSV E GRAFICO =====
doc.add_heading('9. Tabela Comparativa, CSV e Gráfico', level=1)
code_block("""df_out = pd.DataFrame(linhas_csv)
df_out.to_csv('resultados_gridsearch_preprocessamento.csv', index=False)

fig, ax = plt.subplots(figsize=(13, 6))
for i, prep_nome in enumerate(preps):
    r2s = [resultados[p][prep_nome]['r2'] for p, _ in PARAMETROS]
    ax.bar(x + (i - 1.5) * width, r2s, width, label=prep_nome, color=cores[i])
...
plt.savefig('comparativo_gridsearch_preprocessamento.png', dpi=150)""")
explicacao(
    'Depois de percorrer todos os parâmetros, o script monta uma tabela (impressa no '
    'console e salva em resultados_gridsearch_preprocessamento.csv) com o R², RMSE, '
    'RPD e número de componentes de cada combinação de pré-processamento, mais a '
    'coluna "Melhor" indicando o vencedor de cada parâmetro. Em seguida, gera um '
    'gráfico de barras agrupadas (comparativo_gridsearch_preprocessamento.png) com um '
    'grupo de 4 barras (uma por pré-processamento) para cada um dos 9 parâmetros, '
    'facilitando a visualização de onde cada técnica ganha ou perde em relação ao SNV.'
)

# ===== 10. RESULTADOS DA ULTIMA EXECUCAO =====
doc.add_heading('10. Resultado da Última Execução', level=1)
csv_path = 'resultados_gridsearch_preprocessamento.csv'
if os.path.exists(csv_path):
    df_res = pd.read_csv(csv_path)
    explicacao(
        'A tabela abaixo resume a última execução do script (arquivo '
        'resultados_gridsearch_preprocessamento.csv), mostrando o R² de cada '
        'combinação e a melhor opção encontrada para cada parâmetro.'
    )
    linhas = []
    for _, r in df_res.iterrows():
        linhas.append([
            r['Parametro'],
            f"{r['SNV_R2']:.3f}",
            f"{r['SNV+Detrend_R2']:.3f}",
            f"{r['SNV+2aDeriv(15,3)_R2']:.3f}",
            f"{r['MSC_R2']:.3f}",
            r['Melhor'],
        ])
    tabela(['Parâmetro', 'SNV', 'SNV+Detrend', 'SNV+2ªDeriv', 'MSC', 'Melhor'], linhas)
    doc.add_paragraph()
    if os.path.exists('comparativo_gridsearch_preprocessamento.png'):
        doc.add_picture('comparativo_gridsearch_preprocessamento.png', width=Inches(6.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph('Figura 1. R² por parâmetro e pré-processamento.').italic = True
    vencedores = df_res['Melhor'].value_counts()
    resumo = ', '.join(f'{v}x {k}' for k, v in vencedores.items())
    explicacao(f'Resumo dos vencedores entre os 9 parâmetros: {resumo}.')
else:
    explicacao(
        'O arquivo resultados_gridsearch_preprocessamento.csv ainda não foi gerado. '
        'Execute "python nirs_preprocessamento_gridsearch.py" antes de rodar este '
        'script para incluir os resultados mais recentes neste relatório.'
    )

# ===== 11. COMO EXECUTAR =====
doc.add_heading('11. Como Executar', level=1)
code_block("python nirs_preprocessamento_gridsearch.py")
explicacao(
    'Basta rodar o script a partir da pasta do projeto, com Python e as bibliotecas '
    'pandas, numpy, scipy, scikit-learn e matplotlib instaladas. A execução demora '
    'cerca de 40 segundos (9 parâmetros x 4 pré-processamentos x 6 números de '
    'componentes x 10 repetições de validação cruzada) e produz três saídas: a '
    'tabela impressa no console, o arquivo CSV e o gráfico PNG, todos usados para '
    'montar a Seção 10 deste relatório.'
)

output = 'Relatorio_Codigo_GridSearch.docx'
doc.save(output)
print(f"Documento salvo: {output} ({os.path.getsize(output)/1024:.0f} KB)")
