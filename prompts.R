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
