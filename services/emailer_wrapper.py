import smtplib
import os
import re
import time
import random
from email.message import EmailMessage
from threading import Thread

# Default email bodies from original scripts
OFFER_LETTER_SUBJECT = "Internship Offer Letter"

OFFER_LETTER_PLAIN = """\
Dear {name},

Congratulations! You have been selected for the internship program at Zynvex Solutions.

Your official Offer Letter is attached.

The internship begins on 19 July. To confirm your seat, please complete the registration form and pay the nominal fee by 15 July.

To submit your payment details, please click the "Register Now" button below and complete the registration form with the required information.

Registration Form: https://forms.gle/28eDnzxH5DWHejHy7
Fee: PKR 320 (Pakistan) / USD 1.50 (International)

Why a registration fee?
When we launched this internship program, the opportunity was offered completely free of charge. However, due to a lack of serious participation from several candidates in the free batch, we have introduced a nominal registration fee.

This fee is applicable only after you have been shortlisted and received your official offer letter. Its purpose is to ensure that only committed and serious candidates confirm their participation in the program.

There are no charges for the internship certificate, and there are no hidden fees involved.

Best regards,
Zynvex Solutions
"""

OFFER_LETTER_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Internship Offer Letter | Zynvex Solutions</title>
</head>

<body style="margin:0; padding:0; background-color:#F4F2F8; font-family:Arial, Helvetica, sans-serif; color:#292430;">

    <!-- Preheader -->
    <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent;">
        Congratulations! Your official internship offer letter from Zynvex Solutions is attached.
    </div>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
        style="width:100%; background-color:#F4F2F8; padding:45px 15px;">

        <tr>
            <td align="center">

                <!-- Main Container -->
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                    style="max-width:620px; background-color:#FFFFFF; border-radius:16px; overflow:hidden; box-shadow:0 8px 30px rgba(47,34,69,0.10);">

                    <!-- ================= HEADER ================= -->
                    <tr>
                        <td style="background-color:#6F5A8E; padding:38px 40px; text-align:center;">

                            <p style="margin:0; font-size:27px; line-height:1.2; font-weight:700; color:#FFFFFF; letter-spacing:0.5px;">
                                ZYNVEX SOLUTIONS
                            </p>

                            <p style="margin:10px 0 18px; font-size:14px; line-height:1.5; color:#E9E1F4; letter-spacing:1px; text-transform:uppercase;">
                                Internship Offer Letter
                            </p>

                            <!-- Batch Badge -->
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">
                                <tr>
                                    <td style="background-color:#FFFFFF; border-radius:20px; padding:8px 21px;">
                                        <p style="margin:0; font-size:12px; line-height:1.2; font-weight:700; color:#6F5A8E; letter-spacing:1.3px;">
                                            BATCH 04
                                        </p>
                                    </td>
                                </tr>
                            </table>

                        </td>
                    </tr>

                    <!-- ================= CONTENT ================= -->
                    <tr>
                        <td style="padding:42px 42px 38px;">

                            <!-- Greeting -->
                            <p style="margin:0 0 22px; font-size:17px; line-height:1.6; color:#302B38;">
                                Dear <strong style="color:#6F5A8E;">{name}</strong>,
                            </p>

                            <!-- Congratulations -->
                            <p style="margin:0 0 25px; font-size:16px; line-height:1.75; color:#4B4652;">
                                <strong style="color:#6F5A8E;">Congratulations!</strong>
                                We are pleased to inform you that you have been selected for an
                                <strong style="color:#6F5A8E;">internship opportunity</strong>
                                with <strong>Zynvex Solutions</strong>.
                            </p>

                            <!-- Offer Letter Notice -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#F3EFF8; border-radius:12px; margin:0 0 28px;">

                                <tr>
                                    <td style="padding:22px 24px;">

                                        <p style="margin:0 0 7px; font-size:12px; color:#7A6F84; text-transform:uppercase; letter-spacing:0.9px; font-weight:700;">
                                            Official Internship Offer
                                        </p>

                                        <p style="margin:0; font-size:16px; line-height:1.6; color:#4E3B68; font-weight:600;">
                                            Your official Offer Letter is attached to this email.
                                        </p>

                                    </td>
                                </tr>

                            </table>

                            <!-- Internship Details -->
                            <p style="margin:0 0 14px; font-size:18px; line-height:1.4; color:#302B38; font-weight:700;">
                                Internship Details
                            </p>

                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#FBFAFD; border:1px solid #E6DFEE; border-radius:12px; margin:0 0 30px;">

                                <tr>
                                    <td style="padding:22px 24px;">

                                        <p style="margin:0 0 14px; font-size:14px; color:#706675;">
                                            <strong style="color:#3C3544;">Internship Start Date</strong><br>
                                            <span style="font-size:15px; color:#51495A;">
                                                September 20th, 2026
                                            </span>
                                        </p>

                                        <p style="margin:0; font-size:14px; color:#706675;">
                                            <strong style="color:#3C3544;">Confirmation Deadline</strong><br>
                                            <span style="font-size:15px; color:#51495A;">
                                                Within 2 days of receiving your offer letter
                                            </span>
                                        </p>

                                    </td>
                                </tr>

                            </table>

                            <!-- Confirmation Introduction -->
                            <p style="margin:0 0 24px; font-size:15px; line-height:1.75; color:#4F4955;">
                                To confirm your internship seat, please complete the registration form and submit the
                                nominal registration fee before the confirmation deadline.
                            </p>

                            <!-- Registration Instructions -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#F5F0FA; border:1px solid #DED3EA; border-radius:12px; margin:0 0 22px;">

                                <tr>
                                    <td style="padding:20px 22px;">

                                        <p style="margin:0; font-size:14px; line-height:1.7; color:#51495A;">
                                            <strong style="color:#5E4B7A;">Complete Your Registration</strong><br>
                                            To submit your payment details and confirm your participation, click the
                                            <strong>"Register Now"</strong> button below and complete the registration form
                                            with the required information.
                                        </p>

                                    </td>
                                </tr>

                            </table>

                            <!-- Register Button -->
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 30px;">

                                <tr>
                                    <td align="center" style="background-color:#7C64A0; border-radius:8px;">

                                        <a href="https://forms.gle/t5rRd1ar6qiE43yz5"
                                            target="_blank"
                                            style="display:inline-block; padding:15px 38px; font-size:15px; line-height:1.2; font-weight:700; color:#FFFFFF; text-decoration:none; letter-spacing:0.3px;">
                                            Register Now →
                                        </a>

                                    </td>
                                </tr>

                            </table>

                            <!-- Registration Fee -->
                            <p style="margin:0 0 14px; font-size:18px; line-height:1.4; color:#302B38; font-weight:700;">
                                Registration Fee
                            </p>

                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#FBFAFD; border:1px solid #E6DFEE; border-radius:12px; margin:0 0 28px;">

                                <tr>
                                    <td style="padding:20px 24px;">

                                        <p style="margin:0 0 8px; font-size:15px; color:#4A4350;">
                                            <strong style="font-size:18px; color:#4E3B68;">PKR 320</strong>
                                            <span style="color:#77707C;"> — Pakistan</span>
                                        </p>

                                        <p style="margin:0; font-size:15px; color:#4A4350;">
                                            <strong style="font-size:18px; color:#4E3B68;">USD 1.50</strong>
                                            <span style="color:#77707C;"> — International</span>
                                        </p>

                                    </td>
                                </tr>

                            </table>

                            <!-- Why Registration Fee -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#F9F7FB; border-left:4px solid #8E7CC3; margin:0 0 25px;">

                                <tr>
                                    <td style="padding:20px 22px;">

                                        <p style="margin:0 0 10px; font-size:15px; color:#51495A; font-weight:700;">
                                            Why is there a registration fee?
                                        </p>

                                        <p style="margin:0; font-size:14px; line-height:1.75; color:#625B67;">
                                            When we launched this internship program, the opportunity was initially offered
                                            completely free of charge. However, due to limited commitment and participation
                                            from several candidates in the free batch, we introduced a nominal registration fee.
                                        </p>

                                        <p style="margin:12px 0 0; font-size:14px; line-height:1.75; color:#625B67;">
                                            This fee applies only after you have been shortlisted and have received your
                                            official offer letter. Its purpose is to ensure that confirmed participants are
                                            genuinely committed to completing the program.
                                        </p>

                                        <p style="margin:12px 0 0; font-size:14px; line-height:1.75; color:#625B67;">
                                            There are <strong>no charges for the internship certificate</strong> and
                                            <strong>no hidden or additional fees</strong>.
                                        </p>

                                    </td>
                                </tr>

                            </table>

                            <!-- Important Notice -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#FFF7F5; border:1px solid #F1D5CE; border-radius:10px; margin:0 0 30px;">

                                <tr>
                                    <td style="padding:18px 20px;">

                                        <p style="margin:0; font-size:13px; line-height:1.7; color:#75443D;">
                                            <strong>Important:</strong>
                                            This registration link is intended exclusively for selected interns.
                                            Please do not share it with others.
                                        </p>

                                    </td>
                                </tr>

                            </table>

                            <!-- Divider -->
                            <hr style="border:none; border-top:1px solid #E4DEE9; margin:0 0 28px;">

                            <!-- Future Opportunities -->
                            <p style="margin:0 0 14px; font-size:15px; line-height:1.7; color:#4F4955;">
                                <strong style="color:#5E4B7A;">
                                    A Note on Future Opportunities
                                </strong>
                            </p>

                            <p style="margin:0 0 20px; font-size:14px; line-height:1.75; color:#625B67;">
                                Consistent, dedicated, and hardworking candidates may be considered for specific roles
                                within Zynvex Solutions based on their performance, skills, and chosen domain.
                                We look forward to seeing what you are capable of achieving.
                            </p>

                            <p style="margin:0 0 28px; font-size:14px; line-height:1.75; color:#625B67;">
                                Stay committed, give your best, and use this internship as an opportunity to strengthen
                                your skills, gain practical experience, and demonstrate your professionalism.
                            </p>

                            <!-- Email Notice -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="border-top:1px solid #E4DEE9;">

                                <tr>
                                    <td style="padding-top:22px;">

                                        <p style="margin:0; font-size:12px; line-height:1.75; color:#77717D;">
                                            <strong style="color:#625B68;">Email Notice:</strong>
                                            This email was sent from the company's official working email address.
                                            If you find this message in your <strong>Spam or Junk folder</strong>,
                                            this does not necessarily mean the email is suspicious or unauthorized.
                                            Email providers may automatically filter messages when similar official
                                            communications are sent to multiple recipients simultaneously.
                                        </p>

                                    </td>
                                </tr>

                            </table>

                        </td>
                    </tr>

                    <!-- ================= FOOTER ================= -->
                    <tr>
                        <td style="background-color:#F7F5F9; border-top:1px solid #E5DFEA; padding:28px 40px; text-align:center;">

                            <p style="margin:0 0 7px; font-size:14px; color:#756B80;">
                                Best regards,
                            </p>

                            <p style="margin:0; font-size:19px; color:#4E3B68; font-weight:700;">
                                Zynvex Solutions
                            </p>

                            <p style="margin:9px 0 0; font-size:12px; color:#99919F;">
                                Internship Program · Batch 04
                            </p>

                        </td>
                    </tr>

                </table>

                <!-- Copyright -->
                <p style="margin:20px 0 0; font-size:11px; color:#938A9C; text-align:center;">
                    © Zynvex Solutions. All rights reserved.
                </p>

            </td>
        </tr>
    </table>

</body>
</html>
"""

CONFIRM_EMAIL_SUBJECT = "Your ZYNVEX Internship Seat Has Been Confirmed"

CONFIRM_EMAIL_PLAIN = """\
Hello {name},

Congratulations! Your payment has been confirmed. You have been selected for the {role} internship program.

Important Update: The internship start date has been changed from 20 September to 19 September.

Your Internship ID: {internship_id}

Please join your dedicated internship group using the link below:

Group Link: {group_link}

You will receive further instructions and updates through this group.

Best Regards,
ZYNVEX Team
"""

CONFIRM_EMAIL_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Internship Confirmation | Zynvex Solutions</title>
</head>

<body style="margin:0; padding:0; background-color:#F4F2F8; font-family:Arial, Helvetica, sans-serif; color:#25212B;">

    <!-- Preheader -->
    <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent;">
        Your internship payment has been confirmed. Welcome to Zynvex Solutions.
    </div>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
        style="background-color:#F4F2F8; padding:45px 15px;">
        <tr>
            <td align="center">

                <!-- Main Container -->
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                    style="max-width:620px; background-color:#FFFFFF; border-radius:16px; overflow:hidden; box-shadow:0 8px 30px rgba(47,34,69,0.10);">

                    <!-- Header -->
                    <tr>
                        <td style="background-color:#6F5A8E; padding:38px 40px; text-align:center;">

                            <p style="margin:0; font-size:26px; line-height:1.2; font-weight:700; color:#FFFFFF; letter-spacing:0.4px;">
                                ZYNVEX SOLUTIONS
                            </p>

                            <p style="margin:10px 0 18px; font-size:14px; line-height:1.5; color:#E9E1F4; letter-spacing:1px; text-transform:uppercase;">
                                Internship Confirmation
                            </p>

                            <!-- Batch Badge -->
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">
                                <tr>
                                    <td style="background-color:#FFFFFF; border-radius:20px; padding:8px 20px;">
                                        <p style="margin:0; font-size:12px; line-height:1.2; font-weight:700; color:#6F5A8E; letter-spacing:1.2px;">
                                            BATCH 04
                                        </p>
                                    </td>
                                </tr>
                            </table>

                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding:42px 42px 35px;">

                            <!-- Greeting -->
                            <p style="margin:0 0 22px; font-size:17px; line-height:1.6; color:#302B38;">
                                Dear <strong style="color:#6F5A8E;">{name}</strong>,
                            </p>

                            <!-- Introduction -->
                            <p style="margin:0 0 24px; font-size:16px; line-height:1.75; color:#4A4552;">
                                We are pleased to confirm that your payment has been successfully received and your selection for the
                                <strong style="color:#6F5A8E;">{role}</strong> internship program has been confirmed.
                            </p>

                            <!-- Success Banner -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#F3EFF8; border-radius:12px; margin:0 0 28px;">
                                <tr>
                                    <td style="padding:22px 24px;">

                                        <p style="margin:0 0 7px; font-size:13px; color:#756A80; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">
                                            Application Status
                                        </p>

                                        <p style="margin:0; font-size:17px; color:#4E3B68; font-weight:700;">
                                            ✓ Internship Confirmed
                                        </p>

                                    </td>
                                </tr>
                            </table>

                            <!-- Internship ID -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#FBFAFD; border:1px solid #E7E0EF; border-radius:12px; margin:0 0 30px;">
                                <tr>
                                    <td style="padding:22px 24px;">

                                        <p style="margin:0 0 6px; font-size:13px; color:#81758D; text-transform:uppercase; letter-spacing:0.7px; font-weight:600;">
                                            Internship ID
                                        </p>

                                        <p style="margin:0; font-size:19px; color:#30283A; font-weight:700; letter-spacing:0.4px;">
                                            {internship_id}
                                        </p>

                                    </td>
                                </tr>
                            </table>

                            <!-- WhatsApp Section -->
                            <p style="margin:0 0 10px; font-size:18px; color:#302B38; font-weight:700;">
                                Join Your Internship Community
                            </p>

                            <p style="margin:0 0 24px; font-size:15px; line-height:1.7; color:#5B5562;">
                                Please join your dedicated internship WhatsApp group using the button below. Important announcements,
                                instructions, and updates will be shared through this group.
                            </p>

                            <!-- WhatsApp Button -->
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 28px;">
                                <tr>
                                    <td align="center" style="background-color:#25D366; border-radius:8px;">

                                        <a href="{group_link}"
                                            target="_blank"
                                            style="display:inline-block; padding:15px 32px; font-size:15px; line-height:1.2; font-weight:700; color:#FFFFFF; text-decoration:none; letter-spacing:0.2px;">
                                            Join WhatsApp Group →
                                        </a>

                                    </td>
                                </tr>
                            </table>

                            <!-- Reminder -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="background-color:#FFF9F0; border:1px solid #F1DFC1; border-radius:10px; margin:0 0 30px;">
                                <tr>
                                    <td style="padding:18px 20px;">

                                        <p style="margin:0; font-size:14px; line-height:1.65; color:#665742;">
                                            <strong>Please Note:</strong> Make sure you join the WhatsApp group to receive important
                                            internship-related announcements and instructions.
                                        </p>

                                    </td>
                                </tr>
                            </table>

                            <!-- Closing Message -->
                            <p style="margin:0 0 18px; font-size:15px; line-height:1.75; color:#4F4A55;">
                                We are excited to have you join us and look forward to your participation, learning, and contribution
                                throughout the internship program.
                            </p>

                            <p style="margin:0 0 28px; font-size:15px; line-height:1.75; color:#4F4A55;">
                                Stay committed, make the most of this opportunity, and give your best.
                            </p>

                            <!-- Email Authenticity Notice -->
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                style="border-top:1px solid #E8E3ED; margin-top:10px;">
                                <tr>
                                    <td style="padding-top:22px;">

                                        <p style="margin:0; font-size:12px; line-height:1.7; color:#77717D;">
                                            <strong style="color:#625B68;">Email Notice:</strong>
                                            This email was sent from the company's official working email address.
                                            If you find this message in your <strong>Spam or Junk folder</strong>, please note that
                                            this may occur when official communications are sent to multiple recipients simultaneously.
                                        </p>

                                    </td>
                                </tr>
                            </table>

                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color:#F7F5F9; border-top:1px solid #E8E3ED; padding:28px 40px; text-align:center;">

                            <p style="margin:0 0 7px; font-size:14px; color:#756B80;">
                                Best regards,
                            </p>

                            <p style="margin:0; font-size:18px; color:#4E3B68; font-weight:700;">
                                ZYNVEX Team
                            </p>

                            <p style="margin:9px 0 0; font-size:12px; color:#99919F;">
                                Zynvex Solutions · Internship Program
                            </p>

                        </td>
                    </tr>

                </table>

                <!-- Bottom Text -->
                <p style="margin:20px 0 0; font-size:11px; color:#938A9C; text-align:center;">
                    © Zynvex Solutions. All rights reserved.
                </p>

            </td>
        </tr>
    </table>

</body>
</html>
"""

def clean_name(name):
    if not name:
        return ""
    name = str(name).strip()
    name = name.replace("\u00a0", " ")
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r'[/:\*?"<>|]', "", name)
    return name.title()

def get_pdf_for_candidate(temp_dir, full_name, internship_id):
    """
    Looks for a candidate's PDF offer letter inside the temp directory.
    Matches using name + ID digits or fallback to ID digits search.
    """
    if not os.path.exists(temp_dir):
        return None
        
    safe_name = "".join(c if c.isalnum() or c == " " else "_" for c in full_name).strip()
    id_num = internship_id.split("-")[-1]
    
    # Try exact match pattern
    exact_filename = f"{safe_name}_{id_num}_offer_letter.pdf"
    exact_path = os.path.join(temp_dir, exact_filename)
    if os.path.exists(exact_path):
        return exact_path
        
    # Search directory for file containing ID digits
    for file in os.listdir(temp_dir):
        if file.lower().endswith(".pdf") and id_num in file:
            return os.path.join(temp_dir, file)
            
    return None

def normalize_role(role):
    """Replace 'Developer' with 'Development' for consistency."""
    return role.replace("Developer", "Development").strip()

def clean_id(raw_id):
    """
    Extract the trailing numeric portion from an internship ID string.
    Examples:
      "ZYNVEX-FE-1042"  →  "1042"
      "CERT-00111"      →  "00111"
      "1042"            →  "1042"
    Returns empty string if no digits found.
    """
    raw_id = str(raw_id).strip()
    # Take the last segment when split by '-'
    parts = raw_id.split("-")
    num = parts[-1].strip()
    if num.isdigit() or (num and all(c.isdigit() for c in num)):
        return num
    # Fallback: grab all trailing digits from the full string
    m = re.search(r'(\d+)\s*$', raw_id)
    return m.group(1) if m else ""

def parse_pdf(filename):
    """
    Extract (name_part, id_num) from a generated offer-letter PDF filename.
    Expected pattern: <Name>_<digits>_offer_letter.pdf
    Examples:
      "Ahmed_Khan_1042_offer_letter.pdf"  →  ("Ahmed_Khan", "1042")
      "ZYNVEX-CERT-01111.pdf"             →  ("ZYNVEX-CERT-01111", "01111")
    Returns ("", "") if no numeric ID can be found.
    """
    base = os.path.splitext(filename)[0]
    # Look for the last run of digits in the filename
    m = re.search(r'(\d+)', base)
    if not m:
        return (base, "")
    id_num = m.group(1)
    return (base, id_num)

def send_smtp_email(smtp_config, to_email, subject, plain_body, html_body, attachment_path=None):
    """
    Sends a single email using the provided SMTP configurations.
    smtp_config: dict containing host, port, user, password
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_config["user"]
    msg["To"] = to_email

    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_data = f.read()
        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(attachment_path)
        )

    # Establish SMTP connection
    server = smtplib.SMTP(smtp_config["host"], int(smtp_config["port"]))
    server.starttls()
    server.login(smtp_config["user"], smtp_config["password"])
    server.send_message(msg)
    server.quit()

def send_bulk_offer_letters(smtp_config, candidates, temp_dir, templates=None, progress_callback=None):
    """
    Bulk email candidates their offer letters (attaches matching PDF).
    """
    if not templates:
        templates = {
            "subject": OFFER_LETTER_SUBJECT,
            "plain": OFFER_LETTER_PLAIN,
            "html": OFFER_LETTER_HTML
        }

    total = len(candidates)
    sent = 0
    failed = 0
    results = []

    for idx, candidate in enumerate(candidates, start=1):
        name = clean_name(candidate["full_name"])
        email = candidate["email"]
        role = candidate["internship_role"]
        id_ = candidate["internship_id"]

        pdf_path = get_pdf_for_candidate(temp_dir, name, id_)
        if not pdf_path:
            err_msg = f"PDF file not found in current session directory for ID {id_}"
            results.append({"name": name, "success": False, "email": email, "msg": err_msg})
            failed += 1
            if progress_callback:
                progress_callback(idx, total, name, False, err_msg)
            continue

        try:
            formatted_plain = templates["plain"].format(name=name)
            formatted_html = templates["html"].format(name=name)

            send_smtp_email(
                smtp_config=smtp_config,
                to_email=email,
                subject=templates["subject"],
                plain_body=formatted_plain,
                html_body=formatted_html,
                attachment_path=pdf_path
            )

            sent += 1
            results.append({"name": name, "success": True, "email": email, "msg": "Sent successfully"})
            if progress_callback:
                progress_callback(idx, total, name, True, None)

            # Introduce delay to prevent spam filters (similar to 10-12s in original script)
            if idx < total:
                time.sleep(random.randint(10, 12))

        except Exception as e:
            failed += 1
            err_str = str(e)
            results.append({"name": name, "success": False, "email": email, "msg": err_str})
            if progress_callback:
                progress_callback(idx, total, name, False, err_str)

    return sent, failed, results

def send_bulk_confirmations(smtp_config, candidates, whatsapp_links, templates=None, progress_callback=None):
    """
    Bulk email seat confirmations containing specific role WhatsApp group links.
    """
    if not templates:
        templates = {
            "subject": CONFIRM_EMAIL_SUBJECT,
            "plain": CONFIRM_EMAIL_PLAIN,
            "html": CONFIRM_EMAIL_HTML
        }

    total = len(candidates)
    sent = 0
    failed = 0
    results = []

    for idx, candidate in enumerate(candidates, start=1):
        name = clean_name(candidate["full_name"])
        email = candidate["email"]
        role = normalize_role(candidate["internship_role"])
        id_ = candidate["internship_id"]

        group_link = whatsapp_links.get(role)
        if not group_link:
            err_msg = f"WhatsApp group link not configured for role '{role}'"
            results.append({"name": name, "success": False, "email": email, "msg": err_msg})
            failed += 1
            if progress_callback:
                progress_callback(idx, total, name, False, err_msg)
            continue

        try:
            formatted_plain = templates["plain"].format(
                name=name,
                role=role,
                internship_id=id_,
                group_link=group_link
            )
            formatted_html = templates["html"].format(
                name=name,
                role=role,
                internship_id=id_,
                group_link=group_link
            )

            send_smtp_email(
                smtp_config=smtp_config,
                to_email=email,
                subject=templates["subject"],
                plain_body=formatted_plain,
                html_body=formatted_html
            )

            sent += 1
            results.append({"name": name, "success": True, "email": email, "msg": "Seat confirmed, group link sent"})
            if progress_callback:
                progress_callback(idx, total, name, True, None)

            # Introduce delay to prevent spam filters (similar to 10s in original script)
            if idx < total:
                time.sleep(10)

        except Exception as e:
            failed += 1
            err_str = str(e)
            results.append({"name": name, "success": False, "email": email, "msg": err_str})
            if progress_callback:
                progress_callback(idx, total, name, False, err_str)

    return sent, failed, results
