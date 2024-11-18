from decimal import Decimal
import os
from urllib import request
import pandas as pd
import uuid
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, LoginForm, UploadFileForm
from .models import UserMetrics
import plotly.express as px
from django.contrib.auth import authenticate, login 
from django.contrib.auth import logout 
from .forms import QuestionForm
import plotly.express as px
import plotly.io as pio
import uuid
import os
from django.conf import settings

# Define path for uploaded files
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'upload')

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    

def preprocess_data(file_path):
    df = pd.read_csv(file_path)
    
    # Convert 'Purchase Date' to datetime
    df['Purchase Date'] = pd.to_datetime(df['Purchase Date'], errors='coerce', dayfirst=True)
    
    # Drop duplicates
    df.drop_duplicates(inplace=True)
    
    # Fill missing values
    for col in df.select_dtypes(include=['number']).columns:
        df[col] = df[col].fillna(df[col].median())
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna('Unknown')
    
    return df

def aggregate_data(df):
    df['Net Amount'] = df['Net Amount'].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    agegroup_summary = df.groupby('Age Group').agg(
        total_purchases=('CID', 'count'),
        total_revenue=('Net Amount', 'sum')
    ).reset_index()
    return agegroup_summary



def generate_plots(df, agegroup_summary):
    unique_id = str(uuid.uuid4())  # Generate a unique identifier for each plot session

    # Create interactive plots using Plotly
    missing_values = df.isnull().sum().reset_index()
    missing_values.columns = ['Column', 'Missing Count']
    missing_values = missing_values[missing_values['Missing Count'] > 0]  # Filter non-zero missing values

    # Generate plot if there are missing values
    if not missing_values.empty:
        fig_missing = px.bar(missing_values, x='Column', y='Missing Count',
                             title='Missing Values in Dataset',
                             labels={'Column': 'Feature', 'Missing Count': 'Missing Values'})
        fig_missing_html = pio.to_html(fig_missing, full_html=False)
    else:
        fig_missing_html = None  # No missing values to display


    # Plot Total Purchases by Age Group
    purchases_bar = agegroup_summary
    fig1 = px.bar(purchases_bar, x='total_purchases', y='Age Group', 
                  title='Total Purchases by Age Group', labels={'total_purchases': 'Purchases', 'Age Group': 'Age Group'})
    fig1_html = pio.to_html(fig1, full_html=False)  # Generate Plotly HTML

    # Plot Total Revenue by Age Group
    revenue_line = agegroup_summary
    fig2 = px.line(revenue_line, x='Age Group', y='total_revenue', 
                  title='Total Revenue by Age Group', labels={'total_revenue': 'Revenue', 'Age Group': 'Age Group'})
    fig2_html = pio.to_html(fig2, full_html=False)

    # Plot Monthly Sales
    monthly_sales = df.groupby(df['Purchase Date'].dt.month)['Net Amount'].sum().reset_index()
    monthly_sales.rename(columns={'Purchase Date': 'Month'}, inplace=True)
    fig4 = px.scatter(monthly_sales, x='Month', y='Net Amount', 
                      title='Monthly Sales Trend', labels={'Month': 'Month', 'Net Amount': 'Sales'})
    fig4_html = pio.to_html(fig4, full_html=False)

    # Plot Product Category Sales
    prod_cat_sales = df.groupby('Product Category')['Net Amount'].sum().reset_index()
    fig3 = px.pie(prod_cat_sales, names='Product Category', values='Net Amount', 
                  title='Sales Distribution by Product Category')
    fig3_html = pio.to_html(fig3, full_html=False)

    # Plot Gender Sales
    gender_sales = df.groupby('Gender')['Net Amount'].sum().reset_index()
    fig5 = px.bar(gender_sales, x='Gender', y='Net Amount', 
                  title='Total Purchases by Gender', labels={'Net Amount': 'Purchases', 'Gender': 'Gender'})
    fig5_html = pio.to_html(fig5, full_html=False)

    # Plot Location Sales
    location_sales = df.groupby('Location')['Net Amount'].sum().reset_index()
    fig6 = px.bar(location_sales, x='Location', y='Net Amount', 
                  title='Total Sales by Location', labels={'Location': 'Location', 'Net Amount': 'Sales'})
    fig6_html = pio.to_html(fig6, full_html=False)

    # Plot Time Series of Sales
    time_series = df.groupby(df['Purchase Date'].dt.to_period('M'))['Net Amount'].sum().reset_index()
    time_series['Purchase Date'] = time_series['Purchase Date'].dt.strftime('%Y-%m')
    fig_time_series = px.line(time_series, x='Purchase Date', y='Net Amount',
                              title='Sales Over Time', labels={'Purchase Date': 'Date', 'Net Amount': 'Sales'})
    fig_time_series_html = pio.to_html(fig_time_series, full_html=False)

    # Plot Sales by Age Group and Gender
    age_gender = df.groupby(['Age Group', 'Gender'])['Net Amount'].sum().reset_index()
    fig_age_gender = px.bar(age_gender, x='Age Group', y='Net Amount', color='Gender',
                            barmode='group', title='Sales by Age Group and Gender',
                            labels={'Net Amount': 'Sales', 'Age Group': 'Age Group'})
    fig_age_gender_html = pio.to_html(fig_age_gender, full_html=False)

    # Plot Top 10 Locations by Revenue
    top_locations = df.groupby('Location')['Net Amount'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_top_locations = px.bar(top_locations, x='Location', y='Net Amount',
                               title='Top 10 Locations by Revenue', labels={'Net Amount': 'Revenue', 'Location': 'Location'})
    fig_top_locations_html = pio.to_html(fig_top_locations, full_html=False)

    # Plot Heatmap of Sales by Product Category and Location
    category_location = df.pivot_table(index='Location', columns='Product Category', values='Net Amount', aggfunc='sum', fill_value=0)
    fig_heatmap = px.imshow(category_location, title='Sales Heatmap by Product Category and Location',
                            labels=dict(x='Product Category', y='Location', color='Sales'))
    fig_heatmap_html = pio.to_html(fig_heatmap, full_html=False)

    # Plot Purchase Method Distribution
    purchase_method = df.groupby('Purchase Method')['Net Amount'].sum().reset_index()
    fig_purchase_method = px.pie(purchase_method, names='Purchase Method', values='Net Amount',
                                 title='Sales by Purchase Method')
    fig_purchase_method_html = pio.to_html(fig_purchase_method, full_html=False)

    # Plot Revenue Distribution
    fig_revenue_dist = px.histogram(df, x='Net Amount', nbins=20, title='Revenue Per Transaction',
                                    labels={'Net Amount': 'Revenue'})
    fig_revenue_dist_html = pio.to_html(fig_revenue_dist, full_html=False)

    # Return all the plots as HTML
    return {
        'missing_values_plot': fig_missing_html,
        'purchases_bar': fig1_html,
        'revenue_bar': fig2_html,
        'monthly_sales_plot': fig4_html,
        'product_category_plot': fig3_html,
        'gender_sales_plot': fig5_html,
        'location_sales_plot': fig6_html,
        'time_series_plot': fig_time_series_html,
        'age_gender_plot': fig_age_gender_html,
        'top_locations_plot': fig_top_locations_html,
        'heatmap_plot': fig_heatmap_html,
        'purchase_method_plot': fig_purchase_method_html,
        'revenue_distribution_plot': fig_revenue_dist_html,
    }

    
@login_required
def upload_file(request):
    if request.method == 'POST' and 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        unique_filename = f"{uuid.uuid4()}{os.path.splitext(uploaded_file.name)[1]}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save uploaded file
        with open(file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Process the file
        df = preprocess_data(file_path)

        # Aggregate and generate insights
        agegroup_summary = aggregate_data(df)
        plot_paths = generate_plots(df, agegroup_summary)

        # Store metrics and visualizations in session
        request.session['metrics'] = {
            'total_sales': df['Net Amount'].sum(),
            'total_purchases': df['TID'].nunique(),
            'top_product': df.groupby('Product Category')['Net Amount'].sum().idxmax(),
            'top_location': df.groupby('Location')['Net Amount'].sum().idxmax(),
        }
        request.session['plot_paths'] = plot_paths
        request.session['agegroup_summary'] = agegroup_summary.to_dict(orient='records')

        # Redirect to the display page after upload
        return redirect('display_page')

    form = UploadFileForm()
    return render(request, 'visualizer/upload.html', {'form': form})

from django.shortcuts import render
from django.http import HttpResponse

@login_required
def display_page(request):
    plot_paths = request.session.get('plot_paths', {})
    metrics = request.session.get('metrics', {})
    suggestions = [
        "Focus on Age Group and Product Category for insights on your top-selling demographics and products.",
        "Review the Monthly Sales graph to identify trends or seasonality in sales.",
        "The Total Revenue by Age Group can help you identify which groups are most profitable."
    ]
    
    answer = None
    if request.method == 'POST':
        question = request.POST.get('question', '').lower()
        answer = get_answer(question, metrics)  # Call a function to process the question

    # Pass Plotly HTML to the template
    return render(request, 'visualizer/display_images.html', {
        'plot_paths': plot_paths,
        'metrics': metrics,
        'missing_values_plot': plot_paths.get('missing_values_plot'),
        'suggestions': suggestions,
        'answer': answer,  # Pass the answer back to the template
    })


# Function to get insights based on selected question
def get_answer(question, metrics):
    if "total sales" in question:
        return f"Total Sales: {round(metrics['total_sales'], 2)}"
    elif "top product" in question:
        return f"Top Product: {metrics.get('top_product', 'Not available')}. This is your best-seller!🚀"
    elif "top location" in question:
        return f"Top Location: {metrics.get('top_location', 'Not available')}. Focus your marketing efforts here. 💼 "
    elif "discount effectiveness" in question:
        return "The effectiveness of discounts varies across different age groups and product categories. Focus your discounts where they have the most impact.🎁"
    elif "customer retention" in question:
        return "Customers who make multiple purchases tend to generate more revenue over time. Consider loyalty programs to retain them.💵"
    elif "seasonality" in question:
        return "Sales peak during the holiday season. Focus on special offers during these periods to maximize revenue.🛍️"
    else:
        return "Sorry, I can't answer that question right now."



def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'visualizer/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'visualizer/login.html', {'form': form})

@login_required
def dashboard(request):
    # Just render the dashboard with the user details and upload form
    return render(request, 'visualizer/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')
