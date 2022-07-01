DELETE FROM hlt_pt;
LOAD DATA INFILE '/private/tmp/hlt_pt.asc' INTO TABLE hlt_pt
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM hlt_pt;

DELETE FROM llt;
LOAD DATA INFILE '/private/tmp/llt.asc' INTO TABLE llt
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM llt;

DELETE FROM meddra_release;
LOAD DATA INFILE '/private/tmp/meddra_release.asc' INTO TABLE meddra_release
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM meddra_release;