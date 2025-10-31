# Summarize a data frame, for example:
# Data frame dimensions: 10 rows x 3 columns
# Data Summary:
# col1: integer
# col2: numeric, missing=3
# col3: character

summarize <- function(df) {
  nrows <- nrow(df)
  ncols <- ncol(df)
  lines <- c(sprintf("Data frame dimensions: %d rows x %d columns", nrows, ncols), "Data Summary:")

  # Helper for R data type names
  type_map <- function(x) {
    if (is.factor(x)) return("factor")
    if (is.character(x)) return("character")
    if (is.logical(x)) return("logical")
    if (inherits(x, "Date")) return("Date")
    if (is.numeric(x)) {
      vals <- x[!is.na(x)]
      if (length(vals) > 0 && all(abs(vals - round(vals)) < .Machine$double.eps^0.5)) return("integer")
      return("numeric")
    }
    return(class(x)[1])
  }

  for (col in names(df)) {
    dtype <- type_map(df[[col]])
    miss <- sum(is.na(df[[col]]))
    if (miss > 0) {
      lines <- c(lines, sprintf("%s: %s, missing=%d", col, dtype, miss))
    } else {
      lines <- c(lines, sprintf("%s: %s", col, dtype))
    }
  }
  paste(lines, collapse = "\n")
}
