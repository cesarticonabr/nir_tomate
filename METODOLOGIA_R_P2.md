# Recomendação de Análises em R — Predição de 16 Características do Tomate por Espectroscopia NIR (Bloco P2)

**Documento metodológico. Setembro de 2026.**

Este documento recomenda, passo a passo, as análises que podem ser feitas **em R** para responder à pergunta:
*os espectros NIR podem ajudar a predizer as 16 características medidas por análise destrutiva no bloco P2?*
Inclui também a análise da questão específica deste desenho: **quatro orientações de captura por fruto**.

> **Status de execução (Setembro de 2026):** as recomendações centrais deste documento — Seções 4, 6, 7.2,
> 8.1 e 9 (LOFO, dentro-de-cultivar, leave-one-cultivar-out, teste de permutação) — **foram executadas** para
> as 5 estratégias de orientação (O1, O2, O3, O4 e a média das 4), nos scripts [`analise_posicao.R`](analise_posicao.R)
> e, como teste de robustez adicional (Seção 9.1, não prevista na versão original deste documento),
> [`analise_centrado.R`](analise_centrado.R). Os resultados completos, com tabelas e interpretação, estão em
> **[RESULTADOS_CONSOLIDADO.md](RESULTADOS_CONSOLIDADO.md)** (e nos relatórios individuais
> `RESULTADOS_O1-O4.md`/`RESULTADOS_mean.md`). A Seção 11 abaixo foi atualizada com os resultados reais,
> comparados às expectativas originais. O toolkit efetivamente usado foi mais enxuto que o recomendado na
> Seção 3: `readxl`, `dplyr`, `stringr`, `tidyr`, `prospectr`, `pls` e `ggplot2` — PLSR com validação
> LOO + LOCO + permutação já respondeu à pergunta de viabilidade sem necessidade de `glmnet`, `mdatools`,
> `caret`, `vegan`, `lme4`, `plsVarSel` ou `factoextra`.

---

## 1. Dados e desenho experimental

**Fonte:** `Capturas_tomate_NIRS_11agosto (1).xlsx`

| Aba | Conteúdo | Dimensão |
|-----|----------|----------|
| `O1 (stem-end view)` | Espectros na orientação 1 (vertical, região basal exposta) | 4200 λ × 21 frutos |
| `O2 (blossom-end view)` | Espectros na orientação 2 (vertical, região apical exposta) | 4200 λ × 21 frutos |
| `O3 (stem-end to the right)` | Espectros na orientação 3 (horizontal, base → ápice) | 4200 λ × 21 frutos |
| `O4 (stem-end to the left)` | Espectros na orientação 4 (horizontal, ápice → base) | 4200 λ × 21 frutos |
| `T_P2` | Os 84 espectros já concatenados; colunas `T{I\|H\|S}R{1..7}O{1..4}` | 4200 λ × 84 |
| `Analise_destrutiva_P2` | Valores de referência por fruto | 21 frutos × 16 variáveis |
| `Estatistica_Descritiva` | Estatística descritiva por cultivar (N = 7 cada) | — |
| `DESCRICAO` | Descrição textual das 4 orientações | — |

**Espectros:** reflectância, 400–2500 nm, passo 0,5 nm → 4200 comprimentos de onda.

**Unidade amostral:** cada linha da aba `Analise_destrutiva_P2` = **um fruto individual**. Cada fruto foi
escaneado nas **4 orientações** e submetido à análise destrutiva. Portanto:

- **21 frutos independentes** (3 cultivares × 7 frutos): Italiano (TI), Holandês (TH), Salada (TS)
- **84 espectros** (21 frutos × 4 orientações)
- **16 características de referência** por fruto

**Chave de junção** espectro ↔ referência: `Treatments` (TI/TH/TS) + `Repetition` (R1–R7).

### As 16 características (colunas numéricas de `Analise_destrutiva_P2`)

| # | Coluna na planilha | Grupo | Sigla sugerida |
|---|--------------------|-------|----------------|
| 1 | Fruit length | Morfologia | `Length` |
| 2 | Fruit diameter | Morfologia | `Diameter` |
| 3 | C/D | Morfologia | `C_D` |
| 4 | MF (massa fresca) | Morfologia | `MF` |
| 5 | L* | Cor CIELab | `L` |
| 6 | a* | Cor CIELab | `a` |
| 7 | b* | Cor CIELab | `b` |
| 8 | a*/b* | Cor CIELab | `a_b` |
| 9 | Hue | Cor CIELab | `Hue` |
| 10 | Chroma | Cor CIELab | `Chroma` |
| 11 | Firmness | Qualidade | `Firmness` |
| 12 | pH | Qualidade | `pH` |
| 13 | Vit. C | Qualidade | `VitC` |
| 14 | Total soluble solids | Qualidade | `SS` |
| 15 | Titratable acidity | Qualidade | `AT` |
| 16 | SS/AT ratio | Qualidade | `SS_AT` |

---

## 2. Desafios estatísticos (ler antes de modelar)

Estes quatro pontos condicionam **todas** as decisões metodológicas a seguir.

1. **n pequeno, p enorme.** São 21 amostras independentes contra 4200 preditores. Isto é um **estudo de
   viabilidade / prova de conceito**, não uma calibração pronta para uso. Nenhuma métrica de qualidade pode
   vir do ajuste — **toda** avaliação deve sair de validação cruzada, e acompanhada de teste de permutação.

2. **Confundimento com o cultivar.** Os 3 tipos de tomate diferem drasticamente em formato, massa e cor
   (Italiano alongado, Holandês pequeno e redondo, Salada grande). Um modelo pode alcançar R² alto apenas
   por **reconhecer o cultivar** pelo espectro e "chutar" a média daquele grupo. Isso **não** é calibração
   química genuína. Para cada característica é obrigatório reportar o desempenho **global** e o desempenho
   **dentro de cultivar**, além de um teste **leave-one-cultivar-out**.

3. **Quatro espectros por fruto são pseudo-réplicas.** Os 4 espectros de um mesmo fruto são altamente
   correlacionados. Se ficarem divididos entre treino e teste, o R² fica artificialmente inflado (falsa
   replicação). **Regra:** a validação cruzada deve ser **agrupada por fruto** — os 4 espectros de um fruto
   ficam sempre juntos, no treino ou no teste.

4. **Faixas espectrais ruidosas.** As extremidades (< 450 nm e > 2450 nm) e a região de emenda de detector
   (~1000 nm em muitos equipamentos NIR/Vis-NIR) costumam ter baixa relação sinal/ruído. Devem ser aparadas
   antes da modelagem, com a máscara documentada.

**16 alvos → 16 modelos.** Aplicar exatamente o mesmo protocolo às 16 características e consolidar tudo em
uma tabela única, comparável.

---

## 3. Ambiente R e pacotes

| Etapa | Pacotes |
|-------|---------|
| Leitura / manipulação | `readxl`, `dplyr`, `tidyr`, `stringr`, `tibble` |
| Pré-processamento espectral | `prospectr` (SNV, MSC, `savitzkyGolay`, `gapDer`, `detrend`, `standardNormalVariate`) |
| PLS e quimiometria | `pls` (`plsr`, `mvr`), `mdatools` (PLS, PCA, Hotelling T²/Q, VIP, PLS-DA) |
| Reamostragem / CV | `caret` **ou** `rsample`/`tidymodels` (grupos, repetições) |
| Regularização / seleção de λ | `glmnet` (LASSO, Elastic Net) |
| Seleção de variáveis PLS | `plsVarSel` (iPLS, VIP, GA-PLS), `mdatools` (VIP, `selratio`) |
| Efeito da orientação | `vegan` (`adonis2` — PERMANOVA), `lme4`/`lmerTest` (modelo misto sobre scores) |
| PCA auxiliar / gráficos | `factoextra`, `ggplot2`, `patchwork` |
| Métricas | função própria (`RMSE`, `R2cv`, `RPD`, `RPIQ`, `bias`, `slope`) |

Instalação: todos estão no CRAN — `install.packages(c("readxl","dplyr","tidyr","stringr","prospectr","pls","mdatools","caret","glmnet","plsVarSel","vegan","lme4","lmerTest","factoextra","ggplot2","patchwork"))`.

---

## 4. Importação e montagem da matriz

1. **Ler os espectros.** Opção simples: ler a aba `T_P2` diretamente (já traz os 84 espectros). Opção
   explícita: ler `O1`–`O4` separadamente e empilhar.
2. **Transpor** para o formato quimiométrico padrão: **amostras nas linhas**, comprimentos de onda nas
   colunas (`t()` sobre o bloco numérico; a 1ª coluna `Wavelength (nm)` vira os nomes das colunas).
3. **Parse do código da amostra** com `stringr::str_match(cod, "^T([IHS])R([1-7])O([1-4])$")` →
   colunas `Type`, `Rep`, `Orient`. Criar `Fruit = paste0(Type, Rep)` (identificador do fruto = **grupo de CV**).
4. **Ler `Analise_destrutiva_P2`.** Remover as linhas vazias no rodapé; converter as 16 colunas para
   numérico (`as.numeric`); renomear para as siglas da tabela da Seção 1; criar `Fruit` a partir de
   `Treatments` + `Repetition`.
5. **Juntar** por `Fruit` (`dplyr::left_join`). Guardar a matriz espectral como **coluna-matriz** `spc`
   dentro do data.frame (convenção de `pls` e `prospectr`): `dados$spc <- I(X)`.
6. **Vetor de wavelengths** `wl <- as.numeric(colnames(X))` para gráficos e recortes.

Resultado: um data.frame de 84 linhas com `Fruit`, `Type`, `Rep`, `Orient`, `spc` (84 × 4200) e as 16
colunas de referência (repetidas nas 4 orientações do mesmo fruto).

---

## 5. Controle de qualidade espectral e exploração

Antes de qualquer modelo:

1. **Gráfico dos espectros brutos** (`matplot` ou `ggplot` + `geom_line`, `alpha` baixo), colorindo (a) por
   cultivar e (b) por orientação. Objetivo: ver formato geral, ruído nas pontas, deslocamentos de linha de
   base, e se a orientação separa visualmente os espectros.
2. **Recorte de faixas ruidosas.** Manter aproximadamente 450–2450 nm. Inspecionar a 2ª derivada para
   localizar regiões de ruído puro (oscilação sem estrutura). Registrar a máscara aplicada (intervalos e
   nº de pontos removidos).
3. **PCA** (`prcomp` ou `mdatools::pca`, sobre os espectros já pré-processados). Analisar:
   - Scree plot e % de variância de PC1–PC5.
   - Scores PC1×PC2 e PC1×PC3, coloridos por **cultivar** e por **orientação** — verificar visualmente se a
     variância de orientação é grande ou pequena frente à de cultivar.
   - **Detecção de outliers:** Hotelling T² e resíduos Q (`mdatools` fornece direto); distância de
     Mahalanobis nos scores. Listar frutos/espectros fora dos limites (95 %/99 %) para reinspeção.
4. **Agrupamento** (`hclust` sobre distância euclidiana dos scores) — espera-se agrupamento forte por
   cultivar; confirma o desafio nº 2.

---

## 6. Pré-processamento espectral (comparar, não escolher a priori)

Testar um **grid pequeno** de pipelines com `prospectr` e escolher, **por característica**, o de menor
RMSECV (na CV agrupada por fruto da Seção 8):

| Pipeline | Função `prospectr` |
|----------|--------------------|
| Sem pré-processamento (apenas centrado) | — |
| SNV | `standardNormalVariate()` |
| MSC | `msc()` |
| Savitzky-Golay suavização | `savitzkyGolay(w = 11–21, p = 2, m = 0)` |
| SNV + SG 1ª derivada | `savitzkyGolay(..., m = 1)` após SNV |
| SNV + SG 2ª derivada | `savitzkyGolay(..., m = 2)` após SNV |
| Detrend | `detrend()` |
| Normalização por área | dividir cada espectro pela sua norma L1/L2 |

Saída: tabela **"característica × melhor pré-processamento × RMSECV × nº LV"**.

> Observação 1: a centragem/escala final (`scale`/autoscaling) deve ser ajustada **dentro** de cada fold de
> treino, nunca no conjunto todo (evita vazamento).
>
> Observação 2: quando se usar o **espectro médio das orientações** (recomendação da Seção 7.3), aplicar
> SNV/MSC a **cada orientação individualmente antes de mediar**, e não depois.

---

## 7. Questão das 4 orientações (análise distintiva deste estudo)

Esta é a contribuição metodológica específica do bloco P2. Duas frentes:

### 7.1 A orientação afeta o espectro?

- **PERMANOVA** (`vegan::adonis2`) sobre a matriz espectral pré-processada, distância euclidiana:
  `adonis2(spc ~ Type + Orient, strata = Fruit, permutations = 999)`. Quantifica o R² atribuível a `Orient`
  depois de descontar `Type`, respeitando a estrutura de blocos (fruto).
- **Modelo misto** sobre os primeiros scores de PCA: `lmer(PC1 ~ Orient + (1|Fruit))` (idem PC2, PC3), com
  `lmerTest` para o teste de `Orient`. Estima a fração da variância espectral devida a orientação vs. fruto.
- Interpretação: se `Orient` explica variância desprezível → pode-se usar qualquer orientação ou a média.
  Se explica variância relevante → a escolha da orientação importa para a calibração.

### 7.2 Qual estratégia de captura calibra melhor?

Rodar **o mesmo protocolo de CV** (Seção 8) para 4 formas de usar os espectros, em cada característica:

| Estratégia | Matriz X | n |
|------------|----------|---|
| 1. Uma orientação por vez | só O1; só O2; só O3; só O4 | 21 |
| 2. Espectro médio das orientações | média por fruto | 21 |
| 3. Empilhamento (orientação como pseudo-réplica) | 84 espectros, CV agrupada por fruto | 84 → 21 grupos |
| 4. Concatenação (fusão de dados) | vetor de 4 × p por fruto | 21 |

Saída: tabela **"característica × estratégia × R²cv × RMSECV × RPD/RPIQ"** e uma **recomendação prática de
protocolo de escaneamento** (a preencher com os resultados).

### 7.3 Recomendação: a média das orientações como padrão — depois de QC e pré-processamento individual

**Para os modelos finais de calibração, recomenda-se o espectro médio por fruto** (estratégia 2), e não o
empilhamento dos 84 espectros. Motivos:

- **Reduz o ruído de medição** em ~√k (k = nº de orientações mediadas; √4 = 2×) → tende a melhorar R²cv e RMSECV.
- **Casa com a referência:** as 16 características foram medidas no **fruto inteiro**, não numa posição; o
  espectro médio do fruto é o alvo conceitualmente correto.
- **Elimina a pseudo-replicação:** fica 21 espectros ↔ 21 valores; dispensa a CV agrupada (embora n = 21
  continue pequeno). O empilhamento dos 84 espectros serve para **estudar** o efeito da orientação (7.1),
  não para os modelos finais.

**Porém, a média não deve ser aplicada às cegas** — as 4 capturas são **vistas deliberadamente diferentes**
(basal vertical, apical vertical, 2 horizontais), não 4 réplicas do mesmo ponto. Na aba `O2 (blossom-end
view)` a reflectância chega a ~1,1 enquanto `O1/O3/O4` ficam em 0,3–0,6 — valores de reflectância acima de 1
são fisicamente suspeitos (reflexão especular, saturação ou referência diferente). Se uma orientação for
sistematicamente aberrante, a média é puxada para o artefato.

**Procedimento recomendado (nesta ordem):**

1. **QC por orientação** (Seção 5): plotar os 4 grupos sobrepostos; PCA com scores coloridos por `Orient`;
   PERMANOVA da Seção 7.1. Verificar se `O2` (ou outra) se destaca sistematicamente.
2. **Definir o conjunto que entra na média:** as 4 orientações, ou apenas o subconjunto consistente
   (ex.: excluir `O2`, ou usar só as 2 verticais). Documentar a decisão e a justificativa.
3. **Pré-processar cada espectro individualmente antes de mediar.** Aplicar SNV/MSC a cada uma das k
   orientações e só então calcular a média por fruto — o espalhamento óptico depende da geometria da
   captura, e corrigi-lo antes remove parte do efeito de orientação. Testar também "mediar → pré-processar"
   e comparar por RMSECV.
4. **Confirmar na validação:** comparar *média (do conjunto escolhido)* × *melhor orientação isolada* ×
   *concatenação* no protocolo da Seção 9. Se a melhor orientação isolada empatar ou superar a média,
   preferir a orientação isolada (protocolo de escaneamento mais rápido no campo).

---

## 8. Modelos de calibração — foco em PLS + seleção de variáveis

Para **cada uma das 16 características**:

### 8.1 PLSR (método principal)

- `pls::plsr` (ou `mdatools::pls`), 1 a 15 variáveis latentes (LV).
- Número de LV escolhido pelo **mínimo de RMSECV** com a **regra de 1 desvio-padrão** (menor nº de LV cujo
  RMSECV esteja dentro de 1 SE do mínimo) — evita sobreajuste, crítico com n = 21.
- Padrão-ouro para NIR: cria componentes latentes que maximizam a covariância X–y, lida com p ≫ n e com a
  multicolinearidade entre comprimentos de onda vizinhos, e é interpretável (coeficientes/loadings).

### 8.2 LASSO / Elastic Net (regularização + seleção esparsa)

- `glmnet`, com α ∈ {0,25; 0,5; 0,75; 1}; λ por CV agrupada.
- Fornece um conjunto **esparso** de comprimentos de onda — útil para checar se o sinal se concentra em
  poucas bandas interpretáveis ou está difuso (sinal fraco / sobreajuste).

### 8.3 Seleção de variáveis e interpretação química

- **VIP scores** e **coeficientes de regressão PLS** (`mdatools::vipscores`, `plsVarSel`) — mapear os
  comprimentos de onda influentes.
- **iPLS** (`plsVarSel::ipls`) — seleção por intervalos espectrais.
- **Checagem de plausibilidade:** as bandas selecionadas devem fazer sentido físico-químico:
  - água / O–H: ~1450 nm e ~1940 nm (e combinação ~1150 nm)
  - açúcares (C–H, O–H): ~1200 nm, ~1450 nm, ~1700–1800 nm
  - carotenoides / licopeno: região visível (~470–550 nm) — relevante para `a*`, `Chroma`, `Hue`
  - Se o modelo "bom" se apoiar em regiões sem sentido → suspeitar de confundimento/sobreajuste.

### 8.4 Métodos não-lineares — deliberadamente fora

Random Forest, SVM e redes não são recomendados aqui: com n = 21 o risco de sobreajuste é alto e, no estudo
anterior (n = 9), não superaram o PLS. Podem ser reconsiderados quando o nº de amostras aumentar.

---

## 9. Estratégia de validação (crítica com n = 21)

| Esquema | Como | Para quê |
|---------|------|----------|
| **Leave-one-fruit-out (LOFO)** | 21 folds sobre o **espectro médio por fruto** (n = 21) | **Esquema principal** para os modelos finais (Seção 7.3) |
| **k-fold agrupado por fruto, repetido** | 5 folds × 20 repetições, grupo = `Fruit`, sementes distintas | Usado só quando se modela com os 84 espectros empilhados (estudo do efeito da orientação); gera **distribuição** das métricas |
| **Leave-one-cultivar-out** | 3 folds: treina em 2 cultivares, prediz o 3º | Testa generalização **além** da identidade varietal; espera-se queda grande nos traços confundidos com cultivar |
| **Desempenho dentro de cultivar** | remover a média de cada cultivar de `y` e das predições (ou incluir `Type` como bloco) e recalcular r / RMSE | Responde: *o espectro explica a variação fruto-a-fruto além do cultivar?* |
| **Teste de permutação (y-randomization)** | 500–1000 permutações de `y`; refazer toda a CV | O R²cv real deve cair **fora** da distribuição nula; protege contra achados espúrios com p ≫ n |

**Regra anti-vazamento:** todo passo dependente dos dados — centragem, escala, escolha do pré-processamento,
seleção de variáveis, escolha do nº de LV, λ do glmnet — deve ser refeito **dentro** de cada fold de treino.
Na prática, encapsular o pipeline (`caret::train` com `preProcess` + `index` de grupos, ou uma `recipe` do
`tidymodels` com `group_vfold_cv`).

### 9.1 Centralização por cultivar — teste de robustez adicional (implementado)

*Não prevista na versão original deste documento; adicionada após a análise inicial, como resposta à
pergunta "sem considerar o cultivar, a predição melhoraria?"* Implementada em
[`analise_centrado.R`](analise_centrado.R).

**Ideia:** no PLSR padrão (Seção 8.1), os 21 frutos entram misturados no ajuste. Como o cultivar explica boa
parte da variância de X e de y, é possível que as poucas variáveis latentes disponíveis sejam "gastas"
discriminando cultivar, sobrando pouca capacidade para a variação real de composição **dentro** de cada tipo.
A variante centrada remove a média de cada cultivar de X e de y **antes** de ajustar o PLS (não só depois,
como já faz o teste "dentro de cultivar" da tabela acima), forçando o modelo a resolver só a variação
intra-cultivar. A média de cada grupo usada para centralizar o treino e o fruto de teste é sempre recalculada
**só com os frutos de treino** (nunca inclui o próprio fruto predito), para não vazar informação.

**Resultado (as 5 posições, 16 características):** a centralização **não melhora a predição real** — na
maioria dos casos **piora**. Com só 6–7 frutos por cultivar para treinar a parte residual, o modelo overfita:
o teste de generalização (`R²_loco_c`) despenca a valores catastróficos em vários casos (ex.: Firmness em O2 =
−77,8; SS/AT em O2 = −79,7), muito piores que o `R²_loco` do modelo agrupado. A técnica não aumenta o n —
só remove variância — e com p ≫ n isso favorece ruído, não sinal.

**Uso que se revelou válido:** como **checagem de robustez** dos achados já identificados no modelo agrupado.
Sob esse teste mais rigoroso, **L\* em O3 manteve o sinal quase intacto** (`r_within` +0,82→+0,77;
`R²_loco`→`R²_loco_c` +0,80→+0,79), reforçando que é o achado mais sólido de toda a análise. Já **Fruit
length na média**, o melhor resultado por R²cv/RPD do modelo agrupado, **enfraqueceu bastante**
(`r_within` +0,68→+0,43; `R²_loco` +0,56→`R²_loco_c` **−0,39**), sugerindo que parte da sua força dependia de
compartilhar informação entre cultivares no ajuste conjunto. Detalhes completos em
[RESULTADOS_CONSOLIDADO.md](RESULTADOS_CONSOLIDADO.md).

---

## 10. Métricas e interpretação

Reportar, por característica e por estratégia:

| Métrica | Definição | Uso |
|---------|-----------|-----|
| R²cv | 1 − SQres/SQtot na validação | variância explicada fora da amostra |
| RMSECV | raiz do erro quadrático médio na CV | erro na unidade do alvo |
| **RPD** | SD(y) / RMSECV | Relação de Desempenho Residual (Williams) |
| **RPIQ** | IQR(y) / RMSECV | robusta a não-normalidade — **preferir ao RPD com n pequeno** |
| bias | média(pred − obs) | erro sistemático |
| slope | inclinação de obs ~ pred | 1 = ideal; < 1 indica encolhimento |
| nº LV | variáveis latentes do modelo final | parcimônia |

**Classificação de RPD (Williams, 2001):** > 2,5 excelente · 2,0–2,5 bom · 1,5–2,0 razoável · < 1,5 fraco
(não recomendado para predição quantitativa).

---

## 11. Expectativas por grupo de característica → resultados obtidos

Hipóteses originais desta seção, confrontadas com os resultados reais (todas as 5 posições, ver
[RESULTADOS_CONSOLIDADO.md](RESULTADOS_CONSOLIDADO.md)):

- **Morfologia** (`Length`, `Diameter`, `C_D`, `MF`): hipótese **confirmada, sem exceção**. R²cv sempre alto
  (0,45–0,96 conforme a posição) mas `R²_loco` negativo em **praticamente todos os casos** (de −0,12 a
  −29,5) — é discriminação de cultivar, não calibração de composição. Única exceção parcial: `Fruit length`
  na **média das 4 posições** chegou a `R²_loco` +0,56 (real), mas o teste de robustez da Seção 9.1 mostrou
  que esse resultado é **menos sólido** do que parece (cai para `R²_loco_c` −0,39 quando centralizado por
  cultivar).
- **Cor CIELab** (`L`, `a`, `b`, `a_b`, `Hue`, `Chroma`): hipótese **parcialmente confirmada, mas não como
  esperado**. `a*` e `Chroma` (a aposta inicial, ligada a licopeno/carotenoides) **não mostraram nenhum
  sinal em nenhuma posição** (R²cv sempre negativo). Em vez disso, o sinal real apareceu em `L*`, `a*/b*`,
  `Hue` e `b*` — e **só na posição O3**: `L*` em O3 é o achado mais forte de toda a análise
  (`r_within` +0,82, `R²_loco` +0,80), confirmado pelo teste de robustez (Seção 9.1). Nas demais posições
  (O1, O2, O4, média) o mesmo grupo de cor não mostrou sinal real.
- **`SS` e `Firmness`**: hipótese **refutada**. Nenhuma posição chegou perto do R² moderado/bom esperado.
  `Firmness` não teve sinal em nenhuma posição (R²cv sempre ≤ 0). `SS` teve sinal real, mas fraco, só em O3
  (`r_within` +0,30, `R²_loco` +0,46) — muito abaixo do R² ≈ 0,75 do estudo anterior.
- **`pH`, `AT`, `SS_AT`, `VitC`**: hipótese **majoritariamente confirmada, com uma exceção real**. `pH`, `AT`
  e `SS/AT` não mostraram sinal real em nenhuma das 5 posições (`r_within` ≈ 0 ou `R²_loco` negativo em
  todas). **Exceção: `Vit. C` em O1** — único caso com `r_within` e `R²_loco` ambos positivos (+0,52 / +0,21),
  confirmado pelo teste de robustez (Seção 9.1: r_within permanece +0,51 após centralizar por cultivar). Em
  qualquer outra posição, Vit. C perde o sinal (O2: `R²_loco` −9,0; O4: −1,15).

**Conclusão geral da Seção 11:** de 16 características testadas em 5 posições (80 combinações), só **6
combinações** mostraram evidência de sinal real e não-espúrio (`r_within`>0 **e** `R²_loco`>0): L\*, a\*/b\*,
Hue, b\* e SS em O3, e Vit. C em O1. Todas as demais combinações com R²cv alto refletem confundimento
varietal, não calibração química.

---

## 12. Análise complementar — classificação de cultivar (opcional)

**PLS-DA** (`mdatools::plsda`) ou **LDA** sobre scores de PCA para classificar TI/TH/TS a partir do espectro.
Acurácia (em CV agrupada por fruto) provavelmente alta. Serve para **quantificar explicitamente** quanta
informação varietal o espectro carrega — o que contextualiza (e relativiza) os R² altos de morfologia.

---

## 13. Saídas do relatório final

1. **Tabela mestra** — 16 características × [melhor pré-proc. · nº LV · R²cv · RMSECV · RPD · RPIQ · r
   dentro-de-cultivar · R²cv leave-one-cultivar-out · p do teste de permutação · classificação Williams].
2. **Tabela de orientações** — característica × estratégia (O1/O2/O3/O4/média/empilhado/concatenado) +
   **recomendação de protocolo de escaneamento**.
3. **Resultado da PERMANOVA / modelo misto** para o efeito da orientação.
4. **Figuras:** espectros brutos e pré-processados; scores de PCA (por cultivar e por orientação);
   VIP/coeficientes dos melhores modelos com bandas químicas anotadas; observado × predito dos melhores casos.
5. **Matriz de confusão** da PLS-DA de cultivar.
6. **Limitações e recomendações:**
   - n = 21 → resultado é de **viabilidade**, não calibração final.
   - Amostragem futura: idealmente ≥ 40–60 frutos por cultivar, cobrindo faixa ampla de maturação, para
     descolar o sinal químico do efeito varietal e permitir um conjunto de validação externo independente.
   - Padronizar a orientação de captura conforme a conclusão da Seção 7.

---

## Anexo — mapa de decisão rápido

```
84 espectros (21 frutos × 4 orientações) + 16 alvos
        │
        ├─ QC: plotar, aparar 450–2450 nm, PCA, outliers (Hotelling T²/Q)
        │      + checar se alguma orientação (ex.: O2) é aberrante
        │
        ├─ Efeito da orientação: PERMANOVA (spc ~ Type + Orient, strata = Fruit)
        │                        + lmer(PCk ~ Orient + (1|Fruit))
        │
        ├─ Definir conjunto de orientações "bom"  →  SNV/MSC por orientação  →  MÉDIA por fruto
        │      (21 espectros médios ↔ 21 valores de referência)
        │
        └─ Para cada alvo (×16):
               grid de pré-processamento (prospectr)
                     │
               PLSR (1–15 LV, regra 1-SE)  +  glmnet (LASSO/EN)
                     │
               LOFO (n=21, esquema principal)  +  leave-one-cultivar-out
                     │
               métricas: R²cv, RMSECV, RPD, RPIQ, bias, slope
                     │
               + desempenho dentro de cultivar
               + teste de permutação (y-randomization)
                     │
               VIP / coeficientes → checar bandas químicas
                     │
               comparar: média × melhor orientação isolada × concatenação × empilhado (CV agrupada)
        │
        └─ Complementar: PLS-DA de cultivar
        │
        └─ Tabela mestra + tabela de orientações + recomendação de protocolo
```
