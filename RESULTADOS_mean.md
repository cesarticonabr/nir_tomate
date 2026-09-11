# Resultados — Análise NIRS da média das 4 posições (means of 4 positions)

**Predição das 16 características destrutivas do bloco P2 · Setembro de 2026**

Script: [analise_posicao.R](analise_posicao.R) (`Rscript analise_posicao.R mean`) · Saídas: [resultados_mean/](resultados_mean/)

> Glossário completo: ver **Seção 2 de [RESULTADOS_O1.md](RESULTADOS_O1.md)**. `r_within` — correlação
> obs×pred após remover a média de cada cultivar (**≈ 0 → só separa cultivares**). `R²_loco` — R² ao treinar
> em 2 cultivares e prever o 3º (**muito negativo → não generaliza**). `p_perm` — p do teste de permutação.

O espectro de entrada aqui é a **média ponto a ponto das 4 orientações (O1–O4)** de cada fruto (aba
"means of 4 positions"), não uma concatenação — mesma dimensão espectral (4001 bandas) das análises anteriores.

---

## 1. Método (idêntico às demais posições)

PLSR 1–6 LV · grid de 5 pré-processamentos · 450–2450 nm · Leave-One-Fruit-Out (21 folds) · permutação (99×) ·
leave-one-cultivar-out · correlação dentro de cultivar. n = 21 frutos (TI/TH/TS, 7 cada).

---

## 2. Tabela mestra — média das 4 posições (ordenada por R²cv)

| Característica | Pré-proc. | nLV | R²cv | RMSECV | RPD | RPIQ | r_within | **R²_loco** | p_perm | Williams |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **Fruit length** | SNV+D1 | 6 | **0,96** | 1,68 | **5,18** | 10,09 | **+0,68** | **+0,56** | 0,01 | excelente |
| **C/D** | SNV+D2 | 1 | **0,86** | 0,064 | 2,78 | 4,82 | −0,03 | **+0,81** | 0,01 | excelente |
| MF (massa fresca) | SNV+D1 | 6 | 0,79 | 17,5 | 2,23 | 4,12 | +0,18 | −0,90 | 0,01 | bom |
| pH | SNV | 6 | 0,70 | 0,038 | 1,88 | 3,44 | +0,07 | −2,39 | 0,01 | razoável |
| Fruit diameter | SNV+D2 | 2 | 0,64 | 5,03 | 1,70 | 2,67 | +0,19 | −1,83 | 0,01 | razoável |
| L\* | bruto | 5 | 0,33 | 2,43 | 1,26 | 1,82 | +0,30 | −3,01 | 0,01 | fraco |
| SS (sólidos solúveis) | SNV+D2 | 4 | 0,31 | 0,330 | 1,23 | 1,82 | −0,18 | −3,64 | 0,01 | fraco |
| Vit. C | SNV+D2 | 4 | 0,24 | 17,0 | 1,17 | 1,25 | −0,12 | −7,06 | 0,04 | fraco |
| a\*/b\* | SNV | 1 | 0,23 | 0,125 | 1,17 | 1,29 | +0,21 | −0,63 | 0,01 | fraco |
| Hue | SNV | 1 | 0,16 | 3,15 | 1,12 | 1,08 | +0,14 | −0,49 | 0,02 | fraco |
| b\* | SNV | 2 | 0,14 | 2,54 | 1,11 | 1,24 | −0,08 | −1,21 | 0,02 | fraco |
| Chroma | bruto | 1 | −0,07 | 4,33 | 0,99 | 0,65 | −0,30 | −3,43 | 0,11 | fraco |
| a\* | bruto | 1 | −0,07 | 4,50 | 0,99 | 0,58 | −0,29 | −2,17 | 0,14 | fraco |
| Firmness | SNV+D2 | 1 | −0,13 | 1,285 | 0,97 | 1,56 | −0,74 | −3,39 | 0,32 | fraco |
| Titratable acidity | SNV+D1 | 1 | −0,14 | 0,069 | 0,96 | 0,97 | −0,34 | −0,35 | 0,24 | fraco |
| SS/AT | SNV+D2 | 1 | −0,15 | 1,998 | 0,96 | 0,79 | −0,92 | **−51,08** | 0,44 | fraco |

Grades completas: `resultados_mean/grid_<carac>.csv`.

---

## 3. Interpretação

### 3.1 Fruit length na média é o melhor resultado de toda a série

R²cv = 0,96 (RPD 5,18, "excelente" por larga margem), `r_within` **+0,68**, `R²_loco` **+0,56**. É o único
caso em toda a análise (O1–O4 + média) em que um alvo morfológico combina R²cv altíssimo com sinal real
dentro de cultivar **e** generalização para cultivar não visto. Nenhuma posição isolada chega perto: o melhor
R²cv de comprimento numa posição única foi O3 (0,77), mas com `R²_loco` negativo (−0,12). **Média das 4 vistas
cancela o ruído específico de cada orientação e revela um sinal geométrico consistente.**

### 3.2 C/D também "excelente" — mas com ressalva

R²cv 0,86, `R²_loco` +0,81 (o 2º melhor de toda a série), porém `r_within` ≈ 0 (**−0,03**). Isso é um padrão
diferente do de comprimento: o modelo generaliza bem entre cultivares (prevê corretamente o C/D médio de um
cultivar não visto), mas **não** explica a variação fruto-a-fruto dentro do mesmo cultivar. Interpretação mais
provável: C/D varia de forma consistente e "linear" com o cultivar (correlação forte com a assinatura
espectral média do tipo), então LOCO ainda funciona bem mesmo sendo essencialmente uma relação
cultivar→C/D — não é o mesmo tipo de evidência "composicional" que temos para o comprimento. Tratar como
**achado promissor mas a confirmar com mais frutos por cultivar**, não como calibração validada.

### 3.3 O sinal de cor encontrado em O3 desaparece na média

| Alvo | r_within O3 | R²_loco O3 | r_within média | R²_loco média |
|---|:--:|:--:|:--:|:--:|
| L\* | **+0,82** | **+0,80** | +0,30 | −3,01 |
| a\*/b\* | +0,53 | +0,32 | +0,21 | −0,63 |
| Hue | +0,45 | +0,12 | +0,14 | −0,49 |
| SS | +0,30 | +0,46 | −0,18 | −3,64 |

Média com as outras 3 orientações **dilui/anula** o sinal composicional que O3 capturava sozinha para cor e
qualidade. Isso é coerente com a hipótese de que o sinal de L\* em O3 é ligado à geometria específica daquela
vista (ângulo de captura em relação à insolação/pigmentação da casca), que se perde ao promediar com O1/O2/O4.

### 3.4 pH e Vit. C — mesma conclusão de sempre, agravada

`pH`: `r_within` ≈ 0, `R²_loco` −2,39 (o pior entre as posições "puras", só perdendo para O2). `Vit. C`:
`R²_loco` −7,06, muito pior que O1 (+0,21) — a média não ajuda nenhum dos dois; **O1 permanece a única fonte
de sinal real para Vit. C**.

### 3.5 SS/AT: colapso extremo

`R²_loco` = **−51,08**, o pior valor de toda a análise (pior até que o de O2 para Chroma, −50,0). Não usar.

---

## 4. Comparação final — O3 vs. média

| Aspecto | O3 (posição única) | Média das 4 |
|---|---|---|
| Melhor achado | L\* (excelente, real) | Fruit length (excelente, real) |
| 2º melhor achado | a\*/b\*, SS, Hue (fracos, reais) | C/D (forte, mas r_within~0) |
| Sinal de cor/qualidade | 5 alvos com sinal real | nenhum (diluído) |
| Sinal morfológico | fraco/confundido | **muito forte** (comprimento, C/D) |

**Conclusão:** as duas abordagens são complementares, não substitutas. **A média das 4 posições é claramente
superior para morfologia** (comprimento, e com ressalva C/D), enquanto **O3 isolada é a única fonte de sinal
real para cor e qualidade interna** (L\*, a\*/b\*, Hue, SS). Um protocolo prático poderia usar a média das 4
vistas para comprimento/C/D e o espectro de O3 especificamente para L\*.

---

## 5. Próximos passos

Ver relatório consolidado [RESULTADOS_CONSOLIDADO.md](RESULTADOS_CONSOLIDADO.md).
