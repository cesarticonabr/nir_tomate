# Metodologia - Predicao de Parametros de Tomate por Espectroscopia NIRS

## 1. Dados

**Fonte:** Planilha `Capturas_tomate_NIRS_16jun26_corrigido.xlsx` com 2 abas:

| Aba | Conteudo | Dimensao |
|-----|----------|----------|
| **Capturas_NIRS** | 45 espectros de reflectancia (colunas) x 4200 comprimentos de onda (linhas) | 4200 x 46 |
| **Dados_analise_destrutiva** | 9 parcelas com valores de referencia (AT, Firm, pH, SS, etc.) | 9 x 12 |

**Espectros:** 400-2500 nm, passo de 0.5 nm. Cada espectro = 1 fruto.

**Estrutura experimental:** 3 tratamentos (T1=italiano, T2=cereja, T3=?) x 3 repeticoes (R1-R3) x 5 frutos (F1-F5) = **45 frutos**. Os dados destrutivos foram medidos **por parcela** (1 valor para cada 5 frutos). Isso cria um desafio: 45 espectros mas apenas 9 valores independentes de referencia.

## 2. Pre-processamento Espectral

```python
def snv(X):
    return (X - X.mean()) / X.std()
```

**Standard Normal Variate (SNV):** cada espectro e centrado (subtrai a media) e escalado (divide pelo desvio padrao). Remove efeitos de linha de base e variacoes de intensidade entre amostras.

**Savitzky-Golay (1a derivada):** opcionalmente aplicada sobre o SNV com janela=11, ordem=2. Remove tendencias de linha de base e resolve picos sobrepostos.

**Nao foram usados:** filtros de suavizacao adicional, correcao de espalhamento multiplicativo (MSC), ou selecao manual de faixas espectrais.

## 3. Estrutura de Validacao

**Problema:** 45 espectros mas apenas 9 valores independentes de referencia (5 frutos compartilham o mesmo valor).

**Solucao: GroupKFold com grupos = parcelas**

```
Fold 1: treino [8 parcelas = 40 frutos], teste [1 parcela = 5 frutos]
Fold 2: treino [8 parcelas = 40 frutos], teste [1 parcela = 5 frutos]
...
```

Isso garante que os 5 frutos de uma mesma parcela **nunca** sao separados entre treino e teste. Sem isso, teriamos **falsa replicacao** e R2 artificialmente inflados.

**Validacao conservadora adicional:** medias espectrais dos 5 frutos por parcela -> 9 amostras -> Leave-One-Out Cross-Validation (LOOCV).

## 4. Pipeline de Machine Learning

```
Espectros (45 x 4200)
    | SNV
Dados pre-processados
    | GroupKFold (5 folds, 10 repeticoes)
Para cada fold:
    | StandardScaler (centrar + escalar)
    | PLSRegression (1 a 15 componentes)
    | Metricas: R2, RMSE, RPD
```

### Por que PLS?

- **Partial Least Squares Regression** e o padrao ouro para espectroscopia NIR
- Cria componentes latentes que maximizam a covariancia entre X (espectros) e y (parametro alvo)
- Lida naturalmente com **alta dimensionalidade** (4200 features >> 45 amostras)
- Lida com **multicolinearidade** (comprimentos de onda vizinhos sao altamente correlacionados)
- Modelo **interpretavel** (loadings mostram comprimentos de onda importantes)

### Outros modelos testados

- **Random Forest:** testado para AT, mas descartado por ser muito lento (3 min/configuracao) com mesma performance fraca que PLS
- **SVR:** R2 negativo (pior que chutar a media)
- **Ridge / OLS:** usados apenas na validacao LOOCV com 9 medias de parcela

## 5. Metricas de Avaliacao

| Metrica | Formula | Interpretacao |
|---------|---------|---------------|
| **R2** | 1 - S(yi-yi_hat)2 / S(yi-y_bar)2 | Proporcao da variancia explicada. 1 = perfeito, 0 = igual a media, <0 = pior que media |
| **RMSE** | sqrt(S(yi-yi_hat)2 / n) | Raiz do erro quadratico medio. Na mesma unidade do alvo |
| **RPD** | DP(y) / RMSE | Relacao de Desempenho Residual. Quanto maior, melhor |

### Classificacao RPD (Williams, 2001)

| RPD | Classificacao | Significado |
|:---:|:------------:|-------------|
| > 2.5 | **Excelente** | Modelo robusto para predicao quantitativa |
| 2.0 - 2.5 | **Bom** | Predicao quantitativa aproximada |
| 1.5 - 2.0 | **Razoavel** | Correlacao, mas baixa precisao |
| < 1.5 | **Fraco** | Modelo nao recomendado para predicao |

## 6. Parametros Analisados

| Grupo | Parametros | Melhor R2 | Classificacao |
|-------|-----------|:---------:|:-------------:|
| **Morfologia** | Comp, Diam.Equat., C:D | 0.930 - 0.937 | Excelente |
| **Textura** | Firm (Firmeza) | 0.765 | Bom |
| **Qualidade** | SS (Solidos Soluveis) | 0.751 | Bom |
| **Qualidade** | pH | 0.595 | Razoavel |
| **Qualidade** | Vit. C | 0.236 | Fraco |
| **Qualidade** | AT (Acidez) | 0.093 | Fraco |
| **Qualidade** | SS/AT (Razao) | < 0 | Inviavel |

## 7. Ferramentas Utilizadas

| Ferramenta | Funcao |
|-----------|--------|
| Python 3.10 | Linguagem principal |
| pandas / numpy | Manipulacao de dados |
| scikit-learn (PLS, RF, SVR, PCA, GroupKFold) | Machine Learning |
| scipy (savgol_filter, pearsonr, f_oneway) | Pre-processamento e estatistica |
| matplotlib | Visualizacao (graficos PNG) |
| python-docx | Geracao de relatorios Word |
| Git / GitHub | Versionamento e colaboracao |

## 8. Arquivos do Projeto

```
nirs_pH_SS_SSAT_pipeline.py   - Pipeline principal (reutilizado p/ todos parametros)
nirs_AT_pipeline.py            - Pipeline inicial para AT
nirs_AT_pipeline_v2.py         - Versao com analise exploratoria
nirs_AT_pipeline_rapido.py     - Versao otimizada
nirs_Firm_pipeline.py          - Pipeline para Firmeza
nirs_VitC_pipeline.py          - Pipeline para Vitamina C
gerar_relatorio*.py            - Scripts para gerar relatorios Word
Relatorio_*.docx               - Relatorios gerados
Capturas_tomate_NIRS_*.xlsx    - Dados experimentais
```
