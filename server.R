# 20251009 Added plot tool

# Load ellmer for tool() and type_*()
library(ellmer)

# Read prompts
source("prompts.R")

# Run R code to make a plot and return the image data
make_plot <- function(code) {
  # Cursor, Bing and Google AI all suggest this but it causes an error:
  # Error in png(filename = raw_conn) : 
  #   'filename' must be a non-empty character string
  ## Write plot to an in-memory PNG
  #raw_conn <- rawConnection(raw(), open = "wb")
  #png(filename = raw_conn)

  # Use a temporary file to save the plot
  filename <- tempfile(fileext = ".dat")
  on.exit(unlink(filename))

  # Run the plotting code (this should include e.g. png() and dev.off())
  # The code uses a local variable (filename), so don't use envir = globalenv() here
  eval(parse(text = code))

  # Return a PNG image as raw bytes so ADK can save it as an artifact
  readr::read_file_raw(filename)
}

# This is the same code as make_plot() but has a different tool description
make_ggplot <- function(code) {
  filename <- tempfile(fileext = ".dat")
  on.exit(unlink(filename))
  eval(parse(text = code))
  readr::read_file_raw(filename)
}

# Run R code and return the result
# https://github.com/posit-dev/mcptools/issues/71
run_visible <- function(code) {
  eval(parse(text = code), globalenv())
}

# Run R code without returning the result
# https://github.com/posit-dev/mcptools/issues/71
run_hidden <- function(code) {
  eval(parse(text = code), globalenv())
  return("The operation completed successfully")
}

mcptools::mcp_server(tools = list(

  tool(
    run_visible,
    "Run R code",
    arguments = list(
      code = type_string("R code to run.")
    )
  ),

  tool(
    run_hidden,
    "Run R code without returning the result",
    arguments = list(
      code = type_string("R code to run.")
    )
  ),

  tool(
    make_plot,
    make_plot_prompt,
    arguments = list(
      code = type_string("R code to make the plot.")
    )
  ),

  tool(
    make_ggplot,
    make_ggplot_prompt,
    arguments = list(
      code = type_string("R code to make the plot.")
    )
  )

))
