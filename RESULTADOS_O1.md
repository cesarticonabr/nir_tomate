# Resultados — Análise NIRS da posição O1 (stem-end view)

**Predição das 16 características destrutivas do bloco P2 · Setembro de 2026**

Script: [analise_O1.R](analise_O1.R) · Saídas: [resultados_O1/](resultados_O1/)

---

## 1. Dados e método

| Item | Valor |
|------|-------|
| Espectros | posição **O1** apenas — 1 espectro por fruto |
| Amostras | **21 frutos** (Italiano/TI, Holandês/TH, Salada/TS — 7 cada) |
| Faixa espectral | 450–2450 nm (4001 bandas; extremos ruidosos removidos) |
| Pré-processamentos testados | bruto, SNV, SNV+SG 1ª deriv., SNV+SG 2ª deriv., detrend |
| Modelo | PLSR, 1–6 variáveis latentes (nLV pelo mínimo de RMSECV) |
| Validação | Leave-One-Fruit-Out (LOO, 21 folds) |
| Controles | teste de permutação (99×) · leave-one-cultivar-out · correlação dentro de cultivar |

---

## 2. Glossário de abreviaturas

### 2.1 As 16 características de referência

| Sigla | Nome na planilha | Significado | Unidade provável | Amplitude nos dados |
|-------|------------------|-------------|:----------------:|:-------------------:|
| **Length** | Fruit length | Comprimento do fruto (eixo pedúnculo–ápice) | mm | 46–73 |
| **Diameter** | Fruit diameter | Diâmetro equatorial | mm | 53–80 |
| **C_D** | C/D | Razão comprimento/diâmetro → **formato**: > 1 alongado, ≈ 1 redondo, < 1 achatado | adimensional | 0,73–1,29 |
| **MF** | MF | Massa fresca (peso) do fruto | g | 78–200 |
| **L\*** | L* | Luminosidade CIELab: 0 = preto, 100 = branco | adimensional | 48–59 |
| **a\*** | a* | Eixo verde(−)↔vermelho(+) CIELab. Sobe com o amadurecimento (licopeno) | adimensional | 26–49 |
| **b\*** | b* | Eixo azul(−)↔amarelo(+) CIELab | adimensional | 29–40 |
| **a_b** | a*/b* | Razão a\*/b\* — índice clássico de cor/maturação do tomate (quanto maior, mais vermelho) | adimensional | 0,84–1,46 |
| **Hue** | Hue | Ângulo de tonalidade h° = atan2(b\*, a\*). ~0° vermelho puro; **diminui** conforme o fruto amadurece | graus (°) | 33–50 |
| **Chroma** | Chroma | Saturação/pureza da cor C\* = √(a\*² + b\*²). Quanto maior, cor mais viva | adimensional | 41–63 |
| **Firmness** | Firmness | Firmeza da polpa (resistência à penetração/compressão) | N ou kgf (depende do instrumento) | 3,0–7,4 |
| **pH** | pH | pH do suco/polpa | — | 4,19–4,40 |
| **VitC** | Vit. C | Teor de vitamina C (ácido ascórbico) | mg / 100 g | 56–149 |
| **SS** | Total soluble solids | Sólidos solúveis totais (essencialmente açúcares) — o "grau Brix" | °Brix | 3,2–5,0 |
| **AT** | Titratable acid | Acidez titulável (ácidos orgânicos, sobretudo cítrico) | % ácido cítrico (ou g/100 mL) | 0,29–0,54 |
| **SS_AT** | SS/AT ratio | Razão sólidos solúveis / acidez — **índice de sabor** (equilíbrio doce/ácido) | adimensional | 6,7–14,0 |

> Grupos: **Morfologia** = Length, Diameter, C_D, MF · **Cor (CIELab)** = L\*, a\*, b\*, a_b, Hue, Chroma ·
> **Qualidade físico-química** = Firmness, pH, VitC, SS, AT, SS_AT.

### 2.2 Cultivares

| Sigla | Tipo | Formato típico |
|-------|------|----------------|
| **TI** | Italiano (saladete / "roma") | alongado, C/D ≈ 1,1–1,3 |
| **TH** | Holandês (tomate de cacho / rama) | redondo-pequeno, C/D ≈ 0,85 |
| **TS** | Salada | grande e achatado, C/D ≈ 0,75–0,85 |

### 2.3 Espectroscopia e pré-processamento

| Sigla | Significado |
|-------|-------------|
| **NIR / NIRS** | Espectroscopia no infravermelho próximo (near-infrared) |
| **O1** | Orientação de captura 1 — fruto na vertical com a **região basal (pedúnculo)** voltada ao sensor ("stem-end view") |
| **nm** | Nanômetro — unidade de comprimento de onda |
| **bruto / raw** | Espectro sem nenhum tratamento |
| **SNV** | *Standard Normal Variate* — centra e escala cada espectro individualmente; corrige efeitos de espalhamento de luz e de linha de base entre frutos |
| **SG** | Filtro *Savitzky-Golay* — suaviza e/ou deriva o espectro ajustando um polinômio local |
| **D1 / D2** | 1ª / 2ª derivada (via SG). D1 realça inclinações; D2 realça picos e remove tendência linear |
| **detrend** | SNV seguido de remoção de uma tendência polinomial ao longo do espectro |

### 2.4 Modelagem e validação

| Sigla | Significado |
|-------|-------------|
| **PLSR / PLS** | *Partial Least Squares Regression* — regressão que cria poucos componentes ("variáveis latentes") combinando os ~4000 comprimentos de onda; padrão em quimiometria NIR |
| **LV / nLV** | Número de variáveis latentes (componentes) usadas no modelo PLS |
| **LOO** | *Leave-One-Out* — aqui *Leave-One-Fruit-Out*: 21 ajustes, cada um deixando 1 fruto de fora e prevendo-o |
| **LOCO** | *Leave-One-Cultivar-Out* — treina em 2 cultivares e prevê o 3º (3 rodadas) |
| **CV** | Validação cruzada (*cross-validation*) |
| **teste de permutação / y-randomization** | Embaralha o alvo centenas de vezes e refaz a validação, para saber qual R² se obteria "por acaso" |

### 2.5 Métricas

| Métrica | Fórmula | Como ler |
|---------|---------|----------|
| **R²cv** | 1 − Σ(obs−pred)² / Σ(obs−média)² | Fração da variância explicada **na validação**. 1 = perfeito · 0 = igual a chutar a média · **< 0 = pior que a média** |
| **RMSECV** | √[Σ(obs−pred)² / n] | Erro típico de predição, **na unidade do alvo** |
| **RPD** | desvio-padrão(y) / RMSECV | Quantas vezes o erro é menor que a variação natural. Critério de Williams (abaixo) |
| **RPIQ** | IQR(y) / RMSECV | Igual ao RPD mas usa a amplitude interquartil — **mais confiável quando os dados não são normais / n é pequeno** |
| **bias** | média(pred − obs) | Erro sistemático (tendência a superestimar/subestimar) |
| **slope** | inclinação de obs ~ pred | 1 = ideal; < 1 = predições "achatadas" em direção à média |
| **r_within** | correlação obs×pred **após remover a média de cada cultivar** | Mede se o espectro capta a variação **fruto-a-fruto dentro do mesmo tipo**. **≈ 0 → o modelo só distingue cultivares**, não calibra composição. > 0 → há sinal real além do efeito varietal |
| **R²_loco** | R² do leave-one-cultivar-out | **Muito negativo → o modelo não generaliza para um cultivar novo** (o que "funcionava" era o contraste entre tipos) |
| **p_perm** | proporção de permutações com R² ≥ o observado | **> 0,05 → o resultado é indistinguível do acaso** |

**Classificação de RPD (Williams, 2001):**

| RPD | Classe | Uso prático |
|:---:|:------:|-------------|
| > 2,5 | excelente | predição quantitativa confiável |
| 2,0–2,5 | bom | predição quantitativa aproximada |
| 1,5–2,0 | razoável | serve para triagem / tendência, não para valor exato |
| < 1,5 | **fraco** | **não recomendado para predição** |

---

## 3. Tabela mestra (ordenada por R²cv)

| Característica | Pré-proc. | nLV | R²cv | RMSECV | RPD | RPIQ | r_within | R²_loco | p_perm | Williams |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| C/D | SNV+D2 | 4 | **0,72** | 0,092 | 1,94 | 3,36 | +0,16 | −0,27 | 0,01 | razoável |
| pH | SNV | 6 | 0,55 | 0,047 | 1,52 | 2,78 | +0,16 | −1,21 | 0,01 | razoável |
| Vit. C | bruto | 5 | 0,53 | 13,24 | 1,50 | 1,60 | **+0,52** | **+0,21** | 0,01 | razoável |
| Fruit length | SNV | 6 | 0,51 | 5,91 | 1,47 | 2,86 | −0,07 | −3,65 | 0,01 | fraco |
| Fruit diameter | SNV+D2 | 6 | 0,48 | 5,98 | 1,43 | 2,24 | +0,03 | −1,85 | 0,01 | fraco |
| MF (massa fresca) | detrend | 2 | 0,45 | 28,2 | 1,38 | 2,55 | −0,21 | −1,59 | 0,01 | fraco |
| b* | SNV+D2 | 2 | 0,27 | 2,35 | 1,20 | 1,34 | +0,22 | +0,32 | 0,02 | fraco |
| SS (sólidos solúveis) | SNV+D2 | 2 | 0,18 | 0,36 | 1,13 | 1,67 | +0,06 | −0,21 | 0,03 | fraco |
| L* | SNV+D2 | 2 | 0,06 | 2,90 | 1,05 | 1,52 | −0,04 | −0,61 | 0,04 | fraco |
| a*/b* | SNV | 4 | 0,03 | 0,14 | 1,04 | 1,14 | +0,16 | −1,23 | 0,03 | fraco |
| Chroma | SNV+D2 | 1 | 0,01 | 4,17 | 1,03 | 0,67 | +0,08 | +0,06 | 0,07 | fraco |
| Firmness | SNV+D2 | 1 | −0,02 | 1,23 | 1,01 | 1,63 | +0,12 | −1,12 | 0,14 | fraco |
| Hue | SNV | 4 | −0,03 | 3,46 | 1,01 | 0,98 | +0,16 | −1,15 | 0,07 | fraco |
| SS/AT | SNV+D2 | 1 | −0,07 | 1,93 | 0,99 | 0,82 | −0,21 | +0,04 | 0,15 | fraco |
| a* | SNV+D2 | 1 | −0,10 | 4,56 | 0,98 | 0,57 | −0,13 | −0,12 | 0,11 | fraco |
| Titratable acidity | SNV | 1 | −0,11 | 0,068 | 0,97 | 0,98 | −0,16 | +0,07 | 0,31 | fraco |

Grade completa de pré-processamentos por característica: `resultados_O1/grid_<carac>.csv`.

---

## 4. Interpretação geral

### 4.1 Nenhuma calibração utilizável a partir de O1 sozinha

O melhor RPD é **1,94** (C/D) — abaixo do limiar de 2,0 ("bom"). Todas as demais características ficam em
**"fraco"**. Com 1 espectro por fruto e n = 21, a posição O1 isolada **não** produz modelos de predição
quantitativa confiáveis para nenhuma das 16 características.

### 4.2 O sinal aparente é contraste entre cultivares, não composição

As características com R²cv positivo (C/D, pH, comprimento, diâmetro, MF) mostram todas o mesmo padrão:

- **`r_within` ≈ 0** (ou negativo) → o espectro **não** explica a variação fruto-a-fruto dentro do cultivar;
- **`R²_loco` fortemente negativo** (−1,2 a −3,7) → o modelo **desaba** ao prever um cultivar que não viu.

Ou seja, o PLS aproveita as diferenças médias entre TI/TH/TS (formato, tamanho) e "chuta" a média do grupo —
o confundimento previsto na metodologia. A PCA não-supervisionada confirma: os cultivares **não** se separam
de forma limpa no espaço espectral de O1 (PC1 = 83 %, dominada por um outlier — fruto THR4).

### 4.3 Única exceção com sinal genuíno: Vitamina C

`Vit. C` é a única com **`r_within` = +0,52**, **`R²_loco` = +0,21** e **`p_perm` = 0,01** — há indício de que
o espectro O1 carrega informação real sobre a variação de vitamina C **entre frutos do mesmo tipo**.
**Ressalva:** o fruto **THR4** tem Vit. C = 148,8 (≈ 1,5× o segundo maior, 104) e também é o outlier espectral
da PCA. Esse ponto de alta alavanca infla o R². **Reajustar sem THR4** antes de confirmar.

### 4.4 Sem sinal nenhum

`a*`, `Titratable acidity` e `SS/AT` têm **R²cv negativo e `p_perm` não significativo** (0,11–0,31): o
espectro O1 não prediz essas variáveis nem por confundimento.

### 4.5 Aviso técnico

Para várias características de R² ≈ 0 o "vencedor" foi SNV+2ª derivada com poucas LV — típico de **sobreajuste
a ruído**. O nLV foi escolhido na mesma LOO, o que torna o R²cv da tabela **levemente otimista**; os sinais
confiáveis são `p_perm`, `R²_loco` e `r_within`, não o R²cv isolado.

---

## 5. Interpretação característica por característica

### 5.1 Morfologia (Length, Diameter, C_D, MF)

| | Resultado | Leitura |
|---|---|---|
| **C_D** (formato) | R²cv 0,72 · RPD 1,94 · RPIQ 3,36 · r_within +0,16 · R²_loco −0,27 | Melhor caso do estudo, mas ainda "razoável". O RPIQ alto e o R²_loco só levemente negativo sugerem que aqui o confundimento é **menos severo** que nas outras morfológicas — o formato tem alguma assinatura espectral (o formato muda a geometria de reflexão). Mesmo assim, não chega a "bom" e o r_within é baixo: serve para **triagem grosseira de formato**, não para medir C/D de um fruto. |
| **Length / Diameter** | R²cv 0,48–0,51 · RPD ~1,45 · r_within ≈ 0 · **R²_loco −1,8 a −3,7** | Caso-escola de confundimento: o modelo "prevê" comprimento porque os 3 cultivares têm comprimentos médios muito diferentes (Italiano longo, Holandês curto). Ao remover o efeito de cultivar, **não sobra nada** (r_within ≈ 0), e ao prever um cultivar novo o erro explode. **Sem valor prático.** |
| **MF** (massa) | R²cv 0,45 · RPD 1,38 · r_within −0,21 · R²_loco −1,6 | Idem. A massa é quase função do tamanho → mesmo confundimento. r_within negativo indica que, dentro do tipo, o modelo até "erra o sentido". **Sem valor.** |

**Conclusão morfologia:** não usar O1 para estimar dimensões/peso de frutos individuais. Só C/D tem um resíduo
de sinal, e ainda assim fraco.

### 5.2 Cor CIELab (L\*, a\*, b\*, a_b, Hue, Chroma)

| | Resultado | Leitura |
|---|---|---|
| **b\*** (amarelo) | R²cv 0,27 · RPD 1,20 · **R²_loco +0,32** (positivo!) · r_within +0,22 | O único parâmetro de cor com R²_loco positivo e r_within > 0 — indício fraco de sinal real, coerente com a região visível estar no espectro. Ainda assim RPD 1,20 = "fraco". |
| **L\*** (luminosidade) | R²cv 0,06 | Praticamente sem predição. |
| **a\*** (vermelho) | R²cv **−0,10** · p_perm 0,11 | **Sem sinal.** Surpreende (a\* é o eixo do licopeno, deveria aparecer no visível), mas a faixa de a\* é estreita e o fruto **TSR2** (a\* = 26 contra 40–49 nos demais) é um outlier de referência que desestabiliza tudo. |
| **a_b, Hue, Chroma** | R²cv ≈ 0 a −0,03 · RPIQ 0,67–1,14 | São combinações não-lineares de a\* e b\*; herdam o problema de a\* e a faixa estreita. **Sem valor.** |

**Conclusão cor:** O1 no espectro completo (450–2450 nm) não calibra cor. Vale um teste focado **só na região
visível (400–1000 nm)** e **depois de remover/verificar o outlier TSR2**, antes de descartar de vez —
principalmente a\* e a_b, que têm base física (carotenoides).

### 5.3 Qualidade físico-química (Firmness, pH, VitC, SS, AT, SS_AT)

| | Resultado | Leitura |
|---|---|---|
| **Vit. C** | R²cv 0,53 · RPD 1,50 · **r_within +0,52** · **R²_loco +0,21** · p_perm 0,01 | **O achado mais promissor.** É a única característica onde o espectro explica variação **dentro** do cultivar e generaliza para cultivar novo. Mecanismo plausível: ácido ascórbico tem bandas O–H/C–H no NIR. **Mas** depende fortemente do fruto THR4 (valor extremo). Próximo passo obrigatório: reajustar sem THR4; se o r_within continuar ~0,4–0,5, vale desenvolver essa calibração. |
| **pH** | R²cv 0,55 · RPD 1,52 · r_within +0,16 · **R²_loco −1,21** | R²cv parece bom, mas o R²_loco negativo denuncia confundimento: os cultivares têm pH médio ligeiramente diferente (TH ~4,35 vs TI/TS ~4,22) e o modelo usa isso. Sinal intrínseco fraco. |
| **SS** (°Brix) | R²cv 0,18 · RPD 1,13 · r_within +0,06 | Fraco. Ao contrário do esperado (SS costuma ser um bom alvo NIR), aqui a faixa de variação é pequena (3,2–5,0 °Brix) e n = 21 é insuficiente. |
| **Firmness** | R²cv −0,02 · RPD 1,01 · p_perm 0,14 | **Sem sinal** em O1. |
| **AT** (acidez) | R²cv −0,11 · p_perm 0,31 | **Sem sinal** — ácidos em baixa concentração, difícil por NIR e impossível com este n. |
| **SS_AT** (índice de sabor) | R²cv −0,07 · p_perm 0,15 | **Sem sinal.** É uma razão (SS/AT) → propaga o erro de ambos. |

**Conclusão qualidade:** só a **vitamina C** merece continuidade (com verificação de outlier). pH, SS,
firmeza, AT e SS/AT não são preditíveis a partir de O1 com os dados atuais.

---

## 6. Conclusão e próximos passos

**Conclusão:** a posição **O1 isolada não serve** para calibrar as 16 características do bloco P2 com o
conjunto atual (n = 21, 1 espectro/fruto). O pouco que os modelos capturam é diferença varietal (confirmado
por `r_within` ≈ 0 e `R²_loco` negativo). Apenas a **vitamina C** mostra um sinal fraco porém real de
composição, ainda dependente de verificação de outlier.

**Próximos passos:**

1. **Comparar posições** — rodar o mesmo protocolo para O2, O3, O4, para a **média das 4 posições** e para a
   **concatenação** (METODOLOGIA_R_P2, Seções 7.2–7.3). A média deve elevar a relação sinal/ruído.
2. **Investigar outliers:** fruto **THR4** (Vit. C e espectro) e **TSR2** (a\*). Reajustar Vit. C sem THR4.
3. **Teste focado de cor:** só a região visível 400–1000 nm para a\*, a\*/b\*, Chroma.
4. **Não priorizar** `a*`, `Titratable acidity`, `SS/AT`, `Firmness` — sem sinal em O1.
5. Manter **leave-one-cultivar-out** + **teste de permutação** como critério de aceitação em todas as
   posições — o R²cv sozinho engana com n pequeno.
