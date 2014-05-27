Licensed under the Apache 2.0 license.

KML / Google Earth visualization of the Healy Ship Track and Images as
derived from the hourly ship tracks posted on the LDGO satelite of the
Aloftcon camera.

WARNING: the code in the project is not pretty and all the URLs are
currently hardcoded.

-kurt schwehr

Run as a cronjob: (crontab -e)

15 * * * * (cd /Users/schwehr/projects/src/healy/ && make update)
