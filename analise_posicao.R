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
