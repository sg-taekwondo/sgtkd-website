from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from pathlib import Path

OUT = Path("downloads")
OUT.mkdir(exist_ok=True)
BLUE, GREEN, GREY = HexColor("#183b91"), HexColor("#08783f"), HexColor("#555555")

def wrap(text, size, max_width):
    words, lines, current = text.split(), [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if stringWidth(trial, "Helvetica", size) <= max_width:
            current = trial
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines

def build(path, title, subtitle, kind):
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4; f = c.acroForm; left, right = 48, w-48; y = h-120
    def header():
        nonlocal y
        c.setFillColor(BLUE); c.setFont("Helvetica-Bold",17); c.drawCentredString(w/2,h-48,"SG TAEKWON-DO")
        c.setFont("Helvetica-Bold",14); c.drawCentredString(w/2,h-70,title)
        c.setFillColor(GREY); c.setFont("Helvetica-Oblique",9); c.drawCentredString(w/2,h-87,subtitle)
        c.setStrokeColor(GREEN); c.setLineWidth(1.2); c.line(left,h-100,right,h-100)
        y=h-120
    def ensure(points=40):
        nonlocal y
        if y < points:
            c.showPage(); y=h-45
    def section(t):
        nonlocal y
        ensure(70); c.setFillColor(GREEN); c.setFont("Helvetica-Bold",11); c.drawString(left,y,t); y-=18
    def field(label,name,box_h=19,multi=False):
        nonlocal y
        ensure(box_h+55); c.setFillColor(HexColor("#111111")); c.setFont("Helvetica",9); c.drawString(left,y,label); y-=box_h+5
        f.textfield(name=name,tooltip=label,x=left,y=y,width=right-left,height=box_h,borderStyle="underlined",borderWidth=.8,borderColor=GREY,fillColor=HexColor("#ffffff"),textColor=HexColor("#111111"),forceBorder=True,fieldFlags="multiline" if multi else "")
        y-=15
    def check(label,name):
        nonlocal y
        ensure(45); f.checkbox(name=name,tooltip=label,x=left,y=y-2,size=12,buttonStyle="check",borderWidth=1,borderColor=GREY,fillColor=HexColor("#ffffff"),textColor=GREEN,forceBorder=True)
        c.setFillColor(HexColor("#111111")); c.setFont("Helvetica",9); c.drawString(left+19,y,label); y-=22
    def para(t,size=9,leading=12):
        nonlocal y
        for line in wrap(t,size,right-left):
            ensure(45); c.setFillColor(HexColor("#111111")); c.setFont("Helvetica",size); c.drawString(left,y,line); y-=leading
        y-=5
    header()
    if kind=="health":
        section("1. STUDENT DETAILS")
        field("Student full name","student_full_name"); field("Date of birth","date_of_birth")
        field("Parent / guardian (if under 18)","parent_guardian")
        field("Emergency contact and relationship","emergency_contact_relationship")
        field("Emergency contact phone","emergency_contact_phone")
        section("2. HEALTH INFORMATION")
        para("Does the student have any health condition, allergy, injury, disability, medication requirement or other consideration that could affect safe participation in Taekwon-Do or require action in an emergency?")
        check("Yes","health_consideration_yes"); check("No","health_consideration_no")
        field("Relevant details (condition / allergy / injury / triggers)","health_details",38,True)
        field("Medication / emergency treatment instructions (if relevant)","medication_instructions",34,True)
        field("Adjustments or restrictions requested for training (if any)","training_adjustments",34,True)
        section("3. DECLARATION & PRIVACY")
        para("I confirm that the information provided is accurate to the best of my knowledge. I will tell the club promptly if relevant health information changes. This form helps the club consider safe participation and respond to emergencies; it is not a medical assessment or guarantee of safety.")
        para("Health information is sensitive personal data. SG Taekwon-Do will restrict access to people who need it for student safety, use it only for appropriate safety and administration purposes, and handle it under applicable data-protection law and the club privacy notice.")
        field("Parent / guardian or adult student name","declarant_name"); field("Date","declaration_date")
        field("Signature (type full name if completing electronically)","signature")
        check("Student has been involved in discussing relevant health information, where appropriate.","student_involved")
        para("CONFIDENTIAL — KEEP SECURELY. Update this form when relevant health details change. Do not distribute completed forms publicly.",8,10)
    else:
        section("1. STUDENT DETAILS")
        field("Student full name","student_full_name"); field("Date of birth","date_of_birth")
        field("Parent / guardian (if under 18)","parent_guardian"); field("Contact email or phone","contact_details")
        section("2. PERMISSIONS — TICK EACH USE YOU AGREE TO")
        para("SG Taekwon-Do may take photographs and video recordings during training, gradings, competitions and club activities. Consent is optional and is not a condition of joining or taking part. Select the uses you permit.")
        check("Club website and online news / reports","consent_website_news")
        check("Club social media (e.g. Facebook / Instagram)","consent_social_media")
        check("Club advertising, posters, leaflets and promotional materials","consent_promotion")
        check("Competition, grading and event highlights / achievements","consent_events")
        section("3. PLEASE READ")
        para("The club will use images and recordings responsibly for the purposes you have ticked. The club will avoid publishing a student’s full name alongside an image unless there is a specific reason and appropriate agreement.")
        para("Content published online may be viewed, copied or reshared by others. The club cannot guarantee removal of copies made by third parties or from printed materials already distributed.")
        para("You may withdraw consent at any time by contacting seangradytkd4@gmail.com. The club will stop future use for the relevant purpose and, where reasonably practicable, remove content it controls. Withdrawal does not affect the lawfulness of use before withdrawal.")
        para("Identifiable images and contact details will be handled in line with applicable data-protection law and the club privacy notice. For children, the club will also take account of the child’s views and understanding.")
        section("4. DECLARATION")
        para("I confirm that I have read and understood this form and have authority to give consent for the student named above, where applicable. I understand that I can choose different permissions above and withdraw consent as described.")
        field("Parent / guardian or adult student name","declarant_name"); field("Date","declaration_date")
        field("Signature (type full name if completing electronically)","signature")
        check("Student has been involved in discussing consent, where appropriate.","student_involved")
        para("CONSENT RECORD — KEEP SECURELY. Do not distribute completed consent forms publicly. Update the club if permissions change.",8,10)
    if kind == "health":
        para("Return the completed form privately to seangradytkd4@gmail.com. Health information is sensitive; do not post completed forms publicly.",8,10)
    else:
        para("Return the completed form to seangradytkd4@gmail.com.",8,10)
    c.save()

build(OUT/"SG_Taekwondo_Health_Declaration_Fillable.pdf","STUDENT HEALTH DECLARATION","Confidential — complete one form per student","health")
build(OUT/"SG_Taekwondo_Photo_Video_Consent_Fillable.pdf","PHOTO & VIDEO CONSENT FORM","Complete one form per student","consent")
