"""Gera RESULTADOS_O3.docx - resultados + interpretacao da posicao O3 + comparacao O1 x O2 x O3."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

doc = Document()
for _ in range(5):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run('Resultados - Analise NIRS da posicao O3'); r.bold = True
r.font.size = Pt(23); r.font.color.rgb = RGBColor(0, 51, 102)
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run('stem-end to the right - Predicao das 16 caracteristicas do bloco P2')
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

heading('1. Metodo (identico ao de O1/O2)')
para('PLSR 1-6 LV | grid de 5 pre-processamentos (bruto, SNV, SNV+D1, SNV+D2, detrend) | 450-2450 nm | '
     'validacao Leave-One-Fruit-Out (21 folds) | teste de permutacao (99x) | leave-one-cultivar-out | '
     'correlacao dentro de cultivar. n = 21 frutos (TI/TH/TS, 7 cada), 1 espectro por fruto.')

heading('2. Tabela mestra - O3 (ordenada por R2cv)')
table(['Caracteristica','Pre-proc.','nLV','R2cv','RMSECV','RPD','RPIQ','r_within','R2_loco','p_perm','Williams'], [
    ('L*','SNV','5','0,79','1,382','2,21','3,20','+0,82','+0,80','0,01','bom'),
    ('C/D','SNV+D1','6','0,77','0,084','2,14','3,71','+0,18','-0,82','0,01','bom'),
    ('Fruit length','SNV+D1','6','0,77','4,09','2,12','4,14','+0,32','-0,12','0,01','bom'),
    ('pH','SNV+D1','1','0,57','0,046','1,55','2,84','-0,00','-0,60','0,01','razoavel'),
    ('MF (massa fresca)','SNV+D1','5','0,50','26,9','1,45','2,67','+0,02','-2,14','0,01','fraco'),
    ('Fruit diameter','SNV+D2','3','0,47','6,05','1,41','2,21','+0,35','-1,64','0,01','fraco'),
    ('a*/b*','SNV','2','0,45','0,106','1,38','1,52','+0,53','+0,32','0,01','fraco'),
    ('SS (solidos soluveis)','SNV+D2','6','0,38','0,312','1,30','1,92','+0,30','+0,46','0,01','fraco'),
    ('Hue','SNV','2','0,34','2,77','1,26','1,22','+0,45','+0,12','0,01','fraco'),
    ('b*','detrend','3','0,33','2,25','1,25','1,40','+0,37','+0,05','0,01','fraco'),
    ('Vit. C','SNV+D1','6','0,25','16,9','1,18','1,26','+0,21','-0,62','0,02','fraco'),
    ('Titratable acidity','SNV+D2','4','0,19','0,058','1,14','1,15','+0,45','-0,62','0,04','fraco'),
    ('SS/AT','SNV+D2','5','0,17','1,69','1,13','0,93','+0,43','-0,80','0,05','fraco'),
    ('Chroma','bruto','1','-0,04','4,28','1,00','0,65','+0,05','-0,73','0,12','fraco'),
    ('a*','bruto','1','-0,06','4,46','1,00','0,58','+0,02','-0,66','0,10','fraco'),
    ('Firmness','SNV+D1','1','-0,08','1,258','0,99','1,59','-0,24','-0,06','0,23','fraco'),
])

heading('3. Interpretacao')
heading('3.1 O3 e a melhor posicao encontrada ate agora - e por um motivo real, nao artefato', level=2)
para('Ao contrario de O2, onde o R2cv subia mas o R2_loco desabava, em O3 os dois indicadores sobem juntos '
     'para varios alvos. L* e o achado mais forte de toda a serie (O1, O2, O3): R2cv 0,79, r_within +0,82 e '
     'R2_loco +0,80 - a calibracao e quase tao boa dentro de cada cultivar quanto no conjunto todo, e '
     'generaliza para um cultivar que o modelo nao viu. Isso e evidencia de sinal de composicao real, nao de '
     'identidade varietal.')
para('Outros quatro alvos de cor/qualidade mostram o mesmo padrao qualitativo (r_within e R2_loco positivos, '
     'embora fracos): a*/b* (+0,53 / +0,32), SS (+0,30 / +0,46), Hue (+0,45 / +0,12) e b* (+0,37 / +0,05). '
     'Em O1 e O2 nenhum desses tinha R2_loco positivo.')
heading('3.2 Morfologia (C/D, comprimento) ainda mistura cultivar - mas bem menos que em O2', level=2)
para('C/D e comprimento repetem o padrao de R2cv alto blindando confundimento varietal (r_within baixo, '
     '0,18-0,32), mas o grau de confundimento e muito menor que em O2: R2_loco de -0,82 e -0,12 em O3, contra '
     '-4,68 e -29,5 em O2. Ainda nao sao calibracoes utilizaveis, mas o espectro O3 carrega menos artefato '
     'geometrico ligado ao cultivar do que O2 nessas variaveis.')
heading('3.3 pH - mesma conclusao nas tres posicoes', level=2)
para('r_within ~ 0 (-0,00) e R2_loco negativo (-0,60): como em O1 e O2, o R2cv de pH e discriminacao de '
     'cultivar, nao calibracao de composicao.')
heading('3.4 Vitamina C - O1 continua sendo a melhor posicao', level=2)
table(['Posicao', 'r_within', 'R2_loco'], [
    ('O1', '+0,52', '+0,21'),
    ('O2', '+0,39', '-9,00'),
    ('O3', '+0,21', '-0,62'),
])
para('O3 e intermediario entre O1 (melhor) e O2 (pior/catastrofico) para Vit. C, mas nao supera O1.')
heading('3.5 Sem sinal', level=2)
para('Firmness, a*, Chroma - R2cv negativo e p_perm nao significativo (0,10-0,23), como nas outras posicoes.')

heading('4. Comparacao O1 x O2 x O3')
table(['Aspecto', 'O1 (stem-end)', 'O2 (blossom-end)', 'O3 (stem-end direita)'], [
    ('Cultivares na PCA (SNV)', 'misturados', 'separados quase perfeitamente', 'ver pca_O3.png'),
    ('Melhor R2_loco positivo', 'Vit. C (+0,21)', 'nenhum', 'L* (+0,80)'),
    ('Alvos com r_within E R2_loco > 0', '1 (Vit. C)', '0', '5 (L*, a*/b*, SS, Hue, b*)'),
    ('Confundimento em C/D (R2_loco)', '-0,27', '-4,68', '-0,82'),
    ('Confundimento em comprimento (R2_loco)', '-3,65', '-29,5', '-0,12'),
    ('Melhor achado geral', 'Vit. C fraco/real', 'nenhum real', 'L* forte/real'),
])
bold_para('Conclusao preliminar: ', 'O3 e, ate agora, a posicao de captura mais promissora. E a unica em que '
          'uma caracteristica (L*) mostra sinal real forte (R2_loco alto e positivo), e e tambem a que menos '
          'confunde cultivar com morfologia. Falta rodar O4 e a media das 4 posicoes antes de recomendar um '
          'protocolo final.')

heading('5. Proximos passos')
numbered('Rodar O4 (Rscript analise_posicao.R O4) e a media das 4 posicoes (Rscript analise_posicao.R mean).')
numbered('Consolidar a tabela "caracteristica x posicao" (R2_loco + r_within) com as 4 posicoes completas.')
numbered('Investigar por que L* funciona bem especificamente em O3 - inspecionar pca_O3.png e espectros_O3.png '
         'para confirmar que nao ha o mesmo artefato de patamar de reflectancia visto em O2.')
numbered('Verificar o fruto THR4 (outlier em O1/O2) tambem na PCA de O3.')
numbered('Continuar priorizando L* (O3), Vit. C (O1) e, agora, tambem a*/b*, SS e Hue em O3 como candidatos '
         'com sinal real; manter a*, Chroma, Firmness fora de prioridade.')

for img, cap in [('resultados_O3/pca_O3.png', 'PCA (SNV) dos espectros O3.'),
                 ('resultados_O3/espectros_O3.png', 'Espectros O3: bruto, SNV e SNV+1a derivada.'),
                 ('resultados_O3/obs_pred_O3.png', 'Observado vs. predito (LOO) - 6 melhores caracteristicas por R2cv.')]:
    if os.path.exists(img):
        doc.add_page_break(); heading('Figura', level=2)
        doc.add_picture(img, width=Inches(6.2)); para(cap)

out = 'RESULTADOS_O3.docx'
doc.save(out)
print('Salvo:', out, f'({os.path.getsize(out)/1024:.0f} KB)')
