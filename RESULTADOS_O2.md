# Resultados — Análise NIRS da posição O2 (blossom-end view)

**Predição das 16 características destrutivas do bloco P2 · Setembro de 2026**

Script: [analise_posicao.R](analise_posicao.R) (`Rscript analise_posicao.R O2`) · Saídas: [resultados_O2/](resultados_O2/)

> Glossário completo das abreviaturas (16 características, cultivares, SNV/D1/D2, PLSR, todas as métricas):
> ver **Seção 2 de [RESULTADOS_O1.md](RESULTADOS_O1.md)**. Lembrete rápido das colunas de controle:
> `r_within` — correlação obs×pred depois de remover a média de cada cultivar (**≈ 0 → o modelo só separa
> cultivares**). `R²_loco` — R² ao treinar em 2 cultivares e prever o 3º (**muito negativo → não
> generaliza**). `p_perm` — p do teste de permutação (**> 0,05 → indistinguível do acaso**).

---

## 1. Método (idêntico ao de O1)

PLSR 1–6 LV · grid de 5 pré-processamentos (bruto, SNV, SNV+D1, SNV+D2, detrend) · 450–2450 nm ·
validação Leave-One-Fruit-Out (21 folds) · teste de permutação (99×) · leave-one-cultivar-out ·
correlação dentro de cultivar. n = 21 frutos (TI/TH/TS, 7 cada), 1 espectro por fruto.

---

## 2. Tabela mestra — O2 (ordenada por R²cv)

| Característica | Pré-proc. | nLV | R²cv | RMSECV | RPD | RPIQ | r_within | **R²_loco** | p_perm | Williams |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| C/D | bruto | 5 | **0,88** | 0,062 | **2,91** | 5,04 | +0,12 | **−4,68** | 0,01 | excelente |
| pH | bruto | 6 | 0,82 | 0,030 | 2,40 | 4,38 | +0,31 | **−14,70** | 0,01 | bom |
| MF (massa fresca) | SNV+D1 | 6 | 0,74 | 19,3 | 2,02 | 3,73 | +0,20 | −2,83 | 0,01 | bom |
| Fruit diameter | SNV+D1 | 5 | 0,72 | 4,38 | 1,95 | 3,06 | +0,12 | **−4,03** | 0,01 | razoável |
| Fruit length | SNV+D2 | 2 | 0,65 | 4,98 | 1,74 | 3,39 | −0,28 | **−29,52** | 0,01 | razoável |
| L* | SNV | 5 | 0,44 | 2,22 | 1,37 | 1,99 | **+0,52** | −1,92 | 0,01 | fraco |
| Vit. C | bruto | 4 | 0,31 | 16,1 | 1,24 | 1,32 | +0,39 | **−9,00** | 0,01 | fraco |
| SS (sólidos solúveis) | SNV+D2 | 1 | 0,24 | 0,35 | 1,18 | 1,74 | −0,86 | **−27,97** | 0,01 | fraco |
| a*/b* | SNV+D1 | 3 | 0,06 | 0,14 | 1,05 | 1,16 | −0,24 | −1,55 | 0,05 | fraco |
| b* | SNV | 3 | 0,02 | 2,71 | 1,04 | 1,16 | +0,14 | −1,16 | 0,07 | fraco |
| Hue | SNV+D1 | 3 | −0,02 | 3,46 | 1,01 | 0,98 | −0,24 | −1,64 | 0,04 | fraco |
| SS/AT | bruto | 2 | −0,06 | 1,92 | 1,00 | 0,83 | +0,14 | −0,30 | 0,10 | fraco |
| Firmness | bruto | 4 | −0,07 | 1,26 | 0,99 | 1,59 | +0,42 | **−29,87** | 0,05 | fraco |
| Titratable acidity | SNV | 1 | −0,10 | 0,067 | 0,98 | 0,98 | −0,29 | −0,45 | 0,19 | fraco |
| Chroma | SNV+D2 | 2 | −0,12 | 4,43 | 0,97 | 0,63 | −0,45 | **−49,97** | 0,22 | fraco |
| a* | SNV | 1 | −0,13 | 4,61 | 0,97 | 0,56 | −0,64 | −0,05 | 0,24 | fraco |

Grades completas: `resultados_O2/grid_<carac>.csv`.

---

## 3. Interpretação

### 3.1 R²cv sobe muito, mas é uma armadilha

Em O2, C/D chega a R²cv 0,88 (RPD 2,91 = "excelente") e pH a 0,82 ("bom") — números **muito melhores que em
O1**. Porém o **`R²_loco`** dessas mesmas características **despenca para −4,7 (C/D), −14,7 (pH), −29,5
(comprimento), −28 (SS), −30 (firmeza), −50 (Chroma)**. Um R² de −50 significa que, ao prever um cultivar que
o modelo não viu, o erro é ~50× a variância do alvo. **Não há calibração nenhuma** — o que o modelo faz é
reconhecer o cultivar e devolver a média daquele grupo.

### 3.2 A causa: os espectros O2 carregam identidade varietal muito forte

- **PCA (`resultados_O2/pca_O2.png`):** os 3 cultivares se separam **quase perfeitamente** no espaço
  espectral de O2 (PC1 = 85 %). Em O1 eles estavam **misturados**.
- **Espectros brutos (`resultados_O2/espectros_O2.png`):** as 7 curvas do Italiano (TI) ficam num patamar de
  reflectância de ~1,5–2,1, **completamente separadas** de TH + TS (~0,3–1,5). A vista **apical (blossom-end)**
  do fruto alongado apresenta uma geometria muito diferente ao sensor → **deslocamento de linha de base
  ligado ao cultivar**.
- O pré-processamento **"bruto" (raw) vencer** para C/D e pH confirma o diagnóstico: o modelo está usando
  justamente esse patamar de reflectância, que é um artefato geométrico, não composição.

### 3.3 Sinal dentro de cultivar — ligeiramente melhor que O1 para alguns alvos

| Alvo | r_within O2 | r_within O1 | Comentário |
|------|:-----------:|:-----------:|------------|
| **L\*** (luminosidade) | **+0,52** | −0,04 | O2 capta variação de luminosidade dentro do tipo; O1 não. Ainda "fraco" (RPD 1,37). |
| **Firmness** | +0,42 | +0,12 | Sinal intra-cultivar, mas R²cv global negativo e R²_loco −30. Instável. |
| **Vit. C** | +0,39 | **+0,52** | **O1 é melhor para vitamina C** (r_within maior e R²_loco +0,2 vs −9,0 em O2). |
| **pH** | +0,31 | +0,16 | Algum sinal, mas dominado pelo confundimento (R²_loco −14,7). |

### 3.4 Sem sinal

`a*`, `Chroma`, `Titratable acidity`, `SS/AT` — R²cv negativo e `p_perm` não significativo (0,10–0,24).
`r_within` de `a*` e `SS` fortemente **negativo** (−0,64, −0,86): dentro do cultivar o modelo erra o sentido.

### 3.5 Outlier persistente

O fruto **THR4** é de novo o outlier extremo na PCA (PC2 ≈ 8) e tem um pico anômalo em ~1100 nm na 1ª
derivada. Está presente em todas as posições — precisa ser verificado na origem.

---

## 4. Comparação O1 × O2

| Aspecto | **O1** (base / stem-end) | **O2** (ápice / blossom-end) |
|---------|--------------------------|------------------------------|
| Cultivares na PCA (SNV) | misturados | **separados quase perfeitamente** |
| R²cv de morfologia + pH | 0,45–0,72 | 0,65–0,88 |
| R²_loco dos mesmos | −0,3 a −3,7 | **−2,8 a −29,5** |
| Nº de alvos "bom/excelente" (RPD) | 0 | 3 (C/D, pH, MF) — **todos espúrios** |
| Melhor caso real (r_within > 0 **e** R²_loco > 0) | Vit. C (+0,52 / +0,21) | **nenhum** |
| L\* dentro de cultivar (r_within) | −0,04 | +0,52 |
| Grau de confundimento com cultivar | moderado | **severo** |

**Conclusão:** a posição O2, isolada, é **pior** que O1 para calibração — o R²cv mais alto é inteiramente
discriminação de cultivar (comprovado pelos `R²_loco` de −4 a −50 e pela PCA). O único ponto a favor de O2 é
um sinal intra-cultivar um pouco melhor para **L\*** (luminosidade). Para **vitamina C**, **O1 é claramente
superior**.

Este resultado reforça a regra metodológica: **o R²cv sozinho engana** — a posição que "parece" melhor (O2)
é a mais contaminada. O critério de escolha de posição/protocolo deve ser **`R²_loco` + `r_within`**.

---

## 5. Próximos passos

1. **Rodar O3 e O4** (`Rscript analise_posicao.R O3` / `O4`) e a **média das 4** (`Rscript analise_posicao.R mean`).
2. **Consolidar** uma tabela única "característica × posição" usando `R²_loco` e `r_within` como critério —
   não o R²cv.
3. **Verificar o fruto THR4** na base de dados original (outlier em todas as posições).
4. Para **vitamina C** e **L\***: reajustar sem THR4 e testar a média das posições — são os dois únicos alvos
   com indício de sinal intra-cultivar (O1 para VitC, O2 para L\*).
5. Continuar **não priorizando** `a*`, `Chroma`, `Titratable acidity`, `SS/AT`, `Hue` — sem sinal em nenhuma
   posição até agora.
