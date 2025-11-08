# 20251009 Added plot tool
# 20251023 Added help tools

# Load ellmer for tool() and type_*()
library(ellmer)

# Read prompts
source("prompts.R")

# Get help for a package
help_package <- function(package) {
  help_page <- help(package = (package), help_type = "text")
  paste(unlist(help_page$info), collapse = "\n")
}

# Get help for a topic
# Adapted from https://github.com/posit-dev/btw:::help_to_rd
help_topic <- function(topic) {
  help_page <- help(topic = (topic), help_type = "text")
  if(length(help_page) == 0) {
    return(paste0("No help found for '", topic, "'. Please check the name and try again."))
  }
  # Handle multiple help files for a topic
  # e.g. help_topic(plot) returns the help for both base::plot and graphics::plot.default
  help_paths <- as.character(help_page)
  help_result <- sapply(help_paths, function(help_path) {
    rd_name <- basename(help_path)
    rd_package <- basename(dirname(dirname(help_path)))
    db <- tools::Rd_db(rd_package)[[paste0(rd_name, ".Rd")]]
    paste(as.character(db), collapse = "")
  })
  # Insert headings to help the LLM distinguish multiple help files
  # Heading before each help file (e.g. Help file 1, Help file 2)
  help_result <- paste0("## Help file ", seq_along(help_result), ":\n", help_result)
  # Heading at start of message (e.g. 2 help files were retrieved)
  if(length(help_paths) == 1) help_info <- paste0("# ", length(help_paths), " help file was retrieved: ", paste(help_paths, collapse = ", "), ":\n")
  if(length(help_paths) > 1) help_info <- paste0("# ", length(help_paths), " help files were retrieved: ", paste(help_paths, collapse = ", "), ":\n")
  help_result <- c(help_info, help_result)
  help_result
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
  return("The code executed successfully")
}

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

mcptools::mcp_server(tools = list(

  tool(
    help_package,
    help_package_prompt,
    arguments = list(
      package = type_string("Package to get help for.")
    )
  ),

  tool(
    help_topic,
    help_topic_prompt,
    arguments = list(
      topic = type_string("Topic or function to get help for.")
    )
  ),

  tool(
    run_visible,
    run_visible_prompt,
    arguments = list(
      code = type_string("R code to run.")
    )
  ),

  tool(
    run_hidden,
    run_hidden_prompt,
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
