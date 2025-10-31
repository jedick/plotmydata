make_plot_prompt <- '
Runs R code to make a plot with base R graphics.

Args:
  code: R code to run

Returns:
  Binary image data

Details:
`code` should be R code that begins with e.g. `png(filename)` and ends with `dev.off()`.
Always use the variable `filename` instead of an actual file name.

Example: User requests "Plot x (1,2,3) and y (10,20,30)", then `code` is:

png(filename)
x <- c(1, 2, 3)
y <- c(10, 20, 30)
plot(x, y)
dev.off()

Example: User requests "Give me a 8.5x11 inch PDF of y = x^2 from -1 to 1, large font, titled with the function", then `code` is:

pdf(filename, width = 8.5, height = 11)
par(cex = 2)
x <- seq(-1, 1, length.out = 100)
y <- x^2
plot(x, y, type = "l")
title(main = quote(y == x^2))
dev.off()

Example: User requests "Plot radius_worst (y) vs radius_mean (x) from https://zenodo.org/records/3608984/files/breastcancer.csv?download=1", then `code` is:

png(filename)
df <- read.csv("https://zenodo.org/records/3608984/files/breastcancer.csv?download=1")
plot(df$radius_mean, df$radius_worst, xlab = "radius_worst", ylab = "radius_mean")
dev.off()

Example: User requests "Plot radius_worst (y) vs radius_mean (x)" and [Uploaded File: "/tmp/uploads/breast-cancer.csv"], then `code` is:

png(filename)
df <- read.csv("/tmp/uploads/breast-cancer.csv")
plot(df$radius_mean, df$radius_worst, xlab = "radius_worst", ylab = "radius_mean")
dev.off()
'

make_ggplot_prompt <- '
Runs R code to make a plot with ggplot/ggplot2.

Args:
  code: R code to run

Returns:
  Binary image data

Details:
`code` should be R code that begins with `library(ggplot2)` and ends with `ggsave(filename, device = "png")`.

Example: User requests "ggplot wt vs mpg from mtcars", then `code` is:

library(ggplot2)
ggplot(mtcars, aes(mpg, wt)) +
  geom_point()
ggsave(filename, device = "png")

Example: User requests "ggplot wt vs mpg from mtcars as pdf", then `code` is:

library(ggplot2)
ggplot(mtcars, aes(mpg, wt)) +
  geom_point()
ggsave(filename, device = "pdf")

Important notes:

- `code` must end with ggsave(filename, device = ) with a specified device.
- Use `device = "png"` unless the user requests a different format.
- Always use the variable `filename` instead of an actual file name.
'

help_topic_prompt <- '
Gets documentation for a dataset, function, or other topic.

Args:
  topic: Topic or function to get help for.

Returns:
  Documentation text. May include runnable R examples.

Examples:
- Show the arguments of the `lm` function: help_topic("lm").
- Show the format of the `airquality` dataset: help_topic("airquality").
- Get variables in `Titanic`: help_topic("Titanic").
'

help_package_prompt <- '
Summarizes datasets and functions in an R package.

Args:
  package: Package to get help for.

Returns:
  Documentation text. Includes a package description and index of functions and datasets.

Examples:
- Get the names of R datasets: help_package("datasets").
- List graphics functions in base R: help_package("graphics").
'

run_visible_prompt <- '
Runs R code and returns the result.
Does not make plots.

Args:
  code: R code to run.

Returns:
  Result of R code execution.
'

run_hidden_prompt <- '
Run R code without returning the result.
Does not make plots.

Args:
  code: R code to run.

Returns:
  Nothing.

NOTE: Choose this tool if:
  - The user asks to save the result in a variable, or
  - You are performing intermediate calculations before making a plot.
'
