# #####################################################################
#  VARIANTE "CENTRADA POR CULTIVAR" - remove a media de cada cultivar
#  de X e de y ANTES de ajustar o PLS (nao so depois, como r_within faz).
#
#  IDEIA: no script original (analise_posicao.R), o PLSR e ajustado com
#  os 21 frutos misturados. Se cultivar explica boa parte da variancia de
#  X e de y, os poucos componentes disponiveis (max. 6) podem ser "gastos"
#  discriminando cultivar, sobrando pouca capacidade para a variacao real
#  de composicao DENTRO de cada tipo. Aqui removemos a media do cultivar
#  de X e de y antes do ajuste, forcando o PLS a resolver so a variacao
#  intra-cultivar.
#
#  CUIDADO COM VAZAMENTO: a media de cada cultivar usada para centralizar
#  o treino (e para centralizar o fruto de teste) e sempre calculada SO
#  com os frutos de TREINO daquele cultivar - nunca inclui o proprio fruto
#  que esta sendo predito.
#
#  LIMITACOES DESTA VARIANTE (ver texto de acompanhamento):
#  - So 7 frutos por cultivar -> centralizar por grupo nao aumenta o n,
#    so remove variancia; continua sendo p >> n.
#  - Nao ha como fazer um R2_loco "puro" (treinar em 2 cultivares e prever
#    o 3o) porque, para um cultivar nunca visto, nao existe uma media de
#    grupo para descentralizar a predicao. Por isso o R2_loco_centrado
#    aqui usa a media GERAL dos 2 cultivares de treino como linha de base
#    para o cultivar deixado de fora - um teste mais realista ("eu nao
#    conheco a media do cultivar novo, so a media geral") mas nao
#    diretamente comparavel numero-a-numero ao R2_loco do script original.
#
#  USO:  Rscript analise_centrado.R O2   (mesmos argumentos: O1|O2|O3|O4|mean)
# #####################################################################

suppressMessages({
  library(readxl); library(dplyr); library(stringr); library(tidyr)
  library(prospectr); library(pls)
})

set.seed(1)
pls.options(parallel = NULL)

POS <- commandArgs(trailingOnly = TRUE)[1]
if (is.na(POS)) POS <- "O1"

ABAS <- c(
  O1   = "O1 (stem-end view)",
  O2   = "O2 (blossom-end view)",
  O3   = "O3 (stem-end to the right)",
  O4   = "O4 (stem-end to the left)",
  mean = "means of 4 positions"
)
stopifnot(POS %in% names(ABAS))

ARQ      <- "Capturas_tomate_NIRS_11agosto (1).xlsx"
ABA_ESP  <- ABAS[[POS]]
OUT_DIR  <- paste0("resultados_centrado_", POS)
dir.create(OUT_DIR, showWarnings = FALSE)
WL_MIN <- 450; WL_MAX <- 2450
N_PERM <- 99
NLV_MAX <- 6

cat(sprintf(">>> VARIANTE CENTRADA POR CULTIVAR - POSICAO %s (aba: %s)\n\n", POS, ABA_ESP))

# ---------------------------------------------------------------------
# 1. IMPORTACAO (identica ao analise_posicao.R)
# ---------------------------------------------------------------------
esp    <- read_excel(ARQ, sheet = ABA_ESP)
wl_all <- esp[[1]]
X_all  <- t(as.matrix(esp[, -1]))
cod    <- rownames(X_all)

m      <- str_match(cod, "^(T[IHS])R([0-9])")
Fruit  <- paste0(m[, 2], "R", m[, 3])
Type   <- factor(m[, 2])
stopifnot(!anyNA(Fruit), length(unique(Fruit)) == 21)

dest <- read_excel(ARQ, sheet = "Analise_destrutiva_P2")
dest <- dest[!is.na(dest$Treatments), ]

traits <- c("Fruit length","Fruit diameter","C/D","MF","L*","a*","b*","a*/b*",
            "Hue","Chroma","Firmness","pH","Vit. C","Total soluble solids",
            "Titratable acid","SS/AT ratio")
sig <- c("Length","Diameter","C_D","MF","L","a","b","a_b","Hue","Chroma",
         "Firmness","pH","VitC","SS","AT","SS_AT")
stopifnot(all(traits %in% names(dest)))

Y <- as.data.frame(lapply(traits, function(nm) suppressWarnings(as.numeric(dest[[nm]]))))
names(Y) <- sig

ykey <- paste0(dest$Treatments, dest$Repetition)
ord  <- match(Fruit, ykey)
Ymat <- Y[ord, , drop = FALSE]
stopifnot(!anyNA(ord), nrow(Ymat) == 21)

keep <- wl_all >= WL_MIN & wl_all <= WL_MAX
wl   <- wl_all[keep]
X    <- X_all[, keep]
cat(sprintf("Espectros %s: %d frutos x %d bandas (%.0f-%.0f nm)\n", POS, nrow(X), ncol(X), min(wl), max(wl)))

# ---------------------------------------------------------------------
# 2. PRE-PROCESSAMENTOS ESPECTRAIS (identico ao analise_posicao.R)
# ---------------------------------------------------------------------
W <- 15
Xp <- list(
  raw     = X,
  SNV     = standardNormalVariate(X),
  SNV_D1  = savitzkyGolay(standardNormalVariate(X), m = 1, p = 2, w = W),
  SNV_D2  = savitzkyGolay(standardNormalVariate(X), m = 2, p = 2, w = W),
  detrend = detrend(X, wav = wl)
)
Xp <- lapply(Xp, as.matrix)

# ---------------------------------------------------------------------
# 3. FUNCOES DE APOIO
# ---------------------------------------------------------------------
metrics <- function(y, yhat) {
  press <- sum((y - yhat)^2); tss <- sum((y - mean(y))^2)
  rmse  <- sqrt(press / length(y))
  data.frame(R2cv = 1 - press / tss, RMSECV = rmse,
             RPD = sd(y) / rmse, RPIQ = IQR(y) / rmse,
             bias = mean(yhat - y), slope = unname(coef(lm(y ~ yhat))[2]))
}

within_cultivar_r <- function(y, yhat, grp) {
  yr <- y - ave(y, grp); pr <- yhat - ave(yhat, grp)
  suppressWarnings(stats::cor(yr, pr))
}

williams <- function(r) ifelse(r > 2.5, "excelente", ifelse(r > 2.0, "bom",
                        ifelse(r > 1.5, "razoavel", "fraco")))

# 3g. group_mean_rows(): para cada linha de M, devolve a media do SEU
#     grupo (calculada so com as linhas de M, isto e, so com o treino
#     quando M = Xtr). Equivalente a ave() de uma matriz, coluna a coluna.
group_mean_rows <- function(M, grp) {
  out <- M
  for (g in levels(droplevels(grp))) {
    idx <- which(grp == g)
    out[idx, ] <- matrix(colMeans(M[idx, , drop = FALSE]), nrow = length(idx), ncol = ncol(M), byrow = TRUE)
  }
  out
}

# 3h. loo_all_nlv_centered(): Leave-One-Fruit-Out, mas centralizando X e y
#     pela media do CULTIVAR antes de treinar. A media de cada grupo e
#     recalculada a cada fold usando so os frutos de treino (sem o fruto i)
#     - evita vazamento. A predicao final volta pra escala original somando
#     de volta a media do cultivar do fruto i (media essa tambem so-treino).
loo_all_nlv_centered <- function(Xm, y, grp, nlv_max = NLV_MAX) {
  n <- length(y); nlv_max <- min(nlv_max, n - 3)
  P <- matrix(NA_real_, n, nlv_max)
  for (i in seq_len(n)) {
    tr    <- setdiff(seq_len(n), i)
    Xtr   <- Xm[tr, , drop = FALSE]; ytr <- y[tr]; g_tr <- grp[tr]
    gx_i  <- colMeans(Xtr[g_tr == grp[i], , drop = FALSE])  # media espectral do cultivar do fruto i (so treino)
    gy_i  <- mean(ytr[g_tr == grp[i]])                       # media do alvo do cultivar do fruto i (so treino)
    Xtr_c <- Xtr - group_mean_rows(Xtr, g_tr)                # remove a media do proprio grupo de cada fruto de treino
    ytr_c <- ytr - ave(ytr, g_tr)
    Xi_c  <- Xm[i, , drop = FALSE] - matrix(gx_i, nrow = 1)  # centraliza o fruto-teste pela media (so-treino) do MESMO cultivar
    fit   <- plsr(y ~ X, ncomp = nlv_max, data = data.frame(y = ytr_c, X = I(Xtr_c)))
    pr    <- predict(fit, newdata = data.frame(X = I(Xi_c)))
    P[i, ] <- pr[1, 1, ] + gy_i                              # devolve a predicao para a escala original (soma a media do grupo)
  }
  P
}

# 3i. loo_fixed_centered(): mesma ideia, nLV fixo (usada no teste de
#     permutacao, que roda o modelo 99x).
loo_fixed_centered <- function(Xm, y, grp, nlv) {
  n <- length(y); yh <- numeric(n)
  for (i in seq_len(n)) {
    tr    <- setdiff(seq_len(n), i)
    Xtr   <- Xm[tr, , drop = FALSE]; ytr <- y[tr]; g_tr <- grp[tr]
    gx_i  <- colMeans(Xtr[g_tr == grp[i], , drop = FALSE])
    gy_i  <- mean(ytr[g_tr == grp[i]])
    Xtr_c <- Xtr - group_mean_rows(Xtr, g_tr)
    ytr_c <- ytr - ave(ytr, g_tr)
    Xi_c  <- Xm[i, , drop = FALSE] - matrix(gx_i, nrow = 1)
    fit   <- plsr(y ~ X, ncomp = nlv, data = data.frame(y = ytr_c, X = I(Xtr_c)))
    yh[i] <- predict(fit, newdata = data.frame(X = I(Xi_c)), ncomp = nlv)[1, 1, 1] + gy_i
  }
  yh
}

# 3j. permute_within(): embaralha y DENTRO de cada cultivar (preserva a
#     media de cada grupo, so embaralha quem-tem-qual-valor dentro do
#     tipo). E o nulo correto para testar sinal intra-cultivar.
permute_within <- function(y, grp) {
  yp <- y
  for (g in levels(grp)) { idx <- which(grp == g); yp[idx] <- sample(y[idx]) }
  yp
}

# 3k. loco_centered(): treina em 2 cultivares (dados centralizados pela
#     media de CADA um desses 2 grupos) e preve o 3o, nunca visto. Como
#     nao existe media do cultivar novo, o fruto de teste e centralizado
#     pela media GERAL do treino (2 cultivares juntos) - a melhor
#     estimativa disponivel sem conhecer o novo grupo - e a predicao final
#     soma de volta essa mesma media geral. Isto testa se a relacao
#     espectro-residuo aprendida em 2 tipos se transfere a um 3o tipo,
#     partindo de uma linha de base "ingenua" (media geral do treino).
loco_centered <- function(Xm, y, grp, nlv) {
  yh <- numeric(length(y))
  for (g in levels(grp)) {
    te  <- which(grp == g); tr <- which(grp != g)
    Xtr <- Xm[tr, , drop = FALSE]; ytr <- y[tr]; g_tr <- droplevels(grp[tr])
    Xtr_c <- Xtr - group_mean_rows(Xtr, g_tr)
    ytr_c <- ytr - ave(ytr, g_tr)
    baseline <- mean(ytr)                                    # media geral dos 2 cultivares de treino
    Xte_c <- Xm[te, , drop = FALSE] -
      matrix(colMeans(Xtr), nrow = length(te), ncol = ncol(Xtr), byrow = TRUE)  # centraliza pelo centro GERAL do treino
    fit <- plsr(y ~ X, ncomp = nlv, data = data.frame(y = ytr_c, X = I(Xtr_c)))
    pr  <- predict(fit, newdata = data.frame(X = I(Xte_c)), ncomp = nlv)[, 1, 1]
    yh[te] <- pr + baseline
  }
  1 - sum((y - yh)^2) / sum((y - mean(y))^2)
}

# ---------------------------------------------------------------------
# 4. LOOP PRINCIPAL - 16 alvos x 5 pre-processamentos (variante centrada)
# ---------------------------------------------------------------------
res <- list()

for (s in sig) {
  y <- Ymat[[s]]
  if (anyNA(y)) { cat(sprintf("%-10s | NA na referencia - pulado\n", s)); next }

  tab <- NULL
  for (pp in names(Xp)) {
    P      <- loo_all_nlv_centered(Xp[[pp]], y, Type)
    rmsecv <- sqrt(colMeans(sweep(P, 1, y)^2))
    k      <- which.min(rmsecv)
    mt <- metrics(y, P[, k])
    mt$preproc <- pp; mt$nLV <- k
    mt$r_within <- within_cultivar_r(y, P[, k], Type)
    tab <- rbind(tab, mt)
  }
  tab <- tab[order(-tab$R2cv), ]
  write.csv(tab, file.path(OUT_DIR, paste0("grid_", s, ".csv")), row.names = FALSE)

  best <- tab[1, ]; nlv_b <- best$nLV; ppb <- best$preproc

  yhat_b <- loo_fixed_centered(Xp[[ppb]], y, Type, nlv_b)
  r2_obs <- 1 - sum((y - yhat_b)^2) / sum((y - mean(y))^2)

  r2_null <- replicate(N_PERM, {
    yp <- permute_within(y, Type)
    yh <- loo_fixed_centered(Xp[[ppb]], yp, Type, nlv_b)
    1 - sum((yp - yh)^2) / sum((yp - mean(yp))^2)
  })
  p_perm <- (1 + sum(r2_null >= r2_obs)) / (1 + N_PERM)

  r2_loco_c <- loco_centered(Xp[[ppb]], y, Type, nlv_b)

  best$p_perm <- p_perm; best$R2_loco_c <- r2_loco_c; best$classe <- williams(best$RPD)
  res[[s]] <- cbind(trait = s, best)

  cat(sprintf("%-10s | %-7s nLV=%d | R2cv=%+.2f RMSECV=%.3f RPD=%.2f | r_in=%+.2f | R2loco_c=%+.2f | p=%.3f | %s\n",
              s, ppb, nlv_b, best$R2cv, best$RMSECV, best$RPD, best$r_within, r2_loco_c, p_perm, best$classe))
}

master <- do.call(rbind, res)
master <- master[order(-master$R2cv), ]
n <- sapply(master, is.numeric); master[n] <- lapply(master[n], round, 3)
write.csv(master, file.path(OUT_DIR, paste0("resumo_centrado_", POS, ".csv")), row.names = FALSE)
saveRDS(master, file.path(OUT_DIR, paste0("resultados_centrado_", POS, ".rds")))

cat(sprintf("\n================ TABELA MESTRA CENTRADA - %s ================\n", POS))
print(master[, c("trait","preproc","nLV","R2cv","RMSECV","RPD","r_within","R2_loco_c","p_perm","classe")],
      row.names = FALSE)
cat("\nArquivos em", OUT_DIR, "/\n")
