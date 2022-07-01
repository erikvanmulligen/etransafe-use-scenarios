**Concordance tables**

1. identify the drugs that have preclinical and clinical findings and store these in the database.
   1. store the drugs (including the drug group)
2. on basis of these drugs retrieve the findings from eToxSys and MedLine
   1. for preclinical check if these are valid findings (not the 'no abnormalities found' and 0-dose group(controls))
   2. store the findings
3. map the preclinical findings to the clinical findings
   1. use all mapped findings on the lowest distance and check if one of them is contained in the list of clinical findings
   2. store the mapping
4. compute the concordance table
   1. for the various outcome groups (SOC, HLGT, HLT, PT)
   2. for different distance thresholds
   3. show the # findings that were mapped per drug (average)