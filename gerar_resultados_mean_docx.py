"""Gera RESULTADOS_mean.docx - resultados + interpretacao da media das 4 posicoes."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

doc = Document()
for _ in range(5):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run('Resultados - Analise NIRS da media das 4 posicoes'); r.bold = True
r.font.size = Pt(23); r.font.color.rgb = RGBColor(0, 51, 102)
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run('means of 4 positions - Predicao das 16 caracteristicas do bloco P2')
r.font.size = Pt(12); r.font.color.rgb = RGBColor(80, 80, 80)
d = doc.add_paragraph(); d.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = d.add_run('Setembro de 2026'); r.font.size = Pt(11); r.font.color.rgb = RGBColor(120, 120, 120)
doc.add_page_break()


def heading(x, level=1): doc.add_heading(x, level=level)
def para(x): doc.add_paragraph(x)
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


heading('0. Nota sobre abreviaturas')
para('Glossario completo na Secao 2 de RESULTADOS_O1.docx. r_within: correlacao obs x pred apos remover a '
     'media de cada cultivar (~0 -> so separa cultivares). R2_loco: R2 ao treinar em 2 cultivares e prever o '
     '3o (muito negativo -> nao generaliza). p_perm: p do teste de permutacao.')
para('O espectro de entrada aqui e a media ponto a ponto das 4 orientacoes (O1-O4) de cada fruto (aba '
     '"means of 4 positions"), nao uma concatenacao - mesma dimensao espectral (4001 bandas) das analises '
     'anteriores.')

heading('1. Metodo (identico as demais posicoes)')
para('PLSR 1-6 LV | grid de 5 pre-processamentos | 450-2450 nm | Leave-One-Fruit-Out (21 folds) | permutacao '
     '(99x) | leave-one-cultivar-out | correlacao dentro de cultivar. n = 21 frutos (TI/TH/TS, 7 cada).')

heading('2. Tabela mestra - media das 4 posicoes (ordenada por R2cv)')
table(['Caracteristica','Pre-proc.','nLV','R2cv','RMSECV','RPD','RPIQ','r_within','R2_loco','p_perm','Williams'], [
    ('Fruit length','SNV+D1','6','0,96','1,68','5,18','10,09','+0,68','+0,56','0,01','excelente'),
    ('C/D','SNV+D2','1','0,86','0,064','2,78','4,82','-0,03','+0,81','0,01','excelente'),
    ('MF (massa fresca)','SNV+D1','6','0,79','17,5','2,23','4,12','+0,18','-0,90','0,01','bom'),
    ('pH','SNV','6','0,70','0,038','1,88','3,44','+0,07','-2,39','0,01','razoavel'),
    ('Fruit diameter','SNV+D2','2','0,64','5,03','1,70','2,67','+0,19','-1,83','0,01','razoavel'),
    ('L*','bruto','5','0,33','2,43','1,26','1,82','+0,30','-3,01','0,01','fraco'),
    ('SS (solidos soluveis)','SNV+D2','4','0,31','0,330','1,23','1,82','-0,18','-3,64','0,01','fraco'),
    ('Vit. C','SNV+D2','4','0,24','17,0','1,17','1,25','-0,12','-7,06','0,04','fraco'),
    ('a*/b*','SNV','1','0,23','0,125','1,17','1,29','+0,21','-0,63','0,01','fraco'),
    ('Hue','SNV','1','0,16','3,15','1,12','1,08','+0,14','-0,49','0,02','fraco'),
    ('b*','SNV','2','0,14','2,54','1,11','1,24','-0,08','-1,21','0,02','fraco'),
    ('Chroma','bruto','1','-0,07','4,33','0,99','0,65','-0,30','-3,43','0,11','fraco'),
    ('a*','bruto','1','-0,07','4,50','0,99','0,58','-0,29','-2,17','0,14','fraco'),
    ('Firmness','SNV+D2','1','-0,13','1,285','0,97','1,56','-0,74','-3,39','0,32','fraco'),
    ('Titratable acidity','SNV+D1','1','-0,14','0,069','0,96','0,97','-0,34','-0,35','0,24','fraco'),
    ('SS/AT','SNV+D2','1','-0,15','1,998','0,96','0,79','-0,92','-51,08','0,44','fraco'),
])

heading('3. Interpretacao')
heading('3.1 Fruit length na media e o melhor resultado de toda a serie', level=2)
para('R2cv = 0,96 (RPD 5,18, "excelente" por larga margem), r_within +0,68, R2_loco +0,56. E o unico caso em '
     'toda a analise (O1-O4 + media) em que um alvo morfologico combina R2cv altissimo com sinal real dentro '
     'de cultivar e generalizacao para cultivar nao visto. Nenhuma posicao isolada chega perto: o melhor R2cv '
     'de comprimento numa posicao unica foi O3 (0,77), mas com R2_loco negativo (-0,12). Media das 4 vistas '
     'cancela o ruido especifico de cada orientacao e revela um sinal geometrico consistente.')
heading('3.2 C/D tambem "excelente" - mas com ressalva', level=2)
para('R2cv 0,86, R2_loco +0,81 (2o melhor de toda a serie), porem r_within ~ 0 (-0,03). O modelo generaliza '
     'bem entre cultivares mas nao explica a variacao fruto-a-fruto dentro do mesmo cultivar. Tratar como '
     'achado promissor mas a confirmar com mais frutos por cultivar, nao como calibracao validada.')
heading('3.3 O sinal de cor encontrado em O3 desaparece na media', level=2)
table(['Alvo', 'r_within O3', 'R2_loco O3', 'r_within media', 'R2_loco media'], [
    ('L*', '+0,82', '+0,80', '+0,30', '-3,01'),
    ('a*/b*', '+0,53', '+0,32', '+0,21', '-0,63'),
    ('Hue', '+0,45', '+0,12', '+0,14', '-0,49'),
    ('SS', '+0,30', '+0,46', '-0,18', '-3,64'),
])
para('A media com as outras 3 orientacoes dilui/anula o sinal composicional que O3 capturava sozinha para '
     'cor e qualidade - coerente com a hipotese de que o sinal de L* em O3 e ligado a geometria especifica '
     'daquela vista, perdido ao promediar com O1/O2/O4.')
heading('3.4 pH e Vit. C - mesma conclusao de sempre, agravada', level=2)
para('pH: r_within ~ 0, R2_loco -2,39 (o pior entre as posicoes "puras", so perdendo para O2). Vit. C: '
     'R2_loco -7,06, muito pior que O1 (+0,21) - a media nao ajuda nenhum dos dois; O1 permanece a unica '
     'fonte de sinal real para Vit. C.')
heading('3.5 SS/AT: colapso extremo', level=2)
para('R2_loco = -51,08, o pior valor de toda a analise (pior ate que o de O2 para Chroma, -50,0). Nao usar.')

heading('4. Comparacao final - O3 vs. media')
table(['Aspecto', 'O3 (posicao unica)', 'Media das 4'], [
    ('Melhor achado', 'L* (excelente, real)', 'Fruit length (excelente, real)'),
    ('2o melhor achado', 'a*/b*, SS, Hue (fracos, reais)', 'C/D (forte, mas r_within~0)'),
    ('Sinal de cor/qualidade', '5 alvos com sinal real', 'nenhum (diluido)'),
    ('Sinal morfologico', 'fraco/confundido', 'muito forte (comprimento, C/D)'),
])
bold_para('Conclusao: ', 'as duas abordagens sao complementares, nao substitutas. A media das 4 posicoes e '
          'claramente superior para morfologia (comprimento, e com ressalva C/D), enquanto O3 isolada e a '
          'unica fonte de sinal real para cor e qualidade interna (L*, a*/b*, Hue, SS). Um protocolo pratico '
          'poderia usar a media das 4 vistas para comprimento/C/D e o espectro de O3 especificamente para L*.')

heading('5. Proximos passos')
para('Ver relatorio consolidado RESULTADOS_CONSOLIDADO.docx.')

for img, cap in [('resultados_mean/pca_mean.png', 'PCA (SNV) dos espectros medios.'),
                 ('resultados_mean/espectros_mean.png', 'Espectros medios: bruto, SNV e SNV+1a derivada.'),
                 ('resultados_mean/obs_pred_mean.png', 'Observado vs. predito (LOO) - 6 melhores caracteristicas por R2cv.')]:
    if os.path.exists(img):
        doc.add_page_break(); heading('Figura', level=2)
        doc.add_picture(img, width=Inches(6.2)); para(cap)

out = 'RESULTADOS_mean.docx'
doc.save(out)
print('Salvo:', out, f'({os.path.getsize(out)/1024:.0f} KB)')
