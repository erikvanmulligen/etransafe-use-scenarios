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



 