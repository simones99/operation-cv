from core.cv_handler import extract_sections

cv_text = '''Simone MEZZABOTTA
Mail: simonemezzabotta99@gmail.com | Phone: +39 3663505519 | LinkedIn | GitHub
PROFESSIONAL SUMMARY
Data Analyst & Policy Specialist with 3+ years of experience at the intersection of data science, international governance, and public policy.
Proven ability to translate complex datasets into actionable insights for strategic decision-making, with hands-on expertise in Python, SQL,
Power BI, and Salesforce. Career highlights include building machine learning models to uncover policy bias, optimizing KPIs for EU
operations, and advising anti-corruption investment strategy through data-driven approaches. Passionate about leveraging analytics to drive
ethical governance and global development outcomes.
EXPERIENCE
European Commission
Blue Book Trainee, DG SCIC | Webstreaming Team: Data & Metrics (IT-O24 Acceptance Rate: 4.25%)
• Designed and deployed a semi-automated Power BI dashboard that tracked 120+ KPIs related to the
Commission’s interpreted and streamed conferences, improving operational oversight and enabling data-driven
negotiations on inter-agency service chargebacks
• Automated reporting on speaker microphone usage via a VBA and Power Query system, reducing data input time
by 37% and cutting file storage requirements by 54%, improving reporting efficiency across weekly events.
• Produced 27 rapid-turnaround statistical reports within 3-hour windows to support urgent strategic decisions on
conference delivery performance and resource utilization.
• Improved cross-database SQL query performance by 27% (Oct–Dec 2024) by optimizing joins and indexing over
cloud-based systems, increasing data accessibility for real-time dashboarding and reporting.
Basel Institute on Governance | Leading Organization in the fight against corruption and other financial crimes.
Anti-Corruption and Research Intern | Basel Institute on Governance HQ
• Redesigned and streamlined the B20 Collective Action Hub’s dataset architecture using Excel and Python,
enhancing user navigation and enabling faster retrieval of anti-corruption case studies.
• Created multivariate regression models using Python and R to assess the impact of variables like GDP,
governance quality, and education on anti-corruption outcomes, directly shaping the 2023–2030 strategic
investment framework.
• Leveraged Salesforce CRM for segmentation, engagement tracking, and automated follow-ups, contributing to a
25% increase in donor retention and 15% growth in total donations over 8 months.
• Conducted hands-on Salesforce training for 50+ staff members using real-time dashboards and scenario-based
exercises, leading to a 70% improvement in platform utilization and CRM data consistency based on post-
training performance metrics.
EDUCATION
Brussels, Belgium
Oct 2024 – Feb 2025
Basel, Switzerland
Sep 2023 – Apr 2024
Master’s Degree in International Governance & Diplomacy | Sciences Po Paris
• Specialisation: Quantitative Research Methods | avg. 16.3/20 (GPA: 4.0) | Cum Laude (top 12%)
• Relevant coursework: AI for Policy Analysis, Global Financial Regulation, Data Governance, Advanced Python & R.
• Thesis: "Coercion, Territory, and Decision-Making: Explaining State Coercive Strategies" (Grade: 17/20).
• Most relevant project: Built a text classification model using BERT to detect biases in EU public policy languages.
Bachelor’s Degree in Diplomacy & International Affairs | Alma Mater Studiorum University of Bologna
• Field of study: Economics & IR – avg. 29.8/30 (GPA: 4.0) | Final Grade: 110/110 and honours.
• Relevant coursework: Macro & Microeconomics, Statistics, Financial Markets, Regional Studies.
• Most relevant project: Authored a report linking ESG adoption in SME to profitability.
• Fully funded studies based on academic merit (highest GPA in the department).
SKILLS & CERTIFICATIONS
Paris, France
Aug 2021 – Jul 2023
Bologna, Italy
Sep 2018 – Jul 2021
• Data Analysis & BI: Power BI, Tableau, Excel (pivot tables, dashboards), SQL (mySQL, HeidiSQL, MongoDb), Power Query. Streamlit.
• Programming: Python (Pandas, NumPy, Matplotlib, scikit-learn), R, STATA
• Data Engineering/Workflow Tools: Power Automate, VBA, Anaconda, DAX.
• CRM & Marketing Analytics: Salesforce, Mailchimp
• Certifications (AI & Data): Google Advanced Data Analytics Certificate; Microsoft Career Essentials in Data Analysis; LinkedIn: Power BI:
Integrating AI & Machine Learning; Anaconda Python for Data Science Professional Certificate.
• Methodologies: Descriptive & Inferential Statistics; Machine Learning (Regression, Clustering, PCA, Random Forests); Data Visualisation
Best Practices; Dashboarding & Reporting Automation; A/B Testing
• Languages: Italian (Native); English (C2); French (C1+); Spanish (C1+).
• Soft Skills: Stakeholder Communication, Insight Presentation, Project Management, Cross-functional Collaboration, Analytical Thinking.
ADDITIONAL / EXTRA CURRICULAR EXPERIENCE
Mondo Internazionale - Senior Researcher | 2022 - Now
• Designed and executed a stakeholder analysis strategy that led to collaboration with UN SDSN, World Food
Forum, and the Italian Ministry of Defense.
• Produced data-informed policy reports using Excel and R for clients including the Italian Navy and Bocconi.
'''

sections = extract_sections(cv_text)
for name, content in sections.items():
    print(f"=== {name} ===")
    print(content)
    print()
