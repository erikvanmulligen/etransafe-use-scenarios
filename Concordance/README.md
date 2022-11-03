# Notes on concordance tables
# 7 january 2022
1. read article [Clark](https://app.box.com/s/47j3aue06e4z57p3mhc710zhm7b2trr4) on how to do the concordance tables
2. leave FAERS (and later dialyMed out) in order to compare with Clark
3. store in the mapping database the minimal specificity so that in a later stage this can be used to filter 
4. count compounds in the table and not observations
5. count per System Organ Class (SOC), makes it easier to determine TN (for a particular SOC check if the drug has no preclinical findings and clinical findings pertaining to that SOC
6. next round: separate per species

# pseudo code

```` 
for each SOC:
begin
    for each drug:
    begin
        get the preclinical findings for the drug and SOC
        if there are preclinical findings:
            if there is any preclinical_finding mapped to clinical_finding
                increase TP
            else
                increase FP
        else:
            get the clinical findings for the drug and SOC
            if there are clinical findings:
                increase FN
            else
                increase TN
    end
end

```` 

**17 maart 2022**
- opnieuw aanmaken van database
  - create_drug_mapping_with_part_inchikey -usernam tester -password tester -db_server localhost -db_db concordance -db_username root -db_password crosby9 -drugs ../data/drugs_mapping.20220317.json
  - create_local_cache_db -username tester -password tester -clear -db_server localhost -db_db concordance -db_user root -db_pass crosby9 -drugs ../data/drugs_mapping.20220317.json
  - add_pt_to_db
    - opslag van socs, hlts en hlgts bij een preferred term

**18 maart 2022**
- er kunnen bij een pt meerdere socs voorkomen. Ik koos altijd de eerste, dat leidt tot rare situaties (pts die groter zijn dan de bijbehorende soc)
- nu alle socs (hlts, hlgts) opgehaald per pt en die allemaal aflopen
- nog doen: niet vergelijken of de pt zowel klinisch als preklinisch voorkomt, maar of een soc gevonden bij de preklinische termen geassocieerd met een compound ook bij de socs geassocieerd met klinische termen voorkomt
- er komen een aantal LLT termen voor: 10013908 ipv preferred term

**19 mei 2022**
- kijken hoe het zit met de afstand bij bijvoorbeeld vascular disorders

<code>6                                  Vascular disorders  0            -17            21     77  114  35   52 0.69         0.31         1.00 1.00 0.00</code>

- maken script om per group te kijken welke findings er toe behoren en per match te kijken wat de afstand is


 