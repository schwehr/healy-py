-- Since 2009-May-17
-- Kurt Schwehr, UNH CCOM/JHC
CREATE TABLE healy_summary (
  heading REAL, -- ashtech PAT heading in degrees
  lon REAL, -- GGA position
  lat REAL, -- GGA position
  ts TIMESTAMP, -- ZDA
  depth REAL, -- CTR depth_m in meters
  air_temp REAL, -- ME[ABC] Deg C
  rel_humid REAL, -- ME[ABC]
  pressure REAL, -- ME[ABC] barometric pressure_mb (milli bar)
  precip REAL, -- ME[ABC] milimeters
  sea_temp REAL -- STA Deg C
);
-- oxa
   -- oxygen_temp_c
-- vtg
   -- track_deg_true
   -- speed_knots
-- shr
   -- roll_deg
   -- pitch_deg
   -- heave_deg
-- wd
   -- wind_dir_true_true_deg
   -- wind_speed_true_mps
-- wind
   -- cog_deg
-- winch  location {aft,stbd}
   -- wire_out_m
-- sound_vel
   -- sound_velocity
-- sra
   -- short_wave_rad
   -- long_wave_rad


CREATE TABLE wind_side (
  key INTEGER PRIMARY KEY,
  ts TIMESTAMP,   
  wind_speed REAL, -- kts
  wind_dir REAL, -- deg true?
  wind_speed_rel REAL, -- kts
  wind_dir_rel REAL, -- deg true?
  sog REAL, -- kts
  cog REAL, -- kts
  heading REAL -- kts
);

CREATE TABLE air_temp (
  key INTEGER PRIMARY KEY,
  ts TIMESTAMP,
  temp_f REAL,
  temp_c REAL
);

CREATE TABLE samos (
  key INTEGER PRIMARY KEY,
  ts TIMESTAMP,
  sensor VARCHAR(20),
  sensor_id VARCHAR(4),
  mean REAL,
  last_value REAL,
  sum REAL,
  stddev REAL,
  n INTEGER
);

CREATE TABLE noaa_baro (
  key INTEGER PRIMARY KEY,
  ts TIMESTAMP,
  mean REAL,
  last_value REAL,
  sum REAL,
  n INTEGER
);

CREATE TABLE noaa_sst (
  key INTEGER PRIMARY KEY,
  ts TIMESTAMP,
  mean REAL,
  last_value REAL,
  sum REAL,
  n INTEGER
);

