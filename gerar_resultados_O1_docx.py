"""Gera RESULTADOS_O1.docx - resultados + glossario + interpretacoes da posicao O1."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

doc = Document()
for _ in range(5):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run('Resultados - Analise NIRS da posicao O1'); r.bold = True
r.font.size = Pt(23); r.font.color.rgb = RGBColor(0, 51, 102)
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run('Predicao das 16 caracteristicas destrutivas do bloco P2 - com glossario e interpretacoes')
r.font.size = Pt(12); r.font.color.rgb = RGBColor(80, 80, 80)
d = doc.add_paragraph(); d.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = d.add_run('Setembro de 2026'); r.font.size = Pt(11); r.font.color.rgb = RGBColor(120, 120, 120)
doc.add_page_break()


def heading(x, level=1): doc.add_heading(x, level=level)
def para(x): doc.add_paragraph(x)
def bullet(x): doc.add_paragraph(x, style='List Bullet')
def numbered(x): doc.add_paragraph(x, style='List Number')
def bold_para(pfx, rest=''):
    p = doc.add_paragraph(); p.add_run(pfx).bold = True
    if rest: p.add_run(rest)
def table(headers, rows, fs=8):
    tb = doc.add_table(rows=len(rows) + 1, cols=len(headers), style='Light Shading Accent 1')
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        tb.cell(0, j).text = h
        for pp in tb.cell(0, j).paragraphs:
            for rr in pp.runs: rr.bold = True
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            tb.cell(i + 1, j).text = str(val)
    for row in tb.rows:
        for c in row.cells:
            for pp in c.paragraphs:
                for rr in pp.runs: rr.font.size = Pt(fs)
    doc.add_paragraph('')


# ---------------------------------------------------------------- 1
heading('1. Dados e metodo')
table(['Item', 'Valor'], [
    ('Espectros', 'posicao O1 apenas - 1 espectro por fruto'),
    ('Amostras', '21 frutos (TI, TH, TS - 7 cada)'),
    ('Faixa espectral', '450-2450 nm (4001 bandas; extremos ruidosos removidos)'),
    ('Pre-processamentos', 'bruto, SNV, SNV+SG 1a deriv., SNV+SG 2a deriv., detrend'),
    ('Modelo', 'PLSR, 1-6 variaveis latentes (nLV pelo minimo de RMSECV)'),
    ('Validacao', 'Leave-One-Fruit-Out (LOO, 21 folds)'),
    ('Controles', 'teste de permutacao (99x) + leave-one-cultivar-out + r dentro de cultivar'),
])

# ---------------------------------------------------------------- 2
heading('2. Glossario de abreviaturas')

heading('2.1 As 16 caracteristicas de referencia', level=2)
table(['Sigla', 'Nome na planilha', 'Significado', 'Unidade provavel', 'Amplitude'], [
    ('Length', 'Fruit length', 'Comprimento do fruto (pedunculo-apice)', 'mm', '46-73'),
    ('Diameter', 'Fruit diameter', 'Diametro equatorial', 'mm', '53-80'),
    ('C_D', 'C/D', 'Razao comprimento/diametro = FORMATO: >1 alongado, ~1 redondo, <1 achatado', 'adim.', '0,73-1,29'),
    ('MF', 'MF', 'Massa fresca (peso) do fruto', 'g', '78-200'),
    ('L*', 'L*', 'Luminosidade CIELab: 0 preto, 100 branco', 'adim.', '48-59'),
    ('a*', 'a*', 'Eixo verde(-)/vermelho(+) CIELab; sobe com o amadurecimento (licopeno)', 'adim.', '26-49'),
    ('b*', 'b*', 'Eixo azul(-)/amarelo(+) CIELab', 'adim.', '29-40'),
    ('a_b', 'a*/b*', 'Razao a*/b* - indice de cor/maturacao (maior = mais vermelho)', 'adim.', '0,84-1,46'),
    ('Hue', 'Hue', 'Angulo de tonalidade h = atan2(b*,a*); ~0 vermelho puro; diminui ao amadurecer', 'graus', '33-50'),
    ('Chroma', 'Chroma', 'Saturacao da cor C* = raiz(a*^2 + b*^2); maior = cor mais viva', 'adim.', '41-63'),
    ('Firmness', 'Firmness', 'Firmeza da polpa (resistencia a penetracao/compressao)', 'N ou kgf', '3,0-7,4'),
    ('pH', 'pH', 'pH do suco/polpa', '-', '4,19-4,40'),
    ('VitC', 'Vit. C', 'Teor de vitamina C (acido ascorbico)', 'mg/100 g', '56-149'),
    ('SS', 'Total soluble solids', 'Solidos soluveis totais (acucares) - grau Brix', 'Brix', '3,2-5,0'),
    ('AT', 'Titratable acid', 'Acidez titulavel (acidos organicos, sobretudo citrico)', '% ac. citrico', '0,29-0,54'),
    ('SS_AT', 'SS/AT ratio', 'Razao solidos soluveis / acidez - INDICE DE SABOR (doce/acido)', 'adim.', '6,7-14,0'),
])
para('Grupos: Morfologia = Length, Diameter, C_D, MF | Cor CIELab = L*, a*, b*, a_b, Hue, Chroma | '
     'Qualidade fisico-quimica = Firmness, pH, VitC, SS, AT, SS_AT.')

heading('2.2 Cultivares', level=2)
table(['Sigla', 'Tipo', 'Formato tipico'], [
    ('TI', 'Italiano (saladete / "roma")', 'alongado, C/D ~ 1,1-1,3'),
    ('TH', 'Holandes (tomate de cacho / rama)', 'redondo-pequeno, C/D ~ 0,85'),
    ('TS', 'Salada', 'grande e achatado, C/D ~ 0,75-0,85'),
])

heading('2.3 Espectroscopia e pre-processamento', level=2)
table(['Sigla', 'Significado'], [
    ('NIR / NIRS', 'Espectroscopia no infravermelho proximo (near-infrared)'),
    ('O1', 'Orientacao de captura 1 - fruto vertical, regiao basal (pedunculo) voltada ao sensor'),
    ('nm', 'Nanometro - unidade de comprimento de onda'),
    ('bruto / raw', 'Espectro sem nenhum tratamento'),
    ('SNV', 'Standard Normal Variate - centra e escala cada espectro; corrige espalhamento de luz e linha de base'),
    ('SG', 'Filtro Savitzky-Golay - suaviza e/ou deriva ajustando um polinomio local'),
    ('D1 / D2', '1a / 2a derivada (via SG). D1 realca inclinacoes; D2 realca picos e remove tendencia linear'),
    ('detrend', 'SNV seguido de remocao de tendencia polinomial ao longo do espectro'),
])

heading('2.4 Modelagem e validacao', level=2)
table(['Sigla', 'Significado'], [
    ('PLSR / PLS', 'Partial Least Squares Regression - cria poucos componentes ("variaveis latentes") a partir dos ~4000 comprimentos de onda; padrao em quimiometria NIR'),
    ('LV / nLV', 'Numero de variaveis latentes (componentes) do modelo PLS'),
    ('LOO', 'Leave-One-Out (aqui Leave-One-Fruit-Out): 21 ajustes, cada um deixando 1 fruto de fora'),
    ('LOCO', 'Leave-One-Cultivar-Out - treina em 2 cultivares e preve o 3o (3 rodadas)'),
    ('CV', 'Validacao cruzada (cross-validation)'),
    ('teste de permutacao / y-randomization', 'Embaralha o alvo centenas de vezes e refaz a validacao, para saber que R2 se obteria por acaso'),
])

heading('2.5 Metricas', level=2)
table(['Metrica', 'Formula', 'Como ler'], [
    ('R2cv', '1 - S(obs-pred)^2 / S(obs-media)^2', 'Variancia explicada NA VALIDACAO. 1 perfeito; 0 = chutar a media; <0 = pior que a media'),
    ('RMSECV', 'raiz[S(obs-pred)^2 / n]', 'Erro tipico de predicao, na unidade do alvo'),
    ('RPD', 'desvio-padrao(y) / RMSECV', 'Quantas vezes o erro e menor que a variacao natural. Criterio de Williams'),
    ('RPIQ', 'IQR(y) / RMSECV', 'Como o RPD mas com amplitude interquartil - mais confiavel com n pequeno / dados nao-normais'),
    ('bias', 'media(pred - obs)', 'Erro sistematico (super/subestimar)'),
    ('slope', 'inclinacao de obs ~ pred', '1 = ideal; <1 = predicoes achatadas em direcao a media'),
    ('r_within', 'cor(obs, pred) apos remover a media de cada cultivar', '~0 -> o modelo so distingue cultivares, nao calibra composicao. >0 -> ha sinal real alem do efeito varietal'),
    ('R2_loco', 'R2 do leave-one-cultivar-out', 'Muito negativo -> o modelo NAO generaliza para um cultivar novo'),
    ('p_perm', 'proporcao de permutacoes com R2 >= o observado', '>0,05 -> resultado indistinguivel do acaso'),
])
para('Classificacao de RPD (Williams, 2001): >2,5 excelente (predicao confiavel) | 2,0-2,5 bom (aproximada) '
     '| 1,5-2,0 razoavel (so triagem/tendencia) | <1,5 FRACO (nao recomendado para predicao).')

# ---------------------------------------------------------------- 3
doc.add_page_break()
heading('3. Tabela mestra (ordenada por R2cv)')
table(['Caracteristica','Pre-proc.','nLV','R2cv','RMSECV','RPD','RPIQ','r_within','R2_loco','p_perm','Williams'], [
    ('C/D','SNV+D2','4','0,72','0,092','1,94','3,36','+0,16','-0,27','0,01','razoavel'),
    ('pH','SNV','6','0,55','0,047','1,52','2,78','+0,16','-1,21','0,01','razoavel'),
    ('Vit. C','bruto','5','0,53','13,24','1,50','1,60','+0,52','+0,21','0,01','razoavel'),
    ('Fruit length','SNV','6','0,51','5,91','1,47','2,86','-0,07','-3,65','0,01','fraco'),
    ('Fruit diameter','SNV+D2','6','0,48','5,98','1,43','2,24','+0,03','-1,85','0,01','fraco'),
    ('MF (massa fresca)','detrend','2','0,45','28,2','1,38','2,55','-0,21','-1,59','0,01','fraco'),
    ('b*','SNV+D2','2','0,27','2,35','1,20','1,34','+0,22','+0,32','0,02','fraco'),
    ('SS (solidos soluveis)','SNV+D2','2','0,18','0,36','1,13','1,67','+0,06','-0,21','0,03','fraco'),
    ('L*','SNV+D2','2','0,06','2,90','1,05','1,52','-0,04','-0,61','0,04','fraco'),
    ('a*/b*','SNV','4','0,03','0,14','1,04','1,14','+0,16','-1,23','0,03','fraco'),
    ('Chroma','SNV+D2','1','0,01','4,17','1,03','0,67','+0,08','+0,06','0,07','fraco'),
    ('Firmness','SNV+D2','1','-0,02','1,23','1,01','1,63','+0,12','-1,12','0,14','fraco'),
    ('Hue','SNV','4','-0,03','3,46','1,01','0,98','+0,16','-1,15','0,07','fraco'),
    ('SS/AT','SNV+D2','1','-0,07','1,93','0,99','0,82','-0,21','+0,04','0,15','fraco'),
    ('a*','SNV+D2','1','-0,10','4,56','0,98','0,57','-0,13','-0,12','0,11','fraco'),
    ('Titratable acidity','SNV','1','-0,11','0,068','0,97','0,98','-0,16','+0,07','0,31','fraco'),
])
para('Grade completa de pre-processamentos por caracteristica: resultados_O1/grid_<carac>.csv')

# ---------------------------------------------------------------- 4
heading('4. Interpretacao geral')
heading('4.1 Nenhuma calibracao utilizavel a partir de O1 sozinha', level=2)
para('O melhor RPD e 1,94 (C/D) - abaixo do limiar de 2,0 ("bom"). Todas as demais ficam em "fraco". Com 1 '
     'espectro por fruto e n=21, a posicao O1 isolada NAO produz modelos de predicao quantitativa confiaveis '
     'para nenhuma das 16 caracteristicas.')
heading('4.2 O sinal aparente e contraste entre cultivares, nao composicao', level=2)
para('As caracteristicas com R2cv positivo (C/D, pH, comprimento, diametro, MF) mostram todas o mesmo padrao:')
bullet('r_within ~ 0 (ou negativo) -> o espectro nao explica a variacao fruto-a-fruto dentro do cultivar;')
bullet('R2_loco fortemente negativo (-1,2 a -3,7) -> o modelo desaba ao prever um cultivar que nao viu.')
para('Ou seja, o PLS aproveita as diferencas medias entre TI/TH/TS (formato, tamanho) e "chuta" a media do '
     'grupo. A PCA nao-supervisionada confirma: os cultivares nao se separam de forma limpa no espaco '
     'espectral de O1 (PC1 = 83%, dominada por um outlier - fruto THR4).')
heading('4.3 Unica excecao com sinal genuino: Vitamina C', level=2)
para('Vit. C e a unica com r_within = +0,52, R2_loco = +0,21 e p_perm = 0,01 - ha indicio de que o espectro '
     'O1 carrega informacao real sobre a variacao de vitamina C entre frutos do mesmo tipo.')
bold_para('Ressalva: ', 'o fruto THR4 tem Vit. C = 148,8 (~1,5x o segundo maior, 104) e tambem e o outlier '
          'espectral da PCA. Reajustar sem THR4 antes de confirmar.')
heading('4.4 Sem sinal nenhum', level=2)
para('a*, Titratable acidity e SS/AT tem R2cv negativo e p_perm nao significativo (0,11-0,31): o espectro O1 '
     'nao preve essas variaveis nem por confundimento.')
heading('4.5 Aviso tecnico', level=2)
para('Para varias caracteristicas de R2 ~ 0 o "vencedor" foi SNV+2a derivada com poucas LV - tipico de '
     'sobreajuste a ruido. O nLV foi escolhido na mesma LOO, o que torna o R2cv da tabela levemente otimista; '
     'os sinais confiaveis sao p_perm, R2_loco e r_within.')

# ---------------------------------------------------------------- 5
doc.add_page_break()
heading('5. Interpretacao caracteristica por caracteristica')

heading('5.1 Morfologia (Length, Diameter, C_D, MF)', level=2)
table(['Caract.', 'Resultado', 'Leitura'], [
    ('C_D (formato)', 'R2cv 0,72 - RPD 1,94 - RPIQ 3,36 - r_within +0,16 - R2_loco -0,27',
     'Melhor caso do estudo, mas ainda "razoavel". RPIQ alto e R2_loco so levemente negativo -> aqui o '
     'confundimento e menos severo: o formato altera a geometria de reflexao. Serve para triagem grosseira '
     'de formato, nao para medir C/D de um fruto.'),
    ('Length / Diameter', 'R2cv 0,48-0,51 - RPD ~1,45 - r_within ~0 - R2_loco -1,8 a -3,7',
     'Caso-escola de confundimento: o modelo "preve" porque os 3 cultivares tem tamanhos medios muito '
     'diferentes. Removido o efeito de cultivar nao sobra nada; prevendo cultivar novo o erro explode. Sem valor pratico.'),
    ('MF (massa)', 'R2cv 0,45 - RPD 1,38 - r_within -0,21 - R2_loco -1,6',
     'A massa e quase funcao do tamanho -> mesmo confundimento. r_within negativo: dentro do tipo o modelo '
     'ate erra o sentido. Sem valor.'),
])
para('Conclusao morfologia: nao usar O1 para estimar dimensoes/peso de frutos individuais. So C/D tem um '
     'residuo de sinal, e ainda fraco.')

heading('5.2 Cor CIELab (L*, a*, b*, a_b, Hue, Chroma)', level=2)
table(['Caract.', 'Resultado', 'Leitura'], [
    ('b* (amarelo)', 'R2cv 0,27 - RPD 1,20 - R2_loco +0,32 - r_within +0,22',
     'Unico parametro de cor com R2_loco positivo e r_within > 0 - indicio fraco de sinal real, coerente '
     'com a regiao visivel estar no espectro. Ainda assim RPD 1,20 = "fraco".'),
    ('L* (luminosidade)', 'R2cv 0,06', 'Praticamente sem predicao.'),
    ('a* (vermelho)', 'R2cv -0,10 - p_perm 0,11',
     'Sem sinal. Surpreende (a* e o eixo do licopeno), mas a faixa de a* e estreita e o fruto TSR2 '
     '(a* = 26 contra 40-49) e um outlier de referencia que desestabiliza tudo.'),
    ('a_b, Hue, Chroma', 'R2cv ~0 a -0,03 - RPIQ 0,67-1,14',
     'Combinacoes nao-lineares de a* e b*; herdam o problema de a* e a faixa estreita. Sem valor.'),
])
para('Conclusao cor: O1 no espectro completo nao calibra cor. Vale um teste focado so na regiao visivel '
     '(400-1000 nm) e apos verificar o outlier TSR2, antes de descartar de vez - principalmente a* e a_b, '
     'que tem base fisica (carotenoides).')

heading('5.3 Qualidade fisico-quimica (Firmness, pH, VitC, SS, AT, SS_AT)', level=2)
table(['Caract.', 'Resultado', 'Leitura'], [
    ('Vit. C', 'R2cv 0,53 - RPD 1,50 - r_within +0,52 - R2_loco +0,21 - p_perm 0,01',
     'O achado mais promissor. Unica caracteristica onde o espectro explica variacao DENTRO do cultivar e '
     'generaliza para cultivar novo. Mecanismo plausivel: acido ascorbico tem bandas O-H/C-H no NIR. Mas '
     'depende do fruto THR4 (valor extremo). Proximo passo: reajustar sem THR4; se r_within continuar ~0,4-0,5, '
     'vale desenvolver a calibracao.'),
    ('pH', 'R2cv 0,55 - RPD 1,52 - r_within +0,16 - R2_loco -1,21',
     'R2cv parece bom, mas o R2_loco negativo denuncia confundimento: os cultivares tem pH medio diferente '
     '(TH ~4,35 vs TI/TS ~4,22) e o modelo usa isso. Sinal intrinseco fraco.'),
    ('SS (Brix)', 'R2cv 0,18 - RPD 1,13 - r_within +0,06',
     'Fraco. Ao contrario do esperado (SS costuma ser bom alvo NIR), a faixa de variacao e pequena '
     '(3,2-5,0 Brix) e n=21 e insuficiente.'),
    ('Firmness', 'R2cv -0,02 - RPD 1,01 - p_perm 0,14', 'Sem sinal em O1.'),
    ('AT (acidez)', 'R2cv -0,11 - p_perm 0,31', 'Sem sinal - acidos em baixa concentracao, dificil por NIR e impossivel com este n.'),
    ('SS_AT (sabor)', 'R2cv -0,07 - p_perm 0,15', 'Sem sinal. E uma razao (SS/AT) -> propaga o erro de ambos.'),
])
para('Conclusao qualidade: so a vitamina C merece continuidade (com verificacao de outlier). pH, SS, '
     'firmeza, AT e SS/AT nao sao preditiveis a partir de O1 com os dados atuais.')

# ---------------------------------------------------------------- 6
heading('6. Conclusao e proximos passos')
bold_para('Conclusao: ', 'a posicao O1 isolada nao serve para calibrar as 16 caracteristicas do bloco P2 com '
          'o conjunto atual (n=21, 1 espectro/fruto). O pouco que os modelos capturam e diferenca varietal '
          '(confirmado por r_within ~ 0 e R2_loco negativo). Apenas a vitamina C mostra um sinal fraco porem '
          'real de composicao, ainda dependente de verificacao de outlier.')
numbered('Comparar posicoes - rodar o mesmo protocolo para O2, O3, O4, para a media das 4 posicoes e para a '
         'concatenacao (METODOLOGIA_R_P2, Secoes 7.2-7.3). A media deve elevar a relacao sinal/ruido.')
numbered('Investigar outliers: fruto THR4 (Vit. C e espectro) e TSR2 (a*). Reajustar Vit. C sem THR4.')
numbered('Teste focado de cor: so a regiao visivel 400-1000 nm para a*, a*/b*, Chroma.')
numbered('Nao priorizar a*, Titratable acidity, SS/AT, Firmness - sem sinal em O1.')
numbered('Manter leave-one-cultivar-out + teste de permutacao como criterio de aceitacao em todas as '
         'posicoes - o R2cv sozinho engana com n pequeno.')

# ---------------------------------------------------------------- figuras
for img, cap in [('resultados_O1/pca_O1.png', 'PCA (SNV) dos espectros O1 - cultivares nao se separam; fruto THR4 e outlier.'),
                 ('resultados_O1/espectros_O1.png', 'Espectros O1: bruto, SNV e SNV+1a derivada.'),
                 ('resultados_O1/obs_pred_O1.png', 'Observado vs. predito (LOO) - 6 melhores caracteristicas. Linha tracejada = predicao perfeita.')]:
    if os.path.exists(img):
        doc.add_page_break(); heading('Figura', level=2)
        doc.add_picture(img, width=Inches(6.2)); para(cap)

out = 'RESULTADOS_O1.docx'
doc.save(out)
print('Salvo:', out, f'({os.path.getsize(out)/1024:.0f} KB)')
