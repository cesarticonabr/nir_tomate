"""Gera METODOLOGIA_R_P2.docx - recomendacao de analises em R para predicao
das 16 caracteristicas do bloco P2 por NIRS."""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

doc = Document()

for _ in range(5):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run('Recomendacao de Analises em R'); r.bold = True
r.font.size = Pt(24); r.font.color.rgb = RGBColor(0, 51, 102)
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run('Predicao de 16 caracteristicas do tomate por espectroscopia NIR - Bloco P2')
r.font.size = Pt(13); r.font.color.rgb = RGBColor(80, 80, 80)
d = doc.add_paragraph(); d.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = d.add_run('Documento metodologico - Setembro de 2026')
r.font.size = Pt(11); r.font.color.rgb = RGBColor(120, 120, 120)
doc.add_page_break()


def heading(text, level=1):
    doc.add_heading(text, level=level)


def para(text):
    doc.add_paragraph(text)


def bold_para(prefix, rest=''):
    p = doc.add_paragraph()
    p.add_run(prefix).bold = True
    if rest:
        p.add_run(rest)


def bullet(text):
    doc.add_paragraph(text, style='List Bullet')


def numbered(text):
    doc.add_paragraph(text, style='List Number')


def table(headers, rows):
    tb = doc.add_table(rows=len(rows) + 1, cols=len(headers), style='Light Shading Accent 1')
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        tb.cell(0, j).text = h
        for pp in tb.cell(0, j).paragraphs:
            for rr in pp.runs:
                rr.bold = True
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            tb.cell(i + 1, j).text = str(val)
    doc.add_paragraph('')


bold_para('Status de execucao (Setembro de 2026): ',
          'as recomendacoes centrais deste documento - Secoes 4, 6, 7.2, 8.1 e 9 (LOFO, dentro-de-cultivar, '
          'leave-one-cultivar-out, teste de permutacao) - foram executadas para as 5 estrategias de '
          'orientacao (O1, O2, O3, O4 e a media das 4), nos scripts analise_posicao.R e, como teste de '
          'robustez adicional (Secao 9.1, nao prevista na versao original deste documento), '
          'analise_centrado.R. Os resultados completos estao em RESULTADOS_CONSOLIDADO.md (e nos relatorios '
          'individuais RESULTADOS_O1-O4.md/RESULTADOS_mean.md). A Secao 11 foi atualizada com os resultados '
          'reais, comparados as expectativas originais. O toolkit efetivamente usado foi mais enxuto que o '
          'recomendado na Secao 3: readxl, dplyr, stringr, tidyr, prospectr, pls e ggplot2 - PLSR com '
          'validacao LOO + LOCO + permutacao ja respondeu a pergunta de viabilidade sem necessidade de '
          'glmnet, mdatools, caret, vegan, lme4, plsVarSel ou factoextra.')
doc.add_page_break()

heading('1. Dados e desenho experimental')
para('Fonte: Capturas_tomate_NIRS_11agosto (1).xlsx')
table(['Aba', 'Conteudo', 'Dimensao'], [
    ('O1 (stem-end view)', 'Espectros orientacao 1 - vertical, regiao basal exposta', '4200 x 21'),
    ('O2 (blossom-end view)', 'Espectros orientacao 2 - vertical, regiao apical exposta', '4200 x 21'),
    ('O3 (stem-end to the right)', 'Espectros orientacao 3 - horizontal, base -> apice', '4200 x 21'),
    ('O4 (stem-end to the left)', 'Espectros orientacao 4 - horizontal, apice -> base', '4200 x 21'),
    ('T_P2', '84 espectros concatenados - colunas T{I|H|S}R{1..7}O{1..4}', '4200 x 84'),
    ('Analise_destrutiva_P2', 'Valores de referencia por fruto', '21 x 16'),
])
para('Espectros: reflectancia, 400-2500 nm, passo 0,5 nm -> 4200 comprimentos de onda.')
bold_para('Unidade amostral: ', 'cada linha de Analise_destrutiva_P2 = um fruto individual, '
          'escaneado nas 4 orientacoes e submetido a analise destrutiva.')
bullet('21 frutos independentes (3 cultivares x 7 frutos): Italiano (TI), Holandes (TH), Salada (TS)')
bullet('84 espectros (21 frutos x 4 orientacoes)')
bullet('16 caracteristicas de referencia por fruto')
para('Chave de juncao espectro <-> referencia: Treatments (TI/TH/TS) + Repetition (R1-R7).')

heading('As 16 caracteristicas', level=2)
table(['#', 'Coluna na planilha', 'Grupo', 'Sigla'], [
    (1, 'Fruit length', 'Morfologia', 'Length'),
    (2, 'Fruit diameter', 'Morfologia', 'Diameter'),
    (3, 'C/D', 'Morfologia', 'C_D'),
    (4, 'MF (massa fresca)', 'Morfologia', 'MF'),
    (5, 'L*', 'Cor CIELab', 'L'),
    (6, 'a*', 'Cor CIELab', 'a'),
    (7, 'b*', 'Cor CIELab', 'b'),
    (8, 'a*/b*', 'Cor CIELab', 'a_b'),
    (9, 'Hue', 'Cor CIELab', 'Hue'),
    (10, 'Chroma', 'Cor CIELab', 'Chroma'),
    (11, 'Firmness', 'Qualidade', 'Firmness'),
    (12, 'pH', 'Qualidade', 'pH'),
    (13, 'Vit. C', 'Qualidade', 'VitC'),
    (14, 'Total soluble solids', 'Qualidade', 'SS'),
    (15, 'Titratable acidity', 'Qualidade', 'AT'),
    (16, 'SS/AT ratio', 'Qualidade', 'SS_AT'),
])

heading('2. Desafios estatisticos (ler antes de modelar)')
bold_para('1. n pequeno, p enorme. ', '21 amostras independentes contra 4200 preditores. E um estudo de '
          'viabilidade / prova de conceito, nao uma calibracao pronta. Toda metrica deve vir de validacao '
          'cruzada, acompanhada de teste de permutacao.')
bold_para('2. Confundimento com o cultivar. ', 'Os 3 tipos diferem drasticamente em formato, massa e cor. '
          'Um modelo pode acertar so por reconhecer o cultivar pelo espectro e chutar a media do grupo - '
          'isso nao e calibracao quimica genuina. Reportar desempenho global E dentro de cultivar, mais '
          'teste leave-one-cultivar-out.')
bold_para('3. Quatro espectros por fruto sao pseudo-replicas. ', 'Se ficarem divididos entre treino e teste, '
          'o R2 infla (falsa replicacao). A validacao cruzada deve ser agrupada por fruto.')
bold_para('4. Faixas espectrais ruidosas. ', 'Extremidades (<450 nm e >2450 nm) e emenda de detector '
          '(~1000 nm) tem baixa relacao sinal/ruido. Aparar antes de modelar, com a mascara documentada.')
bold_para('16 alvos -> 16 modelos. ', 'Mesmo protocolo para as 16 caracteristicas, consolidado numa tabela unica.')

heading('3. Ambiente R e pacotes')
table(['Etapa', 'Pacotes'], [
    ('Leitura / manipulacao', 'readxl, dplyr, tidyr, stringr, tibble'),
    ('Pre-processamento espectral', 'prospectr (SNV, MSC, savitzkyGolay, gapDer, detrend)'),
    ('PLS e quimiometria', 'pls (plsr, mvr), mdatools (PLS, PCA, Hotelling T2/Q, VIP, PLS-DA)'),
    ('Reamostragem / CV', 'caret ou rsample/tidymodels (grupos, repeticoes)'),
    ('Regularizacao / selecao de lambda', 'glmnet (LASSO, Elastic Net)'),
    ('Selecao de variaveis PLS', 'plsVarSel (iPLS, VIP, GA-PLS), mdatools (VIP, selratio)'),
    ('Efeito da orientacao', 'vegan (adonis2 - PERMANOVA), lme4/lmerTest (modelo misto)'),
    ('PCA auxiliar / graficos', 'factoextra, ggplot2, patchwork'),
    ('Metricas', 'funcao propria (RMSE, R2cv, RPD, RPIQ, bias, slope)'),
])
para('Todos no CRAN: install.packages(c("readxl","dplyr","tidyr","stringr","prospectr","pls",'
     '"mdatools","caret","glmnet","plsVarSel","vegan","lme4","lmerTest","factoextra","ggplot2","patchwork"))')

heading('4. Importacao e montagem da matriz')
numbered('Ler os espectros. Simples: ler a aba T_P2 (84 espectros prontos). Explicito: ler O1-O4 e empilhar.')
numbered('Transpor para o formato quimiometrico: amostras nas linhas, comprimentos de onda nas colunas.')
numbered('Parse do codigo: stringr::str_match(cod, "^T([IHS])R([1-7])O([1-4])$") -> Type, Rep, Orient. '
         'Criar Fruit = paste0(Type, Rep) - identificador do fruto = grupo de CV.')
numbered('Ler Analise_destrutiva_P2. Remover linhas vazias do rodape; as.numeric nas 16 colunas; '
         'renomear para as siglas; criar Fruit a partir de Treatments + Repetition.')
numbered('Juntar por Fruit (dplyr::left_join). Guardar a matriz espectral como coluna-matriz spc '
         '(convencao pls/prospectr): dados$spc <- I(X).')
numbered('Vetor de wavelengths wl <- as.numeric(colnames(X)) para graficos e recortes.')

heading('5. Controle de qualidade espectral e exploracao')
numbered('Grafico dos espectros brutos (matplot / ggplot geom_line, alpha baixo), por cultivar e por orientacao.')
numbered('Recorte de faixas ruidosas: manter ~450-2450 nm; inspecionar a 2a derivada; registrar a mascara.')
numbered('PCA (prcomp / mdatools::pca) sobre espectros pre-processados: scree plot; scores PC1xPC2xPC3 '
         'coloridos por cultivar e por orientacao; outliers por Hotelling T2 e residuos Q; Mahalanobis nos scores.')
numbered('Agrupamento (hclust sobre distancia euclidiana dos scores) - espera-se agrupamento forte por cultivar.')

heading('6. Pre-processamento espectral (comparar, nao escolher a priori)')
para('Testar um grid pequeno com prospectr e escolher, por caracteristica, o de menor RMSECV:')
table(['Pipeline', 'Funcao prospectr'], [
    ('Sem pre-processamento (apenas centrado)', '-'),
    ('SNV', 'standardNormalVariate()'),
    ('MSC', 'msc()'),
    ('Savitzky-Golay suavizacao', 'savitzkyGolay(w=11-21, p=2, m=0)'),
    ('SNV + SG 1a derivada', 'savitzkyGolay(..., m=1) apos SNV'),
    ('SNV + SG 2a derivada', 'savitzkyGolay(..., m=2) apos SNV'),
    ('Detrend', 'detrend()'),
    ('Normalizacao por area', 'dividir cada espectro pela norma L1/L2'),
])
para('Saida: tabela "caracteristica x melhor pre-processamento x RMSECV x n LV". '
     'A centragem/escala final deve ser ajustada dentro de cada fold de treino (evita vazamento).')
para('Quando se usar o espectro medio das orientacoes (recomendacao da Secao 7.3), aplicar SNV/MSC a cada '
     'orientacao individualmente ANTES de mediar, e nao depois.')

heading('7. Questao das 4 orientacoes (analise distintiva deste estudo)')
heading('7.1 A orientacao afeta o espectro?', level=2)
bullet('PERMANOVA (vegan::adonis2) sobre a matriz espectral pre-processada, distancia euclidiana: '
       'adonis2(spc ~ Type + Orient, strata = Fruit, permutations = 999). Quantifica o R2 de Orient '
       'depois de descontar Type, respeitando os blocos (fruto).')
bullet('Modelo misto sobre os primeiros scores de PCA: lmer(PC1 ~ Orient + (1|Fruit)) (idem PC2, PC3), '
       'com lmerTest. Estima a fracao da variancia espectral devida a orientacao vs. fruto.')
bullet('Interpretacao: se Orient explica variancia desprezivel -> usar qualquer orientacao ou a media. '
       'Se explica variancia relevante -> a escolha da orientacao importa para a calibracao.')
heading('7.2 Qual estrategia de captura calibra melhor?', level=2)
para('Rodar o mesmo protocolo de CV para 4 formas de usar os espectros, em cada caracteristica:')
table(['Estrategia', 'Matriz X', 'n'], [
    ('1. Uma orientacao por vez', 'so O1; so O2; so O3; so O4', '21'),
    ('2. Espectro medio das orientacoes', 'media por fruto', '21'),
    ('3. Empilhamento (orientacao como pseudo-replica)', '84 espectros, CV agrupada por fruto', '84 / 21 grupos'),
    ('4. Concatenacao (fusao de dados)', 'vetor de 4 x p por fruto', '21'),
])
para('Saida: tabela "caracteristica x estrategia x R2cv x RMSECV x RPD/RPIQ" e uma recomendacao pratica '
     'de protocolo de escaneamento.')

heading('7.3 Recomendacao: media das orientacoes como padrao - apos QC e pre-processamento individual', level=2)
bold_para('Para os modelos finais de calibracao, recomenda-se o espectro medio por fruto ',
          '(estrategia 2), nao o empilhamento dos 84 espectros. Motivos:')
bullet('Reduz o ruido de medicao em ~raiz(k) (k = n de orientacoes mediadas; raiz(4) = 2x) -> tende a '
       'melhorar R2cv e RMSECV.')
bullet('Casa com a referencia: as 16 caracteristicas foram medidas no fruto inteiro, nao numa posicao; '
       'o espectro medio do fruto e o alvo conceitualmente correto.')
bullet('Elimina a pseudo-replicacao: 21 espectros <-> 21 valores; dispensa a CV agrupada (embora n=21 '
       'continue pequeno). O empilhamento serve para estudar o efeito da orientacao (7.1), nao para os '
       'modelos finais.')
bold_para('Porem, a media nao deve ser aplicada as cegas. ', 'As 4 capturas sao vistas deliberadamente '
          'diferentes (basal vertical, apical vertical, 2 horizontais), nao 4 replicas do mesmo ponto. Na aba '
          'O2 (blossom-end view) a reflectancia chega a ~1,1 enquanto O1/O3/O4 ficam em 0,3-0,6 - valores de '
          'reflectancia acima de 1 sao fisicamente suspeitos (reflexao especular, saturacao ou referencia '
          'diferente). Se uma orientacao for sistematicamente aberrante, a media e puxada para o artefato.')
para('Procedimento recomendado (nesta ordem):')
numbered('QC por orientacao (Secao 5): plotar os 4 grupos sobrepostos; PCA com scores coloridos por Orient; '
         'PERMANOVA da Secao 7.1. Verificar se O2 (ou outra) se destaca sistematicamente.')
numbered('Definir o conjunto que entra na media: as 4 orientacoes, ou apenas o subconjunto consistente '
         '(ex.: excluir O2, ou usar so as 2 verticais). Documentar a decisao e a justificativa.')
numbered('Pre-processar cada espectro individualmente antes de mediar: aplicar SNV/MSC a cada uma das k '
         'orientacoes e so entao calcular a media por fruto. Testar tambem "mediar -> pre-processar" e '
         'comparar por RMSECV.')
numbered('Confirmar na validacao: comparar media (do conjunto escolhido) x melhor orientacao isolada x '
         'concatenacao no protocolo da Secao 9. Se a melhor orientacao isolada empatar ou superar a media, '
         'preferir a orientacao isolada (protocolo de escaneamento mais rapido no campo).')

heading('8. Modelos de calibracao - foco em PLS + selecao de variaveis')
heading('8.1 PLSR (metodo principal)', level=2)
bullet('pls::plsr (ou mdatools::pls), 1 a 15 variaveis latentes (LV).')
bullet('Numero de LV pelo minimo de RMSECV com a regra de 1 desvio-padrao (menor n de LV dentro de 1 SE '
       'do minimo) - evita sobreajuste, critico com n=21.')
bullet('Padrao-ouro para NIR: componentes latentes que maximizam a covariancia X-y, lida com p >> n e com '
       'a multicolinearidade entre comprimentos de onda vizinhos, e e interpretavel.')
heading('8.2 LASSO / Elastic Net (regularizacao + selecao esparsa)', level=2)
bullet('glmnet, com alpha em {0,25; 0,5; 0,75; 1}; lambda por CV agrupada.')
bullet('Fornece um conjunto esparso de comprimentos de onda - util para ver se o sinal se concentra em '
       'poucas bandas interpretaveis ou esta difuso (sinal fraco / sobreajuste).')
heading('8.3 Selecao de variaveis e interpretacao quimica', level=2)
bullet('VIP scores e coeficientes de regressao PLS (mdatools::vipscores, plsVarSel) - mapear os '
       'comprimentos de onda influentes.')
bullet('iPLS (plsVarSel::ipls) - selecao por intervalos espectrais.')
bullet('Checagem de plausibilidade: agua/O-H ~1450 e ~1940 nm; acucares (C-H, O-H) ~1200, ~1450, '
       '~1700-1800 nm; carotenoides/licopeno na regiao visivel ~470-550 nm (relevante para a*, Chroma, Hue). '
       'Se o modelo "bom" se apoiar em regioes sem sentido -> suspeitar de confundimento/sobreajuste.')
heading('8.4 Metodos nao-lineares - deliberadamente fora', level=2)
para('Random Forest, SVM e redes nao sao recomendados aqui: com n=21 o risco de sobreajuste e alto e, no '
     'estudo anterior (n=9), nao superaram o PLS. Reconsiderar quando o n aumentar.')

heading('9. Estrategia de validacao (critica com n=21)')
table(['Esquema', 'Como', 'Para que'], [
    ('Leave-one-fruit-out (LOFO)', '21 folds sobre o espectro medio por fruto (n=21)',
     'Esquema principal para os modelos finais (Secao 7.3)'),
    ('k-fold agrupado por fruto, repetido', '5 folds x 20 repeticoes, grupo = Fruit, sementes distintas',
     'So quando se modela com os 84 espectros empilhados; distribuicao das metricas'),
    ('Leave-one-cultivar-out', '3 folds: treina em 2 cultivares, prediz o 3o',
     'Testa generalizacao alem da identidade varietal'),
    ('Desempenho dentro de cultivar', 'remover a media de cada cultivar de y e das predicoes; recalcular r / RMSE',
     'O espectro explica a variacao fruto-a-fruto alem do cultivar?'),
    ('Teste de permutacao (y-randomization)', '500-1000 permutacoes de y; refazer toda a CV',
     'O R2cv real deve cair fora da distribuicao nula'),
])
bold_para('Regra anti-vazamento: ', 'centragem, escala, escolha do pre-processamento, selecao de variaveis, '
          'n de LV e lambda do glmnet devem ser refeitos dentro de cada fold de treino. Encapsular o pipeline '
          '(caret::train com preProcess + index de grupos, ou uma recipe do tidymodels com group_vfold_cv).')

heading('9.1 Centralizacao por cultivar - teste de robustez adicional (implementado)', level=2)
para('Nao prevista na versao original deste documento; adicionada apos a analise inicial, como resposta a '
     'pergunta "sem considerar o cultivar, a predicao melhoraria?". Implementada em analise_centrado.R.')
bold_para('Ideia: ', 'no PLSR padrao (Secao 8.1), os 21 frutos entram misturados no ajuste. Como o cultivar '
          'explica boa parte da variancia de X e de y, e possivel que as poucas variaveis latentes '
          'disponiveis sejam "gastas" discriminando cultivar, sobrando pouca capacidade para a variacao '
          'real de composicao DENTRO de cada tipo. A variante centrada remove a media de cada cultivar de X '
          'e de y ANTES de ajustar o PLS (nao so depois, como ja faz o teste "dentro de cultivar" da tabela '
          'acima), forcando o modelo a resolver so a variacao intra-cultivar. A media de cada grupo usada '
          'para centralizar o treino e o fruto de teste e sempre recalculada so com os frutos de treino '
          '(nunca inclui o proprio fruto predito), para nao vazar informacao.')
bold_para('Resultado (as 5 posicoes, 16 caracteristicas): ', 'a centralizacao NAO melhora a predicao real - '
          'na maioria dos casos PIORA. Com so 6-7 frutos por cultivar para treinar a parte residual, o '
          'modelo overfita: o teste de generalizacao (R2_loco_c) despenca a valores catastroficos em varios '
          'casos (ex.: Firmness em O2 = -77,8; SS/AT em O2 = -79,7), muito piores que o R2_loco do modelo '
          'agrupado. A tecnica nao aumenta o n - so remove variancia - e com p >> n isso favorece ruido, '
          'nao sinal.')
bold_para('Uso que se revelou valido: ', 'como checagem de robustez dos achados ja identificados no modelo '
          'agrupado. Sob esse teste mais rigoroso, L* em O3 manteve o sinal quase intacto (r_within '
          '+0,82->+0,77; R2_loco->R2_loco_c +0,80->+0,79), reforcando que e o achado mais solido de toda a '
          'analise. Ja Fruit length na media, o melhor resultado por R2cv/RPD do modelo agrupado, '
          'enfraqueceu bastante (r_within +0,68->+0,43; R2_loco +0,56->R2_loco_c -0,39), sugerindo que parte '
          'da sua forca dependia de compartilhar informacao entre cultivares no ajuste conjunto. Detalhes '
          'completos em RESULTADOS_CONSOLIDADO.md.')

heading('10. Metricas e interpretacao')
table(['Metrica', 'Definicao', 'Uso'], [
    ('R2cv', '1 - SQres/SQtot na validacao', 'variancia explicada fora da amostra'),
    ('RMSECV', 'raiz do erro quadratico medio na CV', 'erro na unidade do alvo'),
    ('RPD', 'SD(y) / RMSECV', 'Relacao de Desempenho Residual (Williams)'),
    ('RPIQ', 'IQR(y) / RMSECV', 'robusta a nao-normalidade - preferir ao RPD com n pequeno'),
    ('bias', 'media(pred - obs)', 'erro sistematico'),
    ('slope', 'inclinacao de obs ~ pred', '1 = ideal; < 1 indica encolhimento'),
    ('n LV', 'variaveis latentes do modelo final', 'parcimonia'),
])
bold_para('Classificacao de RPD (Williams, 2001): ', '> 2,5 excelente - 2,0-2,5 bom - 1,5-2,0 razoavel - '
          '< 1,5 fraco (nao recomendado para predicao quantitativa).')

heading('11. Expectativas por grupo de caracteristica -> resultados obtidos')
para('Hipoteses originais desta secao, confrontadas com os resultados reais (todas as 5 posicoes, ver '
     'RESULTADOS_CONSOLIDADO.md):')
bold_para('Morfologia (Length, Diameter, C_D, MF): ', 'hipotese CONFIRMADA, sem excecao. R2cv sempre alto '
          '(0,45-0,96 conforme a posicao) mas R2_loco negativo em praticamente todos os casos (de -0,12 a '
          '-29,5) - e discriminacao de cultivar, nao calibracao de composicao. Unica excecao parcial: '
          'Fruit length na media das 4 posicoes chegou a R2_loco +0,56 (real), mas o teste de robustez da '
          'Secao 9.1 mostrou que esse resultado e menos solido do que parece (cai para R2_loco_c -0,39 '
          'quando centralizado por cultivar).')
bold_para('Cor CIELab (L, a, b, a_b, Hue, Chroma): ', 'hipotese PARCIALMENTE confirmada, mas nao como '
          'esperado. a* e Chroma (a aposta inicial, ligada a licopeno/carotenoides) NAO mostraram nenhum '
          'sinal em nenhuma posicao (R2cv sempre negativo). Em vez disso, o sinal real apareceu em L*, '
          'a*/b*, Hue e b* - e SO na posicao O3: L* em O3 e o achado mais forte de toda a analise '
          '(r_within +0,82, R2_loco +0,80), confirmado pelo teste de robustez (Secao 9.1). Nas demais '
          'posicoes (O1, O2, O4, media) o mesmo grupo de cor nao mostrou sinal real.')
bold_para('SS e Firmness: ', 'hipotese REFUTADA. Nenhuma posicao chegou perto do R2 moderado/bom esperado. '
          'Firmness nao teve sinal em nenhuma posicao (R2cv sempre <= 0). SS teve sinal real, mas fraco, so '
          'em O3 (r_within +0,30, R2_loco +0,46) - muito abaixo do R2 ~ 0,75 do estudo anterior.')
bold_para('pH, AT, SS_AT, VitC: ', 'hipotese MAJORITARIAMENTE confirmada, com uma excecao real. pH, AT e '
          'SS/AT nao mostraram sinal real em nenhuma das 5 posicoes (r_within ~ 0 ou R2_loco negativo em '
          'todas). Excecao: Vit. C em O1 - unico caso com r_within e R2_loco ambos positivos (+0,52 / '
          '+0,21), confirmado pelo teste de robustez (Secao 9.1: r_within permanece +0,51 apos centralizar '
          'por cultivar). Em qualquer outra posicao, Vit. C perde o sinal (O2: R2_loco -9,0; O4: -1,15).')
bold_para('Conclusao geral da Secao 11: ', 'de 16 caracteristicas testadas em 5 posicoes (80 combinacoes), '
          'so 6 combinacoes mostraram evidencia de sinal real e nao-espurio (r_within>0 E R2_loco>0): L*, '
          'a*/b*, Hue, b* e SS em O3, e Vit. C em O1. Todas as demais combinacoes com R2cv alto refletem '
          'confundimento varietal, nao calibracao quimica.')

heading('12. Analise complementar - classificacao de cultivar (opcional)')
para('PLS-DA (mdatools::plsda) ou LDA sobre scores de PCA para classificar TI/TH/TS a partir do espectro. '
     'Acuracia (em CV agrupada por fruto) provavelmente alta. Quantifica explicitamente quanta informacao '
     'varietal o espectro carrega - contextualiza e relativiza os R2 altos de morfologia.')

heading('13. Saidas do relatorio final')
numbered('Tabela mestra - 16 caracteristicas x [melhor pre-proc. - n LV - R2cv - RMSECV - RPD - RPIQ - '
         'r dentro-de-cultivar - R2cv leave-one-cultivar-out - p do teste de permutacao - classificacao Williams].')
numbered('Tabela de orientacoes - caracteristica x estrategia (O1/O2/O3/O4/media/empilhado/concatenado) + '
         'recomendacao de protocolo de escaneamento.')
numbered('Resultado da PERMANOVA / modelo misto para o efeito da orientacao.')
numbered('Figuras: espectros brutos e pre-processados; scores de PCA (por cultivar e por orientacao); '
         'VIP/coeficientes dos melhores modelos com bandas quimicas anotadas; observado x predito.')
numbered('Matriz de confusao da PLS-DA de cultivar.')
numbered('Limitacoes e recomendacoes: n=21 -> resultado de viabilidade, nao calibracao final. Amostragem '
         'futura: idealmente >= 40-60 frutos por cultivar, cobrindo faixa ampla de maturacao, para descolar '
         'o sinal quimico do efeito varietal e permitir validacao externa. Padronizar a orientacao de captura '
         'conforme a conclusao da Secao 7.')

output = 'METODOLOGIA_R_P2.docx'
doc.save(output)
print(f'Salvo: {output} ({os.path.getsize(output) / 1024:.0f} KB)')
