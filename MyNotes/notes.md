local to remote
rsync -avz /Users/manu/Documents/DOE_METRICS_REPORTER/ maddy@perlmutter.nersc.gov:/global/homes/m/maddy/MAGENT/


remote to local
rsync -avz maddy@perlmutter.nersc.gov:/global/homes/m/maddy/MAGENT/ /Users/manu/Documents/DOE_METRICS_REPORTER/