# Summarize a data frame, for example:
# Data frame dimensions: 10 rows x 3 columns
# Data Summary:
# col1: integer
# col2: numeric, missing=3
# col3: character
data_summary <- function(df) {
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

# Check if packages are installed and return status message
# Example: check_packages(c("nlme", "ggplot2", "scatterplot3d"))
# Returns: "nlme and ggplot2 are already installed" if all are installed
# Or: "scatterplot3d needs to be installed" if some are missing
# The message format makes it easy to determine if installation is needed:
# - If message contains "are already installed" and does NOT contain "needs to be installed", all packages are installed
# - If message contains "needs to be installed", some packages need installation
check_packages <- function(packages) {
  if (length(packages) == 0) {
    return("No packages specified")
  }
  
  # Check which packages are installed
  installed <- sapply(packages, function(pkg) {
    requireNamespace(pkg, quietly = TRUE)
  })
  
  installed_pkgs <- packages[installed]
  missing_pkgs <- packages[!installed]
  
  if (length(installed_pkgs) == length(packages)) {
    # All packages are installed
    if (length(installed_pkgs) == 1) {
      return(paste(installed_pkgs, "is already installed"))
    } else if (length(installed_pkgs) == 2) {
      return(paste(installed_pkgs[1], "and", installed_pkgs[2], "are already installed"))
    } else {
      # Format: "pkg1, pkg2, and pkg3 are already installed"
      pkgs_list <- paste(installed_pkgs[-length(installed_pkgs)], collapse = ", ")
      return(paste(pkgs_list, "and", installed_pkgs[length(installed_pkgs)], "are already installed"))
    }
  } else if (length(installed_pkgs) > 0) {
    # Some packages are installed, some are missing
    if (length(installed_pkgs) == 1) {
      installed_msg <- paste(installed_pkgs, "is already installed")
    } else if (length(installed_pkgs) == 2) {
      installed_msg <- paste(installed_pkgs[1], "and", installed_pkgs[2], "are already installed")
    } else {
      pkgs_list <- paste(installed_pkgs[-length(installed_pkgs)], collapse = ", ")
      installed_msg <- paste(pkgs_list, "and", installed_pkgs[length(installed_pkgs)], "are already installed")
    }
    
    if (length(missing_pkgs) == 1) {
      missing_msg <- paste(missing_pkgs, "needs to be installed")
    } else if (length(missing_pkgs) == 2) {
      missing_msg <- paste(missing_pkgs[1], "and", missing_pkgs[2], "need to be installed")
    } else {
      pkgs_list <- paste(missing_pkgs[-length(missing_pkgs)], collapse = ", ")
      missing_msg <- paste(pkgs_list, "and", missing_pkgs[length(missing_pkgs)], "need to be installed")
    }
    
    return(paste(installed_msg, ";", missing_msg))
  } else {
    # No packages are installed
    if (length(missing_pkgs) == 1) {
      return(paste(missing_pkgs, "needs to be installed"))
    } else if (length(missing_pkgs) == 2) {
      return(paste(missing_pkgs[1], "and", missing_pkgs[2], "need to be installed"))
    } else {
      pkgs_list <- paste(missing_pkgs[-length(missing_pkgs)], collapse = ", ")
      return(paste(pkgs_list, "and", missing_pkgs[length(missing_pkgs)], "need to be installed"))
    }
  }
}
