# 20251009 Added plot tool

# Load ellmer for tool() and type_*()
library(ellmer)

# Run any plotting code and return the image data
Plot <- function(code) {
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

# Run any R code
# https://github.com/posit-dev/mcptools/issues/71
Run <- function(code) {
  eval(parse(text = code), globalenv())
}

mcptools::mcp_server(tools = list(

  tool(
    Run,
    "Run R code",
    arguments = list(
      code = type_string("R code to run.")
    )
  ),

  tool(
    Plot,
    "Run R code for plotting",
    arguments = list(
      code = type_string("R code to make the plot.")
    )
  )

))
