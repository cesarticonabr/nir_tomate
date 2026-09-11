# Resultados consolidados — NIRS × posição de captura (P2)

**Comparação final O1 · O2 · O3 · O4 · média das 4, para as 16 características destrutivas · Setembro de 2026**

Relatórios individuais: [RESULTADOS_O1.md](RESULTADOS_O1.md) · [RESULTADOS_O2.md](RESULTADOS_O2.md) ·
[RESULTADOS_O3.md](RESULTADOS_O3.md) · [RESULTADOS_O4.md](RESULTADOS_O4.md) · [RESULTADOS_mean.md](RESULTADOS_mean.md)

> Critério de leitura: **nunca usar R²cv isoladamente** (com n=21 e milhares de bandas, R²cv alto pode ser só
> discriminação de cultivar). O critério de decisão é **`r_within` (sinal dentro de cultivar) + `R²_loco`
> (generaliza para cultivar novo)** — os dois positivos = evidência de calibração real.

---

## 0. Metodologia detalhada — por que não usar só R²cv

### 0.1 O problema: n pequeno, milhares de bandas, 3 grupos muito diferentes

O desenho é **n=21 frutos, ~4000 bandas espectrais** (p ≫ n), divididos em **3 cultivares** (TI/TH/TS, 7
frutos cada) que diferem muito entre si em forma, cor e tamanho — por biologia, não por um tratamento
controlado.

Isso cria um problema estatístico chamado **confundimento (confounding)**: se tanto o espectro quanto a
característica-alvo variam principalmente **entre cultivares** (e pouco **dentro** de cada cultivar), um
modelo pode "acertar" apenas **reconhecendo de qual cultivar é o fruto** e devolvendo a média daquele grupo —
sem captar nenhuma relação real espectro↔composição.

O motivo de isso não aparecer no R²cv comum (validação Leave-One-Fruit-Out, LOO) é sutil: ao deixar 1 fruto de
fora, **os outros 6 frutos do mesmo cultivar continuam no treino**. O modelo aprende a "impressão digital"
espectral daquele cultivar e a média do grupo para o alvo, e prediz próximo dessa média — o que já basta para
um R²cv alto se o alvo difere bastante entre cultivares, mesmo sem nenhuma relação de composição real.

### 0.2 `r_within` — há sinal *dentro* do cultivar?

Código: `analise_posicao.R`, linhas 199–207.

```r
within_cultivar_r <- function(y, yhat, grp) {
  yr <- y - ave(y, grp); pr <- yhat - ave(yhat, grp)
  suppressWarnings(stats::cor(yr, pr))
}
```

Para cada fruto, subtrai-se a **média do seu próprio cultivar** tanto do valor observado quanto do predito
(`ave(y, grp)`). O que sobra é a variação **fruto-a-fruto dentro do tipo** — a parte biologicamente
interessante (ex.: dois frutos Italiano, um mais maduro que o outro). Correlaciona-se os dois resíduos:

- Modelo que só reconhece cultivar → depois de remover a média do grupo quase não sobra sinal em nenhum dos
  dois lados → `r_within` ≈ 0.
- Modelo que capta composição real → a correlação sobrevive → `r_within` > 0.

### 0.3 `R²_loco` — o teste mais duro: cultivar nunca visto

Código: `analise_posicao.R`, linhas 209–220.

```r
loco <- function(Xm, y, grp, nlv) {
  yh <- numeric(length(y))
  for (g in levels(grp)) {
    te <- which(grp == g); tr <- which(grp != g)
    fit <- plsr(y ~ X, ncomp = nlv, data = data.frame(y = y[tr], X = I(Xm[tr, ])))
    yh[te] <- predict(fit, newdata = data.frame(X = I(Xm[te, ])), ncomp = nlv)[, 1, 1]
  }
  1 - sum((y - yh)^2) / sum((y - mean(y))^2)
}
```

O modelo é treinado em **2 cultivares inteiros (14 frutos)** e testado no **3º, nunca visto em nenhum grau**
(nem para calcular médias) — repete-se 3× (uma rodada por cultivar deixado de fora) e o R² final é calculado
sobre as 21 predições fora-da-amostra combinadas.

Por que isso desmonta o artefato: se o modelo só sabe "essa impressão espectral = cultivar TI → devolver a
média do TI", ele **não tem como fazer isso** para um cultivar que nunca esteve no treino — é forçado a
extrapolar via uma relação espectro→cultivar aprendida em *outros* dois grupos, que não tem nada a ver com o
novo. O erro resultante costuma ser **maior que simplesmente chutar a média geral** (R²=0), daí os valores
fortemente negativos observados quando o R²cv era artefato.

### 0.4 `p_perm` — separando "sinal" de "acaso" (não confundimento)

Código: `analise_posicao.R`, linhas 261–269. Embaralha-se `y` 99 vezes (quebrando qualquer relação real com o
espectro) e roda-se a mesma LOO. Se o R² observado não supera a maioria dos R² obtidos com `y` aleatório,
`p_perm` alto → o modelo não supera o acaso, risco esperado quando há mais bandas (~4000) que amostras (21).

**Atenção:** `p_perm` **não pega o confundimento de cultivar** — embaralhar `y` também quebra a associação
cultivar↔alvo, então um modelo puramente "identificador de cultivar" ainda pode ter `p_perm` bem significativo
(< 0,05). Por isso os três critérios são complementares, não substitutos:

| Métrica | O que descarta |
|---|---|
| `p_perm` | Resultado por puro acaso (overfitting com p≫n) |
| `r_within` | Modelo que só distingue cultivar, sem sinal interno |
| `R²_loco` | Modelo que não generaliza além dos cultivares vistos |

### 0.5 Exemplo lado a lado: C/D em O2 (artefato) vs. L\* em O3 (sinal real)

| Passo | **C/D — posição O2** | **L\* — posição O3** |
|---|---|---|
| R²cv (LOO normal) | **0,88** — parece "excelente" | 0,79 — "bom" |
| O que o LOO permite | ao deixar 1 fruto fora, os outros 6 do mesmo cultivar continuam no treino → o modelo aprende a média de C/D daquele cultivar e a reflectância que o identifica | idem, mas aqui a predição não depende só disso |
| `r_within` | **+0,12** (≈ 0) — quase nada sobra ao remover a média do cultivar | **+0,82** — a maior parte do sinal sobrevive: o modelo distingue frutos do MESMO cultivar entre si |
| `R²_loco` (treina em 2, testa no 3º nunca visto) | **−4,68** — o erro é ~4,7× a variância do próprio alvo; pior que simplesmente chutar a média geral | **+0,80** — quase nenhuma perda em relação ao R²cv normal |
| Interpretação | O modelo **não calibra C/D**; ele apenas memorizou "esse espectro = Italiano/Holandês/Salada" e devolveu a média de C/D daquele tipo. Como cada cultivar tem forma de fruto muito diferente, isso basta para um R²cv alto — mas é inútil para um cultivar novo | Evidência de que L\* está ligado a uma **variação real de composição/pigmentação da casca**, que se repete de forma parecida em qualquer cultivar — por isso o modelo treinado em 2 tipos consegue prever bem o 3º |

Esse contraste é o motivo de a Seção 1 usar `R²_loco`/`r_within` como critério de decisão, e não a coluna de
R²cv das tabelas mestras de cada posição.

### 0.6 Fluxo completo do script (`analise_posicao.R`)

1. **Importação e alinhamento** (linhas 74–128): lê a aba de espectros (comprimentos de onda × frutos),
   transpõe; extrai cultivar/fruto do código via regex; lê a aba destrutiva; casa os dois por
   `Treatments+Repetition`; corta para 450–2450 nm.
2. **Grid de 5 pré-processamentos** (linhas 130–144): bruto, SNV, SNV+1ª derivada, SNV+2ª derivada, detrend.
   Cada um age linha a linha (um espectro por vez), por isso pode ser calculado uma única vez sem vazar
   informação para a validação cruzada.
3. **Loop pelas 16 características** (linhas 227–282):
   - `loo_all_nlv()` (174–185): para cada um dos 5 pré-processamentos, roda Leave-One-Fruit-Out completo (21
     ajustes) testando 1 a 6 variáveis latentes de uma vez.
   - Escolhe o nº de LV com menor RMSECV por pré-proc → grava grid completo em `resultados_X/grid_<carac>.csv`.
   - Escolhe o **melhor pré-processamento geral** (menor RMSECV) → modelo final da característica.
   - `loo_fixed()` (189–197) refaz a LOO só com esse (preproc, nLV) fixo → usado no teste de permutação
     (repetido 99×, mais rápido com nLV fixo).
   - Calcula `p_perm`, `R²_loco` (via `loco()`) e `r_within`.
4. **Tabela mestra + gráficos** (linhas 284–347): CSV ordenado por R²cv, espectros coloridos por cultivar,
   PCA não-supervisionada (diagnóstico visual do confundimento) e observado×predito das 6 melhores
   características.

**Limitação assumida no próprio script** (linhas 32–34): o nº de LV é escolhido na mesma LOO que gera o R²cv,
então o R²cv fica levemente otimista (1 hiperparâmetro ajustado nos mesmos dados) — por isso a regra do
projeto é nunca decidir por R²cv sozinho, e sim por `p_perm` + `R²_loco` + `r_within`.

---

## 1. Tabela característica × posição (R²_loco / r_within)

Célula = `R²_loco` / `r_within`. **Negrito** = ambos positivos (evidência de sinal real).

| Característica | O1 | O2 | O3 | O4 | Média |
|---|:--:|:--:|:--:|:--:|:--:|
| Fruit length | −3,65 / −0,07 | −29,5 / −0,28 | −0,12 / +0,32 | −0,57 / +0,38 | **+0,56 / +0,68** |
| Fruit diameter | −1,85 / +0,03 | −4,03 / +0,12 | −1,64 / +0,35 | −0,50 / +0,50 | −1,83 / +0,19 |
| C/D | −0,27 / +0,16 | −4,68 / +0,12 | −0,82 / +0,18 | −1,06 / +0,27 | +0,81 / −0,03 (ver §2.2) |
| MF (massa fresca) | −1,59 / −0,21 | −2,83 / +0,20 | −2,14 / +0,02 | −1,06 / +0,45 | −0,90 / +0,18 |
| L\* | −0,61 / −0,04 | −1,92 / +0,52 | **+0,80 / +0,82** | −0,01 / +0,30 | −3,01 / +0,30 |
| a\* | −0,12 / −0,13 | −0,05 / −0,64 | −0,66 / +0,02 | −0,36 / +0,08 | −2,17 / −0,29 |
| b\* | +0,32 / +0,22 | −1,16 / +0,14 | **+0,05 / +0,37** | −0,30 / −0,09 | −1,21 / −0,08 |
| a\*/b\* | −1,23 / +0,16 | −1,55 / −0,24 | **+0,32 / +0,53** | +0,03 / +0,45 | −0,63 / +0,21 |
| Hue | −1,15 / +0,16 | −1,64 / −0,24 | **+0,12 / +0,45** | −0,04 / +0,38 | −0,49 / +0,14 |
| Chroma | +0,06 / +0,08 | −49,97 / −0,45 | −0,73 / +0,05 | −0,23 / +0,04 | −3,43 / −0,30 |
| Firmness | −1,12 / +0,12 | −29,87 / +0,42 | −0,06 / −0,24 | +0,14 / −0,09 | −3,39 / −0,74 |
| pH | −1,21 / +0,16 | −14,70 / +0,31 | −0,60 / −0,00 | −0,91 / +0,05 | −2,39 / +0,07 |
| Vit. C | **+0,21 / +0,52** | −9,00 / +0,39 | −0,62 / +0,21 | −1,15 / −0,20 | −7,06 / −0,12 |
| SS | −0,21 / +0,06 | −27,97 / −0,86 | **+0,46 / +0,30** | −0,26 / −0,41 | −3,64 / −0,18 |
| AT | +0,07 / −0,16 | −0,45 / −0,29 | −0,62 / +0,45 | −0,25 / −0,05 | −0,35 / −0,34 |
| SS/AT | +0,04 / −0,21 | −0,30 / +0,14 | −0,80 / +0,43 | −0,61 / −0,20 | −51,08 / −0,92 |

(Vit. C, AT e SS/AT em O1/mean têm sinais isolados positivos de `R²_loco` com `r_within` negativo/nulo —
inconsistentes, não contam como achado real: ver notas por posição.)

---

## 2. Achados reais (r_within **e** R²_loco positivos) — recomendação por característica

| Característica | Melhor posição | R²_loco | r_within | Força |
|---|---|:--:|:--:|---|
| **Fruit length** | **Média das 4** | +0,56 | +0,68 | Forte — RPD 5,18, "excelente" |
| **L\*** | **O3** | +0,80 | +0,82 | Forte — o achado mais robusto da série |
| **SS** (sólidos solúveis) | O3 | +0,46 | +0,30 | Fraco mas real |
| **Vit. C** | O1 | +0,21 | +0,52 | Fraco mas real |
| **a\*/b\*** | O3 | +0,32 | +0,53 | Fraco mas real |
| **Hue** | O3 | +0,12 | +0,45 | Fraco mas real |
| **b\*** | O3 (e O1) | +0,05 (+0,32) | +0,37 (+0,22) | Muito fraco mas real em 2 posições |

### 2.1 Sem sinal real em nenhuma posição

`Diameter`, `MF`, `C/D` (ressalva no §2.2), `a*`, `Chroma`, `Firmness`, `pH`, `AT`, `SS/AT` — em nenhuma das 5
análises os dois critérios (`r_within`>0 e `R²_loco`>0) coincidem de forma consistente.

### 2.2 C/D na média: caso à parte

`R²_loco` = +0,81 (2º melhor de toda a série) mas `r_within` ≈ 0 (−0,03). Não é evidência do mesmo tipo que
`Length`/`L*`: o modelo generaliza a relação cultivar→C/D, mas não explica variação fruto-a-fruto dentro do
cultivar. Promissor, mas precisa de mais frutos por cultivar para separar "generaliza porque é uma relação
real e forte" de "generaliza porque C/D e a assinatura espectral do cultivar covariam por acaso com só 3
grupos". Tratar como hipótese, não como calibração validada.

---

## 3. Panorama por posição

| Posição | Perfil | Nº achados reais | Conclusão de uso |
|---|---|:--:|---|
| **O1** (stem-end) | único sinal: Vit. C | 1 | Única fonte de sinal para Vit. C |
| **O2** (blossom-end) | confundimento severo (Italiano em patamar de reflectância isolado) | 0 | **Não recomendada** |
| **O3** (stem-end direita) | sinal real em cor/qualidade (L\*, a\*/b\*, Hue, SS, b\*) | 5 | **Melhor posição isolada** |
| **O4** (stem-end esquerda) | confundimento moderado, repete fracamente o padrão de O3 | 0 (a\*/b\* limítrofe) | Sem vantagem sobre O3 |
| **Média das 4** | sinal morfológico forte (comprimento, C/D-ressalva); cor diluída | 1 (2 com ressalva) | **Melhor para morfologia** |

---

## 4. Recomendação de protocolo

1. **Comprimento do fruto:** usar o espectro **médio das 4 orientações** — único caso "excelente" e
   genuinamente validado (`R²_loco` +0,56).
2. **L\* (luminosidade):** usar especificamente o espectro **O3** — sinal forte e não replicado em nenhuma
   outra posição nem na média.
3. **Vitamina C:** usar **O1** — única posição com sinal real, embora fraco.
4. **SS, a\*/b\*, Hue, b\*:** sinal fraco mas real em **O3** — candidatos a aprofundar com mais frutos antes
   de qualquer recomendação prática.
5. **Diameter, MF, C/D (calibração direta), a\*, Chroma, Firmness, pH, AT, SS/AT:** **nenhuma posição
   testada oferece calibração NIRS confiável** com este n=21. R²cv alto nessas variáveis em qualquer posição
   deve ser tratado como artefato de confundimento varietal, não como modelo utilizável.
6. **Evitar O2** como posição de captura única — é a mais contaminada por identidade varietal de todas.
7. **Fruto THR4:** outlier recorrente em O1/O2 (menos extremo em O3); confirmar na base de origem antes de
   qualquer reajuste dos modelos com sinal real (L\*, Vit. C).
8. **Limitação central a repetir em qualquer publicação:** n=21 frutos (7 por cultivar) é pequeno para PLSR
   com milhares de bandas — todos os achados "reais" aqui são indícios de viabilidade, não modelos prontos
   para uso; validação com mais frutos e, idealmente, mais safras/cultivares é necessária antes de qualquer
   aplicação prática.

---

## Anexo A — Explicação linha a linha do script (`analise_posicao.R`)

### Cabeçalho e configuração (linhas 41–72)

- **L41-44** — carrega os pacotes necessários (`readxl` lê `.xlsx`, `stringr` faz regex, `prospectr` tem
  SNV/derivada/detrend, `pls` faz a regressão PLS, `ggplot2` plota). `suppressMessages({...})` só esconde as
  mensagens de "pacote carregado" que cada `library()` imprime.
- **L46** `set.seed(1)` — trava a semente do gerador aleatório do R. Como o teste de permutação (linha 265)
  embaralha dados aleatoriamente, sem isso cada execução do script daria um `p_perm` ligeiramente diferente;
  com a semente fixa, o resultado é sempre reprodutível.
- **L47** desliga o processamento paralelo do pacote `pls` (evita travamentos no Windows, segundo o comentário).
- **L50** `commandArgs(trailingOnly=TRUE)[1]` — pega o primeiro argumento digitado depois do nome do script (o
  "O3" de `Rscript analise_posicao.R O3`).
- **L51** — se você rodar sem argumento nenhum, `POS` fica `NA`, e essa linha define "O1" como padrão.
- **L54-60** — `ABAS` é um vetor nomeado: um "dicionário" que traduz o código curto ("O3") para o nome exato
  da aba no Excel ("O3 (stem-end to the right)"), já que os nomes das abas são longos.
- **L61** `stopifnot(...)` — se você digitar um código inválido (ex.: "O5"), o script para na hora com erro
  claro, em vez de falhar mais adiante de forma confusa.
- **L65** `ABA_ESP <- ABAS[[POS]]` — busca no dicionário o nome real da aba.
- **L66-67** monta o nome da pasta de saída (`resultados_O3`) e cria essa pasta (`showWarnings=FALSE` evita
  aviso se ela já existir).
- **L68-70** — três constantes do estudo: faixa espectral a manter (corta pontas ruidosas), número de
  permutações (99) e número máximo de variáveis latentes do PLS (6).
- **L72** imprime no console qual posição está rodando.

### Seção 1 — Importação e montagem dos dados (linhas 80–127)

- **L80** lê a aba de espectros como uma tabela (`esp`).
- **L81** `wl_all <- esp[[1]]` — a 1ª coluna da aba é o eixo de comprimentos de onda (400, 400,5, 401...);
  vira um vetor simples.
- **L82** `t(as.matrix(esp[, -1]))` — pega todas as colunas menos a 1ª (os espectros de cada fruto), converte
  para matriz numérica e **transpõe**: na planilha as linhas eram comprimento de onda e as colunas eram
  frutos; depois de `t()` fica frutos nas linhas, bandas nas colunas — formato exigido para modelar.
- **L83** após transpor, os nomes das colunas do Excel (códigos dos espectros, ex. "TIR1O1") viram nomes das
  *linhas* da matriz; `rownames()` extrai esses códigos.
- **L89** `str_match(cod, "^(T[IHS])R([0-9])")` — expressão regular: `^` = início da string; `T[IHS]` casa
  literalmente "TI", "TH" ou "TS"; `R([0-9])` casa "R" seguido de um dígito, capturado entre parênteses.
  `str_match` devolve uma matriz com a correspondência inteira na coluna 1 e cada grupo capturado nas colunas
  seguintes. Funciona mesmo em códigos sem sufixo de posição (ex. "THR7"), pois só olha o prefixo.
- **L90** reconstrói o ID limpo do fruto ("TIR1") juntando cultivar + "R" + dígito capturados, descartando
  qualquer sufixo tipo "O3".
- **L91** `factor(m[,2])` — transforma as letras do cultivar (TI/TH/TS) em variável categórica (fator) do R,
  usada depois como `grp` em `r_within`/`loco`.
- **L92** checagem dupla: nenhum código falhou no regex (`!anyNA`), e existem exatamente 21 frutos distintos.
- **L95-96** lê a aba de análise destrutiva e remove linhas em branco no rodapé (comum em planilhas Excel).
- **L99-103** dois vetores paralelos: `traits` = nomes exatos das 16 colunas no Excel (com acentos/símbolos
  como "a\*/b\*"); `sig` = siglas curtas e "seguras" em R (sem `*`/`/`) usadas no resto do código.
- **L106** confere que as 16 colunas realmente existem na aba — pega erro de digitação/coluna renomeada na
  hora.
- **L112** `lapply(traits, function(nm) as.numeric(dest[[nm]]))` — percorre as 16 características, pega cada
  coluna por nome (`dest[[nm]]`), força para numérico (caso o Excel tenha guardado como texto) e junta as 16
  colunas resultantes num novo data frame `Y`. Acessar por nome individualmente evita a corrupção de colunas
  Hue/Chroma que ocorria ao fazer `dest[traits]` de uma vez (nomes com `*`/`/` confundiam o subset).
- **L113** renomeia as colunas de `Y` para as siglas curtas.
- **L114** imprime quantos `NA` (faltantes) cada característica tem — diagnóstico rápido.
- **L117** monta a chave de junção do lado da referência: `Treatments` ("TI") + `Repetition` (já vem como
  "R1", "R2"...) = "TIR1", igual ao ID do espectro.
- **L118** `match(Fruit, ykey)` — para cada espectro, acha a posição (linha) correspondente em `dest`.
- **L119** reordena `Y` segundo esse casamento, para que a linha *i* de `Ymat` seja do mesmo fruto que a
  linha *i* da matriz espectral.
- **L120** confere que todo espectro achou par (`!anyNA(ord)`) e que sobraram os 21 frutos.
- **L123-125** `keep` marca quais bandas ficam entre 450–2450 nm; `wl` e `X` são recortados para manter só
  essa faixa.
- **L126-127** imprime as dimensões finais da matriz.

### Seção 2 — Pré-processamentos espectrais (linhas 136–144)

- **L136** `W <- 15` — largura da janela do filtro Savitzky-Golay (precisa ser número ímpar de pontos).
- **L137-143** `Xp` é uma lista com 5 versões da mesma matriz espectral:
  - `raw` — sem tratamento nenhum.
  - `SNV` (`standardNormalVariate`) — para cada espectro (linha), subtrai sua própria média e divide pelo seu
    próprio desvio-padrão. Remove diferenças de nível/escala entre frutos causadas por fatores físicos
    (distância ao sensor, textura da casca), deixando só a forma do espectro comparável.
  - `SNV_D1` — aplica SNV e depois a 1ª derivada via Savitzky-Golay (`m=1`: ordem da derivada; `p=2`: grau do
    polinômio local ajustado; `w=W`: tamanho da janela). Derivada realça inclinações/mudanças de direção e
    remove qualquer deslocamento constante restante.
  - `SNV_D2` — igual, mas 2ª derivada (`m=2`): realça picos/curvaturas e remove também tendências lineares.
  - `detrend` — ajusta uma curva polinomial (quadrática) ao longo do eixo de comprimento de onda de cada
    espectro bruto e a subtrai; outra forma (do pacote `prospectr`) de corrigir linha de base curva.
- **L144** garante que todos os 5 elementos da lista sejam matrizes de verdade (algumas funções do
  `prospectr` devolvem outro tipo de objeto).

### Seção 3 — Funções de apoio: o coração da metodologia (linhas 158–224)

**`metrics(y, yhat)`** (L158-164) — recebe observados e preditos e devolve uma linha com 6 números:
- `press` = soma dos erros² (Prediction Error Sum of Squares); `tss` = soma dos desvios² em torno da média de
  `y` (a "régua" de comparação: "o quanto y varia sozinho").
- `rmse` = raiz do erro quadrático médio.
- `R2cv = 1 - press/tss` — 1 é perfeito, 0 é "tão bom quanto chutar a média para todo mundo", negativo é
  "pior que chutar a média".
- `RPD = sd(y)/rmse` — razão entre a dispersão natural do alvo e o erro do modelo (critério de Williams).
- `RPIQ = IQR(y)/rmse` — igual, mas usando a amplitude interquartil (mais robusta a assimetria/outliers).
- `bias = mean(yhat-y)` — erro sistemático médio (super ou sub-estimação).
- `slope = coef(lm(y~yhat))[2]` — regride observado sobre predito e pega a inclinação; modelo ideal tem
  slope ≈ 1.

**`loo_all_nlv()`** (L174-185):
- L175 nunca deixa usar mais variáveis latentes que `n-3` (regra prática para não estourar com poucos dados).
- L176 pré-aloca uma matriz vazia 21×6 para guardar as predições.
- L177-183 `for` fruto a fruto: `tr` = os outros 20 (`setdiff` = "todos menos o i"); `plsr(y~X, ncomp=nlv_max,
  data=data.frame(y=y[tr], X=I(Xm[tr,])))` treina o PLS — o `I(...)` diz ao R "trate essa matriz inteira como
  um único preditor", não uma coluna por banda; `ncomp=nlv_max` faz o pacote calcular de 1 a 6 componentes de
  uma vez só (eficiente, pois o PLS constrói os componentes em sequência); `predict()` prevê o fruto `i` para
  todos os nLV; `pr[1,1,]` extrai esse vetor de um array 3D (`[obs, resposta, ncomp]`) e guarda na linha `i`.
- Devolve uma matriz 21×6: cada célula é "predição do fruto tal, usando tantas variáveis latentes".

**`loo_fixed()`** (L189-197) — igual, mas com um número fixo de LV (não testa 1 a 6). É usada no teste de
permutação porque roda ~100× mais rápido que refazer o `loo_all_nlv` completo a cada embaralhamento.

**`within_cultivar_r()`** (L204-207):
- `ave(y, grp)` calcula a média de `y` dentro de cada grupo e devolve um vetor do mesmo tamanho de `y` (cada
  fruto recebe a média do seu próprio cultivar, repetida). `y - ave(y,grp)` deixa só o desvio de cada fruto
  em relação à média do seu tipo — a variação "fruto a fruto" que interessa biologicamente.
- Mesma coisa é feita com `yhat`.
- `cor(yr, pr)` correlaciona os dois resíduos. `suppressWarnings` só esconde o aviso de "desvio-padrão zero"
  que apareceria se um vetor não tivesse variação.

**`loco()`** (L212-220):
- `for (g in levels(grp))` — um laço por cultivar (3 rodadas).
- `te <- which(grp==g)` = os 7 frutos daquele cultivar (teste); `tr <- which(grp!=g)` = os outros 14 (treino).
- Treina só nos 14, prediz os 7 nunca vistos, guarda em `yh[te]`.
- Ao final, calcula o mesmo R² de sempre, mas agora toda predição veio de um modelo que nunca tinha visto
  nenhum fruto daquele cultivar.

**`williams()`** (L223-224) — `ifelse` aninhado que transforma o número do RPD em rótulo texto
("excelente"/"bom"/"razoável"/"fraco"), seguindo os limiares clássicos da literatura de calibração NIRS
(Williams, 2001).

### Seção 4 — Laço principal, 16 características (linhas 229–282)

- **L229** duas listas vazias que vão acumular, respectivamente, o resumo de cada característica e as
  predições fruto-a-fruto.
- **L231** `for (s in sig)` — percorre as 16 siglas.
- **L232** pega o vetor de 21 valores de referência daquela característica.
- **L233-237** se houver `NA` nessa característica, avisa quais linhas e pula para a próxima com `next`.
- **L242** `for (pp in names(Xp))` — testa os 5 pré-processamentos, um de cada vez:
  - L243 roda o LOO completo (todos os nLV) para este pré-proc.
  - L244 `sweep(P, 1, y)` subtrai `y` de cada coluna de `P` (o `1` diz "alinhar por linha"), dando o erro
    (predito−observado) de cada fruto em cada nº de LV; elevar ao quadrado e tirar a média por coluna
    (`colMeans`) dá um RMSECV por número de componentes.
  - L245 `which.min(rmsecv)` — o nº de LV com menor erro é escolhido como "o melhor" para este pré-proc.
  - L246-248 calcula as métricas completas nesse ponto ótimo, etiqueta a linha com qual pré-proc/nLV a
    geraram, além do `r_within`.
  - L249 empilha essa linha na tabela `tab` (crescendo a cada pré-proc testado).
- **L251-252** ordena as 5 linhas por R²cv decrescente e salva o grid completo em CSV
  (`grid_<caracteristica>.csv`) — a "prestação de contas" de todo o processo de escolha.
- **L255** pega a 1ª linha (a vencedora) como `best`.
- **L258** recalcula as predições LOO com esse (pré-proc, nLV) fixo vencedor — usadas no gráfico e no teste
  de permutação.
- **L259** recalcula o R² observado manualmente (mesmo valor do `R2cv` em `best`, como número solto, para
  comparar com a distribuição nula a seguir).
- **L264-268** `replicate(N_PERM, {...})` roda o bloco entre chaves 99 vezes: `sample(y)` embaralha os 21
  valores (quebra qualquer ligação real com o espectro, mantendo os mesmos números); refaz a LOO com esse
  alvo embaralhado; calcula o R² "de mentira" alcançado. `replicate` junta os 99 resultados no vetor `r2_null`.
- **L269** `p_perm = (1 + Σ(nulo ≥ real)) / (1 + 99)` — conta quantas vezes o acaso empatou ou superou o
  resultado real; o "+1" em cima e embaixo é uma correção estatística padrão para nunca dar exatamente zero.
- **L272** calcula o `R²_loco` do modelo vencedor.
- **L275-277** anexa `p_perm`, `R²_loco` e o rótulo Williams à linha `best`; guarda essa linha final na lista
  `res`; guarda também as 21 predições individuais (observado × predito, com fruto e cultivar) na lista
  `pred_best`, usadas depois no gráfico.
- **L279-281** imprime uma linha-resumo formatada no console, para acompanhar o progresso em tempo real — é
  exatamente essa linha que aparece no terminal quando o script roda.

### Depois do laço e Seção 5 — tabela final e gráficos (linhas 285–347)

- **L285** `do.call(rbind, res)` — empilha todas as linhas-resumo (uma por característica) num único data
  frame.
- **L286** ordena por R²cv decrescente.
- **L287** `sapply(master, is.numeric)` acha quais colunas são numéricas; `lapply(..., round, 3)` arredonda
  só essas para 3 casas decimais (deixa texto como `trait`/`preproc`/`classe` intacto).
- **L288** salva a tabela mestra em CSV (ex.: `resumo_O3.csv`).
- **L290-291** imprime a tabela no console, só com as colunas relevantes — é essa tabela que aparece no topo
  de cada `RESULTADOS_O{n}.md`.
- **L296** empilha as predições fruto-a-fruto de todas as 16 características num único data frame comprido.
- **L297** `saveRDS(...)` grava um arquivo binário do R com a tabela mestra + as predições, para reabrir
  depois sem rodar tudo de novo.
- **L299** define uma cor fixa por cultivar (paleta segura para daltonismo), usada em todos os gráficos.
- **L300** meia-janela do filtro Savitzky-Golay — necessária porque a derivada "come" pontos das duas pontas
  do espectro, então o eixo x precisa encolher do mesmo tanto ao plotar.
- **5a (L303-317)**, dentro de `try({...})` (evita que uma falha de plotagem derrube o script inteiro): abre
  um PNG, arruma um grid 2×2, e desenha espectros brutos, SNV, SNV+1ª derivada (cada linha = 1 fruto,
  colorida por cultivar), e um 4º painel só com a legenda; fecha o arquivo.
- **5b (L321-331)**: `prcomp(...)` roda a Análise de Componentes Principais sobre os espectros SNV — reduz
  milhares de bandas correlacionadas a poucas "direções de máxima variância"; `ve` converte a variância de
  cada componente em % do total; plota PC1×PC2 coloridos por cultivar, rotula cada ponto com o ID do fruto —
  é o gráfico que mostra visualmente se os cultivares se separam sozinhos no espaço espectral (o diagnóstico
  visual do confundimento).
- **5c (L335-345)**: pega as 6 características de maior R²cv; monta um `ggplot` com uma linha tracejada de
  "predição perfeita", pontos observado×predito coloridos por cultivar, um painel por característica com
  escalas livres; salva em PNG.
- **L347** mensagem final indicando onde os arquivos foram salvos.

---

## Anexo B — Código R completo (`analise_posicao.R`)

Script usado para gerar as 5 análises (O1, O2, O3, O4, média). Referenciado nas Seções 0 e Anexo A (funções
`metrics()`, `loo_all_nlv()`, `loo_fixed()`, `within_cultivar_r()`, `loco()`).

```r
# #####################################################################
#  ANALISE NIRS - UMA POSICAO DE CAPTURA (O1, O2, O3, O4 ou a MEDIA)
#  Objetivo: verificar se o espectro NIR de uma dada posicao consegue
#  predizer as 16 caracteristicas medidas por analise destrutiva (P2).
#
#  USO:  Rscript analise_posicao.R O2
#        (argumento: O1 | O2 | O3 | O4 | mean ; padrao = O1)
#
#  DESENHO DOS DADOS
#  - 21 frutos independentes: 3 cultivares (TI = Italiano, TH = Holandes,
#    TS = Salada), 7 frutos cada.
#  - 1 espectro por fruto (a posicao escolhida).
#  - 16 alvos de referencia, 1 valor por fruto.
#
#  DESAFIOS ESTATISTICOS (condicionam todo o script)
#  1. n = 21 contra ~4000 preditores -> estudo de VIABILIDADE, nao
#     calibracao final. Toda metrica sai de validacao cruzada.
#  2. Confundimento com cultivar: os 3 tipos diferem muito em forma/cor,
#     entao um modelo pode "acertar" so reconhecendo o cultivar. Por isso
#     calculamos tambem o desempenho DENTRO de cultivar (r_within) e o
#     leave-one-cultivar-out (R2_loco).
#  3. p >> n favorece achados por acaso -> teste de permutacao (p_perm).
#
#  METODO
#  - PLSR (regressao por minimos quadrados parciais), 1..6 componentes.
#  - Grid de 5 pre-processamentos espectrais; escolhe-se o de menor RMSECV.
#  - Validacao: Leave-One-Fruit-Out (LOO) = 21 ajustes, cada um deixando
#    1 fruto de fora.
#  - No melhor pre-proc de cada alvo: teste de permutacao + leave-one-
#    cultivar-out + correlacao dentro de cultivar.
#
#  LIMITACAO ASSUMIDA: o nLV e escolhido na mesma LOO -> o R2cv da tabela
#  e levemente otimista (1 hiperparametro inteiro). Os numeros confiaveis
#  sao p_perm, R2_loco e r_within.
# #####################################################################

# --- Pacotes -------------------------------------------------------------
# readxl   : ler .xlsx           | prospectr : pre-processamento espectral
# pls      : PLSR + predict      | ggplot2   : grafico observado x predito
# dplyr/tidyr/stringr: manipulacao de dados e parsing dos codigos
suppressMessages({                    # esconde as mensagens de "pacote carregado"
  library(readxl); library(dplyr); library(stringr); library(tidyr)
  library(prospectr); library(pls); library(ggplot2)
})

set.seed(1)                  # trava a semente aleatoria -> permutacoes sempre repetiveis
pls.options(parallel = NULL) # PLSR em serie (evita instabilidade no Windows)

# --- Posicao a analisar (argumento da linha de comando) --------------
POS <- commandArgs(trailingOnly = TRUE)[1]  # 1o argumento apos "Rscript analise_posicao.R"
if (is.na(POS)) POS <- "O1"                 # nenhum argumento informado -> usa O1

# Mapa: rotulo da posicao -> nome exato da aba no arquivo .xlsx
ABAS <- c(                               # vetor NOMEADO: "dicionario" codigo-curto -> nome da aba
  O1   = "O1 (stem-end view)",
  O2   = "O2 (blossom-end view)",
  O3   = "O3 (stem-end to the right)",
  O4   = "O4 (stem-end to the left)",
  mean = "means of 4 positions"          # media das 4 orientacoes (aba gerada a parte)
)
stopifnot(POS %in% names(ABAS))          # para com erro claro se o argumento for invalido (ex.: "O5")

# --- Parametros do estudo ---------------------------------------------
ARQ      <- "Capturas_tomate_NIRS_11agosto (1).xlsx"  # planilha de origem
ABA_ESP  <- ABAS[[POS]]                 # aba com os espectros desta posicao
OUT_DIR  <- paste0("resultados_", POS)  # pasta de saida (tabelas + graficos)
dir.create(OUT_DIR, showWarnings = FALSE)  # cria a pasta (sem avisar se ja existir)
WL_MIN <- 450; WL_MAX <- 2450           # manter so esta faixa (corta ruido nas pontas)
N_PERM <- 99                            # nº de permutacoes do teste y-randomization
NLV_MAX <- 6                            # nº maximo de variaveis latentes do PLS

cat(sprintf(">>> POSICAO %s  (aba: %s)\n\n", POS, ABA_ESP))  # mensagem de status no console

# ---------------------------------------------------------------------
# 1. IMPORTACAO E MONTAGEM DA MATRIZ
# ---------------------------------------------------------------------

# 1a. Espectros: a aba vem com comprimento de onda nas LINHAS e frutos nas
#     COLUNAS. Precisamos do oposto (frutos nas linhas) para modelar.
esp    <- read_excel(ARQ, sheet = ABA_ESP)  # le a aba de espectros inteira como tabela
wl_all <- esp[[1]]                  # 1a coluna = vetor de comprimentos de onda
X_all  <- t(as.matrix(esp[, -1]))   # remove a 1a coluna, converte p/ matriz e TRANSPOE -> 21 frutos x ~4200 bandas
cod    <- rownames(X_all)           # apos transpor, cabecalhos das colunas viram nomes de linha: "TIR1O1", "THR5", "TSR2O3", ...

# 1b. Extrair cultivar e repeticao do codigo do espectro.
#     Regex TOLERANTE: casa so o prefixo "T(I|H|S)R(digito)", ignorando o
#     que vem depois. Algumas colunas de O2/O3/O4 vem sem o sufixo "O#"
#     (ex.: "THR7", "THR4") - o prefixo continua identificando o fruto.
m      <- str_match(cod, "^(T[IHS])R([0-9])")  # extrai (cultivar, digito de repeticao) de cada codigo
Fruit  <- paste0(m[, 2], "R", m[, 3])   # id do fruto: "TIR1" (chave de juncao)
Type   <- factor(m[, 2])                # cultivar como fator (TI/TH/TS)
stopifnot(!anyNA(Fruit), length(unique(Fruit)) == 21)  # nenhum codigo falhou no regex, e sao 21 frutos distintos

# 1c. Referencia destrutiva. Remove as linhas em branco do rodape da aba.
dest <- read_excel(ARQ, sheet = "Analise_destrutiva_P2")  # le a tabela com as 16 medidas destrutivas
dest <- dest[!is.na(dest$Treatments), ]                   # descarta linhas em branco no fim da planilha

# Nomes das 16 colunas na planilha  ->  siglas curtas usadas no codigo
traits <- c("Fruit length","Fruit diameter","C/D","MF","L*","a*","b*","a*/b*",
            "Hue","Chroma","Firmness","pH","Vit. C","Total soluble solids",
            "Titratable acid","SS/AT ratio")             # nomes EXATOS das colunas no Excel
sig <- c("Length","Diameter","C_D","MF","L","a","b","a_b","Hue","Chroma",
         "Firmness","pH","VitC","SS","AT","SS_AT")        # siglas curtas "seguras" p/ usar no codigo R

# Confere que todos os nomes existem na aba (evita erro silencioso).
stopifnot(all(traits %in% names(dest)))

# Constroi a matriz Y (21 x 16), forcando cada coluna a numerico.
# IMPORTANTE: acessar coluna a coluna por nome (dest[[nm]]); subsetar uma
# tibble por vetor de nomes com caracteres especiais ("a*/b*") pode
# corromper as colunas.
Y <- as.data.frame(lapply(traits, function(nm) suppressWarnings(as.numeric(dest[[nm]]))))  # 1 coluna numerica por caracteristica
names(Y) <- sig                                             # renomeia para as siglas curtas
cat("NA por caracteristica:\n"); print(colSums(is.na(Y)))  # diagnostico: quantos faltantes por coluna

# 1d. Alinhar espectros <-> referencia pelo id do fruto.
ykey <- paste0(dest$Treatments, dest$Repetition)  # id do fruto na referencia (Repetition ja vem como "R1","R2"...)
ord  <- match(Fruit, ykey)                        # para cada espectro, a linha correspondente em 'dest'
Ymat <- Y[ord, , drop = FALSE]                    # Y reordenada para casar linha a linha com os espectros
stopifnot(!anyNA(ord), nrow(Ymat) == 21)          # todos os espectros acharam par, e sao 21 no total

# 1e. Recorte espectral: mantem 450-2450 nm (descarta pontas ruidosas).
keep <- wl_all >= WL_MIN & wl_all <= WL_MAX  # vetor logico: TRUE onde a banda esta dentro da faixa
wl   <- wl_all[keep]                          # eixo de comprimento de onda recortado
X    <- X_all[, keep]                              # matriz espectral final (21 x 4001)
cat(sprintf("Espectros %s: %d frutos x %d bandas (%.0f-%.0f nm)\n",
            POS, nrow(X), ncol(X), min(wl), max(wl)))               # confirma dimensoes finais
cat("Frutos/cultivar: ", paste(names(table(Type)), table(Type), sep = "=", collapse = "  "), "\n\n")  # confirma 7/7/7

# ---------------------------------------------------------------------
# 2. PRE-PROCESSAMENTOS ESPECTRAIS
#    Cada transformacao age LINHA A LINHA (um espectro por vez) e NAO
#    aprende parametros do conjunto -> pode ser aplicada uma unica vez
#    aqui, sem risco de vazamento de informacao para a validacao.
# ---------------------------------------------------------------------
W <- 15  # janela do filtro Savitzky-Golay (nº impar de pontos)
Xp <- list(                                                   # lista com as 5 versoes da matriz espectral
  raw     = X,                                                # sem tratamento
  SNV     = standardNormalVariate(X),                         # remove desvio de linha de base e de escala (por espectro)
  SNV_D1  = savitzkyGolay(standardNormalVariate(X), m = 1, p = 2, w = W),  # 1a derivada (realca inclinacoes; m=ordem, p=grau do polinomio, w=janela)
  SNV_D2  = savitzkyGolay(standardNormalVariate(X), m = 2, p = 2, w = W),  # 2a derivada (realca picos/curvatura)
  detrend = detrend(X, wav = wl)                              # remove tendencia polinomial ao longo do comprimento de onda
)
Xp <- lapply(Xp, as.matrix)  # garante que todas sao matriz (savitzkyGolay pode devolver outra classe)

# ---------------------------------------------------------------------
# 3. FUNCOES DE APOIO
# ---------------------------------------------------------------------

# 3a. metrics(): metricas de calibracao a partir dos valores observados (y)
#     e preditos (yhat) na validacao.
#       R2cv  = 1 - SQresiduo / SQtotal  (variancia explicada fora da amostra)
#       RMSECV= raiz do erro quadratico medio (unidade do alvo)
#       RPD   = desvio-padrao(y) / RMSECV   -> criterio de Williams
#       RPIQ  = amplitude interquartil(y) / RMSECV  -> robusto a nao-normalidade
#       bias  = erro sistematico medio
#       slope = inclinacao de obs ~ pred (1 = ideal)
metrics <- function(y, yhat) {
  press <- sum((y - yhat)^2); tss <- sum((y - mean(y))^2)  # soma dos erros^2 (PRESS) e soma dos desvios^2 (baseline "chutar a media")
  rmse  <- sqrt(press / length(y))                          # raiz do erro quadratico medio (RMSECV)
  data.frame(R2cv = 1 - press / tss, RMSECV = rmse,          # R2cv: 1=perfeito, 0="tao bom quanto a media", <0="pior que a media"
             RPD = sd(y) / rmse, RPIQ = IQR(y) / rmse,       # RPD usa desvio-padrao; RPIQ usa amplitude interquartil (mais robusta)
             bias = mean(yhat - y), slope = unname(coef(lm(y ~ yhat))[2]))  # erro sistematico medio; inclinacao obs~pred (ideal=1)
}

# 3b. loo_all_nlv(): validacao Leave-One-Fruit-Out.
#     Para cada fruto i: treina o PLS nos outros 20, preve o fruto i.
#     Retorna uma MATRIZ 21 x NLV_MAX -> predicao de cada fruto para
#     cada numero de componentes (1..NLV_MAX), pois o plsr calcula todos
#     os nLV de uma vez. Assim escolhemos o melhor nLV depois, comparando
#     colunas.
#     Obs: X = I(Xm[tr, ]) guarda a matriz espectral como uma "coluna
#     matriz" do data.frame (idioma padrao do pacote pls).
loo_all_nlv <- function(Xm, y, nlv_max = NLV_MAX) {
  n <- length(y); nlv_max <- min(nlv_max, n - 3)   # nunca mais LV que amostras-3
  P <- matrix(NA_real_, n, nlv_max)                # pre-aloca matriz de predicoes (n frutos x nlv_max componentes)
  for (i in seq_len(n)) {                          # laco: cada fruto i fica de fora uma vez (Leave-One-Out)
    tr  <- setdiff(seq_len(n), i)                  # indices de treino (20 frutos, todos menos o i)
    fit <- plsr(y ~ X, ncomp = nlv_max,             # treina PLS nos 20 fruto de treino, calculando de 1 a nlv_max componentes de uma vez
                data = data.frame(y = y[tr], X = I(Xm[tr, ])))  # I(...) trata a matriz espectral como um unico preditor "em bloco"
    pr  <- predict(fit, newdata = data.frame(X = I(Xm[i, , drop = FALSE])))  # preve o fruto i (fora do treino) para todos os nLV
    P[i, ] <- pr[1, 1, ]                            # extrai o vetor de predicoes (1 obs, 1 resposta, todos os nLV) e guarda na linha i
  }
  P                                                 # devolve matriz n x nlv_max: predicao de cada fruto, por numero de componentes
}

# 3c. loo_fixed(): mesma LOO, mas com nLV FIXO. Mais rapida - usada no
#     teste de permutacao (repetida centenas de vezes).
loo_fixed <- function(Xm, y, nlv) {
  n <- length(y); yh <- numeric(n)                 # vetor vazio para guardar 1 predicao por fruto
  for (i in seq_len(n)) {                          # mesmo esquema Leave-One-Out do loo_all_nlv()
    tr  <- setdiff(seq_len(n), i)                  # treino = todos menos o fruto i
    fit <- plsr(y ~ X, ncomp = nlv, data = data.frame(y = y[tr], X = I(Xm[tr, ])))  # treina so com nLV FIXO (mais rapido)
    yh[i] <- predict(fit, newdata = data.frame(X = I(Xm[i, , drop = FALSE])), ncomp = nlv)[1, 1, 1]  # preve o fruto i com esse nLV
  }
  yh                                                # devolve vetor de 21 predicoes (1 por fruto)
}

# 3d. within_cultivar_r(): correlacao observado x predito DEPOIS de
#     remover a media de cada cultivar (ave(.,grp)). Mede se o espectro
#     explica a variacao fruto-a-fruto DENTRO do mesmo tipo.
#       ~ 0  -> o modelo so distingue cultivares, nao calibra composicao
#       > 0  -> ha sinal real alem do efeito varietal
within_cultivar_r <- function(y, yhat, grp) {
  yr <- y - ave(y, grp); pr <- yhat - ave(yhat, grp)  # ave(y,grp) = media do cultivar de cada fruto; subtrair remove o efeito de cultivar
  suppressWarnings(stats::cor(yr, pr))                # correlaciona os residuos (variacao fruto-a-fruto DENTRO do tipo); NA vira aviso silenciado
}

# 3e. loco(): Leave-One-Cultivar-Out. Treina em 2 cultivares e preve o
#     terceiro (3 rodadas). R2 muito negativo = o modelo nao generaliza
#     para um cultivar novo -> a "calibracao" era contraste entre tipos.
loco <- function(Xm, y, grp, nlv) {
  yh <- numeric(length(y))                          # vetor vazio para as 21 predicoes fora-do-cultivar
  for (g in levels(grp)) {                          # 3 rodadas: uma para cada cultivar (TI, TH, TS)
    te <- which(grp == g); tr <- which(grp != g)    # teste = os 7 frutos do cultivar g; treino = os outros 14
    fit <- plsr(y ~ X, ncomp = nlv, data = data.frame(y = y[tr], X = I(Xm[tr, ])))  # treina SEM NENHUM fruto do cultivar g
    yh[te] <- predict(fit, newdata = data.frame(X = I(Xm[te, ])), ncomp = nlv)[, 1, 1]  # preve os 7 frutos nunca vistos
  }
  1 - sum((y - yh)^2) / sum((y - mean(y))^2)         # R2 sobre as 21 predicoes combinadas (as 3 rodadas juntas)
}

# 3f. williams(): classificacao qualitativa do RPD (Williams, 2001).
williams <- function(r) ifelse(r > 2.5, "excelente", ifelse(r > 2.0, "bom",   # limiares padrao da literatura NIRS
                        ifelse(r > 1.5, "razoavel", "fraco")))

# ---------------------------------------------------------------------
# 4. LOOP PRINCIPAL - 16 alvos x 5 pre-processamentos
# ---------------------------------------------------------------------
res <- list(); pred_best <- list()   # acumuladores: 1 resumo e 1 conjunto de predicoes por caracteristica

for (s in sig) {                     # laco principal: uma iteracao por caracteristica (16 no total)
  y <- Ymat[[s]]                       # vetor de referencia do alvo atual (21 valores)
  if (anyNA(y)) {                      # se houver NA na referencia, pula o alvo
    cat(sprintf("%-10s | NA na referencia (linhas %s) - pulado\n", s,
                paste(which(is.na(y)), collapse = ",")))
    next                                # vai direto para a proxima caracteristica do laco 'for'
  }

  # 4a. Testa os 5 pre-processamentos; para cada um, escolhe o nLV de
  #     menor RMSECV e guarda as metricas.
  tab <- NULL                          # tabela que vai acumular 1 linha por pre-processamento testado
  for (pp in names(Xp)) {              # laco interno: os 5 pre-processamentos (raw, SNV, SNV_D1, SNV_D2, detrend)
    P      <- loo_all_nlv(Xp[[pp]], y)          # 21 x NLV_MAX predicoes na LOO
    rmsecv <- sqrt(colMeans(sweep(P, 1, y)^2))  # subtrai y de cada coluna (sweep), eleva ao quadrado, tira a media -> RMSECV por nLV
    k      <- which.min(rmsecv)                 # melhor nLV para este pre-proc (menor RMSECV)
    mt <- metrics(y, P[, k])                    # metricas completas usando as predicoes desse nLV otimo
    mt$preproc <- pp; mt$nLV <- k                # etiqueta a linha com o pre-proc e o nLV usados
    mt$r_within <- within_cultivar_r(y, P[, k], Type)  # calcula tambem o r_within para esse (pre-proc, nLV)
    tab <- rbind(tab, mt)                        # empilha essa linha na tabela do alvo atual
  }
  tab <- tab[order(-tab$R2cv), ]               # ordena: melhor pre-proc no topo
  write.csv(tab, file.path(OUT_DIR, paste0("grid_", s, ".csv")), row.names = FALSE)  # salva o grid completo (auditoria)

  # 4b. Melhor pre-processamento do alvo.
  best <- tab[1, ]; nlv_b <- best$nLV; ppb <- best$preproc  # extrai a linha vencedora e seus parametros

  # 4c. Predicoes LOO do melhor modelo (para grafico e permutacao).
  yhat_b <- loo_fixed(Xp[[ppb]], y, nlv_b)       # refaz a LOO so com o (pre-proc, nLV) vencedor, ja fixo
  r2_obs <- 1 - sum((y - yhat_b)^2) / sum((y - mean(y))^2)  # R2 observado desse modelo final (numero solto p/ comparar com o teste nulo)

  # 4d. TESTE DE PERMUTACAO (y-randomization):
  #     embaralha y N_PERM vezes, refaz a LOO, e ve quantas vezes o R2 do
  #     acaso >= R2 real. p_perm alto (> 0.05) = o modelo nao supera o acaso.
  r2_null <- replicate(N_PERM, {                  # repete o bloco {...} 99 vezes, juntando os resultados num vetor
    yp <- sample(y)                                 # y embaralhado (quebra qualquer relacao real com o espectro)
    yh <- loo_fixed(Xp[[ppb]], yp, nlv_b)            # refaz a mesma LOO tentando prever o alvo embaralhado
    1 - sum((yp - yh)^2) / sum((yp - mean(yp))^2)    # R2 "de mentira" alcancado por acaso nesta repeticao
  })
  p_perm <- (1 + sum(r2_null >= r2_obs)) / (1 + N_PERM)  # fracao de vezes que o acaso empatou/superou o R2 real (+1/+1 = correcao padrao)

  # 4e. Leave-one-cultivar-out do melhor modelo.
  r2_loco <- loco(Xp[[ppb]], y, Type, nlv_b)      # generaliza para um cultivar nunca visto?

  # 4f. Guarda tudo.
  best$p_perm <- p_perm; best$R2_loco <- r2_loco; best$classe <- williams(best$RPD)  # anexa as 3 metricas de controle + rotulo RPD
  res[[s]] <- cbind(trait = s, best)              # guarda o resumo final desta caracteristica na lista global
  pred_best[[s]] <- data.frame(Fruit = Fruit, Type = Type, obs = y, pred = yhat_b, trait = s)  # guarda obs x pred de cada fruto (p/ grafico)

  cat(sprintf("%-10s | %-7s nLV=%d | R2cv=%+.2f RMSECV=%.3f RPD=%.2f RPIQ=%.2f | r_in=%+.2f | R2loco=%+.2f | p=%.3f | %s\n",
              s, ppb, nlv_b, best$R2cv, best$RMSECV, best$RPD, best$RPIQ,
              best$r_within, r2_loco, p_perm, best$classe))  # imprime a linha-resumo desta caracteristica no console
}

# 4g. Tabela mestra: 1 linha por alvo, ordenada por R2cv.
master <- do.call(rbind, res)                    # empilha os resumos das 16 caracteristicas num unico data frame
master <- master[order(-master$R2cv), ]          # ordena da maior para a menor R2cv
n <- sapply(master, is.numeric); master[n] <- lapply(master[n], round, 3)  # arredonda so as colunas numericas (3 casas)
write.csv(master, file.path(OUT_DIR, paste0("resumo_", POS, ".csv")), row.names = FALSE)  # salva a tabela mestra em CSV
cat(sprintf("\n================ TABELA MESTRA - %s ================\n", POS))
print(master[, c("trait","preproc","nLV","R2cv","RMSECV","RPD","RPIQ","r_within","R2_loco","p_perm","classe")],
      row.names = FALSE)                          # imprime so as colunas relevantes no console

# ---------------------------------------------------------------------
# 5. GRAFICOS  (cada bloco em try() para nao abortar se um falhar)
# ---------------------------------------------------------------------
pb <- do.call(rbind, pred_best)  # predicoes de todos os alvos empilhadas (1 linha por fruto x caracteristica)
saveRDS(list(master = master, pred = pb), file.path(OUT_DIR, paste0("resultados_", POS, ".rds")))  # salva tudo em .rds p/ reabrir sem re-rodar

pal <- c(TI = "#D55E00", TH = "#0072B2", TS = "#009E73")  # cor fixa por cultivar (mesma em todos os graficos)
hw  <- (W - 1) / 2  # meia-janela do SG (nº de bandas perdidas em cada ponta ao derivar)

# 5a. Espectros: bruto, SNV e SNV+1a derivada (para inspecao visual).
try({                                                # try() evita que uma falha de plotagem derrube o script
  png(file.path(OUT_DIR, paste0("espectros_", POS, ".png")), 1400, 950, res = 130)  # abre arquivo de saida
  op <- par(mfrow = c(2, 2), mar = c(4, 4, 2, 1))    # grid 2x2 de graficos, com margens customizadas
  matplot(wl, t(X), type = "l", lty = 1, col = pal[as.character(Type)],
          xlab = "nm", ylab = "Reflectancia", main = paste(POS, "- bruto"))  # painel 1: espectros brutos, 1 linha por fruto
  Xsnv <- standardNormalVariate(X)                    # recalcula SNV so para plotar
  matplot(wl, t(Xsnv), type = "l", lty = 1, col = pal[as.character(Type)],
          xlab = "nm", ylab = "SNV", main = paste(POS, "- SNV"))            # painel 2: espectros apos SNV
  d1 <- savitzkyGolay(Xsnv, m = 1, p = 2, w = W)      # recalcula SNV+1a derivada so para plotar
  wl_sg <- wl[(hw + 1):(length(wl) - hw)]           # eixo x ajustado ao SG
  matplot(wl_sg, t(d1), type = "l", lty = 1, col = pal[as.character(Type)],
          xlab = "nm", ylab = "SNV + 1a deriv.", main = paste(POS, "- SNV + D1"))  # painel 3: espectros derivados
  plot.new(); legend("center", names(pal), col = pal, lwd = 2, bty = "n", title = "Cultivar")  # painel 4: so a legenda
  par(op); dev.off()                                  # restaura parametros graficos e fecha/salva o PNG
})

# 5b. PCA (nao-supervisionada) sobre os espectros SNV: mostra se os
#     cultivares se separam sozinhos no espaco espectral.
try({
  pc <- prcomp(standardNormalVariate(X), center = TRUE, scale. = FALSE)  # PCA sobre os espectros SNV (centrado, sem escalar)
  ve <- round(100 * pc$sdev^2 / sum(pc$sdev^2), 1)   # % variancia explicada por cada componente
  png(file.path(OUT_DIR, paste0("pca_", POS, ".png")), 1000, 850, res = 130)
  plot(pc$x[, 1], pc$x[, 2], col = pal[as.character(Type)], pch = 19,
       xlab = sprintf("PC1 (%.1f%%)", ve[1]), ylab = sprintf("PC2 (%.1f%%)", ve[2]),
       main = paste0("PCA - espectros ", POS, " (SNV)"))  # dispersao PC1 x PC2, colorida por cultivar
  text(pc$x[, 1], pc$x[, 2], Fruit, pos = 3, cex = 0.6)  # rotula cada fruto
  legend("topright", levels(Type), col = pal[levels(Type)], pch = 19, bty = "n")
  dev.off()                                            # fecha/salva o PNG
})

# 5c. Observado vs. predito (LOO) das 6 caracteristicas de maior R2cv.
#     A linha tracejada e a identidade (predicao perfeita).
try({
  top6 <- head(master$trait, 6)                      # as 6 caracteristicas com maior R2cv (master ja esta ordenada)
  g <- ggplot(subset(pb, trait %in% top6), aes(obs, pred, color = Type)) +
    geom_abline(slope = 1, intercept = 0, linetype = 2, color = "grey50") +  # linha tracejada = predicao perfeita
    geom_point(size = 2) +                            # 1 ponto por fruto (obs x pred)
    facet_wrap(~ factor(trait, levels = top6), scales = "free") +  # 1 painel por caracteristica, eixos independentes
    scale_color_manual(values = pal) +                 # aplica a paleta fixa de cultivar
    labs(title = paste0(POS, " - observado vs. predito (LOO)"), x = "observado", y = "predito") +
    theme_bw()
  ggsave(file.path(OUT_DIR, paste0("obs_pred_", POS, ".png")), g, width = 10, height = 6.5, dpi = 130)  # salva o grafico
})

cat("\nArquivos em", OUT_DIR, "/\n")  # mensagem final indicando a pasta de saida

```
