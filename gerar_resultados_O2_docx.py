"""Gera RESULTADOS_O2.docx - resultados + interpretacao da posicao O2 + comparacao O1 x O2."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

doc = Document()
for _ in range(5):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run('Resultados - Analise NIRS da posicao O2'); r.bold = True
r.font.size = Pt(23); r.font.color.rgb = RGBColor(0, 51, 102)
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run('blossom-end view - Predicao das 16 caracteristicas do bloco P2')
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


heading('0. Nota sobre abreviaturas')
para('O glossario completo (16 caracteristicas com significado e unidade, cultivares TI/TH/TS, SNV/D1/D2, '
     'PLSR, e todas as metricas) esta na Secao 2 de RESULTADOS_O1.docx. Lembrete das colunas de controle:')
bold_para('r_within: ', 'correlacao obs x pred apos remover a media de cada cultivar. ~0 -> o modelo so separa cultivares.')
bold_para('R2_loco: ', 'R2 ao treinar em 2 cultivares e prever o 3o. Muito negativo -> nao generaliza para cultivar novo.')
bold_para('p_perm: ', 'p do teste de permutacao. > 0,05 -> indistinguivel do acaso.')

heading('1. Metodo (identico ao de O1)')
para('PLSR 1-6 LV | grid de 5 pre-processamentos (bruto, SNV, SNV+D1, SNV+D2, detrend) | 450-2450 nm | '
     'validacao Leave-One-Fruit-Out (21 folds) | teste de permutacao (99x) | leave-one-cultivar-out | '
     'correlacao dentro de cultivar. n = 21 frutos (TI/TH/TS, 7 cada), 1 espectro por fruto.')

heading('2. Tabela mestra - O2 (ordenada por R2cv)')
table(['Caracteristica','Pre-proc.','nLV','R2cv','RMSECV','RPD','RPIQ','r_within','R2_loco','p_perm','Williams'], [
    ('C/D','bruto','5','0,88','0,062','2,91','5,04','+0,12','-4,68','0,01','excelente'),
    ('pH','bruto','6','0,82','0,030','2,40','4,38','+0,31','-14,70','0,01','bom'),
    ('MF (massa fresca)','SNV+D1','6','0,74','19,3','2,02','3,73','+0,20','-2,83','0,01','bom'),
    ('Fruit diameter','SNV+D1','5','0,72','4,38','1,95','3,06','+0,12','-4,03','0,01','razoavel'),
    ('Fruit length','SNV+D2','2','0,65','4,98','1,74','3,39','-0,28','-29,52','0,01','razoavel'),
    ('L*','SNV','5','0,44','2,22','1,37','1,99','+0,52','-1,92','0,01','fraco'),
    ('Vit. C','bruto','4','0,31','16,1','1,24','1,32','+0,39','-9,00','0,01','fraco'),
    ('SS (solidos soluveis)','SNV+D2','1','0,24','0,35','1,18','1,74','-0,86','-27,97','0,01','fraco'),
    ('a*/b*','SNV+D1','3','0,06','0,14','1,05','1,16','-0,24','-1,55','0,05','fraco'),
    ('b*','SNV','3','0,02','2,71','1,04','1,16','+0,14','-1,16','0,07','fraco'),
    ('Hue','SNV+D1','3','-0,02','3,46','1,01','0,98','-0,24','-1,64','0,04','fraco'),
    ('SS/AT','bruto','2','-0,06','1,92','1,00','0,83','+0,14','-0,30','0,10','fraco'),
    ('Firmness','bruto','4','-0,07','1,26','0,99','1,59','+0,42','-29,87','0,05','fraco'),
    ('Titratable acidity','SNV','1','-0,10','0,067','0,98','0,98','-0,29','-0,45','0,19','fraco'),
    ('Chroma','SNV+D2','2','-0,12','4,43','0,97','0,63','-0,45','-49,97','0,22','fraco'),
    ('a*','SNV','1','-0,13','4,61','0,97','0,56','-0,64','-0,05','0,24','fraco'),
])

heading('3. Interpretacao')
heading('3.1 R2cv sobe muito, mas e uma armadilha', level=2)
para('Em O2, C/D chega a R2cv 0,88 (RPD 2,91 = "excelente") e pH a 0,82 ("bom") - muito melhores que em O1. '
     'Porem o R2_loco dessas mesmas caracteristicas despenca para -4,7 (C/D), -14,7 (pH), -29,5 (comprimento), '
     '-28 (SS), -30 (firmeza), -50 (Chroma). Um R2 de -50 significa que, ao prever um cultivar nao visto, o '
     'erro e ~50x a variancia do alvo. NAO ha calibracao - o modelo apenas reconhece o cultivar e devolve a '
     'media do grupo.')
heading('3.2 A causa: os espectros O2 carregam identidade varietal muito forte', level=2)
bullet('PCA (resultados_O2/pca_O2.png): os 3 cultivares se separam quase perfeitamente no espaco espectral '
       'de O2 (PC1 = 85%). Em O1 estavam misturados.')
bullet('Espectros brutos (resultados_O2/espectros_O2.png): as 7 curvas do Italiano (TI) ficam num patamar de '
       'reflectancia de ~1,5-2,1, completamente separadas de TH+TS (~0,3-1,5). A vista apical (blossom-end) '
       'do fruto alongado apresenta geometria muito diferente ao sensor -> deslocamento de linha de base '
       'ligado ao cultivar.')
bullet('O pre-processamento "bruto" (raw) vencer para C/D e pH confirma: o modelo usa esse patamar de '
       'reflectancia, que e artefato geometrico, nao composicao.')
heading('3.3 Sinal dentro de cultivar - um pouco melhor que O1 para alguns alvos', level=2)
table(['Alvo', 'r_within O2', 'r_within O1', 'Comentario'], [
    ('L* (luminosidade)', '+0,52', '-0,04', 'O2 capta variacao de luminosidade dentro do tipo; O1 nao. Ainda "fraco" (RPD 1,37).'),
    ('Firmness', '+0,42', '+0,12', 'Sinal intra-cultivar, mas R2cv global negativo e R2_loco -30. Instavel.'),
    ('Vit. C', '+0,39', '+0,52', 'O1 e melhor para vitamina C (r_within maior e R2_loco +0,2 vs -9,0 em O2).'),
    ('pH', '+0,31', '+0,16', 'Algum sinal, mas dominado pelo confundimento (R2_loco -14,7).'),
])
heading('3.4 Sem sinal', level=2)
para('a*, Chroma, Titratable acidity, SS/AT - R2cv negativo e p_perm nao significativo (0,10-0,24). '
     'r_within de a* e SS fortemente negativo (-0,64, -0,86): dentro do cultivar o modelo erra o sentido.')
heading('3.5 Outlier persistente', level=2)
para('O fruto THR4 e de novo o outlier extremo na PCA (PC2 ~ 8) e tem um pico anomalo em ~1100 nm na 1a '
     'derivada. Presente em todas as posicoes - precisa ser verificado na origem.')

heading('4. Comparacao O1 x O2')
table(['Aspecto', 'O1 (base / stem-end)', 'O2 (apice / blossom-end)'], [
    ('Cultivares na PCA (SNV)', 'misturados', 'separados quase perfeitamente'),
    ('R2cv de morfologia + pH', '0,45-0,72', '0,65-0,88'),
    ('R2_loco dos mesmos', '-0,3 a -3,7', '-2,8 a -29,5'),
    ('Alvos "bom/excelente" (RPD)', '0', '3 (C/D, pH, MF) - todos espurios'),
    ('Melhor caso real (r_within>0 E R2_loco>0)', 'Vit. C (+0,52 / +0,21)', 'nenhum'),
    ('L* dentro de cultivar (r_within)', '-0,04', '+0,52'),
    ('Grau de confundimento com cultivar', 'moderado', 'severo'),
])
bold_para('Conclusao: ', 'a posicao O2, isolada, e PIOR que O1 para calibracao - o R2cv mais alto e '
          'inteiramente discriminacao de cultivar (comprovado pelos R2_loco de -4 a -50 e pela PCA). O unico '
          'ponto a favor de O2 e um sinal intra-cultivar um pouco melhor para L* (luminosidade). Para '
          'vitamina C, O1 e claramente superior.')
para('Reforca a regra metodologica: o R2cv sozinho engana - a posicao que "parece" melhor (O2) e a mais '
     'contaminada. O criterio de escolha de posicao/protocolo deve ser R2_loco + r_within.')

heading('5. Proximos passos')
numbered('Rodar O3 e O4 (Rscript analise_posicao.R O3 / O4) e a media das 4 (Rscript analise_posicao.R mean).')
numbered('Consolidar uma tabela unica "caracteristica x posicao" usando R2_loco e r_within como criterio - nao o R2cv.')
numbered('Verificar o fruto THR4 na base de dados original (outlier em todas as posicoes).')
numbered('Para vitamina C e L*: reajustar sem THR4 e testar a media das posicoes - os dois unicos alvos com '
         'indicio de sinal intra-cultivar (O1 para VitC, O2 para L*).')
numbered('Continuar nao priorizando a*, Chroma, Titratable acidity, SS/AT, Hue - sem sinal em nenhuma posicao ate agora.')

for img, cap in [('resultados_O2/pca_O2.png', 'PCA (SNV) dos espectros O2 - os 3 cultivares se separam quase perfeitamente (contraste com O1).'),
                 ('resultados_O2/espectros_O2.png', 'Espectros O2: no bruto, o Italiano (TI) fica num patamar de reflectancia totalmente separado.'),
                 ('resultados_O2/obs_pred_O2.png', 'Observado vs. predito (LOO) - 6 melhores caracteristicas por R2cv.')]:
    if os.path.exists(img):
        doc.add_page_break(); heading('Figura', level=2)
        doc.add_picture(img, width=Inches(6.2)); para(cap)

out = 'RESULTADOS_O2.docx'
doc.save(out)
print('Salvo:', out, f'({os.path.getsize(out)/1024:.0f} KB)')
