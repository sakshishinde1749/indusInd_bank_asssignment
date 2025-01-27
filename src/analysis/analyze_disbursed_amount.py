from pathlib import Path
import json
import csv

def parse_amount(amount_str):
    """Convert amount string to numeric value"""
    if not amount_str:
        return 0
    
    # Remove commas and currency symbols, convert to float
    cleaned = amount_str.replace(',', '').replace('₹', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0

def analyze_customer_disbursements(data):
    """Calculate total disbursed amount for a customer"""
    total_amount = 0
    loan_details = []
    
    for loan in data['loans']:
        amount = parse_amount(loan['amount'])
        total_amount += amount
        
        # Store individual loan details for breakdown
        loan_details.append({
            'type': loan['account_type'],
            'amount': amount,
            'date': loan['disbursed_date'],
            'status': loan['status']
        })
    
    return {
        'total_disbursed': total_amount,
        'loan_count': len(loan_details),
        'loan_details': loan_details
    }

def format_amount(amount):
    """Format amount with commas and currency symbol"""
    return f"₹{amount:,.2f}"

def write_to_csv(results, output_dir):
    """Write results to CSV files"""
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Write summary CSV
    summary_file = output_dir / 'disbursement_summary.csv'
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Customer ID', 'Total Disbursed', 'Number of Loans', 'Average per Loan'])
        
        for result in results:
            stats = result['stats']
            total = stats['total_disbursed']
            loan_count = stats['loan_count']
            avg_per_loan = total / loan_count if loan_count > 0 else 0
            
            writer.writerow([
                result['customer_id'],
                format_amount(total),
                loan_count,
                format_amount(avg_per_loan)
            ])
    
    # Write detailed breakdown CSV
    details_file = output_dir / 'disbursement_details.csv'
    with open(details_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Customer ID', 'Loan Type', 'Amount', 'Date', 'Status'])
        
        for result in results:
            customer_id = result['customer_id']
            for loan in result['stats']['loan_details']:
                writer.writerow([
                    customer_id,
                    loan['type'],
                    format_amount(loan['amount']),
                    loan['date'],
                    loan['status']
                ])
    
    # Write overall statistics CSV
    stats_file = output_dir / 'disbursement_overall_stats.csv'
    with open(stats_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        
        grand_total = sum(r['stats']['total_disbursed'] for r in results)
        total_loans = sum(r['stats']['loan_count'] for r in results)
        avg_total = grand_total / len(results) if results else 0
        avg_loans = total_loans / len(results) if results else 0
        
        writer.writerow(['Total Disbursed Across All Customers', format_amount(grand_total)])
        writer.writerow(['Average Disbursed per Customer', format_amount(avg_total)])
        writer.writerow(['Average Number of Loans per Customer', f"{avg_loans:.2f}"])

def main():
    # Process all formatted reports
    reports_dir = Path('formatted_reports')
    results = []
    
    for report_file in reports_dir.glob('formatted_*.json'):
        try:
            # Extract customer ID from filename
            customer_id = report_file.name.split('_')[1].split('.')[0]
            
            # Read the formatted report
            with open(report_file, 'r') as f:
                data = json.load(f)
            
            # Analyze disbursement statistics
            stats = analyze_customer_disbursements(data)
            
            results.append({
                'customer_id': customer_id,
                'stats': stats
            })
            
        except Exception as e:
            print(f"Error processing {report_file}: {str(e)}")
    
    # Write results to CSV files
    write_to_csv(results, 'disbursement_analysis')
    
    print("\nAnalysis complete! Results have been written to:")
    print("1. disbursement_summary.csv - Summary for each customer")
    print("2. disbursement_details.csv - Detailed breakdown of all loans")
    print("3. disbursement_overall_stats.csv - Overall statistics")

if __name__ == "__main__":
    main() 