# app.py
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot

from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import csv
import os
from datetime import datetime

# Create Flask app
app = Flask(__name__)

def load_data():
    """Load data from CSV file and prepare it for analysis"""
    # Load the CSV file and replace NaN values with 0 for numeric operations
    df = pd.read_csv('airemissionsdata.csv')
    
    # Find the 2020 target value - looking for a specific row with this commitment
    target_2020 = 0
    for index, row in df.iterrows():
        if row['Year'] == 2020 and pd.notna(row['2020 Reduction commitment']):
            target_2020 = row['2020 Reduction commitment']
            break
    
    # Find the 2030 target value
    target_2030 = 0
    for index, row in df.iterrows():
        if row['Year'] == 2030 and pd.notna(row['2030 Reduction commitment']):
            target_2030 = row['2030 Reduction commitment']
            break
            
    # Fill missing values with 0 for calculations
    df = df.fillna(0)
    
    # Remove the target rows from our data
    # First, create a copy of the dataframe to work with
    emissions_df = df.copy()
    
    # Remove rows that are for 2020 and have a reduction commitment value
    rows_to_keep = []
    for index, row in emissions_df.iterrows():
        # Skip rows that are targets rather than actual data
        if (row['Year'] == 2020 and row['2020 Reduction commitment'] > 0):
            continue
        if (row['Year'] == 2030 and row['2030 Reduction commitment'] > 0):
            continue
        # Keep all other rows
        rows_to_keep.append(index)
    
    # Create a new dataframe with just the rows we want to keep
    emissions_df = emissions_df.loc[rows_to_keep]
    
    # Sort the dataframe by year
    emissions_df = emissions_df.sort_values('Year')
    
    return emissions_df, target_2020, target_2030

def create_total_emissions_chart():
    """Create a chart showing total emissions over time"""
    # Get data and emission columns
    df, _, _ = load_data()
    emission_cols = [
        'Agriculture/Forestry/Fishing (fuel)', 
        'Residential and Commercial', 
        'Industrial ', 
        'Powerstations', 
        'Transport', 
        'Agriculture', 
        'Other'
    ]
    
    # Calculate total emissions for each year by adding up all sectors
    df['Total'] = 0  # Start with zero
    for col in emission_cols:
        df['Total'] = df['Total'] + df[col]  # Add each column one by one
    
    # Create a new figure with specific size
    plt.figure(figsize=(10, 6))
    
    # Plot the total emissions over time
    plt.plot(df['Year'], df['Total'], marker='o', color='#32CD32', linewidth=2)
    
    # Add title and labels
    plt.title('Total Emissions Over Time')
    plt.xlabel('Year')
    plt.ylabel('Total Emissions (Units)')
    
    # Add a grid to make it easier to read
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Convert the chart to a format we can display in HTML
    return save_chart_as_base64()

def create_sector_comparison_chart(selected_year=None):
    """Create a bar chart comparing emissions by sector for a specific year"""
    # Get data and emission columns
    df, _, _ = load_data()
    emission_cols = [
        'Agriculture/Forestry/Fishing (fuel)', 
        'Residential and Commercial', 
        'Industrial ', 
        'Powerstations', 
        'Transport', 
        'Agriculture', 
        'Other'
    ]
    
    # If no year is selected, use the most recent year
    if selected_year is None:
        years = df['Year'].tolist()
        selected_year = max(years)
    
    # Convert to integer to make sure it's a valid year
    selected_year = int(selected_year)
    
    # Find the row for the selected year
    year_rows = df[df['Year'] == selected_year]
    if len(year_rows) == 0:
        # If we don't have data for this year, return None
        return None
    
    year_data = year_rows.iloc[0]
    
    # Collect non-zero sectors into a dictionary
    sector_data = {}
    for col in emission_cols:
        if year_data[col] > 0:
            sector_data[col] = year_data[col]
    
    # Sort the sectors by their values (highest first)
    # First, create lists to store sorted sectors and values
    sorted_sectors = []
    sorted_values = []
    
    # Sort the dictionary items and add to our lists
    for sector, value in sorted(sector_data.items(), key=lambda item: item[1], reverse=True):
        sorted_sectors.append(sector)
        sorted_values.append(value)
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Define colors for the bars
    colors = ['#32CD32', '#90EE90', '#00FF00', '#7CFC00', '#00FA9A', '#98FB98', '#ADFF2F']
    # Make sure we don't try to use more colors than we have sectors
    colors = colors[:len(sorted_sectors)]
    
    # Create the bar chart
    bars = plt.bar(sorted_sectors, sorted_values, color=colors)
    
    
    # Add title and labels
    plt.title(f'Emission by Sector ({selected_year})')
    plt.xlabel('Sector')
    plt.ylabel('Emissions (Units)')
    
    # Rotate the x-axis labels so they don't overlap
    plt.xticks(rotation=45, ha='right')
    
    # Add a grid for the y-axis
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout to make sure everything fits
    plt.tight_layout()
    
    # Convert the chart to a format we can display in HTML
    return save_chart_as_base64()

def create_trend_by_sector_chart():
    """Create a line chart showing emission trends for each sector over time"""
    # Get data
    df, _, _ = load_data()
    
    # Select columns to show in the trend chart
    trend_cols = [
        'Agriculture/Forestry/Fishing (fuel)', 
        'Residential and Commercial', 
        'Industrial ', 
        'Powerstations', 
        'Transport'
    ]
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Define colors for each line
    colors = ['#32CD32', '#90EE90', '#00FF00', '#7CFC00', '#00FA9A']
    
    # Plot a line for each sector
    for i in range(len(trend_cols)):
        col = trend_cols[i]
        color = colors[i % len(colors)]  # Use modulo to cycle through colors if needed
        
        plt.plot(
            df['Year'],       # X values (years)
            df[col],          # Y values (emissions for this sector)
            marker='o',       # Add dots at each data point
            label=col,        # Label for the legend
            linewidth=2,      # Make the line thicker
            color=color       # Set the line color
        )
    
    # Add title and labels
    plt.title('Emission Trends by Sector')
    plt.xlabel('Year')
    plt.ylabel('Emissions (Units)')
    
    # Add a grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add a legend to identify each line
    plt.legend(loc='upper right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Convert to base64 for HTML display
    return save_chart_as_base64()

def create_reduction_targets_chart():
    """Create a chart showing emissions versus reduction targets"""
    # Get data
    df, target_2020, target_2030 = load_data()
    
    emission_cols = [
        'Agriculture/Forestry/Fishing (fuel)', 
        'Residential and Commercial', 
        'Industrial ', 
        'Powerstations', 
        'Transport', 
        'Agriculture', 
        'Other'
    ]
    
    # Calculate total emissions for each year
    df['Total'] = 0
    for col in emission_cols:
        df['Total'] = df['Total'] + df[col]
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    
    # Plot historical emissions
    plt.plot(
        df['Year'],
        df['Total'],
        marker='o',
        label='Historical Emissions',
        linewidth=2,
        color='#32CD32'
    )
    
    # Plot 2020 target as a horizontal line
    plt.axhline(
        y=target_2020,
        color='#FFD700',  # Gold color
        linestyle='--',   # Dashed line
        label='2020 Target'
    )
    
    # Plot pathway from 2020 to 2030 target
    plt.plot(
        [2020, 2030],              # X values (just two points)
        [target_2020, target_2030], # Y values (the targets)
        color='#FF4500',           # Orange-red color
        linestyle='--',            # Dashed line
        label='2030 Target Pathway'
    )
    
    # Add title and labels
    plt.title('Historical Emissions vs Reduction Targets')
    plt.xlabel('Year')
    plt.ylabel('Emissions (Units)')
    
    # Add a grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add a legend
    plt.legend(loc='upper right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Convert to base64
    return save_chart_as_base64()

def save_chart_as_base64():
    """Save the current matplotlib chart as a base64 encoded string"""
    # Create a bytes buffer to hold the image data
    img = io.BytesIO()
    
    # Save the current figure to the buffer
    plt.savefig(img, format='png', bbox_inches='tight')
    
    # Move back to the start of the buffer
    img.seek(0)
    
    # Close the figure to free up memory
    plt.close()
    
    # Convert the image to base64 and return as a string
    return base64.b64encode(img.getvalue()).decode()

def get_years_for_dropdown():
    """Get a list of years to display in the dropdown selector"""
    # Get data
    df, _, _ = load_data()
    
    # Get all years and sort them
    all_years = df['Year'].tolist()
    all_years = sorted(all_years)
    
    # For simplicity, return all years
    # The original code selected a subset of years to reduce dropdown size,
    # but we'll keep it simple and show all years
    return all_years

def calculate_emission_statistics():
    """Calculate mean, median, and mode for emissions data"""
    # Get the data
    df, _, _ = load_data()
    
    # Define emission columns
    emission_cols = [
        'Agriculture/Forestry/Fishing (fuel)', 
        'Residential and Commercial', 
        'Industrial ', 
        'Powerstations', 
        'Transport', 
        'Agriculture', 
        'Other'
    ]
    
    # Calculate total emissions for each year
    df['Total'] = 0
    for col in emission_cols:
        df['Total'] = df['Total'] + df[col]
    
    # Calculate statistics for total emissions
    total_mean = round(df['Total'].mean(), 2)
    total_median = round(df['Total'].median(), 2)
    
    # Calculate mode (most frequent value)
    # For continuous data like emissions, we'll round to 1 decimal place for mode calculation
    rounded_totals = df['Total'].round(1)
    total_mode = rounded_totals.mode().iloc[0] if not rounded_totals.mode().empty else "None"
    
    # Calculate statistics for each sector
    sector_stats = {}
    for col in emission_cols:
        mean = round(df[col].mean(), 2)
        median = round(df[col].median(), 2)
        
        # Calculate mode with rounding
        rounded_values = df[col].round(1)
        mode = rounded_values.mode().iloc[0] if not rounded_values.mode().empty else "None"
        
        sector_stats[col] = {
            'mean': mean,
            'median': median,
            'mode': mode
        }
    
    return {
        'total_stats': {
            'mean': total_mean,
            'median': total_median,
            'mode': total_mode
        },
        'sector_stats': sector_stats
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route that renders the dashboard page"""
    # Generate all charts
    total_emissions_chart = create_total_emissions_chart()
    trend_by_sector_chart = create_trend_by_sector_chart()
    reduction_targets_chart = create_reduction_targets_chart()
    
    # Get years for dropdown
    years = get_years_for_dropdown()
    
    # Default to most recent year
    selected_year = max(years)
    
    # Check if a year was selected in a form
    if request.method == 'POST':
        form_year = request.form.get('year')
        if form_year:
            selected_year = int(form_year)
    
    # Generate the sector comparison chart for the selected year
    sector_comparison_chart = create_sector_comparison_chart(selected_year)
    
    # Calculate emission statistics for the overview section
    statistics = calculate_emission_statistics()
    
    # Render the HTML template with all our data
    return render_template('index.html',
                          total_emissions_chart=total_emissions_chart,
                          sector_comparison_chart=sector_comparison_chart,
                          trend_by_sector_chart=trend_by_sector_chart,
                          reduction_targets_chart=reduction_targets_chart,
                          years=years,
                          selected_year=selected_year,
                          statistics=statistics)

# NEW CODE: Add the survey route
@app.route('/survey', methods=['GET', 'POST'])
def survey():
    message = ""
    
    # Handle form submission
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '')
        age = request.form.get('age', '')
        concern_level = request.form.get('concern_level', '')
        is_recycling = request.form.get('is_recycling', 'off')
        
        # Convert checkbox to boolean (True/False)
        is_recycling = True if is_recycling == 'on' else False
        
        # Simple validation
        valid = True
        if not name:
            message = "Please enter your name."
            valid = False
        else:
            try:
                # Convert age to integer
                age = int(age)
                if age <= 0 or age > 120:
                    message = "Please enter a valid age between 1 and 120."
                    valid = False
            except ValueError:
                message = "Age must be a number."
                valid = False
            
            try:
                # Convert concern level to float
                concern_level = float(concern_level)
                if concern_level < 1 or concern_level > 10:
                    message = "Concern level must be between 1 and 10."
                    valid = False
            except ValueError:
                message = "Concern level must be a number."
                valid = False
        
        # If all validation passes, save to CSV
        if valid:
            # Create data directory if it doesn't exist
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # Check if file exists to write headers
            file_exists = os.path.isfile('data/survey_responses.csv')
            
            # Open the CSV file in append mode
            with open('data/survey_responses.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                
                # Write headers if file doesn't exist yet
                if not file_exists:
                    writer.writerow(['Name', 'Age', 'Concern Level', 'Is Recycling', 'Date Submitted'])
                
                # Write the data row
                writer.writerow([
                    name, 
                    age, 
                    concern_level, 
                    is_recycling, 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            message = "Thank you for your response!"
    
    # Show survey results summary if requested
    survey_data = []
    avg_age = 0
    avg_concern = 0
    recycling_count = 0
    
    if os.path.exists('data/survey_responses.csv'):
        with open('data/survey_responses.csv', 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Skip header row
            
            for row in reader:
                survey_data.append(row)
            
            # Calculate some basic stats if we have data
            if survey_data:
                total_age = 0
                total_concern = 0
                
                for row in survey_data:
                    total_age += int(row[1])
                    total_concern += float(row[2])
                    if row[3].lower() == 'true':
                        recycling_count += 1
                
                avg_age = round(total_age / len(survey_data), 1)
                avg_concern = round(total_concern / len(survey_data), 1)
    
    # Render the survey template
    return render_template('survey.html', 
                          message=message,
                          survey_count=len(survey_data),
                          avg_age=avg_age,
                          avg_concern=avg_concern,
                          recycling_count=recycling_count)

if __name__ == '__main__':
        app.run(debug=True, host='127.0.0.1', port=5001, use_reloader=False)