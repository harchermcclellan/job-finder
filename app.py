#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import serpapi 
from dotenv import load_dotenv
import os
from db import make_key, get_cached, set_cached


load_dotenv()  # read .env into environment variables

API_KEY = os.getenv("SERP_API_KEY")
DATABASE_URL=os.getenv("DATABASE_URL")
app = Flask(__name__)


def search_jobs(title: str, location: str, work_type: str, salary: str) -> list[dict]:
    """
    Return a list of job dicts. Each dict should have:
        title       str   – job title
        company     str   – company name
        location    str   – where the role is based
        work_type   str   – Remote / Hybrid / On-site
        salary      str   – salary range (or "" if unknown)
        url         str   – link to the full application
        summary     str   – short description / snippet
        posted      str   – posting date (e.g. "2 days ago")
    """

    client = serpapi.Client(api_key=API_KEY)
    results = client.search({
        "engine": "google_jobs",
        "q": title,
        "location": location,
        "google_domain": "google.com",
        "hl": "en",
        "gl": "us",
    })
    
    response = []

    for result in results["jobs_results"]:
        extended = get_extended_details(result, ["salary", "schedule_type", "posted_at", "dental_coverage", "health_insurance"])
        response.append({
            "title":     result.get("title", ""),
            "company":   result.get("company_name", ""),
            "location":  result.get("location", ""),
            "work_type": extended.get("schedule_type", ""),
            "url":       result.get("source_link", ""),
            "salary":    extended.get("salary", ""),
            "posted":    extended.get("posted_at", ""),
        })
    return response


def get_extended_details(result, details_list):
  
    details_output = {}
    for detail_field in details_list:
        try:
            details_output[detail_field] = result["detected_extensions"][detail_field]
        except:
            details_output[detail_field] = "See full listing"

    
    return details_output

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    data      = request.get_json()
    titles    = data.get("titles", [])
    location  = data.get("location", "").strip()
    work_type = data.get("work_type", "any")
    salary    = data.get("salary", "").strip()

    if not titles:
        return jsonify({"error": "Please enter at least one job title."}), 400

    all_jobs = []
    for title in titles:
        cache_key = make_key(title, location, work_type, salary)
        cached = get_cached(cache_key)
        try:
            if cached:
                all_jobs.extend(cached)
            else:
                jobs = search_jobs(title, location, work_type, salary)
                set_cached(cache_key, title, location, jobs)
                all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error searching for '{title}': {e}")
            import traceback; traceback.print_exc()


    return jsonify({"jobs": all_jobs})


if __name__ == "__main__":
    app.run(debug=True)


def get_placeholder():
    placeholder= {
        "jobs_results": [
            {
            "title": "Graphic Designer",
            "company_name": "Cell Signaling Technology",
            "location": "Danvers, MA",
            "via": "Indeed",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=phJPm6Ds4FE-sgoFAAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXNsQrCMBAAUFz7CU63KaKNCC46iYWC4KR7uYYjiZx3IRek_oWfrC5vfc1n1iz6gjkmDx1ZCkIFNnDREYyw-Agq0KsGpvkx1prt4JwZt8Eq1uRbr0-nQqNO7qGj_RksYqHMWGnY7bdTmyWslmdihtsvQE4S4E4-irKGNySBDuVFxdZwPX0BpGvV45MAAAA&shmds=v1_ATWGeePq5XgzE3Hqc42KRV6RDJvhyhd8shB1SEqAQuWFTB5qVg&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=phJPm6Ds4FE-sgoFAAAAAA%3D%3D",
            "thumbnail": "https://serpapi.com/searches/69c6ca4931aafe3e972a6c09/images/7q95LRhnXUo8AuAIEafrXQiw7vuLwWstWp1UxOPYHwo.jpeg",
            "extensions": [
                "3 days ago",
                "81K–120K a year",
                "Full-time",
                "Paid time off",
                "Health insurance"
            ],
            "detected_extensions": {
                "posted_at": "3 days ago",
                "salary": "81K–120K a year",
                "schedule_type": "Full-time",
                "paid_time_off": True,
                "health_insurance": True
            },
            "source_link": "https://www.indeed.com/viewjob?jk=a9b71d0d25e1de09",
            "description": "Who we are…\n\nCell Signaling Technology (CST) is a different kind of life sciences company, one founded, owned, and run by active research scientists, with the highest standards of product and service quality, technological innovation, and scientific rigor for over 20 years. We consistently provide fellow scientists around the globe with best-in-class products and services to fuel their quests for discovery.\n\nHelping researchers find new solutions is our main mission every day, but it's not our only mission. We're also dedicated to helping identify solutions to other problems facing our world. We believe that all businesses must be responsible and work in partnership with local communities, while seeking to minimize their environmental impact. That's why we joined 1% for the Planet as its first life science member, and have committed to achieving net-zero emissions by 2029.\n\nThe role...\n\nThe Graphic Designer is a core member of the design team, reporting directly to the Creative Director. In this role, you will collaborate with a multidisciplinary team of marketing and communication specialists to conceptualize and produce high-impact visual assets across a variety of digital and traditional media formats. This is an on-site position based in Danvers, MA.\n\nYou'll have the opportunity to...\n\nProject Planning & Collaboration (15%)\n• Cross-Functional Partnership: Collaborate with Marketing Managers, Product Management, Scientific Writers, and Regional Managers to define project scope, goals, and deliverables\n• Autonomy & Ownership: Work with minimal supervision to manage the end-to-end design process, from initial conceptualization through final production and implementation\n• Project Management: Simultaneously manage multiple project timelines and coordinate with internal teams and external vendors to ensure timely delivery\n\nGraphic & Visual Design (65%)\n• Interactive Content & Motion Graphics: Design and produce compelling motion graphics, animated elements, and short-form video for use across social media channels, website content, and digital advertising, ensuring assets are optimized for engagement and modern digital standards\n• Proficient Toolset: Utilize a professional suite of tools, including Adobe Creative Cloud (Illustrator, InDesign, Photoshop, Premiere), and web publishing tools (HTML5, PDF)\n• Visual Assets: Create and curate custom iconography, photographic imagery, and illustrations that meet modern digital standards\n• Strategic Optimization: Actively research best practices and measure campaign impact to recommend design changes that improve performance and reduce production effort\n\nCorporate Branding & Identity (5%)\n• Brand Stewardship: Act as a guardian of the corporate style guide, ensuring all materials maintain a consistent, professional \"CST\" look and feel\n• Template Development: Build and maintain standardized Marcom templates to streamline design workflows while ensuring brand alignment\n• Identity Materials: Design core corporate identity assets, including stationery, business cards, logos, and global presentation templates\n\nPackaging & Product Design (5%)\n• Packaging Solutions: Conceptualize and design physical product packaging, including containers, sleeves, labels, and mailing envelopes\n• Strategic Alignment: Partner with Product Management to ensure all packaging designs meet both brand strategy requirements and strict regulatory standards\n\nMaintenance, Implementation & Support (10%).\n• Ongoing Support: Manage the maintenance and implementation of ongoing graphic projects, adapting materials for various formats, channels, and global regions as needed\n• Trend Innovation: Continuously research and implement new graphic design techniques, formats, and trends to keep visual content fresh and competitive\n\nWho you are and what you bring to the team...\n• Bachelor's degree in Graphic Design, Visual Arts, or a related field\n• Minimum of 5 years of related professional graphic design experience, preferably within a corporate or technical/scientific environment.\n• Highly proficient in Adobe Creative Suite (InDesign, Photoshop, Illustrator, Acrobat)\n• Knowledge of Adobe Premiere or comparable video editing software\n• Experience with creating compelling 2D & 3D animations\n• Experience with the four-color printing process, including preparing print files and overseeing press checks\n• Proficiency in Google Slides and Microsoft Office PowerPoint for global sales templates\n• Proven ability to manage the end-to-end design process (concept to finish) with minimal supervision\n• Strong organizational skills to manage multiple projects simultaneously under tight deadlines\n• Excellent communication skills with the ability to work across departments and international regions; confidence in presenting and explaining creative ideas\n• Excellent communication and content development skills\n• Ability to work cooperatively with many personalities and cultures\n• Ability to work independently\n\nIdeally, you have...\n• Experience in creative concept development for print, digital advertising, social media\n• Experience in developing compelling graphics and content for trade show and events environments\n• Experience in video production: shooting, editing, animating\n• Experience with creating compelling 2D & 3D animations\n• Experience with digital asset managers like Bynder\n• Experience creating and managing brand style guides\n• Experience in developing and editing Powerpoint and Google Slides templates and content\n\nPhysical Conditions/Physical Requirements...\n• Work environment is typically quiet for independent desk work and virtual meetings\n• The ability to perform repetitive motions with the wrists, hands, and fingers.\n• The ability to extend hands and arms in any direction to access materials, equipment, or a keyboard\n• The ability to sit for long periods of time (often more than 70% of the workday)\n• Ability to view and read information from a computer monitor, reports, and documents\n• Physically able to safely lift and carry 25 pounds to move, install, unpack PC equipment, office supplies, etc. as required\n\nThis position has a starting base salary range of $81,000 to $120,000 per year, which the company, in good faith, reasonably expects to pay for this role at the time of posting. Actual compensation within this range will be determined based on factors including, but not limited to, relevant skills, qualifications, experience, and internal equity.\n\nWhat we offer...\n\nAt Cell Signaling Technology (CST), we recognize that people will always be our most important asset. Providing a safe, inclusive, and stimulating working environment that understands the importance of diversity, human dignity, and meaningful work is as important as establishing company policies that incorporate excellent health insurance and pay benefits. We recognize that the development of people is the key to their happiness and thus ensure every employee has impactful discussions with their manager and develops actionable performance and professional development plans. Lastly, we are committed to engaging and supporting our employees in committees and philanthropy that benefit their local communities and environment through community investment programs.\n\nBenefits\n• Medical (BCBS) and Dental (Delta Dental) plans paid at 90%\n• Vision Insurance\n• Life Insurance, Short and Long Term Disability\n• Flexible Spending accounts\n• 401(k) Plan with 6% match\n• Tuition Reimbursement\n• Generous PTO package\n• Parental Leave\n• Pet Insurance\n• Employee Assistance Program\n• Onsite Subsidized Cafeteria\n• Free Parking\n\nCell Signaling Technology (CST) is committed to providing equal employment opportunities to all employees and applicants for employment without regard to race, color, religion, sex, sexual orientation, national origin, age, disability, genetic information, status as a veteran or as a member of the military or status in any group protected by applicable federal or state laws.\n\nIt is unlawful in Massachusetts to require or administer a lie detector test as a condition of employment or continued employment. An employer who violates this law shall be subject to criminal penalties and civil liability.\n\nAGENCIES\n\nAll resumes submitted by search firms/employment agencies to any employee at Cell Signaling Technology (CST) via email, the Internet, or in any form and/or method will be deemed the sole property of CST unless CST engaged such search firms/employment agencies for this position and a valid agreement with CST is in place. In the event a candidate who was submitted outside of the CST agency engagement process is hired, no fee or payment of any kind will be paid.\n\nIf you are a California resident, more details on how we process your personal information can be found here.",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "Interactive Content & Motion Graphics: Design and produce compelling motion graphics, animated elements, and short-form video for use across social media channels, website content, and digital advertising, ensuring assets are optimized for engagement and modern digital standards",
                    "Proficient Toolset: Utilize a professional suite of tools, including Adobe Creative Cloud (Illustrator, InDesign, Photoshop, Premiere), and web publishing tools (HTML5, PDF)",
                    "Bachelor's degree in Graphic Design, Visual Arts, or a related field",
                    "Minimum of 5 years of related professional graphic design experience, preferably within a corporate or technical/scientific environment",
                    "Highly proficient in Adobe Creative Suite (InDesign, Photoshop, Illustrator, Acrobat)",
                    "Knowledge of Adobe Premiere or comparable video editing software",
                    "Experience with creating compelling 2D & 3D animations",
                    "Experience with the four-color printing process, including preparing print files and overseeing press checks",
                    "Proficiency in Google Slides and Microsoft Office PowerPoint for global sales templates",
                    "Proven ability to manage the end-to-end design process (concept to finish) with minimal supervision",
                    "Strong organizational skills to manage multiple projects simultaneously under tight deadlines",
                    "Excellent communication skills with the ability to work across departments and international regions; confidence in presenting and explaining creative ideas",
                    "Excellent communication and content development skills",
                    "Ability to work cooperatively with many personalities and cultures",
                    "Ability to work independently",
                    "Experience in creative concept development for print, digital advertising, social media",
                    "Experience in developing compelling graphics and content for trade show and events environments",
                    "Experience in video production: shooting, editing, animating",
                    "Experience with creating compelling 2D & 3D animations",
                    "Experience with digital asset managers like Bynder",
                    "Experience creating and managing brand style guides",
                    "Experience in developing and editing Powerpoint and Google Slides templates and content",
                    "Physical Conditions/Physical Requirements..",
                    "Work environment is typically quiet for independent desk work and virtual meetings",
                    "The ability to perform repetitive motions with the wrists, hands, and fingers",
                    "The ability to extend hands and arms in any direction to access materials, equipment, or a keyboard",
                    "The ability to sit for long periods of time (often more than 70% of the workday)",
                    "Ability to view and read information from a computer monitor, reports, and documents",
                    "Physically able to safely lift and carry 25 pounds to move, install, unpack PC equipment, office supplies, etc. as required"
                ]
                },
                {
                "title": "Benefits",
                "items": [
                    "This position has a starting base salary range of $81,000 to $120,000 per year, which the company, in good faith, reasonably expects to pay for this role at the time of posting",
                    "Medical (BCBS) and Dental (Delta Dental) plans paid at 90%",
                    "Vision Insurance",
                    "Life Insurance, Short and Long Term Disability",
                    "Flexible Spending accounts",
                    "401(k) Plan with 6% match",
                    "Tuition Reimbursement",
                    "Generous PTO package",
                    "Parental Leave",
                    "Pet Insurance",
                    "Employee Assistance Program",
                    "Onsite Subsidized Cafeteria",
                    "Free Parking"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "The Graphic Designer is a core member of the design team, reporting directly to the Creative Director",
                    "In this role, you will collaborate with a multidisciplinary team of marketing and communication specialists to conceptualize and produce high-impact visual assets across a variety of digital and traditional media formats",
                    "Project Planning & Collaboration (15%)",
                    "Cross-Functional Partnership: Collaborate with Marketing Managers, Product Management, Scientific Writers, and Regional Managers to define project scope, goals, and deliverables",
                    "Autonomy & Ownership: Work with minimal supervision to manage the end-to-end design process, from initial conceptualization through final production and implementation",
                    "Project Management: Simultaneously manage multiple project timelines and coordinate with internal teams and external vendors to ensure timely delivery",
                    "Graphic & Visual Design (65%)",
                    "Visual Assets: Create and curate custom iconography, photographic imagery, and illustrations that meet modern digital standards",
                    "Strategic Optimization: Actively research best practices and measure campaign impact to recommend design changes that improve performance and reduce production effort",
                    "Brand Stewardship: Act as a guardian of the corporate style guide, ensuring all materials maintain a consistent, professional \"CST\" look and feel",
                    "Template Development: Build and maintain standardized Marcom templates to streamline design workflows while ensuring brand alignment",
                    "Identity Materials: Design core corporate identity assets, including stationery, business cards, logos, and global presentation templates",
                    "Packaging & Product Design (5%)",
                    "Packaging Solutions: Conceptualize and design physical product packaging, including containers, sleeves, labels, and mailing envelopes",
                    "Strategic Alignment: Partner with Product Management to ensure all packaging designs meet both brand strategy requirements and strict regulatory standards",
                    "Maintenance, Implementation & Support (10%)",
                    "Ongoing Support: Manage the maintenance and implementation of ongoing graphic projects, adapting materials for various formats, channels, and global regions as needed",
                    "Trend Innovation: Continuously research and implement new graphic design techniques, formats, and trends to keep visual content fresh and competitive"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "Indeed",
                "link": "https://www.indeed.com/viewjob?jk=a9b71d0d25e1de09&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Glassdoor",
                "link": "https://www.glassdoor.com/job-listing/graphic-designer-cell-signaling-technology-JV_IC1154555_KO0,16_KE17,42.htm?jl=1010076102515&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "LinkedIn",
                "link": "https://www.linkedin.com/jobs/view/graphic-designer-at-cell-signaling-technology-cst-4389773865?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/Cell-Signaling-Technology/Job/Graphic-Designer/-in-Danvers,MA?jid=e09bbc4f31d38e04&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "The Design Project",
                "link": "https://designproject.io/jobs/jobs/graphic-designer-at-cell-signaling-technology-im60tr?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Teal",
                "link": "https://www.tealhq.com/job/graphic-designer_7ea1ab5c72925f3ac66ac0cbef4de76a9e1ff?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Built In",
                "link": "https://builtin.com/job/graphic-designer/8854945?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "SimplyHired",
                "link": "https://www.simplyhired.com/job/yNtOww_Fl8OfurNDmU9E45ZpJazoVKzgSs4-Ra8DLXSYn1otnkHoWA?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJHcmFwaGljIERlc2lnbmVyIiwiY29tcGFueV9uYW1lIjoiQ2VsbCBTaWduYWxpbmcgVGVjaG5vbG9neSIsImFkZHJlc3NfY2l0eSI6IkRhbnZlcnMsIE1BIiwiaHRpZG9jaWQiOiJwaEpQbTZEczRGRS1zZ29GQUFBQUFBPT0iLCJ1dWxlIjoidytDQUlRSUNJaE1ESXhORFFzVFdGemMyRmphSFZ6WlhSMGN5eFZibWwwWldRZ1UzUmhkR1Z6IiwiZ2wiOiJ1cyIsImhsIjoiZW4ifQ=="
            },
            {
            "title": "Designer",
            "company_name": "CRATE & BARREL",
            "location": "Natick, MA",
            "via": "Jobs And Careers At CRATE & BARREL",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=kicsPssnbAPDw-c_AAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXMMQsCIRQA4P1-QgS9qSFKI2ipyeoIohqk_VB5qGU-8Tnc0I-PW77x637d4oIcfcYKG7iRBUZTXQDKcCXyCWfH0Frhg5TMSXhupkUnHH0lZbQ0yjdZnhg4mIolmYbDbr8dRcl-NT9r9ephCSeldX-HmOE5BZ81PNQfaHEah34AAAA&shmds=v1_ATWGeeMm9M8qTQpNg34Q1qL_jts7RuzuSJ99-83VXPd1PGIM7A&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=kicsPssnbAPDw-c_AAAAAA%3D%3D",
            "thumbnail": "https://serpapi.com/searches/69c6ca4931aafe3e972a6c09/images/J3jYS_JGEZWiKz8UnJy-lFhHT-IHwdLoiJfZu7ctm7M.jpeg",
            "extensions": [
                "Part-time",
                "No degree mentioned"
            ],
            "detected_extensions": {
                "schedule_type": "Part-time",
                "qualifications": "No degree mentioned"
            },
            "source_link": "https://jobs.crateandbarrel.com/job/natick/designer/351/90551819568",
            "description": "Crate and Barrel Designers are passionate about helping customers envision possibilities with the latest home design trends. They build meaningful, long-term relationships by using their knowledge to guide customers in furnishing anything from an entire home to a single accent piece. Skilled across a range of design styles—from classic to contemporary—Designers utilize digital tools and technology during in-store and in-home consultations to bring customer visions to life. In this role, you will drive sales and customer engagement by promoting programs, leveraging leads, and maintaining an active presence on the salesfloor. You will conduct customer outreach, develop design packages to brand standards, and ensure timely follow-up. Maintaining operational excellence through impeccable product presentation and careful use of tools and technology is essential, as is collaborating with store and design teams to support business goals. This role offers a creative, rewarding career path for those passionate about home interiors and thriving in a team-oriented, competitive environment.\n\nA day in the life as a Designer...\n• Drive sales and a differentiated experience by providing enriching customer interactions, and providing elevated design offerings in the store, in-home and virtually with customers\n• Create elevated designs for customers using the preferred design tools to create moodboards, 2D & 3D floor plans, product lists and customer presentations\n• Lead design consultations in person (in-store or in-home) or via email, phone and virtual\n• Deliver projects in a timely manner and within determined timelines\n• Possess a clear understanding of the brand aesthetics and merchandising strategy by channel; Store, E-Commerce, Catalog\n• Ensure full understanding and awareness of all product information, including characteristics, care information and staying informed with the competition and industry trends\n• Deliver individual sales, KPI and service goals, productivity standards, and engage customers on the sales floor by demonstrating our selling skills\n• Actively listen to the customer to identify which products will best meet their needs and communicate company loyalty services. (e.g. designer rewards, Design Trade Program, credit card etc)\n• Support and model excellent service by exhibiting a positive attitude and enthusiasm ensuring all customers are provided gracious, quick, and efficient service\n• Support store training and educating on design services, to drive a clear understanding of design services and offerings\n• Develop new and lasting relationships with customers through networking and clienteling\n• Understanding of basic design functions including spatial planning, fabric selection, lighting, interior design styles\n• Excellent, effective, and timely communication skills and the ability to translate the brand vision and the customers wants/needs\n• Strong affinity for technology (2D and 3D tools, Google suite, video conferencing, iPad) and proficient in floor planning\n• Ability to stay up to date on current design trends\n• Ability to be an agent of change and shift quickly as our business evolves\n\nWe'd love to hear from you if you have…\n• Understanding of basic design functions including spatial planning, fabric selection, lighting, interior design styles\n• Excellent, effective, and timely communication skills and the ability to translate the brand vision of CB2 and the customers wants/needs\n• Strong affinity for technology (2D and 3D tools, Google suite, video conferencing) and proficient in floor planning\n• Ability to stay up to date on current design trends\n• Proven track record of building long-lasting relationships with customers\n\nWe'd love to hear from you if you have…\n• 1+ years of relevant experience in Furniture Sales/ Home Decor Design or retail/ customer service experience\n• Experience working one on one with clients and recommending solutions\n• Proficient in Google platforms, virtual communication, design tool experience preferred",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "Excellent, effective, and timely communication skills and the ability to translate the brand vision and the customers wants/needs",
                    "Strong affinity for technology (2D and 3D tools, Google suite, video conferencing, iPad) and proficient in floor planning",
                    "Ability to stay up to date on current design trends",
                    "Ability to be an agent of change and shift quickly as our business evolves",
                    "Understanding of basic design functions including spatial planning, fabric selection, lighting, interior design styles",
                    "Excellent, effective, and timely communication skills and the ability to translate the brand vision of CB2 and the customers wants/needs",
                    "Strong affinity for technology (2D and 3D tools, Google suite, video conferencing) and proficient in floor planning",
                    "Ability to stay up to date on current design trends",
                    "Proven track record of building long-lasting relationships with customers",
                    "1+ years of relevant experience in Furniture Sales/ Home Decor Design or retail/ customer service experience",
                    "Experience working one on one with clients and recommending solutions"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "They build meaningful, long-term relationships by using their knowledge to guide customers in furnishing anything from an entire home to a single accent piece",
                    "Skilled across a range of design styles—from classic to contemporary—Designers utilize digital tools and technology during in-store and in-home consultations to bring customer visions to life",
                    "In this role, you will drive sales and customer engagement by promoting programs, leveraging leads, and maintaining an active presence on the salesfloor",
                    "You will conduct customer outreach, develop design packages to brand standards, and ensure timely follow-up",
                    "Maintaining operational excellence through impeccable product presentation and careful use of tools and technology is essential, as is collaborating with store and design teams to support business goals",
                    "Drive sales and a differentiated experience by providing enriching customer interactions, and providing elevated design offerings in the store, in-home and virtually with customers",
                    "Create elevated designs for customers using the preferred design tools to create moodboards, 2D & 3D floor plans, product lists and customer presentations",
                    "Lead design consultations in person (in-store or in-home) or via email, phone and virtual",
                    "Deliver projects in a timely manner and within determined timelines",
                    "Possess a clear understanding of the brand aesthetics and merchandising strategy by channel; Store, E-Commerce, Catalog",
                    "Ensure full understanding and awareness of all product information, including characteristics, care information and staying informed with the competition and industry trends",
                    "Deliver individual sales, KPI and service goals, productivity standards, and engage customers on the sales floor by demonstrating our selling skills",
                    "Actively listen to the customer to identify which products will best meet their needs and communicate company loyalty services",
                    "(e.g. designer rewards, Design Trade Program, credit card etc)",
                    "Support and model excellent service by exhibiting a positive attitude and enthusiasm ensuring all customers are provided gracious, quick, and efficient service",
                    "Support store training and educating on design services, to drive a clear understanding of design services and offerings",
                    "Develop new and lasting relationships with customers through networking and clienteling",
                    "Understanding of basic design functions including spatial planning, fabric selection, lighting, interior design styles"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "Jobs And Careers At CRATE & BARREL",
                "link": "https://jobs.crateandbarrel.com/job/natick/designer/351/90551819568?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/Crate-&-Barrel-Holdings/Job/Designer/-in-Natick,MA?jid=22904e6c0b4e6657&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Indeed",
                "link": "https://www.indeed.com/viewjob?jk=9f067ad88e9e7041&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Glassdoor",
                "link": "https://www.glassdoor.com/job-listing/designer-crate-and-barrel-JV_IC1154630_KO0,8_KE9,25.htm?jl=1009996427220&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Lensa",
                "link": "https://lensa.com/job-v1/crate-barrel-holdings/natick-ma/designer/7b312b191a51d6fc2c3a6fe1e537e1be?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "SimplyHired",
                "link": "https://www.simplyhired.com/job/7y7tFfrXxx0-41KAZNwJy2ITfSqqkmRFy0ke8snWkCJcrnSVaPkc7Q?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJEZXNpZ25lciIsImNvbXBhbnlfbmFtZSI6IkNSQVRFIFx1MDAyNiBCQVJSRUwiLCJhZGRyZXNzX2NpdHkiOiJOYXRpY2ssIE1BIiwiaHRpZG9jaWQiOiJraWNzUHNzbmJBUER3LWNfQUFBQUFBPT0iLCJ1dWxlIjoidytDQUlRSUNJaE1ESXhORFFzVFdGemMyRmphSFZ6WlhSMGN5eFZibWwwWldRZ1UzUmhkR1Z6IiwiZ2wiOiJ1cyIsImhsIjoiZW4ifQ=="
            },
            {
            "title": "Associate Graphic Designer",
            "company_name": "Rue Gilt Groupe",
            "location": "Boston, MA",
            "via": "Rue Gilt Groupe",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=we25j3lA-2CSh_fQAAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXNMQoCMRBAUWz3CIIwtWiigo1WK8KCYOMFliQMSSTOhMws7C28smvzy_-676o79iIcslOEobmacoA7So6EDfbwYA-CroUETDAwx4Lra1KtcrFWpJgo6jQHE_hjmdDzbN_s5Z9RkmtYy_IeT-fDbCrF7eY1LVIuunA8VYRMcGNRph08-x8OkiVvkgAAAA&shmds=v1_ATWGeeP1ZSpCIkMAxqH8f_d43QrS3tXfNgTti5B3vLYyxsG_JA&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=we25j3lA-2CSh_fQAAAAAA%3D%3D",
            "extensions": [
                "30 days ago",
                "Full-time",
                "Health insurance",
                "Dental insurance",
                "Paid time off"
            ],
            "detected_extensions": {
                "posted_at": "30 days ago",
                "schedule_type": "Full-time",
                "health_insurance": True,
                "dental_coverage": True,
                "paid_time_off": True
            },
            "source_link": "https://careers.ruegiltgroupe.com/jobs/7586238/associate-graphic-designer/",
            "description": "Title of role: Associate Graphic Designer\nLocation: Boston, MA; Hybrid (2 days in the office required)\nApproved Salary Range: $55,000-$57,000\n\nAbout the Role:\n\nThe Boutiques Associate Graphic Designer is responsible for designing and developing digital and print assets to support the Rue La La & Gilt teams. We’re looking for someone with the desire to be a part of something big, the training and foundation to create outstanding work daily, a sophisticated aesthetic sense and the interest to collaborate and succeed in a dynamic retail fashion environment. You’ll be joining a team that takes pride in the excellence of everything they do, all while respecting and protecting the integrity of the world-class brands featured on-site.\n\nKey Responsibilities:\n• Execute on-brand design demonstrating considered layout, image composition, typography, and a sophisticated use of color palette\n● Design a variety of assets for Boutiques, Marketing, and Acquisitions, including Boutique Main doors, advertising assets, and internal creative needs, from conceptualization through final approval\n● Work collaboratively and constructively on each project with other members on the team including Copywriters, Marketing Managers, Art Directors, Designers, and Brand Operations\n● Develop designs in a fast-paced environment without compromising quality, and be able to shift priorities based on changing calendars\n\nExperience and Background Needed:\n• * BA in Graphic Design\n● 0-2 years of relevant work experience as a junior designer or as a designer in an agency or in-house creative group\nTechnical skills\n● Skilled with imaging applications such as Adobe Photoshop, Adobe Illustrator and Adobe InDesign\n● Experience creating and optimizing graphics for the web\n● Great, positive attitude – we are a highly collaborative and collegial team\n● Desire to learn new things and keep abreast of the world of fashion, style, design, retailing and ecommerce\n● A strong portfolio showing training and potential\nBonus points for…\n● Skills and experience with video applications such as Adobe Premiere Pro and Adobe After Effects are a plus\n● Any photography Art Direction experience\n\nThe above statements are intended to describe the general nature and level of work being performed by employee(s) assigned to this job. They are not intended to be an exhaustive list of all responsibilities, duties and skills required of employee(s) assigned to this job. Rue Gilt Groupe reserves the right at any time, with or without notice, to alter or change job responsibilities, reassign or transfer job position or assign additional job responsibilities within your general skill set or capabilities. Rue Gilt Groupe is proud to be an Equal Opportunity workplace. All qualified applicants will receive consideration for employment without regard to race, color, religion, gender, gender identity or expression, sexual orientation, national origin, genetics, disability, age, or veteran status.\n\nWhat We Offer:\n\nRue Gilt Groupe is committed to providing Associates with equal pay for equal work and carefully considers a wide range of compensation factors, including but not limited to, prior experience, education, certification(s), license(s), skills and expertise, location, internal equity, and other factors that are job related and consistent with business need. Our goal is to support, reward and compensate the entire individual. Depending on role eligibility, your offer may also include bonus/commission, stock options, 401(k) participation, paid time off, medical, dental, vision and basic life insurance. Therefore, final offer amounts may vary from the amount stated.\n\nWe Encourage You to Apply:\n\nAt Rue Gilt Groupe, diversity enriches our passion, collaboration, kindness and innovation. We’re committed to fostering an inclusive environment where every Associate is empowered to learn, grow and bring their full self to work. Even if you don't check off every qualification in the job description, that's okay. We encourage you to apply to any role that excites you and sparks delight! We can't wait to learn more about you.\n\nWork Authorization\nRue Gilt Groupe requires all applicants to be currently authorized to work in the United States on a full-time basis. This position is not eligible for visa sponsorship now or in the future. Rue Gilt Groupe is an Equal Opportunity Employer and will consider all qualified applicants without regard to race, color, religion, sex, national origin, disability, or protected veteran status.\n\nABOUT US:\n\nReady for the most memorable – and stylish – experience of your professional career? Then join us at Rue Gilt Groupe. Combining three complementary brands, Rue La La, Gilt, and Shop Simon, we are the premier off-price e-commerce portfolio company.\n\nOur model defined the online treasure hunt through its daily sale events allowing our customers to discover over 5,000 premium and luxury brands at prices up to 70% off full-price retail. We believe in fashion for all, sparking delight through daily discovery and shopping as an occasion to celebrate! World-class merchandising, technology and marketing bring our shopping experience to life, and we hire world-class people to do it. Living our values and being empowered, tenacious, passionate, collaborative, innovative, and kind is something we strive for every single day. We meet over coffee and brainstorm new ways to spark delight for our members. Volunteer on- and off-hours together. Plan some serious surprises for our coworkers, because nothing ignites innovation like a breakfast cereal buffet or an afternoon slice of cake.\n\nAnd we don't hesitate to use our associate discount – after all, we're as enthusiastic about style as our customers. The way we work? It's so much more than what happens between the weekends. It empowers us to think, create, and innovate, so we can deliver the first-rate experience today's customer’s demand.\n\nRue Gilt Groupe GDPR/CCPA Pre-Collection Notice for Job Applications: We collect personal information (PI) from you in connection with your application for employment with Rue Gilt Groupe, including identifiers, contact information, employment and education history, and related information. We use this PI for purposes related to evaluating your application and potential employment. Depending on your location, you may have rights under GDPR or U.S. state privacy laws. For additional details or if you have questions, please see our GDPR Applicant Privacy Notice and CCPA Applicant Privacy Notice or contact us at recruitingcoordinator@ruegiltgroupe.com.",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "BA in Graphic Design",
                    "0-2 years of relevant work experience as a junior designer or as a designer in an agency or in-house creative group",
                    "Skilled with imaging applications such as Adobe Photoshop, Adobe Illustrator and Adobe InDesign",
                    "Experience creating and optimizing graphics for the web",
                    "Great, positive attitude – we are a highly collaborative and collegial team",
                    "Desire to learn new things and keep abreast of the world of fashion, style, design, retailing and ecommerce",
                    "A strong portfolio showing training and potential",
                    "Any photography Art Direction experience",
                    "Rue Gilt Groupe requires all applicants to be currently authorized to work in the United States on a full-time basis"
                ]
                },
                {
                "title": "Benefits",
                "items": [
                    "Approved Salary Range: $55,000-$57,000",
                    "Rue Gilt Groupe is committed to providing Associates with equal pay for equal work and carefully considers a wide range of compensation factors, including but not limited to, prior experience, education, certification(s), license(s), skills and expertise, location, internal equity, and other factors that are job related and consistent with business need",
                    "Our goal is to support, reward and compensate the entire individual",
                    "Depending on role eligibility, your offer may also include bonus/commission, stock options, 401(k) participation, paid time off, medical, dental, vision and basic life insurance",
                    "Therefore, final offer amounts may vary from the amount stated"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "Execute on-brand design demonstrating considered layout, image composition, typography, and a sophisticated use of color palette",
                    "Design a variety of assets for Boutiques, Marketing, and Acquisitions, including Boutique Main doors, advertising assets, and internal creative needs, from conceptualization through final approval",
                    "Work collaboratively and constructively on each project with other members on the team including Copywriters, Marketing Managers, Art Directors, Designers, and Brand Operations",
                    "Develop designs in a fast-paced environment without compromising quality, and be able to shift priorities based on changing calendars"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "Rue Gilt Groupe",
                "link": "https://careers.ruegiltgroupe.com/jobs/7586238/associate-graphic-designer/?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "VentureFizz",
                "link": "https://venturefizz.com/job/rue-gilt-groupe-associate-graphic-designer/?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Indeed",
                "link": "https://www.indeed.com/viewjob?jk=d1ba697a3d98185e&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/RUE-GILT-GROUPE/Job/Associate-Graphic-Designer/-in-Boston,MA?jid=5d01b21c08ffa471&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Glassdoor",
                "link": "https://www.glassdoor.com/job-listing/associate-graphic-designer-rue-gilt-groupe-JV_IC1154532_KO0,26_KE27,42.htm?jl=1010023013139&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Jobright",
                "link": "https://jobright.ai/jobs/info/6983b74d348f733a5c36f79a?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "SimplyHired",
                "link": "https://www.simplyhired.com/job/LvGN1aIe3T8NBsTeBGyyTDorIrkZ98AdLCAVPEAxwbihoriUL8T5Mg?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Lensa",
                "link": "https://lensa.com/job-v1/rue-gilt-groupe/boston-ma/associate-graphic-designer/0a207dccaffb9acf694b5008bf9586b9?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJBc3NvY2lhdGUgR3JhcGhpYyBEZXNpZ25lciIsImNvbXBhbnlfbmFtZSI6IlJ1ZSBHaWx0IEdyb3VwZSIsImFkZHJlc3NfY2l0eSI6IkJvc3RvbiwgTUEiLCJodGlkb2NpZCI6IndlMjVqM2xBLTJDU2hfZlFBQUFBQUE9PSIsInV1bGUiOiJ3K0NBSVFJQ0loTURJeE5EUXNUV0Z6YzJGamFIVnpaWFIwY3l4VmJtbDBaV1FnVTNSaGRHVnoiLCJnbCI6InVzIiwiaGwiOiJlbiJ9"
            },
            {
            "title": "Technical Designer II",
            "company_name": "New Balance",
            "location": "Boston, MA",
            "via": "ZipRecruiter",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=V0507fG1XZc3ufsrAAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXEsQrCMBAAUFz7BzrdLDURwUUniyAVdHIvl3AkKfEu5AL2C_xu8Q2v-666_kU-cvKY4UqaAlOFcYQd3MWBElYfQRhuIiHT5hxbK3qyVjWboA1b8sbL2wqTk8XO4vTfpBErlYyNpsNxv5jCYbt-0gcGzMieIDEMok24h8flB34gh9uJAAAA&shmds=v1_ATWGeeNCJ-GZR-WmD4b758GgTbOJBh0zwfl3_sfWRbHehPSALg&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=V0507fG1XZc3ufsrAAAAAA%3D%3D",
            "thumbnail": "https://serpapi.com/searches/69c6ca4931aafe3e972a6c09/images/WOqRTZM_XxryWfEsRRaRTCc5H7evKV6JGps6trSF3Lk.png",
            "extensions": [
                "70.6K–90.5K a year",
                "Full-time",
                "Dental insurance",
                "Health insurance"
            ],
            "detected_extensions": {
                "salary": "70.6K–90.5K a year",
                "schedule_type": "Full-time",
                "dental_coverage": True,
                "health_insurance": True
            },
            "source_link": "https://www.ziprecruiter.com/c/New-Balance/Job/Technical-Designer-II/-in-Boston,MA?jid=105da55d56f8fa35",
            "description": "Who We Are:\n\nSince 1906, New Balance has empowered people through sport and craftsmanship to create positive change in communities around the world. We innovate fearlessly, guided by our core values and driven by the belief that conventions were meant to be challenged. We foster a culture in which every associate feels welcomed and respected, where leaders and creatives are inspired to shape the world of tomorrow by taking bold action today.\n\nJOB MISSION:\n\nThis role brings Design intention from development through production. Provide transparency and issue escalation to maintain organizational alignment to ensure product drives fit and sizing consistency and garment construction excellence. Manage complex projects at various stages through design and development, fully coordinate tasks with cross functional team members.\n\nMAJOR ACCOUNTABILITIES:\n• Responsible for accurately interpreting design's intent from development through production.\n• Create and maintain medium complexity tech packs including garment construction, sketches, graded measurement charts, fit comments, and pattern corrections. Able to identify and correct fit issues.\n• Prepare for and lead fit sessions.\n• Communicate fit revisions to factories through pattern corrections and images.\n• Identify potential production, quality and costing issues and make appropriate recommendations while maintaining design and fit intent.\n• Track and manage workflow and ensure seasonal deadlines are met.\n• Strong understanding of industry competitors, trends, and new related technologies.\n\nREQUIREMENTS FOR SUCCESS:\n• Bachelor's degree in Fashion or related major is preferred\n• 5+ years of experience in Tech Design, patternmaking, fitting, and specs, and grading.\n• Experience and/or strong desire to learn Gerber Pattern Design and 3D Clo or related software.\n• Ability to interpret medium complexity technical sketch details in tech pack and identify construction on garment .\n• Understanding of development and manufacturing process.\n• Fluent with grade rule calculations.\n• Ability and willingness to travel globally.\n• System Knowledge of Microsoft Suite (Outlook, Teams, Excel, Powerpoint), Adobe Illustrator, PLM System.\n\nBoston, MA Headquarters - (NB) Only Pay Range: $70,600.00 - $90,500.00 - $110,400.00 Annual (actual base pay varying based upon, but not limited to, relevant experience, time in role, internal equity, geographic location, and more.)\n\nRegular Associate Benefits\n\nOur products are only as good as the people we hire, so we make sure to hire the best and treat them accordingly. New Balance offers a comprehensive traditional benefits package including three options for medical insurance as well as dental, vision, life insurance and 401K. We also proudly offer a slate of more nontraditional perks - opportunities like online learning and development courses, tuition reimbursement, $100 monthly student loan support and various mentorship programs - that encourage our associates to grow personally as they develop professionally. You'll also enjoy a yearly $1,000 lifestyle reimbursement, 4 weeks of vacations, 12 holidays and generous parental leave, because work-life balance is more than just a buzzword - it's part of our culture.\n\nTemporary associates are provided three options for medical insurance as well as dental and vision insurance and an associate discount.\n\nPart time associates are provided 401k, short term disability, a yearly $300 lifestyle reimbursement and an associate discount.\n\nFlexible Work Schedule\n\nFor decades we have fostered a unique culture founded on our values with a particular focus on in-person teamwork and collaboration. Our North American hybrid model encourages rich in-person experiences, showcasing our commitment to teamwork and connection, while maintaining flexibility for associates. New Balance Associates currently work in office three days per week (Tuesday, Wednesday, and Thursday). Our offices are fully open, and amenities are available across our North American office locations. To continue our focus on hybrid work we have introduced \"Work from Anywhere\" (WFA) for four weeks per calendar year. This model will help us enhance our culture while continuing to maintain elements of flexibility.\n\nEqual Opportunity Employer\n\nNew Balance provides equal opportunities for all current and prospective associates to ensure that employment, training, compensation, transfer, promotion and other terms, conditions and privileges of employment are provided without regard to race, color, religion, national origin, sex, sexual orientation, gender identity, age, handicap, genetic information and/or status as an Armed Forces service medal veteran, recently separated veteran, qualified disabled veteran or other protected veteran, or any other protected status.",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "5+ years of experience in Tech Design, patternmaking, fitting, and specs, and grading",
                    "Experience and/or strong desire to learn Gerber Pattern Design and 3D Clo or related software",
                    "Ability to interpret medium complexity technical sketch details in tech pack and identify construction on garment ",
                    "Understanding of development and manufacturing process",
                    "Fluent with grade rule calculations",
                    "Ability and willingness to travel globally",
                    "System Knowledge of Microsoft Suite (Outlook, Teams, Excel, Powerpoint), Adobe Illustrator, PLM System"
                ]
                },
                {
                "title": "Benefits",
                "items": [
                    "Boston, MA Headquarters - (NB) Only Pay Range: $70,600.00 - $90,500.00 - $110,400.00 Annual (actual base pay varying based upon, but not limited to, relevant experience, time in role, internal equity, geographic location, and more.)",
                    "Regular Associate Benefits",
                    "Our products are only as good as the people we hire, so we make sure to hire the best and treat them accordingly",
                    "New Balance offers a comprehensive traditional benefits package including three options for medical insurance as well as dental, vision, life insurance and 401K",
                    "We also proudly offer a slate of more nontraditional perks - opportunities like online learning and development courses, tuition reimbursement, $100 monthly student loan support and various mentorship programs - that encourage our associates to grow personally as they develop professionally",
                    "You'll also enjoy a yearly $1,000 lifestyle reimbursement, 4 weeks of vacations, 12 holidays and generous parental leave, because work-life balance is more than just a buzzword - it's part of our culture",
                    "Temporary associates are provided three options for medical insurance as well as dental and vision insurance and an associate discount",
                    "Part time associates are provided 401k, short term disability, a yearly $300 lifestyle reimbursement and an associate discount",
                    "Flexible Work Schedule",
                    "New Balance provides equal opportunities for all current and prospective associates to ensure that employment, training, compensation, transfer, promotion and other terms, conditions and privileges of employment are provided without regard to race, color, religion, national origin, sex, sexual orientation, gender identity, age, handicap, genetic information and/or status as an Armed Forces service medal veteran, recently separated veteran, qualified disabled veteran or other protected veteran, or any other protected status"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "This role brings Design intention from development through production",
                    "Provide transparency and issue escalation to maintain organizational alignment to ensure product drives fit and sizing consistency and garment construction excellence",
                    "Manage complex projects at various stages through design and development, fully coordinate tasks with cross functional team members",
                    "Responsible for accurately interpreting design's intent from development through production",
                    "Create and maintain medium complexity tech packs including garment construction, sketches, graded measurement charts, fit comments, and pattern corrections",
                    "Able to identify and correct fit issues",
                    "Prepare for and lead fit sessions",
                    "Communicate fit revisions to factories through pattern corrections and images",
                    "Identify potential production, quality and costing issues and make appropriate recommendations while maintaining design and fit intent",
                    "Track and manage workflow and ensure seasonal deadlines are met",
                    "Strong understanding of industry competitors, trends, and new related technologies"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/New-Balance/Job/Technical-Designer-II/-in-Boston,MA?jid=105da55d56f8fa35&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Ladders",
                "link": "https://www.theladders.com/job/technical-designer-ii-newbalance-boston-ma_84681337?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Fashion United",
                "link": "https://fashionunited.com/fashion-jobs/technical-designer-ii-boston-1862149?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Adzuna",
                "link": "https://www.adzuna.com/details/5530027621?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "LinkedIn",
                "link": "https://www.linkedin.com/jobs/view/technical-designer-ii-at-new-balance-4341257843?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "SonicJobs",
                "link": "https://www.sonicjobs.com/us/jobs/boston/full-time/technical-designer-ii-69b1f4bd290380db69997432?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Jobright",
                "link": "https://jobright.ai/jobs/info/692fa2424c474121999e13ef?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Hiring Cafe",
                "link": "https://hiring.cafe/viewjob/xez8pyy8gyuuwsgd?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJUZWNobmljYWwgRGVzaWduZXIgSUkiLCJjb21wYW55X25hbWUiOiJOZXcgQmFsYW5jZSIsImFkZHJlc3NfY2l0eSI6IkJvc3RvbiwgTUEiLCJodGlkb2NpZCI6IlYwNTA3ZkcxWFpjM3Vmc3JBQUFBQUE9PSIsInV1bGUiOiJ3K0NBSVFJQ0loTURJeE5EUXNUV0Z6YzJGamFIVnpaWFIwY3l4VmJtbDBaV1FnVTNSaGRHVnoiLCJnbCI6InVzIiwiaGwiOiJlbiJ9"
            },
            {
            "title": "Principal UI/UX Designer; Onsite, Boston MA",
            "company_name": "Cadence Design Systems",
            "location": "Boston, MA",
            "via": "Built In Boston",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=E0EeYhPe9xh3o6raAAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_y3NsQrCMBCAYVz7CE43OEltRHCxk1UQBVGQgltJ45FG0ruQy1CfyNe0Qpd_-Jcv-86y6h4dGRe0h_qs6iccUZwljCXcSFzCHCqWxATXPazgwi0I6mg6GNeJ2Xqcl11KQXZKifjCStLJmcJwr5iw5UG9uZV_Gul0xOB1wmazXQ9FILtcHPQLyeAEw-MjCXsBRxOcj_IPL_XZaaoAAAA&shmds=v1_ATWGeeO3JXvHHZCTXw6dP9bCnXMpW-aqXZ58iVjwV7i8ujWD4g&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=E0EeYhPe9xh3o6raAAAAAA%3D%3D",
            "thumbnail": "https://serpapi.com/searches/69c6ca4931aafe3e972a6c09/images/7uAtWEsE5dGTiyHG7oEQDhqpN1GltqQtR7g276EcAF8.jpeg",
            "extensions": [
                "9 days ago",
                "118K–218K a year",
                "Full-time",
                "Paid time off",
                "Health insurance",
                "Dental insurance"
            ],
            "detected_extensions": {
                "posted_at": "9 days ago",
                "salary": "118K–218K a year",
                "schedule_type": "Full-time",
                "paid_time_off": True,
                "health_insurance": True,
                "dental_coverage": True
            },
            "source_link": "https://www.builtinboston.com/job/principal-ui-ux-designer-onsite-boston-ma/8815337",
            "description": "At Cadence, we hire and develop leaders and innovators who want to make an impact on the world of technology.\n\nCadence Molecular Sciences has developed a cutting-edge, first-in-class cloud-native platform for molecular design, cheminformatics and data management (“Orion”). Everyone, from top twenty pharmaceutical companies to emerging biotechnology startups use Orion to accelerate the pace of discovery in the areas of new therapeutics and molecular materials.\n\nRequirements:\n\nWe are looking for an outstanding UX/UI designer to lead the design of the Orion platform. You will apply user-experience research and design methodologies to catalyze the development of the platform for molecular design. You will partner with product, UI engineering, drug-discovery science, marketing and senior leadership to oversee the user experience of therapeutic design.\n\nIn your role, you will work with Ph.D. drug-discovery scientists and commercial teams, as well as conduct user research and synthesize the many voices into a unified and strategic roadmap to guide our design. You will develop sketches, wireframes, high-fidelity mockups, and working prototypes and iteratively refine solutions as designs are implemented to deliver creative, consistent and practical solutions. You will provide advocacy for human-centered design.\n\nPrincipal Responsibilities:\n• Conduct high-quality user research to develop user personas and design strategy that can be articulated in a complete user experience\n• Create and iteratively refine design solutions through mocks, wireframes and high-fidelity prototypes\n• Measure product success and value delivery through analytics\n• Participate in formulating strategic product vision as it relates to user experience design\n• Coach stakeholders in key aspects of design\n• Contribute to building design resources with developers (e.g., UI component libraries)\n\nRequirements:\n• BS with a minimum of 7 years of experience OR MS with a minimum of 5 years of experience OR PhD with a minimum of 1 year of experience\n• 3+ years’ experience in UX/UI design at an agile, SaaS or similar organization\n• Excellent user research skills and an ability to synthesize and translate technical user research and experience into elegant visual design.\n• Well-acquainted with design tools such as Balsamiq, Sketch, Figma, InVision, etc.\n• A history of working with diverse stakeholders including front-end engineers, customers and product representatives.\n\nPreferences:\n• Extensive experience working closely with an engineering team.\n• Ability to work with PhD scientists and users.\n• Understanding of molecules, chemistry, pharmaceuticals or a related field.\n• A background or experience in software engineering for a STEM discipline.\n• Experience working on cloud-based SAAS services\n\nYou want:\n\nAn opportunity to be a UX/UI designer in a fast-paced business focused on cutting-edge products directly impacting the discovery of new therapeutics\n\nAn exciting environment that will push and support your desire to grow and improve professionally\n\nA diverse professional environment made up of scientists, engineers, commercial and thought leaders in molecular design, computational chemistry and drug discovery\n\nA Silicon-Valley based company with a long history of technology-first management and rapid adoption of best practices in science and engineering\n\nThe annual salary range for Massachusetts is $117,600 to $218,400. You may also be eligible to receive incentive compensation: bonus, equity, and benefits. Sales positions generally offer a competitive On Target Earnings (OTE) incentive compensation structure. Please note that the salary range is a guideline and compensation may vary based on factors such as qualifications, skill level, competencies and work location. Our benefits programs include: paid vacation and paid holidays, 401(k) plan with employer match, employee stock purchase plan, a variety of medical, dental and vision plan options, and more.\nWe’re doing work that matters. Help us solve what others can’t.",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "BS with a minimum of 7 years of experience OR MS with a minimum of 5 years of experience OR PhD with a minimum of 1 year of experience",
                    "3+ years’ experience in UX/UI design at an agile, SaaS or similar organization",
                    "Excellent user research skills and an ability to synthesize and translate technical user research and experience into elegant visual design",
                    "Well-acquainted with design tools such as Balsamiq, Sketch, Figma, InVision, etc",
                    "A history of working with diverse stakeholders including front-end engineers, customers and product representatives",
                    "Extensive experience working closely with an engineering team",
                    "Ability to work with PhD scientists and users",
                    "Understanding of molecules, chemistry, pharmaceuticals or a related field",
                    "A background or experience in software engineering for a STEM discipline",
                    "Experience working on cloud-based SAAS services",
                    "An opportunity to be a UX/UI designer in a fast-paced business focused on cutting-edge products directly impacting the discovery of new therapeutics"
                ]
                },
                {
                "title": "Benefits",
                "items": [
                    "The annual salary range for Massachusetts is $117,600 to $218,400",
                    "You may also be eligible to receive incentive compensation: bonus, equity, and benefits",
                    "Sales positions generally offer a competitive On Target Earnings (OTE) incentive compensation structure",
                    "Please note that the salary range is a guideline and compensation may vary based on factors such as qualifications, skill level, competencies and work location",
                    "Our benefits programs include: paid vacation and paid holidays, 401(k) plan with employer match, employee stock purchase plan, a variety of medical, dental and vision plan options, and more"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "We are looking for an outstanding UX/UI designer to lead the design of the Orion platform",
                    "You will apply user-experience research and design methodologies to catalyze the development of the platform for molecular design",
                    "You will partner with product, UI engineering, drug-discovery science, marketing and senior leadership to oversee the user experience of therapeutic design",
                    "In your role, you will work with Ph.D. drug-discovery scientists and commercial teams, as well as conduct user research and synthesize the many voices into a unified and strategic roadmap to guide our design",
                    "You will develop sketches, wireframes, high-fidelity mockups, and working prototypes and iteratively refine solutions as designs are implemented to deliver creative, consistent and practical solutions",
                    "You will provide advocacy for human-centered design",
                    "Conduct high-quality user research to develop user personas and design strategy that can be articulated in a complete user experience",
                    "Create and iteratively refine design solutions through mocks, wireframes and high-fidelity prototypes",
                    "Measure product success and value delivery through analytics",
                    "Participate in formulating strategic product vision as it relates to user experience design",
                    "Coach stakeholders in key aspects of design",
                    "Contribute to building design resources with developers (e.g., UI component libraries)"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "Built In Boston",
                "link": "https://www.builtinboston.com/job/principal-ui-ux-designer-onsite-boston-ma/8815337?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/OpenEye-Scientific/Job/Principal-UI-UX-Designer/-in-Boston,MA?jid=9119a29e9d3b2420&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Built In",
                "link": "https://builtin.com/job/principal-ui-ux-designer-onsite-boston-ma/8815337?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Teal",
                "link": "https://www.tealhq.com/job/principal-ui-ux-designer_7ea1a437fbe0e43437edd22bf48259b65d924?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "SimplyHired",
                "link": "https://www.simplyhired.com/job/m1DynmCOTYuW01fTZAq8V-7PTZLm93eamhSPTaFhd0HP7BNd6E6RRw?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "IHireTechnology",
                "link": "https://www.ihiretechnology.com/jobs/view/514266046?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Bandana.com",
                "link": "https://bandana.com/jobs/d2ca537e-cf9f-4bd9-8dc7-6e1bccb7737b?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Ladders",
                "link": "https://www.theladders.com/job/principal-ui-ux-designer-onsite-boston-ma-cadencedesignsystems-boston-ma_86187976?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJQcmluY2lwYWwgVUkvVVggRGVzaWduZXI7IE9uc2l0ZSwgQm9zdG9uIE1BIiwiY29tcGFueV9uYW1lIjoiQ2FkZW5jZSBEZXNpZ24gU3lzdGVtcyIsImFkZHJlc3NfY2l0eSI6IkJvc3RvbiwgTUEiLCJodGlkb2NpZCI6IkUwRWVZaFBlOXhoM282cmFBQUFBQUE9PSIsInV1bGUiOiJ3K0NBSVFJQ0loTURJeE5EUXNUV0Z6YzJGamFIVnpaWFIwY3l4VmJtbDBaV1FnVTNSaGRHVnoiLCJnbCI6InVzIiwiaGwiOiJlbiJ9"
            },
            {
            "title": "Senior Product Designer",
            "company_name": "iRobot",
            "location": "Bedford, MA",
            "via": "IRobot Careers",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=oEdoyu-ecVydhpzHAAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXEsQrCMBAGYFy7uzjdLJqI4KJTRRAEQfQBSpKeSaTmL7kT-gA-uPgNX_OdNebBJaPSraL_BKUTS46FK63pAk_CroZEKHQG4sCLQ1IdZW-tyGCiqNMcTMDborDHZF_w8q-T5CqPg1PutrvNZMYSl_N8h4dSLnTk_onar-ja_gC9M5Z1hwAAAA&shmds=v1_ATWGeeOOS9yQ0I4_tvAwCSAP4rOdalTyNDZAyUMF9t9SYVbSng&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=oEdoyu-ecVydhpzHAAAAAA%3D%3D",
            "extensions": [
                "8 days ago",
                "Full-time"
            ],
            "detected_extensions": {
                "posted_at": "8 days ago",
                "schedule_type": "Full-time"
            },
            "source_link": "https://careers.irobot.com/job/bedford/senior-product-designer/42682/92994471792",
            "description": "Introduction\n\nYou’re a product designer who thinks in systems, not just screens. You bring a high level of craft to mobile experiences, creating interfaces that are clear, cohesive, and on brand. You build scalable, reusable foundations that support consistent delivery, and work closely with engineering to ensure designs are implementable and efficient. You stay connected to the work after launch, using research and data to improve real user outcomes, and you’re comfortable navigating ambiguity and making thoughtful tradeoffs between long-term system quality and immediate product needs.\n\nWhat you’ll do:\n\nDesign Systems\n• Own and evolve the design system (components, patterns, tokens) for the Roomba Home App, partnering with engineering to ensure it is implementable, performant, and scales across teams and features\n• Build and extend system-driven UI across core flows and new features\n• Ensure accessibility, consistency, and reuse across the product\n\nVisual Standards\n• Define and maintain visual standards across UI, illustration, and motion, ensuring consistency and quality at scale\n• Execute and maintain a scalable visual asset library (icons, illustrations, motion), using tools including AI where appropriate, to enable fast, consistent output\n• Partner with marketing to ensure alignment with brand expression across product launches and new app experiences\n\nFeature Delivery\n• Design end-to-end experiences for new robot capabilities and intelligent features\n• Plan and run usability testing to validate designs and drive iteration\n• Partner with engineering early to align on implementation, constraints, and efficiency\n• Own work from concept through production\n• Monitor performance post-launch and iterate to improve outcomes\n\nTo Be Successful You will have:\n• 4–7 years of experience designing mobile apps for consumer-focused products or agencies\n• Strong experience contributing to or owning a design system, including component libraries and scalable patterns\n• High craft bar in visual design, interaction design, and motion\n• Experience with digital and 3d illustration or custom visual asset creation\n• Ability to operate independently and bring clarity to ambiguous problem spaces\n• Strong understanding of user-centered design principles and designing for global audiences\n• Proven track record of shipping high-quality, customer-centric products\n• Proficiency with Figma\n\nNice to have:\n• Bilingual in English and Mandarin\n• Experience creating production quality animations\n• Experience working with or contributing to AI-assisted design workflows (e.g., Figma Make or similar)\n• Bachelor’s degree in Design, UX, HCI, or a related field (or equivalent experience)\n• LI-Hybrid\n\nApplicants must be authorized to work for any employer in the U.S. We are unable to sponsor or assume sponsorship of any additional employment visas at this time.",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "You’re a product designer who thinks in systems, not just screens",
                    "Design end-to-end experiences for new robot capabilities and intelligent features",
                    "4–7 years of experience designing mobile apps for consumer-focused products or agencies",
                    "Strong experience contributing to or owning a design system, including component libraries and scalable patterns",
                    "High craft bar in visual design, interaction design, and motion",
                    "Experience with digital and 3d illustration or custom visual asset creation",
                    "Ability to operate independently and bring clarity to ambiguous problem spaces",
                    "Strong understanding of user-centered design principles and designing for global audiences",
                    "Proven track record of shipping high-quality, customer-centric products",
                    "Proficiency with Figma",
                    "Bilingual in English and Mandarin",
                    "Experience creating production quality animations",
                    "Experience working with or contributing to AI-assisted design workflows (e.g., Figma Make or similar)",
                    "Bachelor’s degree in Design, UX, HCI, or a related field (or equivalent experience)",
                    "LI-Hybrid",
                    "Applicants must be authorized to work for any employer in the U.S. We are unable to sponsor or assume sponsorship of any additional employment visas at this time"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "You bring a high level of craft to mobile experiences, creating interfaces that are clear, cohesive, and on brand",
                    "You build scalable, reusable foundations that support consistent delivery, and work closely with engineering to ensure designs are implementable and efficient",
                    "You stay connected to the work after launch, using research and data to improve real user outcomes, and you’re comfortable navigating ambiguity and making thoughtful tradeoffs between long-term system quality and immediate product needs",
                    "Design Systems",
                    "Own and evolve the design system (components, patterns, tokens) for the Roomba Home App, partnering with engineering to ensure it is implementable, performant, and scales across teams and features",
                    "Build and extend system-driven UI across core flows and new features",
                    "Ensure accessibility, consistency, and reuse across the product",
                    "Visual Standards",
                    "Define and maintain visual standards across UI, illustration, and motion, ensuring consistency and quality at scale",
                    "Execute and maintain a scalable visual asset library (icons, illustrations, motion), using tools including AI where appropriate, to enable fast, consistent output",
                    "Partner with marketing to ensure alignment with brand expression across product launches and new app experiences",
                    "Plan and run usability testing to validate designs and drive iteration",
                    "Partner with engineering early to align on implementation, constraints, and efficiency",
                    "Own work from concept through production",
                    "Monitor performance post-launch and iterate to improve outcomes"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "IRobot Careers",
                "link": "https://careers.irobot.com/job/bedford/senior-product-designer/42682/92994471792?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Built In Boston",
                "link": "https://www.builtinboston.com/job/senior-product-designer/8821509?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Talents By Vaia",
                "link": "https://talents.vaia.com/companies/davita-inc/product-designer-29736246/?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "LinkedIn",
                "link": "https://www.linkedin.com/jobs/view/senior-product-designer-at-irobot-4388731447?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Experteer",
                "link": "https://us.experteer.com/career/view-jobs/senior-product-designer-bedford-ma-usa-56706914?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Ladders",
                "link": "https://www.theladders.com/job/senior-product-designer-irobotcorporation-bedford-ma_86201353?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Built In",
                "link": "https://builtin.com/job/senior-product-designer/8821509?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "IHireAdvertising",
                "link": "https://www.ihireadvertising.com/jobs/view/514531367?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJTZW5pb3IgUHJvZHVjdCBEZXNpZ25lciIsImNvbXBhbnlfbmFtZSI6ImlSb2JvdCIsImFkZHJlc3NfY2l0eSI6IkJlZGZvcmQsIE1BIiwiaHRpZG9jaWQiOiJvRWRveXUtZWNWeWRocHpIQUFBQUFBPT0iLCJ1dWxlIjoidytDQUlRSUNJaE1ESXhORFFzVFdGemMyRmphSFZ6WlhSMGN5eFZibWwwWldRZ1UzUmhkR1Z6IiwiZ2wiOiJ1cyIsImhsIjoiZW4ifQ=="
            },
            {
            "title": "Junior Graphic Designer",
            "company_name": "Lupoli Companies",
            "location": "Lawrence, MA",
            "via": "Paylocity",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=U3UrmDio2yZDCaa3AAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXEwQrCMAwAULzuEzzlLNqK4EVPojAY8xskK6GNdElpOtxf-MviO7zuu-ncsAhrhb5iSRzgQcZRqMIBBp3ACGtIoAK9asy0vabWil28N8suWsPGwQWdvQpNuvq3TvbvZQkrlYyNXqfzcXVF4g7GpWhmuOtcUJgMWGDETyUJtIfn7QfNPT3rkgAAAA&shmds=v1_ATWGeeMbv-o_Tq9PYwlC9bXjmLi4cJD4XmT31ZFU46Hoer1J4Q&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=U3UrmDio2yZDCaa3AAAAAA%3D%3D",
            "thumbnail": "https://serpapi.com/searches/69c6ca4931aafe3e972a6c09/images/lOkVa0f0zjGnbZabJA2My0FGvYZbc593ZykrEBHT2zw.png",
            "extensions": [
                "3 days ago",
                "45K–55K a year",
                "Full-time"
            ],
            "detected_extensions": {
                "posted_at": "3 days ago",
                "salary": "45K–55K a year",
                "schedule_type": "Full-time"
            },
            "source_link": "https://recruiting.paylocity.com/Recruiting/Jobs/Details/4027780",
            "description": "Description\n\nThe Junior Graphic Designer supports the marketing team in creating and executing visual content across multiple brands within the Lupoli Companies portfolio. This role focuses on producing day-to-day marketing materials, assisting with design projects, and ensuring brand consistency across digital and print platforms.\n\nThis is an entry-level position ideal for someone looking to grow their design skills in a fast-paced, multi-brand environment.\n\nResponsibilities\nDesign & Creative Support\n• Create marketing materials including social media graphics, flyers, signage, presentations, and basic print collateral\n• Assist in designing and updating PowerPoint presentations for internal and external use\n• Adapt existing designs to different formats and platforms while maintaining brand consistency\n• Support packaging, promotional, and in-store design needs as directed\nDigital & Content Execution\n• Design graphics for social media using Canva and Adobe Photoshop\n• Resize and format creative assets for web, email, and digital platforms\n• Assist with updates to website visuals and promotional graphics\n• Prepare images and basic edits for marketing campaigns\nProduction & Coordination\n• Prepare files for print and digital use, ensuring correct sizing and formatting\n• Coordinate with vendors or printers as needed for basic production tasks\n• Assist in organizing and maintaining design files and assets\nTeam Collaboration\n• Work closely with the marketing team to execute creative requests\n• Take direction from senior team members and implement feedback\n• Support multiple projects at once while meeting deadlines\n\nRequirements\n\nRequirements\n• Bachelor’s degree (or pursuing) in Graphic Design or related field\n• 0–2 years of experience (internships or freelance work acceptable)\n• Proficiency in:\n• Adobe Photoshop\n• Canva\n• Microsoft PowerPoint\n• Basic understanding of layout, typography, and color\n• Strong attention to detail and willingness to learn\n• Ability to manage time and handle multiple tasks\n• Positive attitude and team-oriented mindset\nNice to Have (Not Required)\n• Experience with Adobe Illustrator or InDesign\n• Basic knowledge of social media platforms and trends\n• Familiarity with website platforms (Wix or Squarespace)",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "This is an entry-level position ideal for someone looking to grow their design skills in a fast-paced, multi-brand environment",
                    "Bachelor’s degree (or pursuing) in Graphic Design or related field",
                    "0–2 years of experience (internships or freelance work acceptable)",
                    "Adobe Photoshop",
                    "Canva",
                    "Microsoft PowerPoint",
                    "Basic understanding of layout, typography, and color",
                    "Strong attention to detail and willingness to learn",
                    "Ability to manage time and handle multiple tasks",
                    "Positive attitude and team-oriented mindset",
                    "Nice to Have (Not Required)",
                    "Experience with Adobe Illustrator or InDesign",
                    "Basic knowledge of social media platforms and trends",
                    "Familiarity with website platforms (Wix or Squarespace)"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "The Junior Graphic Designer supports the marketing team in creating and executing visual content across multiple brands within the Lupoli Companies portfolio",
                    "This role focuses on producing day-to-day marketing materials, assisting with design projects, and ensuring brand consistency across digital and print platforms",
                    "Design & Creative Support",
                    "Create marketing materials including social media graphics, flyers, signage, presentations, and basic print collateral",
                    "Assist in designing and updating PowerPoint presentations for internal and external use",
                    "Adapt existing designs to different formats and platforms while maintaining brand consistency",
                    "Support packaging, promotional, and in-store design needs as directed",
                    "Design graphics for social media using Canva and Adobe Photoshop",
                    "Resize and format creative assets for web, email, and digital platforms",
                    "Assist with updates to website visuals and promotional graphics",
                    "Prepare images and basic edits for marketing campaigns",
                    "Production & Coordination",
                    "Prepare files for print and digital use, ensuring correct sizing and formatting",
                    "Coordinate with vendors or printers as needed for basic production tasks",
                    "Assist in organizing and maintaining design files and assets",
                    "Team Collaboration",
                    "Work closely with the marketing team to execute creative requests",
                    "Take direction from senior team members and implement feedback",
                    "Support multiple projects at once while meeting deadlines"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "Paylocity",
                "link": "https://recruiting.paylocity.com/Recruiting/Jobs/Details/4027780?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Indeed",
                "link": "https://www.indeed.com/viewjob?jk=f125e4f946c06722&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/Lupoli-Companies/Job/Junior-Graphic-Designer/-in-Lawrence,MA?jid=4222540e4346e225&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Glassdoor",
                "link": "https://www.glassdoor.com/job-listing/junior-graphic-designer-jenet-management-llc-JV_IC1154598_KO0,23_KE24,44.htm?jl=1010076472585&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "The Design Project",
                "link": "https://designproject.io/jobs/jobs/junior-graphic-designer-at-lupoli-companies-j3x34e?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Harlow Freelance Job Board",
                "link": "https://freelance-jobs.meetharlow.com/jobs/398455480-junior-graphic-designer?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Design Jobs Careers",
                "link": "https://designjobs.careers/job/203795?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Jobilize",
                "link": "https://www.jobilize.com/amp/job/us-ma-lawrence-junior-graphic-designer-lupoli-companies-hiring-now?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJKdW5pb3IgR3JhcGhpYyBEZXNpZ25lciIsImNvbXBhbnlfbmFtZSI6Ikx1cG9saSBDb21wYW5pZXMiLCJhZGRyZXNzX2NpdHkiOiJMYXdyZW5jZSwgTUEiLCJodGlkb2NpZCI6IlUzVXJtRGlvMnlaRENhYTNBQUFBQUE9PSIsInV1bGUiOiJ3K0NBSVFJQ0loTURJeE5EUXNUV0Z6YzJGamFIVnpaWFIwY3l4VmJtbDBaV1FnVTNSaGRHVnoiLCJnbCI6InVzIiwiaGwiOiJlbiJ9"
            },
            {
            "title": "Designer I",
            "company_name": "NELCO Worldwide",
            "location": "Burlington, MA",
            "via": "Glassdoor",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=qNCK4jZKczFCKMKbAAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXEOwoCMRAAUGz3CFazrWgigo1W_hDFT2m5JNkhicSZkIm4vRcXX_Ga76hp9yjRExY4wQzObEHQFBeACY7MPuF4HWrNstJaJCkv1dTolOOXZkLLg36ylX-dBFMwJ1OxWyzng8rkJ-3tcNnd4cEl9Z_YI0SC7bukSL4yTeG6-QGFsfSUhgAAAA&shmds=v1_ATWGeeMpeIGYFmY58nwvgAFUw1Kq6TzP_msbrpVP6cEOf_V8FQ&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=qNCK4jZKczFCKMKbAAAAAA%3D%3D",
            "extensions": [
                "23 days ago",
                "70K a year",
                "Full-time",
                "Paid time off",
                "Dental insurance",
                "Health insurance"
            ],
            "detected_extensions": {
                "posted_at": "23 days ago",
                "salary": "70K a year",
                "schedule_type": "Full-time",
                "paid_time_off": True,
                "dental_coverage": True,
                "health_insurance": True
            },
            "source_link": "https://www.glassdoor.com/job-listing/designer-i-nelco-worldwide-JV_IC1154543_KO0,10_KE11,26.htm?jl=1009930075944",
            "description": "Note: Trapani + Associates is a division of NELCO Worldwide.\n\nJob Summary\n\nTrapani + Associates’ Radiation Shielding Engineering Designer I will primarily be responsible for the drafting of shielding projects for healthcare, research, and industrial applications under the supervision of senior staff members.\n\nThis entry-level position offers comprehensive training in radiation shielding design from one of the world’s leading design groups. While no prior radiation shielding experience is necessary, candidates must exhibit a strong desire to learn, acute attention to detail, and solid critical thinking skills.\n\nThe standard training period is 1 to 2 years, during which candidates will be introduced to shielding design concepts, implementing their training, and progress to managing more challenging project types. Prior experience with building construction is required.\n\nEssential Functions & Key Responsibilities\n• Collaborate with senior team members to produce construction documents for a variety of shielding projects.\n• Develop and implement design and construction packages, sketches, and fabrication drawings using standard shielding design procedures, methods, and redlines, based on sketches or concepts provided by others.\n• Demonstrate the ability to resolve design challenges and display a high degree of drafting proficiency with strong project organization skills.\n• Frequently coordinate, communicate, and problem-solve within the project team to ensure successful project outcomes.\n• Manage up to five projects at a time, either working independently or in collaboration with senior team members.\n• Proactively anticipate construction challenges and promptly alert senior staff to any issues.\n\nQualifications, Skills & Abilities\n• Associate’s degree with coursework in drafting/design is a plus.\n• 1 to 3 years of experience in Architecture, Structural or Mechanical Engineering, or a related field preferred.\n• Strong understanding of building construction techniques and materials, as well as design principles.\n• Skilled knowledge of Autodesk REVIT and 2D AutoCAD software for architectural or structural design, rendering, and detailing, emphasizing steel and concrete construction.\n• Knowledge of 2D AutoCAD is also required.\n• Strong ability to design within projected schedule timelines.\n• Proven ability to visualize things three-dimensionally from 2D documents.\n• Keen eye for detail in graphics, such as line weights, detail layouts, and grammar.\n• Ability to identify and make suggestions for design improvements.\n• Working knowledge of commonly used concepts, practices, and procedures in construction.\n• Excellent oral and written communication skills to clearly convey design intent graphically and verbally.\n• Strong team player with effective interpersonal skills.\n\nPhysical Demands/Work Environment\n\nWhile performing the duties of this job, the individual is frequently required to move about inside the office to access filing cabinets, office machinery, etc. Constantly operates a computer and other standard office equipment such as copy machines, computer printers and plotters. The staff member in this position frequently communicates internally and externally; must be able to exchange accurate information via phone, email, and/or in person. Specific vision abilities apply including close vision, distance vision, and ability to adjust focus.\n\nThis position operates in a clerical office setting. The noise level in the work environment is usually moderate.\n\nThe above statements are intended to describe the general nature and level of work being performed by people assigned to do this job. The above is not intended to be an exhaustive list of all responsibilities and duties required.\n\nExternal and internal applicants, as well as position incumbents who become disabled as defined under the Americans with Disabilities Act, must be able to perform the essential job functions (as listed) either unaided or with the assistance of a reasonable accommodation. Reasonable accommodations will be made to enable individuals with disabilities to perform the essential functions of this job.\n\nJob Type: Full-time\n\nPay: Up to $70,000.00 per year\n\nBenefits:\n• 401(k)\n• 401(k) matching\n• Dental insurance\n• Flexible spending account\n• Health insurance\n• Health savings account\n• Paid time off\n• Tuition reimbursement\n• Vision insurance\n\nApplication Question(s):\n• Are you proficient in AutoCAD and Revit?\n• Do you have experience with building construction techniques and materials, as well as design principles?\n• Do you have a Bachelor of Science degree in Structural or Civil engineering?\n\nAbility to Commute:\n• Burlington, MA 01803 (Required)\n\nWork Location: In person",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "While no prior radiation shielding experience is necessary, candidates must exhibit a strong desire to learn, acute attention to detail, and solid critical thinking skills",
                    "The standard training period is 1 to 2 years, during which candidates will be introduced to shielding design concepts, implementing their training, and progress to managing more challenging project types",
                    "Prior experience with building construction is required",
                    "Strong understanding of building construction techniques and materials, as well as design principles",
                    "Skilled knowledge of Autodesk REVIT and 2D AutoCAD software for architectural or structural design, rendering, and detailing, emphasizing steel and concrete construction",
                    "Knowledge of 2D AutoCAD is also required",
                    "Strong ability to design within projected schedule timelines",
                    "Proven ability to visualize things three-dimensionally from 2D documents",
                    "Keen eye for detail in graphics, such as line weights, detail layouts, and grammar",
                    "Ability to identify and make suggestions for design improvements",
                    "Working knowledge of commonly used concepts, practices, and procedures in construction",
                    "Excellent oral and written communication skills to clearly convey design intent graphically and verbally",
                    "Strong team player with effective interpersonal skills",
                    "Physical Demands/Work Environment",
                    "External and internal applicants, as well as position incumbents who become disabled as defined under the Americans with Disabilities Act, must be able to perform the essential job functions (as listed) either unaided or with the assistance of a reasonable accommodation",
                    "Are you proficient in AutoCAD and Revit?",
                    "Do you have experience with building construction techniques and materials, as well as design principles?",
                    "Do you have a Bachelor of Science degree in Structural or Civil engineering?",
                    "Burlington, MA 01803 (Required)"
                ]
                },
                {
                "title": "Benefits",
                "items": [
                    "Pay: Up to $70,000.00 per year",
                    "401(k)",
                    "401(k) matching",
                    "Dental insurance",
                    "Flexible spending account",
                    "Health insurance",
                    "Health savings account",
                    "Paid time off",
                    "Tuition reimbursement",
                    "Vision insurance"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "Trapani + Associates’ Radiation Shielding Engineering Designer I will primarily be responsible for the drafting of shielding projects for healthcare, research, and industrial applications under the supervision of senior staff members",
                    "This entry-level position offers comprehensive training in radiation shielding design from one of the world’s leading design groups",
                    "Collaborate with senior team members to produce construction documents for a variety of shielding projects",
                    "Develop and implement design and construction packages, sketches, and fabrication drawings using standard shielding design procedures, methods, and redlines, based on sketches or concepts provided by others",
                    "Demonstrate the ability to resolve design challenges and display a high degree of drafting proficiency with strong project organization skills",
                    "Frequently coordinate, communicate, and problem-solve within the project team to ensure successful project outcomes",
                    "Manage up to five projects at a time, either working independently or in collaboration with senior team members",
                    "Proactively anticipate construction challenges and promptly alert senior staff to any issues",
                    "While performing the duties of this job, the individual is frequently required to move about inside the office to access filing cabinets, office machinery, etc",
                    "Constantly operates a computer and other standard office equipment such as copy machines, computer printers and plotters",
                    "The staff member in this position frequently communicates internally and externally; must be able to exchange accurate information via phone, email, and/or in person",
                    "Specific vision abilities apply including close vision, distance vision, and ability to adjust focus"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "Glassdoor",
                "link": "https://www.glassdoor.com/job-listing/designer-i-nelco-worldwide-JV_IC1154543_KO0,10_KE11,26.htm?jl=1009930075944&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJEZXNpZ25lciBJIiwiY29tcGFueV9uYW1lIjoiTkVMQ08gV29ybGR3aWRlIiwiYWRkcmVzc19jaXR5IjoiQnVybGluZ3RvbiwgTUEiLCJodGlkb2NpZCI6InFOQ0s0alpLY3pGQ0tNS2JBQUFBQUE9PSIsInV1bGUiOiJ3K0NBSVFJQ0loTURJeE5EUXNUV0Z6YzJGamFIVnpaWFIwY3l4VmJtbDBaV1FnVTNSaGRHVnoiLCJnbCI6InVzIiwiaGwiOiJlbiJ9"
            },
            {
            "title": "Graphic Designer",
            "company_name": "Granite",
            "location": "Pepperell, MA",
            "via": "ZipRecruiter",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=Ic3pIKdTy2a1Zdx8AAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXNsQoCMQwAUFzvC8QpmyDaiuCikyAcCIJ_cLQltJVeEpoMN_rp6vLWN3xWw3bsQUpNcEetmbDDAR4cQTH0VIAJRubccHMtZqIX71Wby2rBanKJZ8-EkRf_5qh_Ji2ho7RgOJ3Ox8UJ5d36t1A1hErwQhHs2NoenrcvE3LqhIMAAAA&shmds=v1_ATWGeeOd5mvpCHnAOTjNtn84yl-wt95wKPHiXGqqETdDJeK6VQ&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=Ic3pIKdTy2a1Zdx8AAAAAA%3D%3D",
            "thumbnail": "https://serpapi.com/searches/69c6ca4931aafe3e972a6c09/images/YcK7esXlUFfDi446QrfuD8mXcSm32Nyz5KKZeJtWvqQ.jpeg",
            "extensions": [
                "3 days ago",
                "Full-time",
                "Dental insurance",
                "Health insurance"
            ],
            "detected_extensions": {
                "posted_at": "3 days ago",
                "schedule_type": "Full-time",
                "dental_coverage": True,
                "health_insurance": True
            },
            "source_link": "https://www.ziprecruiter.com/c/Granite/Job/Graphic-Designer/-in-Pepperell,MA?jid=174b9763430233c2",
            "description": "Building a career at Granite may be the most valuable thing you could do...\n\nFind your dream job today, and be part of something great. Our most powerful partnership is the one we have with our employees. Our people are our most valued asset and the foundation of Granite's century-old success. We're building more than infrastructure; we are building your future.\n\nGeneral Summary\n\nThis position is the creative lead at the regional/division level and is responsible for creating and designing proposal documents in response to statements of qualifications, requests for proposals, client presentations, and division-specific marketing and campaign collateral as part of the overall effort to increase market share.\n\nEssential Job Responsibilities\n• Create or update brochures, marketing collateral, and advertisements for internal and external use.\n• Streamline theme concepts and creative design (including mood boards and storyboarding sessions) to ensure efficiency within the department.\n• Understand the division's marketing and business strategy to ensure that it is leading all work products.\n• Participate in pursuit kickoff meetings and all color reviews, by understand the key messages and direction of each deliverable to translate this information into compelling visuals and easy-to-understand copy to effectively convey the Company's message.\n• Lead publishing and assist with proposal production to ensure that they company's high-quality standards are met and proposals are delivered on time.\n• Enforce and maintain corporate brand standards in all marketing, communications and graphics; ensure brand standards and application, to maintain consistency of all division marketing-related materials.\n• Collaborate with corporate Marketing and Communications department to review all ads, brochures, videos, and other external collateral materials (non-proposal items) to ensure materials are all within the overall Company's guidelines.\n• Develop and prepare specific presentations and support material for division business development managers, for industry/association presentations, and/or to enhance new project/client opportunities.\n• Create, organize and gather permissions for content for video, print, and digital application to contribute content to the company's online photo and graphics repository.\n• Provide ready-to-publish division content for the Company's intranet, external website and social media platforms to support the Company's objectives.\n\nEducation\n• Bachelor's Degree in Graphic Design, Fine Art Design, Advertising, Communications, Marketing, or extensive relevant experience required\n\nMinimum Qualifications\n• 5+ years graphic design experience at a mid-size to large professional services organization required\n• Expert knowledge of Adobe Creative Suite (InDesign, Illustrator, Photoshop, Premiere) required\n• Compelling portfolio of original design collateral (both digital and print)\n• Prior experience working in the engineering and/or construction industry preferred\n\nKnowledge, Skills, and Abilities\n• Proficiency with all MS Office products (Word, Excel, PowerPoint)\n• Proficiency in multi-media formats, including print, video, and digital platforms\n• Attention to detail/accuracy, quick learner and internally motivated to seek out answers, generate ideas, and develop new skills\n• Strong written and oral communication skills to effectively disseminate information and convey concepts, ideas and information to all levels of internal and external customers\n• Ability to set priorities, organize work and work in high production environment while responding quickly and effectively under pressure, changing priorities and tight timelines/deadlines\n• Strong problem-solving skills, with demonstrated ability to provide creative solutions to real-time challenges with consistent follow through\n• Ability to work well individually, and as part of a team, as well as with other stakeholders\n• Ability to work in creative and structured, process-driven environment\n\nPhysical Demands\n\nThe physical demands described here are representative of those that must be met by an employee to successfully perform the essential functions of this job. While performing the duties of this job, the employee is regularly required to talk and hear. The employee frequently is required to stand, walk, sit and use hands to operate a computer keyboard. The employee is occasionally required to reach with hands and arms. The employee must occasionally lift and/or move up to 10 pounds. Specific vision abilities required by this job include close vision, and ability to adjust focus. Reasonable accommodations may be made to enable individuals with disabilities to perform the essential functions.\n\nAdditional Requirements/Skills\n• Valid driver's license\n• Ability to travel\n\nOur Benefits at a Glance:\n\nBuilding tomorrow starts with you, and Granite knows that you can excel only if we support you in and out of the workplace. That is why we offer a broad benefits package that includes paid holidays, sick leave, medical, dental, vision, life insurance, disability insurance, flexible spending plans, as well as special programs for musculoskeletal health, mental wellness, and more.\n\nSalaried employees may choose from two PPO medical plans through Anthem BlueCross, including our most popular plan, for which 100% of the premium is paid by Granite for eligible employees and dependents. Employees can also opt into a Health Savings Account (HSA) or a Flexible Spending Account (FSA).\n\nAs part of our investment in your future outside of the workplace, Granite provides a 100% match on the first 6% of eligible compensation that salaried employees defer into their 401(k) plans, which vests immediately.\n\nBenefits may vary for positions located outside of the continental United States.\n\nBase Salary Range:\n$72,355.00 - $138,867.00\n\nPay may vary based upon relevant experience, skills, location, and education among other factors.\n\nAbout Granite Construction Incorporated\n\nGranite Construction Incorporated is a member of the S&P 400 Index and is the parent company of Granite Construction Company, one of the nation's largest heavy civil contractors and construction materials producers. Granite is a Drug-Free Workplace and Equal Opportunity Employer. Employment decisions are made without regard to race, color, religion, sex, sexual orientation, national origin, age, disability, protected veteran status, or any other protected characteristic.We consider qualified applicants with arrest and conviction records in accordance with the San Francisco Fair Chance Ordinance, the Los Angeles Fair Chance Initiative for Hiring Ordinance, and other applicable laws.\n\nFor additional information on applicant/employee rights please clickhere.\n\nNotice to Staffing Agencies\n\nGranite Construction, Inc. and its subsidiaries (\"Granite\") will not accept unsolicited resumes from any source other than directly from a candidate. Any unsolicited resumes sent to Granite, including unsolicited resumes sent to a Granite mailing address, fax machine or email address, directly to Granite employees, or to Granite's resume database will be considered Granite property. Granite will NOT pay a fee for any placement resulting from the receipt of an unsolicited resume.Granite will consider any candidate for whom an Agency has submitted an unsolicited resume to have been referred by the Agency free of any charges or fees.Agencies must obtain advance written approval from Granite's recruiting function to submit resumes, and then only in conjunction with a valid fully-executed contract for service and in response to a specific job opening.Granite will not pay a fee to any Agency that does not have such agreement in place.Agency agreements will only be valid if in writing and signed by Granite's Human Resources Representative or his/ her designee. No other Granite employee is authorized to bind Granite to any agreement regarding the placement of candidates by Agencies.",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "Bachelor's Degree in Graphic Design, Fine Art Design, Advertising, Communications, Marketing, or extensive relevant experience required",
                    "5+ years graphic design experience at a mid-size to large professional services organization required",
                    "Expert knowledge of Adobe Creative Suite (InDesign, Illustrator, Photoshop, Premiere) required",
                    "Compelling portfolio of original design collateral (both digital and print)",
                    "Proficiency with all MS Office products (Word, Excel, PowerPoint)",
                    "Proficiency in multi-media formats, including print, video, and digital platforms",
                    "Attention to detail/accuracy, quick learner and internally motivated to seek out answers, generate ideas, and develop new skills",
                    "Strong written and oral communication skills to effectively disseminate information and convey concepts, ideas and information to all levels of internal and external customers",
                    "Ability to set priorities, organize work and work in high production environment while responding quickly and effectively under pressure, changing priorities and tight timelines/deadlines",
                    "Strong problem-solving skills, with demonstrated ability to provide creative solutions to real-time challenges with consistent follow through",
                    "Ability to work well individually, and as part of a team, as well as with other stakeholders",
                    "Ability to work in creative and structured, process-driven environment",
                    "Specific vision abilities required by this job include close vision, and ability to adjust focus",
                    "Valid driver's license",
                    "Ability to travel",
                    "Agencies must obtain advance written approval from Granite's recruiting function to submit resumes, and then only in conjunction with a valid fully-executed contract for service and in response to a specific job opening"
                ]
                },
                {
                "title": "Benefits",
                "items": [
                    "Building tomorrow starts with you, and Granite knows that you can excel only if we support you in and out of the workplace",
                    "That is why we offer a broad benefits package that includes paid holidays, sick leave, medical, dental, vision, life insurance, disability insurance, flexible spending plans, as well as special programs for musculoskeletal health, mental wellness, and more",
                    "Salaried employees may choose from two PPO medical plans through Anthem BlueCross, including our most popular plan, for which 100% of the premium is paid by Granite for eligible employees and dependents",
                    "Employees can also opt into a Health Savings Account (HSA) or a Flexible Spending Account (FSA)",
                    "As part of our investment in your future outside of the workplace, Granite provides a 100% match on the first 6% of eligible compensation that salaried employees defer into their 401(k) plans, which vests immediately",
                    "Benefits may vary for positions located outside of the continental United States",
                    "$72,355.00 - $138,867.00"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "This position is the creative lead at the regional/division level and is responsible for creating and designing proposal documents in response to statements of qualifications, requests for proposals, client presentations, and division-specific marketing and campaign collateral as part of the overall effort to increase market share",
                    "Create or update brochures, marketing collateral, and advertisements for internal and external use",
                    "Streamline theme concepts and creative design (including mood boards and storyboarding sessions) to ensure efficiency within the department",
                    "Understand the division's marketing and business strategy to ensure that it is leading all work products",
                    "Participate in pursuit kickoff meetings and all color reviews, by understand the key messages and direction of each deliverable to translate this information into compelling visuals and easy-to-understand copy to effectively convey the Company's message",
                    "Lead publishing and assist with proposal production to ensure that they company's high-quality standards are met and proposals are delivered on time",
                    "Enforce and maintain corporate brand standards in all marketing, communications and graphics; ensure brand standards and application, to maintain consistency of all division marketing-related materials",
                    "Collaborate with corporate Marketing and Communications department to review all ads, brochures, videos, and other external collateral materials (non-proposal items) to ensure materials are all within the overall Company's guidelines",
                    "Develop and prepare specific presentations and support material for division business development managers, for industry/association presentations, and/or to enhance new project/client opportunities",
                    "Create, organize and gather permissions for content for video, print, and digital application to contribute content to the company's online photo and graphics repository",
                    "Provide ready-to-publish division content for the Company's intranet, external website and social media platforms to support the Company's objectives",
                    "The physical demands described here are representative of those that must be met by an employee to successfully perform the essential functions of this job",
                    "While performing the duties of this job, the employee is regularly required to talk and hear",
                    "The employee frequently is required to stand, walk, sit and use hands to operate a computer keyboard",
                    "The employee is occasionally required to reach with hands and arms",
                    "The employee must occasionally lift and/or move up to 10 pounds",
                    "Reasonable accommodations may be made to enable individuals with disabilities to perform the essential functions"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/Granite/Job/Graphic-Designer/-in-Pepperell,MA?jid=174b9763430233c2&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Talentify",
                "link": "https://www.talentify.io/job/graphic-designer-pepperell-massachusetts-us-granite-construction-r0000007154?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJHcmFwaGljIERlc2lnbmVyIiwiY29tcGFueV9uYW1lIjoiR3Jhbml0ZSIsImFkZHJlc3NfY2l0eSI6IlBlcHBlcmVsbCwgTUEiLCJodGlkb2NpZCI6IkljM3BJS2RUeTJhMVpkeDhBQUFBQUE9PSIsInV1bGUiOiJ3K0NBSVFJQ0loTURJeE5EUXNUV0Z6YzJGamFIVnpaWFIwY3l4VmJtbDBaV1FnVTNSaGRHVnoiLCJnbCI6InVzIiwiaGwiOiJlbiJ9"
            },
            {
            "title": "Part-time Designer",
            "company_name": "The Container Store Inc.",
            "location": "Newton, MA",
            "via": "ZipRecruiter",
            "share_link": "https://www.google.com/search?ibp=htl;jobs&q=designer&htidocid=Iw3vd5g9g7lER5LDAAAAAA%3D%3D&hl=en-US&shndl=37&shmd=H4sIAAAAAAAA_xXNsQrCMBAAUFz7CU43CYpNRHDRSRREQRF0L2k4kkh6F3IH9jP8ZOny1tf8Zs3y6aq2mgaEM0oKhBVauHEPgq76CExwYQ4Z54eoWmRvrUg2QdRp8sbzYJmw59F-uJeJTqKrWLJT7La7zWgKhdXiHRFOTOrSVLyUK8KVvIFE8MCvMq3hfvwDJv6M1JMAAAA&shmds=v1_ATWGeeNokFgcmn1_1bOj9vcldWbzLdLjsPw5HeUYob2tnHICtQ&source=sh/x/job/li/m1/1#fpstate=tldetail&htivrt=jobs&htiq=designer&htidocid=Iw3vd5g9g7lER5LDAAAAAA%3D%3D",
            "thumbnail": "https://serpapi.com/searches/69c6ca4931aafe3e972a6c09/images/qT-Z9WcnDqvMqdqMms3T6cbzVxrYGjgq5QiokYNilCg.jpeg",
            "extensions": [
                "19 an hour",
                "Part-time",
                "Paid time off",
                "Health insurance",
                "Dental insurance"
            ],
            "detected_extensions": {
                "salary": "19 an hour",
                "schedule_type": "Part-time",
                "paid_time_off": True,
                "health_insurance": True,
                "dental_coverage": True
            },
            "source_link": "https://www.ziprecruiter.com/c/The-Container-Store-Inc./Job/Part-time-Designer/-in-Chestnut-Hill,MA?jid=4191ce6abee8fcab",
            "description": "Overview\n\nThe Part-time Designer is an expert in custom space design with a vast knowledge of all storage and organization solutions and products sold at The Container Store. This position is a strong role model who displays excellent selling skills while maintaining a focus on exceptional customer service. Schedules can include daytime, evenings and weekends. This is a part-time, hourly, non-exempt position.\n\nWhat We Stand For\n\nEstablished in 1978, The Container Store has grown to be the leading specialty retailer of storage and organization products in the United States and the only national retailer solely devoted to the category. We provide creative, multifunctional, customizable storage and organization solutions that help our customers save time, save space and improve the quality of their lives. We foster a culture built around our Foundation Principles, which define how we approach our relationships with our employees, vendors, customers and communities and influence every aspect of our business.\nResponsibilities\n• Manages and maintains multiple, simultaneous customer projects through all phases with a high level of accuracy, timeliness and follow-up with consistent and concise communication to customers and others\n• Collaborates and communicates with the customer to design and present projects and customized plans in a clear and professional manner\n• Closes sales efficiently, builds repeat and referral business\n• Consistently maintains clear communication with Managers and Support Center partners to seamlessly complete projects from inquiry to installation to achieve sales goals\n• As a brand ambassador, enthusiastically drives, motivates and supports all company initiatives by modeling professional and productive behaviors with store employees to achieve store and other goals\n• Remains current with The Container Store training, selling, product knowledge, promotions, processes and philosophies when interacting with customers, CSD, store employees and Installation\n• Proficiently and consistently uses company tools and email\n• Actively participates in the daily maintenance of custom spaces showroom and visual presentation of the store\n• Handles cash and other valuables appropriately and securely\n• Maintains a safe working and shopping environment, utilizing all available resources, ensuring safety and security of the employees, customers and property\n• Assists customers with personal confidential information related to the Company credit card and application process\n• Consistently arrives promptly to work the assigned schedule\n• Responsible for maintaining discretion related to all confidential/sensitive company and customer information\n• Performs other requested tasks and duties\n\nWe believe in taking care of our team. That's why we offer a comprehensive benefits package that goes beyond just health insurance (though we've got that covered too!). Here at The Container Store, we're passionate about helping you contain your health, grow your career, and find balance in your life.\n\nHere's a peek at what you can expect:\n• Rewarding pay to recognize the value you bring to the team. Starting at $17.00 an hour, up to $19.00 an hour.\n• Competitive health, dental, and vision plans to keep you and your loved ones well.\n• 401(k) retirement savings plan with optional investment guidance and assistance offered through Fidelity.\n• Unique \"1equals3\" website for easy access to your benefits information and company updates.\n• We've got your back! Competitive sick pay and PTO plan to ensure you can take time off to recharge and come back feeling your best.\n\nFor our full-time associates, we offer even more:\n• Peace-of-mind benefits: Basic life insurance, disability insurance options, accident insurance, critical illness insurance, hospital indemnity insurance and flexible spending accounts (FSAs).\n• Family-focused support: Considerate parental leave policies, adoption and surrogacy assistance, and fertility & maternity support program.\n• Work-life balance boosters: Paid holidays, gym membership discounts, and a qualified transportation benefits program to save on commutes.\n• Discounts galore: Enjoy a hefty discount on our amazing products, including merchandise, custom spaces, and services, gift cards, and pet insurance (because fur-babies matter!).\n• Recognition you deserve: We honor our employees with service awards and retirement gifts, celebrate those who exemplify our core principles, and recognize exceptional daily contributions.\n• Thriving with diversity: Participate in our Employee Resource and Affinity Groups and help guide how we give back to the community, while having a space to connect, support one another, and celebrate cultural heritages.\n\nBut that's not all! We offer a fun and collaborative work environment where you can learn, grow, and make a real difference.\nQualifications\n• College degree preferred\n• 2-5 years sales and clientele experience preferred\n• Maintains professional appearance and wears required dress code when representing The Container Store\n• Knowledge and passion for following trends in the custom spaces and retail industry\n• Strong computer skills: proficiency in Outlook, Word and knowledge of Excel and Salesforce or Customer Relations Management tools\n• Ability to work in a constant state of alertness and a safe manner\n• Is committed to working scheduled hours and has the flexibility to work additional hours based on changing business needs\n• Ability to communicate clearly and effectively in a professional manner, both orally and in writing, at all levels within and outside the organization\n• Ability to quickly separate the mission-critical tasks from the lower priority tasks; focuses on the most value-added projects of the day or week\n• Flexible, with a positive attitude and passion for knowledge\n• Strong time management and organizational skills with the ability to successfully manage multiple projects at once\n• Possesses focused attention to detail while working quickly and accurately under pressure\n• Makes strategic and effective decisions in the best interest of our customers and our company, taking care to objectively process information\n• Ability to work within and exemplify The Container Store brand which we describe as matchless, fun, authentic, team-focused and life-changing\n• Must be at least 18 years of age\n\nThe Container Store promotes a smoke-free, drug-free environment.\n\nWe are proud to be an Equal Opportunity Employer and comply with the\n\nAmericans with Disabilities Act\n\nStores Physical Requirements\n\nState Specific Notices\nEmployment Type: PART_TIME",
            "job_highlights": [
                {
                "title": "Qualifications",
                "items": [
                    "Maintains professional appearance and wears required dress code when representing The Container Store",
                    "Knowledge and passion for following trends in the custom spaces and retail industry",
                    "Strong computer skills: proficiency in Outlook, Word and knowledge of Excel and Salesforce or Customer Relations Management tools",
                    "Ability to work in a constant state of alertness and a safe manner",
                    "Is committed to working scheduled hours and has the flexibility to work additional hours based on changing business needs",
                    "Ability to communicate clearly and effectively in a professional manner, both orally and in writing, at all levels within and outside the organization",
                    "Ability to quickly separate the mission-critical tasks from the lower priority tasks; focuses on the most value-added projects of the day or week",
                    "Flexible, with a positive attitude and passion for knowledge",
                    "Strong time management and organizational skills with the ability to successfully manage multiple projects at once",
                    "Possesses focused attention to detail while working quickly and accurately under pressure",
                    "Makes strategic and effective decisions in the best interest of our customers and our company, taking care to objectively process information",
                    "Ability to work within and exemplify The Container Store brand which we describe as matchless, fun, authentic, team-focused and life-changing",
                    "Must be at least 18 years of age"
                ]
                },
                {
                "title": "Benefits",
                "items": [
                    "That's why we offer a comprehensive benefits package that goes beyond just health insurance (though we've got that covered too!)",
                    "Rewarding pay to recognize the value you bring to the team",
                    "Starting at $17.00 an hour, up to $19.00 an hour",
                    "Competitive health, dental, and vision plans to keep you and your loved ones well",
                    "401(k) retirement savings plan with optional investment guidance and assistance offered through Fidelity",
                    "Unique \"1equals3\" website for easy access to your benefits information and company updates",
                    "We've got your back!",
                    "Competitive sick pay and PTO plan to ensure you can take time off to recharge and come back feeling your best",
                    "For our full-time associates, we offer even more:",
                    "Peace-of-mind benefits: Basic life insurance, disability insurance options, accident insurance, critical illness insurance, hospital indemnity insurance and flexible spending accounts (FSAs)",
                    "Family-focused support: Considerate parental leave policies, adoption and surrogacy assistance, and fertility & maternity support program",
                    "Work-life balance boosters: Paid holidays, gym membership discounts, and a qualified transportation benefits program to save on commutes",
                    "Discounts galore: Enjoy a hefty discount on our amazing products, including merchandise, custom spaces, and services, gift cards, and pet insurance (because fur-babies matter!)",
                    "Recognition you deserve: We honor our employees with service awards and retirement gifts, celebrate those who exemplify our core principles, and recognize exceptional daily contributions",
                    "Thriving with diversity: Participate in our Employee Resource and Affinity Groups and help guide how we give back to the community, while having a space to connect, support one another, and celebrate cultural heritages",
                    "We offer a fun and collaborative work environment where you can learn, grow, and make a real difference"
                ]
                },
                {
                "title": "Responsibilities",
                "items": [
                    "Schedules can include daytime, evenings and weekends",
                    "This is a part-time, hourly, non-exempt position",
                    "Manages and maintains multiple, simultaneous customer projects through all phases with a high level of accuracy, timeliness and follow-up with consistent and concise communication to customers and others",
                    "Collaborates and communicates with the customer to design and present projects and customized plans in a clear and professional manner",
                    "Closes sales efficiently, builds repeat and referral business",
                    "Consistently maintains clear communication with Managers and Support Center partners to seamlessly complete projects from inquiry to installation to achieve sales goals",
                    "As a brand ambassador, enthusiastically drives, motivates and supports all company initiatives by modeling professional and productive behaviors with store employees to achieve store and other goals",
                    "Remains current with The Container Store training, selling, product knowledge, promotions, processes and philosophies when interacting with customers, CSD, store employees and Installation",
                    "Proficiently and consistently uses company tools and email",
                    "Actively participates in the daily maintenance of custom spaces showroom and visual presentation of the store",
                    "Handles cash and other valuables appropriately and securely",
                    "Maintains a safe working and shopping environment, utilizing all available resources, ensuring safety and security of the employees, customers and property",
                    "Assists customers with personal confidential information related to the Company credit card and application process",
                    "Consistently arrives promptly to work the assigned schedule",
                    "Responsible for maintaining discretion related to all confidential/sensitive company and customer information",
                    "Performs other requested tasks and duties"
                ]
                }
            ],
            "apply_options": [
                {
                "title": "ZipRecruiter",
                "link": "https://www.ziprecruiter.com/c/The-Container-Store-Inc./Job/Part-time-Designer/-in-Chestnut-Hill,MA?jid=4191ce6abee8fcab&utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Career.io",
                "link": "https://career.io/job/designer-newton-the-container-store-inc-4989cae777ca486184b7f40cfe62c843?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "SonicJobs",
                "link": "https://www.sonicjobs.com/us/jobs/new-town/part-time/part-time-designer-69979eea18bd2e508c6ea762?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Breakroom",
                "link": "https://www.breakroom.cc/en-us/jobs/listing/26205699-the-container-store-inc-part-time-designer-55-boylston?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Adzuna",
                "link": "https://www.adzuna.com/details/5595707669?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                },
                {
                "title": "Jobilize",
                "link": "https://www.jobilize.com/job/us-ma-newton-requisition-part-time-designer-container-store-hiring?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"
                }
            ],
            "job_id": "eyJqb2JfdGl0bGUiOiJQYXJ0LXRpbWUgRGVzaWduZXIiLCJjb21wYW55X25hbWUiOiJUaGUgQ29udGFpbmVyIFN0b3JlIEluYy4iLCJhZGRyZXNzX2NpdHkiOiJOZXd0b24sIE1BIiwiaHRpZG9jaWQiOiJJdzN2ZDVnOWc3bEVSNUxEQUFBQUFBPT0iLCJ1dWxlIjoidytDQUlRSUNJaE1ESXhORFFzVFdGemMyRmphSFZ6WlhSMGN5eFZibWwwWldRZ1UzUmhkR1Z6IiwiZ2wiOiJ1cyIsImhsIjoiZW4ifQ=="
            }
        ],
        "serpapi_pagination": {
            "next_page_token": "eyJmYyI6IkVzd0VDb3dFUVUxdU15MTVWRUZSV21WaFRFRjFaWGx2T0hKa01XNTNZMVozVVVaaE5uSnZUMnN6WkdOSGExSTNjMkkwZUdNMlgwOWtMVFF0UTNSVU1XVjNWRzFIT0VGWlRtbEZVVk15Tm1jeGVqQjNlbkJWT1ZGNGFFRmFiamhqVW10cFZWZFNRMEYxWkVOWmVXOWhkVUZTT1RSS2JWTm1TekptVTJWMlIwOVFZVWMyYUc5MVl6TlNRWEY0ZEZOdU0zTk5Na3BzWW1KNVpsZElUa3hKZFZSNGNsUTRNV3R4TW5oTFpVRm9WVFU1WjFwalRsOVJRbkpuZUdjeWNUSTBZbWN3YmtWRFJtRnpXbFZSVVUxUllrZ3RWekpVZUZNMlkwRkVWMHAxYW1RemFtcEJTR1Z6WDA1aWRtMW5XRVJEWkhWa01XcFRRMnM1WlUxcmJIQTFjV2hqUkZsMk1rTnBMVEY1Tm5Zd1ZGcG5aVkF6VVVoRVRTMVNkRGxqTmsxa1pHdEdPRWN4VW5GU1MxOUtVSGh6V0VsQ1Myd3hRM2hhVlhweFluaGZVWE5GVEdzMVdXeFJURVJOU205VldVTkRRVkpWT0ROaE5sWkhlWGhrZEdwWGRHbFNlV010UTI4MWJXSlpWRTh4WjA1UWFFSkRlbmx6U25KWU0ybHhjMjlFYWtoNlEwb3paMU5JVGpaUlJEZ3RaVFJpVkRablRGZFljRkZuVWxaUGIyRjJYME10T1RaMmJ6VklPRVJNYkcxVFZqZDBSbG80TTFseGVXeG5Ra0pwVXpWUWNraEpSa1UxVDBob1RFUkVOWGwxZW5vMGVWRjJWMkZ0UmtSeWJWa3pSemczWm5sQlNETnhSVko0T0VwMVlubE1SbTVPUVc5NmVWQmFaMk14YW1oTU9FeFZaV2h5ZFc1cE5USkVaVUZaWVhvU0YxUnpja2RoWVRNNVRHWTJWSEE0TkZCNGRUSm9kVUZ6R2lKQlNrdE1SbTFKTFRaZlIwSmpYMmQ2YmpGb1VVNHphVWx3UmxCV1JIbHBPRTlCIiwiZmN2IjoiMyJ9",
            "next": "https://serpapi.com/search.json?engine=google_jobs&gl=us&google_domain=google.com&hl=en&location=02144&next_page_token=eyJmYyI6IkVzd0VDb3dFUVUxdU15MTVWRUZSV21WaFRFRjFaWGx2T0hKa01XNTNZMVozVVVaaE5uSnZUMnN6WkdOSGExSTNjMkkwZUdNMlgwOWtMVFF0UTNSVU1XVjNWRzFIT0VGWlRtbEZVVk15Tm1jeGVqQjNlbkJWT1ZGNGFFRmFiamhqVW10cFZWZFNRMEYxWkVOWmVXOWhkVUZTT1RSS2JWTm1TekptVTJWMlIwOVFZVWMyYUc5MVl6TlNRWEY0ZEZOdU0zTk5Na3BzWW1KNVpsZElUa3hKZFZSNGNsUTRNV3R4TW5oTFpVRm9WVFU1WjFwalRsOVJRbkpuZUdjeWNUSTBZbWN3YmtWRFJtRnpXbFZSVVUxUllrZ3RWekpVZUZNMlkwRkVWMHAxYW1RemFtcEJTR1Z6WDA1aWRtMW5XRVJEWkhWa01XcFRRMnM1WlUxcmJIQTFjV2hqUkZsMk1rTnBMVEY1Tm5Zd1ZGcG5aVkF6VVVoRVRTMVNkRGxqTmsxa1pHdEdPRWN4VW5GU1MxOUtVSGh6V0VsQ1Myd3hRM2hhVlhweFluaGZVWE5GVEdzMVdXeFJURVJOU205VldVTkRRVkpWT0ROaE5sWkhlWGhrZEdwWGRHbFNlV010UTI4MWJXSlpWRTh4WjA1UWFFSkRlbmx6U25KWU0ybHhjMjlFYWtoNlEwb3paMU5JVGpaUlJEZ3RaVFJpVkRablRGZFljRkZuVWxaUGIyRjJYME10T1RaMmJ6VklPRVJNYkcxVFZqZDBSbG80TTFseGVXeG5Ra0pwVXpWUWNraEpSa1UxVDBob1RFUkVOWGwxZW5vMGVWRjJWMkZ0UmtSeWJWa3pSemczWm5sQlNETnhSVko0T0VwMVlubE1SbTVPUVc5NmVWQmFaMk14YW1oTU9FeFZaV2h5ZFc1cE5USkVaVUZaWVhvU0YxUnpja2RoWVRNNVRHWTJWSEE0TkZCNGRUSm9kVUZ6R2lKQlNrdE1SbTFKTFRaZlIwSmpYMmQ2YmpGb1VVNHphVWx3UmxCV1JIbHBPRTlCIiwiZmN2IjoiMyJ9&q=designer"
        }
        }
    return placeholder
