"""Gera RESULTADOS_CONSOLIDADO.docx - comparacao final O1/O2/O3/O4/media."""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import os

doc = Document()
for _ in range(5):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run('Resultados consolidados'); r.bold = True
r.font.size = Pt(23); r.font.color.rgb = RGBColor(0, 51, 102)
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run('NIRS x posicao de captura (P2) - Comparacao O1 . O2 . O3 . O4 . media das 4')
r.font.size = Pt(12); r.font.color.rgb = RGBColor(80, 80, 80)
d = doc.add_paragraph(); d.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = d.add_run('Setembro de 2026'); r.font.size = Pt(11); r.font.color.rgb = RGBColor(120, 120, 120)
doc.add_page_break()


def heading(x, level=1): doc.add_heading(x, level=level)
def para(x): doc.add_paragraph(x)
def numbered(x): doc.add_paragraph(x, style='List Number')
def bullet(x): doc.add_paragraph(x, style='List Bullet')
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
def code_block(text, fs=6.5):
    for line in text.split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line if line.strip() else ' ')
        run.font.size = Pt(fs)
        run.font.name = 'Consolas'
        rpr = run._element.get_or_add_rPr()
        rFonts = rpr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = rpr.makeelement(qn('w:rFonts'), {})
            rpr.append(rFonts)
        rFonts.set(qn('w:eastAsia'), 'Consolas')


para('Relatorios individuais: RESULTADOS_O1.docx, RESULTADOS_O2.docx, RESULTADOS_O3.docx, RESULTADOS_O4.docx, '
     'RESULTADOS_mean.docx.')
bold_para('Criterio de leitura: ', 'nunca usar R2cv isoladamente (com n=21 e milhares de bandas, R2cv alto '
          'pode ser so discriminacao de cultivar). O criterio de decisao e r_within (sinal dentro de '
          'cultivar) + R2_loco (generaliza para cultivar novo) - os dois positivos = evidencia de calibracao '
          'real.')

heading('0. Metodologia detalhada - por que nao usar so R2cv')
heading('0.1 O problema: n pequeno, milhares de bandas, 3 grupos muito diferentes', level=2)
para('O desenho e n=21 frutos, ~4000 bandas espectrais (p >> n), divididos em 3 cultivares (TI/TH/TS, 7 '
     'frutos cada) que diferem muito entre si em forma, cor e tamanho - por biologia, nao por um tratamento '
     'controlado.')
para('Isso cria um problema estatistico chamado confundimento (confounding): se tanto o espectro quanto a '
     'caracteristica-alvo variam principalmente entre cultivares (e pouco dentro de cada cultivar), um '
     'modelo pode "acertar" apenas reconhecendo de qual cultivar e o fruto e devolvendo a media daquele '
     'grupo - sem captar nenhuma relacao real espectro-composicao.')
para('O motivo de isso nao aparecer no R2cv comum (validacao Leave-One-Fruit-Out, LOO) e sutil: ao deixar 1 '
     'fruto de fora, os outros 6 frutos do mesmo cultivar continuam no treino. O modelo aprende a impressao '
     'digital espectral daquele cultivar e a media do grupo para o alvo, e prediz proximo dessa media - o '
     'que ja basta para um R2cv alto se o alvo difere bastante entre cultivares, mesmo sem nenhuma relacao '
     'de composicao real.')
heading('0.2 r_within - ha sinal dentro do cultivar?', level=2)
para('Codigo: analise_posicao.R, linhas 199-207. Formula: yr = y - media_do_cultivar(y); '
     'pr = yhat - media_do_cultivar(yhat); r_within = correlacao(yr, pr).')
para('Para cada fruto, subtrai-se a media do seu proprio cultivar tanto do valor observado quanto do '
     'predito. O que sobra e a variacao fruto-a-fruto DENTRO do tipo - a parte biologicamente interessante '
     '(ex.: dois frutos Italiano, um mais maduro que o outro). Correlaciona-se os dois residuos: modelo que '
     'so reconhece cultivar -> depois de remover a media do grupo quase nao sobra sinal -> r_within ~ 0. '
     'Modelo que capta composicao real -> a correlacao sobrevive -> r_within > 0.')
heading('0.3 R2_loco - o teste mais duro: cultivar nunca visto', level=2)
para('Codigo: analise_posicao.R, linhas 209-220. O modelo e treinado em 2 cultivares inteiros (14 frutos) e '
     'testado no 3o, nunca visto em nenhum grau (nem para calcular medias) - repete-se 3x (uma rodada por '
     'cultivar deixado de fora) e o R2 final e calculado sobre as 21 predicoes fora-da-amostra combinadas.')
para('Por que isso desmonta o artefato: se o modelo so sabe "essa impressao espectral = cultivar TI -> '
     'devolver a media do TI", ele nao tem como fazer isso para um cultivar que nunca esteve no treino - e '
     'forcado a extrapolar via uma relacao espectro-cultivar aprendida em OUTROS dois grupos, que nao tem '
     'nada a ver com o novo. O erro resultante costuma ser maior que simplesmente chutar a media geral '
     '(R2=0), dai os valores fortemente negativos observados quando o R2cv era artefato.')
heading('0.4 p_perm - separando "sinal" de "acaso" (nao confundimento)', level=2)
para('Codigo: analise_posicao.R, linhas 261-269. Embaralha-se y 99 vezes (quebrando qualquer relacao real '
     'com o espectro) e roda-se a mesma LOO. Se o R2 observado nao supera a maioria dos R2 obtidos com y '
     'aleatorio, p_perm alto -> o modelo nao supera o acaso, risco esperado quando ha mais bandas (~4000) '
     'que amostras (21).')
bold_para('Atencao: ', 'p_perm NAO pega o confundimento de cultivar - embaralhar y tambem quebra a '
          'associacao cultivar-alvo, entao um modelo puramente "identificador de cultivar" ainda pode ter '
          'p_perm bem significativo (< 0,05). Por isso os tres criterios sao complementares, nao '
          'substitutos.')
table(['Metrica', 'O que descarta'], [
    ('p_perm', 'Resultado por puro acaso (overfitting com p>>n)'),
    ('r_within', 'Modelo que so distingue cultivar, sem sinal interno'),
    ('R2_loco', 'Modelo que nao generaliza alem dos cultivares vistos'),
])
heading('0.5 Exemplo lado a lado: C/D em O2 (artefato) vs. L* em O3 (sinal real)', level=2)
table(['Passo', 'C/D - posicao O2', 'L* - posicao O3'], [
    ('R2cv (LOO normal)', '0,88 - parece "excelente"', '0,79 - "bom"'),
    ('O que o LOO permite', 'ao deixar 1 fruto fora, os outros 6 do mesmo cultivar continuam no treino -> o '
     'modelo aprende a media de C/D daquele cultivar e a reflectancia que o identifica', 'idem, mas aqui a '
     'predicao nao depende so disso'),
    ('r_within', '+0,12 (~0) - quase nada sobra ao remover a media do cultivar', '+0,82 - a maior parte do '
     'sinal sobrevive: o modelo distingue frutos do MESMO cultivar entre si'),
    ('R2_loco (treina em 2, testa no 3o nunca visto)', '-4,68 - o erro e ~4,7x a variancia do proprio alvo; '
     'pior que simplesmente chutar a media geral', '+0,80 - quase nenhuma perda em relacao ao R2cv normal'),
    ('Interpretacao', 'O modelo NAO calibra C/D; apenas memorizou "esse espectro = Italiano/Holandes/Salada" '
     'e devolveu a media de C/D daquele tipo. Como cada cultivar tem forma de fruto muito diferente, isso '
     'basta para um R2cv alto - mas e inutil para um cultivar novo', 'Evidencia de que L* esta ligado a uma '
     'variacao real de composicao/pigmentacao da casca, que se repete de forma parecida em qualquer '
     'cultivar - por isso o modelo treinado em 2 tipos consegue prever bem o 3o'),
], fs=7)
para('Esse contraste e o motivo de a Secao 1 usar R2_loco/r_within como criterio de decisao, e nao a coluna '
     'de R2cv das tabelas mestras de cada posicao.')
heading('0.6 Fluxo completo do script (analise_posicao.R)', level=2)
numbered('Importacao e alinhamento (linhas 74-128): le a aba de espectros (comprimentos de onda x frutos), '
         'transpoe; extrai cultivar/fruto do codigo via regex; le a aba destrutiva; casa os dois por '
         'Treatments+Repetition; corta para 450-2450 nm.')
numbered('Grid de 5 pre-processamentos (linhas 130-144): bruto, SNV, SNV+1a derivada, SNV+2a derivada, '
         'detrend. Cada um age linha a linha (um espectro por vez), por isso pode ser calculado uma unica '
         'vez sem vazar informacao para a validacao cruzada.')
numbered('Loop pelas 16 caracteristicas (linhas 227-282): loo_all_nlv() (174-185) roda Leave-One-Fruit-Out '
         'completo (21 ajustes) testando 1 a 6 variaveis latentes, para cada um dos 5 pre-processamentos; '
         'escolhe o nLV de menor RMSECV por pre-proc (grid completo salvo em resultados_X/grid_<carac>.csv); '
         'escolhe o melhor pre-processamento geral; loo_fixed() (189-197) refaz a LOO com esse (preproc,nLV) '
         'fixo para o teste de permutacao (99x); calcula p_perm, R2_loco (via loco()) e r_within.')
numbered('Tabela mestra + graficos (linhas 284-347): CSV ordenado por R2cv, espectros coloridos por '
         'cultivar, PCA nao-supervisionada (diagnostico visual do confundimento) e observado x predito das '
         '6 melhores caracteristicas.')
bold_para('Limitacao assumida no proprio script (linhas 32-34): ', 'o nLV e escolhido na mesma LOO que gera '
          'o R2cv, entao o R2cv fica levemente otimista (1 hiperparametro ajustado nos mesmos dados) - por '
          'isso a regra do projeto e nunca decidir por R2cv sozinho, e sim por p_perm + R2_loco + r_within.')

heading('1. Tabela caracteristica x posicao (R2_loco / r_within)')
para('Celula = R2_loco / r_within. Em negrito na versao markdown: ambos positivos (evidencia de sinal real).')
table(['Caracteristica','O1','O2','O3','O4','Media'], [
    ('Fruit length','-3,65 / -0,07','-29,5 / -0,28','-0,12 / +0,32','-0,57 / +0,38','+0,56 / +0,68'),
    ('Fruit diameter','-1,85 / +0,03','-4,03 / +0,12','-1,64 / +0,35','-0,50 / +0,50','-1,83 / +0,19'),
    ('C/D','-0,27 / +0,16','-4,68 / +0,12','-0,82 / +0,18','-1,06 / +0,27','+0,81 / -0,03 (ver 2.2)'),
    ('MF (massa fresca)','-1,59 / -0,21','-2,83 / +0,20','-2,14 / +0,02','-1,06 / +0,45','-0,90 / +0,18'),
    ('L*','-0,61 / -0,04','-1,92 / +0,52','+0,80 / +0,82','-0,01 / +0,30','-3,01 / +0,30'),
    ('a*','-0,12 / -0,13','-0,05 / -0,64','-0,66 / +0,02','-0,36 / +0,08','-2,17 / -0,29'),
    ('b*','+0,32 / +0,22','-1,16 / +0,14','+0,05 / +0,37','-0,30 / -0,09','-1,21 / -0,08'),
    ('a*/b*','-1,23 / +0,16','-1,55 / -0,24','+0,32 / +0,53','+0,03 / +0,45','-0,63 / +0,21'),
    ('Hue','-1,15 / +0,16','-1,64 / -0,24','+0,12 / +0,45','-0,04 / +0,38','-0,49 / +0,14'),
    ('Chroma','+0,06 / +0,08','-49,97 / -0,45','-0,73 / +0,05','-0,23 / +0,04','-3,43 / -0,30'),
    ('Firmness','-1,12 / +0,12','-29,87 / +0,42','-0,06 / -0,24','+0,14 / -0,09','-3,39 / -0,74'),
    ('pH','-1,21 / +0,16','-14,70 / +0,31','-0,60 / -0,00','-0,91 / +0,05','-2,39 / +0,07'),
    ('Vit. C','+0,21 / +0,52','-9,00 / +0,39','-0,62 / +0,21','-1,15 / -0,20','-7,06 / -0,12'),
    ('SS','-0,21 / +0,06','-27,97 / -0,86','+0,46 / +0,30','-0,26 / -0,41','-3,64 / -0,18'),
    ('AT','+0,07 / -0,16','-0,45 / -0,29','-0,62 / +0,45','-0,25 / -0,05','-0,35 / -0,34'),
    ('SS/AT','+0,04 / -0,21','-0,30 / +0,14','-0,80 / +0,43','-0,61 / -0,20','-51,08 / -0,92'),
])
para('(Vit. C, AT e SS/AT em O1/media tem sinais isolados positivos de R2_loco com r_within negativo/nulo - '
     'inconsistentes, nao contam como achado real.)')

heading('2. Achados reais (r_within e R2_loco positivos) - recomendacao por caracteristica')
table(['Caracteristica', 'Melhor posicao', 'R2_loco', 'r_within', 'Forca'], [
    ('Fruit length', 'Media das 4', '+0,56', '+0,68', 'Forte - RPD 5,18, "excelente"'),
    ('L*', 'O3', '+0,80', '+0,82', 'Forte - o achado mais robusto da serie'),
    ('SS (solidos soluveis)', 'O3', '+0,46', '+0,30', 'Fraco mas real'),
    ('Vit. C', 'O1', '+0,21', '+0,52', 'Fraco mas real'),
    ('a*/b*', 'O3', '+0,32', '+0,53', 'Fraco mas real'),
    ('Hue', 'O3', '+0,12', '+0,45', 'Fraco mas real'),
    ('b*', 'O3 (e O1)', '+0,05 (+0,32)', '+0,37 (+0,22)', 'Muito fraco mas real em 2 posicoes'),
])
heading('2.1 Sem sinal real em nenhuma posicao', level=2)
para('Diameter, MF, C/D (ressalva no 2.2), a*, Chroma, Firmness, pH, AT, SS/AT - em nenhuma das 5 analises os '
     'dois criterios (r_within>0 e R2_loco>0) coincidem de forma consistente.')
heading('2.2 C/D na media: caso a parte', level=2)
para('R2_loco = +0,81 (2o melhor de toda a serie) mas r_within ~ 0 (-0,03). Nao e evidencia do mesmo tipo que '
     'Length/L*: o modelo generaliza a relacao cultivar->C/D, mas nao explica variacao fruto-a-fruto dentro '
     'do cultivar. Promissor, mas precisa de mais frutos por cultivar para separar "generaliza porque e uma '
     'relacao real e forte" de "generaliza porque C/D e a assinatura espectral do cultivar covariam por '
     'acaso com so 3 grupos". Tratar como hipotese, nao como calibracao validada.')

heading('3. Panorama por posicao')
table(['Posicao', 'Perfil', 'No achados reais', 'Conclusao de uso'], [
    ('O1 (stem-end)', 'unico sinal: Vit. C', '1', 'Unica fonte de sinal para Vit. C'),
    ('O2 (blossom-end)', 'confundimento severo (Italiano em patamar de reflectancia isolado)', '0', 'Nao recomendada'),
    ('O3 (stem-end direita)', 'sinal real em cor/qualidade (L*, a*/b*, Hue, SS, b*)', '5', 'Melhor posicao isolada'),
    ('O4 (stem-end esquerda)', 'confundimento moderado, repete fracamente o padrao de O3', '0 (a*/b* limitrofe)', 'Sem vantagem sobre O3'),
    ('Media das 4', 'sinal morfologico forte (comprimento, C/D-ressalva); cor diluida', '1 (2 com ressalva)', 'Melhor para morfologia'),
])

heading('4. Recomendacao de protocolo')
numbered('Comprimento do fruto: usar o espectro medio das 4 orientacoes - unico caso "excelente" e '
         'genuinamente validado (R2_loco +0,56).')
numbered('L* (luminosidade): usar especificamente o espectro O3 - sinal forte e nao replicado em nenhuma '
         'outra posicao nem na media.')
numbered('Vitamina C: usar O1 - unica posicao com sinal real, embora fraco.')
numbered('SS, a*/b*, Hue, b*: sinal fraco mas real em O3 - candidatos a aprofundar com mais frutos antes de '
         'qualquer recomendacao pratica.')
numbered('Diameter, MF, C/D (calibracao direta), a*, Chroma, Firmness, pH, AT, SS/AT: nenhuma posicao testada '
         'oferece calibracao NIRS confiavel com este n=21. R2cv alto nessas variaveis em qualquer posicao '
         'deve ser tratado como artefato de confundimento varietal, nao como modelo utilizavel.')
numbered('Evitar O2 como posicao de captura unica - e a mais contaminada por identidade varietal de todas.')
numbered('Fruto THR4: outlier recorrente em O1/O2 (menos extremo em O3); confirmar na base de origem antes '
         'de qualquer reajuste dos modelos com sinal real (L*, Vit. C).')
numbered('Limitacao central a repetir em qualquer publicacao: n=21 frutos (7 por cultivar) e pequeno para '
         'PLSR com milhares de bandas - todos os achados "reais" aqui sao indicios de viabilidade, nao '
         'modelos prontos para uso; validacao com mais frutos e, idealmente, mais safras/cultivares e '
         'necessaria antes de qualquer aplicacao pratica.')

doc.add_page_break()
heading('Anexo A - Explicacao linha a linha do script (analise_posicao.R)')

heading('Cabecalho e configuracao (linhas 41-72)', level=2)
bullet('L41-44: carrega os pacotes necessarios (readxl le .xlsx, stringr faz regex, prospectr tem '
       'SNV/derivada/detrend, pls faz a regressao PLS, ggplot2 plota). suppressMessages({...}) so esconde '
       'as mensagens de "pacote carregado" que cada library() imprime.')
bullet('L46 set.seed(1): trava a semente do gerador aleatorio do R. Como o teste de permutacao (linha 265) '
       'embaralha dados aleatoriamente, sem isso cada execucao do script daria um p_perm ligeiramente '
       'diferente; com a semente fixa, o resultado e sempre reprodutivel.')
bullet('L47: desliga o processamento paralelo do pacote pls (evita travamentos no Windows, segundo o '
       'comentario).')
bullet('L50 commandArgs(trailingOnly=TRUE)[1]: pega o primeiro argumento digitado depois do nome do script '
       '(o "O3" de Rscript analise_posicao.R O3).')
bullet('L51: se voce rodar sem argumento nenhum, POS fica NA, e essa linha define "O1" como padrao.')
bullet('L54-60: ABAS e um vetor nomeado - um "dicionario" que traduz o codigo curto ("O3") para o nome exato '
       'da aba no Excel ("O3 (stem-end to the right)"), ja que os nomes das abas sao longos.')
bullet('L61 stopifnot(...): se voce digitar um codigo invalido (ex.: "O5"), o script para na hora com erro '
       'claro, em vez de falhar mais adiante de forma confusa.')
bullet('L65 ABA_ESP <- ABAS[[POS]]: busca no dicionario o nome real da aba.')
bullet('L66-67: monta o nome da pasta de saida (resultados_O3) e cria essa pasta (showWarnings=FALSE evita '
       'aviso se ela ja existir).')
bullet('L68-70: tres constantes do estudo - faixa espectral a manter (corta pontas ruidosas), numero de '
       'permutacoes (99) e numero maximo de variaveis latentes do PLS (6).')
bullet('L72: imprime no console qual posicao esta rodando.')

heading('Secao 1 - Importacao e montagem dos dados (linhas 80-127)', level=2)
bullet('L80: le a aba de espectros como uma tabela (esp).')
bullet('L81 wl_all <- esp[[1]]: a 1a coluna da aba e o eixo de comprimentos de onda (400, 400,5, 401...); '
       'vira um vetor simples.')
bullet('L82 t(as.matrix(esp[, -1])): pega todas as colunas menos a 1a (os espectros de cada fruto), '
       'converte para matriz numerica e TRANSPOE: na planilha as linhas eram comprimento de onda e as '
       'colunas eram frutos; depois de t() fica frutos nas linhas, bandas nas colunas - formato exigido '
       'para modelar.')
bullet('L83: apos transpor, os nomes das colunas do Excel (codigos dos espectros, ex. "TIR1O1") viram nomes '
       'das linhas da matriz; rownames() extrai esses codigos.')
bullet('L89 str_match(cod, "^(T[IHS])R([0-9])"): expressao regular - ^ = inicio da string; T[IHS] casa '
       'literalmente "TI", "TH" ou "TS"; R([0-9]) casa "R" seguido de um digito, capturado entre parenteses. '
       'str_match devolve uma matriz com a correspondencia inteira na coluna 1 e cada grupo capturado nas '
       'colunas seguintes. Funciona mesmo em codigos sem sufixo de posicao (ex. "THR7"), pois so olha o '
       'prefixo.')
bullet('L90: reconstroi o ID limpo do fruto ("TIR1") juntando cultivar + "R" + digito capturados, '
       'descartando qualquer sufixo tipo "O3".')
bullet('L91 factor(m[,2]): transforma as letras do cultivar (TI/TH/TS) em variavel categorica (fator) do R, '
       'usada depois como grp em r_within/loco.')
bullet('L92: checagem dupla - nenhum codigo falhou no regex (!anyNA), e existem exatamente 21 frutos '
       'distintos.')
bullet('L95-96: le a aba de analise destrutiva e remove linhas em branco no rodape (comum em planilhas '
       'Excel).')
bullet('L99-103: dois vetores paralelos - traits = nomes exatos das 16 colunas no Excel (com '
       'acentos/simbolos como "a*/b*"); sig = siglas curtas e "seguras" em R (sem */,) usadas no resto do '
       'codigo.')
bullet('L106: confere que as 16 colunas realmente existem na aba - pega erro de digitacao/coluna renomeada '
       'na hora.')
bullet('L112 lapply(traits, function(nm) as.numeric(dest[[nm]])): percorre as 16 caracteristicas, pega cada '
       'coluna por nome (dest[[nm]]), forca para numerico (caso o Excel tenha guardado como texto) e junta '
       'as 16 colunas resultantes num novo data frame Y. Acessar por nome individualmente evita a '
       'corrupcao de colunas Hue/Chroma que ocorria ao fazer dest[traits] de uma vez (nomes com */, '
       'confundiam o subset).')
bullet('L113: renomeia as colunas de Y para as siglas curtas.')
bullet('L114: imprime quantos NA (faltantes) cada caracteristica tem - diagnostico rapido.')
bullet('L117: monta a chave de juncao do lado da referencia - Treatments ("TI") + Repetition (ja vem como '
       '"R1", "R2"...) = "TIR1", igual ao ID do espectro.')
bullet('L118 match(Fruit, ykey): para cada espectro, acha a posicao (linha) correspondente em dest.')
bullet('L119: reordena Y segundo esse casamento, para que a linha i de Ymat seja do mesmo fruto que a linha '
       'i da matriz espectral.')
bullet('L120: confere que todo espectro achou par (!anyNA(ord)) e que sobraram os 21 frutos.')
bullet('L123-125: keep marca quais bandas ficam entre 450-2450 nm; wl e X sao recortados para manter so '
       'essa faixa.')
bullet('L126-127: imprime as dimensoes finais da matriz.')

heading('Secao 2 - Pre-processamentos espectrais (linhas 136-144)', level=2)
bullet('L136 W <- 15: largura da janela do filtro Savitzky-Golay (precisa ser numero impar de pontos).')
bullet('L137-143: Xp e uma lista com 5 versoes da mesma matriz espectral - raw (sem tratamento); SNV '
       '(standardNormalVariate: para cada espectro/linha, subtrai sua propria media e divide pelo seu '
       'proprio desvio-padrao, removendo diferencas de nivel/escala entre frutos); SNV_D1 (SNV + 1a '
       'derivada via Savitzky-Golay, m=1 ordem da derivada, p=2 grau do polinomio local, w=W tamanho da '
       'janela - realca inclinacoes); SNV_D2 (2a derivada, m=2 - realca picos/curvatura); detrend (ajusta '
       'uma curva quadratica ao longo do eixo de comprimento de onda de cada espectro bruto e a subtrai).')
bullet('L144: garante que todos os 5 elementos da lista sejam matrizes de verdade (algumas funcoes do '
       'prospectr devolvem outro tipo de objeto).')

heading('Secao 3 - Funcoes de apoio: o coracao da metodologia (linhas 158-224)', level=2)
bold_para('metrics(y, yhat) (L158-164): ', 'recebe observados e preditos e devolve uma linha com 6 numeros - '
          'press = soma dos erros2 (Prediction Error Sum of Squares); tss = soma dos desvios2 em torno da '
          'media de y; rmse = raiz do erro quadratico medio; R2cv = 1 - press/tss (1=perfeito, 0="tao bom '
          'quanto chutar a media", negativo="pior que chutar a media"); RPD = sd(y)/rmse (criterio de '
          'Williams); RPIQ = IQR(y)/rmse (robusto a outliers); bias = mean(yhat-y); slope = inclinacao de '
          'lm(y~yhat) (ideal = 1).')
bold_para('loo_all_nlv() (L174-185): ', 'L175 nunca deixa usar mais variaveis latentes que n-3; L176 '
          'pre-aloca matriz 21x6 para as predicoes; L177-183 for fruto a fruto - tr = os outros 20 '
          '(setdiff); plsr(y~X, ncomp=nlv_max, data=data.frame(y=y[tr], X=I(Xm[tr,]))) treina o PLS (o '
          'I(...) diz ao R "trate essa matriz inteira como um unico preditor"); ncomp=nlv_max calcula de 1 '
          'a 6 componentes de uma vez; predict() preve o fruto i para todos os nLV; pr[1,1,] extrai esse '
          'vetor de um array 3D e guarda na linha i. Devolve uma matriz 21x6.')
bold_para('loo_fixed() (L189-197): ', 'igual, mas com um numero fixo de LV (nao testa 1 a 6). Usada no '
          'teste de permutacao porque roda ~100x mais rapido que refazer o loo_all_nlv completo a cada '
          'embaralhamento.')
bold_para('within_cultivar_r() (L204-207): ', 'ave(y, grp) calcula a media de y dentro de cada grupo e '
          'devolve um vetor do mesmo tamanho de y (cada fruto recebe a media do seu proprio cultivar, '
          'repetida). y - ave(y,grp) deixa so o desvio de cada fruto em relacao a media do seu tipo. Mesma '
          'coisa e feita com yhat. cor(yr, pr) correlaciona os dois residuos; suppressWarnings so esconde '
          'o aviso de "desvio-padrao zero".')
bold_para('loco() (L212-220): ', 'for (g in levels(grp)) - um laco por cultivar (3 rodadas); te=which(grp=='
          'g) sao os 7 frutos daquele cultivar (teste), tr=which(grp!=g) os outros 14 (treino); treina so '
          'nos 14, prediz os 7 nunca vistos, guarda em yh[te]. Ao final, calcula o mesmo R2 de sempre, mas '
          'agora toda predicao veio de um modelo que nunca tinha visto nenhum fruto daquele cultivar.')
bold_para('williams() (L223-224): ', 'ifelse aninhado que transforma o numero do RPD em rotulo texto '
          '("excelente"/"bom"/"razoavel"/"fraco"), seguindo os limiares classicos da literatura de '
          'calibracao NIRS (Williams, 2001).')

heading('Secao 4 - Laco principal, 16 caracteristicas (linhas 229-282)', level=2)
bullet('L229: duas listas vazias que vao acumular o resumo de cada caracteristica e as predicoes '
       'fruto-a-fruto.')
bullet('L231 for (s in sig): percorre as 16 siglas.')
bullet('L232: pega o vetor de 21 valores de referencia daquela caracteristica.')
bullet('L233-237: se houver NA nessa caracteristica, avisa quais linhas e pula para a proxima com next.')
bullet('L242 for (pp in names(Xp)): testa os 5 pre-processamentos - L243 roda o LOO completo (todos os '
       'nLV); L244 sweep(P,1,y) subtrai y de cada coluna de P dando o erro de cada fruto em cada nLV, e '
       'colMeans da um RMSECV por numero de componentes; L245 which.min(rmsecv) escolhe o melhor nLV para '
       'este pre-proc; L246-248 calcula as metricas completas nesse ponto, etiqueta com pre-proc/nLV e '
       'r_within; L249 empilha a linha em tab.')
bullet('L251-252: ordena as 5 linhas por R2cv decrescente e salva o grid completo em CSV '
       '(grid_<caracteristica>.csv) - a "prestacao de contas" do processo de escolha.')
bullet('L255: pega a 1a linha (a vencedora) como best.')
bullet('L258: recalcula as predicoes LOO com esse (pre-proc, nLV) fixo vencedor - usadas no grafico e no '
       'teste de permutacao.')
bullet('L259: recalcula o R2 observado manualmente, para comparar com a distribuicao nula a seguir.')
bullet('L264-268 replicate(N_PERM, {...}): roda o bloco 99 vezes - sample(y) embaralha os 21 valores '
       '(quebra qualquer ligacao real com o espectro); refaz a LOO com esse alvo embaralhado; calcula o R2 '
       '"de mentira" alcancado. replicate junta os 99 resultados em r2_null.')
bullet('L269 p_perm = (1 + soma(nulo >= real)) / (1 + 99): conta quantas vezes o acaso empatou ou superou o '
       'resultado real; o "+1" e uma correcao estatistica padrao para nunca dar exatamente zero.')
bullet('L272: calcula o R2_loco do modelo vencedor.')
bullet('L275-277: anexa p_perm, R2_loco e o rotulo Williams a linha best; guarda essa linha final em res; '
       'guarda tambem as 21 predicoes individuais (observado x predito, com fruto e cultivar) em '
       'pred_best, usadas depois no grafico.')
bullet('L279-281: imprime uma linha-resumo formatada no console, para acompanhar o progresso em tempo real '
       '- e exatamente essa linha que aparece no terminal quando o script roda.')

heading('Depois do laco e Secao 5 - tabela final e graficos (linhas 285-347)', level=2)
bullet('L285 do.call(rbind, res): empilha todas as linhas-resumo (uma por caracteristica) num unico data '
       'frame.')
bullet('L286: ordena por R2cv decrescente.')
bullet('L287: sapply(master, is.numeric) acha quais colunas sao numericas; lapply(..., round, 3) arredonda '
       'so essas para 3 casas decimais.')
bullet('L288: salva a tabela mestra em CSV (ex.: resumo_O3.csv).')
bullet('L290-291: imprime a tabela no console, so com as colunas relevantes - e essa tabela que aparece no '
       'topo de cada RESULTADOS_O{n}.md.')
bullet('L296: empilha as predicoes fruto-a-fruto de todas as 16 caracteristicas num unico data frame '
       'comprido.')
bullet('L297 saveRDS(...): grava um arquivo binario do R com a tabela mestra + as predicoes, para reabrir '
       'depois sem rodar tudo de novo.')
bullet('L299: define uma cor fixa por cultivar (paleta segura para daltonismo), usada em todos os graficos.')
bullet('L300: meia-janela do filtro Savitzky-Golay - necessaria porque a derivada "come" pontos das duas '
       'pontas do espectro.')
bullet('5a (L303-317), dentro de try({...}): abre um PNG, arruma um grid 2x2, e desenha espectros brutos, '
       'SNV, SNV+1a derivada (cada linha = 1 fruto, colorida por cultivar), e um 4o painel so com a '
       'legenda; fecha o arquivo.')
bullet('5b (L321-331): prcomp(...) roda a Analise de Componentes Principais sobre os espectros SNV - reduz '
       'milhares de bandas correlacionadas a poucas "direcoes de maxima variancia"; plota PC1xPC2 coloridos '
       'por cultivar, rotula cada ponto com o ID do fruto - mostra visualmente se os cultivares se separam '
       'sozinhos no espaco espectral (diagnostico do confundimento).')
bullet('5c (L335-345): pega as 6 caracteristicas de maior R2cv; monta um ggplot com uma linha tracejada de '
       '"predicao perfeita", pontos observado x predito coloridos por cultivar, um painel por '
       'caracteristica com escalas livres; salva em PNG.')
bullet('L347: mensagem final indicando onde os arquivos foram salvos.')

doc.add_page_break()
heading('Anexo B - Codigo R completo (analise_posicao.R)')
para('Script usado para gerar as 5 analises (O1, O2, O3, O4, media). Referenciado nas Secoes 0 e Anexo A '
     '(funcoes metrics(), loo_all_nlv(), loo_fixed(), within_cultivar_r(), loco()).')
with open('analise_posicao.R', 'r', encoding='utf-8') as f:
    code_block(f.read())

out = 'RESULTADOS_CONSOLIDADO.docx'
doc.save(out)
print('Salvo:', out, f'({os.path.getsize(out)/1024:.0f} KB)')
