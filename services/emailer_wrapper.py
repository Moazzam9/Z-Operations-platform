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
Fee: PKR 300 (Pakistan) / USD 1.50 (International)

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
    <title>Internship Offer Letter</title>
</head>
<body style="margin:0; padding:0; background-color:#F7F4FC; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7F4FC; padding:40px 0;">
        <tr>
            <td align="center">
                <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                    <tr>
                        <td style="background-color:#7C6A9E; padding:32px 40px; border-radius:8px 8px 0 0;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="text-align:center;">
                                        <p style="margin:0; font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:0.5px;">Zynvex Solutions</p>
                                        <p style="margin:6px 0 0; font-size:15px; color:#E3D6F5; font-weight:400;">Internship Offer Letter</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:40px 40px 30px;">
                            <p style="margin:0 0 24px; font-size:17px; color:#2D2D2D; line-height:1.5;">
                                Dear <strong style="color:#5E4B7A;">{name}</strong>,
                            </p>
                            <p style="margin:0 0 20px; font-size:16px; color:#2D2D2D; line-height:1.6;">
                                <strong style="color:#5E4B7A;">Congratulations!</strong> We are pleased to inform you that you have been selected for the <strong>internship program</strong> at Zynvex Solutions. Your official Offer Letter is attached to this email.
                            </p>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7F4FC; border-left:4px solid #8E7CC3; margin:28px 0 28px;">
                                <tr>
                                    <td style="padding:20px 24px;">
                                        <p style="margin:0 0 6px; font-size:15px; color:#2D2D2D;"><strong>Internship Start Date:</strong> August 20th, 2026 </p>
                                        <p style="margin:0; font-size:15px; color:#2D2D2D;"><strong>Confirmation Deadline:</strong> Within 2 days of receiving your offer letter.</p>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin:0 0 28px; font-size:16px; color:#2D2D2D; line-height:1.6;">
                                To confirm your internship seat, please complete the registration form and submit the nominal registration fee before the deadline.
                            </p>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F2ECFA; border-radius:6px; margin-bottom:20px; border:1px solid #D5C9F0;">
                                <tr>
                                    <td style="padding:16px 24px;">
                                        <p style="margin:0; font-size:15px; color:#2D2D2D; line-height:1.5;">
                                            <strong style="color:#5E4B7A;">To submit your payment details</strong>, please click the <strong>&quot;Register Now&quot;</strong> button below and complete the registration form with the required information.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
                                <tr>
                                    <td align="center" style="background-color:#8E7CC3; border-radius:30px; padding:14px 36px;">
                                        <a href="https://forms.gle/t5rRd1ar6qiE43yz5" target="_blank" style="font-size:15px; font-weight:600; color:#FFFFFF; text-decoration:none; letter-spacing:0.3px; display:inline-block;">Register Now</a>
                                    </td>
                                </tr>
                            </table>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7F4FC; border-radius:6px; margin-bottom:28px;">
                                <tr>
                                    <td style="padding:18px 24px;">
                                        <p style="margin:0 0 8px; font-size:15px; color:#2D2D2D;"><strong>Registration Fee</strong></p>
                                        <p style="margin:0 0 4px; font-size:14px; color:#2D2D2D;"><strong>PKR 300</strong> (Pakistan)</p>
                                        <p style="margin:0; font-size:14px; color:#2D2D2D;"><strong>USD 1.50</strong> (International)</p>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin:0 0 20px; font-size:14px; color:#2D2D2D; line-height:1.6;">
                                <strong style="color:#5E4B7A;">Why a registration fee?</strong><br>
                                When we launched this internship program, the opportunity was offered completely free of charge. However, due to a lack of serious participation from several candidates in the free batch, we have introduced a nominal registration fee.<br><br>
                                This fee is applicable only after you have been shortlisted and received your official offer letter. Its purpose is to ensure that only committed and serious candidates confirm their participation in the program.<br><br>
                                There are absolutely no charges for the internship certificate, and there are no hidden fees or additional costs of any kind.
                            </p>
                            <p style="margin:0 0 30px; font-size:14px; color:#B73A3A; line-height:1.6;">
                                <strong>Important:</strong> This registration link is strictly for selected interns and must not be shared.
                            </p>
                            <hr style="border:none; border-top:1px solid #D5C9F0; margin:0 0 28px;">
                            <p style="margin:0 0 16px; font-size:14px; color:#2D2D2D; line-height:1.6;">
                                <strong style="color:#5E4B7A;">A note on future opportunities:</strong><br>
                                Consistent, dedicated, and hardworking candidates may be considered for specific roles within Zynvex Solutions based on their performance and chosen domain. We look forward to seeing what you are capable of!
                            </p>
                            <p style="margin:0; font-size:14px; color:#2D2D2D; line-height:1.6;">
                                Stay committed, give your best, and use this internship to demonstrate your skills and professionalism.
                            </p>
                            <hr style="border: 0; border-top: 2px solid #008000; margin: 15px 0;">
                            <p style="color: #008000; font-size:14px; line-height:1.6;">
                              The email you received was sent from the company’s official working email address. If you found it in your <strong>Spam or Junk folder</strong>, this does not mean the email is suspicious or unauthorized. The most likely reason is that we sent the same official communication to <strong>multiple candidates simultaneously</strong>, which can sometimes cause email providers to automatically filter the message into Spam or Junk.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color:#F7F4FC; padding:24px 40px; border-top:1px solid #D5C9F0; border-radius:0 0 8px 8px; text-align:center;">
                            <p style="margin:0 0 4px; font-size:15px; color:#5E4B7A; font-weight:600;">Best regards,</p>
                            <p style="margin:0; font-size:17px; color:#2D2D2D; font-weight:700;">Zynvex Solutions</p>
                        </td>
                    </tr>
                </table>
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

Important Update: The internship start date has been changed from 20 August to 19 August.

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
    <title>Internship Confirmation</title>
</head>
<body style="margin:0; padding:0; background-color:#F7F4FC; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7F4FC; padding:40px 0;">
        <tr>
            <td align="center">
                <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                    <tr>
                        <td style="background-color:#7C6A9E; padding:32px 40px; border-radius:8px 8px 0 0; text-align:center;">
                            <p style="margin:0; font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:0.5px;">Zynvex Solutions</p>
                            <p style="margin:6px 0 0; font-size:15px; color:#E3D6F5; font-weight:400;">Internship Confirmation</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:40px 40px 30px;">
                            <p style="margin:0 0 24px; font-size:17px; color:#2D2D2D; line-height:1.5;">
                                Hello <strong style="color:#5E4B7A;">{name}</strong>,
                            </p>
                            <p style="margin:0 0 20px; font-size:16px; color:#2D2D2D; line-height:1.6;">
                                <strong style="color:#5E4B7A;">Congratulations!</strong> Your payment has been confirmed. You have been selected for the <strong>{role}</strong> internship program.
                            </p>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FDF0E8; border-left:4px solid #E67E22; margin:0 0 28px;">
                                <tr>
                                    <td style="padding:20px 24px;">
                                        <p style="margin:0; font-size:15px; color:#2D2D2D;"><strong>Important Update:</strong> The internship start date has been changed from 20 August to 19 August.</p>
                                    </td>
                                </tr>
                            </table>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7F4FC; border-left:4px solid #8E7CC3; margin:28px 0 28px;">
                                <tr>
                                    <td style="padding:20px 24px;">
                                        <p style="margin:0; font-size:15px; color:#2D2D2D;"><strong>Your Internship ID:</strong> {internship_id}</p>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin:0 0 20px; font-size:16px; color:#2D2D2D; line-height:1.6;">
                                Please join your dedicated internship group using the button below:
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
                                <tr>
                                    <td align="center" style="background-color:#8E7CC3; border-radius:30px; padding:14px 36px;">
                                        <a href="{group_link}" target="_blank" style="font-size:15px; font-weight:600; color:#FFFFFF; text-decoration:none; letter-spacing:0.3px; display:inline-block;">Join WhatsApp Group</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin:0 0 30px; font-size:14px; color:#2D2D2D; line-height:1.6;">
                                You will receive further instructions and updates through this group.
                            </p>
                            <hr style="border:none; border-top:1px solid #D5C9F0; margin:0 0 28px;">
                            <p style="margin:0; font-size:14px; color:#2D2D2D; line-height:1.6;">
                                Stay committed and give your best. We look forward to seeing your contributions.
                            </p>
                            <p style="color: #008000; font-size:14px; line-height:1.6;">
                              The email you received was sent from the company's official working email address. If you found it in your <strong>Spam or Junk folder</strong>, this does not mean the email is suspicious or unauthorized. The most likely reason is that we sent the same official communication to <strong>multiple candidates simultaneously</strong>, which can sometimes cause email providers to automatically filter the message into Spam or Junk.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color:#F7F4FC; padding:24px 40px; border-top:1px solid #D5C9F0; border-radius:0 0 8px 8px; text-align:center;">
                            <p style="margin:0 0 4px; font-size:15px; color:#5E4B7A; font-weight:600;">Best regards,</p>
                            <p style="margin:0; font-size:17px; color:#2D2D2D; font-weight:700;">ZYNVEX Team</p>
                        </td>
                    </tr>
                </table>
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
