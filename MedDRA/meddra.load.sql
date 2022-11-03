DELETE FROM 1_low_level_term;
LOAD DATA INFILE '/private/tmp/llt.asc' INTO TABLE 1_low_level_term
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_low_level_term;

DELETE FROM 1_pref_term;
LOAD DATA INFILE '/private/tmp/pt.asc' INTO TABLE 1_pref_term
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_pref_term;

DELETE FROM 1_hlt_pref_term;
LOAD DATA INFILE '/private/tmp/hlt.asc' INTO TABLE 1_hlt_pref_term
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_hlt_pref_term;

DELETE FROM 1_hlt_pref_comp;
LOAD DATA INFILE '/private/tmp/hlt_pt.asc' INTO TABLE 1_hlt_pref_comp
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_hlt_pref_comp;

DELETE FROM 1_hlgt_pref_term;
LOAD DATA INFILE '/private/tmp/htlgt.asc' INTO TABLE 1_hlgt_pref_term
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_hlgt_pref_term;

DELETE FROM 1_hlgt_hlt_comp;
LOAD DATA INFILE '/private/tmp/hlgt_hlt.asc' INTO TABLE 1_hlgt_hlt_comp
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_hlgt_hlt_comp;

DELETE FROM 1_soc_term;
LOAD DATA INFILE '/private/tmp/soc.asc' INTO TABLE 1_soc_term
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_soc_term;

DELETE FROM 1_soc_hlgt_comp;
LOAD DATA INFILE '/private/tmp/soc_hlgt.asc' INTO TABLE 1_soc_hlgt_comp
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_soc_hlgt_comp;

DELETE FROM 1_md_hierarchy;
LOAD DATA INFILE '/private/tmp/mdhier.asc' INTO TABLE 1_md_hierarchy
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_md_hierarchy;

DELETE FROM 1_soc_intl_order;
LOAD DATA INFILE '/private/tmp/intl_ord.asc' INTO TABLE 1_soc_intl_order
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_soc_intl_order;

DELETE FROM 1_smq_list;
LOAD DATA INFILE '/private/tmp/smq_list.asc' INTO TABLE 1_smq_list
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_smq_list;

DELETE FROM 1_smq_content;
LOAD DATA INFILE '/private/tmp/smq_content.asc' INTO TABLE 1_smq_content
FIELDS TERMINATED BY '$' LINES TERMINATED BY '$\r\n';
SELECT COUNT(*) FROM 1_smq_content;