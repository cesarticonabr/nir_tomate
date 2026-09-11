# #####################################################################
#  ANALISE NIRS - POSICAO O1 (stem-end view / vista da base do fruto)
#  Objetivo: verificar se o espectro NIR tomado na posicao O1 consegue
#  predizer as 16 caracteristicas medidas por analise destrutiva (P2).
#
#  DESENHO DOS DADOS
#  - 21 frutos independentes: 3 cultivares (TI = Italiano, TH = Holandes,
#    TS = Salada), 7 frutos cada.
#  - 1 espectro por fruto nesta analise (so a posicao O1).
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
suppressMessages({
  library(readxl); library(dplyr); library(stringr); library(tidyr)
  library(prospectr); library(pls); library(ggplot2)
})

set.seed(1)                  # reprodutibilidade (permutacoes)
pls.options(parallel = NULL) # PLSR em serie (evita instabilidade no Windows)

# --- Parametros do estudo ---------------------------------------------
ARQ      <- "Capturas_tomate_NIRS_11agosto (1).xlsx"
ABA_ESP  <- "O1 (stem-end view)"   # aba com os espectros desta posicao
OUT_DIR  <- "resultados_O1"        # pasta de saida (tabelas + graficos)
dir.create(OUT_DIR, showWarnings = FALSE)
WL_MIN <- 450; WL_MAX <- 2450      # manter so esta faixa (corta ruido nas pontas)
N_PERM <- 99                       # nº de permutacoes do teste y-randomization
NLV_MAX <- 6                       # nº maximo de variaveis latentes do PLS

# ---------------------------------------------------------------------
# 1. IMPORTACAO E MONTAGEM DA MATRIZ
# ---------------------------------------------------------------------

# 1a. Espectros: a aba vem com comprimento de onda nas LINHAS e frutos nas
#     COLUNAS. Precisamos do oposto (frutos nas linhas) para modelar.
esp    <- read_excel(ARQ, sheet = ABA_ESP)
wl_all <- esp[[1]]                  # 1a coluna = vetor de comprimentos de onda
X_all  <- t(as.matrix(esp[, -1]))   # transpoe -> 21 frutos x ~4200 bandas
cod    <- rownames(X_all)           # codigos: "TIR1O1", "THR5O1", ...

# 1b. Extrair cultivar e repeticao do codigo do espectro.
#     Regex: T(I|H|S) R(digito) O(digito).  m[,2]=tipo  m[,3]=repeticao
m      <- str_match(cod, "^(T[IHS])R([0-9])O[0-9]$")
Fruit  <- paste0(m[, 2], "R", m[, 3])   # id do fruto: "TIR1" (chave de juncao)
Type   <- factor(m[, 2])                # cultivar como fator (TI/TH/TS)

# 1c. Referencia destrutiva. Remove as linhas em branco do rodape da aba.
dest <- read_excel(ARQ, sheet = "Analise_destrutiva_P2")
dest <- dest[!is.na(dest$Treatments), ]

# Nomes das 16 colunas na planilha  ->  siglas curtas usadas no codigo
traits <- c("Fruit length","Fruit diameter","C/D","MF","L*","a*","b*","a*/b*",
            "Hue","Chroma","Firmness","pH","Vit. C","Total soluble solids",
            "Titratable acid","SS/AT ratio")
sig <- c("Length","Diameter","C_D","MF","L","a","b","a_b","Hue","Chroma",
         "Firmness","pH","VitC","SS","AT","SS_AT")

# Confere que todos os nomes existem na aba (evita erro silencioso).
stopifnot(all(traits %in% names(dest)))

# Constroi a matriz Y (21 x 16), forcando cada coluna a numerico.
# IMPORTANTE: acessar coluna a coluna por nome (dest[[nm]]); subsetar uma
# tibble por vetor de nomes com caracteres especiais ("a*/b*") pode
# corromper as colunas.
Y <- as.data.frame(lapply(traits, function(nm) suppressWarnings(as.numeric(dest[[nm]]))))
names(Y) <- sig
cat("NA por caracteristica:\n"); print(colSums(is.na(Y)))  # diagnostico

# 1d. Alinhar espectros <-> referencia pelo id do fruto.
ykey <- paste0(dest$Treatments, dest$Repetition)  # id do fruto na referencia
ord  <- match(Fruit, ykey)                        # posicao de cada espectro em 'dest'
Ymat <- Y[ord, , drop = FALSE]                    # Y reordenada na ordem dos espectros
stopifnot(!anyNA(ord), nrow(Ymat) == 21)          # todos casaram e sao 21

# 1e. Recorte espectral: mantem 450-2450 nm (descarta pontas ruidosas).
keep <- wl_all >= WL_MIN & wl_all <= WL_MAX
wl   <- wl_all[keep]
X    <- X_all[, keep]                              # matriz espectral final (21 x 4001)
cat(sprintf("Espectros O1: %d frutos x %d bandas (%.0f-%.0f nm)\n",
            nrow(X), ncol(X), min(wl), max(wl)))
cat("Frutos/cultivar: ", paste(names(table(Type)), table(Type), sep = "=", collapse = "  "), "\n\n")

# ---------------------------------------------------------------------
# 2. PRE-PROCESSAMENTOS ESPECTRAIS
#    Cada transformacao age LINHA A LINHA (um espectro por vez) e NAO
#    aprende parametros do conjunto -> pode ser aplicada uma unica vez
#    aqui, sem risco de vazamento de informacao para a validacao.
# ---------------------------------------------------------------------
W <- 15  # janela do filtro Savitzky-Golay (nº impar de pontos)
Xp <- list(
  raw     = X,                                                # sem tratamento
  SNV     = standardNormalVariate(X),                         # remove desvio de linha de base e de escala
  SNV_D1  = savitzkyGolay(standardNormalVariate(X), m = 1, p = 2, w = W),  # 1a derivada (realca inclinacoes)
  SNV_D2  = savitzkyGolay(standardNormalVariate(X), m = 2, p = 2, w = W),  # 2a derivada (realca picos)
  detrend = detrend(X, wav = wl)                              # SNV + remocao de tendencia polinomial
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
  press <- sum((y - yhat)^2); tss <- sum((y - mean(y))^2)
  rmse  <- sqrt(press / length(y))
  data.frame(R2cv = 1 - press / tss, RMSECV = rmse,
             RPD = sd(y) / rmse, RPIQ = IQR(y) / rmse,
             bias = mean(yhat - y), slope = unname(coef(lm(y ~ yhat))[2]))
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
  P <- matrix(NA_real_, n, nlv_max)
  for (i in seq_len(n)) {
    tr  <- setdiff(seq_len(n), i)                  # indices de treino (20 frutos)
    fit <- plsr(y ~ X, ncomp = nlv_max,
                data = data.frame(y = y[tr], X = I(Xm[tr, ])))
    pr  <- predict(fit, newdata = data.frame(X = I(Xm[i, , drop = FALSE])))
    P[i, ] <- pr[1, 1, ]                            # predicoes do fruto i (todos os nLV)
  }
  P
}

# 3c. loo_fixed(): mesma LOO, mas com nLV FIXO. Mais rapida - usada no
#     teste de permutacao (repetida centenas de vezes).
loo_fixed <- function(Xm, y, nlv) {
  n <- length(y); yh <- numeric(n)
  for (i in seq_len(n)) {
    tr  <- setdiff(seq_len(n), i)
    fit <- plsr(y ~ X, ncomp = nlv, data = data.frame(y = y[tr], X = I(Xm[tr, ])))
    yh[i] <- predict(fit, newdata = data.frame(X = I(Xm[i, , drop = FALSE])), ncomp = nlv)[1, 1, 1]
  }
  yh
}

# 3d. within_cultivar_r(): correlacao observado x predito DEPOIS de
#     remover a media de cada cultivar (ave(.,grp)). Mede se o espectro
#     explica a variacao fruto-a-fruto DENTRO do mesmo tipo.
#       ~ 0  -> o modelo so distingue cultivares, nao calibra composicao
#       > 0  -> ha sinal real alem do efeito varietal
within_cultivar_r <- function(y, yhat, grp) {
  yr <- y - ave(y, grp); pr <- yhat - ave(yhat, grp)
  suppressWarnings(stats::cor(yr, pr))
}

# 3e. loco(): Leave-One-Cultivar-Out. Treina em 2 cultivares e preve o
#     terceiro (3 rodadas). R2 muito negativo = o modelo nao generaliza
#     para um cultivar novo -> a "calibracao" era contraste entre tipos.
loco <- function(Xm, y, grp, nlv) {
  yh <- numeric(length(y))
  for (g in levels(grp)) {
    te <- which(grp == g); tr <- which(grp != g)
    fit <- plsr(y ~ X, ncomp = nlv, data = data.frame(y = y[tr], X = I(Xm[tr, ])))
    yh[te] <- predict(fit, newdata = data.frame(X = I(Xm[te, ])), ncomp = nlv)[, 1, 1]
  }
  1 - sum((y - yh)^2) / sum((y - mean(y))^2)
}

# 3f. williams(): classificacao qualitativa do RPD (Williams, 2001).
williams <- function(r) ifelse(r > 2.5, "excelente", ifelse(r > 2.0, "bom",
                        ifelse(r > 1.5, "razoavel", "fraco")))

# ---------------------------------------------------------------------
# 4. LOOP PRINCIPAL - 16 alvos x 5 pre-processamentos
# ---------------------------------------------------------------------
res <- list(); pred_best <- list()

for (s in sig) {
  y <- Ymat[[s]]                       # vetor de referencia do alvo atual (21 valores)
  if (anyNA(y)) {                      # se houver NA na referencia, pula o alvo
    cat(sprintf("%-10s | NA na referencia (linhas %s) - pulado\n", s,
                paste(which(is.na(y)), collapse = ",")))
    next
  }

  # 4a. Testa os 5 pre-processamentos; para cada um, escolhe o nLV de
  #     menor RMSECV e guarda as metricas.
  tab <- NULL
  for (pp in names(Xp)) {
    P      <- loo_all_nlv(Xp[[pp]], y)          # 21 x NLV_MAX predicoes na LOO
    rmsecv <- sqrt(colMeans(sweep(P, 1, y)^2))  # RMSECV por nº de componentes
    k      <- which.min(rmsecv)                 # melhor nLV para este pre-proc
    mt <- metrics(y, P[, k])                    # metricas com esse nLV
    mt$preproc <- pp; mt$nLV <- k
    mt$r_within <- within_cultivar_r(y, P[, k], Type)
    tab <- rbind(tab, mt)
  }
  tab <- tab[order(-tab$R2cv), ]               # ordena: melhor pre-proc no topo
  write.csv(tab, file.path(OUT_DIR, paste0("grid_", s, ".csv")), row.names = FALSE)

  # 4b. Melhor pre-processamento do alvo.
  best <- tab[1, ]; nlv_b <- best$nLV; ppb <- best$preproc

  # 4c. Predicoes LOO do melhor modelo (para grafico e permutacao).
  yhat_b <- loo_fixed(Xp[[ppb]], y, nlv_b)
  r2_obs <- 1 - sum((y - yhat_b)^2) / sum((y - mean(y))^2)

  # 4d. TESTE DE PERMUTACAO (y-randomization):
  #     embaralha y N_PERM vezes, refaz a LOO, e ve quantas vezes o R2 do
  #     acaso >= R2 real. p_perm alto (> 0.05) = o modelo nao supera o acaso.
  r2_null <- replicate(N_PERM, {
    yp <- sample(y)                                 # y embaralhado
    yh <- loo_fixed(Xp[[ppb]], yp, nlv_b)
    1 - sum((yp - yh)^2) / sum((yp - mean(yp))^2)
  })
  p_perm <- (1 + sum(r2_null >= r2_obs)) / (1 + N_PERM)

  # 4e. Leave-one-cultivar-out do melhor modelo.
  r2_loco <- loco(Xp[[ppb]], y, Type, nlv_b)

  # 4f. Guarda tudo.
  best$p_perm <- p_perm; best$R2_loco <- r2_loco; best$classe <- williams(best$RPD)
  res[[s]] <- cbind(trait = s, best)
  pred_best[[s]] <- data.frame(Fruit = Fruit, Type = Type, obs = y, pred = yhat_b, trait = s)

  cat(sprintf("%-10s | %-7s nLV=%d | R2cv=%+.2f RMSECV=%.3f RPD=%.2f RPIQ=%.2f | r_in=%+.2f | R2loco=%+.2f | p=%.3f | %s\n",
              s, ppb, nlv_b, best$R2cv, best$RMSECV, best$RPD, best$RPIQ,
              best$r_within, r2_loco, p_perm, best$classe))
}

# 4g. Tabela mestra: 1 linha por alvo, ordenada por R2cv.
master <- do.call(rbind, res)
master <- master[order(-master$R2cv), ]
n <- sapply(master, is.numeric); master[n] <- lapply(master[n], round, 3)
write.csv(master, file.path(OUT_DIR, "resumo_O1.csv"), row.names = FALSE)
cat("\n================ TABELA MESTRA - O1 ================\n")
print(master[, c("trait","preproc","nLV","R2cv","RMSECV","RPD","RPIQ","r_within","R2_loco","p_perm","classe")],
      row.names = FALSE)

# ---------------------------------------------------------------------
# 5. GRAFICOS  (cada bloco em try() para nao abortar se um falhar)
# ---------------------------------------------------------------------
pb <- do.call(rbind, pred_best)  # predicoes de todos os alvos empilhadas
saveRDS(list(master = master, pred = pb), file.path(OUT_DIR, "resultados_O1.rds"))

pal <- c(TI = "#D55E00", TH = "#0072B2", TS = "#009E73")  # cores por cultivar
hw  <- (W - 1) / 2  # meia-janela do SG (nº de bandas perdidas em cada ponta)

# 5a. Espectros: bruto, SNV e SNV+1a derivada (para inspecao visual).
try({
  png(file.path(OUT_DIR, "espectros_O1.png"), 1400, 950, res = 130)
  op <- par(mfrow = c(2, 2), mar = c(4, 4, 2, 1))
  matplot(wl, t(X), type = "l", lty = 1, col = pal[as.character(Type)],
          xlab = "nm", ylab = "Reflectancia", main = "O1 - bruto")
  Xsnv <- standardNormalVariate(X)
  matplot(wl, t(Xsnv), type = "l", lty = 1, col = pal[as.character(Type)],
          xlab = "nm", ylab = "SNV", main = "O1 - SNV")
  d1 <- savitzkyGolay(Xsnv, m = 1, p = 2, w = W)
  wl_sg <- wl[(hw + 1):(length(wl) - hw)]           # eixo x ajustado ao SG
  matplot(wl_sg, t(d1), type = "l", lty = 1, col = pal[as.character(Type)],
          xlab = "nm", ylab = "SNV + 1a deriv.", main = "O1 - SNV + D1")
  plot.new(); legend("center", names(pal), col = pal, lwd = 2, bty = "n", title = "Cultivar")
  par(op); dev.off()
})

# 5b. PCA (nao-supervisionada) sobre os espectros SNV: mostra se os
#     cultivares se separam sozinhos no espaco espectral.
try({
  pc <- prcomp(standardNormalVariate(X), center = TRUE, scale. = FALSE)
  ve <- round(100 * pc$sdev^2 / sum(pc$sdev^2), 1)   # % variancia por PC
  png(file.path(OUT_DIR, "pca_O1.png"), 1000, 850, res = 130)
  plot(pc$x[, 1], pc$x[, 2], col = pal[as.character(Type)], pch = 19,
       xlab = sprintf("PC1 (%.1f%%)", ve[1]), ylab = sprintf("PC2 (%.1f%%)", ve[2]),
       main = "PCA - espectros O1 (SNV)")
  text(pc$x[, 1], pc$x[, 2], Fruit, pos = 3, cex = 0.6)  # rotula cada fruto
  legend("topright", levels(Type), col = pal[levels(Type)], pch = 19, bty = "n")
  dev.off()
})

# 5c. Observado vs. predito (LOO) das 6 caracteristicas de maior R2cv.
#     A linha tracejada e a identidade (predicao perfeita).
try({
  top6 <- head(master$trait, 6)
  g <- ggplot(subset(pb, trait %in% top6), aes(obs, pred, color = Type)) +
    geom_abline(slope = 1, intercept = 0, linetype = 2, color = "grey50") +
    geom_point(size = 2) +
    facet_wrap(~ factor(trait, levels = top6), scales = "free") +
    scale_color_manual(values = pal) +
    labs(title = "O1 - observado vs. predito (LOO)", x = "observado", y = "predito") +
    theme_bw()
  ggsave(file.path(OUT_DIR, "obs_pred_O1.png"), g, width = 10, height = 6.5, dpi = 130)
})

cat("\nArquivos em", OUT_DIR, "/\n")
