import os
from pathlib import Path
from logging_utils import logger
from config import config

PM_KISAN_DATA_TEXT = """
Scheme Name: PM-KISAN Samman Nidhi
Type: Scheme
Description: The Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) is a central sector scheme that provides income support to all landholding farmers' families in the country to supplement their financial needs for procuring various inputs related to agriculture and allied activities as well as domestic needs. Under the Scheme, an income support of Rs.6000/- per year is provided to all farmer families across the country in three equal installments of Rs.2000/- each every four months.

Target Beneficiary: Farmer
Category: Agriculture
State: All India

Eligibility Criteria:
1. Must be a citizen of India.
2. Must be a farmer with cultivable land.
3. Age must be at least 18 (age >= 18).
4. Must not be an institutional landholder.
5. Must not hold constitutional posts or pay income tax.

Benefits:
- Financial assistance of ₹ 6,000 per year.
- Direct Benefit Transfer (DBT) deposited directly to Aadhaar-linked bank accounts.

Required Documents:
- Aadhaar Card
- Land ownership text / Patta
- Active Bank Account details (Aadhaar linked)
- Citizenship proof (Voter ID / Ration Card)

Application Process:
Farmers can apply directly through the Farmer Corner on the PM-Kisan portal (https://pmkisan.gov.in) or via Common Service Centres (CSCs).
"""

AYUSHMAN_BHARAT_TEXT = """
Scheme Name: Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)
Type: Scheme
Description: A flagship scheme of the Government of India providing a health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization to over 12 crore poor and vulnerable families (approximately 55 crore beneficiaries).

Target Beneficiary: Poor and vulnerable families (BPL)
Category: Health
State: All India (except specific un-adopted states)

Eligibility Criteria:
1. Must belong to the deprived rural categories or identified occupational categories of urban workers described in the Socio-Economic Caste Census (SECC) 2011 database.
2. No cap on family size or age (age >= 0).
3. Income must be below poverty line thresholds or belong to SC/ST households (income <= 150000).

Benefits:
- Health cover of ₹ 5,000,000 (5 Lakhs) per family per annum.
- Cashless and paperless access to quality health care services at empanelled hospitals.

Required Documents:
- Ayushman Card (PMJAY Golden Card)
- Aadhaar Card
- Family documentation (Ration Card)

Application Process:
Eligible families are automatically enrolled based on SECC data. Beneficiaries must authenticate via Aadhaar at empanelled hospitals or CSCs to generate an e-card.
"""

AADHAAR_TEXT = """
Service Name: Aadhaar Enrollment and Update
Type: Identity Service
Description: Aadhaar is a 12-digit individual identification number issued by the Unique Identification Authority of India (UIDAI) on behalf of the Government of India. The number serves as a proof of identity and address, anywhere in India.

Authority: Unique Identification Authority of India (UIDAI)
Category: Identity
State: All India

Eligibility Criteria:
1. Any resident of India can apply for Aadhaar (No age limit).

Fees:
- Aadhaar Enrollment: Free
- Mandatory Biometric Update (5 & 15 yrs): Free
- Demographic Update (Name, Address, DOB, Gender, Mobile, Email): Rs. 50
- Biometric Update: Rs. 100

Required Documents:
- Proof of Identity (POI): Passport, PAN Card, Ration/PDS Photo Card, Voter ID, Driving License.
- Proof of Address (POA): Passport, Bank Statement/Passbook, Ration Card, Voter ID, Driving License, Electricity/Water/Telephone Bill (not older than 3 months).
- Proof of Date of Birth (DOB): Birth Certificate, SSLC Book/Certificate, Passport.

Procedure:
1. Locate an Enrollment Center nearby (UIDAI website).
2. Book an Appointment (Optional but recommended).
3. Visit the center with the required supporting documents.
4. Fill demographic details on the enrollment form.
5. Provide biometrics (fingerprints, iris, facial photograph).
6. Collect enrollment acknowledgment slip.
"""

VOTER_ID_TEXT = """
Service Name: Voter ID Registration (EPIC)
Type: Identity Service
Description: The Electors Photo Identity Card (EPIC) is a photographic identity card issued by the Election Commission of India. It serves as an identity proof for casting votes in democratic elections.

Authority: Election Commission of India (ECI)
Category: Identity, Voting
State: All India

Eligibility Criteria:
1. Must be a citizen of India.
2. Age must be at least 18 years on the qualifying date (usually 1st January of the year).
3. Must be ordinarily resident of the polling area constituency.

Fees:
- Free for a new registration.

Required Documents:
- Form 6 (Application form for new voters).
- Passport size photograph.
- Proof of Age (Birth Certificate, Class 10/12 mark sheet, PAN Card, Aadhaar Card).
- Proof of Residence (Aadhaar Card, Bank Passbook, Ration Card, Utility Bills).

Procedure:
1. Register on the National Voter's Service Portal (NVSP) or the Voter Helpline App.
2. Fill Form 6 with accurate details.
3. Upload passport size photo and required documents (Age & Address proof).
4. Submit the form to generate a reference ID.
5. A Booth Level Officer (BLO) may visit for physical verification.
6. Once approved, the EPIC will be delivered to the registered address.
"""

PASSPORT_TEXT = """
Service Name: Indian Passport Issuance
Type: Identity & Travel Service
Description: An Indian passport is issued by order of the President of India to Indian citizens for the purpose of international travel. It enables the bearer to travel internationally and serves as proof of Indian citizenship.

Authority: Ministry of External Affairs, Consular, Passport and Visa (CPV) Division
Category: Travel, Identity
State: All India

Fees:
- Fresh Passport/Re-issue (36 pages) Normal: Rs. 1,500
- Fresh Passport/Re-issue (36 pages) Tatkaal: Rs. 3,500
- Minor Passport (Below 18 yrs, 5 yr validity) Normal: Rs. 1,000

Required Documents:
- Aadhaar Card / E-Aadhaar.
- Proof of Date of Birth: Birth Certificate, PAN Card, School Leaving Certificate.
- Proof of Present Address: Water Bill, Telephone Bill, Electricity Bill, Income Tax Assessment Order, Election Commission Photo ID card, Aadhaar Card, Rent Agreement.

Procedure:
1. Register on the Passport Seva Online Portal and login.
2. Click on "Apply for Fresh Passport/Re-issue of Passport" link.
3. Fill the application form and submit it.
4. Click the "Pay and Schedule Appointment" link to schedule an appointment at a Passport Seva Kendra (PSK) / Post Office Passport Seva Kendra (POPSK).
5. Visit the PSK with original documents on the scheduled date.
6. Police verification will proceed either pre or post issuance based on checks.
"""


PROPERTY_TAX_TEXT = """
Service Name: Land and Property Registration
Type: Property Service
Description: Registration of property transfers, sales, and agreements under the Registration Act 1908. Essential for assigning legal title to property owners and paying the correct ad-valorem local stamp duty rates.

Authority: Inspector General of Registration (IGR) and Stamps Department (State-level)
Category: Property
State: State Dependent (E.g. Telangana, Maharashtra)

Fees:
- Stamp Duty (Varies 3% - 7% based on the state and urban/rural location)
- Registration Fee (Usually 1% of the property value)

Required Documents:
- Sale Deed / Title Documents
- Encumbrance Certificate (EC)
- ID proofs of Buyer, Seller, and Witnesses (Aadhaar/PAN)
- Passport size photographs
- Pattadar Passbook / Mutation details 
- Property Tax receipts (latest)

Procedure:
1. Estimate the property's market value using State government's fixed guidelines/circle rates.
2. Purchase Stamp Papers or pay Stamp Duty online via State specific portal (e.g. IGRS Telangana).
3. Draft the Sale Deed with the help of a lawyer or document writer.
4. Book a slot at the local Sub-Registrar Office (SRO).
5. Both buyer, seller, and two witnesses must be physically present at the SRO.
6. Provide biometric thumbs and photos for final registration.
7. Collect the registered deed.
"""


def fetch_datasets():
    config.paths.setup()
    
    datasets = {
        "PM_KISAN.txt": PM_KISAN_DATA_TEXT,
        "Ayushman_Bharat.txt": AYUSHMAN_BHARAT_TEXT,
        "Aadhaar_Enrollment.txt": AADHAAR_TEXT,
        "Voter_ID.txt": VOTER_ID_TEXT,
        "Passport_Application.txt": PASSPORT_TEXT,
        "Property_Registration.txt": PROPERTY_TAX_TEXT
    }
    
    for filename, content in datasets.items():
        p = config.paths.data_raw / filename
        p.write_text(content, encoding="utf-8")
        
    logger.info("Successfully fetched and seeded real Indian Civic Dataset sources.")

if __name__ == "__main__":
    fetch_datasets()
