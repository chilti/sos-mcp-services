#!/usr/bin/env Rscript
# ==============================================================================
# CLI Helper: R Bibliometrix Autonomous Runner
# Realiza mapeo cienciométrico, análisis de redes y cartografía temática
# usando el paquete canónico R bibliometrix (Aria & Cuccurullo, 2017).
#
# Uso:
#   Rscript scripts/bibliometrix_runner.R --command summary --input data.csv --output result.json
#   Rscript scripts/bibliometrix_runner.R --command network --type co-citation --input data.csv --output net.json --plot-output net.png
#   Rscript scripts/bibliometrix_runner.R --command thematic --field DE --input data.csv --output themes.json --plot-output themes.png
# ==============================================================================

suppressPackageStartupMessages({
  if (!require("bibliometrix")) {
    stop("Error: El paquete 'bibliometrix' no está instalado en el entorno de R. Instálelo con: install.packages('bibliometrix')")
  }
  if (!require("jsonlite")) {
    stop("Error: El paquete 'jsonlite' no está instalado. Instálelo con: install.packages('jsonlite')")
  }
})

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  params <- list(
    command = "summary",
    input = NULL,
    output = "bibliometrix_output.json",
    plot_output = NULL,
    dbsource = "scopus",
    format = "csv",
    field = "DE",
    type = "collaboration",
    network = "authors",
    n_nodes = 50,
    min_freq = 3,
    seed = 1234
  )

  i <- 1
  while (i <= length(args)) {
    arg <- args[i]
    if (arg == "--command" && i < length(args)) { params$command <- args[i + 1]; i <- i + 2 }
    else if (arg == "--input" && i < length(args)) { params$input <- args[i + 1]; i <- i + 2 }
    else if (arg == "--output" && i < length(args)) { params$output <- args[i + 1]; i <- i + 2 }
    else if (arg == "--plot-output" && i < length(args)) { params$plot_output <- args[i + 1]; i <- i + 2 }
    else if (arg == "--dbsource" && i < length(args)) { params$dbsource <- args[i + 1]; i <- i + 2 }
    else if (arg == "--format" && i < length(args)) { params$format <- args[i + 1]; i <- i + 2 }
    else if (arg == "--field" && i < length(args)) { params$field <- args[i + 1]; i <- i + 2 }
    else if (arg == "--type" && i < length(args)) { params$type <- args[i + 1]; i <- i + 2 }
    else if (arg == "--network" && i < length(args)) { params$network <- args[i + 1]; i <- i + 2 }
    else if (arg == "--n-nodes" && i < length(args)) { params$n_nodes <- as.integer(args[i + 1]); i <- i + 2 }
    else if (arg == "--min-freq" && i < length(args)) { params$min_freq <- as.integer(args[i + 1]); i <- i + 2 }
    else if (arg == "--seed" && i < length(args)) { params$seed <- as.integer(args[i + 1]); i <- i + 2 }
    else { i <- i + 1 }
  }

  if (is.null(params$input)) {
    stop("Error: El argumento --input es obligatorio.")
  }
  return(params)
}

main <- function() {
  params <- parse_args()
  set.seed(params$seed)

  cat(sprintf("[Bibliometrix Runner] Cargando datos desde: %s (dbsource: %s, format: %s)\n", params$input, params$dbsource, params$format))
  
  M <- tryCatch({
    convert2df(file = params$input, dbsource = params$dbsource, format = params$format)
  }, error = function(e) {
    stop(sprintf("Fallo al convertir el archivo a bibliometrix dataframe: %s", e$message))
  })

  cat(sprintf("[Bibliometrix Runner] Dataset cargado: %d documentos, %d columnas\n", nrow(M), ncol(M)))

  if (params$command == "summary") {
    cat("[Bibliometrix Runner] Ejecutando biblioAnalysis()...\n")
    results <- biblioAnalysis(M, sep = ";")
    s <- summary(results, k = 10, pause = FALSE)

    ci_val <- suppressWarnings(as.numeric(results$CollaborationIndex))
    agr_val <- suppressWarnings(as.numeric(results$AnnualGrowthRate))

    summary_data <- list(
      n_documents = nrow(M),
      period = c(min(M$PY, na.rm = TRUE), max(M$PY, na.rm = TRUE)),
      total_authors = results$nAuthors,
      single_authored_docs = results$nAuthors - results$nAuthorsFractional,
      co_authors_per_doc = round(results$nAuthors / nrow(M), 2),
      collaboration_index = if (length(ci_val) > 0 && !is.na(ci_val[1])) round(ci_val[1], 2) else NULL,
      annual_growth_rate = if (length(agr_val) > 0 && !is.na(agr_val[1])) round(agr_val[1], 2) else NULL,
      top_sources = if (!is.null(results$Sources)) as.data.frame(head(results$Sources, 10)) else data.frame(),
      top_authors = if (!is.null(results$Authors)) as.data.frame(head(results$Authors, 10)) else data.frame(),
      top_countries = if (!is.null(results$Countries)) as.data.frame(head(results$Countries, 10)) else data.frame()
    )

    dir.create(dirname(normalizePath(params$output, mustWork = FALSE)), recursive = TRUE, showWarnings = FALSE)
    write_json(summary_data, path = params$output, pretty = TRUE, auto_unbox = TRUE)
    cat(sprintf("[Bibliometrix Runner] Resumen descriptivo guardado en: %s\n", params$output))

  } else if (params$command == "network") {
    cat(sprintf("[Bibliometrix Runner] Construyendo red de tipo '%s' sobre '%s'...\n", params$type, params$network))
    net_matrix <- biblioNetwork(M, analysis = params$type, network = params$network, sep = ";")

    if (!is.null(params$plot_output)) {
      dir.create(dirname(normalizePath(params$plot_output, mustWork = FALSE)), recursive = TRUE, showWarnings = FALSE)
      png(filename = params$plot_output, width = 2400, height = 2000, res = 300)
      net_plot <- networkPlot(net_matrix, n = params$n_nodes, Title = sprintf("Network: %s (%s)", params$type, params$network),
                              type = "fruchterman", size = TRUE, remove.multiple = TRUE, labelsize = 0.8)
      dev.off()
      cat(sprintf("[Bibliometrix Runner] Gráfico de red exportado a: %s\n", params$plot_output))
    }

    net_info <- list(
      analysis_type = params$type,
      network_target = params$network,
      nodes_count = min(params$n_nodes, ncol(net_matrix)),
      density = round(sum(net_matrix > 0) / (ncol(net_matrix) * (ncol(net_matrix) - 1)), 4),
      output_plot = params$plot_output
    )

    write_json(net_info, path = params$output, pretty = TRUE, auto_unbox = TRUE)
    cat(sprintf("[Bibliometrix Runner] Metadatos de red guardados en: %s\n", params$output))

  } else if (params$command == "thematic") {
    cat(sprintf("[Bibliometrix Runner] Generando Mapa Temático Estratégico de Callon (campo: %s)...\n", params$field))
    
    t_map <- thematicMap(M, field = params$field, n = params$n_nodes, minfreq = params$min_freq,
                         stemming = FALSE, size = 0.5, n.labels = 3, repel = TRUE)

    if (!is.null(params$plot_output)) {
      dir.create(dirname(normalizePath(params$plot_output, mustWork = FALSE)), recursive = TRUE, showWarnings = FALSE)
      png(filename = params$plot_output, width = 2400, height = 2000, res = 300)
      plot(t_map$map)
      dev.off()
      cat(sprintf("[Bibliometrix Runner] Mapa temático exportado a: %s\n", params$plot_output))
    }

    clusters_df <- t_map$clusters
    themes_data <- list(
      analysis = "Callon Strategic Thematic Map",
      field = params$field,
      clusters_count = nrow(clusters_df),
      clusters = as.data.frame(clusters_df),
      plot_path = params$plot_output
    )

    write_json(themes_data, path = params$output, pretty = TRUE, auto_unbox = TRUE)
    cat(sprintf("[Bibliometrix Runner] Resultados de cuadrantes temáticos guardados en: %s\n", params$output))

  } else {
    stop(sprintf("Comando desconocido: '%s'. Opciones válidas: 'summary', 'network', 'thematic'", params$command))
  }
}

main()
