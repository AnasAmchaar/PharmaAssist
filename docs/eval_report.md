# PharmaAssist evaluation report

- Run: 2026-11-12 11:00 UTC against `http://localhost:8000`
- Result: **10/10 cases passed**

| Case | Result | Time | Critic | Revisions | Verdict | Cited files |
|---|---|---|---|---|---|---|
| Q1 warfarin contraindications | PASS | 12 s | approve | 0 | — | `dailymed-warfarin.md` |
| Q2 warfarin vs apixaban | PASS | 16 s | approve | 0 | — | `dailymed-apixaban.md`, `dailymed-warfarin.md` |
| Q3 warfarin + sertraline bleeding | PASS | 18 s | approve | 0 | — | `dailymed-sertraline.md`, `dailymed-warfarin.md` |
| Q4 metformin at eGFR 25 | PASS | 10 s | approve | 0 | — | `dailymed-metformin.md` |
| Validate metformin, eGFR 25 | PASS | 16 s | approve | 0 | rejected | `dailymed-metformin.md` |
| Validate sertraline on warfarin | PASS | 60 s | revise | 1 | approved_with_warnings | `dailymed-sertraline.md`, `dailymed-warfarin.md` |
| Validate amoxicillin, amoxicillin allergy | PASS | 42 s | revise | 1 | rejected | `dailymed-amoxicillin.md` |
| Validate amoxicillin, penicillin allergy | PASS | 19 s | approve | 0 | rejected | `dailymed-amoxicillin.md` |
| Write first-line T2D | PASS | 102 s | approve | 1 | approved | `dailymed-metformin.md` |
| Prescription photo, eGFR 25 | PASS | 18 s | approve | 0 | rejected | `dailymed-metformin.md` |

## Q1 warfarin contraindications

> What are the main contraindications for warfarin?

Plan: Identify the labeled contraindications for warfarin. → Summarize the main contraindication categories concisely.

Warfarin is contraindicated in **pregnancy**, except for pregnant women with **mechanical heart valves** who are at high thromboembolic risk. [1]

Other main contraindication categories are:  
- **Hemorrhagic tendencies or blood dyscrasias.** [1]  
- **Recent or planned CNS or eye surgery**, or traumatic surgery with large open surfaces. [1]  
- **Active or high-risk bleeding conditions**, including active ulceration or overt GI, genitourinary, or respiratory bleeding; CNS hemorrhage; cerebral aneurysm or dissecting aorta; pericarditis/pericardial effusion; and bacterial endocarditis. [1]  
- **Threatened abortion, eclampsia, or preeclampsia.** [1]  
- **Procedures or anesthesia with risk of uncontrolled bleeding**, including spinal puncture and major regional or lumbar block anesthesia. [1]  
- **Unsupervised patients** with conditions associated with a potentially high level of noncompliance. [1]  
- **Hypersensitivity** to warfarin or a product component, including anaphylaxis. [1]  
- **Malignant hypertension.** [1]

**Reviewer notes**
- The pregnancy exception is limited to pregnant women with mechanical heart valves who are at high risk of thromboembolism; the draft states this correctly. The passage does not establish that warfarin should routinely be used in this group, only that the labeled pregnancy contraindication has this exception.
- “Active or high-risk bleeding conditions” is a summary label. The cited contraindication is specifically “bleeding tendencies associated with” the listed conditions; the listed examples in the draft are accurate.
- For procedures, the label separately lists spinal puncture/other diagnostic or therapeutic procedures with potential for uncontrollable bleeding and major regional or lumbar block anesthesia. The draft accurately summarizes both, but clinical applicability depends on the particular procedure and bleeding risk.

**Sources**
[1] dailymed-warfarin.md — Warfarin (DailyMed label) › 4 CONTRAINDICATIONS

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Q2 warfarin vs apixaban

> Compare the contraindications of warfarin and apixaban. What conditions are shared and which are unique to each drug?

Plan: Identify labeled contraindications for warfarin. → Identify labeled contraindications for apixaban. → Compare the two lists to separate shared contraindications from those unique to each drug.

**Shared contraindication categories**
- **Active bleeding:** apixaban contraindicates *active pathological bleeding*; warfarin contraindicates bleeding tendencies associated with *active ulceration or overt bleeding* of the gastrointestinal, genitourinary, or respiratory tract, and also lists several high-bleeding-risk conditions. [1] [2]
- **Severe hypersensitivity:** apixaban is contraindicated with severe hypersensitivity to apixaban (including anaphylaxis); warfarin is contraindicated with hypersensitivity to warfarin or product components (e.g., anaphylaxis). [1] [2]

**Contraindications unique to warfarin**
- Pregnancy, except pregnant women with mechanical heart valves at high thromboembolic risk. [2]
- Hemorrhagic tendencies or blood dyscrasias. [2]
- Recent or planned central-nervous-system or eye surgery, or traumatic surgery producing large open surfaces. [2]
- CNS hemorrhage, cerebral aneurysm, dissecting aorta, pericarditis/pericardial effusions, or bacterial endocarditis. [2]
- Threatened abortion, eclampsia, or preeclampsia. [2]
- Unsupervised patients with conditions associated with likely high noncompliance. [2]
- Spinal puncture or other procedures with potential for uncontrollable bleeding; major regional or lumbar block anesthesia; or malignant hypertension. [2]

**Contraindications unique to apixaban**
- The apixaban label lists no additional contraindication beyond active pathological bleeding and severe hypersensitivity. [1]

**Reviewer notes**
- The active-bleeding contraindications are overlapping categories rather than identically worded conditions: apixaban contraindicates any “active pathological bleeding,” whereas warfarin specifies bleeding tendencies associated with active ulceration or overt bleeding in particular tracts, along with other named bleeding-associated conditions.
- Warfarin pregnancy is contraindicated except for pregnant women with mechanical heart valves who are at high thromboembolic risk; this is an explicit labeled exception, not a general endorsement of warfarin use in pregnancy.
- Warfarin’s “unsupervised patients” contraindication is conditional on conditions associated with a potential high level of noncompliance.

**Sources**
[1] dailymed-apixaban.md — Apixaban (DailyMed label) › 4 CONTRAINDICATIONS
[2] dailymed-warfarin.md — Warfarin (DailyMed label) › 4 CONTRAINDICATIONS

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Q3 warfarin + sertraline bleeding

> A patient currently on warfarin is prescribed sertraline. What is the risk of bleeding and what monitoring is recommended?

Plan: Review the bleeding risk of concomitant warfarin and sertraline use. → Identify recommended monitoring for bleeding and anticoagulation when sertraline is initiated with warfarin.

**Bleeding risk:** Sertraline can increase bleeding risk, and using it with warfarin may further potentiate that risk. Reported bleeding associated with serotonin-reuptake inhibitors ranges from bruising, hematoma, nosebleeds, and petechiae to life-threatening hemorrhage. [1] Warfarin specifically lists sertraline among serotonin-reuptake inhibitors that increase bleeding risk when used concomitantly. [2] Warfarin itself can cause major or fatal bleeding; an INR >4.0 is a listed bleeding-risk factor. [3]

**Recommended monitoring:**  
- Carefully monitor the **INR** when sertraline is used with warfarin. [1]  
- Obtain **more frequent INR monitoring when sertraline is started** (and if it is stopped or its dose is changed), with warfarin dose adjustment as needed to maintain the intended therapeutic range. [3] [4]  
- Monitor closely for clinical bleeding; warfarin labeling directs patients to report signs and symptoms of bleeding. [3]

**Reviewer notes**
- No specific INR-testing interval is provided for starting sertraline; the warfarin label directs more frequent INR monitoring when medications are initiated, stopped, or dose-changed, with frequency based on the clinical situation.
- A therapeutic INR does not eliminate bleeding risk, including the pharmacodynamic bleeding risk associated with concomitant sertraline.
- The degree of incremental bleeding risk for this individual depends on patient-specific factors (for example, age, prior GI bleeding, renal impairment, baseline INR stability, and other concomitant drugs), which are not provided. તેમ

**Sources**
[1] dailymed-sertraline.md — Sertraline (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.3 Increased Risk of Bleeding
[2] dailymed-warfarin.md — Warfarin (DailyMed label) › 7 DRUG INTERACTIONS › 7.3 Drugs that Increase Bleeding Risk
[3] dailymed-warfarin.md — Warfarin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Hemorrhage
[4] dailymed-warfarin.md — Warfarin (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 General Information

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Q4 metformin at eGFR 25

> A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin contraindicated at this level of renal function, and what is the threshold?

Plan: Check metformin labeling for renal contraindications by eGFR. → Identify whether eGFR 25 mL/min meets the contraindication threshold and state that threshold.

Yes. An eGFR of **25 mL/min** is below the labeling threshold, so metformin is **contraindicated**. [1]

The threshold is **eGFR below 30 mL/min/1.73 m²** (severe renal impairment). [2]

**Reviewer notes**
- The label’s threshold is expressed as eGFR <30 mL/min/1.73 m²; the question reports 25 mL/min without a stated body-surface-area normalization. In routine reporting eGFR is generally normalized to 1.73 m², but the answer appropriately states the labeled unit.
- The answer addresses renal-function contraindication only. The label also lists hypersensitivity and acute or chronic metabolic acidosis as contraindications, but these are not relevant to the specific renal-threshold question.

**Sources**
[1] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.3 Recommendations for Use in Renal Impairment
[2] dailymed-metformin.md — Metformin (DailyMed label) › 4 CONTRAINDICATIONS

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate metformin, eGFR 25

> Can I start my patient on metformin 500 mg twice daily?

Plan: Validate whether metformin 500 mg twice daily is appropriate given the patient’s eGFR of 25 mL/min/1.73 m². → Check labeled renal contraindications and initiation recommendations for metformin. → Summarize whether metformin can be started in this patient.

**No.** The prescription validator’s verdict is **rejected**: metformin 500 mg orally twice daily should not be initiated at an eGFR of 25 mL/min/1.73 m². [1] [2] [3]

Metformin is contraindicated when eGFR is **below 30 mL/min/1.73 m²**; if a patient already taking it later falls below this threshold, the label directs discontinuation. [2]

For comparison, initiation is also not recommended at eGFR **30–45 mL/min/1.73 m²**. [2] At age 67, renal function warrants more frequent assessment because age ≥65 increases the risk of metformin-associated lactic acidosis. [4]

**Reviewer notes**
- The conclusion depends on the reported eGFR of 25 mL/min/1.73 m² being current and accurate. The label requires renal-function assessment before initiation and periodic reassessment.
- Although the patient is 67 and the label calls for more frequent renal assessment in elderly patients, age does not alter the immediate conclusion: eGFR below 30 mL/min/1.73 m² is a contraindication.

**Sources**
[1] dailymed-metformin.md — Metformin (DailyMed label) › 4 CONTRAINDICATIONS
[2] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.3 Recommendations for Use in Renal Impairment
[3] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.6 Renal Impairment
[4] dailymed-metformin.md — Metformin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Lactic Acidosis

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate sertraline on warfarin

> I'd like to prescribe sertraline 50 mg once daily for this patient. Any problems?

Plan: Validate the proposed sertraline 50 mg once-daily prescription against the patient profile and sertraline labeling. → Check for clinically relevant interactions between sertraline and warfarin, including bleeding risk and anticoagulation monitoring considerations. → Summarize whether any label-based problems or precautions apply to this prescription.

**Verdict: approved with warnings, but the indication is required to confirm the appropriate starting dose.** The patient has no reported renal or hepatic impairment requiring a sertraline adjustment; no dose adjustment is needed with mild-to-severe renal impairment. [1]  

For **adult MDD or OCD**, sertraline **50 mg once daily** is the labeled starting dose. For **panic disorder, PTSD, or social anxiety disorder**, the labeled starting dose is **25 mg once daily**. [2]  

**Warfarin interaction:** Sertraline plus warfarin may potentiate bleeding risk. Counsel the patient on this increased bleeding risk and carefully monitor INR. [3] [4] Arrange more frequent INR testing when sertraline is initiated, after dose changes, and when it is stopped; warfarin labeling directs more frequent INR monitoring whenever another drug is started, stopped, or dose-changed. [5] [6] Sertraline and warfarin are highly protein-bound; monitor for adverse reactions and adjust either drug’s dose if warranted. [7]  

**Medication-reconciliation/contraindication check:** Do not use sertraline with an MAOI (including linezolid or IV methylene blue), within 14 days of stopping an MAOI, with pimozide, or with known sertraline hypersensitivity. [8] Verify no other serotonergic agents are being used; if concomitant use is warranted, monitor for serotonin syndrome, particularly during initiation and dose increases. [4]

**Reviewer notes**
- The indication is unknown. A 50 mg daily start is labeled for adult MDD/OCD, whereas PD, PTSD, and SAD start at 25 mg daily; therefore the prescription cannot be fully approved until the indication is confirmed.
- The profile reports no hepatic impairment, but this is conditional on that history being accurate. Mild hepatic impairment requires half the usual recommended dose, and moderate/severe impairment is not recommended.
- The degree of warfarin-related bleeding risk and the appropriate INR-testing frequency depend on unknown factors such as current INR stability, other bleeding-risk factors, and unreported prescription/OTC/herbal agents.
- Personal or family history of bipolar disorder, mania, or hypomania is unknown.
- The absence of MAOIs, pimozide, other serotonergic drugs, and QT-prolonging drugs is not fully established by the provided medication list alone.

**Sources**
[1] dailymed-sertraline.md — Sertraline (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.7 Renal Impairment
[2] dailymed-sertraline.md — Sertraline (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.1 Dosage in Patients with MDD, OCD, PD, PTSD, and SAD
[3] dailymed-sertraline.md — Sertraline (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.3 Increased Risk of Bleeding
[4] dailymed-sertraline.md — Sertraline (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 Clinically Significant Drug Interactions
[5] dailymed-warfarin.md — Warfarin (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 General Information
[6] dailymed-warfarin.md — Warfarin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Hemorrhage
[7] dailymed-sertraline.md — Sertraline (DailyMed label) › 7 DRUG INTERACTIONS › 7.1 Clinically Significant Drug Interactions
[8] dailymed-sertraline.md — Sertraline (DailyMed label) › 4 CONTRAINDICATIONS

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate amoxicillin, amoxicillin allergy

> Is amoxicillin 500 mg every 8 hours OK for this patient?

Plan: Confirm the intended indication and assess whether amoxicillin is appropriate given the documented amoxicillin allergy (hives). → Validate the proposed amoxicillin 500 mg every 8 hours regimen against patient-specific factors, including renal and hepatic function if available.

**Not enough information to confirm that 500 mg every 8 hours is appropriate.**

- For patients aged ≥3 months who weigh **>40 kg**, 500 mg every 8 hours is a labeled regimen for **severe** ear/nose/throat, skin/skin-structure, or genitourinary infections, and for **mild/moderate or severe lower-respiratory-tract infections**. It is not the listed mild/moderate regimen for the former infection groups. [1]  
- The indication, infection severity, and weight are unknown, so the proposed regimen cannot be matched to the labeled schedule. [1]
- The history of amoxicillin-associated hives requires careful assessment of prior hypersensitivity before starting treatment. Amoxicillin is formally contraindicated if the patient has had a **serious** hypersensitivity reaction, such as anaphylaxis or Stevens–Johnson syndrome, to amoxicillin or another beta-lactam antibacterial. [2] [3]
- Renal function is also needed. For GFR **10–30 mL/min**, the labeled regimen is 500 mg or 250 mg every 12 hours; for GFR **<10 mL/min**, 500 mg or 250 mg every 24 hours, depending on infection severity. [4]

**Reviewer notes**
- Not verified against the sources: “Renal function is also needed” is too categorical. The label states that dose reduction is generally not required unless renal impairment is severe (GFR <30 mL/min); revise to say that renal function/eGFR is needed to rule out severe renal impairment or that the proposed q8h regimen should not be used if GFR is <30 mL/min.
- Hives is a documented amoxicillin-allergy symptom, but the provided contraindication passage specifies a prior *serious* hypersensitivity reaction and gives anaphylaxis/SJS as examples. The available information does not establish whether this prior episode meets that threshold. The answer should not imply that hives is automatically outside the contraindication, and should retain the need for prescriber assessment of the prior reaction.
- The appropriateness of 500 mg every 8 hours depends on the actual infection, its severity, organism susceptibility, and patient weight. The labeled adult/over-40-kg schedules cited do not establish appropriateness for an unknown indication.
- For H. pylori/duodenal-ulcer treatment, the label provides different combination regimens (1 g with other agents), so 500 mg every 8 hours as amoxicillin monotherapy would not match those labeled regimens.
- eGFR is unknown. If GFR is 10–30 mL/min or <10 mL/min, the q8h schedule does not match the renal-adjusted schedules.

**Sources**
[1] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.2 Dosage for Adults and Pediatric Patients Aged 3 Months (12 weeks) and Older
[2] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Anaphylactic Reactions
[3] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 4 CONTRAINDICATIONS
[4] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.5 Dosage in Renal Impairment for Adults and Pediatric Patients Aged 3 Months and Older and Weight Greater than 40 kg

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Validate amoxicillin, penicillin allergy

> Is amoxicillin 500 mg every 8 hours OK for this patient?

Plan: Validate whether amoxicillin 500 mg every 8 hours is appropriate given the documented penicillin anaphylaxis and available renal function.

**Verdict: rejected.** Amoxicillin is contraindicated in patients with a serious hypersensitivity reaction—including anaphylaxis—to penicillins or other β-lactam antibacterials. This patient reports penicillin anaphylaxis. [1] [2]

Renal function does not require dose reduction at eGFR 90 mL/min/1.73 m²; labeled renal dose adjustments apply to severe impairment (GFR <30 mL/min). [3] [4]

Therefore, **do not prescribe amoxicillin 500 mg every 8 hours** for this patient. [1]

**Reviewer notes**
- The label’s renal-adjustment threshold is expressed as GFR, whereas the available patient value is eGFR (90 mL/min/1.73 m²). This does not suggest a need for adjustment here, but the measures are not identically termed in the source.
- The underlying infection and its severity are unknown. Although this does not alter the conclusion that amoxicillin is contraindicated with documented penicillin anaphylaxis, 500 mg every 8 hours is a labeled regimen only for certain adult infection/severity categories.

**Sources**
[1] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 4 CONTRAINDICATIONS
[2] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Anaphylactic Reactions
[3] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.5 Dosage in Renal Impairment for Adults and Pediatric Patients Aged 3 Months and Older and Weight Greater than 40 kg
[4] dailymed-amoxicillin.md — Amoxicillin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.6 Dosing in Renal Impairment

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Write first-line T2D

> What should I prescribe this patient for newly diagnosed type 2 diabetes?

Plan: Assess whether metformin is appropriate as initial therapy for this 60-year-old with newly diagnosed type 2 diabetes, given eGFR 75 mL/min/1.73 m² and no hepatic impairment. → Draft an initial metformin prescription if appropriate.

**Prescription:** Metformin hydrochloride 500 mg orally twice daily with meals, as an adjunct to diet and exercise for type 2 diabetes mellitus. This is a labeled adult starting dose; the labeled maximum is 2550 mg/day in divided doses. [1] [2]

**Renal/hepatic assessment:** Her eGFR of 75 mL/min/1.73 m² does not meet the threshold where initiation is not recommended (eGFR 30–45 mL/min/1.73 m²) or contraindicated (<30 mL/min/1.73 m²). Reported absence of hepatic impairment does not trigger the label’s hepatic-impairment caution. [3] [4] [5]

**Before prescribing:** Confirm no metformin hypersensitivity and no acute or chronic metabolic acidosis, including diabetic ketoacidosis; these are contraindications. [6]

Assess renal function before initiation and periodically thereafter; obtain eGFR at least annually. [3] [4]

**If iodinated contrast is planned:** Discontinue metformin at or before the procedure if eGFR is 30–60 mL/min/1.73 m², there is liver disease, alcoholism, or heart failure, or intra-arterial contrast will be used; re-evaluate eGFR after 48 hours and restart only if renal function is stable. [7]

**Validation verdict: approved.** The prescribed 500 mg twice-daily dose is label-supported for this patient profile.

**Reviewer notes**
- Metformin remains conditional on confirming no hypersensitivity and no acute or chronic metabolic acidosis/diabetic ketoacidosis; these are not established by the supplied profile.
- Hepatic impairment is reported absent, but the label states metformin is not recommended with clinical or laboratory evidence of hepatic disease; newly identified liver disease would change the assessment.
- Future iodinated contrast exposure, intra-arterial contrast, liver disease, alcoholism, heart failure, acute hypoxic illness, restricted intake around surgery/procedures, or decline in renal function can require temporary discontinuation or reassessment.
- The label directs dose increases based on glycemic control and tolerability; the patient’s glycemic data and tolerability after initiation are not provided.

**Sources**
[1] dailymed-metformin.md — Metformin (DailyMed label) › 1 INDICATIONS AND USAGE
[2] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.1 Adult Dosage
[3] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.3 Recommendations for Use in Renal Impairment
[4] dailymed-metformin.md — Metformin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Lactic Acidosis
[5] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.7 Hepatic Impairment
[6] dailymed-metformin.md — Metformin (DailyMed label) › 4 CONTRAINDICATIONS
[7] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.4 Discontinuation for Iodinated Contrast Imaging Procedures

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*

## Prescription photo, eGFR 25

> Is this prescription safe for my patient? *(+1 image)*

Plan: Identify the prescription as metformin 500 mg by mouth twice daily with meals and validate it against the patient’s age and eGFR of 25 mL/min/1.73 m². → Check metformin labeling for renal contraindications, dose restrictions, and relevant safety considerations in severe renal impairment. → Determine whether the prescribed regimen is safe for this patient based on the available profile.

**Verdict: Rejected — this prescription is not safe for this patient.** [1]

The patient’s eGFR is **25 mL/min/1.73 m²**. Metformin is contraindicated when eGFR is **below 30 mL/min/1.73 m²**; the label directs that it not be prescribed and that it be discontinued if eGFR falls below this threshold. [2] [1]

Severe renal impairment increases metformin accumulation and the risk of metformin-associated lactic acidosis. [3] At age 67, the patient also has an increased risk of this complication, and renal function requires more frequent assessment. [4] [5]

**Do not initiate or continue metformin 500 mg by mouth twice daily at this renal function.** [2]

**Reviewer notes**
- The conclusion assumes the reported eGFR of 25 mL/min/1.73 m² is current and applicable to this prescribing decision. If renal function is rapidly changing or the value is erroneous, it should be confirmed; however, based on the provided value, the label contraindication is unambiguous.

**Sources**
[1] dailymed-metformin.md — Metformin (DailyMed label) › 4 CONTRAINDICATIONS
[2] dailymed-metformin.md — Metformin (DailyMed label) › 2 DOSAGE AND ADMINISTRATION › 2.3 Recommendations for Use in Renal Impairment
[3] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.6 Renal Impairment
[4] dailymed-metformin.md — Metformin (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Lactic Acidosis
[5] dailymed-metformin.md — Metformin (DailyMed label) › 8 USE IN SPECIFIC POPULATIONS › 8.5 Geriatric Use

*Disclaimer: This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and educational purposes only. It is not medical advice and does not replace the judgment of a qualified clinician or pharmacist.*
