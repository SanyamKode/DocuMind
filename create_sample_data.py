# create_sample_data.py
import pandas as pd
from datetime import datetime, timedelta
import random

def create_sample_financial_data():
    """Create a comprehensive financial Excel file for testing"""
    
    # 1. Supplier Payments Sheet
    suppliers = ['ABC Corp', 'XYZ Ltd', 'Global Supplies Inc', 'Tech Solutions', 'Office Depot', 
                 'Marketing Pro', 'Cloud Services Ltd', 'Hardware Direct', 'Consulting Group', 'Legal Associates']
    payment_data = []
    
    for i in range(100):
        supplier = random.choice(suppliers)
        amount = round(random.uniform(1000, 75000), 2)
        due_date = datetime.now() - timedelta(days=random.randint(0, 120))
        paid_date = due_date + timedelta(days=random.randint(-5, 45))
        days_delayed = (paid_date - due_date).days
        
        payment_data.append({
            'Supplier': supplier,
            'Invoice Number': f'INV-2024-{i+1000}',
            'Amount': amount,
            'Due Date': due_date.strftime('%Y-%m-%d'),
            'Paid Date': paid_date.strftime('%Y-%m-%d'),
            'Days Delayed': max(0, days_delayed),
            'Status': 'Overdue' if days_delayed > 30 else 'On Time',
            'Payment Method': random.choice(['Bank Transfer', 'Check', 'Credit Card', 'ACH']),
            'Department': random.choice(['Operations', 'Marketing', 'IT', 'HR', 'Finance'])
        })
    
    # 2. Quarterly Financial Summary
    financial_summary = {
        'Quarter': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
        'Revenue': [1250000, 1380000, 1420000, 1550000],
        'Cost of Goods Sold': [500000, 552000, 568000, 620000],
        'Gross Profit': [750000, 828000, 852000, 930000],
        'Operating Expenses': [480000, 498000, 532000, 560000],
        'Net Profit': [270000, 330000, 320000, 370000],
        'Profit Margin %': [21.6, 23.9, 22.5, 23.9],
        'Customer Count': [245, 267, 289, 312],
        'Average Deal Size': [5102, 5169, 4913, 4968]
    }
    
    # 3. Monthly Revenue Breakdown
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    revenue_breakdown = {
        'Month': months,
        'Product Sales': [380000, 395000, 415000, 420000, 435000, 445000, 
                         450000, 465000, 470000, 480000, 495000, 510000],
        'Service Revenue': [120000, 125000, 130000, 135000, 140000, 145000,
                           150000, 155000, 160000, 165000, 170000, 175000],
        'Subscription Revenue': [80000, 82000, 84000, 86000, 88000, 90000,
                                92000, 94000, 96000, 98000, 100000, 102000],
        'Total Revenue': [580000, 602000, 629000, 641000, 663000, 680000,
                         692000, 714000, 726000, 743000, 765000, 787000]
    }
    
    # 4. Expense Categories
    expense_categories = {
        'Category': ['Salaries & Benefits', 'Rent & Utilities', 'Marketing & Advertising', 
                    'R&D', 'Operations', 'Professional Services', 'Travel & Entertainment',
                    'Office Supplies', 'Insurance', 'Other'],
        'Q1': [450000, 65000, 85000, 120000, 100000, 45000, 25000, 15000, 35000, 40000],
        'Q2': [480000, 68000, 95000, 140000, 110000, 48000, 28000, 17000, 35000, 29000],
        'Q3': [500000, 70000, 100000, 150000, 115000, 52000, 30000, 18000, 35000, 30000],
        'Q4': [520000, 72000, 110000, 160000, 125000, 55000, 32000, 20000, 35000, 41000],
        'Annual Total': [1950000, 275000, 390000, 570000, 450000, 200000, 115000, 70000, 140000, 140000]
    }
    
    # 5. Customer Analysis
    customer_data = []
    customer_names = [f'Customer {i:03d}' for i in range(1, 51)]
    industries = ['Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing', 'Education']
    
    for customer in customer_names:
        customer_data.append({
            'Customer Name': customer,
            'Industry': random.choice(industries),
            'Annual Revenue': round(random.uniform(50000, 500000), 2),
            'Payment Terms': random.choice(['Net 30', 'Net 45', 'Net 60', 'Due on Receipt']),
            'Account Status': random.choice(['Active', 'Active', 'Active', 'At Risk', 'Churned']),
            'Customer Since': f'{random.randint(2019, 2023)}-{random.randint(1,12):02d}',
            'Last Purchase': f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}'
        })
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('sample_financial_data.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(payment_data).to_excel(writer, sheet_name='Supplier Payments', index=False)
        pd.DataFrame(financial_summary).to_excel(writer, sheet_name='Quarterly Summary', index=False)
        pd.DataFrame(revenue_breakdown).to_excel(writer, sheet_name='Monthly Revenue', index=False)
        pd.DataFrame(expense_categories).to_excel(writer, sheet_name='Expense Breakdown', index=False)
        pd.DataFrame(customer_data).to_excel(writer, sheet_name='Customer Analysis', index=False)
        
        # Format the Excel file
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print("✅ Sample Excel file 'sample_financial_data.xlsx' created successfully!")
    print("\n📊 File contains:")
    print("- Supplier Payments (100 records)")
    print("- Quarterly Financial Summary")
    print("- Monthly Revenue Breakdown")
    print("- Expense Categories by Quarter")
    print("- Customer Analysis (50 customers)")

if __name__ == "__main__":
    create_sample_financial_data()
