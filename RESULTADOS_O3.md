# Resultados — Análise NIRS da posição O3 (stem-end to the right)

**Predição das 16 características destrutivas do bloco P2 · Setembro de 2026**

Script: [analise_posicao.R](analise_posicao.R) (`Rscript analise_posicao.R O3`) · Saídas: [resultados_O3/](resultados_O3/)

> Glossário completo das abreviaturas (16 características, cultivares, SNV/D1/D2, PLSR, todas as métricas):
> ver **Seção 2 de [RESULTADOS_O1.md](RESULTADOS_O1.md)**. Lembrete rápido das colunas de controle:
> `r_within` — correlação obs×pred depois de remover a média de cada cultivar (**≈ 0 → o modelo só separa
> cultivares**). `R²_loco` — R² ao treinar em 2 cultivares e prever o 3º (**muito negativo → não
> generaliza**). `p_perm` — p do teste de permutação (**> 0,05 → indistinguível do acaso**).

---

## 1. Método (idêntico ao de O1/O2)

PLSR 1–6 LV · grid de 5 pré-processamentos (bruto, SNV, SNV+D1, SNV+D2, detrend) · 450–2450 nm ·
validação Leave-One-Fruit-Out (21 folds) · teste de permutação (99×) · leave-one-cultivar-out ·
correlação dentro de cultivar. n = 21 frutos (TI/TH/TS, 7 cada), 1 espectro por fruto.

---

## 2. Tabela mestra — O3 (ordenada por R²cv)

| Característica | Pré-proc. | nLV | R²cv | RMSECV | RPD | RPIQ | r_within | **R²_loco** | p_perm | Williams |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **L\*** | SNV | 5 | 0,79 | 1,382 | 2,21 | 3,20 | **+0,82** | **+0,80** | 0,01 | bom |
| C/D | SNV+D1 | 6 | 0,77 | 0,084 | 2,14 | 3,71 | +0,18 | −0,82 | 0,01 | bom |
| Fruit length | SNV+D1 | 6 | 0,77 | 4,09 | 2,12 | 4,14 | +0,32 | −0,12 | 0,01 | bom |
| pH | SNV+D1 | 1 | 0,57 | 0,046 | 1,55 | 2,84 | −0,00 | −0,60 | 0,01 | razoável |
| MF (massa fresca) | SNV+D1 | 5 | 0,50 | 26,9 | 1,45 | 2,67 | +0,02 | −2,14 | 0,01 | fraco |
| Fruit diameter | SNV+D2 | 3 | 0,47 | 6,05 | 1,41 | 2,21 | +0,35 | −1,64 | 0,01 | fraco |
| **a\*/b\*** | SNV | 2 | 0,45 | 0,106 | 1,38 | 1,52 | **+0,53** | **+0,32** | 0,01 | fraco |
| **SS (sólidos solúveis)** | SNV+D2 | 6 | 0,38 | 0,312 | 1,30 | 1,92 | **+0,30** | **+0,46** | 0,01 | fraco |
| **Hue** | SNV | 2 | 0,34 | 2,77 | 1,26 | 1,22 | **+0,45** | **+0,12** | 0,01 | fraco |
| **b\*** | detrend | 3 | 0,33 | 2,25 | 1,25 | 1,40 | **+0,37** | **+0,05** | 0,01 | fraco |
| Vit. C | SNV+D1 | 6 | 0,25 | 16,9 | 1,18 | 1,26 | +0,21 | −0,62 | 0,02 | fraco |
| Titratable acidity | SNV+D2 | 4 | 0,19 | 0,058 | 1,14 | 1,15 | +0,45 | −0,62 | 0,04 | fraco |
| SS/AT | SNV+D2 | 5 | 0,17 | 1,69 | 1,13 | 0,93 | +0,43 | −0,80 | 0,05 | fraco |
| Chroma | bruto | 1 | −0,04 | 4,28 | 1,00 | 0,65 | +0,05 | −0,73 | 0,12 | fraco |
| a\* | bruto | 1 | −0,06 | 4,46 | 1,00 | 0,58 | +0,02 | −0,66 | 0,10 | fraco |
| Firmness | SNV+D1 | 1 | −0,08 | 1,258 | 0,99 | 1,59 | −0,24 | −0,06 | 0,23 | fraco |

Grades completas: `resultados_O3/grid_<carac>.csv`.

---

## 3. Interpretação

### 3.1 O3 é a melhor posição encontrada até agora — e por um motivo real, não artefato

Ao contrário de O2, onde o R²cv subia mas o `R²_loco` desabava, em O3 **os dois indicadores sobem juntos**
para vários alvos. **L\* é o achado mais forte de toda a série** (O1, O2, O3): R²cv 0,79, `r_within` **+0,82**
e `R²_loco` **+0,80** — a calibração é quase tão boa dentro de cada cultivar quanto no conjunto todo, e
generaliza para um cultivar que o modelo não viu. Isso é evidência de **sinal de composição real**, não de
identidade varietal.

Outros quatro alvos de cor/qualidade mostram o mesmo padrão qualitativo (`r_within` **e** `R²_loco`
positivos, embora fracos): **a\*/b\*** (+0,53 / +0,32), **SS** (+0,30 / +0,46), **Hue** (+0,45 / +0,12) e
**b\*** (+0,37 / +0,05). Em O1 e O2 nenhum desses tinha `R²_loco` positivo.

### 3.2 Morfologia (C/D, comprimento) ainda mistura cultivar — mas bem menos que em O2

C/D e comprimento repetem o padrão de R²cv alto blindando confundimento varietal (`r_within` baixo, 0,18–0,32),
mas o grau de confundimento é **muito menor que em O2**: `R²_loco` de −0,82 e −0,12 em O3, contra **−4,68** e
**−29,5** em O2. Ainda não são calibrações utilizáveis, mas o espectro O3 carrega menos artefato geométrico
ligado ao cultivar do que O2 nessas variáveis.

### 3.3 pH — mesma conclusão nas três posições

`r_within` ≈ 0 (−0,00) e `R²_loco` negativo (−0,60): como em O1 e O2, o R²cv de pH é discriminação de
cultivar, não calibração de composição.

### 3.4 Vitamina C — O1 continua sendo a melhor posição

| Posição | r_within | R²_loco |
|---|:--:|:--:|
| O1 | **+0,52** | **+0,21** |
| O2 | +0,39 | −9,00 |
| O3 | +0,21 | −0,62 |

O3 é intermediário entre O1 (melhor) e O2 (pior/catastrófico) para Vit. C, mas não supera O1.

### 3.5 Sem sinal

`Firmness`, `a*`, `Chroma` — R²cv negativo e `p_perm` não significativo (0,10–0,23), como nas outras
posições.

---

## 4. Comparação O1 × O2 × O3

| Aspecto | O1 (stem-end) | O2 (blossom-end) | **O3 (stem-end direita)** |
|---|---|---|---|
| Cultivares na PCA (SNV) | misturados | separados quase perfeitamente | ver `pca_O3.png` |
| Melhor `R²_loco` positivo | Vit. C (+0,21) | nenhum | **L\* (+0,80)** |
| Nº de alvos com `r_within` **e** `R²_loco` > 0 | 1 (Vit. C) | 0 | **5 (L\*, a\*/b\*, SS, Hue, b\*)** |
| Confundimento em C/D (`R²_loco`) | −0,27 | **−4,68** | −0,82 |
| Confundimento em comprimento (`R²_loco`) | −3,65 | **−29,5** | −0,12 |
| Melhor achado geral | Vit. C fraco/real | nenhum real | **L\* forte/real** |

**Conclusão preliminar:** O3 é, até agora, a **posição de captura mais promissora**. É a única em que uma
característica (L\*) mostra sinal real forte (`R²_loco` alto e positivo), e é também a que menos confunde
cultivar com morfologia. Falta rodar O4 e a média das 4 posições antes de recomendar um protocolo final.

---

## 5. Próximos passos

1. **Rodar O4** (`Rscript analise_posicao.R O4`) e a **média das 4 posições** (`Rscript analise_posicao.R mean`).
2. Consolidar a tabela "característica × posição" (`R²_loco` + `r_within`) com as 4 posições completas.
3. **Investigar por que L\* funciona bem especificamente em O3** — inspecionar `resultados_O3/pca_O3.png` e
   `espectros_O3.png` para confirmar que não há o mesmo artefato de patamar de reflectância visto em O2.
4. Verificar o fruto **THR4** (outlier em O1/O2) também na PCA de O3.
5. Continuar priorizando **L\*** (O3), **Vit. C** (O1) e, agora, também **a\*/b\*, SS e Hue em O3** como
   candidatos com sinal real; manter `a*`, `Chroma`, `Firmness` fora de prioridade.
