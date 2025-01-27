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

def has_30plus_dpd(loan):
    """Check if a loan has any instance of 30+ DPD"""
    dpd_months = []
    for payment in loan['payment_history']:
        dpd = parse_dpd_code(payment['status'])
        if dpd >= 30:
            dpd_months.append({
                'date': payment['date'],
                'dpd': dpd
            })
    return dpd_months

def analyze_customer_dpd(data):
    """Analyze DPD statistics for a customer"""
    total_trades = len(data['loans'])
    loan_details = []
    
    for loan in data['loans']:
        dpd_months = has_30plus_dpd(loan)
        loan_details.append({
            'type': loan['account_type'],
            'status': loan['status'],
            'dpd_months': dpd_months,
            'has_30plus_dpd': len(dpd_months) > 0
        })
    
    trades_with_30plus_dpd = sum(1 for loan in loan_details if loan['has_30plus_dpd'])
    percentage = (trades_with_30plus_dpd / total_trades * 100) if total_trades > 0 else 0
    
    return {
        'total_trades': total_trades,
        'trades_with_30plus_dpd': trades_with_30plus_dpd,
        'percentage': round(percentage, 2),
        'loan_details': loan_details
    }

def write_to_csv(results, output_dir):
    """Write results to CSV files"""
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Write summary CSV
    summary_file = output_dir / 'dpd_summary.csv'
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Customer ID', 'Total Trades', '30+ DPD Trades', 'Percentage'])
        
        for result in results:
            stats = result['stats']
            writer.writerow([
                result['customer_id'],
                stats['total_trades'],
                stats['trades_with_30plus_dpd'],
                f"{stats['percentage']}%"
            ])
    
    # Write detailed breakdown CSV
    details_file = output_dir / 'dpd_details.csv'
    with open(details_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Customer ID', 'Loan Type', 'Loan Status', 'Has 30+ DPD', 'DPD Months'])
        
        for result in results:
            customer_id = result['customer_id']
            for loan in result['stats']['loan_details']:
                dpd_months_str = '; '.join([
                    f"{month['date']}: {month['dpd']} days" 
                    for month in loan['dpd_months']
                ]) if loan['dpd_months'] else 'None'
                
                writer.writerow([
                    customer_id,
                    loan['type'],
                    loan['status'],
                    'Yes' if loan['has_30plus_dpd'] else 'No',
                    dpd_months_str
                ])
    
    # Write overall statistics CSV
    stats_file = output_dir / 'dpd_overall_stats.csv'
    with open(stats_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        
        total_all_trades = sum(r['stats']['total_trades'] for r in results)
        total_30plus_trades = sum(r['stats']['trades_with_30plus_dpd'] for r in results)
        overall_percentage = (total_30plus_trades / total_all_trades * 100) if total_all_trades > 0 else 0
        
        writer.writerow(['Total Trades', total_all_trades])
        writer.writerow(['Trades with 30+ DPD', total_30plus_trades])
        writer.writerow(['Overall Percentage', f"{round(overall_percentage, 2)}%"])

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
            
            # Analyze DPD statistics
            stats = analyze_customer_dpd(data)
            
            results.append({
                'customer_id': customer_id,
                'stats': stats
            })
            
        except Exception as e:
            print(f"Error processing {report_file}: {str(e)}")
    
    # Write results to CSV files
    write_to_csv(results, 'dpd_analysis')
    
    print("\nAnalysis complete! Results have been written to:")
    print("1. dpd_summary.csv - Summary for each customer")
    print("2. dpd_details.csv - Detailed breakdown of all loans")
    print("3. dpd_overall_stats.csv - Overall statistics")

if __name__ == "__main__":
    main() 