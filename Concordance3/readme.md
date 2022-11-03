### Logica ###
Er zijn 4 stappen in het bouwen van de concordantie tabellen:

1.	het vinden van de compounds die zowel klinisch als een preklinisch voorkomen (1_identify_drugs.py). Dat gebeurt nu op basis van de inchikey. Dat zou ook op de eerste 14 tekens van de inchi kunnen. Voor elke drug worden de finding ids opgeslagen
2. het ophalen van de findings voor de finding_ids (2_get_findings.py)
3. het mappen van de HPATH concepten naar MedDRA codes d.m.v. (3_mapping.py)
4. het construeren van de eigenlijke concordantie tabellen (concordance_tablev2.py). Daar wordt per drug gekeken voor alle preklinisch concepten die met een drug geassocieerd zijn, welke klinische concepten per aggregatie (SOC, HLGT, HLT) overeenkomen.
	5. Daar zouden we nog kunnen kijken naar aggregatie per SMQ


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

**30 juni 2022**

Naar aanleiding van de bespreking van de resultaten van de concordantie tabellen kijken
wat het zou betekenen als we:

1. beperken tot MedLine
2. maximale afstand: 0, 1, 2, 3, 4
3. beperken tot treatment related findings


### 22 juli 2022 ###
Suggesties om de precisie te verbeteren: 

* kijken of de inchi groep meer matches oplevert  
* kijken of de mapping van HPATH -> MedDRA kan worden uitgebreid met vader concepten
    * eerst kijken of er een verschil is tussen de niveaus van HPATH mapping voor preklinische bronnen en voor die van klinische bronnen. Ze zijn allemaal pt's en hebben in de MedDRA hierarchie een afstand van 4 tot de SOC. PT->HLT->HLGT->SOC
    * kijken hoe de logica eruit ziet om de classificatie te maken
    * kijken hoe de matching van drugs gedaan wordt (nu 298)

### Fri 19 august 2022 ###
* Preklinisch corrigeren voor hoe vaak een HPATH term in de controle groep voorkomt.
* Kijken of we clusters kunnen maken: een HPATH term met al zijn kinderen die gemapped is naar een HLT/PT term met al zijn kinderen
* Brengt ons bij de vraag: hoeveel HPATH termen en MedDRA termen worden nu gemapped voor de verschillende compounds

* resultaten: opnieuw gedraaid alleen voor eTOxSys en Medline, dose groep 0 uitgesloten (zie getAllFindingByIds in primitiveadapter.py)
* iets betere LR+ bij alleen