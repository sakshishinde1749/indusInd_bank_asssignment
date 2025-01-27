import xml.etree.ElementTree as ET
import json
from pathlib import Path

def xml_to_dict(element):
    """Convert XML to dictionary."""
    result = {}
    
    # Handle attributes if present
    if element.attrib:
        result.update(element.attrib)
    
    # Handle child elements
    for child in element:
        child_data = xml_to_dict(child)
        
        # Handle case where tag already exists
        if child.tag in result:
            # If it's not already a list, convert to list
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data
    
    # Handle text content
    if element.text and element.text.strip():
        if not result:  # If no children or attributes
            return element.text.strip()
        else:
            result['text'] = element.text.strip()
    
    return result

def parse_payment_history(history_str):
    """Parse the combined payment history string into a list of monthly records"""
    if not history_str:
        return []
    
    entries = history_str.split("|")
    parsed = []
    
    for entry in entries:
        if not entry.strip():
            continue
        try:
            date, status = entry.split(",")
            parsed.append({
                "date": date,
                "status": status
            })
        except ValueError:
            continue
            
    return parsed

def format_loan_details(loan):
    """Format a single loan's details into a readable structure"""
    loan_details = loan.get("LOAN-DETAILS", {})
    
    formatted = {
        "account_type": loan_details.get("ACCT-TYPE"),
        "status": loan_details.get("ACCOUNT-STATUS"),
        "amount": loan_details.get("DISBURSED-AMT"),
        "current_balance": loan_details.get("CURRENT-BAL"),
        "disbursed_date": loan_details.get("DISBURSED-DATE"),
        "closed_date": loan_details.get("CLOSED-DATE"),
        "security_status": loan_details.get("SECURITY-STATUS"),
        "payment_history": parse_payment_history(loan_details.get("COMBINED-PAYMENT-HISTORY", ""))
    }
    
    return formatted

def analyze_credit_report(xml_data):
    """Convert XML to JSON and analyze the credit report in one step"""
    # Convert XML to dictionary
    data = xml_to_dict(xml_data)
    
    report = data.get("INDV-REPORTS", {}).get("INDV-REPORT", {})
    
    # Basic information
    header = report.get("HEADER", {})
    score = report.get("SCORES", {}).get("SCORE", {})
    
    # Account summaries
    accounts = report.get("ACCOUNTS-SUMMARY", {})
    derived = accounts.get("DERIVED-ATTRIBUTES", {})
    primary = accounts.get("PRIMARY-ACCOUNTS-SUMMARY", {})
    
    analysis = {
        "report_date": header.get("DATE-OF-ISSUE"),
        "credit_score": {
            "value": score.get("SCORE-VALUE"),
            "type": score.get("SCORE-TYPE"),
            "comments": score.get("SCORE-COMMENTS")
        },
        "summary": {
            "total_accounts": primary.get("PRIMARY-NUMBER-OF-ACCOUNTS"),
            "active_accounts": primary.get("PRIMARY-ACTIVE-NUMBER-OF-ACCOUNTS"),
            "overdue_accounts": primary.get("PRIMARY-OVERDUE-NUMBER-OF-ACCOUNTS"),
            "total_balance": primary.get("PRIMARY-CURRENT-BALANCE"),
            "credit_history_years": derived.get("LENGTH-OF-CREDIT-HISTORY-YEAR"),
            "recent_inquiries": derived.get("INQUIRIES-IN-LAST-SIX-MONTHS")
        },
        "loans": []
    }
    
    # Process each loan
    responses = report.get("RESPONSES", {}).get("RESPONSE", [])
    if not isinstance(responses, list):
        responses = [responses]
        
    for response in responses:
        formatted_loan = format_loan_details(response)
        analysis["loans"].append(formatted_loan)
    
    return analysis

def process_credit_report(xml_file, output_dir):
    """Process a single credit report from XML to formatted JSON"""
    try:
        # Parse XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Analyze the report directly from XML
        analysis = analyze_credit_report(root)
        
        # Create output filename
        output_file = output_dir / f"formatted_{xml_file.stem}.json"
        
        # Write formatted output
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Print key insights
        print(f"\nCredit Report Summary for {xml_file.name}:")
        print("-" * 50)
        print(f"Report Date: {analysis['report_date']}")
        print(f"Credit Score: {analysis['credit_score']['value']} ({analysis['credit_score']['comments']})")
        print(f"Total Accounts: {analysis['summary']['total_accounts']}")
        print(f"Active Accounts: {analysis['summary']['active_accounts']}")
        print(f"Credit History: {analysis['summary']['credit_history_years']} years")
        print(f"Recent Inquiries: {analysis['summary']['recent_inquiries']}")
        print(f"Current Total Balance: ₹{analysis['summary']['total_balance']}")
        print()
        
        return output_file
        
    except Exception as e:
        print(f"Error processing {xml_file}: {str(e)}")
        return None

def clean_credit_reports(input_dir='data/raw_files/xml', output_dir='data/interim'):
    """Process all credit reports in the input directory"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    processed_files = []
    
    for xml_file in input_dir.glob('*.xml'):
        output_file = process_credit_report(xml_file, output_dir)
        if output_file:
            processed_files.append(output_file)
    
    return processed_files

if __name__ == "__main__":
    processed_files = clean_credit_reports()
    print(f"\nProcessed {len(processed_files)} files successfully") 