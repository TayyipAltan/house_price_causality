library(sf)
library(arrow)
library(dplyr)
library(fixest)
library(data.table)
library(arrow)  
library(lubridate)
library(units)


#-----------
# Data loading + prep
#-----------
eq <- read_parquet("../data/processed/gdf_aardbevingen.parquet") |>
  st_as_sf(crs = 4326)  

muni <- read_parquet("../data/processed/gdf_area_prijs.parquet") |>
  st_as_sf(crs = 28992)

# To scope the data, leave out unnecessary provinces
relevant_provinces <- c("Groningen", "Friesland", "Drenthe")

muni <- muni |> 
  filter(provincie %in% relevant_provinces)

# Define IDs for the merge
eq <- eq |>
  arrange(timestamp) |>
  mutate(eq_id = as.character(row_number()))

# Align CRS with 3035, since earthquakes in neighbouring countries are involved
target_crs <- 3035  # ETRS89 / LAEA Europe
eq   <- st_transform(eq, target_crs)
muni <- st_transform(muni, target_crs)

# Create quarterly earthquake timing
eq <- eq |>
  mutate(
    year = year(timestamp),
    quarter = floor_date(timestamp, "quarter"),
    tq = year * 4 + quarter   # numeric time index
  )

muni <- muni |>
  mutate(
    year = year(date),
    quarter = floor_date(date, "quarter"),
    tq = year * 4 + quarter,   # numeric time index
    muni_id = paste0(gemeente, "_", tq),
    perceived_risk = ifelse(provincie == 'Groningen', 1, 0)
  )


#-----------
# Defining the distance matrix
#-----------

muni_boundary <- st_boundary(muni)

# Compute distance to any earthquake (for filtering Groningen)
dist_matrix <- st_distance(muni_boundary, eq)
dist_matrix <- set_units(dist_matrix, "m")
dist_matrix <- drop_units(dist_matrix)

dist_df <- as.data.frame(dist_matrix)

dist_df$municipality <- muni$gemeente[match(
  rownames(dist_df),
  rownames(muni)
)]

# Assigning col names for identification
colnames(dist_df) <- as.character(eq$eq_id)

#-------------
# Create exposure 
#-------------


mag_weight <- 10^(1.5 * eq$magnitude)
depth_weight <- 1 / (1 + eq$depth)
eq_strength <- mag_weight * depth_weight

strength_matrix <- matrix(
  eq_strength,
  nrow = nrow(dist_matrix),
  ncol = length(eq_strength),
  byrow = TRUE
)

lambda <- 0.0001

distance_decay <- exp(-lambda * dist_matrix)

quarters <- sort(unique(muni$quarter))

# Non cumulative exposure 
for(q in quarters){
  
  # earthquakes occurring THIS quarter only
  eq_now <- which(eq$quarter == q)
  
  if(length(eq_now) == 0){
    muni$exposure[muni$quarter == q] <- 0
    next
  }
  
  exposure_q <- rowSums(
    strength_matrix[, eq_now, drop = FALSE] *
      distance_decay[, eq_now, drop = FALSE],
    na.rm = TRUE
  )
  
  muni$exposure[muni$quarter == q] <- exposure_q
}


muni <- muni %>%
  mutate(
    post = ifelse(year(date) >= 2000, 1, 0),
    event_time = year(date) - 2000
  )


#-------------------------
# Models
#-------------------------

# Main spatial DiD model as baseline
model <- feols(
  price_index ~ exposure:post + perceived_risk |
    gemeente + quarter,
  data = muni,
  cluster = ~gemeente
)

summary(model)

# check dropped collinear vars
model$collin.var



# event study (diagnostic + dynamic effects)
event_model <- feols(
  price_index ~ i(event_time, exposure, ref = -1) +
    perceived_risk |
    gemeente + quarter,
  data = muni,
  cluster = ~gemeente
)

# Summary model
summary(event_model)

# Visualize parallel trends
iplot(
  event_model,
  main = "Event Study: Earthquake Exposure and Housing Prices",
  xlab = "Years Relative to 2000",
  ylab = "Effect on Housing Prices"
)







