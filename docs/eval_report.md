# PharmaAssist evaluation report

- Run: 2026-11-12 09:35 UTC against `http://localhost:8000`
- Result: **9/9 cases passed**

| Case | Result | Time | Critic | Revisions | Verdict | Cited files |
|---|---|---|---|---|---|---|
| Q1 warfarin contraindications | PASS | 10 s | approve | 0 | — | `dailymed-warfarin.md` |
| Q2 warfarin vs apixaban | PASS | 12 s | approve | 0 | — | `dailymed-apixaban.md`, `dailymed-warfarin.md` |
| Q3 warfarin + sertraline bleeding | PASS | 75 s | revise | 1 | needs_more_info | `dailymed-sertraline.md`, `dailymed-warfarin.md` |
| Q4 metformin at eGFR 25 | PASS | 13 s | approve | 0 | — | `dailymed-metformin.md` |
| Validate metformin, eGFR 25 | PASS | 14 s | approve | 0 | rejected | `dailymed-metformin.md` |
| Validate sertraline on warfarin | PASS | 77 s | revise | 1 | approved_with_warnings | `dailymed-sertraline.md`, `dailymed-warfarin.md` |
| Validate amoxicillin, amoxicillin allergy | PASS | 55 s | revise | 1 | rejected | `dailymed-amoxicillin.md` |
| Validate amoxicillin, penicillin allergy | PASS | 67 s | approve | 1 | rejected | `dailymed-amoxicillin.md`, `medlineplus-amoxicillin.md` |
| Write first-line T2D | PASS | 56 s | revise | 1 | approved | `dailymed-metformin.md` |

## Q1 warfarin contraindications

> What are the main contraindications for warfarin?

Plan: Identify the labeled contraindications for warfarin. → Summarize the main contraindications clearly and concisely.

Warfarin is contraindicated in:  

- **Pregnancy**, except in pregnant women with **mechanical heart valves** who are at high thromboembolic risk. [1]  
- **Hemorrhagic tendencies or blood dyscrasias.** [1]  
- **Recent or planned CNS or eye surgery**, or traumatic surgery with large open surfaces. [1]  
- Conditions with significant bleeding risk, including **active ulceration or overt GI, GU, or respiratory-tract bleeding; CNS hemorrhage; cerebral aneurysm; dissecting aorta; pericarditis/pericardial effusion; or bacterial endocarditis.** [1]  
- **Threatened abortion, eclampsia, or preeclampsia.** [1]  
- Patients who cannot be supervised and have a high likelihood of **nonadherence**. [1]  
- **Spinal puncture** or other procedures with potential for uncontrollable bleeding. [1]  
- **Hypersensitivity** to warfarin or product components, including anaphylaxis. [1]  
- **Major regional or lumbar block anesthesia** and **malignant hypertension**. [1]

**Reviewer notes**
- The pregnancy exception is conditional: the label permits warfarin in pregnant women with mechanical heart valves only when they are at high risk of thromboembolism.
- The list describes labeled contraindications; individual bleeding-risk assessment and procedural context may still be clinically relevant, but no additional qualification is provided in the retrieved passage.

**Sources**
[1] dailymed-warfarin.md — Warfarin (DailyMed label) › 4 CONTRAINDICATIONS

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Q2 warfarin vs apixaban

> Compare the contraindications of warfarin and apixaban. What conditions are shared and which are unique to each drug?

Plan: Identify labeled contraindications for warfarin. → Identify labeled contraindications for apixaban. → Compare the two lists to distinguish shared contraindications from those unique to each drug.

**Shared contraindications**

- **Active bleeding:** Warfarin contraindicates bleeding tendencies associated with active ulceration or overt gastrointestinal, genitourinary, or respiratory-tract bleeding, as well as several other bleeding-prone conditions; apixaban contraindicates **active pathological bleeding**. [1] [2]
- **Hypersensitivity:** Both are contraindicated with hypersensitivity to the drug/product components, including anaphylaxis. [1] [2]

**Contraindications unique to warfarin**

- **Pregnancy**, except for pregnant women with mechanical heart valves who are at high thromboembolic risk. [1]
- Hemorrhagic tendencies or blood dyscrasias. [1]
- Recent or contemplated central-nervous-system or eye surgery, or traumatic surgery with large open surfaces. [1]
- CNS hemorrhage, cerebral aneurysm, dissecting aorta, pericarditis/pericardial effusion, or bacterial endocarditis. [1]
- Threatened abortion, eclampsia, or preeclampsia. [1]
- Unsupervised patients with conditions associated with likely high non-compliance. [1]
- Spinal puncture or other procedures with potential for uncontrollable bleeding; major regional or lumbar-block anesthesia. [1]
- Malignant hypertension. [1]

**Contraindications unique to apixaban**

- The label lists no additional contraindications beyond active pathological bleeding and severe hypersensitivity. [2]

**Reviewer notes**
- “Active bleeding” is a high-level comparison rather than identical label wording: apixaban specifies “active pathological bleeding,” while warfarin lists bleeding tendencies associated with active ulceration or overt gastrointestinal, genitourinary, or respiratory tract bleeding, plus CNS hemorrhage and other listed conditions.
- The pregnancy exception for warfarin is conditional: it applies to pregnant women with mechanical heart valves who are at high risk of thromboembolism.
- The apixaban label’s contraindication is specifically a “severe hypersensitivity reaction,” whereas the warfarin label says hypersensitivity to warfarin or any product component; the shared category is appropriate but the wording differs.

**Sources**
[1] dailymed-warfarin.md — Warfarin (DailyMed label) › 4 CONTRAINDICATIONS
[2] dailymed-apixaban.md — Apixaban (DailyMed label) › 4 CONTRAINDICATIONS

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Q3 warfarin + sertraline bleeding

> A patient currently on warfarin is prescribed sertraline. What is the risk of bleeding and what monitoring is recommended?

Plan: Validate the sertraline prescription in a patient receiving warfarin for potential interaction-related bleeding risk. → Review the evidence on bleeding risk with concomitant sertraline and warfarin. → Identify recommended clinical and INR monitoring after starting sertraline with warfarin.

**Bleeding risk:** Sertraline and other drugs that inhibit serotonin reuptake increase bleeding risk; concomitant warfarin may add to or potentiate this risk. Reported events range from bruising, hematoma, nosebleeds, and petechiae to life-threatening hemorrhage. [1] [2] Warfarin can itself cause major or fatal bleeding. [3]

Risk is higher with high-intensity anticoagulation (**INR >4.0**) and with factors including age ≥65 years, variable INRs, prior gastrointestinal bleeding, hypertension, cerebrovascular disease, anemia, malignancy, trauma, renal impairment, certain concomitant drugs, and long-duration warfarin therapy. [3] Maintaining INR in the therapeutic range does not eliminate bleeding risk. [3]

**Monitoring:** Carefully monitor INR when sertraline is used with warfarin. [1] Increase INR-monitoring frequency after initiating sertraline, because warfarin labeling directs more frequent INR monitoring when other drugs are started, stopped, or dose-changed; the label does not specify an exact post-initiation interval. [3]

**Patient counseling:** Inform the patient that sertraline plus warfarin increases bleeding risk and advise reporting bleeding signs or symptoms. [1] Warfarin labeling includes prolonged bleeding, unusual bruising or bleeding, nosebleeds, gum bleeding, red/dark-brown urine, red or tar-black stools, headache, dizziness, weakness, pain, swelling, or discomfort among reportable signs. [4]

**Reviewer notes**
- No exact INR-testing interval after sertraline initiation is specified in the cited labeling; monitoring frequency should be individualized to the clinical situation. Warfarin labeling gives generally acceptable INR intervals of 1–4 weeks only after INR stabilization, while also directing additional/more frequent testing when medications are initiated or changed.
- The patient’s baseline bleeding risk is unknown. It depends on factors such as INR intensity, age, prior gastrointestinal bleeding, variable INRs, renal impairment, comorbidities, and other concomitant drugs.
- The appropriate therapeutic INR target depends on the indication for warfarin; the cited material does not establish the patient’s target range.

**Sources**
[1] dailymed-sertraline.md — Sertraline (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.3 Increased Risk of Bleeding
[2] dailymed-sertraline.md — Sertraline (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 Clinically Significant Drug Interactions
[3] dailymed-warfarin.md — Warfarin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Hemorrhage
[4] dailymed-warfarin.md — Warfarin (DailyMed label) › 17 PATIENT COUNSELING INFORMATION

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Q4 metformin at eGFR 25

> A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin contraindicated at this level of renal function, and what is the threshold?

Plan: Check metformin labeling for renal-function contraindications using eGFR. → Identify the eGFR threshold at which metformin is contraindicated and apply it to eGFR 25 mL/min.

Yes. An eGFR of **25 mL/min** is below the labeled contraindication threshold, so metformin is contraindicated at this renal-function level. [1]

The threshold is **eGFR below 30 mL/min/1.73 m²**. [2]

**Sources**
[1] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.3 Recommendations for Use in Renal Impairment
[2] dailymed-metformin.md — Metformin (DailyMed label) › 4 CONTRAINDICATIONS

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate metformin, eGFR 25

> Validate this prescription for the patient: metformin 500 mg twice daily.

Plan: Assess whether metformin 500 mg twice daily is appropriate for a 67-year-old patient with eGFR 25 mL/min/1.73 m². → Check renal contraindications and label-based dosing restrictions for metformin. → Determine whether the prescription should be accepted, modified, or avoided.

**Verdict: Rejected.** Metformin 500 mg orally twice daily should **not** be prescribed for this patient because his eGFR is 25 mL/min/1.73 m². Metformin is contraindicated when eGFR is below 30 mL/min/1.73 m²; if a patient taking it later falls below this threshold, the label directs discontinuation. [1] [2] [3]

At age 67, renal function also warrants more frequent assessment because older age increases the risk of metformin-associated lactic acidosis. [4] [5]

**Reviewer notes**
- The conclusion assumes the reported eGFR of 25 mL/min/1.73 m² is current and applicable to prescribing; the label directs assessment of renal function before initiation and periodically thereafter.

**Sources**
[1] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.3 Recommendations for Use in Renal Impairment
[2] dailymed-metformin.md — Metformin (DailyMed label) › 4 CONTRAINDICATIONS
[3] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.6 Renal Impairment
[4] dailymed-metformin.md — Metformin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Lactic Acidosis
[5] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.5 Geriatric Use

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate sertraline on warfarin

> Validate this prescription for the patient: sertraline 50 mg once daily.

Plan: Confirm that sertraline 50 mg once daily is an appropriate labeled regimen for this 58-year-old patient, considering renal and hepatic function. → Check for clinically relevant interaction and bleeding-risk considerations with concurrent warfarin. → Determine whether the prescription can be validated or requires prescriber review/monitoring adjustments.

**Conditional validation—prescriber/indication clarification needed.** The automated prescription check returned **approved with warnings** for the warfarin interaction. [1] [2] [3] [4] [5]

- **Indication-dependent dose:** Sertraline **50 mg once daily** is the labeled adult starting dose for **MDD or OCD**. It is **not** the labeled starting dose for **panic disorder, PTSD, or social anxiety disorder**, for which the labeled adult starting dose is **25 mg once daily**. The indication was not provided, so prescriber clarification is required before treating this regimen as fully validated. [6]

- **Renal/hepatic status:** No sertraline dose adjustment is needed in mild-to-severe renal impairment; the reported eGFR is 80 mL/min/1.73 m². [7] No hepatic adjustment is indicated for the reported absence of hepatic impairment. If mild hepatic impairment were present, the starting dose and therapeutic range would be half the usual daily dosage; sertraline is not recommended in moderate or severe hepatic impairment. [8]

- **Warfarin:** Concurrent sertraline and warfarin can increase bleeding risk, and sertraline labeling directs careful INR monitoring. [1] [2] After sertraline initiation, perform **more frequent INR monitoring**; warfarin labeling directs this whenever another medication is initiated, discontinued, or dose-changed. [9] [4] Adjust warfarin only as clinically warranted by INR monitoring. [10]

**Reviewer notes**
- Not verified against the sources: “The automated prescription check returned approved with warnings” is not supported by any retrieved passage.
- Not verified against the sources: “No hepatic adjustment is indicated for the reported absence of hepatic impairment” is not explicitly stated in the cited label passage. The passage only provides dose modifications for mild impairment and says use is not recommended in moderate/severe impairment.
- Not verified against the sources: “Prescriber clarification is required” is a reasonable workflow conclusion given the unknown indication, but the cited dosing passage does not state that clarification is required.
- The appropriateness of 50 mg once daily depends on the intended indication: it is the labeled adult starting dose for MDD/OCD but PD/PTSD/SAD start at 25 mg daily. The indication is unknown.
- The warfarin-sertraline combination is not described as contraindicated, but both labels require careful/more frequent INR monitoring when sertraline is initiated; bleeding risk remains even if INR is therapeutic.
- The sertraline label directs clinicians to inform patients about increased bleeding risk with anticoagulants. The draft does not include this counseling point.
- Before initiating sertraline, the label directs screening for personal or family history of bipolar disorder, mania, or hypomania; this information is not supplied.
- The profile lists no other medications/allergies, but validation remains conditional on the list being complete. Sertraline is contraindicated with MAOIs (including linezolid and IV methylene blue), pimozide, and known sertraline hypersensitivity.

**Sources**
[1] dailymed-sertraline.md — Sertraline (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.3 Increased Risk of Bleeding
[2] dailymed-sertraline.md — Sertraline (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 Clinically Significant Drug Interactions
[3] dailymed-sertraline.md — Sertraline (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 Clinically Significant Drug Interactions
[4] dailymed-warfarin.md — Warfarin (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 General Information
[5] dailymed-warfarin.md — Warfarin (DailyMed label) › 7 DRUG INTERACTIONS › 7.3 Drugs that Increase Bleeding Risk
[6] dailymed-sertraline.md — Sertraline (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.1 Dosage in Patients with MDD, OCD, PD, PTSD, and SAD
[7] dailymed-sertraline.md — Sertraline (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.7 Renal Impairment
[8] dailymed-sertraline.md — Sertraline (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.4 Dosage Modifications in Patients with Hepatic Impairment
[9] dailymed-warfarin.md — Warfarin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.4 Monitoring to Achieve Optimal Anticoagulation
[10] dailymed-warfarin.md — Warfarin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Hemorrhage

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate amoxicillin, amoxicillin allergy

> Validate this prescription for the patient: amoxicillin 500 mg every 8 hours.

Plan: Confirm the indication and intended duration for amoxicillin 500 mg every 8 hours. → Screen the prescription against the documented amoxicillin allergy (hives) and determine whether amoxicillin is contraindicated. → Review available patient factors and concomitant medications for dosing or safety issues.

**Do not validate or dispense without prescriber review.**

- The reported amoxicillin-associated hives require clarification of the prior reaction before treatment. Serious, occasionally fatal hypersensitivity reactions are more likely in people with a history of penicillin hypersensitivity, and the label directs careful inquiry about previous reactions before starting amoxicillin. [1] Amoxicillin is formally contraindicated only for patients with a history of a **serious** hypersensitivity reaction (for example, anaphylaxis or Stevens-Johnson syndrome) to amoxicillin or other beta-lactam antibiotics. [2]

- Indication and duration are missing. Confirm a proven or strongly suspected bacterial infection; consider culture/susceptibility results when available, or local epidemiology and susceptibility patterns when they are not. [3] Use without a proven or strongly suspected bacterial infection or prophylactic indication is unlikely to benefit the patient and increases resistance risk. [4]

- **Regimen suitability:** 500 mg every 8 hours is labeled for adults and patients weighing >40 kg with severe ear/nose/throat, skin/skin-structure, or genitourinary infections, and for mild/moderate or severe lower-respiratory infections. Thus appropriateness depends on diagnosis, severity, and the patient’s unknown weight. [5] Treatment should continue at least 48–72 hours after symptoms resolve or bacterial eradication; *S. pyogenes* infections require at least 10 days. [5]

- **Renal function:** eGFR is unknown. With GFR 10–30 mL/min, the labeled regimen is 500 mg or 250 mg every 12 hours; with GFR <10 mL/min, every 24 hours. [6]

- No concomitant medications are listed. If present, probenecid can increase and prolong amoxicillin concentrations, and allopurinol increases rash incidence. [7] [8]

**Reviewer notes**
- The documented reaction is “hives,” but the cited contraindication is limited to a history of a *serious* hypersensitivity reaction (examples: anaphylaxis or Stevens-Johnson syndrome). The available history does not establish whether this patient’s prior reaction meets that threshold; the label requires careful inquiry about prior reactions before treatment.
- The diagnosis, infection severity, intended duration, culture/susceptibility data, weight, and renal function are unknown. These determine whether 500 mg every 8 hours is appropriate and whether renal adjustment is required.
- Hepatic impairment is unknown. The retrieved MedlinePlus passage instructs patients to tell the clinician about current or past liver disease, but it does not provide a dose-adjustment recommendation.
- Although no concomitant medicines are listed, the available passages also identify oral anticoagulants (monitor INR/possible dose adjustment) and other antibacterials (possible in-vitro interference with bactericidal effect, with uncertain clinical significance) as interaction considerations.

**Sources**
[1] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Anaphylactic Reactions
[2] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 4 CONTRAINDICATIONS
[3] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 1 INDICATIONS AND USAGE
[4] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.5 Development of Drug-Resistant Bacteria
[5] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.2 Dosage for Adults and Pediatric Patients Aged 3 Months (12 weeks) and Older
[6] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.5 Dosage in Renal Impairment for Adults and Pediatric Patients Aged 3 Months and Older and Weight Greater than 40 kg
[7] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 Probenecid
[8] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 7 DRUG INTERACTIONS › 7.3 Allopurinol

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate amoxicillin, penicillin allergy

> Validate this prescription for the patient: amoxicillin 500 mg every 8 hours.

Plan: Check amoxicillin for contraindications based on the documented penicillin anaphylaxis. → Assess whether amoxicillin 500 mg every 8 hours is appropriate for the available adult renal and hepatic profile. → Determine whether the prescription can be validated or should be rejected based on the patient-specific findings.

**Verdict: rejected.** Amoxicillin is contraindicated because the patient has documented penicillin anaphylaxis, a serious hypersensitivity reaction to a β-lactam antibacterial drug. [1]

**Dose assessment:** Amoxicillin 500 mg every 8 hours is a labeled regimen for severe ear/nose/throat, skin/skin-structure, or genitourinary infections, and for mild/moderate or severe lower respiratory tract infections; the actual indication and infection severity were not provided. [2] Amoxicillin formulations are taken by mouth, but the prescribed route was not supplied. [3]

**Renal function:** The reported eGFR is 90 mL/min/1.73 m². The label expresses its adjustment threshold as **GFR <30 mL/min** and states that dose reduction is generally not required unless renal impairment is severe; therefore, severe-renal-impairment dose reduction is not indicated based on the reported renal value. [4] [5]

**Hepatic function:** Hepatic impairment is unknown. The retrieved passages do not provide a hepatic dose-adjustment recommendation.

Do not prescribe amoxicillin because the allergy contraindication overrides dosing considerations. [1]

**Reviewer notes**
- The labeled adult dosing table cited applies to adults and pediatric patients weighing more than 40 kg; the patient’s weight is unknown, although the patient is age 30.
- Appropriateness of 500 mg every 8 hours apart from the contraindication depends on the infection indication and severity, which are not provided. The regimen is labeled for severe ear/nose/throat, skin/skin-structure, or genitourinary infections and for lower respiratory tract infections of either severity.
- The renal label uses GFR thresholds, whereas the supplied result is eGFR; the reported value of 90 is well above the label’s severe-impairment threshold of GFR less than 30 mL/min.
- Hepatic impairment is unknown, and the retrieved passages provide no hepatic dose-adjustment recommendation.

**Sources**
[1] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 4 CONTRAINDICATIONS
[2] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.2 Dosage for Adults and Pediatric Patients Aged 3 Months (12 weeks) and Older
[3] medlineplus-amoxicillin.md — Amoxicillin (MedlinePlus) › How should this medicine be used?
[4] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.5 Dosage in Renal Impairment for Adults and Pediatric Patients Aged 3 Months and Older and Weight Greater than 40 kg
[5] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.6 Dosing in Renal Impairment

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Write first-line T2D

> Write a prescription for this request and validate it for the patient: first-line oral therapy for newly diagnosed type 2 diabetes.

Plan: Identify the first-line oral therapy for newly diagnosed type 2 diabetes from the available drug-label corpus. → Validate metformin suitability for this 60-year-old patient using renal function, hepatic status, pregnancy status, allergies, conditions, and current medications. → Draft a metformin prescription appropriate to the validated request.

**Prescription:** Metformin 500 mg orally twice daily with meals. Increase by 500 mg weekly based on glycemic control and tolerability; maximum 2550 mg/day in divided doses. [1]

The retrieved label supports metformin, with diet and exercise, to improve glycemic control in adults with type 2 diabetes mellitus; it does **not** address whether metformin is first-line therapy. [2]

**Validation verdict: Approved.** eGFR 75 mL/min/1.73 m² is above the range in which initiation is not recommended (30–45 mL/min/1.73 m²) and above the contraindication threshold (<30 mL/min/1.73 m²). [3] No hepatic impairment is reported; metformin is not recommended with hepatic impairment. [4] The provided history reports no metformin allergy, metabolic acidosis, or diabetic ketoacidosis; these are labeled contraindications. [5]

Obtain eGFR before treatment and at least annually; assess renal function more frequently if risk for renal impairment develops. [3]

**Conditional hold instructions:** Temporarily discontinue during procedures with restricted food or fluid intake and discontinue during hypoxic acute illness (e.g., shock, acute myocardial infarction, sepsis, or hypoxemia). [6] For iodinated-contrast imaging, stop at or before the procedure if eGFR is 30–60, there is liver disease, alcoholism, heart failure, or intra-arterial contrast is planned; re-evaluate eGFR after 48 hours and restart only if renal function is stable. [7] Avoid excessive alcohol intake. [6]

Pregnancy/lactation risk cannot be definitively established from the label: pregnancy data are limited, and lactation data are insufficient to determine infant or milk-production effects. [8] [9]

**Reviewer notes**
- The patient is documented as not pregnant and not breastfeeding, but the answer does not explicitly validate these statuses; instead it gives general label uncertainty. The label states pregnancy data are insufficient to determine drug-associated major-birth-defect or miscarriage risk, and lactation data are insufficient to determine effects on the infant or milk production.
- Current medications are listed as empty, but the answer does not explicitly validate the absence of listed interacting medicines. The label calls for consideration/monitoring with carbonic anhydrase inhibitors, drugs that reduce metformin clearance, alcohol, insulin/secretagogues, and drugs affecting glycemic control.
- Alcohol use is not included in the profile. The label warns against excessive alcohol intake, so suitability remains conditional on counseling/assessment of alcohol use.
- Although age 60 is below the label's age-65 risk-factor threshold, renal function should still be monitored at least annually; more frequent assessment is conditional on risk for renal impairment developing.
- The corpus does not establish metformin as “first-line” therapy. The draft appropriately acknowledges this limitation, but the prescription should make clear that first-line status cannot be verified from the retrieved label rather than implying that this conclusion was established.

**Sources**
[1] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.1 Adult Dosage
[2] dailymed-metformin.md — Metformin (DailyMed label) › 1 INDICATIONS AND USAGE
[3] dailymed-metformin.md — Metformin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Lactic Acidosis
[4] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.7 Hepatic Impairment
[5] dailymed-metformin.md — Metformin (DailyMed label) › 4 CONTRAINDICATIONS
[6] dailymed-metformin.md — Metformin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Lactic Acidosis
[7] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.4 Discontinuation for Iodinated Contrast Imaging Procedures
[8] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.1 Pregnancy
[9] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.2 Lactation

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*
