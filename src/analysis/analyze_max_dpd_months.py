from pathlib import Path
import json
import csv

def parse_dpd_code(status):
    """Convert status codes to DPD values"""
    dpd_mapping = {
        'XXX': '000',
        'STD': '000',
        'SUB': '091',
        'DBT': '151',
        'LSS': '181',
        'SMA': '061',
        'DDD': '000'
    }
    
    # Split into DPD value and status code
    dpd, code = status.split('/')
    
    # If DPD is a code, map it; otherwise use the numeric value
    if dpd in dpd_mapping:
        return int(dpd_mapping[dpd])
    return int(dpd)

def count_30plus_dpd_months(loan):
    """Count number of months with 30+ DPD for a single loan"""
    count = 0
    dpd_months = []
    
    for payment in loan['payment_history']:
        dpd = parse_dpd_code(payment['status'])
        if dpd >= 30:
            count += 1
            dpd_months.append({
                'date': payment['date'],
                'dpd': dpd
            })
    
    return {
        'count': count,
        'dpd_months': dpd_months
    }

def analyze_customer_max_dpd_months(data):
    """Find the maximum number of 30+ DPD months among all trades for a customer"""
    max_dpd_months = 0
    loan_dpd_counts = []
    
    for loan in data['loans']:
        dpd_info = count_30plus_dpd_months(loan)
        loan_dpd_counts.append({
            'type': loan['account_type'],
            'disbursed_date': loan['disbursed_date'],
            'dpd_count': dpd_info['count'],
            'dpd_months': dpd_info['dpd_months']
        })
        
        max_dpd_months = max(max_dpd_months, dpd_info['count'])
    
    return {
        'max_dpd_months': max_dpd_months,
        'loan_details': loan_dpd_counts
    }

def write_to_csv(results, output_dir):
    """Write results to CSV files"""
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Write summary CSV
    summary_file = output_dir / 'max_dpd_summary.csv'
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Customer ID', 'Maximum 30+ DPD Months'])
        
        for result in results:
            writer.writerow([
                result['customer_id'],
                result['stats']['max_dpd_months']
            ])
    
    # Write detailed breakdown CSV
    details_file = output_dir / 'max_dpd_details.csv'
    with open(details_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Customer ID', 'Loan Type', 'Disbursed Date', 'Number of 30+ DPD Months', 'DPD Details'])
        
        for result in results:
            customer_id = result['customer_id']
            for loan in result['stats']['loan_details']:
                if loan['dpd_count'] > 0:
                    dpd_details = '; '.join([
                        f"{month['date']}: {month['dpd']} days" 
                        for month in loan['dpd_months']
                    ])
                    
                    writer.writerow([
                        customer_id,
                        loan['type'],
                        loan['disbursed_date'],
                        loan['dpd_count'],
                        dpd_details
                    ])
    
    # Write overall statistics CSV
    stats_file = output_dir / 'max_dpd_overall_stats.csv'
    with open(stats_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        
        overall_max = max(r['stats']['max_dpd_months'] for r in results)
        max_dpd_customers = [r['customer_id'] for r in results 
                           if r['stats']['max_dpd_months'] == overall_max]
        
        writer.writerow(['Overall Maximum 30+ DPD Months', overall_max])
        writer.writerow(['Customers with Maximum DPD', ', '.join(max_dpd_customers)])
        writer.writerow(['Total Customers Analyzed', len(results)])

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
            
            # Analyze max DPD months
            stats = analyze_customer_max_dpd_months(data)
            
            results.append({
                'customer_id': customer_id,
                'stats': stats
            })
            
        except Exception as e:
            print(f"Error processing {report_file}: {str(e)}")
    
    # Write results to CSV files
    write_to_csv(results, 'max_dpd_analysis')
    
    print("\nAnalysis complete! Results have been written to:")
    print("1. max_dpd_summary.csv - Summary for each customer")
    print("2. max_dpd_details.csv - Detailed breakdown of loans with 30+ DPD")
    print("3. max_dpd_overall_stats.csv - Overall statistics")

if __name__ == "__main__":
    main() 