import os
import streamlit as st
import PyPDF2
from groq import Groq
import requests
import smtplib


client = Groq(api_key="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")



def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    for page_text in reader.pages:
        yield page_text.extract_text()

def split_text_into_chunks(text, chunk_size=2000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def process_with_groq(text_chunks, task_type):
    results = []
    for chunk in text_chunks:
        prompt = f"Task: {task_type}\n\nDocument:\n{chunk}\n\nOutput:"
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            if hasattr(response, "choices") and response.choices:
                results.append(response.choices[0].message.content)
            else:
                results.append("No response received from the model.")
        except Exception as e:
            results.append(f"Error: {str(e)}")
    return " ".join(results)



RISK_KEYWORDS = [
    "penalty", "breach", "liability", "default", "hidden obligations",
    "indemnity", "terms of service", "non-compliance", "force majeure"
]

REGULATORY_UPDATES = [
    {"name": "GDPR", "last_updated": "2023-12-01", "description": "General Data Protection Regulation updates on user consent."},
   
]
#  detecting risk 

RISK_KEYWORDS = [
    "penalty", "breach", "liability", "default", "hidden obligations",
    "indemnity", "terms of service", "non-compliance", "force majeure"
]
def detect_risks(text_chunks):
    """
    Detects potential risks based on predefined keywords in a list of text chunks.

    Parameters:
        text_chunks (list): List of text chunks to analyze.

    Returns:
        list: List of detected risks with contextual information.
    """
    if not text_chunks:
        print("No text chunks provided for risk detection.")
        return []

    risks_found = []
    for chunk_index, chunk in enumerate(text_chunks):
        if not chunk.strip():
            continue 

        print(f"Analyzing chunk {chunk_index + 1}/{len(text_chunks)}: {chunk[:100]}...")  # Debugging info
        for keyword in RISK_KEYWORDS:
            if keyword.lower() in chunk.lower():
                risks_found.append(f"Risk detected: '{keyword}' in text: {chunk[:150]}...")
                print(f"--> Risk detected: '{keyword}' in chunk {chunk_index + 1}")  # Debugging info

    if not risks_found:
        print("No risks detected.")
    else:
        print(f"{len(risks_found)} risks detected.")

    return risks_found


#  REGULATORY_UPDATES

REGULATORY_UPDATES = [
    {"name": "GDPR", "last_updated": "2023-12-01", "description": "General Data Protection Regulation updates on user consent."},

]
REGULATORY_UPDATES = [
    {
        'name': 'GDPR Compliance',
        'description': 'General Data Protection Regulation compliance requirements.',
        'last_updated': '2024-01-01',
        'status': 'Pending'
    },
    {
        'name': 'PCI DSS',
        'description': 'Payment Card Industry Data Security Standard compliance.',
        'last_updated': '2023-11-01',
        'status': 'Completed'
    }
    
]

def check_regulatory_compliance(text_chunks):
    compliance_issues = []
    for chunk in text_chunks:
        for update in REGULATORY_UPDATES:
            if update['name'].lower() in chunk.lower():
                # Adding regulatory update status and last updated date
                compliance_issues.append(
                    f"Regulatory Update Detected: {update['name']} - {update['description']}\n"
                    f"Status: {update['status']} | Last Updated: {update['last_updated']}"
                )
    return compliance_issues

text_chunks = [
    "We need to review GDPR Compliance for the upcoming year.",
    "The new PCI DSS standards have been implemented."
]

compliance_issues = check_regulatory_compliance(text_chunks)
for issue in compliance_issues:
    print(issue)

st.title("📜 Legal Document Assistant with Risk Detection & Regulatory Update Tracker")
st.markdown("""
**Welcome to the Enhanced Legal Document Assistant!**  
- 📑 Extract key clauses from legal documents  
- 📜 Provide readable legal summaries  
- ⚖️ Detect potential legal risks  
- 📰 Track regulatory updates  
- ✉️ Send summaries directly via email  
""")

st.sidebar.title("Options")
uploaded_files = st.sidebar.file_uploader(
    "Upload PDFs or Text Files", type=["pdf", "txt"], accept_multiple_files=True
)
tasks = st.sidebar.multiselect(
    "Choose Tasks", ["Extract Clauses", "Summarize", "Risk Detection", "Regulatory Update Tracker"]
)

# Initialize an empty dictionary to store generated summaries
generated_summaries = {}

def process_file(file, selected_tasks):
    if file.type == "application/pdf":
        text_chunks = []
        for page_text in extract_text_from_pdf(file):
            text_chunks.extend(split_text_into_chunks(page_text))
    else:
        text = file.read().decode("utf-8")
        text_chunks = split_text_into_chunks(text)

    task_results = {}
    for task in selected_tasks:
        if task == "Risk Detection":
            task_results[task] = detect_risks(text_chunks)
        elif task == "Regulatory Update Tracker":
            task_results[task] = check_regulatory_compliance(text_chunks)
        else:
            task_results[task] = process_with_groq(text_chunks, task)
        
        # Save summaries to the generated_summaries dictionary
        generated_summaries[file.name] = task_results
    return task_results

if uploaded_files and tasks:
    st.write("🔄 Processing documents... Please wait.")
    combined_results = {}

    for file in uploaded_files:
        st.write(f"Processing: {file.name}")
        combined_results[file.name] = process_file(file, tasks)

    st.success("🎉 All tasks completed!")

    # Display results and allow downloading
    for file_name, results in combined_results.items():
        st.subheader(f"Results for {file_name}:")
        for task, result in results.items():
            st.text_area(f"Task: {task}", result, height=300)
            st.download_button(
                label=f"📥 Download {task} Result for {file_name}",
                data="\n".join(result),
                file_name=f"{file_name}_{task}_result.txt",
                mime="text/plain",
            )

#Email-sending section with PDF generation
    st.markdown("## ✉️ Send Summary via Email")
with st.form(key="email_form"):
    task_to_send = st.selectbox(
        "Select a task summary to send:", 
        [f"{file_name} - {task}" for file_name, results in generated_summaries.items() for task in results.keys()]
    )
    receiver_email = st.text_input("Enter receiver email:")
    email_subject = st.text_input("Enter email subject:", value="Legal Document Summary")
    sender_email = st.text_input("Sender email (Gmail):", value="your_email@gmail.com")
    sender_password = st.text_input("Sender email password:", type="password")
    submit_email = st.form_submit_button("Send Email")

    if submit_email:
        selected_file, selected_task = task_to_send.split(" - ")
        email_body = generated_summaries[selected_file][selected_task] 
        pdf_filename = f"{selected_file}_{selected_task}.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, email_body)  
        pdf.output(pdf_filename)

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()  
            server.login(sender_email, sender_password) 
            
            message = f"""From: {sender_email}
To: {receiver_email}
Subject: {email_subject}\n
Please find the attached PDF summary for your review.
"""
            
           
            with open(pdf_filename, "rb") as pdf_file:
                attachment = pdf_file.read()

            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders

            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = email_subject

        
            msg.attach(MIMEText(message, 'plain'))

           
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={pdf_filename}",
            )
            msg.attach(part)

            server.send_message(msg)
            server.quit()  
            
            os.remove(pdf_filename)

            st.success("📧 Email sent successfully with the attached PDF!")
        except Exception as e:
            st.error(f"Failed to send email: {str(e)}")
def answer_question_with_summary(summary, question):
    """
    Generate an answer to a user's question based on the provided summary.

    Parameters:
        summary (str): The summary used as context.
        question (str): The user's question.

    Returns:
        str: The generated answer.
    """
    prompt = f"Context:\n{summary}\n\nQuestion: {question}\n\nAnswer:"
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "No response received from the model."
    except Exception as e:
        return f"Error: {str(e)}"
if "Summarize" in tasks:
    st.markdown("## ❓ Ask Questions Based on the Summary")
    selected_file_summary = st.selectbox(
        "Select a file summary to ask questions about:",
        [file_name for file_name in generated_summaries.keys()]
    )
    user_question = st.text_input("Ask a question about the selected summary:")
    if st.button("Get Answer"):
        if user_question and selected_file_summary:
            summary = generated_summaries[selected_file_summary].get("Summarize", "")
            if summary:
                answer = answer_question_with_summary(summary, user_question)
                st.markdown(f"**Answer:** {answer}")
            else:
                st.error("No summary available for the selected file.")
        else:
            st.error("Please select a file summary and enter a question.")
