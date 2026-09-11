# Resultados — Análise NIRS da posição O4 (stem-end to the left)

**Predição das 16 características destrutivas do bloco P2 · Setembro de 2026**

Script: [analise_posicao.R](analise_posicao.R) (`Rscript analise_posicao.R O4`) · Saídas: [resultados_O4/](resultados_O4/)

> Glossário completo: ver **Seção 2 de [RESULTADOS_O1.md](RESULTADOS_O1.md)**. `r_within` — correlação
> obs×pred após remover a média de cada cultivar (**≈ 0 → só separa cultivares**). `R²_loco` — R² ao treinar
> em 2 cultivares e prever o 3º (**muito negativo → não generaliza**). `p_perm` — p do teste de permutação.

---

## 1. Método (idêntico às demais posições)

PLSR 1–6 LV · grid de 5 pré-processamentos · 450–2450 nm · Leave-One-Fruit-Out (21 folds) · permutação (99×) ·
leave-one-cultivar-out · correlação dentro de cultivar. n = 21 frutos (TI/TH/TS, 7 cada).

---

## 2. Tabela mestra — O4 (ordenada por R²cv)

| Característica | Pré-proc. | nLV | R²cv | RMSECV | RPD | RPIQ | r_within | **R²_loco** | p_perm | Williams |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| pH | SNV+D2 | 6 | 0,77 | 0,033 | 2,15 | 3,92 | +0,05 | −0,91 | 0,01 | bom |
| Fruit diameter | SNV+D1 | 5 | 0,75 | 4,18 | 2,04 | 3,21 | +0,50 | −0,50 | 0,01 | bom |
| Fruit length | SNV+D2 | 2 | 0,73 | 4,38 | 1,98 | 3,86 | +0,38 | −0,57 | 0,01 | razoável |
| MF (massa fresca) | SNV+D1 | 5 | 0,70 | 20,8 | 1,88 | 3,47 | +0,45 | −1,06 | 0,01 | razoável |
| C/D | SNV+D2 | 3 | 0,64 | 0,105 | 1,71 | 2,95 | +0,27 | −1,06 | 0,01 | razoável |
| a\*/b\* | SNV | 1 | 0,35 | 0,115 | 1,27 | 1,40 | +0,45 | +0,03 | 0,01 | fraco |
| Hue | SNV | 1 | 0,26 | 2,95 | 1,19 | 1,15 | +0,38 | −0,04 | 0,01 | fraco |
| L\* | SNV | 1 | 0,26 | 2,57 | 1,19 | 1,72 | +0,30 | −0,01 | 0,01 | fraco |
| Vit. C | SNV+D2 | 2 | 0,11 | 18,3 | 1,09 | 1,16 | −0,20 | −1,15 | 0,05 | fraco |
| b\* | SNV+D1 | 1 | 0,02 | 2,71 | 1,04 | 1,16 | −0,09 | −0,30 | 0,07 | fraco |
| Firmness | SNV+D2 | 1 | −0,04 | 1,233 | 1,01 | 1,62 | −0,09 | +0,14 | 0,16 | fraco |
| a\* | bruto | 1 | −0,04 | 4,42 | 1,01 | 0,59 | +0,08 | −0,36 | 0,06 | fraco |
| Chroma | bruto | 1 | −0,05 | 4,28 | 1,00 | 0,65 | +0,04 | −0,23 | 0,08 | fraco |
| Titratable acidity | SNV+D1 | 1 | −0,08 | 0,067 | 0,98 | 0,99 | −0,05 | −0,25 | 0,16 | fraco |
| SS | bruto | 1 | −0,09 | 0,414 | 0,98 | 1,45 | −0,41 | −0,26 | 0,19 | fraco |
| SS/AT | bruto | 1 | −0,15 | 1,993 | 0,96 | 0,79 | −0,20 | −0,61 | 0,45 | fraco |

Grades completas: `resultados_O4/grid_<carac>.csv`.

---

## 3. Interpretação

### 3.1 O4 volta ao padrão de confundimento (nível O1/O2), sem repetir o achado de O3

Nenhuma característica em O4 tem `R²_loco` claramente positivo. As morfológicas (pH, diâmetro, comprimento,
MF, C/D) têm R²cv alto (0,64–0,77) mas `R²_loco` sempre negativo (−0,50 a −1,06) — menos catastrófico que O2,
mas sem generalizar. `Diameter` tem o melhor `r_within` isolado da série para essa variável (+0,50), porém
ainda com `R²_loco` −0,50: sinal parcial, não calibração limpa.

### 3.2 O achado de O3 (L\*) não se repete em O4

`L*` em O4: R²cv 0,26, `r_within` +0,30, `R²_loco` −0,01 (praticamente zero) — muito abaixo do resultado de O3
(R²cv 0,79 / +0,82 / +0,80). Confirma que o sinal de L\* encontrado em O3 é **específico daquela orientação**
de captura, não uma propriedade geral do fruto.

### 3.3 a\*/b\* e Hue: sinal residual, mas mais fraco que em O3

`a*/b*`: `r_within` +0,45 (próximo do valor de O3, +0,53) mas `R²_loco` apenas +0,03 (quase zero, contra +0,32
em O3). `Hue`: `r_within` +0,38 mas `R²_loco` −0,04. Direção do sinal é a mesma de O3, porém mais fraca e sem
generalização clara.

### 3.4 pH e Vit. C — conclusões reforçadas

`pH`: `r_within` ≈ 0 (+0,05) e `R²_loco` −0,91 — quinta posição seguida (contando O1, O2, O3) confirmando que
o R²cv de pH é discriminação de cultivar. `Vit. C`: `r_within` **negativo** (−0,20) em O4, pior que em
qualquer outra posição — reforça que **O1 é a única posição com sinal real de Vit. C**.

---

## 4. Comparação O1 × O2 × O3 × O4

| Aspecto | O1 | O2 | **O3** | O4 |
|---|:--:|:--:|:--:|:--:|
| Melhor `R²_loco` positivo | Vit. C (+0,21) | nenhum | **L\* (+0,80)** | nenhum |
| Nº alvos com `r_within` **e** `R²_loco` > 0 | 1 | 0 | **5** | 1 (a*/b*, marginal +0,03) |
| Confundimento em C/D (`R²_loco`) | −0,27 (melhor) | −4,68 | −0,82 | −1,06 |
| Confundimento em comprimento (`R²_loco`) | −3,65 | −29,5 | **−0,12 (melhor)** | −0,57 |

**O3 continua sendo a posição isolada mais promissora.** O4 não traz nenhum achado novo — repete, em versão
atenuada, tanto o confundimento morfológico de O2 quanto os traços fracos de cor de O3, sem superar nenhum
dos dois.

---

## 5. Próximos passos

Ver relatório consolidado [RESULTADOS_CONSOLIDADO.md](RESULTADOS_CONSOLIDADO.md), que reúne O1–O4 e a média
das 4 posições em uma única tabela característica × posição.
