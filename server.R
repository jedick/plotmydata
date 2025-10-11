# 20250808 Added tool definitions for random number functions
#   Text descriptions were modified from R help pages for each distribution and from ?mcptools::mcp_server (for rnorm)
# 20251009 Added plot tool

# Load ellmer for tool() and type_*()
library(ellmer)

# Custom plot function with explicit arguments
BasePlot <- function(x, y, type = "p") {
  # Cursor, Bing and Google AI all suggest this but it causes an error:
  # Error in png(filename = raw_conn) : 
  #   'filename' must be a non-empty character string
  ## Write plot to an in-memory PNG
  #raw_conn <- rawConnection(raw(), open = "wb")
  #png(filename = raw_conn)

  # Write PNG to a temporary file
  # Modified from https://hypatia.math.ethz.ch/pipermail/r-help/2023-May/477468.html
  filename <- tempfile(fileext = ".png")
  on.exit(unlink(filename))
  png(filename)
  plot(x, y, type = type)
  dev.off()
  # Return a PNG image as raw bytes so ADK can save it as an artifact
  readr::read_file_raw(filename)
}

# Function to generate random numbers from a discrete probability distribution
Discrete <- function(name, n, size_binom, prob, lambda, m_balls, n_balls, k_balls, size_multinom, prob_multinom, size_rnbinom, mu) {
  switch(name,
    rbinom = rbinom(n, size_binom, prob),
    rpois = rpois(n, lambda),
    rgeom = rgeom(n, prob),
    rhyper = rhyper(n, m_balls, n_balls, k_balls),
    rmultinom = rmultinom(n, size_multinom, prob_multinom),
    rnbinom = rnbinom(n, size_rnbinom, prob, mu),
    NULL
  )
}

# Function to generate random numbers from a continuous probability distribution
Continuous <- function(name, n, mean=0, sd=1, min=0, max=1, rate=1, df, ncp=0, ncp_t, shape, scale=1,
                       shape1, shape2, location=0, df1, df2, ncp_f, meanlog=0, sdlog=1) {
  switch(name,
    rnorm = rnorm(n, mean, sd),
    runif = runif(n, min, max),
    rexp = rexp(n, rate),
    rchisq = rchisq(n, df, ncp),
    rt = rt(n, df, ncp_t),
    rgamma = rgamma(n, shape, scale = scale),
    rbeta = rbeta(n, shape1, shape2, ncp),
    rcauchy = rcauchy(n, location, scale),
    rf = rf(n, df1, df2, ncp_f),
    rlogis = rlogis(n, location, scale),
    rlnorm = rlnorm(n, meanlog, sdlog),
    rweibull = rweibull(n, shape, scale),
    NULL
  )
}

# Run any R code
# https://github.com/posit-dev/mcptools/issues/71
Run <- function(code) {
  eval(parse(text = code), globalenv())
}

mcptools::mcp_server(tools = list(

  # Discrete probability distributions
  # TODO: Add others (from contributed packages): Benford, Dirichlet

  tool(
    Discrete,
    "Draw random numbers from a discrete probability distribution (binomial, Poisson, geometric, hypergeometric, multinomial, or negative binomial)",
    arguments = list(
      # NOTE: required = TRUE is the default for arguments
      name = type_string("The function's name: rbinom, rpois, rgeom, rhyper, rmultinom, or rnbinom."),
      n = type_integer("Number of observations. Must be a positive integer."),
      size_binom = type_number("Number of trials. Must be a positive integer or zero.", required = FALSE),
      prob = type_number("Probability of success in each trial.", required = FALSE),
      lambda = type_number("Mean and variance of the distribution.", required = FALSE),
      m_balls = type_integer("Number of white balls in the urn.", required = FALSE),
      n_balls = type_integer("Number of black balls in the urn.", required = FALSE),
      k_balls = type_integer("Number of balls drawn from the urn. Must be in 0,1,...,m+n.", required = FALSE),
      size_multinom = type_number("Total number of objects that are put into K boxes. Must be a positive integer or zero.", required = FALSE),
      prob_multinom = type_array(type_number("Vector of length K, specifying the probability for the K classes. Each value must be non-negative."), required = FALSE),
      size_rnbinom = type_number("Target for number of successful trials. Must be strictly positive, need not be integer.", required = FALSE),
      mu = type_number("Alternative parametrization via mean.", required = FALSE)
    )
  ),

  # Continuous probability distributions
  # TODO: Add others (from contributed packages): triangular

  tool(
    Continuous,
    paste("Draw random numbers from a continuous probability distribution",
          "(normal, uniform, exponential, Chi-Squared, Student t, Gamma, Beta, Cauchy, F, logistic, log normal, or Weibull)"),
    arguments = list(
      name = type_string("The function's name: rnorm, runif, rexp, rchisq, rt, rgamma, rbeta, rcauchy, rf, rlogis, rlnorm, or rweibull."),
      n = type_integer("Number of observations. Must be a positive integer."),
      mean = type_number("Mean of the distribution.", required = FALSE),
      sd = type_number("Standard deviation of the distribution. Must be a non-negative number.", required = FALSE),
      min = type_number("Lower limit of the distribution. Must be finite.", required = FALSE),
      max = type_number("Upper limit of the distribution. Must be finite.", required = FALSE),
      rate = type_number("Rate parameter (lambda). Must be positive.", required = FALSE),
      df = type_number("Degrees of freedom. Must be non-negative, but can be non-integer.", required = FALSE),
      ncp = type_number("Non-centrality parameter. Must non-negative.", required = FALSE),
      ncp_t = type_number("Non-centrality parameter. If omitted, use the central t distribution.", required = FALSE),
      shape = type_number("Shape parameter. Must be positive.", required = FALSE),
      scale = type_number("Scale parameter.", required = FALSE),
      shape1 = type_number("Non-negative parameter of the Beta distribution.", required = FALSE),
      shape2 = type_number("Non-negative parameter of the Beta distribution.", required = FALSE),
      location = type_number("Location parameter.", required = FALSE),
      df1 = type_number("Degrees of freedom. 'Inf' is allowed.", required = FALSE),
      df2 = type_number("Degrees of freedom. 'Inf' is allowed.", required = FALSE),
      ncp_f = type_number("Non-centrality parameter. If omitted the central F is assumed.", required = FALSE),
      meanlog = type_number("Mean of the distribution on the log scale.", required = FALSE),
      sdlog = type_number("Standard deviation of the distribution on the log scale.", required = FALSE)
    )
  ),

  tool(
    BasePlot,
    "Make a plot",
    arguments = list(
      x = type_array(type_number("Vector of x values.")),
      y = type_array(type_number("Vector of y values.")),
      type = type_string("Type of plot: 'p' for points, 'l' for lines, 'b' for both.", required = FALSE)
    )
  ),

  tool(
    Run,
    "Run R Code",
    arguments = list(
      code = type_string("R code to run, formatted as plain text.")
    )
  )

))
