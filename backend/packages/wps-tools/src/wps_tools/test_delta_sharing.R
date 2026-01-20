#!/usr/bin/env Rscript
#' Test Delta Sharing Client (R)
#'
#' Tests the delta-sharing protocol implementation against a running API.
#'
#' Usage:
#'   Rscript test_delta_sharing.R
#'   Rscript test_delta_sharing.R --endpoint http://localhost:8080/api/delta-sharing
#'   Rscript test_delta_sharing.R --endpoint https://api.example.com/api/delta-sharing --token <jwt>
#'
#' Requirements:
#'   install.packages(c("httr", "jsonlite", "arrow"))

library(httr)
library(jsonlite)
library(arrow)

# Parse command line arguments
parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  endpoint <- "http://localhost:8080/api/delta-sharing"
  token <- NULL

  i <- 1
  while (i <= length(args)) {
    if (args[i] == "--endpoint" && i < length(args)) {
      endpoint <- args[i + 1]
      i <- i + 2
    } else if (args[i] == "--token" && i < length(args)) {
      token <- args[i + 1]
      i <- i + 2
    } else {
      i <- i + 1
    }
  }

  list(endpoint = endpoint, token = token)
}

# Create headers for requests
make_headers <- function(token = NULL) {
  headers <- c("Content-Type" = "application/json")
  if (!is.null(token)) {
    headers <- c(headers, "Authorization" = paste("Bearer", token))
  }
  headers
}

# Parse newline-delimited JSON response
parse_ndjson <- function(text) {
  lines <- strsplit(text, "\n")[[1]]
  lines <- lines[lines != ""]
  lapply(lines, fromJSON)
}

# Test the delta sharing protocol
test_delta_sharing <- function(endpoint, token = NULL) {
  headers <- make_headers(token)

  cat("=== Testing Delta Sharing Protocol (R) ===\n\n")

  # 1. List shares
  cat("1. GET /shares\n")
  response <- GET(paste0(endpoint, "/shares"), add_headers(.headers = headers))
  if (status_code(response) == 200) {
    data <- content(response, "parsed")
    cat("   Shares:", paste(sapply(data$items, function(x) x$name), collapse = ", "), "\n")
  } else {
    cat("   Error:", status_code(response), "\n")
  }
  cat("\n")

  # 2. List schemas
  cat("2. GET /shares/historical/schemas\n")
  response <- GET(paste0(endpoint, "/shares/historical/schemas"), add_headers(.headers = headers))
  if (status_code(response) == 200) {
    data <- content(response, "parsed")
    cat("   Schemas:", paste(sapply(data$items, function(x) x$name), collapse = ", "), "\n")
  } else {
    cat("   Error:", status_code(response), "\n")
  }
  cat("\n")

  # 3. List tables
  cat("3. GET /shares/historical/schemas/default/tables\n")
  response <- GET(
    paste0(endpoint, "/shares/historical/schemas/default/tables"),
    add_headers(.headers = headers)
  )
  if (status_code(response) == 200) {
    data <- content(response, "parsed")
    tables <- sapply(data$items, function(x) x$name)
    cat("   Tables:", paste(tables, collapse = ", "), "\n")
  } else {
    cat("   Error:", status_code(response), "\n")
  }
  cat("\n")

  # 4. Query stations table and load as dataframe
  cat("4. Load stations table\n")
  response <- POST(
    paste0(endpoint, "/shares/historical/schemas/default/tables/stations/query"),
    add_headers(.headers = headers),
    body = "{}",
    encode = "raw",
    content_type_json()
  )

  if (status_code(response) == 200) {
    text <- content(response, "text", encoding = "UTF-8")
    parsed <- parse_ndjson(text)

    # Find file entries
    file_urls <- c()
    for (item in parsed) {
      if (!is.null(item$file)) {
        file_urls <- c(file_urls, item$file$url)
      }
    }

    cat("   Files:", length(file_urls), "\n")

    if (length(file_urls) > 0) {
      # Read parquet files and combine
      dfs <- lapply(file_urls, function(url) {
        tryCatch({
          read_parquet(url)
        }, error = function(e) {
          cat("   Error reading", substr(url, 1, 80), "...\n")
          cat("   ", conditionMessage(e), "\n")
          NULL
        })
      })

      # Remove NULLs and combine
      dfs <- Filter(Negate(is.null), dfs)
      if (length(dfs) > 0) {
        df <- do.call(rbind, dfs)
        cat("   Shape:", nrow(df), "rows x", ncol(df), "cols\n")
        cat("   Columns:", paste(head(names(df), 6), collapse = ", "), "...\n")
        cat("   Sample:\n")
        print(head(df, 3))
      }
    }
  } else {
    cat("   Error:", status_code(response), content(response, "text"), "\n")
  }
  cat("\n")

  # 5. Query observations table (with limit)
  cat("5. Load observations table (first few files)\n")
  response <- POST(
    paste0(endpoint, "/shares/historical/schemas/default/tables/observations/query"),
    add_headers(.headers = headers),
    body = toJSON(list(limitHint = 2), auto_unbox = TRUE),
    encode = "raw",
    content_type_json()
  )

  if (status_code(response) == 200) {
    text <- content(response, "text", encoding = "UTF-8")
    parsed <- parse_ndjson(text)

    # Find file entries
    file_urls <- c()
    for (item in parsed) {
      if (!is.null(item$file)) {
        file_urls <- c(file_urls, item$file$url)
      }
    }

    cat("   Files:", length(file_urls), "\n")

    if (length(file_urls) > 0) {
      # Read first parquet file only (for speed)
      url <- file_urls[1]
      cat("   Reading first file...\n")

      tryCatch({
        df <- read_parquet(url)
        cat("   Shape:", nrow(df), "rows x", ncol(df), "cols\n")
        cat("   Columns:", paste(head(names(df), 8), collapse = ", "), "...\n")
        cat("   Sample:\n")
        print(head(df, 3))
      }, error = function(e) {
        cat("   Error reading parquet:\n")
        cat("   ", conditionMessage(e), "\n")
        cat("   URL:", substr(url, 1, 100), "...\n")
      })
    }
  } else {
    cat("   Error:", status_code(response), content(response, "text"), "\n")
  }
}

# Main
main <- function() {
  args <- parse_args()
  cat("Endpoint:", args$endpoint, "\n")
  if (!is.null(args$token)) {
    cat("Token: [provided]\n")
  }
  cat("\n")

  test_delta_sharing(args$endpoint, args$token)
}

main()
