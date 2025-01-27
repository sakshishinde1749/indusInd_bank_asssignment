from pathlib import Path
import logging
from datetime import datetime
import json
from src.cleaning.format_reports import clean_credit_reports
from src.analysis.analyze_dpd import analyze_customer_dpd, write_to_csv as write_dpd_csv
from src.analysis.analyze_disbursed_amount import analyze_customer_disbursements, write_to_csv as write_disbursement_csv
from src.analysis.analyze_max_dpd_months import analyze_customer_max_dpd_months, write_to_csv as write_max_dpd_csv

def setup_logging():
    """Configure logging with timestamp and proper formatting"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f'analysis_{timestamp}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def setup_directory_structure():
    """Create necessary directories for the analysis pipeline"""
    directories = {
        'xml': Path('data/raw_files/xml'),
        'interim': Path('data/interim'),
        'results': Path('data/results')
    }
    
    # Create directories if they don't exist
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return directories


def run_analysis(formatted_reports, results_dir, logger):
    """Run various analyses on the formatted reports"""
    analyses = {
        'dpd': {
            'analyze': analyze_customer_dpd,
            'write': write_dpd_csv
        },
        'max_dpd_months': {
            'analyze': analyze_customer_max_dpd_months,
            'write': write_max_dpd_csv
        },
        'disbursements': {
            'analyze': analyze_customer_disbursements,
            'write': write_disbursement_csv
        }
    }
    
    for analysis_name, analysis_funcs in analyses.items():
        try:
            results = []
            for report_file in formatted_reports:
                try:
                    # Extract customer ID from filename
                    customer_id = report_file.name.split('_')[1].split('.')[0]
                    
                    # Read the formatted report
                    with open(report_file, 'r') as f:
                        data = json.load(f)
                    
                    # Analyze the report
                    stats = analysis_funcs['analyze'](data)
                    
                    results.append({
                        'customer_id': customer_id,
                        'stats': stats
                    })
                    
                    logger.info(f"Analyzed {report_file.name} successfully")
                    
                except Exception as e:
                    logger.error(f"Error analyzing {report_file}: {str(e)}")
            
            # Write results
            output_dir = Path(results_dir) / f"{analysis_name}_analysis"
            analysis_funcs['write'](results, output_dir)
            
        except Exception as e:
            logger.error(f"Error in {analysis_name} analysis: {str(e)}")

def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting analysis pipeline...")
    
    try:
        # Setup directory structure
        dirs = setup_directory_structure()
        logger.info("Directory structure created successfully")
        
        # Format raw reports (combines XML conversion and formatting)
        formatted_reports = clean_credit_reports(
            input_dir=dirs['xml'],
            output_dir=dirs['interim']
        )
        logger.info(f"Formatted {len(formatted_reports)} reports successfully")
        
        # Run analysis
        run_analysis(formatted_reports, dirs['results'], logger)
        logger.info("Analysis completed successfully")
        
        print("\nAnalysis pipeline completed! Results can be found in:")
        print(f"1. Interim data: {dirs['interim']}")
        print(f"2. Analysis results: {dirs['results']}")
        print(f"3. Logs: logs/")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
