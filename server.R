# 20250808 Added tool definitions for random number functions
#   Text descriptions were modified from R help pages for each distribution and from ?mcptools::mcp_server (for rnorm)
# 20251009 Added plot tool

# Load ellmer for tool() and type_*()
library(ellmer)

# Define custom plot function with explicit arguments
mkplot <- function(x, y, type = "p") {
  plot(x, y, type = type)
}

mcptools::mcp_server(tools = list(

  # Discrete probability distributions
  # TODO: Add others (from contributed packages): Benford, Dirichlet

  tool(
    rbinom,
    "Draw random numbers from a binomial distribution",
    arguments = list(
      # NOTE: required = TRUE is the default for arguments
      n = type_integer("Number of observations. Must be a positive integer."),
      size = type_number("Number of trials. Must be a positive integer or zero."),
      prob = type_number("Probability of success in each trial.")
    )
  ),

  tool(
    rpois,
    "Draw random numbers from a Poisson distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      lambda = type_number("Mean and variance of the distribution.")
    )
  ),

  tool(
    rgeom,
    "Draw random numbers from a geometric distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      prob = type_number("Probability of success in each trial.")
    )
  ),

  tool(
    rhyper,
    "Draw random numbers from a hypergeometric distribution",
    arguments = list(
      nn = type_integer("Number of observations. Must be a positive integer."),
      m = type_integer("Number of white balls in the urn."),
      n = type_integer("Number of black balls in the urn."),
      k = type_integer("Number of balls drawn from the urn. Must be in 0,1,...,m+n.")
    )
  ),

  tool(
    rmultinom,
    "Draw random numbers from a multinomial distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      size = type_number("Total number of objects that are put into K boxes. Must be a positive integer or zero."),
      prob = type_array(type_number("Vector of length K, specifying the probability for the K classes. Each value must be non-negative."))
    )
  ),

  tool(
    rnbinom,
    "Draw random numbers from a negative binomial distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      size = type_number("Target for number of successful trials. Must be strictly positive, need not be integer."),
      prob = type_number("Probability of success in each trial."),
      mu = type_number("Alternative parametrization via mean.", required = FALSE)
    )
  ),

  # Continuous probability distributions
  # TODO: Add others (from contributed packages): triangular

  tool(
    rnorm,
    "Draw random numbers from a normal distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      mean = type_number("Mean of the distribution.", required = FALSE),
      sd = type_number("Standard deviation of the distribution. Must be a non-negative number.", required = FALSE)
    )
  ),

  tool(
    runif,
    "Draw random numbers from a uniform distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      min = type_number("Lower limit of the distribution. Must be finite.", required = FALSE),
      max = type_number("Upper limit of the distribution. Must be finite.", required = FALSE)
    )
  ),

  tool(
    rexp,
    "Draw random numbers from an exponential distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      rate = type_number("Rate parameter (lambda). Must be positive.", required = FALSE)
    )
  ),

  tool(
    rchisq,
    "Draw random numbers from a Chi-Squared distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      df = type_number("Degrees of freedom. Must be non-negative, but can be non-integer."),
      ncp = type_number("Non-centrality parameter. Must non-negative.", required = FALSE)
    )
  ),

  tool(
    rt,
    "Draw random numbers from a Student t distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      df = type_number("Degrees of freedom. Must be non-negative, but can be non-integer."),
      ncp = type_number("Non-centrality parameter. If omitted, use the central t distribution.", required = FALSE)
    )
  ),

  tool(
    rgamma,
    "Draw random numbers from a Gamma distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      shape = type_number("Shape parameter. Must be positive."),
      rate = type_number("Alternative way to specify the scale.", required = FALSE),
      scale = type_number("Scale parameter. Must be strictly positive.", required = FALSE)
    )
  ),

  tool(
    rbeta,
    "Draw random numbers from a Beta distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      shape1 = type_number("Non-negative parameter of the Beta distribution."),
      shape2 = type_number("Non-negative parameter of the Beta distribution."),
      ncp = type_number("Non-centrality parameter. Must non-negative.", required = FALSE)
    )
  ),

  tool(
    rcauchy,
    "Draw random numbers from a Cauchy distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      location = type_number("Location parameter."),
      scale = type_number("Scale parameter.")
    )
  ),

  tool(
    rf,
    "Draw random numbers from an F distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      df1 = type_number("Degrees of freedom. 'Inf' is allowed."),
      df2 = type_number("Degrees of freedom. 'Inf' is allowed."),
      ncp = type_number("Non-centrality parameter. If omitted the central F is assumed.", required = FALSE)
    )
  ),

  tool(
    rlogis,
    "Draw random numbers from a logistic distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      location = type_number("Location parameter.", required = FALSE),
      scale = type_number("Scale parameter.", required = FALSE)
    )
  ),

  tool(
    rlnorm,
    "Draw random numbers from a log normal distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      meanlog = type_number("Mean of the distribution on the log scale.", required = FALSE),
      sdlog = type_number("Standard deviation of the distribution on the log scale.", required = FALSE)
    )
  ),

  tool(
    rweibull,
    "Draw random numbers from a Weibull distribution",
    arguments = list(
      n = type_integer("Number of observations. Must be a positive integer."),
      shape = type_number("Shape parameter."),
      scale = type_number("Scale parameter.", required = FALSE)
    )
  ),

  tool(
    mkplot,
    "Make a plot",
    arguments = list(
      x = type_array(type_number("Vector of x values.")),
      y = type_array(type_number("Vector of y values.")),
      type = type_string("Type of plot: 'p' for points, 'l' for lines, 'b' for both.", required = FALSE)
    )
  )

))
